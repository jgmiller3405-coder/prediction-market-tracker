"""Write data/status.json, which describes the latest run."""
import json
from datetime import datetime, timezone
from pathlib import Path

from .fetch import read_log
from .history import load_history
from .moves import day_index, previous_date
from .rawstore import list_days


def compute_status(root: Path, now: datetime = None) -> dict:
    root = Path(root)
    now = now or datetime.now(timezone.utc)
    days = sorted(list_days(root))
    log = read_log(root / "data" / "source_log.csv")
    history = load_history(root / "data" / "history.csv")

    run_date = max((r["date"] for r in log), default=None)
    sources = [
        {"name": r["source"], "ok": r["ok"] == "true", "count": int(r["count"])}
        for r in log if r["date"] == run_date
    ]
    cur = day_index(history, run_date) if run_date else {}
    prev_date = previous_date(history, run_date) if run_date else None
    prev = day_index(history, prev_date) if prev_date else {}
    return {
        "run_time": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "first_run_date": days[0] if days else None,
        "days_with_success": len(days),
        "items": len(cur),
        "new_today": sorted(i for i in cur if i not in prev) if prev else [],
        "gone_today": sorted(i for i in prev if i not in cur),
        "sources": sources,
    }


def write_status(root: Path, now: datetime = None) -> dict:
    status = compute_status(root, now)
    path = Path(root) / "data" / "status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    return status
