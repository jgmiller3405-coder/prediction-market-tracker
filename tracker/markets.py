"""The 5 Polymarket events we track and the outcome markets we keep from each.

One financial, one pop culture, one political and two sports markets. Each outcome
market is one item (25 items in total). The ids were chosen on 2026-11-25 as outcomes
with large one-day price swings in markets that close after 2026-12-03 (the earliest
tracked close is 2026-12-15). The tool asks the API for these ids only, so the raw
files hold nothing else.
"""
from typing import NamedTuple


class Event(NamedTuple):
    slug: str          # used in the source name and raw file name
    category: str      # Financial, Pop culture, Political or Sports
    short: str         # prefix of every item name
    title: str         # full Polymarket event title
    market_ids: tuple  # the outcome markets we track


EVENTS = [
    Event(
        "bitcoin", "Financial", "Bitcoin 2026", "What price will Bitcoin hit in 2026?",
        ("701501", "1339767", "701502", "1339768", "1345531"),
    ),
    Event(
        "google_searches", "Pop culture", "Top-5 Google searched 2026",
        "Top 5 Most Searched People on Google 2026",
        ("4425386", "6992350", "4425383", "4425380", "7121266"),
    ),
    Event(
        "iran_blockade", "Political", "Iran blockade ends",
        "US announces end of Iranian blockade by...?",
        ("4906129", "7155713", "7155711", "6907990", "3128886"),
    ),
    Event(
        "nhl_playoffs", "Sports", "Makes NHL playoffs",
        "Which teams will make the NHL Playoffs?",
        ("5084167", "5084162", "5084163", "5084166", "5084169"),
    ),
    Event(
        "epl_relegation", "Sports", "EPL relegation",
        "Premier League: Teams relegated (2026-27)",
        ("3848389", "3848398", "3848379", "3848396", "3848377"),
    ),
]

BY_SOURCE = {f"polymarket_{e.slug}": e for e in EVENTS}


def source_name(event: Event) -> str:
    return f"polymarket_{event.slug}"
