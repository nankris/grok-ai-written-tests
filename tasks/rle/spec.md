# Run-length encoding that allows digits and backslashes

Create `rle.py` in the current directory with these functions:

```python
def encode(s: str) -> str:
    ...
def decode(encoded: str) -> str:
    ...
```

Use only the Python standard library.

The alphabet is every Unicode character. `encode("")` and `decode("")` are `""`. For every string `s`, `decode(encode(s)) == s`. `encode` always emits the canonical form below. `decode` parses the token grammar greedily and raises `ValueError` on input that is not a concatenation of tokens. A concatenation of tokens is valid even when two neighbouring tokens happen to repeat the same character (that string is not what `encode` would emit, but it is still decodable).

Canonical encoding walks maximal runs. For a run of character `c` with length `n >= 1`:

- If `c` is a backslash or an ASCII digit (`0` through `9`), the token is a backslash, then `c`, then the decimal length with no leading zeros. The length is always written, including when it is 1.
- Otherwise the token is `c` when `n == 1`, and `c` plus the decimal length when `n >= 2`. The length has no leading zeros. A length of 1 is omitted.

`decode` reads tokens from left to right:

- A backslash introduces an escaped run. The next character must be a digit or a backslash, and that character is the run character. After it, a decimal length of at least one digit is required, with no leading zeros and a value of at least 1. The length is required even when it is 1. A trailing backslash or any other character after the backslash is an error.
- Any other character is a normal run character and must not be an ASCII digit (a bare digit is an error). If decimal digits follow, they are the length: no leading zeros, and the value must be at least 2. If no digits follow, the length is 1.
- Digits are consumed greedily as a length, so a normal token `a10` is ten `a`s, not an `a` followed by a bare digit.

A length of 0, a leading zero in a length, an explicit length of 1 on a normal character, a bare digit, and a bad escape all raise `ValueError`.
