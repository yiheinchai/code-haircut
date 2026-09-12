class Registry:
    def run(self) -> str:
        return "ran"

    def tag_exists(self, tag: str) -> bool:
        return tag == "ok"

    def unused_method(self) -> str:
        return "nope"


registry = Registry()
run = registry.run
tag_exists = registry.tag_exists
