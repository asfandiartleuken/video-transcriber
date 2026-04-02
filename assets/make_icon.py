"""Generate a tiny placeholder app.ico without external deps.

Creates a 16x16 32-bit RGBA icon with a simple gradient.
"""

from __future__ import annotations

import struct
from pathlib import Path


def _build_icon_bytes() -> bytes:
    width = 16
    height = 16

    # Build XOR bitmap (BGRA, bottom-up)
    rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            r = 40 + x * 5
            g = 110 + y * 3
            b = 200
            a = 255
            row += bytes((b & 0xFF, g & 0xFF, r & 0xFF, a))
        rows.append(bytes(row))
    # Bottom-up: reverse rows
    xor_bitmap = b"".join(reversed(rows))

    # AND mask: 1-bit mask, here fully opaque (all zeros). Row padded to 4 bytes.
    and_row = b"\x00\x00\x00\x00"
    and_mask = and_row * height

    # BITMAPINFOHEADER
    bi_size = 40
    bi_width = width
    bi_height = height * 2  # includes XOR + AND mask
    planes = 1
    bitcount = 32
    compression = 0
    image_size = len(xor_bitmap) + len(and_mask)
    ppm = 2835  # ~72 DPI
    header = struct.pack(
        "<IIIHHIIIIII",
        bi_size,
        bi_width,
        bi_height,
        planes,
        bitcount,
        compression,
        image_size,
        ppm,
        ppm,
        0,
        0,
    )

    dib = header + xor_bitmap + and_mask

    # ICONDIR
    reserved = 0
    icon_type = 1
    count = 1
    icondir = struct.pack("<HHH", reserved, icon_type, count)

    bytes_in_res = len(dib)
    image_offset = 6 + 16  # ICONDIR + one ICONDIRENTRY
    icondir_entry = struct.pack(
        "<BBBBHHII",
        width,
        height,
        0,  # color count
        0,  # reserved
        1,  # planes
        32,  # bitcount
        bytes_in_res,
        image_offset,
    )

    return icondir + icondir_entry + dib


def main() -> None:
    out_path = Path(__file__).resolve().parent / "app.ico"
    out_path.write_bytes(_build_icon_bytes())
    print(f"Wrote placeholder icon to {out_path}")


if __name__ == "__main__":
    main()
