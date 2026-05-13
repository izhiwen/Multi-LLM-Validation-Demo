# Security & Privacy

This repo is the worked example of an LLM-as-measurement validity
protocol. It handles API keys for five frontier LLM providers
(OpenAI, Google, Anthropic, DashScope/Qwen, DeepSeek) and processes
archival text data.

## API key handling

`multi_llm_scoring.py` reads provider credentials from environment
variables only:

- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `ANTHROPIC_API_KEY`
- `DASHSCOPE_API_KEY`
- `DEEPSEEK_API_KEY`

**Never commit these.** The repo's `.gitignore` excludes common env
files (`.env`, `.envrc`, `~`) but you are responsible for not
running `git add -A` on a working tree that contains them. If you fork
this repo and accidentally commit a key, rotate it immediately at the
provider's console and force-push the cleaned history (or just rotate;
the key is the part that matters).

For local development the recommended pattern is:

```bash
export OPENAI_API_KEY=$(security find-generic-password -s openai -w)  # macOS Keychain
# or
export $(cat .env | grep -v '^#' | xargs)  # plain .env file, .gitignore'd
```

If you use the [AiPlus secret-broker](https://github.com/izhiwen/AiPlus-Agent-Key)
(`aiplus secret-broker`), it can resolve aliases against Bitwarden
Secrets Manager and inject them as env vars at runtime without ever
persisting the secret to disk.

## Data handling

The CSV in `data/llm_scores_aggregated.csv` contains **only aggregate
scores** — one row per (document, model) pair, no raw text, no author
identifiers. The underlying Classical Chinese source text stays in a
private research repository (`AIER_OS_Qing`) until the JMP that uses
this corpus is publicly released.

If you fork this repo to apply the same protocol to your own corpus:

- **Do not commit raw source text** if it has any identifiability
  concerns (named authors, sensitive content, copyright). Aggregate
  outputs only.
- **Do not commit prompt versions that embed PII or sensitive
  identifiers** — prompts in this repo are intentionally generic.
- For IRB-protected corpora, coordinate with your institutional IRB
  office before any LLM-scoring run.

## Reporting issues

For non-sensitive bugs and feature requests, open a GitHub issue.

For security or privacy issues (a way to leak data outside the
designed boundaries, a key handling flaw, a deserialization bug, etc.),
email the maintainer directly instead of opening a public issue:

- `zhw94@pitt.edu` (academic)
- `wangecon@outlook.com` (primary)

## What this repo does not claim

- This is **not** a general-purpose LLM-as-measurement framework — it
  is one worked example. For the methodology behind it, see
  [AiEconLab's LLM-as-Measurement Specialist persona](https://github.com/izhiwen/AiEconLab/blob/main/core/templates/personas/llm-measurement.md).
- The scoring runs in this repo were performed with model snapshots
  current at the time of publication. LLM providers update models;
  scores may not be literally reproducible. The validity claim is
  about the **protocol**, not about exact score replicability.
- Hand-coded ground truth, where used in the paper, is held in the
  private research repo. The public CSV in this repo is the model
  scores only.
