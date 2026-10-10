# Final summary

Telling Grok 4.7 to write its own tests first produced a mean hidden-test fraction 0.111 lower than code-only. The bootstrap 95% CI on that paired difference (-0.33 to 0.00) includes zero. Full passes: tests-first only 0, code-only only 1, both 7, neither 1 (n_pairs=9).

Sample size: 19 scored runs, reps [1], tasks in the repo 10.

tests-first full pass 7/9.
code-only full pass 9/10.

Issues worth reading: timeouts and retries in issues-found/001-failed-runs.md, peeks and false-failing tests in issues-found/002-measurement.md, flag and harness limits in issues-found/003-workflow.md.

Incomplete relative to the original brief: a second repetition was optional and is present only if `reps` above contains 2. No mutation testing of the agent suites. The newsletter archive page was not fetched (blocked); the claim is taken from the tweet the archive URL points at.
