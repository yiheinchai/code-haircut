from .query import QuerySet


def prepare(value: str) -> str:
    return value.strip()


def unused_helper(value: str) -> str:
    return value.upper()


class Model:
    objects = QuerySet()

    def save(self, name: str) -> str:
        return prepare(name)

    def delete(self) -> str:
        return "deleted"
