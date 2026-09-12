"""Exercise a couple of shop APIs so CodeHaircut can see what actually ran."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shop.catalog import Catalog
from shop.payments import charge

if __name__ == "__main__":
    print(Catalog().lookup("tea-tin"))
    print(charge(12))
