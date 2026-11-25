"""Reading and writing the compressed raw files: data/raw/<date>/<source>.<format>.gz"""
import gzip
import shutil
from pathlib import Path


def raw_root(root: Path) -> Path:
    return Path(root) / "data" / "raw"


def write_raw(root: Path, date: str, source: str, ext: str, content: bytes) -> Path:
    """Gzip with a fixed mtime so the same bytes always give the same file."""
    path = raw_root(root) / date / f"{source}.{ext}.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            gz.write(content)
    return path


def clear_day(root: Path, date: str) -> None:
    """Delete one day's raw files (a second run on the same day replaces them)."""
    day = raw_root(root) / date
    if day.exists():
        shutil.rmtree(day)


def read_raw(path: Path) -> bytes:
    with gzip.open(path, "rb") as f:
        return f.read()


def source_of(path: Path) -> str:
    """polymarket_bitcoin.json.gz -> polymarket_bitcoin"""
    return path.name.split(".")[0]


def list_days(root: Path) -> dict:
    """{date: [raw file paths]} for every day that has at least one raw file."""
    out = {}
    base = raw_root(root)
    if not base.exists():
        return out
    for day in sorted(p for p in base.iterdir() if p.is_dir()):
        files = sorted(day.glob("*.gz"))
        if files:
            out[day.name] = files
    return out
