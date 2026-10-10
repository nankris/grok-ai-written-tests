# Parse a canonical Roman numeral

Create `roman.py` in the current directory with this function:

```python
def parse_roman(s: str) -> int:
    ...
```

Use only the Python standard library.

`parse_roman` accepts only the canonical Roman spelling of an integer from 1 through 3999 and returns that integer. Every other string raises `ValueError`, including the empty string, any lowercase or non-Roman character, surrounding whitespace, and any non-canonical spelling of an in-range value.

The canonical spelling is the usual place-value form. Encode thousands, hundreds, tens, and ones independently and concatenate them:

- thousands: 0 `""`, 1 `M`, 2 `MM`, 3 `MMM` (3999 is the maximum, so four `M`s never appear)
- hundreds: `""`, `C`, `CC`, `CCC`, `CD`, `D`, `DC`, `DCC`, `DCCC`, `CM`
- tens: `""`, `X`, `XX`, `XXX`, `XL`, `L`, `LX`, `LXX`, `LXXX`, `XC`
- ones: `""`, `I`, `II`, `III`, `IV`, `V`, `VI`, `VII`, `VIII`, `IX`

A string is valid exactly when it equals that encoding for some integer from 1 through 3999.
