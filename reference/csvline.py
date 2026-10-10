def parse_line(line: str) -> list[str]:
    if "\n" in line or "\r" in line:
        raise ValueError("line contains a newline")
    if line == "":
        return [""]
    fields: list[str] = []
    i = 0
    n = len(line)
    while True:
        if i < n and line[i] == '"':
            i += 1
            chars: list[str] = []
            closed = False
            while i < n:
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        chars.append('"')
                        i += 2
                        continue
                    i += 1
                    closed = True
                    break
                chars.append(line[i])
                i += 1
            if not closed:
                raise ValueError("unclosed quote")
            if i < n and line[i] != ",":
                raise ValueError("trailing characters after a quoted field")
            fields.append("".join(chars))
        else:
            chars = []
            while i < n and line[i] != ",":
                if line[i] == '"':
                    raise ValueError("quote in an unquoted field")
                chars.append(line[i])
                i += 1
            fields.append("".join(chars))
        if i >= n:
            break
        i += 1
        if i == n:
            fields.append("")
            break
    return fields
