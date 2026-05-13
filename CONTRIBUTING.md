# Contributing

This repo is the worked example of a single validity protocol on a
specific archival corpus, not a general-purpose library. So
contribution scope is narrow.

## What fits

✅ **In scope**:
- Bug fixes in `multi_llm_scoring.py` or `correlation_analysis.py`
- Documentation improvements (README, this file, SECURITY.md)
- Additional figure outputs (B&W versions, alternative encodings,
  color-blind palette variants)
- Reproducibility fixes (pinning, environment, deterministic seeds)
- Adapter examples for using the same protocol on a different corpus
  (without committing your corpus's raw data here)

❌ **Out of scope** (better placed elsewhere):
- New LLM-as-measurement methodology — that belongs in
  [AiEconLab's LLM-as-Measurement Specialist persona](https://github.com/izhiwen/AiEconLab/blob/main/core/templates/personas/llm-measurement.md)
  (open an issue / PR there instead)
- Generalizing into a framework / library — keep this as the worked
  example; if you want a framework, fork and rename
- Changes to the underlying job-market paper's claims (those go through
  the academic publication process, not GitHub)
- Adding more model providers (low ROI — the panel is already 5 frontier
  models with diverse training origins)

## Before opening a PR

1. **Open an issue first** for anything non-trivial. The methodology is
   tightly tied to a published / about-to-be-published paper and we
   want to avoid accidentally diverging from the paper's claims.
2. **Run the existing pipeline end-to-end** to make sure your change
   doesn't break the figure regeneration:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python correlation_analysis.py
   ```
3. **No API keys in code or fixtures**. See SECURITY.md.

## Commit messages

Bilingual title preferred for user-facing changes:
`English title / 中文标题`

## Author / maintainer

Steve Zhiwen Wang, PhD candidate, Department of Economics, University
of Pittsburgh. zhw94@pitt.edu · zhiwen-wang.com
