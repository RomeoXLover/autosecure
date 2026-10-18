"""Number formatting utility — abbreviate large numbers with K/M/B/T suffixes."""


def simplify(amount) -> str:
    """Format a number with magnitude suffix.

    Returns ``"0"`` for falsy input, ``"1.23M"`` for millions, etc.
    Always returns a string (callers embed this in Discord messages).
    """
    if not amount:
        return "0"

    try:
        val = float(amount)
    except (TypeError, ValueError):
        return "0"

    units = [
        (1_000_000_000_000, "T"),
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1_000, "K"),
    ]
    for threshold, suffix in units:
        if val >= threshold:
            return f"{val / threshold:.2f}{suffix}"
    return f"{val:.2f}"
