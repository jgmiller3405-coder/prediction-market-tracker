import json

import pytest

from tracker.markets import EVENTS, source_name


def make_market(market_id, yes=0.5, **over):
    market = {
        "id": market_id, "question": f"Question {market_id}?", "groupItemTitle": f"Outcome {market_id}",
        "outcomes": '["Yes", "No"]', "outcomePrices": json.dumps([str(yes), str(round(1 - yes, 4))]),
        "bestBid": yes - 0.005, "bestAsk": yes + 0.005, "oneDayPriceChange": 0.01,
        "volume24hr": 1000.4, "volumeNum": 50000.6, "liquidityNum": 2500.2,
        "endDate": "2027-01-01T05:00:00Z", "closed": False,
    }
    market.update(over)
    return market


def event_payload(event, yes=0.5, skip=(), **over):
    """A raw response for one event: every tracked market, except those in skip."""
    markets = [make_market(i, yes, **over) for i in event.market_ids if i not in skip]
    return json.dumps(markets).encode()


@pytest.fixture
def event():
    return EVENTS[0]


@pytest.fixture
def good_fetcher():
    """Returns a valid response for any event; yes probability can be changed per test."""
    state = {"yes": 0.5, "fail": set()}

    def fetcher(ev):
        if source_name(ev) in state["fail"]:
            raise RuntimeError("boom")
        return event_payload(ev, state["yes"])

    fetcher.state = state
    return fetcher
