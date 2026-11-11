# AI log

## Tool

Claude Code CLI, model Sonnet, run headless in stages from a short spec. I reviewed every diff,
ran tests and an e2e check between stages and made the commits myself.

## Decisions I made up front

- **Python backend as a proxy.** GitHub Pages is static and Vite bakes every `VITE_*` var into
  the bundle, so a key in the frontend env would be public. FastAPI on my own VPS holds the key.
- **OpenAI, cheap and fast.** `gpt-6-luna` with `reasoning_effort=none`, structured output
  (`json_schema`, strict), Pydantic on the server and Zod in the browser.
- **Limits.** 10 MB, 100 pages, 400k chars, rate limit per IP in the app and in nginx, CORS only
  for the Pages origin plus 403 for a foreign `Origin`.
- **PDF text is data.** Document goes inside `<document>` tags, the model reports
  `injectionDetected`, a regex check runs next to it, the UI shows a badge.
- **Tailwind** for the UI instead of hand-written CSS.
- **Git flow.** Feature branches, PRs into `develop`, release PR into `main`. No single big commit.

## Key prompts (shortened)

1. Spec for every stage: monorepo `web/` + `api/`, schema from the brief, one retry with the
   validation error then `AI_INVALID_OUTPUT`, no `any`, no `console.log`, no comments that repeat
   the code, no git commands.
2. Backend: OpenAI + deterministic mock provider, chunking by pages, merge without the model,
   tests with a fake provider (valid, invalid then valid, invalid twice, injection flag).
3. "pypdf breaks Polish words. Compare pypdf layout mode and pdfplumber on the test contract,
   pick the cleaner one, add a test on page 4 text."
4. "Amounts are money only, no percentages or day counts. A date needs an exact day. Cap after
   merge."
5. "Final summary waits for all chunks and the contract takes over 30 s. Summarise the full text
   in parallel with chunk extraction."

## Where the generated code was wrong

- **Text extraction** (`76d2f6d`). pypdf returned Polish words split by spaces around
  diacritics. Claude first worked around it in the injection regex by joining the gaps, which only
  hid it. Switched extraction to pdfplumber (pypdf still opens and validates the file), dropped
  the workaround, added a test on page 4 of the contract.
- **Injection echo check** (`69a0d3b`). The snippet started 20 chars before the match and the
  check skipped its first word, so a normal summary quoting the payment terms next to the
  injected line could be rejected. Snippet is now only the offending sentence, with a test for
  that case.
- **Temperature** (`7738a76`). The provider sent `temperature=0.1` unless the model name started
  with `gpt-5` or `o`. `gpt-6-luna` answered 400, so the first real call failed. Now an optional
  env var, not sent by default. The same commit isolated tests from my shell env: with
  `OPENAI_API_KEY` exported, the config test failed.
- **Reasoning effort** (`b33932a`). Claude allowed `minimal`, the model takes
  `none|low|medium|high|xhigh`, and `none` was rejected by our own validation. Fixed the allowed
  values.
- **Amounts and dates** (`9829c7c`). First real runs gave 40-60 amounts (the whole price list),
  a quarter turned into a first-of-month date, and a smaller model I tried put "30%" and
  "14 days" in amounts as PLN. Tightened the prompt, capped and deduped after the merge.
- **Latency** (`4241397`). With `low` effort one call took 33 s, chunked 26 s, because the final
  summary waited for the chunks. Full-text summary now runs in parallel. 12-18 s on production.
- **Duplicate companies** (`7434f3f`). Merge kept "Nordwave Logistics" and "Nordwave Logistics
  sp. z o.o." as two entries. Names are now compared without the legal form.
- **Out of scope git use.** Claude ran `git stash` and `git rm --cached` once each against the
  spec. Nothing was lost, but one file deletion landed in the wrong commit and I moved it with a
  rebase before the first push.

## Checked by hand

- Diffs and prompts before each commit.
- `gitleaks` and a grep for key prefixes over the whole history before every push. The key lives
  only in a root-only env file on the server.
- The test contract through the live UI: parties, 184 500 / 226 935 PLN, 12 300 PLN monthly,
  8 600 EUR yearly, 890 USD monthly, injection flagged and ignored, page 11 reported as a scan,
  under 30 s.
- 360 px layout without horizontal scroll, JSON download, history after reload (headless e2e).
