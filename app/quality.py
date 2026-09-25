import csv
import json
import sqlite3
from contextlib import closing

from app.sources import DATA_DIR


def check_data_quality() -> dict:
    issues = []

    # проверяем склад и запоминаем все пары товар-город
    inventory_keys = set()

    with (DATA_DIR / "inventory.csv").open(encoding="utf-8", newline="") as file:
        for row_number, row in enumerate(csv.DictReader(file), start=2):
            product = row["product"]
            city = row["warehouse"]
            inventory_keys.add((product, city))

            try:
                quantity = int(row["quantity"])
            except ValueError:
                issues.append({
                    "source": "inventory.csv",
                    "message": f"Строка {row_number}: остаток не является числом",
                })
                continue

            if quantity < 0:
                issues.append({
                    "source": "inventory.csv",
                    "message": f"Строка {row_number}: отрицательный остаток",
                })

    # для каждой складской позиции должна существовать история продаж
    with closing(sqlite3.connect(DATA_DIR / "sales.db")) as connection:
        for product, city in sorted(inventory_keys):
            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM sales
                WHERE product = ? AND region = ?
                """,
                (product, city),
            ).fetchone()[0]

            if count == 0:
                issues.append({
                    "source": "sales.db",
                    "message": f"Нет продаж для {product} / {city}",
                })

    # проверяем поставки
    with (DATA_DIR / "logistics.json").open(encoding="utf-8") as file:
        shipments = json.load(file)["shipments"]

    for shipment in shipments:
        shipment_id = shipment["shipment_id"]
        key = (shipment["product"], shipment["destination"])

        if key not in inventory_keys:
            issues.append({
                "source": "logistics.json",
                "message": f"{shipment_id}: нет соответствующего склада",
            })

        if shipment["quantity"] <= 0 or shipment["arrival_days"] < 0:
            issues.append({
                "source": "logistics.json",
                "message": f"{shipment_id}: некорректное количество или срок",
            })

    return {
        "status": "ok" if not issues else "issues_found",
        "issue_count": len(issues),
        "issues": issues,
    }