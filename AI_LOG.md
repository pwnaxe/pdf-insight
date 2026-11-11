# AI log

## Tools

- Claude Code CLI (`claude`, model Sonnet), headless, wrote the code. I ran it in stages from a
  short spec, reviewed every diff, ran tests and e2e between stages and committed myself.
- An AI assistant (Grok Bot) that drove the Claude Code runs, did the server setup (Docker,
  nginx, certbot) and the manual tests against the real API.
- OpenAI `gpt-6-luna` is the model inside the app.

## Key prompts (shortened)

1. Spec, given to every stage:
   > Monorepo web/ + api/. FastAPI extracts text (pypdf), chunks it, calls OpenAI with a strict
   > json_schema, validates with Pydantic, one retry with the validation error, then
   > AI_INVALID_OUTPUT. Document goes inside `<document>` tags as untrusted data, model sets
   > injectionDetected, plus a regex heuristic. Zod on the frontend before display. No any, no
   > console.log, no comments that repeat the code, no git commands.
2. Stage prompt, backend:
   > Implement app/llm (OpenAI + deterministic mock), prompts, pipeline (single call or chunks with
   > a semaphore of 3, deterministic merge, final summary), rate limit, CORS + 403 on foreign
   > Origin, size/page/text limits. Tests with a fake provider: valid, invalid then valid, invalid
   > twice, injection flagged even if the model says false.
3. Review fixes:
   > pypdf splits Polish words ("p ł atno ś ci"). Compare pypdf layout mode vs pdfplumber on the
   > test contract and pick the cleaner one. Injection snippet must be only the offending
   > sentence, so the echo check can't reject a summary for repeating normal text next to it.
4. Quality after the first real run:
   > Never turn a percentage, a day count or a quantity into an amount. A date needs an exact
   > day: "I kwartał 2027" is not a date. Cap amounts and dates after merge.
5. Latency:
   > The final summary call runs after all chunk calls and pushes the contract over 30 s. Run a
   > summary over the full text in parallel with chunk extraction when the text is short enough.

## Where AI got it wrong and what I did

- **Polish text from pypdf.** The first extraction gave "wcze ś niejsze", "co dajełącznie". Claude
  first patched the injection regex around it (joining gaps), which only hid the problem. I sent it
  back to fix extraction itself: switched to pdfplumber, removed the hack, added a test that page 4
  of the contract contains "warunki płatności" and "226 935,00 zł brutto".
- **Temperature on a reasoning model.** The provider sent `temperature=0.1` except for model names
  starting with `gpt-5`/`o`. `gpt-6-luna` rejected it with a 400, so the first real call failed.
  Replaced the name guessing with an optional `LLM_TEMPERATURE` env var. Same story with
  `reasoning_effort`: Claude allowed `minimal`, the model supports `none`/`low`/... only.
- **Too slow.** With `reasoning_effort=low` the contract took 33 s in one call and 26 s in chunks
  (final summary waited for all chunks). Fix: summary over the full text in parallel with chunk
  extraction, and `reasoning_effort=none`. Now about 12-14 s with the same facts.
- **Model output quality.** First real run: 43-62 amounts (whole price list, "30%" and "14 dni"
  as PLN when I tried a smaller model), "I kwartał 2027" turned into `2027-01-01`, migration start
  date wrong, a power of attorney attributed to the wrong person, final summary without any money
  values. Tightened the prompt rules, added caps and near-duplicate dedupe in the merge, and asked
  for parties, money with currency and term in the summary.
- **Echo check too eager.** The first version of the "summary repeats the injected text" check used
  a snippet with 20 chars of context before the match and skipped its first word, so it could
  reject a normal summary. Narrowed the snippet to the offending sentence and added a test that the
  regular payment terms from the same paragraph pass.
- **Tests depended on my shell.** With `OPENAI_API_KEY` exported locally `test_config` failed.
  Claude added an autouse fixture that clears all settings env vars and disables `.env` loading.
- **Rules broken by the agent.** Claude ran `git stash` and `git rm --cached` once each although
  the spec said no git commands. Nothing was lost, I checked the tree and committed by hand.
- **Mock provider.** The regex mock produced cut-off contexts ("ament miesięczny w wysokości").
  It's only for running without a key, but I had it cleaned up so the demo mode is readable.

## What I checked by hand

- Every diff before a commit, the prompts word by word.
- `git log -p` and gitleaks for secrets before each push. The key exists only in a root-only env
  file on the server.
- The test contract against the real model: values, currencies, parties, date, injection flagged
  and not followed, page 11 listed as having no text, time under 30 s.
