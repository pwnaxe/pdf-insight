# 0006. Date precision

## Context

The brief asks for dates in ISO 8601. Documents often give only a month or a year ("marzec
2026", "w roku 2027"). A model forced into `YYYY-MM-DD` fills the gap with an invented day,
usually the first, and the UI then shows a precise date the document never stated.

## Decision

- ISO 8601 allows reduced precision, so `dates[].date` may be `YYYY`, `YYYY-MM` or
  `YYYY-MM-DD`. This still follows the brief.
- A field `dates[].precision` (`year`, `month`, `day`) was added. No existing field was changed
  or removed.
- `document.date` stays a full day (`YYYY-MM-DD`) or `null`. A month or a year alone is not
  a document date.
- The prompt says never to invent a day or a month, but the server does not rely on it:
  `normalize.py` validates each date, derives `precision` from the string (the model's value is
  ignored), drops invalid dates and sets `document.date` to `null` unless it is a valid full day.
- Model output uses a lenient date type (`DateMention`) so that one bad date is dropped and
  does not fail the whole call. The final `AnalysisResult` is strict: precision must match the
  string.
- The web schema derives `precision` when it is missing, so history entries saved earlier still
  load.
- The UI shows `2024` for a year, a month name with the year for a month, and the full date for
  a day.

## Consequences

- Clients of the API must accept three date formats in `dates[].date`.
- A date given as a quarter or a season is still skipped.
