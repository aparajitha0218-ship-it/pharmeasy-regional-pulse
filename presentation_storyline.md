# Presentation Storyline

## 1. Executive audience — Situation / Complication / Resolution

### Situation
The June-ready dataset contains 2,100 cleaned orders across 9 active regions, with sales calculated consistently through the same SQL-backed pipeline.

### Complication
Guntur's sales moved from ₹62,442.27 in April to ₹138,738.93 in May, a +122.19% month-on-month change. The movement is large enough to be the main review point, but the dataset alone does not establish why it happened.

### Resolution
Treat the Guntur movement as a review item rather than a confirmed cause: check the May order/category mix first, confirm the operational context with the regional team, and only then decide whether a targeted follow-up is needed.

## 2. Regional manager audience — Overview / Category / Detail

### Overview
Guntur sales increased by 122.19% from April to May, then moved to ₹99,745.18 in June.

### Category
In May, Wellness & Nutrition was the largest Guntur category by sales at ₹53,085.01, followed by Medical Devices at ₹32,766.69 and Lab Tests at ₹23,590.94.

### Detail
The figures come from the cleaned order table and the SQL region/month aggregation. April had 51 Guntur orders, May had 77, and June had 62; the dashboard lets the reviewer inspect the same pattern by region and category.

## Stakeholder pushback Q&A

### Q1. Why should I believe the +122.19% number?
**1 — Acknowledge:** That is a fair question because the movement is unusually large compared with the other month-to-month changes.

**2 — Verified vs. not verified:** The number is calculated from the cleaned order data and SQL monthly sales totals; the data does not independently verify a business cause for the movement.

**3 — Resolve uncertainty:** Reconcile the Guntur April and May order/category totals with the regional source export and operational notes before the next review cycle.

### Q2. What if an alternative explanation is driving the increase?
**1 — Acknowledge:** The order data cannot distinguish every operational reason behind a sales change.

**2 — Verified vs. not verified:** The April and May sales totals, order counts and category breakdown are verified in the pipeline, while the reason for the change remains unverified.

**3 — Resolve uncertainty:** Compare the May category/order mix with the source-system operational notes and confirm the explanation with the regional owner before taking action.
