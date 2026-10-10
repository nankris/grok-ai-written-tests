"""Tests for canonical Roman numeral parsing.

The oracle below is the place-value encoding from the spec, built independently
of parse_roman. A string is valid exactly when it is that encoding of an
integer from 1 through 3999.
"""

import itertools

import pytest

from roman import parse_roman

_THOUSANDS = ("", "M", "MM", "MMM")
_HUNDREDS = ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM")
_TENS = ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC")
_ONES = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")

# Hand-checked (spelling, value) pairs. These do not go through the oracle
# builder, so a swapped token in both places still fails here.
_KNOWN = (
    ("I", 1),
    ("II", 2),
    ("III", 3),
    ("IV", 4),
    ("V", 5),
    ("VI", 6),
    ("VII", 7),
    ("VIII", 8),
    ("IX", 9),
    ("X", 10),
    ("XI", 11),
    ("XII", 12),
    ("XIII", 13),
    ("XIV", 14),
    ("XV", 15),
    ("XVI", 16),
    ("XVII", 17),
    ("XVIII", 18),
    ("XIX", 19),
    ("XX", 20),
    ("XXX", 30),
    ("XL", 40),
    ("XLI", 41),
    ("XLIV", 44),
    ("XLV", 45),
    ("XLIX", 49),
    ("L", 50),
    ("LX", 60),
    ("LXX", 70),
    ("LXXX", 80),
    ("XC", 90),
    ("XCIV", 94),
    ("XCIX", 99),
    ("C", 100),
    ("CI", 101),
    ("CC", 200),
    ("CCC", 300),
    ("CD", 400),
    ("CDXL", 440),
    ("CDXLIV", 444),
    ("CDXLIX", 449),
    ("CDXC", 490),
    ("D", 500),
    ("DI", 501),
    ("DLV", 555),
    ("DC", 600),
    ("DCLXVI", 666),
    ("DCC", 700),
    ("DCCLXXVII", 777),
    ("DCCC", 800),
    ("DCCCLXXXVIII", 888),
    ("CM", 900),
    ("CMI", 901),
    ("CMXL", 940),
    ("CMXLIV", 944),
    ("CMXC", 990),
    ("CMXCIX", 999),
    ("M", 1000),
    ("MI", 1001),
    ("MIV", 1004),
    ("MIX", 1009),
    ("MX", 1010),
    ("MXL", 1040),
    ("MC", 1100),
    ("MCD", 1400),
    ("MCDXLIV", 1444),
    ("MD", 1500),
    ("MDC", 1600),
    ("MCM", 1900),
    ("MCMXC", 1990),
    ("MCMXCIV", 1994),
    ("MCMXCIX", 1999),
    ("MM", 2000),
    ("MMXXIV", 2024),
    ("MMXXVI", 2026),
    ("MMCCXXII", 2222),
    ("MMCDXLIV", 2444),
    ("MMCMXCIX", 2999),
    ("MMM", 3000),
    ("MMMI", 3001),
    ("MMMXC", 3090),
    ("MMMCCCXXXIII", 3333),
    ("MMMCDXLIV", 3444),
    ("MMMDCCCLXXXVIII", 3888),
    ("MMMCM", 3900),
    ("MMMCMXC", 3990),
    ("MMMCMXCIV", 3994),
    ("MMMCMXCVIII", 3998),
    ("MMMCMXCIX", 3999),
)

_INVALID = (
    "",
    " ",
    "  ",
    "\t",
    "\n",
    "\r",
    "\f",
    "\v",
    "I ",
    " I",
    " I ",
    "IV ",
    " IV",
    "IV\n",
    "\nIV",
    "\tX",
    "X\t",
    "I\r",
    "\r\n",
    "X I",
    "MM XX",
    "I I",
    "i",
    "iv",
    "ix",
    "x",
    "l",
    "c",
    "d",
    "m",
    "Iv",
    "iV",
    "McM",
    "Mmm",
    "xix",
    "mmmcmxcix",
    "IIII",
    "IIIII",
    "VIIII",
    "XIIII",
    "XVIIII",
    "XXXX",
    "XXXXX",
    "LXXXX",
    "CCCC",
    "DCCCC",
    "MMMM",
    "MMMMM",
    "MMMMCMXCIX",
    "VV",
    "LL",
    "DD",
    "IIX",
    "XIIX",
    "IIV",
    "IIIV",
    "XXL",
    "XXXL",
    "XXC",
    "CCD",
    "CCCD",
    "CCM",
    "CMM",
    "IC",
    "IL",
    "ID",
    "IM",
    "VX",
    "VL",
    "VC",
    "VD",
    "VM",
    "XD",
    "XM",
    "LC",
    "LD",
    "LM",
    "DM",
    "IVI",
    "IXI",
    "IXV",
    "IXX",
    "IXII",
    "IXXI",
    "IXL",
    "IXC",
    "IXM",
    "XCL",
    "XCM",
    "XCX",
    "XLX",
    "XLXL",
    "XIXIX",
    "IVIV",
    "IXIX",
    "XCXC",
    "CDCD",
    "CMCM",
    "CMC",
    "CMD",
    "CDC",
    "DCD",
    "VIV",
    "LXL",
    "LLX",
    "XLL",
    "MDM",
    "DMC",
    "MIM",
    "IIIX",
    "VVIII",
    "CMXCIXI",
    "MMMCMXCX",
    "MMMCMXCIXI",
    "MMXXVI ",
    " MMXXVI",
    "0",
    "1",
    "12",
    "4",
    "+IV",
    "-IV",
    "IV.",
    "I.V",
    "ABC",
    "A",
    "null",
    "None",
    "roman",
    "Ⅰ",
    "Ⅳ",
    "Ⅹ",
    "Ⅿ",
    "Ⅲ",
    "Ι",  # Greek iota
    "ΙV",
    "VΙ",
    "I\x00",
    "I\x00V",
    "\u00a0I",
    "I\u00a0",
    "\u200b",
    "I\u200bV",
    "Ｍ",  # fullwidth M
    "I" * 4,
    "X" * 4,
    "C" * 4,
    "M" * 4,
    "V" * 2,
    "L" * 2,
    "D" * 2,
    "I" * 20,
    "M" * 15,
)


def _canonical_map() -> dict[str, int]:
    """Every canonical spelling from the spec tables, except 0."""
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
                    assert spelling not in mapping, spelling
                    mapping[spelling] = value
    assert len(mapping) == 3999
    assert set(mapping.values()) == set(range(1, 4000))
    return mapping


_CANONICAL = _canonical_map()
_BY_VALUE = {value: spelling for spelling, value in _CANONICAL.items()}


def test_known_values():
    for spelling, value in _KNOWN:
        assert parse_roman(spelling) == value
        assert type(parse_roman(spelling)) is int


def test_each_place_token():
    for digit, token in enumerate(_ONES):
        if token:
            assert parse_roman(token) == digit
    for digit, token in enumerate(_TENS):
        if token:
            assert parse_roman(token) == digit * 10
    for digit, token in enumerate(_HUNDREDS):
        if token:
            assert parse_roman(token) == digit * 100
    for digit, token in enumerate(_THOUSANDS):
        if token:
            assert parse_roman(token) == digit * 1000


def test_every_canonical_value():
    for spelling, value in _CANONICAL.items():
        assert parse_roman(spelling) == value


def test_bounds():
    assert parse_roman("I") == 1
    assert parse_roman("MMMCMXCIX") == 3999
    assert parse_roman("MMMDCCCLXXXVIII") == 3888


def test_repeated_calls_are_stable():
    assert parse_roman("MCMXCIV") == parse_roman("MCMXCIV") == 1994


@pytest.mark.parametrize("bad", _INVALID)
def test_invalid_strings_raise_value_error(bad):
    assert bad not in _CANONICAL
    with pytest.raises(ValueError):
        parse_roman(bad)


def test_non_strings_raise_value_error():
    for bad in (None, 1, 4, 3.14, b"IV", bytearray(b"X"), ["IV"], ("IV",), True, False):
        with pytest.raises(ValueError):
            parse_roman(bad)


def test_other_ascii_letters_and_digits():
    valid_singles = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if ch in valid_singles:
            assert parse_roman(ch) == valid_singles[ch]
        else:
            with pytest.raises(ValueError):
                parse_roman(ch)
    for ch in "abcdefghijklmnopqrstuvwxyz0123456789":
        with pytest.raises(ValueError):
            parse_roman(ch)
    for ch in " .,;:!?-_/\\'\"()[]{}@#$%^&*+=<>~`":
        with pytest.raises(ValueError):
            parse_roman(ch)


def test_short_strings_over_roman_alphabet():
    """Every string of length 1..4 made from I,V,X,L,C,D,M is canonical or rejected."""
    alphabet = "IVXLCDM"
    for length in range(1, 5):
        for chars in itertools.product(alphabet, repeat=length):
            spelling = "".join(chars)
            if spelling in _CANONICAL:
                assert parse_roman(spelling) == _CANONICAL[spelling]
            else:
                with pytest.raises(ValueError):
                    parse_roman(spelling)


def test_prefix_and_suffix_mutations():
    extras = ("I", "V", "X", "L", "C", "D", "M", "i", " ", "A", "1")
    for value in range(1, 4000):
        spelling = _BY_VALUE[value]
        mutants = [extra + spelling for extra in extras]
        mutants += [spelling + extra for extra in extras]
        if len(spelling) > 1:
            mutants.append(spelling[1:])
            mutants.append(spelling[:-1])
        for mutant in mutants:
            if mutant not in _CANONICAL:
                with pytest.raises(ValueError):
                    parse_roman(mutant)


def test_case_and_whitespace_around_known_values():
    for spelling, _value in _KNOWN:
        for mutant in (
            spelling.lower(),
            " " + spelling,
            spelling + " ",
            "\t" + spelling,
            spelling + "\n",
            spelling[:1].lower() + spelling[1:] if spelling else spelling,
        ):
            if mutant == spelling:
                continue
            if mutant not in _CANONICAL:
                with pytest.raises(ValueError):
                    parse_roman(mutant)
