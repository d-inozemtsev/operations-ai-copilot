from app.sources import get_inventory, get_sales, get_shipments


def calculate_scenario(product: str, city: str, horizon_days: int = 14, demand_growth_pct: float = 20, shipment_delay_days: int = 3) -> dict:
    if horizon_days < 1:
        raise ValueError("horizon_days must be at least 1")
    if demand_growth_pct < -100:
        raise ValueError("demand_growth_pct cannot be less than -100")
    if shipment_delay_days < 0:
        raise ValueError("shipment_delay_days cannot be negative")

    sales = get_sales(product, city, days=14)
    opening_stock = get_inventory(product, city)
    shipments = get_shipments(product, city)

    average_daily_sales = sum(row["quantity"] for row in sales) / len(sales)
    expected_daily_demand = average_daily_sales * (1 + demand_growth_pct / 100)

    balance = float(opening_stock)
    stockout_day = None
    daily_projection = []

    for day in range(1, horizon_days + 1):
        arriving_quantity = sum(
            shipment["quantity"]
            for shipment in shipments
            if shipment["arrival_days"] + shipment_delay_days == day
        )

        balance += arriving_quantity - expected_daily_demand

        if balance <= 0 and stockout_day is None:
            stockout_day = day

        daily_projection.append(
            {
                "day": day,
                "arriving_quantity": arriving_quantity,
                "expected_demand": round(expected_daily_demand, 2),
                "projected_balance": round(balance, 2),
            }
        )

    return {
        "product": product,
        "city": city,
        "opening_stock": opening_stock,
        "average_daily_sales": round(average_daily_sales, 2),
        "demand_growth_pct": demand_growth_pct,
        "shipment_delay_days": shipment_delay_days,
        "stockout_day": stockout_day,
        "daily_projection": daily_projection,
    }