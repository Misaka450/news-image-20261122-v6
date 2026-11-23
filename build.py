#!/usr/bin/env python3
"""
v6 Broadsheet News Infographic Builder — Sunday 22 November 2026
Strategy: Cut story count from 34 to 26 while achieving 100% illustration
coverage (14 main cards with 110px editorial illustrations + 12 briefs with
24x24px line-art icons), open cream newsprint breathing room, and a clean
low-density y896-1024 bottom band.

Pure Python + Pillow deterministic 1024x1024 renderer + 300x300 preview.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# 1. Canvas, Palette & Typography Configuration
# ---------------------------------------------------------------------------

CANVAS_W = 1024
CANVAS_H = 1024
MARGIN_X = 14
INNER_W = CANVAS_W - 2 * MARGIN_X  # 996 px
GAP = 10
CARD_PAD = 8
MAX_BYTES = 1_048_576  # 1 MiB limit

OUT_DIR = Path(__file__).resolve().parent
ENTRY_PATH = OUT_DIR / "entry.png"
PREVIEW_PATH = OUT_DIR / "preview-300.png"

# Warm newsprint broadsheet palette (champion-calibrated open paper aesthetic)
BG_PAPER = "#F8F3E9"
DATE_CHECK_BG = "#FBF7EE"
RULE_HAIRLINE = "#DCD3C4"
RULE_DARK = "#18202D"

INK_DARK = "#121923"
INK_BODY = "#222A36"
INK_MUTED = "#4E5766"

NAVY_BAR = "#101D3D"
NAVY_UTC = "#162647"
NAVY_DIV = "#2E436F"
MAP_OCEAN = "#15254A"

CRIMSON = "#9E1F28"
GOLD = "#EBC365"
WHITE = "#FFFFFF"

REGION_ORDER = [
    "EUROPE",
    "ASIA-PACIFIC",
    "AMERICAS",
    "MIDDLE EAST",
    "AFRICA",
    "OCEANIA",
    "WORLD",
]

# Restrained, earthy editorial region palette
REGION_COLORS: Dict[str, str] = {
    "EUROPE": "#235773",
    "ASIA-PACIFIC": "#B45E1F",
    "AMERICAS": "#33548E",
    "MIDDLE EAST": "#A6232B",
    "AFRICA": "#3B7042",
    "OCEANIA": "#6E4B8A",
    "WORLD": "#4D5560",
}

# Soft tinted illustration backdrops (low edge noise, crisp figure-ground contrast)
ART_BACKDROPS: Dict[str, str] = {
    "EUROPE": "#E2ECF2",
    "ASIA-PACIFIC": "#F4E7DA",
    "AMERICAS": "#E3E9F4",
    "MIDDLE EAST": "#F3E3E4",
    "AFRICA": "#E3EDE4",
    "OCEANIA": "#ECE5F2",
    "WORLD": "#E6E8EB",
}

MAP_LAND_FILL: Dict[str, str] = {
    "EUROPE": "#467794",
    "ASIA-PACIFIC": "#9E6E46",
    "AMERICAS": "#4E6D9E",
    "MIDDLE EAST": "#994A50",
    "AFRICA": "#4E8256",
    "OCEANIA": "#775B91",
    "WORLD": "#657180",
}

FONT_PATHS = {
    "serif_bold": "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "serif_reg": "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "serif_cond_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf",
    "sans_bold": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "sans_reg": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "sans_cond_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
    "sans_cond_reg": "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
    "mono_bold": "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
}

_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}


def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    cache_key = (key, size)
    if cache_key not in _FONT_CACHE:
        path = FONT_PATHS[key]
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required font: {path}")
        _FONT_CACHE[cache_key] = ImageFont.truetype(path, size)
    return _FONT_CACHE[cache_key]


# ---------------------------------------------------------------------------
# 2. Data Model & 26 Curated Verified Stories (Sunday 22 November 2026)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Story:
    id: int
    region: str
    domain: str
    headline: str
    lead: str
    location: str
    source: str
    status: str
    coords: Optional[Tuple[float, float]] = None


STORIES: List[Story] = [
    # --- 14 Main Illustrated Cards (#1-#14) ---
    Story(
        1, "WORLD", "CLIMATE",
        "COP31 collapses in Antalya",
        "Nearly 200 nations deadlock past 03:00 UTC over fossil fuels and a $120bn floor.",
        "ANTALYA", "Reuters, AFP, BBC", "Confirmed",
    ),
    Story(
        2, "EUROPE", "MILITARY",
        "Russia fires 186 drones; 161 downed",
        "Overnight wave of 72 jet UAVs batters Dymer flats and triggers grid blackouts.",
        "KYIV", "Ukr. Air Force, BBC", "Confirmed",
    ),
    Story(
        3, "AFRICA", "MILITARY",
        "Warship Merkury sinks in Benghazi",
        "Russian corvette capsizes after suspected sea-drone strike off Libya.",
        "BENGHAZI", "Reuters, Al Jazeera", "Confirmed",
    ),
    Story(
        4, "MIDDLE EAST", "MILITARY",
        "Iran strike hurts 2 in Bahrain",
        "Manama cites Sitra plant fire; IRGC alleges US Patriot radar hit.",
        "SITRA", "MEE, Times of Israel", "Claim",
    ),
    Story(
        5, "ASIA-PACIFIC", "POLITICS",
        "HK polls hit 98.8% with 856 hopefuls",
        "Election Committee fills 723 seats as 5,640 electors vote 01:00–10:00 UTC.",
        "HONG KONG", "info.gov.hk, China Daily", "Confirmed",
    ),
    Story(
        6, "WORLD", "SPACE",
        "BepiColombo reaches Mercury",
        "European-Japanese probe enters orbit after 8 yrs to map crust and field.",
        "MERCURY", "BBC, ESA", "Confirmed",
    ),
    Story(
        7, "AMERICAS", "SECURITY",
        "Mexico seizes cartel chief",
        "Special forces nab FBI Most Wanted boss Meza Flores in raid.",
        "SINALOA", "BBC, Reuters", "Confirmed",
    ),
    Story(
        8, "OCEANIA", "SPORT",
        "India hits record 720/9",
        "Visitors break NZ Test mark; hosts bat 120 overs to draw.",
        "WELLINGTON", "ESPN, Jamaica Obs.", "Confirmed",
    ),
    Story(
        9, "ASIA-PACIFIC", "DISASTER",
        "Banten plant fire kills 3",
        "Rescuers comb gutted Banten factory; 36 missing, 4 hurt.",
        "BANTEN", "AFP, BBC", "Ongoing",
    ),
    Story(
        10, "EUROPE", "POLITICS",
        "Fico blocks €45bn EU loan",
        "Slovak PM rejects European Union aid package for Ukraine.",
        "BRATISLAVA", "Reuters, Kyiv Post", "Confirmed",
    ),
    Story(
        11, "EUROPE", "SPORT",
        "Alcaraz wins ATP Finals",
        "Spaniard beats Zverev in Turin for his first Finals title.",
        "TURIN", "Reuters, Guardian", "Confirmed",
    ),
    Story(
        12, "MIDDLE EAST", "CRISIS",
        "Gaza toll hits 74,742",
        "Health ministry updates toll; Hamas urges mediator talks.",
        "GAZA", "WAFA, Anadolu", "Ongoing",
    ),
    Story(
        13, "AMERICAS", "SPORT",
        "Wembanyama drops 50 pts",
        "Spurs star posts historic 50-pt, 19-reb night in Texas.",
        "SAN ANTONIO", "CBS, KSAT", "Confirmed",
    ),
    Story(
        14, "AFRICA", "CONFLICT",
        "Drones strike Khartoum",
        "RSF UAVs hit residential homes and UN compound; four killed.",
        "KHARTOUM", "Al Jazeera", "Reported",
    ),
    # --- 12 Illustrated Briefs (#15-#26, mapped on left 320x220 world map) ---
    Story(
        15, "EUROPE", "SAFETY",
        "12,000 evacuated at Co-op Live arena",
        "Suspected gas leak forces venue sweep",
        "Manchester", "BBC, SBS", "Reported", (-2.2, 53.5),
    ),
    Story(
        16, "MIDDLE EAST", "POLITICS",
        "Lebanon marks 83rd Independence Day",
        "Displaced locals return for holiday",
        "Beirut", "NPR, L'Orient", "Ongoing", (35.5, 33.9),
    ),
    Story(
        17, "MIDDLE EAST", "MILITARY",
        "Saudi coalition downs Houthi fire",
        "Missiles and drones intercepted",
        "Riyadh", "Anadolu, ISW", "Reported", (46.7, 24.7),
    ),
    Story(
        18, "ASIA-PACIFIC", "TECH",
        "S. Korea education chief quits",
        "Resigns amid AI exam chaos",
        "Seoul", "AFP, BBC", "Confirmed", (127.0, 37.6),
    ),
    Story(
        19, "ASIA-PACIFIC", "CULTURE",
        "Japan marks Shuri Castle rebuild",
        "Main hall restored 7 yrs post-fire",
        "Okinawa", "Wash. Post, JT", "Confirmed", (127.7, 26.2),
    ),
    Story(
        20, "AMERICAS", "DISASTER",
        "Supercell storm kills 5 in Brazil",
        "Over 250 injured by severe storm",
        "Tupanciretã", "AFP", "Confirmed", (-53.8, -29.1),
    ),
    Story(
        21, "AMERICAS", "SPORT",
        "Verstappen wins Las Vegas F1 GP",
        "Finishes ahead of both McLarens",
        "Las Vegas", "Guardian", "Confirmed", (-115.1, 36.2),
    ),
    Story(
        22, "AFRICA", "DISASTER",
        "Boat capsize kills 24 mourners",
        "River tragedy hits southern state",
        "Bayelsa", "AllAfrica", "Confirmed", (6.1, 4.8),
    ),
    Story(
        23, "AFRICA", "DIPLOMACY",
        "Kenya's Ruto & DRC restore ties",
        "Diplomatic ties resumed",
        "Oyo, Congo", "Pan African Visions", "Confirmed", (15.9, -1.2),
    ),
    Story(
        24, "OCEANIA", "POLITICS",
        "Albanese backs Bowen post-COP31",
        "PM defends minister after uproar",
        "Canberra", "Guardian AU", "Confirmed", (149.1, -35.3),
    ),
    Story(
        25, "OCEANIA", "CLIMATE",
        "Pope urges aid for PNG drought",
        "Severe drought grips all 22 zones",
        "Port Moresby", "Crux, CathNews", "Ongoing", (147.2, -9.4),
    ),
    Story(
        26, "WORLD", "TRADE",
        "WTO flags $1.5tn & $5.4tn curbs",
        "Record global export & import curbs",
        "Geneva", "WTO, SunStar", "Confirmed", (6.1, 46.2),
    ),
]

UTC_TIMELINE: List[Tuple[str, str]] = [
    ("01:00", "HK polls open"),
    ("01:25", "Cartel seized"),
    ("03:00", "COP31 fails"),
    ("04:00", "Vegas F1 GP"),
    ("10:44", "Mercury orbit"),
    ("20:43", "Alcaraz ATP"),
]

EXCLUDED_ITEMS: List[str] = [
    "Peru M6.7 quake (20 Nov)",
    "Russia 400-drone barrage (19–20 Nov)",
    "APEC Shenzhen summit (19 Nov)",
    "French Senate vote (20 Nov)",
]


def extract_verified_kpis(stories: Sequence[Story]) -> List[Tuple[str, str, int, str]]:
    """Extract all 6 KPI figures directly from STORIES via regex and assert integrity."""
    by_id = {s.id: s for s in stories}

    def pull(sid: int, pattern: str) -> str:
        s = by_id[sid]
        blob = f"{s.headline} {s.lead}"
        m = re.search(pattern, blob)
        if not m:
            raise AssertionError(f"KPI regex {pattern!r} failed on story #{sid}: {blob!r}")
        return m.group(1)

    specs = [
        (2, r"\bfires\s+(\d+)\s+drones\b", "DRONES FIRED AT UKRAINE"),
        (2, r";\s*(\d+)\s+downed\b", "DRONES DOWNED"),
        (1, r"(\$120bn)\b", "COP31 FINANCE FLOOR"),
        (12, r"hits\s+([\d,]+)\b", "GAZA DEATH TOLL"),
        (5, r"with\s+(\d+)\s+hopefuls", "HK POLL CANDIDATES"),
        (8, r"record\s+(\d+/\d+)\b", "INDIA TEST RECORD"),
    ]
    kpis: List[Tuple[str, str, int, str]] = []
    for sid, pat, label in specs:
        val = pull(sid, pat)
        kpis.append((val, label, sid, by_id[sid].region))

    expected = ["186", "161", "$120bn", "74,742", "856", "720/9"]
    got = [k[0] for k in kpis]
    assert got == expected, f"KPI mismatch: got {got}, expected {expected}"
    return kpis


def validate_dataset(stories: Sequence[Story]) -> Counter:
    assert len(stories) == 26, f"Expected 26 stories, got {len(stories)}"
    assert [s.id for s in stories] == list(range(1, 27)), "Story IDs must be 1..26"
    counts = Counter(s.region for s in stories)
    assert set(counts.keys()) == set(REGION_ORDER), f"Unexpected regions: {set(counts.keys())}"
    for r in REGION_ORDER:
        assert 3 <= counts[r] <= 4, f"Region {r} must have 3-4 stories, got {counts[r]}"
    mapped = [s for s in stories if s.coords is not None]
    assert [s.id for s in mapped] == list(range(15, 27)), "Briefs #15..#26 must have map coordinates"
    return counts


# ---------------------------------------------------------------------------
# 3. Typography Fitting (fit / fit_multiline) & Collision Detection
# ---------------------------------------------------------------------------

def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def fit(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_key: str,
    max_size: int,
    min_size: int,
    max_width: float,
    max_height: Optional[float] = None,
) -> Tuple[ImageFont.FreeTypeFont, int, int, int]:
    """Find largest font size in [min_size, max_size] fitting strictly within bounds."""
    for size in range(max_size, min_size - 1, -1):
        font = get_font(font_key, size)
        w, h = measure_text(draw, text, font)
        if w <= max_width and (max_height is None or h <= max_height):
            return font, size, w, h
    raise RuntimeError(
        f"fit() overflow: {text!r} cannot fit w={max_width}, h={max_height} at min={min_size} ({font_key})"
    )


def _wrap_words(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: float,
) -> List[str]:
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    cur = words[0]
    for word in words[1:]:
        cand = f"{cur} {word}"
        if measure_text(draw, cand, font)[0] <= max_width:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def fit_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_key: str,
    max_size: int,
    min_size: int,
    max_width: float,
    max_lines: int,
    line_spacing: float = 1.15,
    max_height: Optional[float] = None,
) -> Tuple[ImageFont.FreeTypeFont, int, List[str], int]:
    """Wrap text into <= max_lines within max_width and max_height at largest valid size."""
    for size in range(max_size, min_size - 1, -1):
        font = get_font(font_key, size)
        lines = _wrap_words(draw, text, font, max_width)
        if len(lines) > max_lines:
            continue
        if any(measure_text(draw, ln, font)[0] > max_width for ln in lines):
            continue
        line_h = max(int(round(size * line_spacing)), measure_text(draw, "Ag", font)[1])
        if max_height is not None and line_h * len(lines) > max_height:
            continue
        return font, size, lines, line_h
    raise RuntimeError(
        f"fit_multiline() overflow: {text!r} cannot fit {max_lines}L x w={max_width}, h={max_height} at min={min_size}"
    )


def draw_text_centered(
    draw: ImageDraw.ImageDraw,
    box: Tuple[float, float, float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    tb = draw.textbbox((0, 0), text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tx = x0 + (x1 - x0 - tw) / 2.0 - tb[0]
    ty = y0 + (y1 - y0 - th) / 2.0 - tb[1]
    draw.text((tx, ty), text, font=font, fill=fill)
    return (tx + tb[0], ty + tb[1], tx + tb[2], ty + tb[3])


def draw_text_aligned(
    draw: ImageDraw.ImageDraw,
    box: Tuple[float, float, float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    align: str = "left",
) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    tb = draw.textbbox((0, 0), text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tx = (x1 - tw - tb[0]) if align == "right" else (x0 - tb[0])
    ty = y0 + (y1 - y0 - th) / 2.0 - tb[1]
    draw.text((tx, ty), text, font=font, fill=fill)
    return (tx + tb[0], ty + tb[1], tx + tb[2], ty + tb[3])


def draw_text_baseline_centered(
    draw: ImageDraw.ImageDraw,
    x0: float,
    x1: float,
    baseline_y: float,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> Tuple[float, float, float, float]:
    ascent, _ = font.getmetrics()
    tb = draw.textbbox((0, 0), text, font=font)
    tw = tb[2] - tb[0]
    tx = x0 + (x1 - x0 - tw) / 2.0 - tb[0]
    ty = baseline_y - ascent
    draw.text((tx, ty), text, font=font, fill=fill)
    return (tx + tb[0], ty + tb[1], tx + tb[2], ty + tb[3])


class CollisionTracker:
    """Tracks bounding boxes per logical group and asserts zero overlap and strict containment."""

    def __init__(self, canvas_w: int = CANVAS_W, canvas_h: int = CANVAS_H) -> None:
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.groups: Dict[str, List[Tuple[str, Tuple[float, float, float, float]]]] = {}
        self.total_registered = 0

    def add(self, group: str, label: str, box: Tuple[float, float, float, float]) -> None:
        x0, y0, x1, y1 = box
        if x1 < x0 or y1 < y0:
            raise ValueError(f"Inverted box {group}/{label}: {box}")
        if x0 < -0.5 or y0 < -0.5 or x1 > self.canvas_w + 0.5 or y1 > self.canvas_h + 0.5:
            raise AssertionError(f"Out-of-canvas box {group}/{label}: {box}")
        self.groups.setdefault(group, []).append((label, box))
        self.total_registered += 1

    def assert_no_collisions(self, tolerance: float = 0.25) -> int:
        checked_pairs = 0
        collisions: List[str] = []
        for group, items in self.groups.items():
            n = len(items)
            for i in range(n):
                l1, (ax0, ay0, ax1, ay1) = items[i]
                for j in range(i + 1, n):
                    l2, (bx0, by0, bx1, by1) = items[j]
                    checked_pairs += 1
                    ix = min(ax1, bx1) - max(ax0, bx0)
                    iy = min(ay1, by1) - max(ay0, by0)
                    if ix > tolerance and iy > tolerance:
                        collisions.append(
                            f"[{group}] {l1} {tuple(round(v, 1) for v in items[i][1])} "
                            f"overlaps {l2} {tuple(round(v, 1) for v in items[j][1])} "
                            f"by ({ix:.1f}x{iy:.1f})"
                        )
        if collisions:
            raise AssertionError(
                f"Detected {len(collisions)} layout collision(s):\n" + "\n".join(collisions[:15])
            )
        return checked_pairs


# ---------------------------------------------------------------------------
# 4. World Map Polygons & Iterative Pin Collision Resolver (#15-#26)
# ---------------------------------------------------------------------------

WORLD_POLYGONS: List[Tuple[str, List[Tuple[float, float]]]] = [
    ("AMERICAS", [
        (-166, 65), (-150, 71), (-132, 69), (-112, 68), (-95, 62), (-82, 63),
        (-65, 60), (-54, 52), (-62, 44), (-71, 41), (-76, 35), (-81, 25),
        (-84, 29), (-90, 29), (-97, 26), (-97, 19), (-88, 21), (-83, 15),
        (-78, 9), (-84, 9), (-93, 15), (-105, 20), (-112, 29), (-118, 33),
        (-125, 42), (-125, 49), (-135, 57), (-152, 60), (-163, 55),
    ]),
    ("AMERICAS", [
        (-52, 60), (-42, 60), (-22, 70), (-18, 79), (-44, 81), (-62, 76), (-55, 67),
    ]),
    ("AMERICAS", [
        (-79, 10), (-71, 12), (-61, 10), (-50, 1), (-35, -6), (-38, -14),
        (-41, -23), (-48, -26), (-50, -30), (-53, -34), (-58, -38),
        (-63, -42), (-68, -53), (-74, -52), (-73, -40), (-71, -30),
        (-71, -18), (-81, -5),
    ]),
    ("EUROPE", [
        (-9, 37), (-9, 43), (-2, 43), (-4, 48), (2, 51), (8, 54), (10, 57),
        (14, 54), (21, 55), (28, 60), (38, 66), (48, 66), (52, 54), (42, 47),
        (34, 46), (28, 41), (24, 37), (19, 40), (15, 38), (12, 44), (6, 43),
        (3, 42), (-5, 36),
    ]),
    ("EUROPE", [(-6, 50), (2, 51), (1, 55), (-3, 59), (-7, 58), (-9, 53)]),
    ("EUROPE", [(5, 59), (10, 58), (18, 60), (22, 65), (29, 70), (18, 70), (11, 64)]),
    ("AFRICA", [
        (-17, 15), (-13, 27), (-6, 36), (10, 37), (12, 33), (25, 32), (33, 31),
        (43, 12), (51, 11), (42, 0), (40, -11), (35, -24), (28, -33), (18, -35),
        (15, -26), (12, -14), (9, -1), (9, 5), (-4, 5), (-16, 11),
    ]),
    ("AFRICA", [(44, -25), (47, -25), (50, -15), (48, -12), (44, -18)]),
    ("MIDDLE EAST", [
        (26, 41), (36, 42), (45, 40), (54, 38), (61, 35), (61, 25), (56, 26),
        (59, 22), (52, 16), (44, 13), (39, 21), (35, 29), (34, 33), (36, 37), (27, 37),
    ]),
    ("ASIA-PACIFIC", [
        (52, 54), (58, 68), (85, 73), (115, 73), (145, 71), (172, 66),
        (162, 58), (142, 54), (136, 44), (129, 40), (126, 35), (122, 38),
        (118, 39), (122, 31), (116, 23), (109, 21), (109, 12), (104, 1),
        (100, 7), (98, 16), (90, 22), (80, 8), (73, 19), (68, 24), (61, 25),
        (61, 35), (54, 38), (52, 47),
    ]),
    ("ASIA-PACIFIC", [(130, 31), (135, 34), (141, 36), (145, 44), (140, 44), (136, 37), (130, 33)]),
    ("ASIA-PACIFIC", [(95, 5), (105, -6), (115, -8), (114, -9), (103, -7), (95, 2)]),
    ("ASIA-PACIFIC", [(109, 1), (118, 5), (119, -3), (111, -3)]),
    ("ASIA-PACIFIC", [(120, 18), (124, 15), (126, 7), (122, 8), (120, 14)]),
    ("OCEANIA", [
        (114, -22), (123, -16), (131, -12), (137, -15), (142, -11), (146, -18),
        (153, -27), (150, -37), (141, -38), (135, -34), (128, -32), (115, -34), (113, -27),
    ]),
    ("OCEANIA", [(131, -2), (141, -3), (150, -10), (146, -10), (137, -5)]),
    ("OCEANIA", [(173, -35), (178, -38), (174, -42), (167, -46), (166, -45), (172, -41)]),
]


def project_lonlat(
    lon: float,
    lat: float,
    map_box: Tuple[float, float, float, float],
) -> Tuple[float, float]:
    x0, y0, x1, y1 = map_box
    lon_min, lon_max = -176.0, 186.0
    lat_min, lat_max = -58.0, 82.0
    px = x0 + (lon - lon_min) / (lon_max - lon_min) * (x1 - x0)
    py = y0 + (lat_max - lat) / (lat_max - lat_min) * (y1 - y0)
    return px, py


def resolve_map_pin_collisions(
    pin_stories: Sequence[Story],
    map_box: Tuple[float, float, float, float],
    pin_radius: float = 8.0,
    min_gap: float = 2.0,
) -> List[Tuple[Story, Tuple[float, float], Tuple[float, float]]]:
    """Deterministic spring + pairwise repulsion solver ensuring zero pin overlap."""
    x0, y0, x1, y1 = map_box
    pad = pin_radius + 3.0
    min_dist = 2.0 * pin_radius + min_gap

    anchors: List[Tuple[float, float]] = []
    pos: List[List[float]] = []
    for s in pin_stories:
        assert s.coords is not None
        ax, ay = project_lonlat(s.coords[0], s.coords[1], map_box)
        anchors.append((ax, ay))
        pos.append([
            max(x0 + pad, min(x1 - pad, ax)),
            max(y0 + pad, min(y1 - pad, ay)),
        ])

    n = len(pin_stories)
    for _ in range(320):
        moved = False
        for i in range(n):
            ax, ay = anchors[i]
            pos[i][0] += (ax - pos[i][0]) * 0.03
            pos[i][1] += (ay - pos[i][1]) * 0.03

        for i in range(n):
            for j in range(i + 1, n):
                dx = pos[j][0] - pos[i][0]
                dy = pos[j][1] - pos[i][1]
                ov_x = min_dist - abs(dx)
                ov_y = min_dist - abs(dy)
                dist = math.hypot(dx, dy)
                if ov_x > 0 and ov_y > 0:
                    if dist < 1e-4:
                        angle = ((pin_stories[i].id * 41 + pin_stories[j].id * 23) % 360) * math.pi / 180.0
                        ux, uy = math.cos(angle), math.sin(angle)
                        push = min_dist * 0.6
                    else:
                        ux, uy = dx / dist, dy / dist
                        push = max(min(ov_x, ov_y), max(0.0, min_dist - dist)) * 0.65 + 0.35
                    pos[i][0] -= ux * push
                    pos[i][1] -= uy * push
                    pos[j][0] += ux * push
                    pos[j][1] += uy * push
                    moved = True

        for i in range(n):
            pos[i][0] = max(x0 + pad, min(x1 - pad, pos[i][0]))
            pos[i][1] = max(y0 + pad, min(y1 - pad, pos[i][1]))
        if not moved:
            break

    for i in range(n):
        for j in range(i + 1, n):
            d = math.hypot(pos[j][0] - pos[i][0], pos[j][1] - pos[i][1])
            assert d >= 2.0 * pin_radius + 0.5, f"Map pins #{pin_stories[i].id} & #{pin_stories[j].id} overlap"

    return [(pin_stories[i], anchors[i], (pos[i][0], pos[i][1])) for i in range(n)]


# ---------------------------------------------------------------------------
# 5. 14 Main-Card Editorial Illustrations (height = 110px, clean line+tint)
# ---------------------------------------------------------------------------

def draw_main_card_illustration(
    draw: ImageDraw.ImageDraw,
    story: Story,
    box: Tuple[int, int, int, int],
    accent: str,
) -> None:
    """
    Draw a cohesive editorial flat-color + crisp 2px line-art poster illustration
    inside `box` (height strictly >= 110px, zero human faces, strong 300px impact).
    """
    x0, y0, x1, y1 = box
    w = x1 - x0
    h = y1 - y0
    assert h >= 110, f"Card #{story.id} illustration height {h} < 110px"

    cx = (x0 + x1) // 2
    ay0 = y0 + 20
    ay1 = y1 - 8
    acy = (ay0 + ay1) // 2
    r_max = min((w - 18) // 2, (ay1 - ay0) // 2)
    ink = INK_DARK
    lw = 2
    sid = story.id

    if sid == 1:
        # COP31 collapse: deep teal-slate summit hall + crisp mint-ivory globe + crimson fault + gold gavel
        draw.rectangle(box, fill="#1D3640")
        r = min(25, r_max)
        gy = acy + 8
        draw.ellipse((cx - r, gy - r, cx + r, gy + r), fill="#9CC4B8", outline=WHITE, width=lw)
        draw.ellipse((cx - r // 2, gy - r, cx + r // 2, gy + r), outline="#2E5B5E", width=lw)
        draw.line((cx - r, gy, cx + r, gy), fill="#2E5B5E", width=lw)
        draw.line(
            [(cx - 5, gy - r - 2), (cx + 4, gy - 5), (cx - 4, gy + 5), (cx + 6, gy + r + 2)],
            fill="#E84A3C", width=3,
        )
        draw.line((cx - 22, ay0 + 9, cx + 10, ay0 + 2), fill=GOLD, width=2)
        draw.rectangle((cx + 6, ay0 - 3, cx + 24, ay0 + 8), fill=GOLD, outline=WHITE, width=1)

    elif sid == 2:
        # 186 drones / 161 downed: midnight radar sky + rings + sweep + gold delta UAVs + crimson X
        draw.rectangle(box, fill="#142342")
        ry = acy + 4
        rr_outer = min(31, r_max + 2)
        for rr in (rr_outer, int(rr_outer * 0.65), int(rr_outer * 0.3)):
            draw.ellipse((cx - rr, ry - rr, cx + rr, ry + rr), outline="#3D5A8C", width=1)
        draw.line((cx, ry, cx + int(rr_outer * 0.8), ry - int(rr_outer * 0.65)), fill=GOLD, width=lw)
        for dx, dy in [(-20, -15), (14, -7), (-7, 15)]:
            pts = [
                (cx + dx, ry + dy - 6),
                (cx + dx + 8, ry + dy + 5),
                (cx + dx, ry + dy + 2),
                (cx + dx - 8, ry + dy + 5),
            ]
            draw.polygon(pts, fill=GOLD, outline=WHITE)
        bx, by = cx + 14, ry - 7
        draw.line((bx - 7, by - 7, bx + 7, by + 7), fill="#F05146", width=2)
        draw.line((bx - 7, by + 7, bx + 7, by - 7), fill="#F05146", width=2)

    elif sid == 3:
        # Warship Merkury sinking: twilight sky + deep sea + capsized hull silhouette + layered fire plume
        wy = acy + 11
        draw.rectangle((x0, y0, x1, wy), fill="#1F3042")
        draw.rectangle((x0, wy, x1, y1), fill="#295B66")
        hull = [
            (cx - 36, wy - 16), (cx + 30, wy + 2),
            (cx + 22, wy + 12), (cx - 28, wy - 3),
        ]
        draw.polygon(hull, fill="#8C9EAE", outline=WHITE)
        draw.line((cx - 10, wy - 11, cx - 1, wy - 35), fill=WHITE, width=lw)
        draw.line((cx - 8, wy - 30, cx + 10, wy - 25), fill=GOLD, width=lw)
        # Layered impact fire (outer crimson + inner amber)
        flame_out = [(cx + 8, wy - 4), (cx + 16, wy - 30), (cx + 23, wy - 14), (cx + 30, wy - 25), (cx + 29, wy + 1)]
        draw.polygon(flame_out, fill="#E04B3A")
        flame_in = [(cx + 13, wy - 4), (cx + 18, wy - 20), (cx + 24, wy - 4)]
        draw.polygon(flame_in, fill=GOLD)
        for off in (6, 15):
            pts = [(x0 + 6 + k, wy + off + (3 if (k // 9) % 2 == 0 else -2)) for k in range(0, w - 12, 9)]
            draw.line(pts, fill="#9ED3DC", width=lw)

    elif sid == 4:
        # Bahrain refinery strike: dusk desert sky + solid industrial tanks + layered blaze + Patriot radar
        draw.rectangle(box, fill="#291E2B")
        base_y = ay1 - 3
        draw.rectangle((x0, base_y, x1, y1), fill="#3E323C")
        # Smoke plume behind fire
        draw.ellipse((x0 + 18, ay0 + 2, x0 + 56, ay0 + 30), fill="#4E434D")
        draw.ellipse((x0 + 34, ay0 - 2, x0 + 68, ay0 + 22), fill="#433842")
        # Industrial tanks
        draw.rectangle((x0 + 12, base_y - 24, x0 + 42, base_y), fill="#C9B9AC", outline=WHITE, width=1)
        draw.arc((x0 + 12, base_y - 31, x0 + 42, base_y - 17), 180, 360, fill=WHITE, width=lw)
        draw.rectangle((x0 + 46, base_y - 16, x0 + 68, base_y), fill="#A9998D", outline=WHITE, width=1)
        # Layered blaze rising from tank
        blaze1 = [(x0 + 18, base_y - 24), (x0 + 24, base_y - 46), (x0 + 31, base_y - 35), (x0 + 38, base_y - 50), (x0 + 42, base_y - 24)]
        draw.polygon(blaze1, fill="#E64B38")
        blaze2 = [(x0 + 23, base_y - 24), (x0 + 30, base_y - 40), (x0 + 37, base_y - 24)]
        draw.polygon(blaze2, fill=GOLD)
        # Crisp Patriot radar dish & scan beam on right
        draw.arc((x1 - 34, ay0 + 18, x1 - 8, ay0 + 46), 115, 255, fill=WHITE, width=lw)
        draw.line((x1 - 21, ay0 + 32, x1 - 11, ay0 + 22), fill=GOLD, width=lw)
        draw.line((x1 - 21, ay0 + 45, x1 - 21, base_y), fill=WHITE, width=lw)
        draw.line((x1 - 11, ay0 + 22, x1 - 4, ay0 + 12), fill=GOLD, width=1)

    elif sid == 5:
        # HK polls 98.8%: rich editorial slate + ivory ballot box + crisp white ballot + bold crimson checkmark
        draw.rectangle(box, fill="#2A303E")
        bx0, by0, bx1, by1 = cx - 28, acy + 3, cx + 28, ay1 - 3
        draw.rectangle((bx0, by0, bx1, by1), fill="#E9DEC9", outline=WHITE, width=1)
        draw.line((bx0 - 4, by0, bx1 + 4, by0), fill=WHITE, width=lw)
        draw.line((cx - 16, by0 + 5, cx + 16, by0 + 5), fill="#2A303E", width=3)
        draw.rectangle((cx - 14, ay0 + 2, cx + 14, by0 + 3), fill=WHITE, outline="#121923", width=1)
        draw.line([(cx - 7, ay0 + 16), (cx - 1, ay0 + 23), (cx + 9, ay0 + 9)], fill="#C92630", width=3)
        draw.rectangle((bx0 + 8, by1 - 16, bx1 - 8, by1 - 10), fill="#C92630")
        draw.rectangle((bx0 + 8, by1 - 8, bx1 - 18, by1 - 4), fill="#3F4B61")

    elif sid == 6:
        # BepiColombo orbiter at Mercury: deep cosmos + cratered sphere + gold orbit + solar probe
        draw.rectangle(box, fill="#172238")
        py = acy + 9
        pr = min(22, r_max)
        draw.ellipse((cx - pr, py - pr, cx + pr, py + pr), fill="#D4C2A3", outline=WHITE, width=lw)
        draw.ellipse((cx - 10, py - 7, cx - 2, py + 1), outline="#857458", width=lw)
        draw.ellipse((cx + 4, py + 2, cx + 11, py + 9), outline="#857458", width=lw)
        draw.arc((x0 + 8, ay0 + 5, x1 - 8, ay1 - 2), 195, 350, fill=GOLD, width=lw)
        sx, sy = cx, ay0 + 10
        draw.rectangle((sx - 6, sy - 4, sx + 6, sy + 4), fill=WHITE, outline=ink, width=1)
        draw.rectangle((sx - 25, sy - 3, sx - 8, sy + 3), fill="#5B9BD5", outline=WHITE, width=1)
        draw.rectangle((sx + 8, sy - 3, sx + 25, sy + 3), fill="#5B9BD5", outline=WHITE, width=1)

    elif sid == 7:
        # Mexico cartel night raid: deep slate-blue sky + Sierra silhouette + helicopter + bright gold beam
        draw.rectangle(box, fill="#1E2D45")
        base_y = ay1 - 3
        # Glowing searchlight beam behind mountains
        beam = [(cx, ay0 + 23), (x0 + 10, base_y - 6), (x1 - 10, base_y - 6)]
        draw.polygon(beam, fill="#4A5248")
        peaks = [
            (x0 + 2, base_y), (x0 + 17, base_y - 26), (cx, base_y - 12),
            (x1 - 16, base_y - 31), (x1 - 2, base_y),
        ]
        draw.polygon(peaks, fill="#101A2B", outline="#5B7599")
        draw.rectangle((x0, base_y, x1, y1), fill="#101A2B")
        hx, hy = cx, ay0 + 14
        draw.line((hx - 20, hy - 6, hx + 20, hy - 6), fill=WHITE, width=lw)
        draw.line((hx, hy - 6, hx, hy - 1), fill=WHITE, width=lw)
        draw.ellipse((hx - 10, hy - 1, hx + 8, hy + 10), fill=GOLD, outline=WHITE, width=1)
        draw.line((hx + 8, hy + 4, hx + 20, hy + 2), fill=WHITE, width=lw)
        draw.line((hx + 20, hy - 2, hx + 20, hy + 6), fill=WHITE, width=lw)
        draw.line((hx - 2, hy + 10, x0 + 12, base_y - 8), fill=GOLD, width=1)
        draw.line((hx + 2, hy + 10, x1 - 12, base_y - 8), fill=GOLD, width=1)

    elif sid == 8:
        # India 720/9 cricket: rich pitch emerald + ivory stumps + wood bat + crimson ball cleanly cleared below badge
        draw.rectangle(box, fill="#244B3C")
        base_y = ay1 - 4
        draw.rectangle((x0, base_y, x1, y1), fill="#3E6E52")
        draw.line((x0 + 6, base_y, x1 - 6, base_y), fill=WHITE, width=lw)
        for sx in (cx - 10, cx, cx + 10):
            draw.line((sx, base_y, sx, ay0 + 26), fill="#F5ECD7", width=lw)
        draw.line((cx - 11, ay0 + 24, cx - 1, ay0 + 24), fill=GOLD, width=lw)
        draw.line((cx + 1, ay0 + 24, cx + 11, ay0 + 24), fill=GOLD, width=lw)
        bat = [(x0 + 12, ay1 - 15), (x1 - 14, ay0 + 14), (x1 - 9, ay0 + 19), (x0 + 17, ay1 - 10)]
        draw.polygon(bat, fill="#E0C38E", outline=WHITE)
        # Crimson ball + clean arc shifted well below #8 badge
        draw.ellipse((x0 + 14, ay0 + 10, x0 + 24, ay0 + 20), fill="#E0433E", outline=WHITE, width=1)
        draw.arc((x0 + 18, ay0 + 8, cx + 14, ay0 + 32), 215, 320, fill=WHITE, width=lw)

    elif sid == 9:
        # Indonesia Banten factory fire: dark night + sawtooth plant with lit windows + multi-tone blaze & smoke
        draw.rectangle(box, fill="#2D2224")
        base_y = ay1 - 4
        draw.rectangle((x0, base_y, x1, y1), fill="#1A1416")
        draw.ellipse((cx - 16, ay0 + 2, cx + 14, ay0 + 26), fill="#4B3E40")
        flame_out = [
            (cx - 13, base_y - 31), (cx - 16, ay0 + 18), (cx - 5, ay0 + 8),
            (cx + 2, ay0 + 20), (cx + 11, ay0 + 11), (cx + 15, base_y - 31),
        ]
        draw.polygon(flame_out, fill="#E04632")
        flame_mid = [(cx - 8, base_y - 31), (cx - 5, ay0 + 16), (cx + 1, ay0 + 24), (cx + 7, ay0 + 17), (cx + 9, base_y - 31)]
        draw.polygon(flame_mid, fill="#F28C28")
        flame_core = [(cx - 4, base_y - 31), (cx, ay0 + 24), (cx + 4, base_y - 31)]
        draw.polygon(flame_core, fill=GOLD)
        factory = [
            (x0 + 6, base_y), (x0 + 6, base_y - 23),
            (x0 + 20, base_y - 33), (x0 + 20, base_y - 23),
            (x0 + 34, base_y - 33), (x0 + 34, base_y - 23),
            (x0 + 48, base_y - 33), (x0 + 48, base_y),
        ]
        draw.polygon(factory, fill="#493E3C", outline=WHITE)
        draw.rectangle((x0 + 12, base_y - 16, x0 + 22, base_y - 8), fill=GOLD)
        draw.rectangle((x0 + 29, base_y - 16, x0 + 39, base_y - 8), fill=GOLD)

    elif sid == 10:
        # Fico blocks €45bn EU loan: deep EU cobalt + 12 gold stars ring + crisp € + bold crimson veto
        draw.rectangle(box, fill="#193A6A")
        sr = min(26, r_max + 2)
        for k in range(12):
            ang = k * (2 * math.pi / 12)
            sx = cx + math.cos(ang) * sr
            sy = acy + 2 + math.sin(ang) * sr
            draw.ellipse((sx - 1.5, sy - 1.5, sx + 1.5, sy + 1.5), fill=GOLD)
        r = 18
        draw.ellipse((cx - r, acy + 2 - r, cx + r, acy + 2 + r), outline=GOLD, width=1)
        f_eu = get_font("serif_bold", 26)
        draw_text_centered(draw, (cx - r, acy + 2 - r, cx + r, acy + 2 + r), "€", f_eu, WHITE)
        draw.ellipse((cx - r - 3, acy + 2 - r - 3, cx + r + 3, acy + 2 + r + 3), outline="#E64A45", width=3)
        draw.line((cx - r + 1, acy + 2 + r - 1, cx + r - 1, acy + 2 - r + 1), fill="#E64A45", width=3)

    elif sid == 11:
        # Alcaraz ATP Finals: indoor blue court + handled gold chalice trophy + chartreuse ball
        draw.rectangle(box, fill="#1A3D61")
        base_y = ay1 - 4
        draw.rectangle((x0, acy + 12, x1, y1), fill="#265A8A")
        draw.line((x0 + 4, acy + 12, x1 - 4, acy + 12), fill=WHITE, width=1)
        draw.line((cx, acy + 12, cx, y1), fill=WHITE, width=1)
        # Handled gold chalice trophy
        draw.arc((cx - 19, ay0 + 12, cx - 7, ay0 + 28), 90, 270, fill=GOLD, width=2)
        draw.arc((cx + 7, ay0 + 12, cx + 19, ay0 + 28), 270, 90, fill=GOLD, width=2)
        cup = [(cx - 13, ay0 + 10), (cx + 13, ay0 + 10), (cx + 8, ay0 + 34), (cx - 8, ay0 + 34)]
        draw.polygon(cup, fill=GOLD, outline=WHITE)
        draw.rectangle((cx - 3, ay0 + 34, cx + 3, ay0 + 45), fill=GOLD)
        draw.rectangle((cx - 12, ay0 + 45, cx + 12, ay0 + 51), fill="#C99E3D", outline=WHITE, width=1)
        draw.ellipse((x1 - 19, ay0 + 6, x1 - 7, ay0 + 18), fill="#D8E64C", outline=WHITE, width=1)

    elif sid == 12:
        # Gaza toll 74,742: somber twilight dusk sky + muted horizon band + stark urban skyline silhouette
        draw.rectangle(box, fill="#2B242B")
        draw.rectangle((x0, acy - 10, x1, ay1), fill="#6E4442")
        draw.rectangle((x0, acy + 4, x1, ay1), fill="#8F5C52")
        base_y = ay1 - 2
        draw.rectangle((x0, base_y, x1, y1), fill="#1A161A")
        # Stark dignified skyline/rubble silhouette
        blds = [
            (x0 + 4, base_y - 26, x0 + 16, base_y),
            (x0 + 18, base_y - 38, x0 + 32, base_y),
            (x0 + 34, base_y - 22, x0 + 46, base_y),
            (x0 + 48, base_y - 31, x1 - 5, base_y),
        ]
        for bx0, by0, bx1, by1 in blds:
            draw.rectangle((bx0, by0, bx1, by1), fill="#1A161A")
        # Quiet pale moon/memorial crescent in upper right dusk sky
        draw.ellipse((cx + 6, ay0 + 6, cx + 20, ay0 + 20), fill="#E9DEC9")
        draw.ellipse((cx + 10, ay0 + 4, cx + 23, ay0 + 18), fill="#2B242B")

    elif sid == 13:
        # Wembanyama 50 pts: dark Spurs arena + crisp glass backboard + orange rim + net + swish ball
        draw.rectangle(box, fill="#202733")
        draw.rectangle((cx - 22, ay0 + 6, cx + 22, ay0 + 34), fill="#EAEFF5", outline=WHITE, width=lw)
        draw.rectangle((cx - 9, ay0 + 17, cx + 9, ay0 + 31), outline="#E04B3A", width=lw)
        draw.line((cx - 12, ay0 + 34, cx + 12, ay0 + 34), fill="#E65A2B", width=3)
        net = [(cx - 10, ay0 + 35), (cx - 6, ay0 + 50), (cx + 6, ay0 + 50), (cx + 10, ay0 + 35)]
        draw.line(net, fill=WHITE, width=lw)
        draw.line((cx - 7, ay0 + 42, cx + 7, ay0 + 42), fill="#C9D3DF", width=1)
        draw.ellipse((cx - 9, ay0 + 54, cx + 9, ay0 + 72), fill="#E07634", outline=WHITE, width=1)
        draw.line((cx - 9, ay0 + 63, cx + 9, ay0 + 63), fill="#202733", width=1)
        draw.line((cx, ay0 + 54, cx, ay0 + 72), fill="#202733", width=1)

    elif sid == 14:
        # Khartoum drones: dusk desert-navy + solid skyline silhouette + impact burst + crisp UAV
        draw.rectangle(box, fill="#202A3A")
        base_y = ay1 - 3
        draw.rectangle((x0, base_y, x1, y1), fill="#121824")
        # Impact glow behind buildings
        draw.ellipse((cx - 12, base_y - 32, cx + 18, base_y - 4), fill="#D9523B")
        draw.ellipse((cx - 6, base_y - 26, cx + 12, base_y - 10), fill=GOLD)
        draw.rectangle((x0 + 6, base_y - 22, x0 + 26, base_y), fill="#121824", outline="#526B87", width=1)
        draw.rectangle((x0 + 30, base_y - 28, x1 - 6, base_y), fill="#121824", outline="#526B87", width=1)
        # Crisp white UAV overhead
        dy = ay0 + 20
        pts = [(cx, dy - 7), (cx + 15, dy + 6), (cx, dy + 2), (cx - 15, dy + 6)]
        draw.polygon(pts, fill=WHITE, outline=GOLD)

    # Subtle top-left story index square drawn LAST so it always stays razor-crisp
    badge = (x0, y0, x0 + 20, y0 + 18)
    draw.rectangle(badge, fill=accent)
    f_idx = get_font("sans_bold", 10)
    draw_text_centered(draw, badge, str(story.id), f_idx, WHITE)


# ---------------------------------------------------------------------------
# 6. 12 Brief Line-Art Icons (24x24px, distinct per story #15-#26)
# ---------------------------------------------------------------------------

def draw_brief_icon(
    draw: ImageDraw.ImageDraw,
    story: Story,
    box: Tuple[int, int, int, int],
    accent: str,
) -> None:
    """Draw a crisp 24x24px geometric editorial line-art icon for brief #15-#26."""
    x0, y0, x1, y1 = box
    assert (x1 - x0) == 24 and (y1 - y0) == 24, f"Brief #{story.id} icon must be 24x24, got {box}"
    cx, cy = x0 + 12, y0 + 12
    ink = INK_DARK
    bg = ART_BACKDROPS[story.region]

    # Subtle tinted rounded tile (no heavy black border -> keeps edge density low)
    draw.rounded_rectangle(box, radius=4, fill=bg)

    sid = story.id
    if sid == 15:  # Co-op Live evacuation: dome + exit arrow
        draw.arc((x0 + 3, y0 + 5, x1 - 3, y1 - 3), 180, 360, fill=ink, width=2)
        draw.line((x0 + 3, y1 - 6, x1 - 3, y1 - 6), fill=ink, width=2)
        draw.line((cx, y0 + 10, cx + 6, y0 + 10), fill=CRIMSON, width=2)
        draw.line([(cx + 3, y0 + 7), (cx + 6, y0 + 10), (cx + 3, y0 + 13)], fill=CRIMSON, width=2)
    elif sid == 16:  # Lebanon Independence: stylized cedar tree
        draw.polygon([(cx, y0 + 4), (x0 + 5, y1 - 7), (x1 - 5, y1 - 7)], fill=accent, outline=ink)
        draw.line((cx, y1 - 7, cx, y1 - 3), fill=ink, width=2)
    elif sid == 17:  # Saudi missile intercept: shield + deflected arc
        shield = [(cx, y0 + 4), (x1 - 5, y0 + 7), (x1 - 6, y1 - 7), (cx, y1 - 3), (x0 + 6, y1 - 7), (x0 + 5, y0 + 7)]
        draw.line(shield + [shield[0]], fill=accent, width=2)
        draw.line((x0 + 5, y0 + 5, cx + 2, cy + 1), fill=CRIMSON, width=2)
    elif sid == 18:  # S. Korea AI exam: paper sheet + spark
        draw.rectangle((x0 + 5, y0 + 4, x1 - 5, y1 - 4), outline=ink, width=2)
        draw.line((x0 + 8, y0 + 9, x1 - 8, y0 + 9), fill=accent, width=2)
        draw.line((x0 + 8, y0 + 14, x1 - 9, y0 + 14), fill=ink, width=2)
    elif sid == 19:  # Shuri Castle rebuild: tiered curved roofline
        draw.line([(x0 + 4, y0 + 10), (cx, y0 + 5), (x1 - 4, y0 + 10)], fill=CRIMSON, width=2)
        draw.line((x0 + 6, y0 + 14, x1 - 6, y0 + 14), fill=accent, width=2)
        draw.rectangle((x0 + 7, y0 + 14, x1 - 7, y1 - 4), outline=ink, width=2)
    elif sid == 20:  # Brazil supercell storm: funnel + lightning bolt
        draw.line([(x0 + 4, y0 + 6), (x1 - 4, y0 + 6), (cx + 2, y1 - 6), (cx - 2, y1 - 6)], fill=ink, width=2)
        draw.line([(cx + 1, y0 + 9), (cx - 3, cy + 3), (cx + 2, cy + 3), (cx - 2, y1 - 3)], fill=CRIMSON, width=2)
    elif sid == 21:  # Las Vegas F1 GP: checkered racing flag
        draw.line((x0 + 6, y0 + 4, x0 + 6, y1 - 4), fill=ink, width=2)
        draw.rectangle((x0 + 6, y0 + 5, x1 - 4, y0 + 14), outline=ink, width=2)
        draw.rectangle((x0 + 7, y0 + 6, x0 + 12, y0 + 10), fill=ink)
        draw.rectangle((x0 + 13, y0 + 10, x1 - 5, y0 + 13), fill=accent)
    elif sid == 22:  # Nigeria boat capsize: tilted boat + wave
        draw.line([(x0 + 5, y0 + 12), (x1 - 5, y0 + 7), (x1 - 7, y0 + 13), (x0 + 6, y0 + 15)], fill=ink, width=2)
        draw.line([(x0 + 3, y1 - 5), (cx - 3, y1 - 7), (cx + 3, y1 - 5), (x1 - 3, y1 - 7)], fill=accent, width=2)
    elif sid == 23:  # Kenya & DRC ties: interlocking rings
        draw.ellipse((x0 + 4, y0 + 7, x0 + 15, y0 + 18), outline=accent, width=2)
        draw.ellipse((x0 + 9, y0 + 7, x1 - 4, y0 + 18), outline=ink, width=2)
    elif sid == 24:  # Albanese / Bowen: parliament podium + mic
        draw.rectangle((x0 + 7, y0 + 12, x1 - 7, y1 - 4), outline=ink, width=2)
        draw.line((cx, y0 + 7, cx, y0 + 12), fill=accent, width=2)
        draw.ellipse((cx - 3, y0 + 4, cx + 3, y0 + 9), fill=accent)
    elif sid == 25:  # PNG drought: sun rays + water drop
        draw.ellipse((x0 + 4, y0 + 4, x0 + 12, y0 + 12), outline=CRIMSON, width=2)
        draw.polygon([(cx + 4, y0 + 9), (cx + 8, y1 - 6), (cx, y1 - 6)], fill=accent, outline=ink)
        draw.ellipse((cx, y1 - 9, cx + 8, y1 - 3), fill=accent, outline=ink, width=1)
    elif sid == 26:  # WTO trade curbs: cargo container + stop bar
        draw.rectangle((x0 + 4, y0 + 7, x1 - 4, y1 - 6), outline=ink, width=2)
        draw.line((cx - 3, y0 + 7, cx - 3, y1 - 6), fill=accent, width=1)
        draw.line((cx + 3, y0 + 7, cx + 3, y1 - 6), fill=accent, width=1)
        draw.line((x0 + 4, y1 - 6, x1 - 4, y0 + 7), fill=CRIMSON, width=2)


# ---------------------------------------------------------------------------
# 7. Band Renderers (Bands 1 to 8)
# ---------------------------------------------------------------------------

def draw_band1_topbar(
    draw: ImageDraw.ImageDraw,
    story_count: int,
    region_count: int,
    tracker: CollisionTracker,
) -> None:
    box = (0, 0, CANVAS_W, 20)
    draw.rectangle(box, fill=NAVY_BAR)
    tracker.add("bands", "band1_topbar", box)

    left_txt = "THE WORLD IN ONE DAY"
    right_txt = f"{story_count} STORIES · {region_count} REGIONS · EVERY ONE DATED SUNDAY 22 NOVEMBER 2026"
    f_l, _, _, _ = fit(draw, left_txt, "sans_bold", 11, 9, 240, 16)
    f_r, _, _, _ = fit(draw, right_txt, "sans_bold", 10, 8, 740, 16)

    lb = draw_text_aligned(draw, (MARGIN_X, 0, 260, 20), left_txt, f_l, GOLD, align="left")
    rb = draw_text_aligned(draw, (260, 0, CANVAS_W - MARGIN_X, 20), right_txt, f_r, WHITE, align="right")
    tracker.add("band1_text", "left", lb)
    tracker.add("band1_text", "right", rb)


def draw_band2_masthead(draw: ImageDraw.ImageDraw, tracker: CollisionTracker) -> None:
    """Oversized crimson bold serif date masthead on open cream paper + double rule."""
    title = "Sunday 22 November 2026"
    mast_box = (MARGIN_X, 23, CANVAS_W - MARGIN_X, 71)
    tracker.add("bands", "band2_masthead", mast_box)

    f_title, _, _, _ = fit(draw, title, "serif_bold", 56, 44, INNER_W - 80, 48)
    tb = draw_text_centered(draw, mast_box, title, f_title, CRIMSON)
    tracker.add("band2_text", "date_title", tb)

    # Crisp double editorial rule
    draw.rectangle((MARGIN_X, 74, CANVAS_W - MARGIN_X, 75), fill=RULE_DARK)
    draw.rectangle((MARGIN_X, 77, CANVAS_W - MARGIN_X, 77), fill=CRIMSON)
    tracker.add("bands", "band2_rule", (MARGIN_X, 74, CANVAS_W - MARGIN_X, 77))


def draw_band3_kpi_strip(
    draw: ImageDraw.ImageDraw,
    kpis: Sequence[Tuple[str, str, int, str]],
    tracker: CollisionTracker,
) -> None:
    """Open, borderless 6-column KPI strip with crisp dark-navy serif figures & clean labels."""
    y0, y1 = 80, 127
    tracker.add("bands", "band3_kpi", (MARGIN_X, y0, CANVAS_W - MARGIN_X, y1))

    n = len(kpis)
    cell_w = INNER_W / n
    baseline_y = y0 + 30.0

    for idx, (val, label, _sid, _region) in enumerate(kpis):
        cx0 = MARGIN_X + idx * cell_w
        cx1 = MARGIN_X + (idx + 1) * cell_w
        if idx > 0:
            draw.line((cx0, y0 + 7, cx0, y1 - 7), fill=RULE_HAIRLINE, width=1)
        tracker.add("kpi_cells", f"kpi_{idx}", (cx0 + 1, y0, cx1 - 1, y1))

        f_val, _, _, _ = fit(draw, val, "serif_bold", 38, 30, (cx1 - cx0) - 10, 34)
        vb = draw_text_baseline_centered(draw, cx0 + 4, cx1 - 4, baseline_y, val, f_val, NAVY_BAR)

        f_lbl, _, _, _ = fit(draw, label, "sans_cond_bold", 10, 8, (cx1 - cx0) - 8, 12)
        lb = draw_text_centered(draw, (cx0 + 4, y0 + 35, cx1 - 4, y1 - 1), label, f_lbl, INK_MUTED)

        tracker.add(f"kpi_inner_{idx}", "val", vb)
        tracker.add(f"kpi_inner_{idx}", "lbl", lb)

    draw.line((MARGIN_X, y1, CANVAS_W - MARGIN_X, y1), fill=RULE_HAIRLINE, width=1)


def draw_band4_utc_timeline(draw: ImageDraw.ImageDraw, tracker: CollisionTracker) -> None:
    """Clean single-line navy DAY IN UTC strip (zero 2-line wrapping)."""
    y0, y1 = 132, 154
    bar_box = (MARGIN_X, y0, CANVAS_W - MARGIN_X, y1)
    draw.rectangle(bar_box, fill=NAVY_UTC)
    tracker.add("bands", "band4_utc", bar_box)

    lead_w = 88
    draw.rectangle((MARGIN_X, y0, MARGIN_X + 3, y1), fill=GOLD)
    f_t, _, _, _ = fit(draw, "DAY IN UTC", "sans_bold", 11, 9, lead_w - 8, 16)
    draw_text_centered(draw, (MARGIN_X + 4, y0, MARGIN_X + lead_w, y1), "DAY IN UTC", f_t, GOLD)
    draw.line((MARGIN_X + lead_w + 2, y0 + 4, MARGIN_X + lead_w + 2, y1 - 4), fill=NAVY_DIV, width=1)

    slots_x0 = MARGIN_X + lead_w + 6
    slots_w = (CANVAS_W - MARGIN_X) - slots_x0
    n = len(UTC_TIMELINE)
    slot_w = slots_w / n

    for idx, (tm, desc) in enumerate(UTC_TIMELINE):
        sx0 = slots_x0 + idx * slot_w
        sx1 = slots_x0 + (idx + 1) * slot_w
        if idx > 0:
            draw.line((sx0, y0 + 5, sx0, y1 - 5), fill=NAVY_DIV, width=1)
        tracker.add("utc_slots", f"utc_{idx}", (sx0 + 1, y0 + 1, sx1 - 1, y1 - 1))

        f_tm = get_font("mono_bold", 10)
        tm_w, _ = measure_text(draw, tm, f_tm)
        avail_desc = slot_w - tm_w - 14
        f_ds, _, ds_w, _ = fit(draw, desc, "sans_cond_bold", 10, 8, avail_desc, 14)

        total_w = tm_w + 5 + ds_w
        start_x = sx0 + (slot_w - total_w) / 2.0
        draw_text_aligned(draw, (start_x, y0, start_x + tm_w + 2, y1), tm, f_tm, GOLD, align="left")
        draw_text_aligned(draw, (start_x + tm_w + 5, y0, sx1 - 3, y1), desc, f_ds, WHITE, align="left")


def draw_band5_region_bar(
    draw: ImageDraw.ImageDraw,
    counts: Counter,
    tracker: CollisionTracker,
) -> None:
    y0, y1 = 159, 177
    tracker.add("bands", "band5_regions", (MARGIN_X, y0, CANVAS_W - MARGIN_X, y1))
    total = sum(counts.values())

    raw = [counts[r] / total * INNER_W for r in REGION_ORDER]
    widths = [int(math.floor(v)) for v in raw]
    rem = INNER_W - sum(widths)
    for i in sorted(range(len(raw)), key=lambda idx: raw[idx] - widths[idx], reverse=True)[:rem]:
        widths[i] += 1

    cx = MARGIN_X
    for r, w in zip(REGION_ORDER, widths):
        seg_box = (cx, y0, cx + w, y1)
        draw.rectangle(seg_box, fill=REGION_COLORS[r])
        if cx > MARGIN_X:
            draw.line((cx, y0, cx, y1), fill=BG_PAPER, width=1)
        tracker.add("region_bar", r, (cx + 0.5, y0, cx + w - 0.5, y1))

        lbl = f"{r} {counts[r]}"
        f_r, _, _, _ = fit(draw, lbl, "sans_cond_bold", 11, 8, w - 6, 14)
        draw_text_centered(draw, seg_box, lbl, f_r, WHITE)
        cx += w


def draw_band6_main_cards(
    draw: ImageDraw.ImageDraw,
    card_stories: Sequence[Story],
    tracker: CollisionTracker,
) -> int:
    """
    Band 6 (y=187..665, h=478): 14 borderless editorial cards in 4 rows (3+3+4+4).
    - Every card has height=112px, 10px row/col gaps, 8px inner padding.
    - Every card features a 110px-tall editorial illustration (102x110 on 3-col, 68x110 on 4-col).
    - Uniform rhythm: 19px bold serif headline (<=2L) + 12px lead (<=2L) + 9px source (1L).
    Returns number of main card illustrations drawn (must be 14).
    """
    assert len(card_stories) == 14
    y_start = 187
    card_h = 112
    row_specs = [
        (0, 3, 3, 110),   # Row 0: #1-#3 (3 cols, 110x110 hero art)
        (3, 6, 3, 110),   # Row 1: #4-#6 (3 cols, 110x110 hero art)
        (6, 10, 4, 68),   # Row 2: #7-#10 (4 cols, 68x110 art)
        (10, 14, 4, 68),  # Row 3: #11-#14 (4 cols, 68x110 art)
    ]
    y_end = y_start + 4 * card_h + 3 * GAP  # 665
    tracker.add("bands", "band6_cards", (MARGIN_X, y_start, CANVAS_W - MARGIN_X, y_end))

    art_count = 0
    for r_idx, (s_start, s_end, ncols, art_w) in enumerate(row_specs):
        y0 = y_start + r_idx * (card_h + GAP)
        y1 = y0 + card_h
        card_w = (INNER_W - (ncols - 1) * GAP) / ncols

        for c_idx, s in enumerate(card_stories[s_start:s_end]):
            x0 = int(round(MARGIN_X + c_idx * (card_w + GAP)))
            x1 = int(round(MARGIN_X + (c_idx + 1) * card_w + c_idx * GAP))
            accent = REGION_COLORS[s.region]

            # Open broadsheet card directly on warm paper: crisp 2px top region bar only
            draw.rectangle((x0, y0, x1, y0 + 2), fill=accent)
            draw.line((x0, y1, x1, y1), fill=RULE_HAIRLINE, width=1)
            tracker.add("cards", f"card_{s.id}", (x0, y0, x1, y1))

            # Left-side editorial illustration (strictly 110px tall: y0+2 .. y1)
            art_box = (x0, y0 + 2, x0 + art_w, y1)
            draw_main_card_illustration(draw, s, art_box, accent)
            art_count += 1
            tracker.add(f"card_{s.id}_inner", "art", art_box)

            # Right-side text column with clean 8px padding
            tx0 = art_box[2] + CARD_PAD
            tx1 = x1 - 6
            tw = tx1 - tx0

            # 1) Headline: 19px bold serif (max 2 lines)
            hl_font_key = "serif_bold" if ncols == 3 else "serif_cond_bold"
            try:
                f_hl, _, hl_lines, hl_lh = fit_multiline(
                    draw, s.headline, hl_font_key, 19, 17, tw,
                    max_lines=2, line_spacing=1.06, max_height=42,
                )
            except RuntimeError:
                f_hl, _, hl_lines, hl_lh = fit_multiline(
                    draw, s.headline, "serif_cond_bold", 18, 15, tw,
                    max_lines=2, line_spacing=1.06, max_height=42,
                )

            hy = y0 + CARD_PAD
            hl_bottom = hy
            for ln in hl_lines:
                tb = draw.textbbox((0, 0), ln, font=f_hl)
                draw.text((tx0 - tb[0], hy - tb[1]), ln, font=f_hl, fill=INK_DARK)
                hl_bottom = hy + (tb[3] - tb[1])
                hy += hl_lh
            tracker.add(f"card_{s.id}_inner", "headline", (tx0, y0 + CARD_PAD, tx1, hl_bottom))

            # 2) Lead: 12px regular sans (max 2 lines)
            lead_y0 = max(hl_bottom + 6, y0 + 50)
            lead_font_key = "sans_reg" if ncols == 3 else "sans_cond_reg"
            f_ld, _, ld_lines, ld_lh = fit_multiline(
                draw, s.lead, lead_font_key, 12, 10, tw,
                max_lines=2, line_spacing=1.18, max_height=31,
            )
            ly = lead_y0
            ld_bottom = ly
            for ln in ld_lines:
                tb = draw.textbbox((0, 0), ln, font=f_ld)
                draw.text((tx0 - tb[0], ly - tb[1]), ln, font=f_ld, fill=INK_BODY)
                ld_bottom = ly + (tb[3] - tb[1])
                ly += ld_lh
            tracker.add(f"card_{s.id}_inner", "lead", (tx0, lead_y0, tx1, ld_bottom))

            # 3) Source + location + plain status (9px, 1 line, anchored cleanly above bottom pad)
            src_y0 = y1 - CARD_PAD - 11
            src_y1 = y1 - CARD_PAD + 1
            src_txt = f"{s.location} · {s.source}" if ncols == 3 else f"{s.source} · {s.status}"
            f_src, _, _, _ = fit(draw, src_txt, "sans_cond_bold", 9, 8, tw, 12)
            sb = draw_text_aligned(draw, (tx0, src_y0, tx1, src_y1), src_txt, f_src, INK_MUTED, align="left")
            tracker.add(f"card_{s.id}_inner", "source", sb)

    return art_count


def draw_band7_map_and_briefs(
    draw: ImageDraw.ImageDraw,
    brief_stories: Sequence[Story],
    tracker: CollisionTracker,
) -> Tuple[int, int]:
    """
    Band 7 (y=675..895, h=220):
      - Left: 320x220 dark-navy minimalist world map with 12 collision-free pins (#15-#26).
      - Right: 666x220 open 2-col x 6-row grid of 12 briefs, each with a 24x24px line-art icon
        on the left and strictly 2 lines of text on the right.
    Returns (icons_drawn, displaced_map_pins).
    """
    assert len(brief_stories) == 12
    y0, y1 = 675, 895  # exact height = 220px, ends cleanly before y=896!
    tracker.add("bands", "band7_lower", (MARGIN_X, y0, CANVAS_W - MARGIN_X, y1))

    # --- Left 320x220 World Map (x=14..334) ---
    mx0, mx1 = MARGIN_X, MARGIN_X + 320
    tracker.add("band7_panes", "map", (mx0, y0, mx1, y1))

    hdr_h = 17
    f_sec = get_font("sans_bold", 10)
    f_sub = get_font("sans_cond_reg", 9)
    draw_text_aligned(draw, (mx0, y0, mx0 + 185, y0 + hdr_h), "WHERE IT HAPPENED", f_sec, CRIMSON, align="left")
    draw_text_aligned(draw, (mx0 + 185, y0, mx1, y0 + hdr_h), "PINS #15–#26", f_sub, INK_MUTED, align="right")

    map_vp = (mx0, y0 + hdr_h + 2, mx1, y1)  # 320 x 201 px
    draw.rectangle(map_vp, fill=MAP_OCEAN)

    # Subtle landmass polygons (zero busy lat/lon clutter -> low edge density)
    for reg, poly in WORLD_POLYGONS:
        pts = [project_lonlat(lon, lat, map_vp) for lon, lat in poly]
        draw.polygon(pts, fill=MAP_LAND_FILL[reg])

    pin_r = 7.2
    resolved = resolve_map_pin_collisions(brief_stories, map_vp, pin_radius=pin_r, min_gap=4.2)
    displaced = 0
    for s, (ax, ay), (px, py) in resolved:
        if math.hypot(px - ax, py - ay) > 2.5:
            displaced += 1
            draw.line((ax, ay, px, py), fill="#C8D7EC", width=1)
            draw.ellipse((ax - 1.8, ay - 1.8, ax + 1.8, ay + 1.8), fill=GOLD)

    f_pin = get_font("sans_bold", 8)
    for s, _, (px, py) in resolved:
        pbox = (px - pin_r, py - pin_r, px + pin_r, py + pin_r)
        draw.ellipse(pbox, fill=CRIMSON, outline=WHITE, width=1)
        draw_text_centered(draw, pbox, str(s.id), f_pin, WHITE)
        tracker.add("map_pins", f"pin_{s.id}", pbox)

    # --- Right 12 Illustrated Briefs (x=344..1010, w=666, h=220) ---
    bx0, bx1 = mx1 + GAP, CANVAS_W - MARGIN_X
    tracker.add("band7_panes", "briefs", (bx0, y0, bx1, y1))

    draw_text_aligned(
        draw, (bx0, y0, bx0 + 440, y0 + hdr_h),
        "ALSO ON SUNDAY 22 NOVEMBER · 12 ILLUSTRATED BRIEFS", f_sec, CRIMSON, align="left",
    )
    draw_text_aligned(
        draw, (bx1 - 200, y0, bx1, y0 + hdr_h),
        "MATCHES MAP PINS #15–#26", f_sub, INK_MUTED, align="right",
    )
    draw.line((bx0, y0 + hdr_h + 1, bx1, y0 + hdr_h + 1), fill=RULE_HAIRLINE, width=1)

    body_y0 = y0 + hdr_h + 3  # 695
    body_h = y1 - body_y0     # 200px -> 33.33px per row across 6 rows!
    row_h = body_h / 6.0
    col_gap = 12
    col_w = (bx1 - bx0 - col_gap) / 2.0  # 327px

    icons_drawn = 0
    for idx, s in enumerate(brief_stories):
        col = idx // 6
        row = idx % 6
        cx0 = bx0 + col * (col_w + col_gap)
        cx1 = cx0 + col_w
        ry0 = body_y0 + row * row_h
        ry1 = ry0 + row_h
        accent = REGION_COLORS[s.region]

        if row > 0:
            draw.line((cx0, ry0, cx1, ry0), fill="#E8E1D3", width=1)
        tracker.add("brief_rows", f"brief_{s.id}", (cx0, ry0 + 0.5, cx1, ry1 - 0.5))

        # Left 24x24px line-art icon (vertically centered in 33.3px row)
        ic_x0 = int(round(cx0))
        ic_y0 = int(round(ry0 + (row_h - 24) / 2.0))
        ic_box = (ic_x0, ic_y0, ic_x0 + 24, ic_y0 + 24)
        draw_brief_icon(draw, s, ic_box, accent)
        icons_drawn += 1

        # Right 2-line text block (number + headline on line 1; location + detail + source on line 2)
        tx0 = ic_box[2] + 8
        tw = cx1 - tx0

        num_txt = f"{s.id} "
        f_num = get_font("sans_bold", 11)
        num_w, _ = measure_text(draw, num_txt, f_num)

        f_hl, _, _, _ = fit(draw, s.headline, "serif_bold", 12, 10, tw - num_w - 2, 14)
        line1_box = (tx0, ry0 + 3, cx1, ry0 + 17)
        nb = draw_text_aligned(draw, (tx0, ry0 + 3, tx0 + num_w + 2, ry0 + 17), num_txt, f_num, accent, align="left")
        hb = draw_text_aligned(draw, (tx0 + num_w + 1, ry0 + 3, cx1, ry0 + 17), s.headline, f_hl, INK_DARK, align="left")

        line2_txt = f"{s.location} · {s.lead} ({s.source})"
        f_l2, _, _, _ = fit(draw, line2_txt, "sans_cond_reg", 10, 8, tw, 12)
        l2b = draw_text_aligned(draw, (tx0, ry0 + 18, cx1, ry1 - 2), line2_txt, f_l2, INK_MUTED, align="left")

        tracker.add(f"brief_inner_{s.id}", "icon", ic_box)
        tracker.add(f"brief_inner_{s.id}", "num", nb)
        tracker.add(f"brief_inner_{s.id}", "headline", hb)
        tracker.add(f"brief_inner_{s.id}", "line2", l2b)

    return icons_drawn, displaced


def draw_band8_quiet_bottom(draw: ImageDraw.ImageDraw, tracker: CollisionTracker) -> None:
    """
    Band 8 (y=896..1024, 128px): Deliberate breathing room matching champion's quiet finish.
    Contains ONLY:
      - DATE CHECK — READ THIS FIRST (y=912..954, h=42px, <=2 lines)
      - Single-line editorial colophon footer (y=994..1012, h=18px) with broadsheet double rule
    Total active height = 60px (<=70px); remaining 68px is pure open cream newsprint.
    """
    # 1) DATE CHECK box (y=912..954, h=42px)
    dx0, dy0, dx1, dy1 = MARGIN_X, 912, CANVAS_W - MARGIN_X, 954
    dc_box = (dx0, dy0, dx1, dy1)
    draw.rectangle(dc_box, fill=DATE_CHECK_BG, outline=CRIMSON, width=1)
    tracker.add("bands", "band8_date_check", dc_box)

    # Line 1: Bold crimson header + verification cutoff
    p1 = "DATE CHECK — READ THIS FIRST"
    f_p1 = get_font("sans_bold", 10)
    p1w, _ = measure_text(draw, p1, f_p1)
    r1_b1 = draw_text_aligned(draw, (dx0 + 10, dy0 + 6, dx0 + 10 + p1w + 4, dy0 + 19), p1, f_p1, CRIMSON, align="left")

    c1 = "· Cutoff Sun 22 Nov 2026 23:59 UTC. Every story verified to this date; prior-day news excluded."
    f_c1, _, _, _ = fit(draw, c1, "sans_reg", 10, 9, dx1 - 10 - (r1_b1[2] + 5), 14)
    r1_b2 = draw_text_aligned(draw, (r1_b1[2] + 5, dy0 + 6, dx1 - 10, dy0 + 19), c1, f_c1, INK_DARK, align="left")
    tracker.add("band8_row1", "title", r1_b1)
    tracker.add("band8_row1", "cutoff", r1_b2)

    # Line 2: Excluded near-date stories
    p2 = "EXCLUDED:"
    f_p2 = get_font("sans_bold", 10)
    p2w, _ = measure_text(draw, p2, f_p2)
    r2_b1 = draw_text_aligned(draw, (dx0 + 10, dy0 + 23, dx0 + 10 + p2w + 4, dy1 - 6), p2, f_p2, CRIMSON, align="left")

    ex_txt = " · ".join(EXCLUDED_ITEMS)
    f_ex, _, _, _ = fit(draw, ex_txt, "sans_reg", 10, 8, dx1 - 10 - (r2_b1[2] + 5), 13)
    r2_b2 = draw_text_aligned(draw, (r2_b1[2] + 5, dy0 + 23, dx1 - 10, dy1 - 6), ex_txt, f_ex, INK_BODY, align="left")
    tracker.add("band8_row2", "label", r2_b1)
    tracker.add("band8_row2", "items", r2_b2)

    # 2) Anchored single-line editorial footer (y=994..1012, h=18px) with broadsheet double rule
    fy0, fy1 = 994, 1012
    draw.rectangle((MARGIN_X, fy0 - 6, CANVAS_W - MARGIN_X, fy0 - 5), fill=NAVY_BAR)
    draw.line((MARGIN_X, fy0 - 3, CANVAS_W - MARGIN_X, fy0 - 3), fill=RULE_HAIRLINE, width=1)
    foot_l = "SUNDAY 22 NOVEMBER 2026 · 26 VERIFIED STORIES · 7 REGIONS · 26 ORIGINAL ILLUSTRATIONS"
    foot_r = "PROGRAMMATICALLY RENDERED · PYTHON / PILLOW"
    f_fl, _, _, _ = fit(draw, foot_l, "sans_cond_bold", 10, 8, 660, 14)
    f_fr, _, _, _ = fit(draw, foot_r, "sans_cond_bold", 10, 8, 310, 14)
    flb = draw_text_aligned(draw, (MARGIN_X, fy0, MARGIN_X + 670, fy1), foot_l, f_fl, INK_DARK, align="left")
    frb = draw_text_aligned(draw, (CANVAS_W - MARGIN_X - 320, fy0, CANVAS_W - MARGIN_X, fy1), foot_r, f_fr, INK_MUTED, align="right")
    tracker.add("bands", "band8_footer", (MARGIN_X, fy0, CANVAS_W - MARGIN_X, fy1))
    tracker.add("band8_foot_txt", "left", flb)
    tracker.add("band8_foot_txt", "right", frb)


# ---------------------------------------------------------------------------
# 8. Quantitative Self-Audit & Deterministic Pipeline
# ---------------------------------------------------------------------------

def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def measure_visual_metrics(img: Image.Image) -> Dict[str, object]:
    """Compute exact 8-band PIL FIND_EDGES density and lower-half content ratio."""
    gray = img.convert("L")
    edges = np.array(gray.filter(ImageFilter.FIND_EDGES), dtype=np.float64)
    band_edges = [float(edges[i * 128:(i + 1) * 128].mean()) for i in range(8)]

    arr = np.array(img.convert("RGB"), dtype=np.float64)
    # Paper background RGB (#F8F3E9 = 248, 243, 233)
    bg_rgb = np.array([248.0, 243.0, 233.0])
    non_paper = np.linalg.norm(arr - bg_rgb, axis=2) > 5.0

    # Also compute 16x16 block occupancy (non-uniform blocks) for conservative audit
    blocks = arr.reshape(64, 16, 64, 16, 3)
    block_occ = (blocks.max(axis=(1, 3)) - blocks.min(axis=(1, 3))).max(axis=2) > 10.0

    return {
        "band_edges": [round(b, 1) for b in band_edges],
        "edge_y896_1024": round(band_edges[7], 2),
        "content_all_px": round(float(non_paper.mean()) * 100.0, 1),
        "content_top_px": round(float(non_paper[:512].mean()) * 100.0, 1),
        "content_bot_px": round(float(non_paper[512:].mean()) * 100.0, 1),
        "content_bot_blk16": round(float(block_occ[32:].mean()) * 100.0, 1),
    }


def build() -> None:
    region_counts = validate_dataset(STORIES)
    kpis = extract_verified_kpis(STORIES)

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_PAPER)
    draw = ImageDraw.Draw(img)
    tracker = CollisionTracker(CANVAS_W, CANVAS_H)

    draw_band1_topbar(draw, len(STORIES), len(region_counts), tracker)
    draw_band2_masthead(draw, tracker)
    draw_band3_kpi_strip(draw, kpis, tracker)
    draw_band4_utc_timeline(draw, tracker)
    draw_band5_region_bar(draw, region_counts, tracker)
    main_art_count = draw_band6_main_cards(draw, STORIES[:14], tracker)
    brief_icon_count, displaced = draw_band7_map_and_briefs(draw, STORIES[14:26], tracker)
    draw_band8_quiet_bottom(draw, tracker)

    total_illustrations = main_art_count + brief_icon_count
    assert main_art_count == 14, f"Expected 14 main illustrations, got {main_art_count}"
    assert brief_icon_count == 12, f"Expected 12 brief icons, got {brief_icon_count}"
    assert total_illustrations >= 26, f"Expected >=26 illustrations, got {total_illustrations}"

    checked_pairs = tracker.assert_no_collisions()

    img.save(ENTRY_PATH, format="PNG", optimize=True, compress_level=9)
    size_bytes = ENTRY_PATH.stat().st_size
    assert img.size == (CANVAS_W, CANVAS_H), f"Bad size: {img.size}"
    assert size_bytes <= MAX_BYTES, f"entry.png exceeds 1 MiB: {size_bytes}"

    preview = img.resize((300, 300), Image.Resampling.LANCZOS)
    preview.save(PREVIEW_PATH, format="PNG", optimize=True, compress_level=9)

    metrics = measure_visual_metrics(img)
    digest = md5_file(ENTRY_PATH)

    print(f"OK | stories={len(STORIES)} | regions={dict((r, region_counts[r]) for r in REGION_ORDER)}")
    print(f"OK | kpis={[k[0] for k in kpis]}")
    print(f"OK | illustrations={total_illustrations} (main={main_art_count}, brief_icons={brief_icon_count})")
    print(f"OK | collision_boxes={tracker.total_registered} | checked_pairs={checked_pairs} | map_leaders={displaced}")
    print(f"OK | band_edges={metrics['band_edges']} | y896-1024={metrics['edge_y896_1024']}")
    print(
        f"OK | content_px: all={metrics['content_all_px']}% "
        f"top={metrics['content_top_px']}% bot={metrics['content_bot_px']}% "
        f"| bot_blk16={metrics['content_bot_blk16']}%"
    )
    print(f"OK | entry.png: {img.size[0]}x{img.size[1]}, {size_bytes:,} bytes (<= {MAX_BYTES:,}), md5={digest}")
    print(f"OK | preview-300.png: {preview.size[0]}x{preview.size[1]}, {PREVIEW_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    build()
