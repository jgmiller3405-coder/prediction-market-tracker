"""Build data/history.csv from the raw files alone."""
import csv
import json
from pathlib import Path

from .convert import COLUMNS, convert_markets
from .markets import BY_SOURCE
from .rawstore import list_days, read_raw, source_of


def build_rows(root: Path) -> list:
    """Convert every raw file, day by day. Sorted by date, then item_id."""
    rows = []
    for date, files in list_days(root).items():
        for path in files:
            source = source_of(path)
            event = BY_SOURCE.get(source)
            if event is None:
                continue
            try:
                rows.extend(convert_markets(event, source, date, read_raw(path)))
            except (ValueError, TypeError, json.JSONDecodeError):
                continue  # an unreadable raw file contributes no rows
    rows.sort(key=lambda r: (r["date"], r["item_id"]))
    return rows


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value == int(value) and abs(value) >= 1000:
        return str(int(value))
    return str(value)


def write_history(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow([_cell(row.get(c)) for c in COLUMNS])


def build_history(root: Path) -> list:
    rows = build_rows(root)
    write_history(Path(root) / "data" / "history.csv", rows)
    return rows


def load_history(path: Path) -> list:
    path = Path(path)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(value):
    """Cell text -> float, or None when empty."""
    if value in (None, ""):
        return None
    return float(value)
