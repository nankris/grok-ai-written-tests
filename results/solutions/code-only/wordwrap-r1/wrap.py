def wrap_text(text: str, width: int) -> str:
    """Wrap one paragraph greedily to at most `width` characters per line.

    Words are maximal runs of non-whitespace. A single word longer than
    `width` stays intact on its own line. Lines are joined with ``\\n``.
    """
    if not isinstance(width, int) or width < 1:
        raise ValueError("width must be an int greater than or equal to 1")

    words = text.split()
    if not words:
        return ""

    lines: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        word_len = len(word)
        if not current:
            current = [word]
            current_len = word_len
        elif current_len + 1 + word_len <= width:
            current.append(word)
            current_len += 1 + word_len
        else:
            lines.append(" ".join(current))
            current = [word]
            current_len = word_len

    lines.append(" ".join(current))
    return "\n".join(lines)
