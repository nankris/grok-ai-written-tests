def wrap_text(text: str, width: int) -> str:
    if isinstance(width, bool) or not isinstance(width, int) or width < 1:
        raise ValueError("width must be an int >= 1")
    words = text.split()
    if not words:
        return ""
    lines: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        if not current:
            current = [word]
            current_len = len(word)
        elif current_len + 1 + len(word) <= width:
            current.append(word)
            current_len += 1 + len(word)
        else:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
    lines.append(" ".join(current))
    return "\n".join(lines)
