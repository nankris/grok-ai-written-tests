"""Tests for greedy word wrap.

The layout is unique: split on every Python whitespace run, pack left to
right, and break only when the next word does not fit.
"""

import random

import pytest

from wrap import wrap_text

# Every code point Python treats as whitespace (str.isspace / str.split).
PYTHON_WHITESPACE = [chr(i) for i in range(0x110000) if chr(i).isspace()]

# Not whitespace: must stay inside a word (format / control / soft hyphen).
NON_BREAKING = [
    "\u00ad",  # soft hyphen
    "\u180e",  # mongolian vowel separator (not whitespace in Python 3)
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u2060",  # word joiner
    "\ufeff",  # bom / zero-width no-break space
]


def assert_valid_wrap(text: str, width: int, result: str) -> None:
    """Check result against the spec rules for this text and width."""
    words = text.split()
    assert isinstance(result, str)
    if not words:
        assert result == ""
        return

    assert result != ""
    assert not result.endswith("\n")
    assert not result.startswith("\n")
    assert "\r" not in result

    lines = result.split("\n")
    flat: list[str] = []
    for index, line in enumerate(lines):
        assert line != ""
        assert line == line.strip(" ")
        parts = line.split(" ")
        assert all(parts)  # single spaces only; no empty slots
        built = parts[0]
        for word in parts[1:]:
            assert len(built) + 1 + len(word) <= width
            built = f"{built} {word}"
        assert built == line
        if index < len(lines) - 1:
            next_word = lines[index + 1].split(" ", 1)[0]
            assert len(line) + 1 + len(next_word) > width
        flat.extend(parts)
    assert flat == words


@pytest.mark.parametrize(
    ("text", "width", "expected"),
    [
        ("", 5, ""),
        ("   ", 5, ""),
        ("\n\t\n", 3, ""),
        ("\r\n\r\n", 4, ""),
        ("hello", 5, "hello"),
        ("hello", 4, "hello"),
        ("hello", 10, "hello"),
        ("  hello  ", 5, "hello"),
        ("a", 1, "a"),
        ("ab", 1, "ab"),
        ("a b", 3, "a b"),
        ("a b", 2, "a\nb"),
        ("a b", 1, "a\nb"),
        ("a b c", 1, "a\nb\nc"),
        ("a bb c", 1, "a\nbb\nc"),
        ("ab c", 4, "ab c"),
        ("ab cd", 4, "ab\ncd"),
        ("ab cd", 5, "ab cd"),
        ("abc d", 3, "abc\nd"),
        ("abc d", 4, "abc d"),
        ("a bb c", 6, "a bb c"),
        ("a bb c", 5, "a bb\nc"),
        ("aa bb cc", 5, "aa bb\ncc"),
        ("aaaaa bb cc", 8, "aaaaa bb\ncc"),
        ("x xx xx", 5, "x xx\nxx"),
        ("aaa bb cc ddd", 6, "aaa bb\ncc ddd"),
        ("aaaa b c", 5, "aaaa\nb c"),
        ("a b c d e", 9, "a b c d e"),
        ("a b c d e", 8, "a b c d\ne"),
        ("a b c d e", 3, "a b\nc d\ne"),
        ("one two three four", 10, "one two\nthree four"),
        ("one two three four", 8, "one two\nthree\nfour"),
        ("one two three four", 3, "one\ntwo\nthree\nfour"),
        (
            "The quick brown fox jumps over the lazy dog",
            15,
            "The quick brown\njumps over the\nlazy dog",
        ),
        (
            "The quick brown fox jumps over the lazy dog",
            10,
            "The quick\nbrown\njumps over\nthe lazy\ndog",
        ),
        (
            "The quick brown fox jumps over the lazy dog",
            9,
            "The quick\nbrown\njumps\nover the\nlazy dog",
        ),
        ("abcdef g", 3, "abcdef\ng"),
        ("abcdef ghij", 3, "abcdef\nghij"),
        ("short toolong short", 6, "short\ntoolong\nshort"),
        ("toolong a b", 3, "toolong\na b"),
        ("a bb ccc dddd e", 3, "a\nbb\nccc\ndddd\ne"),
        ("aaaa bbb cc", 1, "aaaa\nbbb\ncc"),
        ("zz yy", 1, "zz\nyy"),
        ("   supercalifragilistic   ", 5, "supercalifragilistic"),
        ("  abcdef  ghijkl  ", 3, "abcdef\nghijkl"),
        ("alpha    beta\t\tgamma", 11, "alpha beta\ngamma"),
        ("alpha    beta\t\tgamma", 10, "alpha beta\ngamma"),
        ("alpha    beta\t\tgamma", 9, "alpha\nbeta\ngamma"),
        (" \t\nhello \f\v world\r\n", 11, "hello world"),
        ("hello\nworld", 20, "hello world"),
        ("hello\nworld", 5, "hello\nworld"),
        ("hi\nthere", 8, "hi there"),
        ("a\nb\nc\nd", 7, "a b c d"),
        ("a\n\n\nb", 10, "a b"),
        ("  a \n b \t c  ", 100, "a b c"),
        ("hello-world", 5, "hello-world"),
        ("abc-def-ghij", 6, "abc-def-ghij"),
        ("abc def-ghij", 6, "abc\ndef-ghij"),
        ("hello, world!", 13, "hello, world!"),
        ("hello, world!", 12, "hello,\nworld!"),
        ("(hello) [world]", 8, "(hello)\n[world]"),
        ("... --- ...", 7, "... ---\n..."),
        ("... --- ...", 3, "...\n---\n..."),
        ('"hello" world', 7, '"hello"\nworld'),
        ("don't stop", 20, "don't stop"),
        ("don't stop", 6, "don't\nstop"),
        ("1,000 2,000", 11, "1,000 2,000"),
        ("1,000 2,000", 10, "1,000\n2,000"),
        ("caf\u00e9 au", 4, "caf\u00e9\nau"),
        ("caf\u00e9 au", 7, "caf\u00e9 au"),
        ("e\u0301 x", 3, "e\u0301\nx"),
        ("e\u0301 x", 4, "e\u0301 x"),
        ("\uff11\uff12 \uff13\uff14", 5, "\uff11\uff12 \uff13\uff14"),
        ("\uff11\uff12 \uff13\uff14", 4, "\uff11\uff12\n\uff13\uff14"),
        ("\uff21 \uff22 \uff23", 3, "\uff21 \uff22\n\uff23"),
        ("hello\u00a0world", 20, "hello world"),
        ("hello\u200bworld", 5, "hello\u200bworld"),
        ("\U0001f44d\U0001f3fb a", 4, "\U0001f44d\U0001f3fb a"),
        ("\U0001f44d\U0001f3fb a", 3, "\U0001f44d\U0001f3fb\na"),
    ],
)
def test_wrap_examples(text: str, width: int, expected: str) -> None:
    assert wrap_text(text, width) == expected
    assert_valid_wrap(text, width, expected)


def test_family_emoji_is_one_word() -> None:
    family = "\U0001f468\u200d\U0001f469\u200d\U0001f467\u200d\U0001f466"
    assert len(family) == 7
    assert " " not in family
    assert wrap_text(family, 1) == family
    assert wrap_text(f"{family} x", 8) == f"{family}\nx"
    assert wrap_text(f"{family} x", 9) == f"{family} x"


def test_single_letters() -> None:
    text = " ".join("abcdefghij")
    assert wrap_text(text, 1) == "\n".join("abcdefghij")
    assert wrap_text(text, 19) == text
    assert wrap_text(text, 100) == text


@pytest.mark.parametrize(
    "width",
    [0, -1, -100, False, 1.0, 2.5, "3", "1", None, [], {}, b"4", 0.0],
)
def test_invalid_width_raises(width: object) -> None:
    with pytest.raises(ValueError):
        wrap_text("hello world", width)


@pytest.mark.parametrize("width", [1, 2, 10, 10**6])
def test_valid_width_accepts_minimum_and_large(width: int) -> None:
    result = wrap_text("hi", width)
    assert result == "hi"


def test_blank_inputs_at_several_widths() -> None:
    blanks = ["", " ", "\t", "\n", "\r\n", " \t\n ", "\f\v", "\u00a0", "\u3000", "\u0085"]
    for text in blanks:
        assert text.strip() == "" or text.split() == []
        for width in (1, 2, 40):
            assert wrap_text(text, width) == ""


def test_common_whitespace_runs_are_single_breaks() -> None:
    separators = [
        " ",
        "  ",
        "\t",
        "\n\n",
        "\r\n",
        " \t\n ",
        "\u00a0",
        "\u3000",
        "\u2028\u2029",
        "\x0b\x0c",
        "\u0085",
        "\u2003",
    ]
    for sep in separators:
        assert wrap_text(f"red{sep}blue", 8) == "red blue"
        assert wrap_text(f"red{sep}blue", 7) == "red\nblue"
        assert wrap_text(f"red{sep}blue", 3) == "red\nblue"
        assert wrap_text(sep, 4) == ""
        assert wrap_text(f"{sep}red{sep * 2}blue{sep}", 8) == "red blue"


def test_every_python_whitespace_character_is_a_break() -> None:
    assert len(PYTHON_WHITESPACE) >= 25
    all_ws = "".join(PYTHON_WHITESPACE)
    assert wrap_text(all_ws, 5) == ""
    assert wrap_text(f"word{all_ws}word", 9) == "word word"
    assert wrap_text(f"word{all_ws}word", 8) == "word\nword"
    for ch in PYTHON_WHITESPACE:
        assert wrap_text(f"aa{ch}bb", 10) == "aa bb"
        assert wrap_text(ch, 1) == ""
        assert wrap_text(ch * 4, 2) == ""
        assert wrap_text(f"{ch}aa{ch * 3}bb{ch}", 5) == "aa bb"


def test_non_whitespace_format_characters_stay_inside_the_word() -> None:
    for ch in NON_BREAKING:
        assert not ch.isspace()
        word = f"ab{ch}cd"
        assert len(word) > 2
        assert wrap_text(word, 2) == word
        assert wrap_text(f"X{ch}Y Z", 10) == f"X{ch}Y Z"
        # 3-char token + space + "Z" needs width 5; width 4 must break.
        assert len(f"X{ch}Y") == 3
        assert wrap_text(f"X{ch}Y Z", 4) == f"X{ch}Y\nZ"


def test_no_trailing_newline_or_padding_spaces() -> None:
    samples = [
        ("one two three", 7),
        ("overlongword", 3),
        ("a b c d", 1),
        ("  spaced\tout  ", 6),
    ]
    for text, width in samples:
        result = wrap_text(text, width)
        assert not result.endswith("\n")
        assert not result.endswith(" ")
        if result:
            for line in result.split("\n"):
                assert line
                assert line == line.strip(" ")
                assert len(line) <= width or " " not in line


def test_word_sequence_and_lengths_follow_len_not_display_width() -> None:
    text = "caf\u00e9 \uff21\uff21 e\u0301\u0301 xx"
    # café (4), ＡＡ (2), e + two combining marks (3), xx (2)
    words = text.split()
    assert [len(word) for word in words] == [4, 2, 3, 2]
    result = wrap_text(text, 4)
    assert result.split() == words
    for line in result.split("\n"):
        if " " in line:
            assert len(line) <= 4


def test_idempotent_for_same_width() -> None:
    text = "The quick brown fox jumps over the lazy dog"
    for width in range(1, 25):
        once = wrap_text(text, width)
        assert wrap_text(once, width) == once
        assert once.split() == text.split()


def test_wider_width_never_adds_lines() -> None:
    text = "The quick brown fox jumps over the lazy dog"
    previous = None
    for width in range(1, 40):
        result = wrap_text(text, width)
        count = 0 if result == "" else result.count("\n") + 1
        if previous is not None:
            assert count <= previous
        previous = count
    assert wrap_text(text, 10**9) == " ".join(text.split())


def test_random_layouts_match_greedy_rules() -> None:
    rng = random.Random(20261010)
    alphabet = "abcXYZ"
    for _ in range(200):
        words = [
            "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 12)))
            for _ in range(rng.randint(0, 25))
        ]
        if not words:
            text = "".join(rng.choice(PYTHON_WHITESPACE) for _ in range(rng.randint(0, 6)))
        else:
            pieces: list[str] = []
            if rng.random() < 0.7:
                pieces.append(
                    "".join(rng.choice(PYTHON_WHITESPACE) for _ in range(rng.randint(1, 3)))
                )
            for index, word in enumerate(words):
                pieces.append(word)
                if index != len(words) - 1:
                    pieces.append(
                        "".join(
                            rng.choice(PYTHON_WHITESPACE) for _ in range(rng.randint(1, 4))
                        )
                    )
            if rng.random() < 0.7:
                pieces.append(
                    "".join(rng.choice(PYTHON_WHITESPACE) for _ in range(rng.randint(1, 3)))
                )
            text = "".join(pieces)
        width = rng.randint(1, 20)
        assert_valid_wrap(text, width, wrap_text(text, width))


def test_long_word_is_not_hyphenated_or_split() -> None:
    word = "x" * 50
    assert wrap_text(word, 1) == word
    assert wrap_text(word, 49) == word
    assert wrap_text(word, 50) == word
    # The long word sits between "ab" and "cd", so those two never share a line.
    assert wrap_text(f"ab {word} cd", 4) == f"ab\n{word}\ncd"
    assert wrap_text(f"ab {word} cd", 5) == f"ab\n{word}\ncd"
    # "ab cd" is exactly 5, then the long word drops to the next line.
    assert wrap_text(f"ab cd {word}", 5) == f"ab cd\n{word}"
