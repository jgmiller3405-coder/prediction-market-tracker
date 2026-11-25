# Prediction Market Odds Tracker

[![tests](https://github.com/jgmiller3405-coder/prediction-market-tracker/actions/workflows/tests.yml/badge.svg)](https://github.com/jgmiller3405-coder/prediction-market-tracker/actions/workflows/tests.yml)
[![daily](https://github.com/jgmiller3405-coder/prediction-market-tracker/actions/workflows/daily.yml/badge.svg)](https://github.com/jgmiller3405-coder/prediction-market-tracker/actions/workflows/daily.yml)

Every day, on its own, this tool downloads the latest odds for 23 outcomes in 5 volatile
[Polymarket](https://polymarket.com) prediction markets, adds them to a history (one row per item per day),
reports what moved in a GitHub Issue, and publishes the result as an installable website.

- **Site:** https://jgmiller3405-coder.github.io/prediction-market-tracker/
- **Repository:** https://github.com/jgmiller3405-coder/prediction-market-tracker

## What is tracked

Five multi-outcome markets were chosen on 2026-11-25 because their outcomes had large one-day price swings
and every tracked outcome closes after 2026-12-03 (the earliest is 2026-12-15). Each outcome is one **item**
(23 in all). The item key is Polymarket's numeric market id, which does not change from day to day.

| Source name | Polymarket event | Items |
|---|---|---|
| `polymarket_bitcoin` | What price will Bitcoin hit in 2026? | 5 |
| `polymarket_anthropic` | Will Anthropic's valuation hit __ by December 31? | 5 |
| `polymarket_google_searches` | Top 5 Most Searched People on Google 2026 | 5 |
| `polymarket_iran_blockade` | US announces end of Iranian blockade by...? | 5 |
| `polymarket_netanyahu` | Netanyahu out by...? | 3 |

The list of ids lives in `tracker/markets.py`. To track something else, edit it there.

## Sources

| Source | Format | URL | Login |
|---|---|---|---|
| one per event above | JSON | `https://gamma-api.polymarket.com/markets?id=<id>&id=<id>...` | none, no API key |

The request asks for the tracked market ids only, so **the raw files keep only the tracked outcomes**
(a Bitcoin event has 47 outcomes; we keep 5). Each source is a separate request. If one fails (three
attempts), it writes no raw file that day, is recorded as failed, and the other sources still run.

## Files

| Path | What it does |
|---|---|
| `pipeline.py` | Command line: `fetch`, `build`, `status`, `issue`, `daily` |
| `tracker/markets.py` | The 5 events and 23 market ids that are tracked |
| `tracker/fetch.py` | Downloads each source, saves the raw file, records every source result in `data/source_log.csv` |
| `tracker/rawstore.py` | Writes and reads the gzipped raw files |
| `tracker/convert.py` | Converts a raw response into rows with the common columns |
| `tracker/history.py` | Builds `data/history.csv` from the raw files alone |
| `tracker/moves.py` | The move rule |
| `tracker/status.py` | Writes `data/status.json` |
| `tracker/issues.py` | Builds and publishes the daily GitHub Issue |
| `tests/` | pytest suite (conversion, move rule, history, same-day rerun, status, issue) |
| `.github/workflows/daily.yml` | Runs the pipeline every day at 06:17 UTC and commits the result |
| `.github/workflows/tests.yml` | Runs the tests on every push |
| `data/raw/<date>/<source>.json.gz` | What each source returned, compressed, in the format it came in |
| `data/history.csv` | One row per item per day |
| `data/status.json` | Describes the latest run |
| `data/source_log.csv` | Result of every source on every day (`date,source,ok,count,error`) |
| `index.html`, `browse.html`, `trends.html` | The three site pages: Today, Browse, Trends |
| `lib.js` | Shared pure functions: CSV parser, the move rule in JavaScript, trend statistics |
| `app.js`, `app.css` | Shared navigation bar, data loading, shortlist, and the one set of colors and fonts |
| `sw.js`, `manifest.webmanifest`, `icons/` | Make the site installable and usable offline |
| `vendor/chart.umd.js` | Chart.js 4.4.1 (stored locally so charts work offline) |
| `tools/make_icons.py` | Generates the PNG app icons |

## `data/history.csv` columns

The rows are sorted by `date`, then `item_id`. A value the source does not report is left empty.

| Column | Meaning | Unit |
|---|---|---|
| `date` | UTC date of the run that produced the row | `YYYY-MM-DD` |
| `item_id` | Polymarket market id (the key) | text |
| `item` | Item name: short event name plus the outcome | text |
| `source` | The source (raw file name) the row came from | text |
| `event` | Full title of the Polymarket event | text |
| `end_date` | Date the market is scheduled to close | `YYYY-MM-DD` |
| `closed` | `true` once Polymarket marks the market closed | true/false |
| `yes_pct` | Market-implied probability of Yes (the odds) | percent, 0 to 100 |
| `best_bid_pct` | Highest price a buyer offers for Yes | percent |
| `best_ask_pct` | Lowest price a seller asks for Yes | percent |
| `day_change_pts` | Change in the Yes price over the previous 24 hours, as reported by Polymarket | percentage points |
| `volume_24h_usd` | Money traded in the last 24 hours | US dollars |
| `volume_total_usd` | Money traded since the market opened | US dollars |
| `liquidity_usd` | Liquidity in the market's order book | US dollars |

## `data/status.json`

`run_time` (UTC), `first_run_date` (earliest raw file), `days_with_success` (dates with at least one raw
file), `items` (items in the latest run), `new_today` and `gone_today` (lists of item ids that appeared or
disappeared since the previous date in the history), and `sources` (a list of `name`, `ok`, `count`).
`count` is the number of markets the source returned.

## The move rule

An item's **move** is the change in `yes_pct` (percentage points) between the latest run and the previous
date in the history. Items are ranked by the **size** of that change, up or down. Ties go to the item with the
larger `volume_24h_usd`, then the smaller `item_id`. The daily Issue lists the **top 5** moves with their old
and new values, plus any item that appeared or disappeared (an item that is in only one of the two days).
An item whose Yes probability did not change is not listed. The Issue is opened every day, even with no
changes, and closes the previous day's Issue. A second run on the same day updates that day's Issue.

## Build the history from the raw files

```
uv run python pipeline.py build
```

This reads only `data/raw/` and rewrites `data/history.csv`; running it again gives the same file, and a
change to a conversion rule applies to every day. (`uv run python pipeline.py daily` does the whole run:
fetch, build, status, issue.)

## Run it yourself

```
uv sync
uv run python pipeline.py fetch      # today's raw files
uv run python pipeline.py build      # history.csv
uv run python pipeline.py status     # status.json
uv run python pipeline.py issue --no-publish   # print the issue instead of posting it
uv run pytest
```

A second run on the same UTC date replaces that day's raw files, rebuilds the history and counts the day once.

## Site

Serve the repository folder with any static server (for example `python -m http.server`) and open
`index.html`. Pages load `data/history.csv` and `data/status.json` in the browser and compute everything
there. Online, the pages fetch the data files from the network; offline, the service worker serves the last
copy it saved. The site can be installed from the browser as an app.

- **Today**: time of the last run, status of every source, counts, latest values with change since the previous run, biggest moves.
- **Browse**: filters (event, close date, minimum Yes %, minimum 24h volume), name search, sort by every numeric column, and a star that saves an item to a shortlist in the browser.
- **Trends**: a chart of every numeric value with an item picker, and five findings with explanation, numbers and chart.

## GitHub setup

- Pages: Settings, Pages, deploy from branch `main`, folder `/ (root)`.
- Actions: the default `GITHUB_TOKEN` is used with `contents: write` and `issues: write`. No secrets are needed because the Polymarket API needs no key.
