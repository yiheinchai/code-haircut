from functools import partial


class ClientMixin:
    def _parse_json(self, response: str) -> str:
        return response

    def unused(self) -> str:
        return "nope"


class Client(ClientMixin):
    def request(self) -> object:
        return partial(self._parse_json, "ok")


def run() -> object:
    return Client().request()
