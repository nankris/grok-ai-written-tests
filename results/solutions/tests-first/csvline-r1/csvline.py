"""Parse one comma-separated record. Spaces are kept. Backslashes are not escapes."""


def parse_line(line: str) -> list[str]:
    """Return the fields of a single record.

    The line must not contain a newline or carriage return. A field is quoted
    only when it begins with a double quote. Inside a quoted field, a doubled
    quote is one literal quote. Raise ValueError when the record is malformed.
    """
    if "\n" in line or "\r" in line:
        raise ValueError("line contains a newline or carriage return")

    fields: list[str] = []
    i = 0
    n = len(line)

    while True:
        if i < n and line[i] == '"':
            i += 1
            parts: list[str] = []
            closed = False
            while i < n:
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        parts.append('"')
                        i += 2
                    else:
                        i += 1
                        closed = True
                        break
                else:
                    parts.append(line[i])
                    i += 1
            if not closed:
                raise ValueError("unclosed quoted field")
            if i < n and line[i] != ",":
                raise ValueError("characters after closing quote")
            fields.append("".join(parts))
        else:
            start = i
            while i < n and line[i] != ",":
                if line[i] == '"':
                    raise ValueError("double quote in unquoted field")
                i += 1
            fields.append(line[start:i])

        if i >= n:
            break
        i += 1
        if i == n:
            fields.append("")
            break

    return fields
