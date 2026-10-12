"""
Generates a fully compliant Windows multi-layer icon (.ico) file.
Includes standard 32-bit DIB layers (16x16, 24x24, 32x32, 48x48, 64x64, 128x128)
and a 256x256 PNG layer, ensuring crisp rendering across all Windows Explorer view modes
(Details, List, Small Icons, Tiles, Medium, Large, Extra Large).
"""

import io
import struct
from PIL import Image


def generate_windows_ico(src_path: str = "favicon.png", dst_path: str = "favicon.ico"):
    src = Image.open(src_path).convert("RGBA")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    entries = []

    for sz in sizes:
        resized = src.resize((sz, sz), Image.Resampling.LANCZOS)
        if sz == 256:
            buf = io.BytesIO()
            resized.save(buf, format="PNG")
            data = buf.getvalue()
        else:
            width = height = sz
            pixels_bgra = bytearray()
            row_and_bytes = ((width + 31) // 32) * 4
            and_mask = bytearray(row_and_bytes * height)

            for y in range(height - 1, -1, -1):
                for x in range(width):
                    r, g, b, a = resized.getpixel((x, y))
                    pixels_bgra.extend([b, g, r, a])
                    if a < 128:
                        byte_idx = (height - 1 - y) * row_and_bytes + (x // 8)
                        bit_idx = 7 - (x % 8)
                        and_mask[byte_idx] |= (1 << bit_idx)

            bih = struct.pack(
                "<IiiHHIIiiII",
                40, width, height * 2, 1, 32, 0,
                len(pixels_bgra) + len(and_mask),
                0, 0, 0, 0
            )
            data = bih + bytes(pixels_bgra) + bytes(and_mask)

        w_b = 0 if sz == 256 else sz
        h_b = 0 if sz == 256 else sz
        entries.append((w_b, h_b, data))

    with open(dst_path, "wb") as f:
        f.write(struct.pack("<HHH", 0, 1, len(entries)))
        offset = 6 + len(entries) * 16
        for w_b, h_b, data in entries:
            f.write(struct.pack("<BBBBHHII", w_b, h_b, 0, 0, 1, 32, len(data), offset))
            offset += len(data)
        for _, _, data in entries:
            f.write(data)


if __name__ == "__main__":
    generate_windows_ico()
