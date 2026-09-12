from attrpkg import fields

TABLE = [(fields.PositiveIntegerField, fields.CharField)]


def run() -> int:
    return len(TABLE)
