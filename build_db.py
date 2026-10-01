"""Build the local SQLite database used by the metrics and dashboard layers."""
import sqlite3
from pathlib import Path
import pandas as pd

DB_FILE = Path("pharmeasy.db")


def build_database(clean_file="orders_clean.csv", regions_file="regions_master.csv", db_file=DB_FILE):
    orders = pd.read_csv(clean_file)
    regions = pd.read_csv(regions_file)
    with sqlite3.connect(db_file) as conn:
        regions.to_sql("regions_master", conn, if_exists="replace", index=False)
        orders.to_sql("orders_clean", conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_region ON orders_clean(region)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_date ON orders_clean(order_date)")
        conn.commit()
    print(f"Built {db_file} with {len(regions)} master regions and {len(orders)} clean orders.")


if __name__ == "__main__":
    build_database()
