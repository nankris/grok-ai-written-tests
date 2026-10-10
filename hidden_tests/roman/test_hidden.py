import pytest

from roman import parse_roman


@pytest.mark.parametrize(
    "text, value",
    [
        ("I", 1),
        ("IV", 4),
        ("IX", 9),
        ("XL", 40),
        ("XC", 90),
        ("CD", 400),
        ("CM", 900),
        ("MCMXCIV", 1994),
        ("MMXXVI", 2026),
        ("MMMCMXCIX", 3999),
    ],
)
def test_canonical_values(text, value):
    assert parse_roman(text) == value


@pytest.mark.parametrize(
    "text",
    ["", "IIII", "IC", "IIX", "IXI", "DM", "MMMM", "iv", " III", "CDCD"],
)
def test_rejects_non_canonical(text):
    with pytest.raises(ValueError):
        parse_roman(text)
