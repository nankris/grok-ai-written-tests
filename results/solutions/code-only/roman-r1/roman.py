"""Parse canonical Roman numerals in the range 1 through 3999."""

_THOUSANDS = ("", "M", "MM", "MMM")
_HUNDREDS = ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM")
_TENS = ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC")
_ONES = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")


def _symbols_longest_first(symbols: tuple[str, ...]) -> tuple[tuple[int, str], ...]:
    """Pair each non-empty place symbol with its value, longest symbol first."""
    pairs = [(value, symbol) for value, symbol in enumerate(symbols) if symbol]
    pairs.sort(key=lambda pair: len(pair[1]), reverse=True)
    return tuple(pairs)


# Thousands, hundreds, tens, and ones use disjoint letters, so a longest match
# in each place is the only candidate for the canonical spelling.
_PLACES = (
    (1000, _symbols_longest_first(_THOUSANDS)),
    (100, _symbols_longest_first(_HUNDREDS)),
    (10, _symbols_longest_first(_TENS)),
    (1, _symbols_longest_first(_ONES)),
)


def parse_roman(s: str) -> int:
    """Return the integer written by a canonical Roman numeral.

    `s` must be the place-value spelling of an integer from 1 through 3999.
    Any other string raises ValueError.
    """
    if not isinstance(s, str):
        raise ValueError("invalid Roman numeral")

    index = 0
    total = 0
    for weight, symbols in _PLACES:
        for value, symbol in symbols:
            if s.startswith(symbol, index):
                index += len(symbol)
                total += value * weight
                break

    if total == 0 or index != len(s):
        raise ValueError("invalid Roman numeral")
    return total
