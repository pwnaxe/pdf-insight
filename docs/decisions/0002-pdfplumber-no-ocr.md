# 0002. pdfplumber for text, no OCR

## Context

The first version used pypdf for text. On Polish contracts it split words with spaces around
diacritics, which broke names and amounts in the model input. pdfplumber returned clean text on
the same files. Many PDFs are scans without a text layer, and OCR would add a heavy dependency
and more latency.

## Decision

- `pdf.py` extracts text per page with pdfplumber.
- pypdf stays for opening the file, detecting encryption (`PDF_ENCRYPTED`) and counting pages
  (`TOO_MANY_PAGES` is checked before extraction).
- A page with fewer than 10 non-space characters counts as having no text layer. It is skipped
  and listed in `warnings`.
- If no page has text, the API returns `NO_TEXT`.
- No OCR.

## Consequences

- Clean Polish text for digital PDFs.
- Scanned pages are silently absent from the analysis except for the warning, so a mixed
  document can give a partial result.
- A fully scanned PDF is rejected with a clear message.
- Two PDF libraries are dependencies.
- Multi-column layouts can mix columns.
