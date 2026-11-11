# 0005. Chunking and merge

## Context

Long contracts do not fit well in one call, and one big call is slow. Model output is capped
(`LLM_MAX_TOKENS`) and each call has a timeout (`LLM_TIMEOUT_S`).

## Decision

- `chunking.py` splits the text by whole pages into chunks of up to 12,000 chars
  (`CHUNK_CHARS`). A page larger than that is split by paragraphs. At most 12 chunks
  (`MAX_CHUNKS`); the rest is dropped and a warning says so.
- One chunk means one call that returns everything.
- Several chunks are extracted with concurrency 3 (`CHUNK_CONCURRENCY`).
- While the chunks run, a separate `summary` call reads the full text, as long as it is within
  `DIRECT_SUMMARY_CHARS` (150,000). Above that, a `final` call writes the summary from the
  chunk summaries after the chunks finish. With the defaults the cap is 12 x 12k = 144k chars,
  so this fallback only applies if those settings are raised.
- `merge.py` merges chunk outputs without a model: dedupe of organizations, people and keywords,
  fuzzy dedupe of amounts, first non-empty title and date, most common language and type.
- Caps: 20 amounts, 20 dates, 12 keywords.

## Consequences

- Latency stays close to one slow call instead of the sum of all.
- Merge is deterministic and testable, but it is heuristic: near-duplicate amounts with
  different wording can survive, and a real duplicate with a different context can be dropped.
- Entities near a chunk boundary can be split across chunks.
- Very long documents are analyzed only from the start, with a warning.
- Up to 13 model calls for one request (12 chunks plus the summary).
