# Greedy word wrap

Create `wrap.py` in the current directory with this function:

```python
def wrap_text(text: str, width: int) -> str:
    ...
```

Use only the Python standard library.

Wrap one paragraph so that each line is at most `width` characters, except for a single over-long word as described below.

`width` must be an `int` greater than or equal to 1. Otherwise raise `ValueError`. Width counts Python characters (`len` of the string), not display columns.

Treat every run of Unicode whitespace (spaces, tabs, newlines, and the rest of Python's whitespace) as a break. Discard leading and trailing whitespace of the whole input. Do not preserve interior whitespace: when two words share a line they are separated by one space. A word is a maximal run of non-whitespace characters. Never split a word. A word longer than `width` is placed alone on a line, and that line may exceed `width`.

Fill lines greedily from left to right. A word fits on the current line when the line is empty, or when `len(line) + 1 + len(word) <= width` (the extra 1 is the separating space). Otherwise start a new line. Join lines with `\n`. Do not put a trailing newline after the last line, and do not put trailing spaces on a line.

Empty input, or input that is only whitespace, returns `""`.
