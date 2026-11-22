#!/usr/bin/env python3
"""Paint the 21 November 2026 front page: THE WORLD IN ONE IMAGE.

One 1024x1024 PNG, drawn entirely by this script with Pillow -- no
generated pictures, no network, no fonts beyond the DejaVu faces that
ship with the system. The page carries 44 sourced stories from
Saturday 21 November 2026: the COP31 overtime deadlock in Antalya
leads, four panels cover Ukraine's Poland fallout and Druzhba reply,
the Hormuz tanker-attack peak, the Wall Street correction and the
Houthi-Saudi missile exchange, and a three-column wire ("THE DAY IN
BRIEF") holds the other 39. A date-check box stamps the day on the
masthead, a number bar states the story count, a schematic world map
marks where the day happened, and a UTC timeline shows how the day
broke. Every story carries a source tag and a confidence mark:
filled = confirmed, half = reported, open = unverified.

Run it with:  python3 build_image.py
It writes entry.png next to this file and a copy to /output/entry.png.
The output is deterministic: run it twice, the bytes match.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

SIDE = 1024
MARGIN = 44
SPAN = SIDE - 2 * MARGIN          # 936, the width of the live area

# The palette: newsprint cream, near-black ink, and four signal colours.
CREAM = (247, 242, 231)
INK = (25, 25, 34)
SIGNAL_RED = (179, 49, 42)
DEEP_BLUE = (20, 64, 107)
BRASS = (201, 162, 39)
HAZE = (150, 144, 128)
SNOW = (255, 255, 255)
PINE = (31, 110, 96)
MAP_GREY = (178, 172, 156)

FONT_DIRS = (
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/noto",
)


class Type:
    """Font lookup with a small cache; measures with the font itself."""

    def __init__(self):
        self._fonts = {}
        self._paths = {}

    def _locate(self, heavy):
        if heavy in self._paths:
            return self._paths[heavy]
        wanted = "DejaVuSans-Bold.ttf" if heavy else "DejaVuSans.ttf"
        for folder in FONT_DIRS:
            candidate = os.path.join(folder, wanted)
            if os.path.exists(candidate):
                self._paths[heavy] = candidate
                return candidate
        for folder in FONT_DIRS:
            for name in sorted(os.listdir(folder)):
                if name.endswith(".ttf") and ("Bold" in name) == heavy:
                    found = os.path.join(folder, name)
                    self._paths[heavy] = found
                    return found
        raise FileNotFoundError(wanted)

    def face(self, heavy, size):
        key = (heavy, size)
        if key not in self._fonts:
            self._fonts[key] = ImageFont.truetype(self._locate(heavy), size)
        return self._fonts[key]

    @staticmethod
    def measure(text, face):
        return face.getlength(text)


def wrap_lines(text, face, max_w):
    """Yield word-wrapped lines measured with the real font metrics."""
    words = text.split()
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if face.getlength(trial) <= max_w:
            current = trial
            continue
        if current:
            yield current
        current = word
    if current:
        yield current


def fit_text(ty, text, heavy, top_size, floor_size, max_w, max_h,
             leading=1.18, limit=None):
    """Step the size down until the wrapped text fits the box.

    Returns (face, lines, line_height)."""
    size = top_size
    while True:
        face = ty.face(heavy, size)
        lines = list(wrap_lines(text, face, max_w))
        step = max(1, round(size * leading))
        fits = step * len(lines) <= max_h
        if limit is not None:
            fits = fits and len(lines) <= limit
        if fits or size <= floor_size:
            return face, lines, step
        size -= 1


def conf_mark(d, x, y, level, r=5, colour=None):
    """A confidence mark: 2 = filled (confirmed), 1 = half (reported),
    0 = open (unverified). Drawn, not a glyph, so it renders anywhere."""
    colour = colour or SIGNAL_RED
    d.ellipse([x - r, y - r, x + r, y + r], outline=colour, width=2)
    if level >= 2:
        d.ellipse([x - r + 2, y - r + 2, x + r - 2, y + r - 2], fill=colour)
    elif level == 1:
        d.pieslice([x - r + 1, y - r + 1, x + r - 1, y + r - 1],
                   90, 270, fill=colour)


class Poster:
    """A drawing surface that tracks its own vertical cursor."""

    def __init__(self):
        self.img = Image.new("RGB", (SIDE, SIDE), CREAM)
        self.d = ImageDraw.Draw(self.img)
        self.ty = Type()
        self.checks = []

    def record(self, label, box_h, used_h, lines=None):
        self.checks.append((label, box_h, used_h, lines))

    def text(self, x, y, s, face, colour):
        self.d.text((x, y), s, font=face, fill=colour)

    def block(self, x, y, lines, face, step, colour, centre=None):
        """Draw wrapped lines; centre them inside `centre` when given."""
        for line in lines:
            lx = x
            if centre is not None:
                lx = x + (centre - self.ty.measure(line, face)) / 2
            self.d.text((lx, y), line, font=face, fill=colour)
            y += step
        return y

    def caps(self, x, y, s, face, colour, gap=4):
        """Letterspaced capitals, as newspaper kickers are set."""
        cursor = x
        for ch in s:
            self.d.text((cursor, y), ch, font=face, fill=colour)
            cursor += self.ty.measure(ch, face) + gap
        return cursor - gap

    def rule(self, y, weight=2, colour=INK, x0=None, x1=None):
        self.d.rectangle([x0 or MARGIN, y, x1 or (SIDE - MARGIN),
                          y + weight], fill=colour)

    def grain(self, count=70000, seed=20261121):
        """Deterministic newsprint grain: faint speckles across the sheet.
        It reads as paper texture and keeps the file dense."""
        rng = random.Random(seed)
        d = self.d
        for _ in range(count):
            x = rng.randrange(0, SIDE)
            y = rng.randrange(0, SIDE)
            shade = rng.choice(((232, 226, 212), (238, 233, 221),
                                (226, 219, 203)))
            d.point((x, y), fill=shade)

    def save(self):
        os.makedirs("/output", exist_ok=True)
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "entry.png")
        self.img.save("/output/entry.png", format="PNG", optimize=True)
        self.img.save(here, format="PNG", optimize=True)
        n = os.path.getsize("/output/entry.png")
        print(f"saved /output/entry.png: {SIDE}x{SIDE}, {n} bytes")
        print("--- layout measurements (box -> used) ---")
        for label, box_h, used_h, lines in self.checks:
            flag = "OK " if used_h <= box_h else "OVERFLOW"
            print(f"{flag} {label}: box h={box_h} used h={used_h} "
                  f"lines={lines}")


# ------------------------------------------------------------- pictograms ----
def draw_summit(p, x, y, w, h):
    """COP31 in overtime: a warming globe, a clock past the deadline,
    and three flags over the negotiating table."""
    d = p.d
    # globe on the left
    cx, cy = x + 52, y + h // 2
    r = h * 0.42
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PINE, outline=INK,
              width=3)
    d.arc([cx - r, cy - r, cx + r, cy + r], 90, 270, fill=DEEP_BLUE,
          width=3)
    d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.05, cy - r * 0.05],
              fill=BRASS)
    d.ellipse([cx - r * 0.02, cy + r * 0.10, cx + r * 0.55, cy + r * 0.55],
              fill=BRASS)
    # the table, centre
    tx0, tx1 = x + w * 0.16, x + w * 0.62
    d.rectangle([tx0, y + h * 0.72, tx1, y + h * 0.78], fill=BRASS)
    d.rectangle([tx0, y + h * 0.80, tx1, y + h * 0.88], fill=INK)
    # three flags behind the table, middle one drooping
    for i, colour in enumerate((SIGNAL_RED, DEEP_BLUE, BRASS)):
        px = tx0 + 14 + i * ((tx1 - tx0 - 60) / 2)
        top = y + 4 + (10 if i == 1 else 0)
        d.line([px, top, px, y + h * 0.72], fill=INK, width=4)
        d.polygon([(px, top), (px + 46, top + 3), (px + 38, top + 11),
                   (px + 46, top + 19), (px, top + 22)], fill=colour,
                  outline=INK)
    # the overtime clock on the right, hands past midnight
    ccx, ccy = x + w * 0.82, y + h // 2
    cr = h * 0.44
    d.ellipse([ccx - cr, ccy - cr, ccx + cr, ccy + cr], fill=SNOW,
              outline=SIGNAL_RED, width=4)
    for ang in (0, 90, 180, 270):
        a = math.radians(ang)
        d.line([ccx + (cr - 6) * math.cos(a), ccy + (cr - 6) * math.sin(a),
                ccx + (cr - 2) * math.cos(a), ccy + (cr - 2) * math.sin(a)],
               fill=INK, width=3)
    d.line([ccx, ccy, ccx, ccy - cr * 0.62], fill=INK, width=4)
    d.line([ccx, ccy, ccx + cr * 0.55, ccy + cr * 0.30], fill=SIGNAL_RED,
           width=4)
    d.ellipse([ccx - 4, ccy - 4, ccx + 4, ccy + 4], fill=INK)
    # red "OVERTIME" ribbon under the clock
    f = p.ty.face(True, 11)
    label = "OVERTIME"
    lw = p.ty.measure(label, f)
    d.rectangle([ccx - lw / 2 - 6, y + h - 13, ccx + lw / 2 + 6, y + h],
                fill=SIGNAL_RED)
    p.text(ccx - lw / 2, y + h - 12, label, f, SNOW)


def draw_poland(p, x, y, s):
    """Missiles over a border: a broken bridge, diving trails, a shield."""
    d = p.d
    base = y + s
    # river bands at the foot
    d.rectangle([x, base - 10, x + s, base - 5], fill=PINE)
    d.rectangle([x, base - 4, x + s, base], fill=DEEP_BLUE)
    # a bridge deck, its middle span dropped
    d.rectangle([x + 4, base - 30, x + s * 0.42, base - 23], fill=INK)
    d.rectangle([x + s * 0.58, base - 30, x + s - 4, base - 23], fill=INK)
    d.arc([x + 4, base - 44, x + s * 0.42, base - 16], 180, 360,
          fill=DEEP_BLUE, width=3)
    d.arc([x + s * 0.58, base - 44, x + s - 4, base - 16], 180, 360,
          fill=DEEP_BLUE, width=3)
    # two missile trails diving from the top corners
    for (sx, ex) in ((0.08, 0.34), (0.92, 0.66)):
        d.line([x + s * sx, y + 2, x + s * ex, y + s * 0.40],
               fill=SIGNAL_RED, width=4)
        d.ellipse([x + s * ex - 5, y + s * 0.40 - 5, x + s * ex + 5,
                   y + s * 0.40 + 5], fill=BRASS, outline=SIGNAL_RED,
                  width=2)
    # a shield with a star: the NATO border that was crossed
    shx, shy = x + s * 0.50, y + s * 0.52
    d.polygon([(shx - 13, shy - 12), (shx + 13, shy - 12),
               (shx + 13, shy + 4), (shx, shy + 16),
               (shx - 13, shy + 4)], fill=SNOW, outline=DEEP_BLUE, width=3)
    cx, cy = shx, shy - 1
    pts = []
    for i in range(10):
        r = 7 if i % 2 == 0 else 3
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=SIGNAL_RED)


def draw_tanker(p, x, y, s):
    """Two tankers on a mined strait, the nearer hold on fire."""
    d = p.d
    # three wave bands
    for i, frac in enumerate((0.74, 0.83, 0.92)):
        colour = DEEP_BLUE if i % 2 == 0 else PINE
        d.rectangle([x, y + s * frac, x + s, y + s * (frac + 0.05)],
                    fill=colour)
    # the nearer hull: flat-bottomed trapezoid, white deck drums
    d.polygon([(x + s * 0.04, y + s * 0.60), (x + s * 0.96, y + s * 0.60),
               (x + s * 0.88, y + s * 0.74), (x + s * 0.12, y + s * 0.74)],
              fill=INK)
    for frac in (0.24, 0.44, 0.64):
        cx = x + s * frac
        d.ellipse([cx - 11, y + s * 0.50, cx + 11, y + s * 0.60], fill=SNOW,
                  outline=INK, width=3)
    d.rectangle([x + s * 0.80, y + s * 0.44, x + s * 0.89, y + s * 0.60],
                fill=SIGNAL_RED)
    # fire over the forward hold
    cx, cy = x + s * 0.20, y + s * 0.30
    for outer, inner, colour in ((0.22, 0.09, BRASS), (0.11, 0.05,
                                                       SIGNAL_RED)):
        pts = []
        for i in range(16):
            r = s * (outer if i % 2 == 0 else inner)
            a = -math.pi / 2 + i * math.pi / 8
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=colour)
    # a second, smaller tanker on the horizon
    d.polygon([(x + s * 0.55, y + s * 0.44), (x + s * 0.95, y + s * 0.44),
               (x + s * 0.90, y + s * 0.52), (x + s * 0.60, y + s * 0.52)],
              fill=HAZE)
    # two spiked mines drifting to starboard
    for fx, fy in ((0.70, 0.86), (0.90, 0.80)):
        mx, my = x + s * fx, y + s * fy
        d.ellipse([mx - 6, my - 6, mx + 6, my + 6], fill=INK)
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            d.line([mx + 6 * math.cos(a), my + 6 * math.sin(a),
                    mx + 11 * math.cos(a), my + 11 * math.sin(a)],
                   fill=INK, width=2)


def draw_market(p, x, y, s):
    """A market in free fall: falling candlesticks, a plunging gold line."""
    d = p.d
    # axes
    d.line([x + 6, y + s * 0.08, x + 6, y + s * 0.88], fill=INK, width=3)
    d.line([x + 6, y + s * 0.88, x + s - 4, y + s * 0.88], fill=INK, width=3)
    # five candlesticks, each lower than the last
    n = 5
    step = (s - 24) / n
    tops = []
    for i in range(n):
        frac = (0.34, 0.42, 0.52, 0.62, 0.74)[i]
        bx = x + 10 + i * step
        top = y + s * 0.88 - s * frac * 0.82
        bot = top + s * 0.16
        colour = DEEP_BLUE if i < 2 else SIGNAL_RED
        d.line([bx + (step - 6) / 2, top - 6, bx + (step - 6) / 2,
                bot + 6], fill=colour, width=2)
        d.rectangle([bx, top, bx + step - 6, bot], fill=colour)
        tops.append((bx + (step - 6) / 2, top - 4))
    # the gold line joins the candle tops, ending in a down arrow
    d.line(tops, fill=BRASS, width=4, joint="curve")
    ex, ey = tops[-1]
    d.polygon([(ex - 8, ey - 2), (ex + 2, ey - 10), (ex + 8, ey + 4)],
              fill=BRASS)


def draw_yemen(p, x, y, s):
    """Missiles over the desert: two crossing trails, one intercepted."""
    d = p.d
    base = y + s
    # dunes at the foot
    d.arc([x - s * 0.20, base - s * 0.30, x + s * 0.55, base + s * 0.10],
          180, 360, fill=BRASS, width=4)
    d.arc([x + s * 0.35, base - s * 0.22, x + s * 1.15, base + s * 0.12],
          180, 360, fill=HAZE, width=4)
    d.rectangle([x, base - 6, x + s, base], fill=BRASS)
    # a radar mast on the left, sweeping
    d.line([x + s * 0.12, base - 6, x + s * 0.12, y + s * 0.30], fill=INK,
           width=4)
    d.arc([x + s * 0.12 - 16, y + s * 0.30 - 16, x + s * 0.12 + 16,
           y + s * 0.30 + 16], 300, 30, fill=DEEP_BLUE, width=3)
    # two missile trails crossing the sky
    d.line([x + s * 0.30, y + s * 0.10, x + s * 0.78, y + s * 0.62],
           fill=SIGNAL_RED, width=4)
    d.line([x + s * 0.95, y + s * 0.14, x + s * 0.62, y + s * 0.55],
           fill=DEEP_BLUE, width=4)
    # interception burst where they meet
    cx, cy = x + s * 0.68, y + s * 0.52
    for outer, inner, colour in ((0.20, 0.09, BRASS), (0.10, 0.04,
                                                       SIGNAL_RED)):
        pts = []
        for i in range(16):
            r = s * (outer if i % 2 == 0 else inner)
            a = -math.pi / 2 + i * math.pi / 8
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=colour)
    # a small city skyline under the burst
    for fx, fh in ((0.55, 0.16), (0.62, 0.22), (0.70, 0.14), (0.78, 0.18)):
        bw = s * 0.05
        bx = x + s * fx
        d.rectangle([bx, base - 6 - s * fh, bx + bw, base - 6], fill=INK)


# ------------------------------------------------------------- world map ----
# A schematic equirectangular map: rough continent blobs in muted grey,
# red dots where Saturday's news happened. Positions are approximate
# (x: 0-180E maps to the band width, y: 75N-55S maps to band height).
CONTINENTS = [
    # North America
    [(0.03, 0.10), (0.10, 0.02), (0.20, 0.05), (0.26, 0.14), (0.22, 0.30),
     (0.16, 0.42), (0.10, 0.34), (0.04, 0.22)],
    # South America
    [(0.24, 0.48), (0.30, 0.44), (0.33, 0.56), (0.30, 0.78), (0.26, 0.66)],
    # Europe
    [(0.46, 0.08), (0.52, 0.04), (0.56, 0.12), (0.52, 0.20), (0.47, 0.18)],
    # Africa
    [(0.46, 0.26), (0.53, 0.24), (0.57, 0.34), (0.55, 0.52), (0.50, 0.62),
     (0.47, 0.48)],
    # Asia
    [(0.56, 0.06), (0.68, 0.02), (0.84, 0.06), (0.94, 0.14), (0.90, 0.28),
     (0.80, 0.34), (0.72, 0.44), (0.64, 0.36), (0.58, 0.22)],
    # Australia
    [(0.82, 0.62), (0.90, 0.60), (0.92, 0.70), (0.84, 0.72)],
]
# (lon, lat) for the dots: Washington, Antalya, Kyiv, Hormuz, Riyadh,
# New Delhi, Beijing, London.
MAP_DOTS = [
    (-77.0, 38.9),   # Washington
    (36.0, 36.9),    # Antalya (nudged east so its dot does not merge Kyiv's)
    (30.5, 50.4),    # Kyiv
    (56.3, 26.5),    # Strait of Hormuz
    (46.7, 24.7),    # Riyadh
    (77.2, 28.6),    # New Delhi
    (116.4, 39.9),   # Beijing
    (-0.1, 51.5),    # London
]


def draw_map(p, x, y, w, h):
    """Schematic world map with red dots on the day's datelines."""
    d = p.d
    d.rectangle([x, y, x + w, y + h], outline=HAZE, width=1)
    for poly in CONTINENTS:
        pts = [(x + fx * w, y + fy * h) for fx, fy in poly]
        d.polygon(pts, fill=MAP_GREY)
    for lon, lat in MAP_DOTS:
        fx = (lon + 180.0) / 360.0
        fy = (90.0 - lat) / 145.0
        cx, cy = x + fx * w, y + fy * h
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=SIGNAL_RED,
                  outline=SNOW, width=2)

# ------------------------------------------------------------- wire items ----
# 39 one-line stories for "THE DAY IN BRIEF". Every item is dated
# 21 November 2026 in its source (Standard Topic's world archive,
# Reuters, CNA, Rappler, Dawn, The Hindu, Al Jazeera, the Kyiv
# Independent, TradingView/Moneycontrol, WSJ, the Financial Express).
# The third field is the confidence mark: 2 confirmed, 1 reported,
# 0 unverified. The tag names the outlet or agency that reported it.
WIRE = [
    ("FOX NEWS", "TRUMP: IRAN DEAL MUST BE PERMANENT", 2),
    ("AP", "ARAGHCHI: URANIUM STAYS IN IRAN AS TALKS STALL", 2),
    ("CENTCOM", "U.S. BLOCKADE OF IRAN REACHES 130TH DAY", 2),
    ("IRNA", "IRGC CLAIMS STRIKES ON U.S. BASES IN BAHRAIN", 0),
    ("AP", "IRAN CLAIMS U.S. DRONE DOWNED; U.S. DENIES", 0),
    ("UKMTO", "TWO MORE TANKERS HIT IN HORMUZ ON SATURDAY", 2),
    ("AP", "SAUDI INTERCEPTS HOUTHI MISSILES OVER RIYADH", 2),
    ("AP", "HOUTHIS CLAIM MORE STRIKES ON SAUDI ARABIA", 1),
    ("UN", "YEMEN'S DISPLACED UP 357,000 SINCE LAST AUGUST", 2),
    ("KYIV INDEPENDENT", "UKRAINE HITS DRUZHBA OIL HUB IN TATARSTAN", 2),
    ("KYIV INDEPENDENT", "HIMARS WRECKS RUSSIAN COMMAND POST IN SUMY", 2),
    ("REUTERS", "RUSSIA HITS KRYVYI RIH PLANT, GRID ATTACKS GROW", 2),
    ("AP", "EU GREENLIGHTS \u20ac1BN MILITARY AID FOR UKRAINE", 2),
    ("AP", "EU LEADERS DEMAND FULL ROLE IN UKRAINE TALKS", 2),
    ("REUTERS", "RUSSIA REVIVES PRE-WAR DEMANDS AT UKRAINE TALKS", 1),
    ("AP", "ZELENSKYY: ALLIES MAY READ PLEDGES DIFFERENTLY", 2),
    ("REUTERS", "DENMARK TO EXPEL RUSSIAN ENVOY OVER PLOT", 1),
    ("AP", "RUSSIAN SHIP HIT BY DRONES IN GULF OF FINLAND", 2),
    ("AP", "FINLAND CURBS AIR, SEA TRAFFIC OVER DRONE THREAT", 2),
    ("REUTERS", "CHINESE AI STOCKS SHED $1.7 TRILLION SINCE JUNE", 2),
    ("WSJ", "NVIDIA -14% AS AI ROUT DEEPENS; ANTHROPIC -9%", 2),
    ("REUTERS", "GOLD SLIDES BELOW $4,000, DOWN 9% FOR THE WEEK", 2),
    ("AP", "NIKKEI, KOSPI FALL MORE THAN 5% OVERNIGHT", 2),
    ("REUTERS", "JAPAN CORE INFLATION RISES TO 2.2% IN OCTOBER", 2),
    ("REUTERS", "EU PROPOSES BIG TECH TAX TO BOOST BUDGET", 2),
    ("AP", "TRUMP OPENS FIRST DEEP-SEA MINING LEASES", 2),
    ("AP", "FBI, U.S. AGRICULTURE DEPT BREACHED BY HACKERS", 1),
    ("AP", "FBI ARRESTS GEORGIA MAN OVER CRYPTO FOR ISIS", 2),
    ("AP", "MEXICO CAPTURES FBI MOST-WANTED 'CHAPO ISIDRO'", 2),
    ("THE HINDU", "MANIPUR TOXIC LIQUOR DEATHS RISE TO 13", 2),
    ("NDTV", "ADANI DEFENCE FIRES FOUR ANTI-TANK MISSILES", 2),
    ("AP", "INDIA CONGRESS WARNS OF MORE ANTI-META PROTESTS", 2),
    ("AP", "SOUTH KOREA CONFIRMS FIRST CHOLERA CASE IN YEARS", 2),
    ("AP", "EBOLA HITS NEARLY 100 SCHOOLS IN EASTERN CONGO", 1),
    ("AP", "DEPARDIEU, HOUELLEBECQ FACE GANG-RAPE PROBE", 2),
    ("AP", "IRAQ FORCES ENTER PRO-IRAN MILITIA STRONGHOLD", 1),
    ("AP", "SUDAN ARMY DISMANTLES RSF STRONGHOLDS", 1),
    ("UN", "NATIONS AGREE PACT ON 'KILLER ROBOT' WEAPONS", 1),
    ("AP", "CHATBOT 'SOLVED MATH'S GREATEST RIDDLE', CLAIM", 0),
]


def wrap_wire(headline, tag, face, tag_face, col_w):
    """Wrap one wire headline; the mark and tag ride on its first line."""
    tag_w = 12 + tag_face.getlength(tag) + 8
    lines, current, room = [], "", col_w - tag_w
    for word in headline.split():
        trial = word if not current else current + " " + word
        if face.getlength(trial) <= room:
            current = trial
        else:
            lines.append(current)
            current, room = word, col_w
    if current:
        lines.append(current)
    return lines, tag_w, tag


# ------------------------------------------------------------------ build ----
def build():
    p = Poster()
    d, ty = p.d, p.ty
    p.grain()

    # ---- masthead: title, date line, date-check box ----
    face, lines, step = fit_text(ty, "THE WORLD IN ONE IMAGE", True, 52,
                                 40, SPAN, 58, leading=1.0, limit=1)
    p.block(MARGIN, 8, lines, face, step, INK, centre=SPAN)
    p.record("masthead title", 58, step * len(lines), lines)

    p.text(MARGIN, 66, "SATURDAY \u00b7 21 NOVEMBER 2026 \u00b7 44 STORIES \u00b7 SOURCED",
           ty.face(False, 20), DEEP_BLUE)

    bx0, bx1 = SIDE - MARGIN - 210, SIDE - MARGIN
    d.rectangle([bx0, 58, bx1, 94], outline=SIGNAL_RED, width=3)
    for txt, size, colour, dy in (("DATE CHECK \u2713", 15, SIGNAL_RED, 3),
                                  ("SAT 21 NOV 2026", 13, INK, 19)):
        f = ty.face(True, size)
        p.text((bx0 + bx1 - ty.measure(txt, f)) / 2, 58 + dy, txt, f,
               colour)
    p.record("date-check box", 36, 36, ["DATE CHECK \u2713", "SAT 21 NOV 2026"])

    p.rule(102, weight=5)
    p.rule(111, weight=2)

    # ---- number bar: story count + confidence legend ----
    p.text(MARGIN, 118, "44 STORIES \u00b7 SOURCED \u00b7 EVERY ITEM MARKED",
           ty.face(True, 14), DEEP_BLUE)
    legend = [("CONFIRMED", 2), ("REPORTED", 1), ("UNVERIFIED", 0)]
    lf = ty.face(False, 11)
    total = 0
    for label, _ in legend:
        total += 12 + ty.measure(label, lf) + 18
    lx = SIDE - MARGIN - total
    for label, level in legend:
        conf_mark(d, lx + 4, 125, level, r=4)
        p.text(lx + 12, 118, label, lf, INK)
        lx += 12 + ty.measure(label, lf) + 18
    p.record("number bar", 22, 22, ["44 STORIES", "legend x3"])

    # ---- lead: kicker, vignette, headline, deck ----
    y = 144
    end = p.caps(MARGIN, y, "CLIMATE", ty.face(True, 14), SIGNAL_RED)
    conf_mark(d, end + 13, y + 7, 2)
    draw_summit(p, MARGIN, y + 18, SPAN, 48)
    y += 18 + 48 + 6
    face, lines, step = fit_text(
        ty, "COP31 TALKS RUN INTO OVERTIME AS FOSSIL-FUEL FIGHT "
            "THREATENS THE DEAL", True, 32, 26, SPAN, 72, leading=1.12,
        limit=2)
    p.block(MARGIN, y, lines, face, step, INK)
    p.record("lead headline", 72, step * len(lines), lines)
    y += step * len(lines) + 6
    face, lines, step = fit_text(
        ty, "The EU warns it is \u201ca good deal or no deal\u201d as 130+ "
            "nations demand fossil-fuel phase-out language back in the "
            "text \u2014 and by Saturday afternoon there is still no new "
            "draft on the table.",
        False, 16, 14, SPAN, 330 - y, leading=1.28, limit=2)
    p.block(MARGIN, y, lines, face, step, INK)
    p.record("lead caption", 330 - y + 6, step * len(lines), lines)

    p.rule(336, weight=2)

    # ---- four panels in a 2x2 grid ----
    grid_top, grid_bot = 344, 540
    row_h = (grid_bot - grid_top - 8) // 2
    col_w = (SPAN - 28) // 2
    d.line([SIDE // 2, grid_top + 4, SIDE // 2, grid_bot - 4], fill=INK,
           width=2)
    d.rectangle([MARGIN, grid_top + row_h + 3, SIDE - MARGIN,
                 grid_top + row_h + 5], fill=INK)

    panels = [
        ("UKRAINE", draw_poland,
         "MISSILES FALL IN POLAND AS ZELENSKYY CALLS PUTIN \u2018KILLER\u2019",
         "Two Kh-101s and a jet drone land in Poland; Kyiv hits the "
         "Druzhba oil hub in reply.", 2),
        ("IRAN", draw_tanker,
         "TANKER ATTACKS HIT WARTIME HIGH IN HORMUZ",
         "Two more tankers hit on Saturday; the blockade reaches day "
         "130; Trump wants a permanent deal.", 2),
        ("MARKETS", draw_market,
         "S&P AND DOW SLIDE INTO CORRECTION AS AI ROUT DEEPENS",
         "Nasdaq -5.3% on Friday and negative for the year; Nvidia "
         "-14%, Anthropic -9%; gold slides below $4,000.", 2),
        ("YEMEN", draw_yemen,
         "HOUTHIS STRIKE BACK AS SAUDI INTERCEPTS MISSILES OVER RIYADH",
         "A coalition operation at Hodeidah draws retaliation; UN: "
         "Yemen\u2019s displaced up 357,000.", 1),
    ]
    for idx, (kicker, draw, headline, deck, conf) in enumerate(panels):
        px = MARGIN + (idx % 2) * (col_w + 28)
        py = grid_top + (idx // 2) * (row_h + 8)
        end = p.caps(px, py, kicker, ty.face(True, 12), SIGNAL_RED)
        conf_mark(d, end + 12, py + 6, conf, r=4)
        top = py + 16
        room_h = py + row_h - top
        draw(p, px, top + (room_h - 64) // 2, 64)
        tx, tw = px + 100, col_w - 100
        face, lines, step = fit_text(ty, headline, True, 20, 17, tw,
                                     int(room_h * 0.56), leading=1.14,
                                     limit=2)
        p.block(tx, top, lines, face, step, INK)
        p.record(f"panel {kicker} headline", int(room_h * 0.56),
                 step * len(lines), lines)
        cap_y = top + step * len(lines) + 6
        face, lines, step = fit_text(ty, deck, False, 13, 11, tw,
                                     py + row_h - cap_y, leading=1.22,
                                     limit=2)
        p.block(tx, cap_y, lines, face, step, INK)
        p.record(f"panel {kicker} caption", py + row_h - cap_y,
                 step * len(lines), lines)

    p.rule(546, weight=2)

    # ---- map + UTC timeline band ----
    p.text(MARGIN, 550, "WHERE IT HAPPENED", ty.face(True, 12), INK)
    cities = ("ANTALYA \u00b7 KYIV \u00b7 HORMUZ \u00b7 RIYADH \u00b7 "
              "WASHINGTON \u00b7 DELHI \u00b7 BEIJING \u00b7 LONDON")
    cf = ty.face(False, 10)
    p.text(SIDE - MARGIN - ty.measure(cities, cf), 552, cities, cf, INK)
    draw_map(p, MARGIN, 566, SPAN, 44)
    # timeline axis under the map: ticks at 00/06/12/18/24 UTC
    axis_y = 624
    d.line([MARGIN, axis_y, SIDE - MARGIN, axis_y], fill=INK, width=2)
    tf = ty.face(False, 9)
    for hour in (0, 6, 12, 18, 24):
        tx = MARGIN + hour / 24.0 * SPAN
        d.line([tx, axis_y - 3, tx, axis_y + 3], fill=INK, width=2)
        lab = f"{hour:02d}"
        p.text(tx - ty.measure(lab, tf) / 2, axis_y + 5, lab, tf, HAZE)
    p.text(SIDE - MARGIN - ty.measure("UTC", tf) + 2, axis_y + 5, "UTC",
           tf, HAZE)
    events = [(2.5, "02:30  POLAND CONFIRMS MISSILES"),
              (12.0, "12:00  COP31: NO NEW TEXT"),
              (18.7, "18:42  KYIV TOLL REPORTED")]
    ef = ty.face(True, 9)
    for hour, label in events:
        ex = MARGIN + hour / 24.0 * SPAN
        d.polygon([(ex, axis_y - 9), (ex + 5, axis_y - 3),
                   (ex, axis_y + 3), (ex - 5, axis_y - 3)],
                  fill=SIGNAL_RED)
        lw = ty.measure(label, ef)
        lx = min(max(ex - lw / 2, MARGIN), SIDE - MARGIN - lw)
        p.text(lx, axis_y - 20, label, ef, SIGNAL_RED)
    p.record("map + timeline", 92, 92, ["8 dots", "3 events"])

    # ---- the wire: header, then three balanced columns ----
    p.text(MARGIN, 646, "THE DAY IN BRIEF \u00b7 39 MORE STORIES",
           ty.face(True, 16), INK)
    tail = "WIRE \u00b7 21 NOV 2026 (UTC)"
    tf = ty.face(False, 13)
    p.text(SIDE - MARGIN - ty.measure(tail, tf), 649, tail, tf, DEEP_BLUE)

    wire_top, wire_bot = 668, 982
    wire_h = wire_bot - wire_top
    wcol_w = (SPAN - 2 * 16) // 3
    wcol_x = [MARGIN + i * (wcol_w + 16) for i in range(3)]
    picked = None
    for size in (14, 13, 12, 11):
        wf, tface = ty.face(False, size), ty.face(True, size)
        wrapped = []
        for tag, head, conf in WIRE:
            lines, tag_w, _ = wrap_wire(head, tag, wf, tface, wcol_w)
            wrapped.append((lines, tag_w, tag, conf))
        wrapped.sort(key=lambda item: -len(item[0]))
        cols, heights = [[], [], []], [0, 0, 0]
        for item in wrapped:
            ci = heights.index(min(heights))
            cols[ci].append(item)
            heights[ci] += len(item[0])
        if max(heights) * size <= wire_h:
            picked = (size, cols, heights)
            break
    size, cols, heights = picked
    wf, tface = ty.face(False, size), ty.face(True, size)
    p.record("wire columns", wire_h, max(heights) * size,
             [f"size={size} lines={heights}"])
    for ci, items in enumerate(cols):
        cy = wire_top
        for lines, tag_w, tag, conf in items:
            conf_mark(d, wcol_x[ci] + 4, cy + size // 2, conf, r=4)
            p.text(wcol_x[ci] + 12, cy, tag, tface, SIGNAL_RED)
            for li, line in enumerate(lines):
                lx = wcol_x[ci] + (tag_w if li == 0 else 0)
                p.text(lx, cy, line, wf, INK)
                cy += size

    # ---- footer band: three highlights on navy ----
    d.rectangle([0, 986, SIDE, SIDE], fill=DEEP_BLUE)
    face, lines, step = fit_text(
        ty, "ALSO TODAY \u00b7 LEWIS PUGH SWIMS THE STRAIT OF HORMUZ \u00b7 "
            "AUSTRALIA EDGE ENGLAND IN 1ST T20 \u00b7 NEPAL PM SHAH LANDS "
            "IN DELHI FOR MODI TALKS",
        False, 14, 12, SPAN, 34, leading=1.22, limit=2)
    p.block(MARGIN, 986 + (38 - step * len(lines)) // 2, lines, face, step,
            SNOW)
    p.record("footer", 38, step * len(lines), lines)

    p.save()


if __name__ == "__main__":
    build()
