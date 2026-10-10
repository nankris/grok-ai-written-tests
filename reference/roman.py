_HUNDREDS = ["", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM"]
_TENS = ["", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"]
_ONES = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]


def _canonical(n: int) -> str:
    thousands, rem = divmod(n, 1000)
    hundreds, rem = divmod(rem, 100)
    tens, ones = divmod(rem, 10)
    return ("M" * thousands) + _HUNDREDS[hundreds] + _TENS[tens] + _ONES[ones]


_CANONICAL = { _canonical(n): n for n in range(1, 4000) }


def parse_roman(s: str) -> int:
    if not isinstance(s, str) or s not in _CANONICAL:
        raise ValueError(f"not a canonical Roman numeral: {s!r}")
    return _CANONICAL[s]
