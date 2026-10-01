"""Turn flagged metric changes into a short Context-Insight-Implication narrative."""
from pathlib import Path
import pandas as pd
from queries import run_queries
from metrics_engine import flag_significant_regions_v1

REPORT_FILE = Path("cii_report.md")


def draft_report_v1(flagged_regions, metrics):
    """Return one CII block for each unique flagged region."""
    monthly = metrics["monthly"].copy()
    blocks = []
    for region in sorted(set(flagged_regions)):
        rows = monthly[monthly["region"] == region].sort_values("month")
        if rows.empty:
            continue
        sales = dict(zip(rows["month"], rows["sales_inr"]))
        changes = []
        if region in metrics["april_may_changes"]:
            changes.append(("April→May", metrics["april_may_changes"][region]))
        if region in metrics["may_june_changes"]:
            changes.append(("May→June", metrics["may_june_changes"][region]))
        change_text = "; ".join(f"{period}: {value:.2f}%" for period, value in changes)
        blocks.append({
            "region": region,
            "Context": f"{region} has monthly sales of ₹{sales.get('2026-04', 0):,.2f} in April, ₹{sales.get('2026-05', 0):,.2f} in May and ₹{sales.get('2026-06', 0):,.2f} in June.",
            "Insight": f"The measured month-on-month changes are {change_text}.",
            "Implication": "The movement is worth a human review before any operational action is taken; the 8% rule is an alert threshold, not proof of a cause.",
        })
    return blocks


def main():
    metrics = run_queries()
    april_flags = flag_significant_regions_v1(metrics["april_may_changes"], threshold=8)
    may_flags = flag_significant_regions_v1(metrics["may_june_changes"], threshold=8)
    blocks = draft_report_v1(set(april_flags) | set(may_flags), metrics)

    lines = ["# CII Insight Narrative", "", "This draft is generated only from the SQL-verified metrics.", ""]
    for block in blocks:
        lines += [
            f"## {block['region']}",
            f"**Context:** {block['Context']}",
            f"**Insight:** {block['Insight']}",
            f"**Implication:** {block['Implication']}",
            "",
        ]
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_FILE} with {len(blocks)} unique flagged regions.")


if __name__ == "__main__":
    main()
