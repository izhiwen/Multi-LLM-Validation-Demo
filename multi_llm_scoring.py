"""
multi_llm_scoring.py
--------------------
Reference implementation of the multi-model LLM-as-measurement pipeline used to
score archival documents in the underlying research project (see README).

The actual production pipeline is in a private research repo and includes
project-specific OCR, prompt versioning, retry / rate-limit handling, and
provenance logging. This module is a clean, pedagogical version that
demonstrates:

    1. A single, version-pinned scoring contract (one structured score per
       document per model).
    2. Parallel scoring across five frontier providers with a unified
       interface.
    3. Strict structured-output validation, so a malformed model response is
       caught at the boundary rather than silently corrupting the scores file.

The pipeline is intentionally agnostic about what is being measured. Plug in
your own `prompt_template` and your own `parse_score` and the same scaffolding
works for sentiment, ideology, claim extraction, plan-quality scoring, etc.

Author : Steve Zhiwen Wang  (zhw94@pitt.edu)
"""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Iterable

# NOTE: provider SDKs are imported lazily in their respective adapters so the
# module can be imported without all keys configured.


# ----------------------------------------------------------------------------
# Scoring contract
# ----------------------------------------------------------------------------

PROMPT_TEMPLATE = """\
You will be given the full text of a single archival document written by a
late-19th-century Chinese government official in response to a memorial
proposing institutional reform.

Your job is to assess how strongly the document expresses pro-reform sentiment
toward [TARGET_INSTITUTION]. Score on a 0.0 - 1.0 scale where:

  0.0   = clearly opposes the proposed institution
  0.5   = neutral, ambiguous, or mixed
  1.0   = clearly endorses the proposed institution

Return JSON only, with this exact schema:

  {{"score": <float 0.0 to 1.0>,
    "rationale": "<one sentence in English>",
    "key_phrases": ["<up to three short Chinese excerpts>"]}}

Do not return any text outside the JSON object.

DOCUMENT:
\"\"\"{document_text}\"\"\"
"""


@dataclass(frozen=True)
class ScoreRecord:
    doc_id: str
    model: str
    score: float
    rationale: str
    key_phrases: tuple[str, ...]
    latency_seconds: float


def parse_score(raw: str) -> dict:
    """Strict JSON parse of a model response. Raises if malformed."""
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("Model response was not a JSON object.")
    score = float(obj["score"])
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"Score out of range: {score}")
    rationale = str(obj.get("rationale", ""))
    key_phrases = tuple(str(p) for p in obj.get("key_phrases", []))[:3]
    return {"score": score, "rationale": rationale, "key_phrases": key_phrases}


# ----------------------------------------------------------------------------
# Provider adapters
# ----------------------------------------------------------------------------
# Each adapter takes a fully-rendered prompt string and returns the raw text
# response. Adapters are intentionally thin — error handling and retries live
# in the orchestration layer below.


# NOTE: model strings below are pinned as of 2026-05. Each provider rotates SKUs
# faster than this demo will be touched; if you reuse this code in a different
# month, update each `model=` argument to whatever your provider currently ships.

def _call_chatgpt(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model="gpt-4o",  # update to current OpenAI flagship for your run
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _call_gemini(prompt: str) -> str:
    # Uses the legacy `google-generativeai` SDK; the newer `google-genai` SDK
    # has a different surface but the same JSON-mode pattern works there too.
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-pro")  # bump to current Gemini Pro for your run
    resp = model.generate_content(
        prompt,
        generation_config={"temperature": 0.0, "response_mime_type": "application/json"},
    )
    return resp.text


def _call_claude(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _call_qwen(prompt: str) -> str:
    # Alibaba DashScope (OpenAI-compatible endpoint).
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    resp = client.chat.completions.create(
        model="qwen-max",  # bump to current Qwen flagship for your run
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _call_deepseek(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )
    resp = client.chat.completions.create(
        model="deepseek-chat",  # alias tracking DeepSeek's current chat model
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


PROVIDERS: dict[str, Callable[[str], str]] = {
    "chatgpt": _call_chatgpt,
    "gemini": _call_gemini,
    "claude": _call_claude,
    "qwen": _call_qwen,
    "deepseek": _call_deepseek,
}


# ----------------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------------


def score_document(
    doc_id: str,
    document_text: str,
    target_institution: str,
    models: Iterable[str] | None = None,
    max_retries: int = 3,
) -> list[ScoreRecord]:
    """Score one document with each requested model. Retries on parse / API errors."""
    if models is None:
        models = list(PROVIDERS.keys())
    prompt = PROMPT_TEMPLATE.format(
        document_text=document_text,
        target_institution=target_institution,
    )
    records: list[ScoreRecord] = []
    for model in models:
        adapter = PROVIDERS[model]
        last_err: Exception | None = None
        for attempt in range(max_retries):
            t0 = time.time()
            try:
                raw = adapter(prompt)
                parsed = parse_score(raw)
                records.append(
                    ScoreRecord(
                        doc_id=doc_id,
                        model=model,
                        score=parsed["score"],
                        rationale=parsed["rationale"],
                        key_phrases=parsed["key_phrases"],
                        latency_seconds=time.time() - t0,
                    )
                )
                break
            except Exception as exc:  # noqa: BLE001 -- adapter or JSON parse failure
                last_err = exc
                time.sleep(2.0 ** attempt)
        else:
            raise RuntimeError(
                f"Model {model} failed for doc {doc_id} after {max_retries} retries: {last_err}"
            )
    return records


def score_corpus_parallel(
    documents: dict[str, str],
    target_institution: str,
    max_workers: int = 8,
) -> list[ScoreRecord]:
    """Score every (document, model) pair in a thread pool. One row per pair."""
    out: list[ScoreRecord] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(score_document, doc_id, text, target_institution): doc_id
            for doc_id, text in documents.items()
        }
        for fut in as_completed(futures):
            out.extend(fut.result())
    return out


if __name__ == "__main__":
    # Smoke-test path. Real corpus loading happens in the private research repo.
    sample_docs = {"demo_001": "（示例文本，仅用于测试）"}
    records = score_corpus_parallel(sample_docs, target_institution="Parliament")
    for r in records:
        print(r)
