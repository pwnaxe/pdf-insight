# 0008. Output language follows the document

## Context

The brief (F-03, MUST) requires the summary, descriptions and all extracted values to be in the
language of the document. An earlier change made the model write in the UI language (sent as a
`lang` form field), so an English UI over a Polish contract produced an English summary.

## Decision

- This supersedes the UI-language behaviour. `POST /api/analyze` has no `lang` parameter; a
  `lang` field in the request is ignored.
- The prompts tell the model to write the summary, key points, keywords, title and every
  context or description field in the language of the document. JSON keys stay English.
- The PL/EN toggle changes only UI labels. It is not sent to the API and never re-runs anything.
- Server warnings follow `document.language`: Polish for `pl`, English otherwise. Generic
  fallbacks (for example the context of an amount) follow it the same way.
- Error responses are English. The web app maps known error codes to its own localized texts.
- The mock provider detects the document language from the text and answers in it.

## Consequences

- The same file gives the same analysis whatever the UI language, so results in history are
  consistent.
- A reader who wants the summary in another language has to translate it outside the app.
