"""SQL validation and region/month metrics for the PharmEasy pipeline."""
import sqlite3
from pathlib import Path
import pandas as pd
from metrics_engine import compute_percentage_change_v1, flag_significant_regions_v1, save_state_v1, load_previous_state_v1

DB_FILE = Path("pharmeasy.db")


def run_queries(db_file=DB_FILE):
    with sqlite3.connect(db_file) as conn:
        left_count = conn.execute(
            "SELECT COUNT(*) FROM regions_master r LEFT JOIN orders_clean o ON r.region = o.region"
        ).fetchone()[0]
        inner_count = conn.execute(
            "SELECT COUNT(*) FROM regions_master r INNER JOIN orders_clean o ON r.region = o.region"
        ).fetchone()[0]
        duplicates = pd.read_sql_query(
            "SELECT order_id, COUNT(*) AS n FROM orders_clean GROUP BY order_id HAVING COUNT(*) > 1",
            conn,
        )
        null_check = pd.read_sql_query(
            """
            SELECT r.region,
                   COUNT(*) AS count_star,
                   COUNT(o.order_id) AS count_order_id
            FROM regions_master r
            LEFT JOIN orders_clean o ON r.region = o.region
            GROUP BY r.region
            ORDER BY r.region
            """,
            conn,
        )
        region_counts = pd.read_sql_query(
            """
            SELECT r.region, COUNT(o.order_id) AS order_count
            FROM regions_master r
            LEFT JOIN orders_clean o ON r.region = o.region
            GROUP BY r.region
            ORDER BY order_count, r.region
            """,
            conn,
        )
        monthly = pd.read_sql_query(
            """
            SELECT region, substr(order_date, 1, 7) AS month,
                   ROUND(SUM(sales_inr), 2) AS sales_inr,
                   ROUND(SUM(profit_inr), 2) AS profit_inr,
                   COUNT(DISTINCT order_id) AS order_count
            FROM orders_clean
            GROUP BY region, substr(order_date, 1, 7)
            ORDER BY region, month
            """,
            conn,
        )

    pivot = monthly.pivot(index="region", columns="month", values="sales_inr").fillna(0)
    april_may = {
        region: compute_percentage_change_v1(float(row.get("2026-05", 0)), float(row.get("2026-04", 0)))
        for region, row in pivot.iterrows()
    }
    may_june = {
        region: compute_percentage_change_v1(float(row.get("2026-06", 0)), float(row.get("2026-05", 0)))
        for region, row in pivot.iterrows()
    }

    return {
        "left_count": left_count,
        "inner_count": inner_count,
        "duplicates": duplicates,
        "null_check": null_check,
        "region_counts": region_counts,
        "monthly": monthly,
        "april_may_changes": april_may,
        "may_june_changes": may_june,
    }


def main():
    result = run_queries()
    print(f"LEFT JOIN row count: {result['left_count']}")
    print(f"INNER JOIN row count: {result['inner_count']}")
    print(f"Duplicate order IDs found: {len(result['duplicates'])}")
    print("COUNT(*) vs COUNT(order_id):")
    print(result["null_check"].to_string(index=False))
    print("\nPer-region order counts:")
    print(result["region_counts"].to_string(index=False))
    print("\nApril -> May sales change (%):")
    for region, value in result["april_may_changes"].items():
        print(f"  {region}: {value:.2f}%")
    print("\nMay -> June sales change (%):")
    for region, value in result["may_june_changes"].items():
        print(f"  {region}: {value:.2f}%")

    if (result["left_count"], result["inner_count"]) != (2101, 2100):
        raise ValueError("JOIN row-count acceptance check failed.")
    if not result["duplicates"].empty:
        raise ValueError("Duplicate order IDs remain in the clean database.")

    april_flags = flag_significant_regions_v1(result["april_may_changes"], threshold=8)
    may_flags = flag_significant_regions_v1(result["may_june_changes"], threshold=8)
    expected_april = {"Hyderabad", "Warangal", "Visakhapatnam", "Guntur", "Tirupati", "Karimnagar", "Bengaluru"}
    expected_may = {"Hyderabad", "Warangal", "Vijayawada", "Visakhapatnam", "Guntur", "Tirupati", "Karimnagar"}
    if set(april_flags) != expected_april or set(may_flags) != expected_may:
        raise ValueError("Flagging acceptance check failed.")

    april_state = {region: result["monthly"].query("region == @region").set_index("month")["sales_inr"].to_dict() for region in result["april_may_changes"]}
    save_state_v1(april_state, "state_april.json")
    if load_previous_state_v1("state_april.json") != april_state:
        raise ValueError("State persistence round-trip failed.")

    may_state = {region: result["monthly"].query("region == @region").set_index("month")["sales_inr"].to_dict() for region in result["may_june_changes"]}
    save_state_v1(may_state, "state_may.json")
    if load_previous_state_v1("state_may.json") != may_state:
        raise ValueError("May state persistence round-trip failed.")

    print("State persistence round-trip: passed")
    print("\nFlagging acceptance checks passed.")
    print("April -> May flags:", ", ".join(sorted(april_flags)))
    print("May -> June flags:", ", ".join(sorted(may_flags)))


if __name__ == "__main__":
    main()
