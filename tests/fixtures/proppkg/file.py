class Uploaded:
    def _get_name(self) -> str:
        return getattr(self, "_name", "")

    def _set_name(self, value: str) -> None:
        self._name = value

    name = property(_get_name, _set_name)

    def unused(self) -> str:
        return "nope"


def run() -> str:
    uploaded = Uploaded()
    uploaded.name = "file.txt"
    return uploaded.name
