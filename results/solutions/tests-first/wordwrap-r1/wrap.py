def wrap_text(text: str, width: int) -> str:
    """Greedily wrap one paragraph to lines of at most `width` characters.

    Words are maximal runs of non-whitespace. A single word longer than
    `width` stays intact on its own line. `width` counts Python characters.
    """
    if not isinstance(width, int) or width < 1:
        raise ValueError("width must be an int >= 1")

    words = text.split()
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

    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)
