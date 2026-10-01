"""Reusable percentage-change, flagging, and state-persistence functions."""
import json
from pathlib import Path


def compute_percentage_change_v1(current, previous):
    """Return percentage change; a zero previous value produces 0 by design."""
    if previous == 0:
        return 0
    return (current - previous) / previous * 100


def flag_significant_regions_v1(changes, threshold=8):
    """Flag regions whose absolute MoM change is greater than the threshold."""
    return {
        region: change
        for region, change in changes.items()
        if abs(change) > threshold
    }


def save_state_v1(month_summary, path):
    path = Path(path)
    path.write_text(json.dumps(month_summary, indent=2, sort_keys=True), encoding="utf-8")


def load_previous_state_v1(path):
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
