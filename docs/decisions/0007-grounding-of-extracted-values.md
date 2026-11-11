# 0007. Grounding of extracted values

## Context

A model can return a plausible value that the document never states: a total it added up
itself, a day it filled in, a person it inferred. The prompt forbids this, but a prompt is not
a guarantee, and an embedded instruction in the PDF may try to plant values too.

## Decision

- After merge and before the final validation, `grounding.py` checks every amount, date,
  person, organisation and `document.date` against the extracted text of all pages. Items that
  are not found are dropped (`document.date` becomes `null`). One warning (in the document language) states the
  number of dropped items, and only when it is above zero.
- Amounts: every number in the text goes into an index, normalised to two decimals. Thousands
  separators (space, no-break space, narrow no-break space, thin space, dot, comma,
  apostrophe), a decimal comma or dot and an optional `,00` are handled, so `184 500`,
  `184.500,00`, `184,500.00` and `184500` are the same value. A value is grounded only if it is
  in the index. Sums are never recomputed: a total that is not in the text is dropped.
  Numbers followed by `%` are skipped. A bare integer below 1000 counts only next to a currency
  marker, so a list number or a count cannot ground an amount. The currency code of the
  amount is not compared.
- Dates: the text is scanned for ISO, `dd.mm.yyyy`, `dd/mm/yyyy`, `dd-mm-yyyy`, two-digit years
  (not inside longer number chains), Polish month names in all cases and English month names
  and abbreviations, with optional leading zeros. A day grounds its month and year. A month
  (`YYYY-MM`) needs a month name with a year, `03.2026`, `03/2026` or `2026-03`. A year needs
  the four-digit token. A month never grounds a day.
- Entities: casefolded, whitespace collapsed, quotes and dashes unified, legal forms (`sp. z o.o.`,
  `S.A.`, `sp.k.`, `Ltd`, `GmbH`, `Inc.`, `LLC` and similar) removed from both sides, then a
  whole-word substring match. People: the surname (last word, at least 3 characters) is matched
  by a prefix that tolerates Polish endings, and a first-name prefix must be within three
  words of it. A name with one word matches by prefix only.
- Lines of an embedded instruction (the hit found by `injection.py` plus its continuation
  lines) are removed from the evidence, so a value that only the injected text states cannot
  pass.
- Context fields are free text and are not grounded.

## Consequences

- A correct value written in a form not listed above (for example "12,3 tys.") is dropped, and
  the user sees the warning. This is the accepted cost of having no invented values.
- A number split by a line break (`295` / `200,00`) is not joined.
- Without a two-digit-year rule a date like `12.03.26` would be missed, with it a chain such as
  `1.3.26.5` is deliberately ignored.
- Person matching is heuristic: a rare surname together with a first-name stem next to it is
  enough, and very short or unusual names may be dropped.
