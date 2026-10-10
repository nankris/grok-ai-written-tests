"""Run-length encoding that allows digits and backslashes.

Canonical form walks maximal runs. A backslash or an ASCII digit is always
written as a backslash, the character, and a decimal length (including 1).
Any other character is written alone when the run length is 1, and with a
decimal length when the run length is at least 2. Lengths have no leading zeros.

``decode`` accepts any concatenation of those tokens, including neighbouring
tokens that repeat the same character, and raises ``ValueError`` otherwise.
"""

__all__ = ["encode", "decode"]


def encode(s: str) -> str:
    """Encode ``s`` into the canonical run-length form."""
    parts: list[str] = []
    index = 0
    size = len(s)
    while index < size:
        char = s[index]
        end = index + 1
        while end < size and s[end] == char:
            end += 1
        count = end - index
        if char == "\\" or "0" <= char <= "9":
            parts.append(f"\\{char}{count}")
        elif count == 1:
            parts.append(char)
        else:
            parts.append(f"{char}{count}")
        index = end
    return "".join(parts)


def decode(encoded: str) -> str:
    """Decode a concatenation of run-length tokens.

    Raises ``ValueError`` when ``encoded`` is not a concatenation of tokens.
    """
    parts: list[str] = []
    index = 0
    size = len(encoded)
    while index < size:
        char = encoded[index]
        if char == "\\":
            if index + 1 >= size:
                raise ValueError("truncated escape")
            run_char = encoded[index + 1]
            if run_char != "\\" and not ("0" <= run_char <= "9"):
                raise ValueError("invalid escape")
            length, index = _read_length(encoded, index + 2, minimum=1)
            parts.append(run_char * length)
        elif "0" <= char <= "9":
            raise ValueError("bare digit")
        elif index + 1 < size and "0" <= encoded[index + 1] <= "9":
            length, index = _read_length(encoded, index + 1, minimum=2)
            parts.append(char * length)
        else:
            parts.append(char)
            index += 1
    return "".join(parts)


def _read_length(text: str, start: int, minimum: int) -> tuple[int, int]:
    """Read a decimal length at ``text[start:]``.

    The length has at least one digit, no leading zero, and a value of at
    least ``minimum``. Returns the value and the index just past the digits.
    """
    if start >= len(text) or not ("0" <= text[start] <= "9"):
        raise ValueError("missing length")
    if text[start] == "0":
        raise ValueError("invalid length")
    end = start + 1
    while end < len(text) and "0" <= text[end] <= "9":
        end += 1
    value = int(text[start:end])
    if value < minimum:
        raise ValueError("invalid length")
    return value, end
