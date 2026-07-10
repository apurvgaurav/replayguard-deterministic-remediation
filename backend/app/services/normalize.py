def normalize_code(code: str) -> str:
    """
    Normalizes line endings to LF, strips trailing whitespace on each line,
    and removes leading/trailing blank lines to ensure syntactic consistency.
    """
    if not code:
        return ""
    # Standardize line endings to LF
    lines = code.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    # Strip trailing whitespace on each line
    cleaned_lines = [line.rstrip() for line in lines]
    # Remove leading blank lines
    while cleaned_lines and not cleaned_lines[0]:
        cleaned_lines.pop(0)
    # Remove trailing blank lines
    while cleaned_lines and not cleaned_lines[-1]:
        cleaned_lines.pop()
    return "\n".join(cleaned_lines)
