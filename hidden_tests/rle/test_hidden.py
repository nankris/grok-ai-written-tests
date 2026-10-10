import pytest

from rle import decode, encode


@pytest.mark.parametrize(
    "text, encoded",
    [
        ("", ""),
        ("a", "a"),
        ("aaa", "a3"),
        ("aabbbcc", "a2b3c2"),
        ("1", r"\11"),
        ("a11b", r"a\12b"),
        ("\\", r"\\1"),
        ("\\\\", r"\\2"),
        ("0000000000", r"\010"),
        ("aaaaaaaaaa", "a10"),
        ("ééé", "é3"),
        ("9a9", r"\91a\91"),
        ("  ", " 2"),
    ],
)
def test_encode_and_roundtrip(text, encoded):
    assert encode(text) == encoded
    assert decode(encoded) == text


def test_non_maximal_tokens_still_decode():
    assert decode("a2a") == "aaa"
    assert decode("abc") == "abc"


def test_roundtrip_mixed():
    for sample in ("12a", "a1b2c3", "\\1\\", "a" * 12):
        assert decode(encode(sample)) == sample


@pytest.mark.parametrize(
    "encoded",
    ["a1", "a01", "5", "\\", "\\1", "\\00", "\\101"],
)
def test_invalid(encoded):
    with pytest.raises(ValueError):
        decode(encoded)
