# 002 - Measurement notes

**Peeks outside the work directory.** The prompt forbids reading the rest of the disk. The scanner flags a tool path or command that mentions this repo, `hidden_tests`, or `reference/` and is not inside the work directory. Flagged runs: 0.

None flagged.

**Solution text mentioning the repo or hidden tests.** 0 run(s).

None.

**Code-only runs that wrote a test file anyway.** 0 run(s). Hidden scoring ignores test files, so this does not by itself change the hidden-test score. It does mean the condition was not clean.

None.

**Agent tests that do not pass on the reference solution.** These are the false-failing tests: the agent's own suite rejects the reference implementation, so the suite is not a correct reading of the spec (or it errors before it can check).

- `lru_ttl` r1: false-failing 1 (failed 1, errors 0) of 77 collected
- `ratelimit` r1: false-failing 1 (failed 1, errors 0) of 73 collected
- `wordwrap` r1: false-failing 4 (failed 4, errors 0) of 108 collected
- `daterange` r1: false-failing 2 (failed 2, errors 0) of 101 collected

**Session command scan is best-effort.** `results/raw/*.json` stores the headless response, which has usage and the final text, not the tool trace. Commands are scraped from `~/.grok/sessions/.../updates.jsonl` by looking for `command` and path fields. A future CLI that renames those fields would show up as zero check commands. `n_missing_session_scan` in the condition block counts runs whose session directory was not found.
