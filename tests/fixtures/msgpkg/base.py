from .messages import Warning

ISSUES = [Warning("x")]


def check(issues):
    return [item for item in issues if not item.is_silenced()]


def run() -> int:
    return len(check([]))
