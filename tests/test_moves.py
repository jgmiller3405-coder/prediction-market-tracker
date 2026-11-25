from tracker.moves import compute_moves, previous_date


def row(item_id, yes, vol=100, name=None):
    return {"item_id": item_id, "item": name or f"Item {item_id}", "yes_pct": str(yes),
            "volume_24h_usd": str(vol)}


def idx(*rows):
    return {r["item_id"]: r for r in rows}


def test_moves_are_ranked_by_absolute_change_in_either_direction():
    prev = idx(row("a", 50), row("b", 40), row("c", 10))
    cur = idx(row("a", 52), row("b", 30), row("c", 15))
    result = compute_moves(prev, cur)
    assert [m["item_id"] for m in result["moves"]] == ["b", "c", "a"]
    assert [m["delta"] for m in result["moves"]] == [-10.0, 5.0, 2.0]
    assert (result["moves"][0]["old"], result["moves"][0]["new"]) == (40.0, 30.0)


def test_ties_go_to_higher_volume_then_smaller_id():
    prev = idx(row("a", 10), row("b", 10), row("c", 10))
    cur = idx(row("a", 15, vol=5), row("b", 15, vol=50), row("c", 15, vol=50))
    assert [m["item_id"] for m in compute_moves(prev, cur)["moves"]] == ["b", "c", "a"]


def test_only_the_top_n_are_listed_and_zero_moves_are_dropped():
    prev = idx(*[row(str(i), 10) for i in range(8)])
    cur = idx(*[row(str(i), 10 + i) for i in range(8)])
    result = compute_moves(prev, cur, top=3)
    assert [m["item_id"] for m in result["moves"]] == ["7", "6", "5"]
    assert all(m["delta"] != 0 for m in compute_moves(prev, cur)["moves"])


def test_a_day_with_no_changes_has_no_moves():
    same = idx(row("a", 50), row("b", 20))
    assert compute_moves(same, same) == {"moves": [], "appeared": [], "disappeared": []}


def test_items_that_appear_or_disappear_are_reported_not_ranked():
    prev = idx(row("a", 50), row("gone", 5))
    cur = idx(row("a", 51), row("new", 90))
    result = compute_moves(prev, cur)
    assert result["appeared"] == ["new"] and result["disappeared"] == ["gone"]
    assert [m["item_id"] for m in result["moves"]] == ["a"]


def test_an_empty_value_cannot_move():
    prev = idx(row("a", ""))
    cur = idx(row("a", 40))
    assert compute_moves(prev, cur)["moves"] == []


def test_previous_date_skips_gaps():
    rows = [{"date": "2026-11-20"}, {"date": "2026-11-23"}, {"date": "2026-11-25"}]
    assert previous_date(rows, "2026-11-25") == "2026-11-23"
    assert previous_date(rows, "2026-11-20") is None
