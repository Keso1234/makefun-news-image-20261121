"""Render THE WORLD TODAY, a one-page news poster for Saturday 21 Nov 2026.

Pure standard library: draws into an RGB bytearray and encodes the PNG by
hand (zlib + struct). Text uses a small 5x7 bitmap font defined below, drawn
at integer scales so every glyph stays crisp at any size. No network, no
randomness, no timestamps: the same code always renders the same bytes.
"""

import hashlib
import math
import struct
import zlib
from pathlib import Path

W = 1024
H = 1024

PAPER = (246, 241, 230)
NAVY = (16, 35, 63)
RED = (179, 38, 30)
GOLD = (217, 164, 65)
INK = (26, 26, 26)
WHITE = (255, 255, 255)
BLACK = (17, 17, 17)
TEAL = (14, 107, 92)
AMBER = (138, 90, 0)
BLUE = (29, 78, 216)
GREY = (205, 198, 182)

# 5x7 bitmap font, one glyph per character. Each glyph is 7 rows of 5 cells,
# '#' set and '.' clear. Uppercase letters, digits and the punctuation the
# poster needs; anything else renders as a space.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
}

FONT.update({
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "#.#..", "..#..", "..#..", "..#..", "#####"),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "/": ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "\u2022": (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
})


def normalise(text):
    """Uppercase and fold the few non-font characters the copy uses."""
    out = []
    for ch in text.upper():
        if ch in ("\u2018", "\u2019", "\u02bc"):
            out.append("'")
        elif ch in ("\u2013", "\u2014", "\u2212"):
            out.append("-")
        elif ch not in FONT:
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


# ---------------------------------------------------------------- canvas


def new_canvas():
    buf = bytearray(W * H * 3)
    rect(buf, 0, 0, W, H, PAPER)
    return buf


def px(buf, x, y, colour):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = colour[0]
        buf[i + 1] = colour[1]
        buf[i + 2] = colour[2]


def rect(buf, x, y, w, h, colour):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(colour) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        buf[i:i + len(row)] = row


def vgrad(buf, x, y, w, h, top, bottom):
    """Vertical gradient, top colour at y fading to bottom colour at y+h."""
    for yy in range(max(0, y), min(H, y + h)):
        t = (yy - y) / max(1, h - 1)
        c = tuple(round(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        rect(buf, x, yy, w, 1, c)


def disc(buf, cx, cy, r, colour, clip=None):
    """Filled circle; clip=(ccx, ccy, cr) keeps pixels inside that circle."""
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            dx, dy = xx - cx, yy - cy
            if dx * dx + dy * dy > r * r:
                continue
            if clip is not None:
                ddx, ddy = xx - clip[0], yy - clip[1]
                if ddx * ddx + ddy * ddy > clip[2] * clip[2]:
                    continue
            px(buf, xx, yy, colour)


def ring(buf, cx, cy, r, thick, colour):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d2 = (xx - cx) ** 2 + (yy - cy) ** 2
            if (r - thick) ** 2 <= d2 <= r * r:
                px(buf, xx, yy, colour)


def poly(buf, pts, colour):
    """Scanline fill of a simple polygon."""
    ys = [p[1] for p in pts]
    n = len(pts)
    for yy in range(min(ys), max(ys) + 1):
        xs = []
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 <= yy < y2) or (y2 <= yy < y1):
                xs.append(x1 + (yy - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for xx in range(int(xs[i]), int(xs[i + 1]) + 1):
                px(buf, xx, yy, colour)


def star_points(cx, cy, r_out, r_in, points=5):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(i * 180 / points - 90)
        pts.append((round(cx + r * math.cos(a)), round(cy + r * math.sin(a))))
    return pts


BURST_FACTORS = (1.00, 0.80, 1.12, 0.88, 1.06, 0.78,
                 1.14, 0.86, 1.02, 0.82, 1.08, 0.90)


def burst_points(cx, cy, r_out, r_in, rot):
    """Jagged 12-spike blast outline; fixed factors keep it deterministic."""
    pts = []
    n = len(BURST_FACTORS)
    for i, f in enumerate(BURST_FACTORS):
        a = math.radians(i * 360 / n + rot - 90)
        pts.append((round(cx + r_out * f * math.cos(a)),
                    round(cy + r_out * f * math.sin(a))))
        a2 = math.radians((i + 0.5) * 360 / n + rot - 90)
        pts.append((round(cx + r_in * math.cos(a2)),
                    round(cy + r_in * math.sin(a2))))
    return pts


# ---------------------------------------------------------------- text


def glyph_width(scale):
    return 6 * scale


def text_width(text, scale):
    text = normalise(text)
    if not text:
        return 0
    return len(text) * glyph_width(scale) - scale


def draw_glyph(buf, x, y, ch, scale, colour):
    rows = FONT.get(ch, FONT[" "])
    for ry, row in enumerate(rows):
        for rx, cell in enumerate(row):
            if cell == "#":
                rect(buf, x + rx * scale, y + ry * scale, scale, scale, colour)


def draw_line(buf, x, y, text, scale, colour):
    text = normalise(text)
    for i, ch in enumerate(text):
        draw_glyph(buf, x + i * glyph_width(scale), y, ch, scale, colour)


def wrap(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    lines = []
    for para in text.split("\n"):
        words = normalise(para).split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if text_width(trial, scale) <= max_width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                while text_width(word, scale) > max_width:
                    cut = max(1, max_width // glyph_width(scale))
                    lines.append(word[:cut])
                    word = word[cut:]
                cur = word
        if cur or not lines:
            lines.append(cur)
    return lines


def draw_text(buf, x, y, text, scale, colour, align="left", max_width=None,
              line_gap=8, centre_x=None):
    """Draw text, wrapping at max_width when given. Returns the y just below
    the last line. With align='center', centre_x is the line centre."""
    lines = wrap(text, max_width, scale) if max_width else [normalise(text)]
    line_h = 7 * scale + line_gap
    for i, line in enumerate(lines):
        ly = y + i * line_h
        if align == "center":
            lx = centre_x - text_width(line, scale) // 2
        else:
            lx = x
        draw_line(buf, lx, ly, line, scale, colour)
    return y + len(lines) * line_h - line_gap


# ---------------------------------------------------------------- icons


def draw_lead_visual(buf, x, y, w, h):
    """Night blast over a Gulf skyline: the Bahrain strikes, drawn flat."""
    rect(buf, x, y, w, h, NAVY)
    ix, iy, iw, ih = x + 4, y + 4, w - 8, h - 8
    vgrad(buf, ix, iy, iw, ih, (22, 33, 58), (122, 52, 26))
    for sx, sy in [(30, 26), (90, 14), (150, 34), (210, 18), (260, 40),
                   (320, 22), (60, 60), (180, 58), (300, 58), (120, 90)]:
        rect(buf, ix + sx, iy + sy, 3, 3, WHITE)
    cx, cy = ix + iw // 2 + 8, iy + 118
    # smoke rising behind the blast, drawn first so the fire overlaps it
    for sx, sy, sr in [(cx - 68, cy - 82, 22), (cx - 8, cy - 96, 22),
                       (cx + 52, cy - 86, 22), (cx + 94, cy - 66, 18)]:
        disc(buf, sx, sy, sr, (70, 70, 78))
    # jagged layered fireball: irregular spikes read as a blast, not a sun
    poly(buf, burst_points(cx, cy, 100, 54, 0), (193, 39, 45))
    poly(buf, burst_points(cx, cy, 78, 42, 9), (244, 123, 32))
    poly(buf, burst_points(cx, cy, 54, 30, 18), (255, 210, 63))
    disc(buf, cx, cy, 20, (255, 240, 180))
    # embers flung out from the blast
    for ex, ey, ec in [(-120, -40, (244, 123, 32)), (-100, 30, (255, 210, 63)),
                       (110, -50, (255, 210, 63)), (130, 10, (244, 123, 32)),
                       (-60, -110, (255, 210, 63)), (70, -105, (244, 123, 32))]:
        rect(buf, cx + ex, cy + ey, 4, 4, ec)
    # skyline silhouettes along the bottom
    base = iy + ih
    for dx, bw, bh in [(0, 44, 54), (48, 30, 80), (82, 52, 44),
                       (138, 26, 96), (168, 60, 58), (232, 34, 88),
                       (270, 48, 50), (322, 46, 72)]:
        rect(buf, ix + dx, base - bh, bw, bh, (8, 10, 18))
    # lit windows, fixed positions
    for wx, wy in [(10, 34), (24, 22), (56, 52), (60, 30), (96, 26),
                   (146, 66), (150, 44), (182, 34), (206, 22),
                   (240, 58), (282, 30), (334, 46)]:
        rect(buf, ix + wx, base - wy, 4, 6, (255, 210, 63))
    # caption strip
    rect(buf, ix, base - 30, iw, 30, (10, 15, 26))
    draw_text(buf, 0, base - 22, "STRIKES ON BAHRAIN", 2, WHITE,
              align="center", centre_x=ix + iw // 2)


def draw_globe(buf, cx, cy, r):
    """Blue globe with green land, for the COP31 climate story."""
    disc(buf, cx, cy, r, (46, 111, 205))
    clip = (cx, cy, r)
    for dx, dy, br in [(-12, -10, 12), (12, 8, 14), (16, -16, 8),
                       (-16, 16, 7), (0, -24, 6)]:
        disc(buf, cx + dx, cy + dy, br, (74, 160, 90), clip=clip)
    ring(buf, cx, cy, r, 3, WHITE)


def draw_shield(buf, cx, cy, w, h):
    """Gold badge shield with a star, for the cartel arrest."""
    pts = [(cx - w // 2, cy - h // 2), (cx + w // 2, cy - h // 2),
           (cx + w // 2, cy + 6), (cx, cy + h // 2),
           (cx - w // 2, cy + 6)]
    poly(buf, pts, (255, 210, 63))
    poly(buf, star_points(cx, cy - 6, 20, 8), AMBER)


def draw_flags(buf, x, y, w, h):
    """EU flag beside the Indonesian flag, for the trade deal."""
    half = w // 2 - 6
    rect(buf, x, y, half, h, (0, 51, 153))
    ccx, ccy = x + half // 2, y + h // 2
    for i in range(12):
        a = math.radians(i * 30 - 90)
        disc(buf, round(ccx + 20 * math.cos(a)),
             round(ccy + 20 * math.sin(a)), 3, (255, 204, 0))
    fx = x + half + 12
    rect(buf, fx, y, half, h // 2, (206, 17, 38))
    rect(buf, fx, y + h // 2, half, h - h // 2, WHITE)


# ---------------------------------------------------------------- layout


def compose():
    buf = new_canvas()
    # masthead
    rect(buf, 0, 0, W, 140, NAVY)
    draw_text(buf, 0, 38, "THE WORLD TODAY", 9, WHITE,
              align="center", centre_x=W // 2)
    rect(buf, 0, 140, W, 5, GOLD)
    # date strip: the day this poster sums up, named loud and clear
    draw_text(buf, 0, 162, "SATURDAY, 21 NOVEMBER 2026", 5, RED,
              align="center", centre_x=W // 2)
    rect(buf, 28, 177, 91, 4, RED)
    rect(buf, 905, 177, 91, 4, RED)
    rect(buf, 0, 218, W, 4, NAVY)
    # lead story: Iran strikes Bahrain
    draw_text(buf, 28, 240, "MIDDLE EAST - WAR IN THE GULF", 3, RED)
    head_end = draw_text(buf, 28, 272, "IRAN STRIKES U.S. BASES IN BAHRAIN",
                         6, INK, max_width=572, line_gap=8)
    rect(buf, 28, head_end + 14, 120, 5, RED)
    draw_text(buf, 28, head_end + 32,
              "TEHRAN TARGETS AMERICAN SITES; BAHRAIN REPORTS FIRE AT AN "
              "INDUSTRIAL FACILITY.",
              3, INK, max_width=572, line_gap=6)
    draw_lead_visual(buf, 620, 238, 376, 286)
    rect(buf, 0, 540, W, 4, NAVY)
    # three secondary stories
    columns = [
        {"x": 16, "band": TEAL, "label": "CLIMATE - COP31",
         "headline": "COP31 TALKS DEADLOCK",
         "deck": "FOSSIL-FUEL FIGHT PUSHES SUMMIT INTO OVERTIME"},
        {"x": 352, "band": AMBER, "label": "MEXICO - CRIME",
         "headline": "MOST-WANTED DRUG LORD SEIZED",
         "deck": "FBI-LISTED KINGPIN HELD AFTER SHOOT-OUT"},
        {"x": 688, "band": BLUE, "label": "ASIA - EUROPE",
         "headline": "EU-INDONESIA DEAL SIGNED",
         "deck": "TRADE PACT SEALED AFTER TEN YEARS OF TALKS"},
    ]
    for i, col in enumerate(columns):
        x = col["x"]
        rect(buf, x, 552, 320, 120, col["band"])
        if i == 0:
            draw_globe(buf, x + 160, 600, 34)
        elif i == 1:
            draw_shield(buf, x + 160, 600, 64, 72)
        else:
            draw_flags(buf, x + 40, 566, 240, 68)
        draw_text(buf, 0, 640, col["label"], 3, WHITE,
                  align="center", centre_x=x + 160)
        hend = draw_text(buf, x, 688, col["headline"], 4, INK,
                         max_width=320, line_gap=8)
        rect(buf, x, hend + 10, 60, 4, RED)
        draw_text(buf, x, hend + 26, col["deck"], 3, INK,
                  max_width=320, line_gap=5)
    rect(buf, 344, 560, 3, 328, GREY)
    rect(buf, 680, 560, 3, 328, GREY)
    # bottom ticker: three more real stories from the day
    rect(buf, 0, 900, W, 4, GOLD)
    rect(buf, 0, 904, W, 120, BLACK)
    draw_text(buf, 28, 922, "ALSO TODAY:", 3, GOLD)
    draw_text(buf, 240, 922, "6.7 QUAKE SHAKES PERU \u2022 FBI PROBES", 3, WHITE)
    draw_text(buf, 28, 952, "HACK OF ITS CRIME DATABASE \u2022 INDIA", 3, WHITE)
    draw_text(buf, 28, 982, "720/9, A RECORD TEST SCORE IN NZ", 3, WHITE)
    return buf


# ---------------------------------------------------------------- png


def png_bytes(buf):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none, per scanline
        raw.extend(buf[y * W * 3:(y + 1) * W * 3])

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    data = png_bytes(compose())
    out = Path(__file__).resolve().parent / "entry.png"
    out.write_bytes(data)
    print("wrote %s %d bytes sha256=%s"
          % (out, len(data), hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
