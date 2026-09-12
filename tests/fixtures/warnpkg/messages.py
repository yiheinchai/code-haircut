from __future__ import annotations


class Warning:
    def __init__(self, msg: str, id: str | None = None, **kwargs):
        self.msg = msg
        self.id = id


class UnusedWarning:
    pass
