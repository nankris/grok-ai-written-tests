"""Tests for the one-line comma-separated parser in csvline.py."""

import pytest

from csvline import parse_line


def encode_field(field: str) -> str:
    """Encode one field in this dialect (no newlines allowed)."""
    if '"' in field or "," in field:
        return '"' + field.replace('"', '""') + '"'
    return field


def encode_line(fields: list[str]) -> str:
    return ",".join(encode_field(field) for field in fields)


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("", [""]),
        (",", ["", ""]),
        (",,", ["", "", ""]),
        (",,,", ["", "", "", ""]),
        ("a", ["a"]),
        ("a,b", ["a", "b"]),
        ("a,b,c", ["a", "b", "c"]),
        ("a,", ["a", ""]),
        (",a", ["", "a"]),
        (",a,", ["", "a", ""]),
        ("a,,b", ["a", "", "b"]),
        (",,", ["", "", ""]),
        ("a,,,b,,", ["a", "", "", "b", "", ""]),
        (",,a,,", ["", "", "a", "", ""]),
        ("1,2,3", ["1", "2", "3"]),
        ("true,false", ["true", "false"]),
        ("None,null", ["None", "null"]),
    ],
)
def test_unquoted_fields_and_empty_fields(line: str, expected: list[str]) -> None:
    assert parse_line(line) == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (" ", [" "]),
        ("   ", ["   "]),
        (" a ", [" a "]),
        ("a, b", ["a", " b"]),
        (" a,b ", [" a", "b "]),
        ("a ,b", ["a ", "b"]),
        (" a , b ", [" a ", " b "]),
        ("   ,   ", ["   ", "   "]),
        ("\t", ["\t"]),
        ("a\tb", ["a\tb"]),
        ("a,\tb", ["a", "\tb"]),
        (" \t , \t ", [" \t ", " \t "]),
        ("a\fb", ["a\fb"]),
        ("a\vb", ["a\vb"]),
        ("a\x00b", ["a\x00b"]),
        ("héllo,世界", ["héllo", "世界"]),
        (" spaced , more ", [" spaced ", " more "]),
    ],
)
def test_spaces_and_non_comma_characters_are_significant(line: str, expected: list[str]) -> None:
    assert parse_line(line) == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ('""', [""]),
        ('"",""', ["", ""]),
        ('"","",""', ["", "", ""]),
        ('"hello"', ["hello"]),
        ('"hello, world"', ["hello, world"]),
        ('"a","b"', ["a", "b"]),
        ('"a,b",c', ["a,b", "c"]),
        ('a,"b,c"', ["a", "b,c"]),
        ('"a","b","c"', ["a", "b", "c"]),
        ('"abc",', ["abc", ""]),
        (',"abc"', ["", "abc"]),
        (',"abc",', ["", "abc", ""]),
        ('"a",,"b"', ["a", "", "b"]),
        ('a,"",b', ["a", "", "b"]),
        (',"",', ["", "", ""]),
        ('" a "', [" a "]),
        ('"a b","c d"', ["a b", "c d"]),
        ('" a , b "', [" a , b "]),
        ('",,,"', [",,,"]),
        ('"a,,b"', ["a,,b"]),
        ('x,",,",y', ["x", ",,", "y"]),
        ('","', [","]),
        ('"a,"', ["a,"]),
        (',"a",', ["", "a", ""]),
        ('"a\tb"', ["a\tb"]),
        ('"héllo, 世界"', ["héllo, 世界"]),
        ('"a\\b"', ["a\\b"]),
        ('"\\"', ["\\"]),
    ],
)
def test_quoted_fields(line: str, expected: list[str]) -> None:
    assert parse_line(line) == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ('"a"""', ['a"']),
        ('""""', ['"']),
        ('""""""', ['""']),
        ('"a""b"', ['a"b']),
        ('"""a"', ['"a']),
        ('"a"""', ['a"']),
        ('"say ""hi"""', ['say "hi"']),
        ('"say ""hello, world"""', ['say "hello, world"']),
        ('"a""""b"', ['a""b']),
        ('a,"b""c",d', ["a", 'b"c', "d"]),
        ('"a""",b', ['a"', "b"]),
        ('"""",""', ['"', ""]),
        ('"",""""', ["", '"']),
        ('"""","x"', ['"', "x"]),
        ('""",","x"', ['",', "x"]),
        ('""","', ['",']),
        ('"a"",b"', ['a",b']),
        ('"say ""hi"", friend"', ['say "hi", friend']),
        ('""""', ['"']),
        ('" """', [' "']),
        ('""" "', ['" ']),
        ('"a""b""c"', ['a"b"c']),
        ('"","""",""', ["", '"', ""]),
    ],
)
def test_escaped_quotes(line: str, expected: list[str]) -> None:
    assert parse_line(line) == expected


def test_backslash_is_not_an_escape() -> None:
    assert parse_line("a\\,b") == ["a\\", "b"]
    assert parse_line("a\\\\b") == ["a\\\\b"]
    assert parse_line('"a\\b\\c"') == ["a\\b\\c"]
    # A backslash before a quote does not escape it: `"a\"` closes after the quote.
    assert parse_line('"a\\"') == ["a\\"]
    # `"a\""` is open + a + backslash + a doubled quote, and never closes.
    with pytest.raises(ValueError):
        parse_line('"a\\""')


@pytest.mark.parametrize(
    "line",
    [
        "\n",
        "\r",
        "\r\n",
        "\n\r",
        "a\n",
        "a\r",
        "\nb",
        "\rb",
        "a\nb",
        "a\rb",
        "a\r\nb",
        "a\n\rb",
        "\na,b",
        "a,b\n",
        "a,\nb",
        '"a\nb"',
        '"a\rb"',
        '"\n"',
        '"\r"',
        '"a\r\nb"',
        'a,"b\nc"',
        "\n\n",
    ],
)
def test_newline_or_carriage_return_is_rejected(line: str) -> None:
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize(
    "line",
    [
        '"',
        '"a',
        '"a""',
        '"""',
        '"""""',
        '"abc',
        'a,"b',
        '"",",',
        '"a"",',
        ',"',
        ',"""',
        '"a""b""',
        '"""a""',
        '"missing end',
        'a,"unterminated',
        '""","b',
    ],
)
def test_unclosed_quoted_field_is_rejected(line: str) -> None:
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize(
    "line",
    [
        '"a"b',
        '"a" b',
        '"a"b,c',
        '"a"bc,d',
        '"abc"def',
        '""a',
        '"a" ,b',
        '"a"\t,b',
        '"a" ,',
        'a,"b"c',
        'a,"b"c,d',
        '"a"b"',
        '"" ',
        '"a"b"',
        ' "a"',
        'a, "b"',
        '"a" , "b"',
        '""x""',
        '"hello"world',
        'a,"b" ',
        '"a"\t',
        ',"a"b',
        '"a""",b"',
    ],
)
def test_characters_after_closing_quote_are_rejected(line: str) -> None:
    with pytest.raises(ValueError):
        parse_line(line)


@pytest.mark.parametrize(
    "line",
    [
        'a"',
        'a"b',
        '"b',
        'a,b"',
        'a,b"c',
        'a",b',
        'a" ,b',
        ' "a"',
        'a, "b"',
        'ab"cd,ef',
    ],
)
def test_quote_in_unquoted_field_is_rejected(line: str) -> None:
    with pytest.raises(ValueError):
        parse_line(line)


def test_quote_starts_a_quoted_field_only_at_field_start() -> None:
    """A quote is syntax only when it is the first character of a field."""
    assert parse_line('""') == [""]
    assert parse_line('"",a') == ["", "a"]
    with pytest.raises(ValueError):
        parse_line(' ""')
    with pytest.raises(ValueError):
        parse_line('a""')


def test_unicode_line_separators_are_ordinary_characters() -> None:
    """Only \\n and \\r are rejected; other unicode separators stay in the field."""
    assert parse_line("a\u2028b") == ["a\u2028b"]
    assert parse_line("a\u2029b") == ["a\u2029b"]
    assert parse_line("a\u0085b") == ["a\u0085b"]
    assert parse_line('"a\u2028b"') == ["a\u2028b"]


def test_only_ascii_double_quote_delimits() -> None:
    curly = "\u201c"
    assert parse_line(f"a{curly}b") == [f"a{curly}b"]
    assert parse_line(f"{curly}hello{curly}") == [f"{curly}hello{curly}"]


def test_many_fields_keep_order() -> None:
    fields = [f"f{i}" for i in range(50)]
    fields[3] = ""
    fields[10] = "has space"
    fields[17] = 'say "hi"'
    fields[20] = "a,b"
    fields[40] = ""
    assert parse_line(encode_line(fields)) == fields


@pytest.mark.parametrize(
    "fields",
    [
        [""],
        ["", ""],
        ["", "", ""],
        ["a"],
        ["a", "b", "c"],
        ["a", "", "b"],
        ["", "a", ""],
        [" a ", " b "],
        ["a,b", "c"],
        ['say "hi"', "there"],
        ['"', '"'],
        ['""', "x"],
        ['a"b"c', "d,e,f"],
        ["hello, world", 'he said "go"', "", "z"],
        [",", ",", ","],
        ['","', "plain"],
        ["\\", "a\\b", "\\,"],
        ["héllo", "世界", " "],
        ["\t", "a\tb"],
        ['leading " and , comma', "tail"],
        ["a" * 100, "b" * 100],
        ['"' * 20, "," * 15, ""],
    ],
)
def test_round_trip(fields: list[str]) -> None:
    assert parse_line(encode_line(fields)) == fields


def test_each_call_returns_a_new_list() -> None:
    first = parse_line("a,b")
    second = parse_line("a,b")
    assert first == ["a", "b"]
    assert first == second
    assert first is not second
    first.append("c")
    assert parse_line("a,b") == ["a", "b"]


def test_does_not_strip_or_interpret_backslash_sequences() -> None:
    raw = "\\\\n,\\\\r,\\\\t"
    assert parse_line(raw) == ["\\\\n", "\\\\r", "\\\\t"]
