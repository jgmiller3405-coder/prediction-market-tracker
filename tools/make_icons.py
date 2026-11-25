"""Write the PNG app icons (no dependencies). Run: uv run python tools/make_icons.py"""
import struct
import zlib
from pathlib import Path

BLUE, WHITE = (37, 99, 235), (255, 255, 255)
OUT = Path(__file__).resolve().parent.parent / "icons"


def png(size: int, rounded: bool, inset: float) -> bytes:
    """Three white bars on a blue square. inset shrinks the artwork (maskable icons need a safe zone)."""
    s = size / 512
    bars = [(104, 288, 176, 408), (220, 208, 292, 408), (336, 112, 408, 408)]
    c = 256

    def inside_bar(x, y):
        x, y = (x / s - c) / inset + c, (y / s - c) / inset + c
        return any(x0 <= x < x1 and y0 <= y < y1 for x0, y0, x1, y1 in bars)

    def inside_round(x, y):
        r, cx = 96 * s, min(max(x, 96 * s), size - 96 * s)
        cy = min(max(y, 96 * s), size - 96 * s)
        return (x - cx) ** 2 + (y - cy) ** 2 <= r * r

    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            if rounded and not inside_round(x + .5, y + .5):
                raw += bytes((0, 0, 0, 0))
            else:
                raw += bytes((*(WHITE if inside_bar(x + .5, y + .5) else BLUE), 255))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    (OUT / "icon-192.png").write_bytes(png(192, True, 1.0))
    (OUT / "icon-512.png").write_bytes(png(512, True, 1.0))
    (OUT / "icon-maskable-512.png").write_bytes(png(512, False, 0.7))
    print("icons written")
