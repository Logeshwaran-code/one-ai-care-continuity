"""Medicine Cost Help: brand vs possible generic equivalent, with source + freshness. Always a confirm-with-pharmacist notice.
Ships with ILLUSTRATIVE demo values only; real use needs an imported, current price list."""
import csv
import json
from pathlib import Path
from typing import Any

from app.guardrails import ESCALATE
from app.medguard.engine import get_kb

DATA = Path(__file__).parent / "knowledge" / "seed_prices.json"


def load_prices(path: Path = DATA) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_prices_csv(path: Path) -> dict[str, Any]:
    """CSV columns: generic,brand,brand_price_inr,generic_price_inr,pack,source,as_of"""
    items, source, as_of = [], "csv-import", ""
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            items.append({"generic": r["generic"].lower(), "brand": r["brand"].lower(), "brand_price_inr": float(r["brand_price_inr"]),
                          "generic_price_inr": float(r["generic_price_inr"]), "pack": r.get("pack", "")})
            source, as_of = r.get("source", source), r.get("as_of", as_of)
    return {"_meta": {"label": "IMPORTED PRICE LIST", "source": source, "as_of": as_of}, "items": items}


def compare(name: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    data = data or load_prices()
    res = get_kb().resolve(name)
    meta = {"label": data["_meta"]["label"], "source": data["_meta"]["source"], "as_of": data["_meta"]["as_of"]}
    base: dict[str, Any] = {"query": name, "data": meta, "confirm": ESCALATE["en"] + " A generic with the same ingredient is not always right for every person; your pharmacist or doctor decides."}
    if not res.ingredients:
        return {**base, "found": False, "message": "Medicine not recognised in the seed list."}
    item = next((i for i in data["items"] if i["generic"] == res.generic_name), None)
    if item is None:
        return {**base, "found": False, "generic": res.generic_name, "message": "No price data available for this medicine."}
    saving = round(item["brand_price_inr"] - item["generic_price_inr"], 2)
    return {**base, "found": True, "generic": res.generic_name, "brand_price_inr": item["brand_price_inr"], "generic_price_inr": item["generic_price_inr"],
            "possible_saving_inr": saving, "pack": item["pack"]}
