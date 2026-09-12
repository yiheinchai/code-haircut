class Widget:
    def __str__(self) -> str:
        return "ok"

    def render(self) -> str:
        return "rendered"

    def open(self) -> str:
        return "opened"

    open.alters_data = True

    def unused(self) -> str:
        return "nope"


def run() -> str:
    return Widget().render()
