_ESCAPES = {
    "\\": "\\",
    "'": "'",
    '"': '"',
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


def _ident_char(ch: str, first: bool) -> bool:
    if first:
        return ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ch == "_"
    return _ident_char(ch, True) or ("0" <= ch <= "9")


def _unescape(path: str, i: int, quote: str):
    chars: list[str] = []
    n = len(path)
    while i < n:
        ch = path[i]
        if ch == quote:
            return "".join(chars), i + 1
        if ch == "\\":
            if i + 1 >= n:
                raise ValueError("bad escape")
            esc = path[i + 1]
            if esc == "u":
                hex_digits = path[i + 2 : i + 6]
                if len(hex_digits) != 4 or any(c not in "0123456789abcdefABCDEF" for c in hex_digits):
                    raise ValueError("bad unicode escape")
                chars.append(chr(int(hex_digits, 16)))
                i += 6
                continue
            if esc not in _ESCAPES:
                raise ValueError("bad escape")
            chars.append(_ESCAPES[esc])
            i += 2
            continue
        chars.append(ch)
        i += 1
    raise ValueError("unclosed string")


def get_path(doc, path: str):
    if not isinstance(path, str) or not path.startswith("$"):
        raise ValueError("path must start with $")
    cur = doc
    i = 1
    n = len(path)
    while i < n:
        ch = path[i]
        if ch == ".":
            i += 1
            if i >= n or not _ident_char(path[i], True):
                raise ValueError("expected identifier")
            j = i + 1
            while j < n and _ident_char(path[j], False):
                j += 1
            key = path[i:j]
            if not isinstance(cur, dict):
                raise TypeError("dot lookup requires a dict")
            if key not in cur:
                raise KeyError(key)
            cur = cur[key]
            i = j
        elif ch == "[":
            i += 1
            if i >= n:
                raise ValueError("unclosed bracket")
            if path[i] in "\"'":
                quote = path[i]
                key, i = _unescape(path, i + 1, quote)
                if i >= n or path[i] != "]":
                    raise ValueError("expected ]")
                i += 1
                if not isinstance(cur, dict):
                    raise TypeError("string lookup requires a dict")
                if key not in cur:
                    raise KeyError(key)
                cur = cur[key]
            elif path[i] == "-":
                raise ValueError("negative index is not allowed")
            elif "0" <= path[i] <= "9":
                j = i
                while j < n and "0" <= path[j] <= "9":
                    j += 1
                token = path[i:j]
                if (len(token) > 1 and token[0] == "0") or j >= n or path[j] != "]":
                    raise ValueError("bad index")
                index = int(token)
                i = j + 1
                if not isinstance(cur, list):
                    raise TypeError("index requires a list")
                if index >= len(cur):
                    raise IndexError("index out of range")
                cur = cur[index]
            else:
                raise ValueError("bad bracket segment")
        else:
            raise ValueError("unexpected character in path")
    return cur
