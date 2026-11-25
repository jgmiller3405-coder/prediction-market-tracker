"""The daily GitHub Issue: biggest moves since the previous run, plus appeared/gone items."""
import json
import subprocess
import tempfile
from pathlib import Path

from .fetch import read_log
from .history import load_history
from .moves import TOP_N, compute_moves, day_index, previous_date

LABEL = "daily"


def build_issue(history: list, date: str, failed_sources: list = ()) -> tuple:
    """Return (title, markdown body). The title is the date."""
    cur = day_index(history, date)
    prev_date = previous_date(history, date)
    prev = day_index(history, prev_date) if prev_date else {}
    names = {r["item_id"]: r["item"] for r in history}
    lines = [f"Run date: **{date}** (UTC). Compared with: **{prev_date or 'no earlier run'}**.", ""]

    if not prev_date:
        lines.append("First run in the history: there is no previous run to compare with.")
    else:
        result = compute_moves(prev, cur)
        lines.append(f"### Biggest moves (top {TOP_N} by change in Yes probability)")
        if result["moves"]:
            lines += ["", "| Item | Old Yes % | New Yes % | Change (pts) |", "|---|---:|---:|---:|"]
            for m in result["moves"]:
                lines.append(f"| {m['item']} | {m['old']:.2f} | {m['new']:.2f} | {m['delta']:+.2f} |")
        else:
            lines.append("")
            lines.append("No item changed its Yes probability since the previous run.")
        lines += ["", "### Appeared"]
        lines += [f"- {cur[i]['item']}" for i in result["appeared"]] or ["- none"]
        lines += ["", "### Disappeared"]
        lines += [f"- {names.get(i, i)}" for i in result["disappeared"]] or ["- none"]

    if failed_sources:
        lines += ["", "### Sources that failed today"] + [f"- {s}" for s in failed_sources]
    return date, "\n".join(lines) + "\n"


def run_issue(root: Path, date: str, publish: bool = True) -> tuple:
    root = Path(root)
    history = load_history(root / "data" / "history.csv")
    failed = [r["source"] for r in read_log(root / "data" / "source_log.csv")
              if r["date"] == date and r["ok"] != "true"]
    title, body = build_issue(history, date, failed)
    if publish:
        publish_issue(title, body)
    return title, body


def _gh(*args) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def publish_issue(title: str, body: str) -> None:
    """Create (or update) the issue titled with the date, and close every other open daily issue."""
    _gh("label", "create", LABEL, "--color", "1f6feb", "--force")
    open_issues = json.loads(_gh("issue", "list", "--label", LABEL, "--state", "open",
                                 "--json", "number,title", "--limit", "200"))
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(body)
        body_file = f.name
    same = [i for i in open_issues if i["title"] == title]
    if same:
        _gh("issue", "edit", str(same[0]["number"]), "--body-file", body_file)
    else:
        _gh("issue", "create", "--title", title, "--body-file", body_file, "--label", LABEL)
    for issue in open_issues:
        if issue["title"] != title:
            _gh("issue", "close", str(issue["number"]), "--comment", f"Superseded by the {title} issue.")
