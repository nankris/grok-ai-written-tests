# Compare SemVer 2.0.0 versions

Create `semver.py` in the current directory with this function:

```python
def compare_semver(a: str, b: str) -> int:
    ...
```

Use only the Python standard library.

Return `-1` if `a` has lower precedence than `b`, `0` if they are equal, and `1` if `a` is higher. Raise `ValueError` if either argument is not a valid SemVer 2.0.0 version. Do not accept a leading `v`.

A valid version matches `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`:

- `MAJOR`, `MINOR`, and `PATCH` are non-negative decimal integers with no leading zeros. `0` itself is valid. There are exactly three numeric components.
- If a prerelease is present, a hyphen introduces it and the hyphen must not be the last character. The prerelease is a dot-separated list of non-empty identifiers. Each identifier is ASCII alphanumerics and hyphens (`[0-9A-Za-z-]`). An identifier that is all digits is numeric and must not have a leading zero (`0` is valid, `01` is not). The first hyphen separates the core from the prerelease; further hyphens belong to identifiers.
- If build metadata is present, a plus introduces it. Build identifiers use the same character set, are non-empty, are dot-separated, and may contain leading zeros. Build metadata does not affect precedence.
- Empty pieces are invalid: `1.0.0-`, `1.0.0+`, `1.0.0-a.`, `1.0.0+.b`, whitespace, and an empty string are invalid.

Precedence, from SemVer 2.0.0:

- Compare `MAJOR`, then `MINOR`, then `PATCH` as integers.
- A version with a prerelease has lower precedence than the same core version without one.
- Compare prerelease identifiers from left to right. Numeric identifiers compare as integers and have lower precedence than non-numeric identifiers. Non-numeric identifiers compare by ASCII code point. If one prerelease has more identifiers and the shared prefix is equal, the longer prerelease is higher.
- Versions that differ only in build metadata compare equal.
