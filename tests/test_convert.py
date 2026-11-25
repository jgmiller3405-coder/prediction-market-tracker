import json

import pytest

from tracker.convert import COLUMNS, NUMERIC, convert_markets
from tracker.markets import EVENTS, source_name
from tests.conftest import event_payload, make_market


def test_columns_start_with_the_four_fixed_ones_and_have_two_numeric():
    assert COLUMNS[:4] == ["date", "item_id", "item", "source"]
    assert len(NUMERIC) >= 2 and set(NUMERIC) <= set(COLUMNS)


@pytest.mark.parametrize("event", EVENTS, ids=lambda e: e.slug)
def test_every_source_converts_to_the_common_columns(event):
    rows = convert_markets(event, source_name(event), "2026-11-25", event_payload(event, 0.25))
    assert len(rows) == len(event.market_ids)
    for row in rows:
        assert list(row) == COLUMNS
        assert row["source"] == source_name(event)
        assert row["date"] == "2026-11-25"
        assert row["yes_pct"] == 25.0
        assert row["item"].startswith(event.short + ": ")


def test_values_are_scaled_and_rounded(event):
    raw = json.dumps([make_market(event.market_ids[0], 0.545, bestBid=0.54, bestAsk=0.55,
                                  oneDayPriceChange=-0.04)]).encode()
    row = convert_markets(event, "s", "2026-11-25", raw)[0]
    assert (row["yes_pct"], row["best_bid_pct"], row["best_ask_pct"]) == (54.5, 54.0, 55.0)
    assert row["day_change_pts"] == -4.0
    assert row["volume_24h_usd"] == 1000 and row["volume_total_usd"] == 50001
    assert row["end_date"] == "2027-01-01" and row["closed"] == "false"


def test_yes_is_found_even_when_outcomes_are_reversed(event):
    raw = json.dumps([make_market(event.market_ids[0], outcomes='["No", "Yes"]',
                                  outcomePrices='["0.9", "0.1"]')]).encode()
    assert convert_markets(event, "s", "d", raw)[0]["yes_pct"] == 10.0


def test_missing_values_are_left_empty(event):
    market = make_market(event.market_ids[0])
    for key in ("bestBid", "bestAsk", "oneDayPriceChange", "liquidityNum"):
        del market[key]
    row = convert_markets(event, "s", "d", json.dumps([market]).encode())[0]
    assert row["best_bid_pct"] is None and row["day_change_pts"] is None and row["liquidity_usd"] is None


def test_untracked_markets_are_ignored(event):
    raw = json.dumps([make_market("999999999"), make_market(event.market_ids[0])]).encode()
    assert [r["item_id"] for r in convert_markets(event, "s", "d", raw)] == [event.market_ids[0]]


def test_arrows_in_labels_become_words(event):
    raw = json.dumps([make_market(event.market_ids[0], groupItemTitle="↑$2.0T")]).encode()
    assert convert_markets(event, "s", "d", raw)[0]["item"].endswith("Hit $2.0T")


def test_at_least_ten_items_are_tracked():
    assert sum(len(e.market_ids) for e in EVENTS) >= 10


def test_markets_cover_the_requested_categories():
    cats = [e.category for e in EVENTS]
    assert sorted(cats) == ["Financial", "Political", "Pop culture", "Sports", "Sports"]


def test_rows_carry_the_events_category(event):
    rows = convert_markets(event, source_name(event), "2026-11-25", event_payload(event))
    assert {r["category"] for r in rows} == {event.category}
