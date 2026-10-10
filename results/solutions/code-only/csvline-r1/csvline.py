def parse_line(line: str) -> list[str]:
    """Parse one comma-separated record and return its fields.

    The caller passes a line without its terminator. Spaces are kept.
    A field is quoted only when it begins with a double quote. Inside a
    quoted field, a doubled quote is one literal quote. Malformed input
    raises ValueError.
    """
    if "\n" in line or "\r" in line:
        raise ValueError("line contains a newline or carriage return")

    fields: list[str] = []
    index = 0
    length = len(line)

    while index <= length:
        if index == length:
            fields.append("")
            break

        if line[index] == '"':
            field, index = _parse_quoted(line, index)
        else:
            field, index = _parse_unquoted(line, index)

        fields.append(field)
        if index == length:
            break
        if line[index] != ",":
            raise ValueError("characters after closing quote")
        index += 1

    return fields


def _parse_quoted(line: str, index: int) -> tuple[str, int]:
    """Read a quoted field starting at its opening quote.

    Returns the field text and the index just after the closing quote.
    """
    length = len(line)
    index += 1
    chars: list[str] = []

    while index < length:
        char = line[index]
        if char != '"':
            chars.append(char)
            index += 1
            continue
        if index + 1 < length and line[index + 1] == '"':
            chars.append('"')
            index += 2
            continue
        return "".join(chars), index + 1

    raise ValueError("unterminated quoted field")


def _parse_unquoted(line: str, index: int) -> tuple[str, int]:
    """Read an unquoted field. A double quote anywhere in it is an error."""
    length = len(line)
    chars: list[str] = []

    while index < length and line[index] != ",":
        if line[index] == '"':
            raise ValueError("double quote in unquoted field")
        chars.append(line[index])
        index += 1

    return "".join(chars), index
