# Data Quality Report

The cleaning process is deliberately small and traceable: each change responds to a specific issue in the generated export.

| Data-quality dimension | What was checked or fixed |
|---|---|
| Accuracy | Missing profit is estimated from the category's observed average profit margin rather than dropped. |
| Completeness | Missing category and profit values are filled so the clean dataset has no missing values in those fields. |
| Consistency | Region names are stripped and title-cased so variants such as `HYDERABAD ` map to `Hyderabad`. |
| Timeliness | The order date is parsed and retained as an ISO date so monthly grouping is repeatable. |
| Validity | `validate_schema()` checks that all required columns exist before downstream work starts. |
| Uniqueness | Exact duplicate rows are removed before metrics are calculated. |
| Relevance | The pipeline keeps the fields needed for region/month sales, profit, orders and category analysis. |

## Recorded checks

- Raw export: 2,159 rows.
- Exact duplicate rows removed: 59.
- Clean dataset: 2,100 rows.
- Raw region variants: 16.
- Canonical active regions after normalization: 9.
- Missing category before imputation: 48.
- Missing profit before imputation: 94.
- Missing category after imputation: 0.
- Missing profit after imputation: 0.
- Clean schema validation: `validated`.
- Deliberately broken schema validation: `blocked_schema`, missing `profit_inr`.
