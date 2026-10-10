import pytest

from csvline import parse_line


@pytest.mark.parametrize(
    "line, expected",
    [
        ("a,b,c", ["a", "b", "c"]),
        ("", [""]),
        (",", ["", ""]),
        ("a,", ["a", ""]),
        ("a,,b", ["a", "", "b"]),
        ("a, b", ["a", " b"]),
        ('"a,b",c', ["a,b", "c"]),
        ('"a""b"', ['a"b']),
        ('a,"b""c",d', ["a", 'b"c', "d"]),
        ('""', [""]),
        ('""""', ['"']),
        ('","', [","]),
    ],
)
def test_parse(line, expected):
    assert parse_line(line) == expected


@pytest.mark.parametrize(
    "line",
    ['a,"b', 'a,b"c', '"ab"c', '"a" ,b', '"""', "a,b\n", "a\rb"],
)
def test_malformed(line):
    with pytest.raises(ValueError):
        parse_line(line)
