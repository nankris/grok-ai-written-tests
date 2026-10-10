"""Run-length encoding that allows digits and backslashes.

Canonical encode walks maximal runs. A backslash or an ASCII digit is always
written as a backslash, the character, and a decimal length (including 1).
Any other character is written alone when the run length is 1, and with a
decimal length when the run is longer. Decode parses that token grammar
greedily and accepts any concatenation of tokens.
"""


def _is_ascii_digit(char: str) -> bool:
    return "0" <= char <= "9"


def _is_escaped(char: str) -> bool:
    return char == "\\" or _is_ascii_digit(char)


def encode(s: str) -> str:
    parts: list[str] = []
    index = 0
    size = len(s)
    while index < size:
        char = s[index]
        end = index + 1
        while end < size and s[end] == char:
            end += 1
        run = end - index
        if _is_escaped(char):
            parts.append("\\" + char + str(run))
        elif run == 1:
            parts.append(char)
        else:
            parts.append(char + str(run))
        index = end
    return "".join(parts)


def _read_length(encoded: str, index: int, minimum: int) -> tuple[int, int]:
    size = len(encoded)
    if index >= size or not _is_ascii_digit(encoded[index]):
        raise ValueError("missing length")
    if encoded[index] == "0":
        raise ValueError("invalid length")
    end = index + 1
    while end < size and _is_ascii_digit(encoded[end]):
        end += 1
    value = int(encoded[index:end])
    if value < minimum:
        raise ValueError("invalid length")
    return value, end


def decode(encoded: str) -> str:
    parts: list[str] = []
    index = 0
    size = len(encoded)
    while index < size:
        char = encoded[index]
        if char == "\\":
            if index + 1 >= size:
                raise ValueError("truncated escape")
            run_char = encoded[index + 1]
            if not _is_escaped(run_char):
                raise ValueError("bad escape")
            run, index = _read_length(encoded, index + 2, 1)
            parts.append(run_char * run)
        elif _is_ascii_digit(char):
            raise ValueError("bare digit")
        else:
            index += 1
            if index < size and _is_ascii_digit(encoded[index]):
                run, index = _read_length(encoded, index, 2)
                parts.append(char * run)
            else:
                parts.append(char)
    return "".join(parts)
