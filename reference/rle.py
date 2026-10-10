def _is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def _read_count(encoded: str, i: int, minimum: int):
    if i >= len(encoded) or not _is_digit(encoded[i]):
        raise ValueError("missing count")
    j = i + 1
    while j < len(encoded) and _is_digit(encoded[j]):
        j += 1
    token = encoded[i:j]
    if len(token) > 1 and token[0] == "0":
        raise ValueError("leading zero in count")
    count = int(token)
    if count < minimum:
        raise ValueError("count below minimum")
    return count, j


def encode(s: str) -> str:
    if s == "":
        return ""
    parts: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        j = i + 1
        while j < n and s[j] == s[i]:
            j += 1
        char = s[i]
        count = j - i
        if char == "\\" or _is_digit(char):
            parts.append("\\" + char + str(count))
        elif count == 1:
            parts.append(char)
        else:
            parts.append(char + str(count))
        i = j
    return "".join(parts)


def decode(encoded: str) -> str:
    if encoded == "":
        return ""
    parts: list[str] = []
    i = 0
    n = len(encoded)
    while i < n:
        char = encoded[i]
        if char == "\\":
            if i + 1 >= n:
                raise ValueError("trailing backslash")
            run_char = encoded[i + 1]
            if run_char != "\\" and not _is_digit(run_char):
                raise ValueError("bad escape")
            count, i = _read_count(encoded, i + 2, 1)
            parts.append(run_char * count)
        elif _is_digit(char):
            raise ValueError("bare digit")
        else:
            i += 1
            if i < n and _is_digit(encoded[i]):
                count, i = _read_count(encoded, i, 2)
                parts.append(char * count)
            else:
                parts.append(char)
    return "".join(parts)
