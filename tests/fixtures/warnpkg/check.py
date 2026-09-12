from .messages import Warning


def run() -> str:
    warning = Warning("shadows the builtin", id="W001")
    return warning.id or ""
