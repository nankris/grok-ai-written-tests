# 003 - Workflow and harness choices

**Extra CLI flags.** The brief's headless pattern is `grok -p ... --always-approve --output-format json --cwd`. The solver calls also pass `--no-subagents` and `--disable-web-search`. Subagents are off because each one would be another model call, and the machine is shared with other experiments under a two-at-a-time cap. Web search is off so a run cannot spend the 600 second budget on search, and so the two conditions see the same spec rather than a textbook solution one of them happened to retrieve. Both choices make this a narrower test than an unrestricted coding agent.

**Parallelism.** At most two Grok processes. The queue alternates which condition is listed first as the task index and repetition change. With two workers, the two conditions of one task usually start together.

**What is scored.** Hidden tests run in a fresh directory that receives the non-test Python files from the work directory. `test_*.py`, `*_test.py`, and `conftest.py` are left behind so the agent's tests cannot weaken the hidden suite. A missing module fails at collection and counts as fraction 0.

**Reference check.** `harness/run.py` refuses to start if any hidden suite fails on `reference/<id>.py`. That validation is `results/reference_validation.json`.

**Cost.** Reported cost is the CLI field `total_cost_usd`. A one-word probe before the experiment returned about 14k input tokens, so most of the bill is the system prompt and tool definitions, repeated every turn.

**Not done.** There is no mutation score of the agent tests, no second model, and no attempt to stop the agent from reading arbitrary paths beyond the prompt and the after-the-fact peek flag.
