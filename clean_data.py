"""Clean and validate the generated PharmEasy order export."""
from pathlib import Path
import pandas as pd

RAW_FILE = Path("pharmeasy_orders_raw.csv")
CLEAN_FILE = Path("orders_clean.csv")
REGIONS_FILE = Path("regions_master.csv")
REQUIRED_COLUMNS = [
    "order_id", "order_date", "region", "category",
    "product", "quantity", "sales_inr", "profit_inr",
]


def validate_schema(df: pd.DataFrame, required_columns: list[str]) -> dict:
    """Return a small validation result without changing the input data."""
    missing = [column for column in required_columns if column not in df.columns]
    return {
        "status": "blocked_schema" if missing else "validated",
        "row_count": len(df),
        "missing_columns": missing,
    }


def clean_orders(raw_path: str | Path = RAW_FILE) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(raw_path, dtype={"order_id": str, "region": str, "category": str, "product": str})
    raw_rows = len(raw)

    # 1) Exact duplicate rows are removed first, as required by the pipeline.
    df = raw.drop_duplicates(keep="first").copy()
    duplicate_rows_removed = raw_rows - len(df)

    # 2) Normalize region names. The generated data only needs text cleanup.
    df["region"] = df["region"].fillna("").str.strip().str.title()

    # 3) Recover missing categories from the product names that are present elsewhere.
    product_category = (
        df.dropna(subset=["category"])
        .loc[lambda x: x["category"].astype(str).str.strip().ne("")]
        .drop_duplicates("product")
        .set_index("product")["category"]
        .to_dict()
    )
    missing_category_before = int(df["category"].isna().sum() + df["category"].astype(str).eq("").sum())
    df["category"] = df["category"].replace("", pd.NA)
    df["category"] = df["category"].fillna(df["product"].map(product_category))

    # 4) Estimate missing profit from the average observed margin by category.
    df["sales_inr"] = pd.to_numeric(df["sales_inr"], errors="coerce")
    df["profit_inr"] = pd.to_numeric(df["profit_inr"], errors="coerce")
    observed = df[df["profit_inr"].notna() & df["sales_inr"].gt(0)].copy()
    observed["margin"] = observed["profit_inr"] / observed["sales_inr"]
    category_margin = observed.groupby("category")["margin"].mean().to_dict()
    missing_profit_before = int(df["profit_inr"].isna().sum())

    missing_profit = df["profit_inr"].isna()
    df.loc[missing_profit, "profit_inr"] = (
        df.loc[missing_profit, "sales_inr"]
        * df.loc[missing_profit, "category"].map(category_margin)
    ).round(2)

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("int64")
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
    df["sales_inr"] = df["sales_inr"].round(2)
    df["profit_inr"] = df["profit_inr"].round(2)

    # Write ISO dates so the SQLite and Streamlit layers can read them cleanly.
    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")
    df.to_csv(CLEAN_FILE, index=False)

    report = {
        "raw_rows": raw_rows,
        "duplicate_rows_removed": duplicate_rows_removed,
        "clean_rows": len(df),
        "raw_region_variants": int(raw["region"].nunique()),
        "canonical_regions": int(df["region"].nunique()),
        "missing_category_before_imputation": missing_category_before,
        "missing_profit_before_imputation": missing_profit_before,
        "missing_category_after_imputation": int(df["category"].isna().sum()),
        "missing_profit_after_imputation": int(df["profit_inr"].isna().sum()),
    }
    return df, report


def main() -> None:
    df, report = clean_orders()
    clean_check = validate_schema(df, REQUIRED_COLUMNS)
    broken = df.drop(columns=["profit_inr"])
    broken_check = validate_schema(broken, REQUIRED_COLUMNS)

    print("Cleaning summary")
    for key, value in report.items():
        print(f"- {key}: {value}")
    print(f"Schema check: {clean_check}")
    print(f"Broken-copy check: {broken_check}")

    if clean_check["status"] != "validated":
        raise ValueError("Clean data failed schema validation.")
    if broken_check["status"] != "blocked_schema":
        raise ValueError("Broken schema demonstration did not block as expected.")
    if report["duplicate_rows_removed"] != 59 or report["clean_rows"] != 2100:
        raise ValueError("Dataset cleaning counts do not match the capstone acceptance checks.")
    if report["missing_category_after_imputation"] or report["missing_profit_after_imputation"]:
        raise ValueError("Missing values remain after imputation.")


if __name__ == "__main__":
    main()
