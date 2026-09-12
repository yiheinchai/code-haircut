from apilib import fields, public_path


def run() -> tuple[str, str]:
    return public_path(), fields.CharField.kind
