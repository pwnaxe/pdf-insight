# 0004. Prompt injection

## Context

A PDF is untrusted input and its text goes into a prompt. A document can contain lines like
"ignore previous instructions" aimed at the model. The result should describe the document, not
obey it.

## Decision

Several layers, none of them enough alone:

- `prompts.py` wraps the text in `<document>` tags and the system prompt says the content is
  data. Literal `<document>` tags inside the text are replaced, so the document cannot close the
  wrapper.
- The model is asked to set `injectionDetected` and copy the text to `injectionQuotes`.
- `injection.py` scans each page with regexes (Polish and English, diacritics folded).
  `suspectedInjection` is true if the model or the regex fires.
- An echo check in `pipeline.py` compares the summary and key points with 4-word phrases from the
  matched snippets. If they repeat the injected text, the call is retried once with a
  correction, then fails with `AI_INVALID_OUTPUT`.
- The API adds a warning with the page numbers and the UI shows a badge.

## Consequences

- Obvious attacks are flagged and kept out of the summary.
- The regex list is short and misses paraphrased or translated attacks. The model flag covers
  only part of that.
- The echo check only works when the regex matched.
- A false positive (a contract that quotes such a phrase) gives a warning, not a failure.
- This reduces the risk, it does not remove it. Model output is just data shown as text; the
  app takes no actions based on it.
