# AI log

## Tool

Claude Code CLI, model Sonnet, run headless in stages from a short spec. I reviewed every diff,
ran tests and an e2e check between stages and made the commits myself.

## Decisions I made up front

- **Python backend as a proxy.** GitHub Pages is static, and Vite puts every `VITE_*` variable into
  the public bundle, so a key in the frontend would be visible to everyone. FastAPI on my own VPS
  holds the key.
- **OpenAI, cheap and fast.** `gpt-6-luna` with `reasoning_effort=none`. The answer must match a
  strict JSON schema, checked by Pydantic on the server and Zod in the browser.
- **Limits.** 10 MB, 100 pages, 400k chars, a rate limit per IP in the app and in nginx, and CORS
  only for the Pages site. Requests with a foreign `Origin` get 403.
- **PDF text is data.** The document goes inside `<document>` tags, the model reports
  `injectionDetected`, a regex check runs next to it, and the UI shows a badge.
- **Tailwind** for the UI instead of hand-written CSS.
- **Git flow.** Feature branches, PRs into `develop`, release PR into `main`. No single big commit.

## Key prompts (shortened)

1. Spec for every stage: monorepo `web/` + `api/`, schema from the brief, one retry with the
   validation error then `AI_INVALID_OUTPUT`, no `any`, no `console.log`, no comments that repeat
   the code, no git commands.
2. Backend: OpenAI plus a fake provider for tests, PDF split by pages, results merged in code
   (not by the model), tests with a fake provider (valid answer, invalid then valid, invalid
   twice, injection flag).
3. "pypdf breaks Polish words. Compare pypdf layout mode and pdfplumber on the test contract,
   pick the cleaner one. The test contract has a hidden AI instruction on page 4, add a test that
   checks we catch it."
4. "Amounts are money only, no percentages or day counts. A date needs an exact day. Limit the
   number after merging."
5. "The final summary waits for all chunks and the contract takes over 30 s. Summarise the full
   text at the same time as the chunks."

## Where the generated code was wrong

- **Text extraction** (`76d2f6d`). pypdf put extra spaces inside Polish words. Claude first
  patched the injection check to ignore those gaps, which only hid the problem. Switched to
  pdfplumber (pypdf still opens and validates the file), removed the patch, and added a test on
  page 4 of the contract.
- **Injection echo check** (`69a0d3b`). Fixed a false alarm: the check that the summary doesn't
  repeat the injected text looked at too much text, so a normal summary could get rejected. Now
  it only checks the suspicious sentence. Added a test.
- **Temperature** (`7738a76`). The code sent `temperature=0.1` unless the model name started with
  `gpt-5` or `o`. `gpt-6-luna` refused it with an error, so the first real call failed. Now it is
  an optional setting and not sent by default. The same commit stopped tests from reading my shell
  settings: with `OPENAI_API_KEY` set, the config test failed.
- **Reasoning effort** (`b33932a`). Claude allowed `minimal`, but the model accepts
  `none|low|medium|high|xhigh`, and our own check rejected `none`. Fixed the allowed values.
- **Amounts and dates** (`9829c7c`). The first real runs returned 40-60 amounts (the whole price
  list). A quarter became a date on the first of the month. A smaller model I tried listed "30%"
  and "14 days" as PLN amounts. Tightened the prompt, and now the list is deduplicated and limited
  after merging.
- **Latency** (`4241397`). With `low` effort one call took 33 s, and a chunked one 26 s, because
  the final summary waited for the chunks. Now the summary of the full text runs at the same time.
  It takes 12-18 s on production.
- **Duplicate companies** (`7434f3f`). The merge kept "Nordwave Logistics" and "Nordwave Logistics
  sp. z o.o." as two entries. Names are now compared without the legal form.
- **Out of scope git use.** Claude ran `git stash` and `git rm --cached` once each, against the
  spec. Nothing was lost, but one file deletion ended up in the wrong commit and I moved it with a
  rebase before the first push.

## Checked by hand

- Diffs and prompts before each commit.
- `gitleaks` and a search for key prefixes over the whole history before every push. The key lives
  only in a root-only env file on the server.
- The test contract through the live UI: parties, 184 500 / 226 935 PLN, 12 300 PLN monthly,
  8 600 EUR yearly, 890 USD monthly, injection flagged and ignored, page 11 reported as a scan,
  under 30 s.
- 360 px wide layout with no sideways scroll, JSON download, history after reload (headless e2e).

## Last round: hardening, redesign, language

- **Grounding.** Every amount, date, person and company must appear in the PDF text, otherwise it
  is dropped and one warning says how many. Dates keep their precision (year, month or day), and a
  missing day is never invented.
- **CV as a subtype.** Instead of adding a new value to the `type` list from the brief,
  `document.subtype` holds a short label like `cv`, and `type` stays `inne`.
- **Security audit.** Pinned GitHub Actions versions, security headers and a content security
  policy (CSP), stable error codes, a container that doesn't run as root, `SECURITY.md`, and
  `npm audit fix` applied through a minimatch override.
- **UI redesign.** Own colors and self-hosted fonts, plus a PL/EN switch for the UI.
- **Language fix.** I first made the output follow the UI language. The brief says the values
  must be in the document's language, so I switched it back: the API has no `lang` parameter, and
  the switch only changes labels (ADR 0008).
- **What went wrong.** The first CSP build embedded small font files inside the CSS and the
  policy `font-src 'self'` blocked them (fixed with `assetsInlineLimit: 0`). A test value named
  `SECRET` triggered gitleaks, so it was renamed. The model also wrote "not a date" remarks inside
  the context text, which are now filtered out afterwards.
