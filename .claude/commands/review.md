---
description: Review the current diff against CLAUDE.md and run the checks
allowed-tools: Bash(git diff:*), Bash(git status:*), Bash(git log:*), Bash(npm ci), Bash(npm run:*), Bash(npm test), Bash(uv sync), Bash(uv run:*)
---

Review the current changes (`git status`, `git diff`) against CLAUDE.md.

1. Boundaries: look for secrets or keys, `dangerouslySetInnerHTML`, `any`, `console.log`,
   a removed `<document>` wrapping or injection check, and looser CORS or limits.
2. Schema: if `api/app/schemas.py` or `web/src/lib/schema.ts` changed, check that both match.
3. Definition of done: tests for new logic, README and `.env.example` updated if needed.
4. Run the checks for each package that changed (see Commands in CLAUDE.md). Web: lint,
   format:check, typecheck, test, build. API: ruff check, ruff format --check, pytest.

Report findings by file and line, most serious first, then the check results. Say plainly which
checks failed. Do not fix anything unless asked.
