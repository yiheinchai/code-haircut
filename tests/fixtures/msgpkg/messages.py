class CheckMessage:
    def __init__(self, ident: str):
        self.id = ident

    def is_silenced(self) -> bool:
        return self.id == "quiet"

    def unused(self) -> str:
        return "nope"


class Warning(CheckMessage):
    pass
