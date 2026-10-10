import pytest

from wrap import wrap_text


@pytest.mark.parametrize(
    "text, width, expected",
    [
        ("hello world", 5, "hello\nworld"),
        ("a b c", 5, "a b c"),
        ("a b c", 3, "a b\nc"),
        ("aaaa bb c", 6, "aaaa\nbb c"),
        ("hi world", 5, "hi\nworld"),
        ("hello", 3, "hello"),
        ("abcd efghij kl", 4, "abcd\nefghij\nkl"),
        ("hi   world", 20, "hi world"),
        ("hi\n\nworld", 20, "hi world"),
        ("hi\tworld", 20, "hi world"),
        ("  hello world  ", 11, "hello world"),
        ("", 5, ""),
        (" \n\t ", 5, ""),
        ("a b", 1, "a\nb"),
        ("hello, world", 8, "hello,\nworld"),
    ],
)
def test_wrap(text, width, expected):
    assert wrap_text(text, width) == expected


def test_no_trailing_newline():
    assert wrap_text("one two", 3) == "one\ntwo"


@pytest.mark.parametrize("width", [0, -1, 1.0])
def test_bad_width(width):
    with pytest.raises(ValueError):
        wrap_text("a", width)
