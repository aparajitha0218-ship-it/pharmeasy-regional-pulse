# PharmEasy Regional Pulse

A small end-to-end regional performance pipeline built around a deterministic PharmEasy-style order export. The project cleans the data, validates it, stores the clean rows in SQLite, calculates region/month metrics, flags large month-on-month movements, drafts a reviewable narrative, and presents the results in a local Streamlit dashboard.

## 1. Install and run

Use Python 3.10 or newer. From the repository root, run these three commands:

```bash
pip install -r requirements.txt
```

```bash
python generate_dataset.py && python clean_data.py && python build_db.py && python queries.py && python draft_report.py && python review_gate.py
```

```bash
streamlit run app.py
```

The pipeline needs no API key, network service, paid tool, or signup-gated service.

## 2. Evaluation-ready cover note

**Headline finding:** Guntur's April-to-May sales moved from ₹62,442.27 to ₹138,738.93, a +122.19% month-on-month swing that is the main review item in this dataset.

- **Streamlit dashboard — `app.py`:** live exploration of the headline KPIs, regional trend, region comparison, category share, and detail table.
- **CII narrative — embedded in the dashboard (also generated in `cii_report.md`):** explains the Context, Insight and Implication behind the flagged regional movements.
- **One-page memo — `memo.md`:** records the Guntur finding, evidence, recommendation, next check and the remaining assumption.
- **Presentation storyline — `presentation_storyline.md`:** reframes the same finding for an executive and a regional manager and includes stakeholder pushback Q&A.

**Reviewer order:** open the dashboard first, read the CII narrative, then the one-page memo, and finally the presentation storyline.

**Single unverified assumption:** the order table does not contain the operational context needed to identify the cause of the Guntur May increase, so the cause remains unverified until the regional source notes are checked.

## Project structure

- `generate_dataset.py` — deterministic raw-data generator.
- `clean_data.py` — duplicate removal, region normalization, imputation and schema validation.
- `data_quality_report.md` — data-quality dimensions and recorded checks.
- `build_db.py` — SQLite database builder.
- `queries.py` — JOIN checks, null-count pitfall, region counts and monthly metrics.
- `metrics_engine.py` — percentage change, alert flagging and JSON state persistence.
- `draft_report.py` — CII narrative generator.
- `memo.md` — recommendation memo.
- `review_gate.py` — approve/edit/reject review gate and audit-log harness.
- `audit_log.jsonl` — review actions written by the harness.
- `reliability_checklist.md` — safety, validation, critique/refine and human sign-off checks.
- `app.py` — Streamlit + Plotly dashboard.
- `presentation_storyline.md` — audience reframing and Q&A.

Generated pipeline outputs include `pharmeasy_orders_raw.csv`, `regions_master.csv`, `orders_clean.csv`, `pharmeasy.db`, and state/report files.

## Notes on the data

The generator uses the fixed seed required by the capstone, so the raw export is reproducible. The clean pipeline removes 59 exact duplicates, leaves 2,100 clean orders, normalizes 16 raw region variants to 9 active regions, and imputes the specified missing category and profit values.
