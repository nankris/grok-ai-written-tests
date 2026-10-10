# 004 - Coordinator notes (run interruptions, timing caveats)

**1. The first batch was killed mid-run.** The Grok session that launched the batch exited at ~21:52 IST (10 Oct 2026) and took its child batch with it after 4/20 runs were scored. The batch was resumed with `harness/run.py --reps 1 --skip-validate`, which skips already-scored runs (log: `results/batch_resume.log`).

**2. An orphan solver overlapped one run.** A Grok solver left over from the killed batch kept working in `/tmp/ai-written-tests-work/tests-first/lru_ttl-r1` for ~15 min while the resumed batch's attempt 1 of the same run used that directory. The coordinator killed the orphan at ~22:15 IST. Attempt 1 timed out and was not scored. The scored attempt 2 started at 22:18 IST in a directory the harness deletes and recreates per attempt, after the orphan was dead, so the scored result is treated as clean. It was not rerun: rerunning only the run that failed would bias the comparison.

**3. Every failure is a timeout, not a wrong answer.** All 3 failed runs (lru_ttl tests-first, jsonpath both arms) hit the 600 s solver budget and scored 0 hidden tests. tests-first hit the budget 5/10 times vs code-only 2/10. With a larger budget the gap may shrink or vanish; this experiment measures "solved within 10 minutes", not code quality.

**4. Reported wall time is capped at 600 s.** For timed-out runs `wall_seconds` records the timeout, but the process sometimes took longer to exit (lru_ttl attempt 1 ran from 22:00 to 22:18 IST). Medians for tests-first are therefore lower bounds.

**5. Shared plan quota.** Three other Grok experiments ran in parallel on the same SuperGrok plan during this batch; slower responses could have contributed to timeouts in both arms.
