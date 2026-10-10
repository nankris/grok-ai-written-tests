# 001 - Failed or retried solver runs

- `code-only` `lru_ttl` r1: timed out; attempts=2
- `tests-first` `lru_ttl` r1: timed out; attempts=2
- `tests-first` `semver` r1: timed out
- `tests-first` `csvline` r1: timed out; attempts=2
- `tests-first` `ratelimit` r1: attempts=2
- `tests-first` `wordwrap` r1: timed out
- `code-only` `jsonpath` r1: timed out; attempts=2
- `tests-first` `jsonpath` r1: timed out; attempts=2
- `code-only` `rle` r1: attempts=2
- `tests-first` `rle` r1: attempts=2

A retry happens only when the Grok process times out, returns a non-zero status, or does not emit JSON, and the required module file is absent. A finished run that fails hidden tests is not a harness failure and is not listed here unless it also hit one of those process problems.

Session logs that could not be opened (7):

- `code-only` `lru_ttl` r1
- `tests-first` `lru_ttl` r1
- `tests-first` `semver` r1
- `tests-first` `csvline` r1
- `tests-first` `wordwrap` r1
- `code-only` `jsonpath` r1
- `tests-first` `jsonpath` r1
