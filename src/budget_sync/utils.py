"""backend/budget_sync/utils.py"""

def safe_str_cmp(a, b):
    """Safely compare two strings."""
    if isinstance(a, str):
        a = a.encode("utf-8")
    if isinstance(b, str):
        b = b.encode("utf-8")
    return a == b
