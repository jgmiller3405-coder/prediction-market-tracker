import csv
import gzip
import json
from datetime import datetime, timezone

from tracker import rawstore
from tracker.convert import COLUMNS
from tracker.fetch import read_log, run_fetch
from tracker.history import build_history, load_history
from tracker.issues import build_issue
from tracker.markets import EVENTS, source_name
from tracker.status import write_status

TOTAL = sum(len(e.market_ids) for e in EVENTS)
D1, D2 = "2026-11-25", "2026-11-26"


def test_raw_files_are_gzipped_at_the_fixed_path(tmp_path, good_fetcher):
    run_fetch(tmp_path, D1, good_fetcher)
    path = tmp_path / "data" / "raw" / D1 / "polymarket_bitcoin.json.gz"
    assert path.exists()
    assert isinstance(json.loads(gzip.decompress(path.read_bytes())), list)


def test_history_has_one_row_per_item_per_day_sorted(tmp_path, good_fetcher):
    for d in (D2, D1):  # fetched out of order on purpose
        run_fetch(tmp_path, d, good_fetcher)
    rows = build_history(tmp_path)
    assert len(rows) == 2 * TOTAL
    keys = [(r["date"], r["item_id"]) for r in rows]
    assert keys == sorted(keys) and len(set(keys)) == len(keys)
    with open(tmp_path / "data" / "history.csv", newline="", encoding="utf-8") as f:
        assert next(csv.reader(f)) == COLUMNS


def test_building_again_gives_the_same_file(tmp_path, good_fetcher):
    run_fetch(tmp_path, D1, good_fetcher)
    run_fetch(tmp_path, D2, good_fetcher)
    build_history(tmp_path)
    first = (tmp_path / "data" / "history.csv").read_bytes()
    build_history(tmp_path)
    assert (tmp_path / "data" / "history.csv").read_bytes() == first


def test_history_depends_on_the_raw_files_alone(tmp_path, good_fetcher):
    run_fetch(tmp_path, D1, good_fetcher)
    build_history(tmp_path)
    (tmp_path / "data" / "history.csv").write_text("garbage")
    (tmp_path / "data" / "source_log.csv").unlink()
    rows = build_history(tmp_path)
    assert len(rows) == TOTAL and len(load_history(tmp_path / "data" / "history.csv")) == TOTAL


def test_a_failed_source_writes_no_raw_file_and_is_logged(tmp_path, good_fetcher):
    good_fetcher.state["fail"].add("polymarket_bitcoin")
    results = run_fetch(tmp_path, D1, good_fetcher)
    assert not (tmp_path / "data" / "raw" / D1 / "polymarket_bitcoin.json.gz").exists()
    failed = [r for r in results if not r["ok"]]
    assert [r["source"] for r in failed] == ["polymarket_bitcoin"] and failed[0]["error"] == "boom"
    assert len(results) == len(EVENTS)  # the other sources still ran
    assert len(read_log(tmp_path / "data" / "source_log.csv")) == len(EVENTS)
    rows = build_history(tmp_path)
    assert len(rows) == TOTAL - len(EVENTS[0].market_ids)
    assert "polymarket_bitcoin" not in {r["source"] for r in rows}


def test_a_second_run_on_the_same_day_replaces_that_days_data(tmp_path, good_fetcher):
    run_fetch(tmp_path, D1, good_fetcher)
    build_history(tmp_path)
    good_fetcher.state["yes"] = 0.7
    good_fetcher.state["fail"].add("polymarket_netanyahu")
    run_fetch(tmp_path, D1, good_fetcher)
    rows = build_history(tmp_path)
    assert len({r["date"] for r in rows}) == 1                     # still one day
    assert len(rows) == TOTAL - len(EVENTS[-1].market_ids)          # old netanyahu rows are gone
    assert {r["yes_pct"] for r in rows} == {70.0}                   # new values replaced old
    log = read_log(tmp_path / "data" / "source_log.csv")
    assert len(log) == len(EVENTS)                                  # one block of log rows per date
    assert write_status(tmp_path)["days_with_success"] == 1


def test_status_file_keys_and_counts(tmp_path, good_fetcher):
    run_fetch(tmp_path, D1, good_fetcher)
    build_history(tmp_path)
    good_fetcher.state["fail"].add("polymarket_anthropic")
    run_fetch(tmp_path, D2, good_fetcher)
    build_history(tmp_path)
    status = write_status(tmp_path, datetime(2026, 11, 26, 6, 0, tzinfo=timezone.utc))
    assert status["run_time"] == "2026-11-26T06:00:00Z"
    assert status["first_run_date"] == D1 and status["days_with_success"] == 2
    assert status["items"] == TOTAL - 5
    assert status["new_today"] == [] and len(status["gone_today"]) == 5
    by_name = {s["name"]: s for s in status["sources"]}
    assert len(by_name) == len(EVENTS)
    assert by_name["polymarket_anthropic"] == {"name": "polymarket_anthropic", "ok": False, "count": 0}
    assert by_name["polymarket_bitcoin"]["ok"] is True and by_name["polymarket_bitcoin"]["count"] == 5
    assert json.loads((tmp_path / "data" / "status.json").read_text()) == status


def test_days_with_success_counts_dates_not_runs(tmp_path, good_fetcher):
    for d in (D1, D1, D2):
        run_fetch(tmp_path, d, good_fetcher)
    assert len(rawstore.list_days(tmp_path)) == 2


def test_issue_lists_moves_and_disappeared_items(tmp_path, good_fetcher):
    run_fetch(tmp_path, D1, good_fetcher)
    good_fetcher.state["yes"] = 0.6
    good_fetcher.state["fail"].add("polymarket_netanyahu")
    run_fetch(tmp_path, D2, good_fetcher)
    build_history(tmp_path)
    title, body = build_issue(load_history(tmp_path / "data" / "history.csv"), D2)
    assert title == D2
    assert "+10.00" in body and "50.00" in body and "60.00" in body
    assert "Disappeared" in body and "Netanyahu out" in body


def test_issue_is_written_even_on_a_day_with_no_changes(tmp_path, good_fetcher):
    run_fetch(tmp_path, D1, good_fetcher)
    run_fetch(tmp_path, D2, good_fetcher)
    build_history(tmp_path)
    title, body = build_issue(load_history(tmp_path / "data" / "history.csv"), D2)
    assert title == D2 and "No item changed" in body


def test_first_day_issue_has_nothing_to_compare(tmp_path, good_fetcher):
    run_fetch(tmp_path, D1, good_fetcher)
    build_history(tmp_path)
    _, body = build_issue(load_history(tmp_path / "data" / "history.csv"), D1)
    assert "First run" in body
