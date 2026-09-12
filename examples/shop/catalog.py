"""Product catalog with both the lookup path you use and a bunch of dead code."""


class Catalog:
    store_name = "Corner Shop"

    def lookup(self, sku: str) -> str:
        if not sku:
            raise ValueError("sku is required")
        return f"{self.store_name}:{sku}"

    def discontinued_items(self) -> list[str]:
        return ["legacy-sku", "never-shipped"]

    def import_from_csv(self, path: str) -> int:
        raise NotImplementedError("bulk import is not used by the demo")


class Warehouse:
    def restock(self, sku: str, qty: int) -> None:
        raise NotImplementedError("warehouse restock is unused")
