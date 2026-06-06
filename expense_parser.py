def parse_expense(text):
    """
    Parse a free-text message into (amount, category, note).
 
    Supports:
      500 lunch
      lunch 500
      1200 groceries big monthly shop
      1.5k rent
      800 fuel bike fillup
 
    Returns (amount, category, note) or raises ValueError.
    """
    text = text.strip()
    tokens = text.split()
 
    if not tokens:
        raise ValueError("Empty message")
 
    amount = None
    amount_index = None
 
    for i, token in enumerate(tokens):
        parsed = _parse_amount(token)
        if parsed is not None:
            amount = parsed
            amount_index = i
            break
 
    if amount is None:
        raise ValueError("No amount found")
 
    remaining = [t for i, t in enumerate(tokens) if i != amount_index]
 
    if not remaining:
        raise ValueError("No category found")
 
    category = remaining[0].lower()
    note = " ".join(remaining[1:]) if len(remaining) > 1 else None
 
    return amount, category, note


def _parse_amount(token):
    """
    Try to parse a single token as a money amount.
    Returns float or None.
 
      '500'    -> 500.0
      '1200.5' -> 1200.5
      '1.5k'   -> 1500.0
      '2K'     -> 2000.0
      'lunch'  -> None
    """
    token = token.lower()
 
    if token.endswith('k'):
        try:
            return float(token[:-1]) * 1000
        except ValueError:
            return None
 
    try:
        return float(token)
    except ValueError:
        return None
 