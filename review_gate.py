"""Human review gate and a small three-path test harness."""
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

AUDIT_FILE = Path("audit_log.jsonl")
ALLOWED_DECISIONS = {"approve", "edit", "reject"}


def review_gate_v1(report, decision, reviewer_note=""):
    """Validate a review decision and log the action before downstream use."""
    decision = str(decision).lower().strip()
    if decision not in ALLOWED_DECISIONS:
        raise ValueError("decision must be one of: approve, edit, reject")

    run_id = str(uuid4())
    region = report.get("region", "unknown") if isinstance(report, dict) else "unknown"
    downstream_allowed = decision == "approve"
    result = dict(report) if isinstance(report, dict) else {"report": report}
    result.update({
        "decision": decision,
        "downstream_allowed": downstream_allowed,
        "reviewer_note": reviewer_note,
        "run_id": run_id,
    })

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "region": region,
        "decision": decision,
        "reviewer_note": reviewer_note,
    }
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return result


def main():
    # The harness deliberately exercises all three valid decisions.
    sample = {"region": "Guntur", "headline": "April to May sales change: +122.19%"}
    for decision, note in [
        ("approve", "Numbers checked against the SQL output."),
        ("edit", "Clarify that the alert rule does not establish a cause."),
        ("reject", "Do not use until the supporting evidence is reviewed."),
    ]:
        before = dict(sample)
        after = review_gate_v1(sample, decision, note)
        print("BEFORE:", before)
        print("AFTER:", after)
        print("---")


if __name__ == "__main__":
    main()
