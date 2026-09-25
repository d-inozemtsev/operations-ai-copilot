import csv
import sqlite3
from contextlib import closing
from pathlib import Path
import json


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def get_inventory(product: str, warehouse: str) -> int:
    '''читает складской CSV, ищет строку, где совпали тоывр и склад, и возвращает quantity'''
    with (DATA_DIR / "inventory.csv").open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["product"] == product and row["warehouse"] == warehouse:
                return int(row["quantity"])

    raise ValueError(f"No inventory for product={product!r}, warehouse={warehouse!r}")



def get_sales(product: str, region: str, days: int = 14) -> list[dict[str, str | int]]:
    
    if days < 1:
        raise ValueError("days must be at least 1")

    with closing(sqlite3.connect(DATA_DIR / "sales.db")) as connection:
        rows = connection.execute(
            """
            SELECT date, quantity
            FROM sales
            WHERE product = ? AND region = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (product, region, days),
        ).fetchall()

    if not rows:
        raise ValueError(f"No sales for product={product!r}, region={region!r}")

    return [{"date": date, "quantity": quantity} for date, quantity in reversed(rows)]


def get_shipments(product: str, destination: str) -> list[dict]:
    with (DATA_DIR / "logistics.json").open(encoding="utf-8") as file:
        data = json.load(file)

    return [
        shipment
        for shipment in data["shipments"]
        if shipment["product"] == product
        and shipment["destination"] == destination
    ]