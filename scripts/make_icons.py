#!/usr/bin/env python3
"""Generate VPN-Follower app icons with the standard library only.

Draws a "radar / target lock" motif (concentric rings + a crosshair) on a dark
indigo background -- evoking following a signal through its layers. Produces the
PNG sizes a PWA / native packagers expect. No third-party dependencies.
"""

from __future__ import annotations

import math
import os
import struct
import zlib

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vpnfollower", "web", "icons")

BG = (15, 18, 38)        # deep indigo
RING = (94, 234, 212)    # teal
ACCENT = (129, 140, 248)  # indigo-300


def _blend(base, top, alpha):
    return tuple(round(b + (t - b) * alpha) for b, t in zip(base, top))


def _pixel(x, y, size):
    cx = cy = (size - 1) / 2
    dx, dy = x - cx, y - cy
    dist = math.hypot(dx, dy)
    radius = size * 0.46
    color = BG

    # concentric rings
    if dist <= radius:
        ring_w = size * 0.035
        for k in (0.34, 0.62, 0.9):
            edge = abs(dist - radius * k)
            if edge < ring_w:
                color = _blend(color, RING, 1 - edge / ring_w)
    # outer rim
    rim = abs(dist - radius)
    if rim < size * 0.03:
        color = _blend(color, ACCENT, 1 - rim / (size * 0.03))
    # crosshair
    cross_w = size * 0.012
    if dist <= radius:
        if abs(dx) < cross_w or abs(dy) < cross_w:
            color = _blend(color, ACCENT, 0.85)
    # centre dot
    if dist < size * 0.05:
        color = RING
    return color


def _png(size: int) -> bytes:
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter type 0 for the row
        for x in range(size):
            raw += bytes(_pixel(x, y, size))
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # 8-bit RGB
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    for size in (192, 512):
        path = os.path.join(OUT_DIR, f"icon-{size}.png")
        with open(path, "wb") as fh:
            fh.write(_png(size))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
