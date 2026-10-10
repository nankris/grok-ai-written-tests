"""Tests for the run-length codec described in spec.md.

Canonical encode walks maximal runs. Digits and backslashes are always
escaped and always carry a length. Other characters omit a length of 1.
Decode accepts any concatenation of valid tokens, including neighbours
that repeat the same character, and rejects anything else with ValueError.
"""

import random

import pytest

from rle import decode, encode

BACKSLASH = "\\"


def test_empty_string() -> None:
    assert encode("") == ""
    assert decode("") == ""


@pytest.mark.parametrize("ch", [chr(i) for i in range(128)])
def test_ascii_canonical_singles_pairs_and_illegal_lengths(ch: str) -> None:
    """Every ASCII character follows either the escaped rule or the normal rule."""
    if ch == BACKSLASH or "0" <= ch <= "9":
        assert encode(ch) == BACKSLASH + ch + "1"
        assert encode(ch * 2) == BACKSLASH + ch + "2"
        assert decode(BACKSLASH + ch + "1") == ch
        assert decode(BACKSLASH + ch + "2") == ch * 2
        with pytest.raises(ValueError):
            decode(ch)
        with pytest.raises(ValueError):
            decode(BACKSLASH + ch)
        with pytest.raises(ValueError):
            decode(BACKSLASH + ch + "0")
        with pytest.raises(ValueError):
            decode(BACKSLASH + ch + "01")
    else:
        assert encode(ch) == ch
        assert encode(ch * 2) == ch + "2"
        assert decode(ch) == ch
        assert decode(ch + "2") == ch * 2
        with pytest.raises(ValueError):
            decode(ch + "1")
        with pytest.raises(ValueError):
            decode(ch + "0")
        with pytest.raises(ValueError):
            decode(ch + "01")
        with pytest.raises(ValueError):
            decode(ch + "00")


@pytest.mark.parametrize("n", [1, 2, 9, 10, 11, 99, 100, 1000])
def test_normal_run_omits_length_one_and_writes_decimal(n: int) -> None:
    original = "q" * n
    if n == 1:
        assert encode(original) == "q"
    else:
        assert encode(original) == "q" + str(n)
    assert decode(encode(original)) == original


@pytest.mark.parametrize("n", [1, 2, 9, 10, 11, 99, 100, 1000])
@pytest.mark.parametrize("ch", ["0", "1", "5", "9", BACKSLASH])
def test_special_run_always_writes_length(ch: str, n: int) -> None:
    assert encode(ch * n) == BACKSLASH + ch + str(n)
    assert decode(BACKSLASH + ch + str(n)) == ch * n


def test_maximal_runs_not_global_counts() -> None:
    assert encode("aba") == "aba"
    assert encode("aaabaaa") == "a3ba3"
    assert encode("aabbaa") == "a2b2a2"
    assert encode("aaabbc") == "a3b2c"
    assert encode("aabbcc") == "a2b2c2"
    assert encode("abc") == "abc"
    assert encode("aabba") == "a2b2a"


def test_crlf_are_separate_characters() -> None:
    assert encode("\r\n") == "\r\n"
    assert encode("\r\n" * 3) == "\r\n" * 3
    assert encode("\r\r\n\n") == "\r2\n2"
    assert decode("\r2\n2") == "\r\r\n\n"


def test_controls_null_and_space() -> None:
    assert encode("\x00") == "\x00"
    assert encode("\x00" * 4) == "\x004"
    assert decode("\x004") == "\x00" * 4
    assert encode("\x01\x02\x01") == "\x01\x02\x01"
    assert encode(" ") == " "
    assert encode("   ") == " 3"
    assert decode(" 3") == "   "
    assert decode("a 2") == "a  "
    assert decode("a2 ") == "aa "
    assert encode("a  ") == "a 2"
    assert encode("aa ") == "a2 "


def test_digit_and_backslash_placement() -> None:
    assert encode("a1") == "a" + BACKSLASH + "11"
    assert encode("1a") == BACKSLASH + "11" + "a"
    assert encode("10") == BACKSLASH + "11" + BACKSLASH + "01"
    assert encode("a0b") == "a" + BACKSLASH + "01" + "b"
    assert encode("00a11") == BACKSLASH + "02" + "a" + BACKSLASH + "12"
    assert encode("111222") == BACKSLASH + "13" + BACKSLASH + "23"
    assert encode("0123456789") == "".join(BACKSLASH + digit + "1" for digit in "0123456789")
    assert encode("a\\") == "a" + BACKSLASH + BACKSLASH + "1"
    assert encode("\\a") == BACKSLASH + BACKSLASH + "1" + "a"
    assert encode("a\\a") == "a" + BACKSLASH + BACKSLASH + "1" + "a"
    assert encode("\\\\a") == BACKSLASH + BACKSLASH + "2" + "a"
    assert encode("a\\\\") == "a" + BACKSLASH + BACKSLASH + "2"
    assert encode("1\\") == BACKSLASH + "11" + BACKSLASH + BACKSLASH + "1"
    assert encode("\\1") == BACKSLASH + BACKSLASH + "1" + BACKSLASH + "11"
    assert encode("\\1\\") == BACKSLASH + BACKSLASH + "1" + BACKSLASH + "11" + BACKSLASH + BACKSLASH + "1"
    assert encode("\\a\\a") == (BACKSLASH + BACKSLASH + "1" + "a") * 2
    assert decode(encode("a1")) == "a1"
    assert decode(encode("10")) == "10"
    assert decode(encode("\\1\\")) == "\\1\\"


def test_confusable_zero_and_one_lengths() -> None:
    """The digit after a backslash is the run character; following digits are the length."""
    assert encode("0") == BACKSLASH + "01"
    assert encode("00") == BACKSLASH + "02"
    assert encode("0" * 10) == BACKSLASH + "010"
    assert encode("0" * 11) == BACKSLASH + "011"
    assert decode(BACKSLASH + "01") == "0"
    assert decode(BACKSLASH + "02") == "00"
    assert decode(BACKSLASH + "010") == "0" * 10
    assert decode(BACKSLASH + "011") == "0" * 11

    assert encode("1") == BACKSLASH + "11"
    assert encode("1" * 10) == BACKSLASH + "110"
    assert encode("1" * 11) == BACKSLASH + "111"
    assert encode("1" * 111) == BACKSLASH + "1111"
    assert decode(BACKSLASH + "11") == "1"
    assert decode(BACKSLASH + "110") == "1" * 10
    assert decode(BACKSLASH + "111") == "1" * 11
    assert decode(BACKSLASH + "1111") == "1" * 111
    assert decode(BACKSLASH + "120") == "1" * 20

    assert encode(BACKSLASH) == BACKSLASH + BACKSLASH + "1"
    assert encode(BACKSLASH * 10) == BACKSLASH + BACKSLASH + "10"
    assert encode(BACKSLASH * 11) == BACKSLASH + BACKSLASH + "11"
    assert decode(BACKSLASH + BACKSLASH + "1") == BACKSLASH
    assert decode(BACKSLASH + BACKSLASH + "10") == BACKSLASH * 10
    assert decode(BACKSLASH + BACKSLASH + "11") == BACKSLASH * 11


def test_greedy_length_on_normal_characters() -> None:
    assert decode("a10") == "a" * 10
    assert decode("a11") == "a" * 11
    assert decode("a21") == "a" * 21
    assert decode("a10b3") == "a" * 10 + "bbb"
    assert decode("b10c10") == "b" * 10 + "c" * 10
    assert decode("ab2") == "abb"
    assert decode("a2b") == "aab"
    assert decode("a2b3c") == "aabbbc"
    assert decode("z9") == "z" * 9
    assert decode("a100") == "a" * 100
    assert decode("a23") == "a" * 23


def test_noncanonical_but_valid_concatenations() -> None:
    assert decode("aa") == "aa"
    assert decode("aaa") == "aaa"
    assert decode("a" * 50) == "a" * 50
    assert decode("a2a") == "aaa"
    assert decode("a2a2") == "aaaa"
    assert decode("a2a3") == "aaaaa"
    assert decode("a2b2a2") == "aabbaa"
    assert decode(BACKSLASH + "11" + BACKSLASH + "11") == "11"
    assert decode(BACKSLASH + "11" + BACKSLASH + "12") == "111"
    assert decode(BACKSLASH + BACKSLASH + "1" + BACKSLASH + BACKSLASH + "1") == BACKSLASH * 2
    assert decode(BACKSLASH + BACKSLASH + "1" + BACKSLASH + BACKSLASH + "2") == BACKSLASH * 3
    assert decode("你你") == "你你"
    assert decode("²2²") == "²²²"

    assert encode(decode("aa")) == "a2"
    assert encode(decode("aaa")) == "a3"
    assert encode(decode("a" * 50)) == "a50"
    assert encode(decode("a2a")) == "a3"
    assert encode(decode("a2a2")) == "a4"
    assert encode(decode("a2a3")) == "a5"
    assert encode(decode(BACKSLASH + "11" + BACKSLASH + "11")) == BACKSLASH + "12"
    assert encode(decode(BACKSLASH + "11" + BACKSLASH + "12")) == BACKSLASH + "13"
    assert encode(decode(BACKSLASH + BACKSLASH + "1" + BACKSLASH + BACKSLASH + "1")) == (
        BACKSLASH + BACKSLASH + "2"
    )
    assert encode(decode("你你")) == "你2"
    assert encode(decode("²2²")) == "²3"


def test_unicode_is_not_normalized_or_treated_as_ascii_digits() -> None:
    composed = "é"
    decomposed = "e\u0301"
    assert composed != decomposed
    assert encode(composed) == composed
    assert encode(decomposed) == decomposed
    assert encode(composed) != encode(decomposed)
    assert decode(encode(composed)) == composed
    assert decode(encode(decomposed)) == decomposed
    assert encode(composed * 2) == composed + "2"
    # Repeating the decomposed pair alternates e and the combining mark.
    assert encode(decomposed * 2) == decomposed * 2
    assert encode("ee\u0301\u0301") == "e2\u03012"

    assert encode("你") == "你"
    assert encode("你" * 3) == "你3"
    assert decode("你3") == "你" * 3
    assert decode("你你") == "你你"

    assert encode("🙂" * 2) == "🙂2"
    assert decode("🙂2") == "🙂🙂"
    assert decode(encode("\U0001F600" * 4)) == "\U0001F600" * 4
    assert decode(encode("\U0010FFFF" * 3)) == "\U0010FFFF" * 3
    assert decode(encode("\ud800\udc00")) == "\ud800\udc00"

    # Unicode digits and a fullwidth backslash are ordinary characters.
    for ch, run in (("²", 2), ("０", 2), ("٠", 3), ("＼", 2), ("\u00a0", 2)):
        assert encode(ch) == ch
        assert encode(ch * run) == ch + str(run)
        assert decode(ch + str(run)) == ch * run
        with pytest.raises(ValueError):
            decode(ch + "1")
        with pytest.raises(ValueError):
            decode(BACKSLASH + ch)
        with pytest.raises(ValueError):
            decode(BACKSLASH + ch + "1")

    assert decode("a²") == "a²"
    assert decode("a2") == "aa"
    assert encode("a²") == "a²"
    assert encode("aa") == "a2"
    # One escaped ASCII '1', then a fullwidth digit as its own character.
    assert decode(BACKSLASH + "11" + "２") == "1２"
    with pytest.raises(ValueError):
        decode(BACKSLASH + "1" + "２")


def test_symbols_around_the_digit_range() -> None:
    assert encode("/") == "/"
    assert encode(":") == ":"
    assert encode("//") == "/2"
    assert encode("::") == ":2"
    assert decode("/2") == "//"
    assert decode("a+2") == "a++"
    assert decode("a+10") == "a" + "+" * 10
    assert encode("a++") == "a+2"
    assert encode("-") == "-"
    assert encode("--") == "-2"
    assert decode("-2") == "--"


def test_mixed_canonical_string() -> None:
    original = "a" * 3 + "1" * 3 + BACKSLASH * 2 + "b" * 2 + "9" + "c" * 2 + "\n" * 2 + "你" * 2 + "0"
    expected = (
        "a3"
        + BACKSLASH
        + "13"
        + BACKSLASH
        + BACKSLASH
        + "2"
        + "b2"
        + BACKSLASH
        + "91"
        + "c2"
        + "\n2"
        + "你2"
        + BACKSLASH
        + "01"
    )
    assert encode(original) == expected
    assert decode(expected) == original
    assert decode(encode(original)) == original


def test_plain_unique_characters_roundtrip_unchanged() -> None:
    original = "abcXYZ!@#你🙂é²０٠＼ \n\t"
    assert encode(original) == original
    assert decode(original) == original


@pytest.mark.parametrize(
    "encoded",
    [
        "a0",
        "a1",
        "a01",
        "a02",
        "a00",
        "a0010",
        "1",
        "0",
        "9",
        "42",
        "5a",
        "0123",
        BACKSLASH,
        BACKSLASH * 2,
        BACKSLASH + "1",
        BACKSLASH + "0",
        BACKSLASH + "9",
        BACKSLASH + "a",
        BACKSLASH + "a2",
        BACKSLASH * 2 + "a",
        BACKSLASH + "10",
        BACKSLASH * 2 + "0",
        BACKSLASH + "00",
        BACKSLASH + "101",
        BACKSLASH * 2 + "01",
        BACKSLASH + "002",
        BACKSLASH + "102",
        "a" + BACKSLASH,
        "a2" + BACKSLASH,
        "a2" + BACKSLASH + "a",
        "a2" + BACKSLASH + "1",
        "a1b2",
        "aa1",
        "b0",
        "a2b1",
        "a2b01",
        BACKSLASH + "12" + "a1",
        BACKSLASH + " ",
        BACKSLASH + "\n",
        BACKSLASH + "x41",
        "你1",
        " 1",
        " 0",
        " 01",
        "²1",
        "²0",
        BACKSLASH + "²",
        BACKSLASH + "²1",
        BACKSLASH + "０1",
        BACKSLASH + "٠1",
        BACKSLASH + "1" + "２",
        "-1",
        "-0",
        "a2" + BACKSLASH + "12" + BACKSLASH,
        BACKSLASH + "11" + BACKSLASH,
        BACKSLASH + "01" + "a1",
        BACKSLASH * 2 + "2" + BACKSLASH + "a",
        "a2c1d3",
        "a10b1",
        "🙂1",
        "＼1",
    ],
)
def test_decode_rejects_invalid_token_stream(encoded: str) -> None:
    with pytest.raises(ValueError):
        decode(encoded)


def test_decode_rejects_are_value_errors_not_index_errors() -> None:
    for encoded in (BACKSLASH, BACKSLASH + "1", BACKSLASH * 2, "1", "a1", "a0"):
        try:
            decode(encoded)
        except ValueError:
            continue
        except Exception as exc:  # pragma: no cover - assertion path
            pytest.fail(f"decode({encoded!r}) raised {type(exc).__name__}, expected ValueError")
        else:
            pytest.fail(f"decode({encoded!r}) did not raise")


def test_random_roundtrip_and_canonical_fixed_point() -> None:
    rng = random.Random(12345)
    alphabet = [chr(i) for i in range(32, 127)] + [
        "你",
        "🙂",
        "é",
        "\u0301",
        "²",
        "０",
        "٠",
        "＼",
        "\u00a0",
        "\x00",
        "\n",
        "\ud800",
        "\U0001F600",
        "\U0010FFFF",
    ]
    for _ in range(200):
        original = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 50)))
        encoded = encode(original)
        assert decode(encoded) == original
        assert encode(decode(encoded)) == encoded


def test_random_explicit_runs_roundtrip() -> None:
    rng = random.Random(99)
    alphabet = ["a", "b", "Z", "0", "1", "9", BACKSLASH, "你", "²", " ", "\n", "🙂", "０"]
    for _ in range(80):
        parts = []
        for _run in range(rng.randint(0, 12)):
            parts.append(rng.choice(alphabet) * rng.randint(1, 40))
        original = "".join(parts)
        encoded = encode(original)
        assert decode(encoded) == original
        assert encode(original) == encoded


def test_long_special_and_normal_runs() -> None:
    assert encode("7" * 1000) == BACKSLASH + "71000"
    assert decode(BACKSLASH + "71000") == "7" * 1000
    assert encode(BACKSLASH * 1000) == BACKSLASH + BACKSLASH + "1000"
    assert decode(BACKSLASH + BACKSLASH + "1000") == BACKSLASH * 1000
    original = "a" * 50 + "1" * 17 + BACKSLASH * 23 + "你" * 8 + "b" * 2 + "0" * 11 + "²" * 3
    expected = (
        "a50"
        + BACKSLASH
        + "117"
        + BACKSLASH
        + BACKSLASH
        + "23"
        + "你8"
        + "b2"
        + BACKSLASH
        + "011"
        + "²3"
    )
    assert encode(original) == expected
    assert decode(expected) == original
