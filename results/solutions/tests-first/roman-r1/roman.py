"""Parse the canonical Roman spelling of an integer from 1 through 3999."""

_THOUSANDS = ("", "M", "MM", "MMM")
_HUNDREDS = ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM")
_TENS = ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC")
_ONES = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")


def _canonical_map() -> dict[str, int]:
    mapping: dict[str, int] = {}
    for thousands in range(4):
        for hundreds in range(10):
            for tens in range(10):
                for ones in range(10):
                    value = thousands * 1000 + hundreds * 100 + tens * 10 + ones
                    if value == 0:
                        continue
                    spelling = (
                        _THOUSANDS[thousands]
                        + _HUNDREDS[hundreds]
                        + _TENS[tens]
                        + _ONES[ones]
                    )
                    mapping[spelling] = value
    return mapping


_CANONICAL = _canonical_map()


def parse_roman(s: str) -> int:
    """Return the integer spelled by a canonical Roman numeral.

    Accepts only the place-value spelling of an integer from 1 through 3999.
    Any other string, and any non-string, raises ValueError.
    """
    if not isinstance(s, str):
        raise ValueError("Roman numeral must be a string")
    try:
        return _CANONICAL[s]
    except KeyError:
        raise ValueError(f"invalid Roman numeral: {s!r}") from None
