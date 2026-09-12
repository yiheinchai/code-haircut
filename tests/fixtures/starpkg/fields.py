from io import BytesIO


class Kept:
    def run(self) -> str:
        return "ok"


class Unused:
    pass


def _private() -> None:
    return None
