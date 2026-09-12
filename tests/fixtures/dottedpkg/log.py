DEFAULT = {"()": "dottedpkg.log.RequireDebugFalse"}


class RequireDebugFalse:
    def filter(self, record: object) -> bool:
        return True


class UnusedHandler:
    pass


def configure() -> str:
    return DEFAULT["()"]
