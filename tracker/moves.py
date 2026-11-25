"""The move rule.

An item's move is the change in its yes_pct (probability of Yes, in percentage
points) between the previous day in the history and the latest run. Items are
ranked by the size of that change (up or down). Ties go to the item with the
larger volume_24h_usd, then to the smaller item_id. The top TOP_N moves with a
non-zero change are reported.
"""
from .history import num

TOP_N = 5


def day_index(rows: list, date: str) -> dict:
    return {r["item_id"]: r for r in rows if r["date"] == date}


def previous_date(rows: list, date: str):
    earlier = sorted({r["date"] for r in rows if r["date"] < date})
    return earlier[-1] if earlier else None


def compute_moves(prev: dict, cur: dict, top: int = TOP_N) -> dict:
    """prev and cur map item_id -> history row (strings or numbers)."""
    appeared = sorted(i for i in cur if i not in prev)
    disappeared = sorted(i for i in prev if i not in cur)
    moves = []
    for item_id in cur:
        if item_id not in prev:
            continue
        old, new = num(prev[item_id].get("yes_pct")), num(cur[item_id].get("yes_pct"))
        if old is None or new is None:
            continue
        delta = round(new - old, 2)
        if delta == 0:
            continue
        moves.append({
            "item_id": item_id,
            "item": cur[item_id]["item"],
            "old": old,
            "new": new,
            "delta": delta,
            "volume_24h_usd": num(cur[item_id].get("volume_24h_usd")) or 0.0,
        })
    moves.sort(key=lambda m: (-abs(m["delta"]), -m["volume_24h_usd"], m["item_id"]))
    return {"moves": moves[:top], "appeared": appeared, "disappeared": disappeared}
