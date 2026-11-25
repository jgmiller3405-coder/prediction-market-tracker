"""Convert one raw Polymarket response into rows with the common columns."""
import json

from .markets import Event

COLUMNS = [
    "date", "item_id", "item", "source",        # fixed first four
    "event", "end_date", "closed",              # text columns
    "yes_pct", "best_bid_pct", "best_ask_pct",  # odds, in percent
    "day_change_pts",                           # change in yes_pct over 24 h
    "volume_24h_usd", "volume_total_usd", "liquidity_usd",
]
NUMERIC = [
    "yes_pct", "best_bid_pct", "best_ask_pct", "day_change_pts",
    "volume_24h_usd", "volume_total_usd", "liquidity_usd",
]


def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _scaled(value, factor, digits):
    number = _float(value)
    return None if number is None else round(number * factor, digits)


def _yes_price(market):
    """Price of the 'Yes' outcome (outcomes and prices are JSON strings)."""
    try:
        outcomes = json.loads(market["outcomes"])
        prices = json.loads(market["outcomePrices"])
        index = outcomes.index("Yes") if "Yes" in outcomes else 0
        return prices[index]
    except (KeyError, ValueError, TypeError, IndexError):
        return None


def _label(market):
    label = (market.get("groupItemTitle") or market.get("question") or "").strip()
    label = label.replace("↓", "Dip ").replace("↑", "Hit ")
    return " ".join(label.split())


def convert_markets(event: Event, source: str, date: str, raw: bytes) -> list:
    """One row per tracked market found in the raw response. Untracked markets are ignored."""
    markets = json.loads(raw)
    rows = []
    for market in markets:
        market_id = str(market.get("id"))
        if market_id not in event.market_ids:
            continue
        rows.append({
            "date": date,
            "item_id": market_id,
            "item": f"{event.short}: {_label(market)}",
            "source": source,
            "event": event.title,
            "end_date": (market.get("endDate") or "")[:10],
            "closed": "true" if market.get("closed") else "false",
            "yes_pct": _scaled(_yes_price(market), 100, 2),
            "best_bid_pct": _scaled(market.get("bestBid"), 100, 2),
            "best_ask_pct": _scaled(market.get("bestAsk"), 100, 2),
            "day_change_pts": _scaled(market.get("oneDayPriceChange"), 100, 2),
            "volume_24h_usd": _scaled(market.get("volume24hr"), 1, 0),
            "volume_total_usd": _scaled(market.get("volumeNum"), 1, 0),
            "liquidity_usd": _scaled(market.get("liquidityNum"), 1, 0),
        })
    return rows
