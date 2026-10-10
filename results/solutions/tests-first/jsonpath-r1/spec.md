# A small JSONPath getter

Create `jsonpath.py` in the current directory with this function:

```python
def get_path(doc, path: str):
    ...
```

Use only the Python standard library.

`doc` is a JSON-like tree of `dict`, `list`, and scalar values. `path` uses a subset of JSONPath. There is no whitespace anywhere in a valid path. A malformed path raises `ValueError`.

Grammar:

- `path := "$" segment*`
- `segment := "." identifier | "[" index "]" | "[" string "]"`
- `identifier := [A-Za-z_][A-Za-z0-9_]*`
- `index := "0" | [1-9][0-9]*` (no sign, no leading zeros)
- `string := '"' chars '"' | "'" chars "'"`
- inside a string, a character is either a normal character other than the surrounding quote and the backslash, or a backslash escape
- the escapes are `\\`, `\'`, `\"`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`, and `\u` followed by exactly four hexadecimal digits

Evaluation, starting at `doc`:

- `$` alone returns `doc`.
- `.identifier` and a bracket string look up that exact key. The current value must be a `dict`, otherwise raise `TypeError`. A missing key raises `KeyError`.
- `[index]` indexes a `list`. The current value must be a `list`, otherwise raise `TypeError`. An index past the end raises `IndexError`. Do not use Python's negative-index wrap. A minus sign makes the path malformed (`ValueError`), it does not mean the last element.
- Bracket strings use the unescaped key. `["a.b"]` is the single key `a.b`, which dot notation cannot express.
- An empty string path, a missing `$`, a trailing dot, empty brackets, a leading-zero index, an unclosed string, a bad escape, and trailing junk are all `ValueError`.
