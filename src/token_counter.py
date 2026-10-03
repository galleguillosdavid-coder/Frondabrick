"""
Token and character counting utility module.
"""

def count_tokens(text: str) -> int:
    """Counts whitespace-delimited tokens in text."""
    if not text:
        return 0
    return len(text.strip().split())

def count_chars(text: str) -> int:
    """Counts characters in text."""
    if not text:
        return 0
    return len(text)
