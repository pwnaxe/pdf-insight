# 0003. Structured output and one retry

## Context

The app needs predictable JSON: fixed fields, ISO dates, 3-letter currencies, 3-7 key points.
Free-form model output breaks the UI. The JSON schema sent to the model cannot express every
rule: the sentence count of the summary and the length of `keyPoints` live in Pydantic
validators and do not appear in the schema.

## Decision

- The schema for each call comes from a Pydantic model (`ModelOutput`, `ChunkOutput`,
  `FinalOutput` in `schemas.py`) via `model_json_schema()` and is sent as `json_schema` with
  `strict: true`. The models forbid extra fields.
- The reply is parsed and validated with Pydantic in `pipeline._call`.
- On a validation failure (or a failed echo check, see
  [0004](0004-prompt-injection.md)), the call is repeated once with the error text appended
  to the prompt.
- A second failure returns `AI_INVALID_OUTPUT` (502).
- The final `AnalysisResult` is validated again before it is returned.
- The client validates the response with Zod (`web/src/lib/schema.ts`). The schema is kept in
  both places and changes must be made in both.

## Consequences

- One bad answer usually costs one more call, not an error for the user.
- Worst case is two calls per step, so more latency and cost.
- Timeouts and provider errors are not retried (`AI_TIMEOUT`, `AI_ERROR`).
- Two copies of the schema can drift, so tests exist on both sides.
