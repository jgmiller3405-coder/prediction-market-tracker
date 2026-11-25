"""Download each source, save the raw response, and log the result of every source."""
import csv
import json
import time
from pathlib import Path

import requests

from .markets import EVENTS, source_name
from .rawstore import clear_day, write_raw

API = "https://gamma-api.polymarket.com/markets"
LOG_COLUMNS = ["date", "source", "ok", "count", "error"]


def fetch_event(event, attempts: int = 3) -> bytes:
    """Request only the tracked market ids. Raises if the answer is unusable."""
    params = [("id", market_id) for market_id in event.market_ids]
    last = None
    for attempt in range(attempts):
        try:
            response = requests.get(API, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list) or not data:
                raise ValueError("empty or unexpected response")
            return response.content
        except (requests.RequestException, ValueError) as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(str(last))


def run_fetch(root: Path, date: str, fetcher=fetch_event, events=EVENTS) -> list:
    """Replace the day's raw files with fresh ones. One failing source does not stop the rest."""
    root = Path(root)
    clear_day(root, date)
    results = []
    for event in events:
        source = source_name(event)
        try:
            content = fetcher(event)
            count = len(json.loads(content))
            write_raw(root, date, source, "json", content)
            results.append({"date": date, "source": source, "ok": True, "count": count, "error": ""})
        except Exception as exc:  # any failure: record it, write no raw file
            results.append({"date": date, "source": source, "ok": False, "count": 0,
                            "error": str(exc)[:200]})
    update_log(root / "data" / "source_log.csv", date, results)
    return results


def read_log(path: Path) -> list:
    path = Path(path)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def update_log(path: Path, date: str, results: list) -> None:
    """Keep one block of rows per date; a rerun on the same date replaces its block."""
    rows = [r for r in read_log(path) if r["date"] != date] + results
    rows.sort(key=lambda r: (r["date"], r["source"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(LOG_COLUMNS)
        for r in rows:
            ok = r["ok"] if isinstance(r["ok"], str) else str(bool(r["ok"])).lower()
            writer.writerow([r["date"], r["source"], ok, r["count"], r["error"]])
