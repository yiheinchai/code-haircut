"""Payment helpers. Only the happy-path charge is exercised by the demo."""


def charge(amount: int) -> str:
    if amount > 0:
        return f"charged {amount}"
    raise ValueError("amount must be positive")


def refund(amount: int) -> str:
    if amount > 0:
        return f"refunded {amount}"
    raise ValueError("amount must be positive")


def apply_coupon(amount: int, code: str) -> int:
    if code == "SAVE10":
        return max(amount - 10, 0)
    return amount
