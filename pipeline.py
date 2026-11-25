"""Command line for the daily pipeline.

  python pipeline.py fetch    download every source into data/raw/<date>/ and log the results
  python pipeline.py build    rebuild data/history.csv from the raw files (nothing else is read)
  python pipeline.py status   write data/status.json
  python pipeline.py issue    open or update today's GitHub Issue and close the previous one
  python pipeline.py daily    fetch + build + status + issue (what the workflow runs)
"""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from tracker.fetch import run_fetch
from tracker.history import build_history
from tracker.issues import run_issue
from tracker.status import write_status

ROOT = Path(__file__).resolve().parent


def utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("command", choices=["fetch", "build", "status", "issue", "daily"])
    parser.add_argument("--date", default=None, help="UTC date YYYY-MM-DD (default: today)")
    parser.add_argument("--no-publish", action="store_true", help="issue: print instead of using gh")
    args = parser.parse_args(argv)
    date = args.date or utc_today()

    if args.command in ("fetch", "daily"):
        for r in run_fetch(ROOT, date):
            print(f"{r['source']}: {'ok' if r['ok'] else 'FAILED ' + r['error']} ({r['count']})")
    if args.command in ("build", "daily"):
        print(f"history rows: {len(build_history(ROOT))}")
    if args.command in ("status", "daily"):
        write_status(ROOT)
    if args.command in ("issue", "daily"):
        title, body = run_issue(ROOT, date, publish=not args.no_publish)
        if args.no_publish:
            print(f"# {title}\n{body}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
