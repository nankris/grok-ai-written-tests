# One-line comma-separated parser

Create `csvline.py` in the current directory with this function:

```python
def parse_line(line: str) -> list[str]:
    ...
```

Use only the Python standard library.

Parse a single record in the dialect below and return the field strings. Raise `ValueError` on malformed input. Spaces are significant and are never stripped. Backslash escapes are not used.

- If `line` contains `\n` or `\r`, raise `ValueError`. The caller passes one line without its terminator.
- Fields are separated by commas. An empty line is one empty field: `""` returns `[""]`. A trailing comma produces a final empty field. A line that is only a comma returns two empty fields.
- A field is quoted if and only if its first character is a double quote (`"`). A quoted field runs until a closing unescaped double quote. That closing quote must end the field: the next character is a comma or the end of the line. Characters between the closing quote and the next comma are an error.
- Inside a quoted field, two consecutive double quotes are one literal double quote. A quoted field may contain commas and spaces. A quoted field that never closes is an error.
- An unquoted field runs until the next comma or the end of the line and must not contain a double quote. A double quote anywhere in an unquoted field is an error.
