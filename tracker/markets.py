"""The 5 Polymarket events we track and the outcome markets we keep from each.

Each outcome market is one item (23 items in total). The ids were chosen on
2026-11-25 as the outcomes with the largest one-day price swings among markets
that close after 2026-12-03 (the earliest tracked close is 2026-12-15).
The tool asks the API for these ids only, so the raw files hold nothing else.
"""
from typing import NamedTuple


class Event(NamedTuple):
    slug: str          # used in the source name and raw file name
    short: str         # prefix of every item name
    title: str         # full Polymarket event title
    market_ids: tuple  # the outcome markets we track


EVENTS = [
    Event(
        "bitcoin", "Bitcoin 2026", "What price will Bitcoin hit in 2026?",
        ("701501", "1339767", "701502", "1339768", "1345531"),
    ),
    Event(
        "anthropic", "Anthropic valuation",
        "Will Anthropic's valuation hit __ by December 31?",
        ("7185169", "2299960", "2299962", "2299955", "2299954"),
    ),
    Event(
        "google_searches", "Top-5 Google searched 2026",
        "Top 5 Most Searched People on Google 2026",
        ("4425386", "6992350", "4425383", "4425380", "7121266"),
    ),
    Event(
        "iran_blockade", "Iran blockade ends",
        "US announces end of Iranian blockade by...?",
        ("4906129", "7155713", "7155711", "6907990", "3128886"),
    ),
    Event(
        "netanyahu", "Netanyahu out",
        "Netanyahu out by...?",
        ("6254930", "567688", "6254929"),
    ),
]

BY_SOURCE = {f"polymarket_{e.slug}": e for e in EVENTS}


def source_name(event: Event) -> str:
    return f"polymarket_{event.slug}"
