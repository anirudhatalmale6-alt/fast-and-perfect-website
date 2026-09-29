#!/usr/bin/env python3
"""
Generates the placeholder artwork used across the Fast and Perfect site.

These are flat geometric interior illustrations drawn in the brand palette.
They exist so the site looks finished before real job photography arrives —
every one of them is meant to be swapped for a real photo. File names stay
the same, so dropping a real .jpg in with the matching name is all it takes
(then change the extension in the HTML, or just save the photo as .svg's
neighbour and update the src).
"""
import math
import os
import random

OUT = os.path.join(os.path.dirname(__file__), "..", "site", "assets", "img")

PAL = {
    "bone": "#f6f2ea",
    "paper": "#fffdf8",
    "ink": "#131c17",
    "pine": "#1c4b3a",
    "pine_deep": "#0f2e23",
    "pine_lift": "#276250",
    "sage": "#dce6dd",
    "sage_deep": "#b6cbbc",
    "marigold": "#e3a02c",
    "marigold_soft": "#f0c67d",
}

W, H = 1200, 900


def head(w=W, h=H, extra=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img">{extra}'
    )


def defs(grad_id, c1, c2, angle="v"):
    x2, y2 = ("0", "1") if angle == "v" else ("1", "0")
    return (
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
        f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/>'
        f"</linearGradient></defs>"
    )


def sparkle(cx, cy, r, fill, op=0.9):
    """Four-point star — the 'clean' motif used throughout."""
    k = r * 0.28
    return (
        f'<path d="M {cx} {cy - r} C {cx + k} {cy - k} {cx + k} {cy - k} {cx + r} {cy} '
        f"C {cx + k} {cy + k} {cx + k} {cy + k} {cx} {cy + r} "
        f"C {cx - k} {cy + k} {cx - k} {cy + k} {cx - r} {cy} "
        f'C {cx - k} {cy - k} {cx - k} {cy - k} {cx} {cy - r} Z" '
        f'fill="{fill}" opacity="{op}"/>'
    )


def grain(op=0.05):
    return (
        f'<filter id="g"><feTurbulence type="fractalNoise" baseFrequency="0.9" '
        f'numOctaves="3"/><feColorMatrix type="saturate" values="0"/></filter>'
        f'<rect width="{W}" height="{H}" filter="url(#g)" opacity="{op}"/>'
    )


# ---------------------------------------------------------------- scenes
def living_room(dull=False):
    """Bright living room: window, light beam, sofa, rug, plant."""
    wall_a = "#e6ddd0" if dull else PAL["bone"]
    wall_b = "#cfc6b6" if dull else "#e9e3d6"
    floor_a = "#9a8c76" if dull else "#d9c9ad"
    floor_b = "#7d715e" if dull else "#c2ad8c"
    light = 0.10 if dull else 0.34
    sofa = "#8d9b90" if dull else PAL["sage_deep"]
    accent = "#a98c52" if dull else PAL["marigold"]

    s = [head(extra="")]
    s.append(
        f'<defs><linearGradient id="w" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{wall_a}"/><stop offset="1" stop-color="{wall_b}"/>'
        f"</linearGradient>"
        f'<linearGradient id="f" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{floor_a}"/><stop offset="1" stop-color="{floor_b}"/>'
        f"</linearGradient>"
        f'<linearGradient id="beam" x1="0" y1="0" x2="0.4" y2="1">'
        f'<stop offset="0" stop-color="#fff8e4" stop-opacity="{light}"/>'
        f'<stop offset="1" stop-color="#fff8e4" stop-opacity="0"/></linearGradient>'
        f"</defs>"
    )
    # wall + floor
    s.append(f'<rect width="{W}" height="{H}" fill="url(#w)"/>')
    s.append(f'<rect y="600" width="{W}" height="300" fill="url(#f)"/>')
    s.append(f'<rect y="596" width="{W}" height="5" fill="{PAL["ink"]}" opacity="0.10"/>')

    # window
    s.append(f'<rect x="700" y="130" width="380" height="400" rx="8" fill="{PAL["paper"]}" opacity="0.92"/>')
    s.append(f'<rect x="700" y="130" width="380" height="400" rx="8" fill="none" stroke="{PAL["pine_deep"]}" stroke-width="7" opacity="0.55"/>')
    s.append(f'<line x1="890" y1="130" x2="890" y2="530" stroke="{PAL["pine_deep"]}" stroke-width="7" opacity="0.55"/>')
    s.append(f'<line x1="700" y1="330" x2="1080" y2="330" stroke="{PAL["pine_deep"]}" stroke-width="7" opacity="0.55"/>')
    # sky in the window
    s.append(f'<rect x="707" y="137" width="366" height="386" rx="4" fill="#cfe0e6" opacity="{0.4 if dull else 0.75}"/>')
    s.append(f'<circle cx="1010" cy="215" r="34" fill="{PAL["marigold_soft"]}" opacity="{0.35 if dull else 0.85}"/>')

    # light beam onto the floor
    s.append(f'<path d="M700 130 L1080 130 L1180 760 L420 760 Z" fill="url(#beam)"/>')

    # rug
    s.append(f'<ellipse cx="520" cy="742" rx="430" ry="88" fill="{PAL["pine"]}" opacity="{0.10 if dull else 0.16}"/>')

    # sofa
    s.append(f'<rect x="150" y="430" width="440" height="150" rx="26" fill="{sofa}"/>')
    s.append(f'<rect x="150" y="530" width="470" height="110" rx="24" fill="{sofa}" opacity="0.85"/>')
    s.append(f'<rect x="120" y="470" width="60" height="170" rx="24" fill="{sofa}"/>')
    s.append(f'<rect x="588" y="470" width="60" height="170" rx="24" fill="{sofa}"/>')
    # cushions
    s.append(f'<rect x="205" y="452" width="120" height="96" rx="16" fill="{PAL["paper"]}" opacity="0.5"/>')
    s.append(f'<rect x="345" y="452" width="120" height="96" rx="16" fill="{accent}" opacity="0.65"/>')
    # legs
    for lx in (150, 600):
        s.append(f'<rect x="{lx}" y="636" width="16" height="34" rx="6" fill="{PAL["pine_deep"]}" opacity="0.5"/>')

    # coffee table
    s.append(f'<rect x="300" y="672" width="300" height="16" rx="8" fill="{PAL["pine_deep"]}" opacity="0.42"/>')
    s.append(f'<rect x="330" y="686" width="12" height="46" rx="5" fill="{PAL["pine_deep"]}" opacity="0.32"/>')
    s.append(f'<rect x="558" y="686" width="12" height="46" rx="5" fill="{PAL["pine_deep"]}" opacity="0.32"/>')

    # plant
    s.append(f'<path d="M980 600 L1020 600 L1012 700 L988 700 Z" fill="{accent}" opacity="0.8"/>')
    for i, (dx, dy, rr) in enumerate([(-46, -70, 40), (0, -104, 46), (44, -66, 38), (-22, -40, 30), (26, -36, 30)]):
        s.append(f'<ellipse cx="{1000 + dx}" cy="{600 + dy}" rx="{rr}" ry="{rr * 0.72}" '
                 f'fill="{PAL["pine"] if not dull else "#5c6b5f"}" opacity="{0.55 + i * 0.07:.2f}" '
                 f'transform="rotate({dx * 0.4} {1000 + dx} {600 + dy})"/>')

    # wall art — filled, so it reads as a framed picture rather than a
    # broken-image glyph
    s.append(f'<rect x="230" y="170" width="200" height="160" rx="4" fill="{PAL["paper"]}" opacity="{0.55 if dull else 0.85}"/>')
    s.append(f'<rect x="242" y="182" width="176" height="136" rx="2" fill="{PAL["sage"]}" opacity="{0.6 if dull else 0.95}"/>')
    s.append(f'<circle cx="300" cy="222" r="22" fill="{accent}" opacity="{0.45 if dull else 0.8}"/>')
    s.append(f'<path d="M242 318 Q300 252 360 296 Q400 322 418 300 L418 318 Z" fill="{PAL["pine"] if not dull else "#6b7a6e"}" opacity="0.7"/>')
    s.append(f'<path d="M242 318 Q286 278 330 318 Z" fill="{PAL["pine_deep"] if not dull else "#55614f"}" opacity="0.55"/>')
    s.append(f'<rect x="230" y="170" width="200" height="160" rx="4" fill="none" stroke="{PAL["pine_deep"]}" stroke-width="7" opacity="0.4"/>')

    if dull:
        # grime: scattered specks and smears
        rng = random.Random(7)
        for _ in range(180):
            x = rng.uniform(0, W)
            y = rng.uniform(560, H)
            r = rng.uniform(1.5, 6)
            s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#4a3f2c" opacity="{rng.uniform(0.06, 0.2):.2f}"/>')
        for _ in range(9):
            x = rng.uniform(120, 1080)
            y = rng.uniform(620, 860)
            s.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rng.uniform(40, 120):.0f}" '
                     f'ry="{rng.uniform(10, 26):.0f}" fill="#3f3524" opacity="0.10" '
                     f'transform="rotate({rng.uniform(-18, 18):.0f} {x:.0f} {y:.0f})"/>')
        s.append(f'<rect width="{W}" height="{H}" fill="#6b5b3e" opacity="0.10"/>')
    else:
        # clean: sparkles
        for (cx, cy, r, op) in [(640, 250, 26, 0.9), (700, 320, 14, 0.7), (1120, 470, 18, 0.8),
                                (300, 390, 16, 0.6), (870, 660, 20, 0.55)]:
            s.append(sparkle(cx, cy, r, PAL["marigold"], op))
        s.append(f'<rect width="{W}" height="{H}" fill="#fffaf0" opacity="0.06"/>')

    s.append(f"<defs>{''}</defs>")
    s.append("</svg>")
    return "".join(s)


def office():
    s = [head()]
    s.append(defs("w", "#eef1ec", "#dbe3dc"))
    s.append(f'<rect width="{W}" height="{H}" fill="url(#w)"/>')
    s.append(f'<rect y="620" width="{W}" height="280" fill="{PAL["sage_deep"]}" opacity="0.5"/>')
    s.append(f'<rect y="616" width="{W}" height="5" fill="{PAL["pine_deep"]}" opacity="0.14"/>')

    # window wall
    for i in range(4):
        x = 60 + i * 300
        s.append(f'<rect x="{x}" y="90" width="250" height="420" rx="6" fill="#cfe0e6" opacity="0.6"/>')
        s.append(f'<rect x="{x}" y="90" width="250" height="420" rx="6" fill="none" stroke="{PAL["pine_deep"]}" stroke-width="6" opacity="0.4"/>')

    # ceiling lights
    for i in range(3):
        x = 200 + i * 400
        s.append(f'<rect x="{x}" y="0" width="180" height="26" rx="13" fill="{PAL["marigold_soft"]}" opacity="0.7"/>')
        s.append(f'<path d="M{x} 26 L{x + 180} 26 L{x + 250} 300 L{x - 70} 300 Z" fill="#fff8e4" opacity="0.22"/>')

    # desk row
    for i in range(3):
        x = 110 + i * 370
        s.append(f'<rect x="{x}" y="560" width="300" height="20" rx="8" fill="{PAL["pine_deep"]}" opacity="0.55"/>')
        s.append(f'<rect x="{x + 16}" y="580" width="14" height="110" rx="6" fill="{PAL["pine_deep"]}" opacity="0.38"/>')
        s.append(f'<rect x="{x + 270}" y="580" width="14" height="110" rx="6" fill="{PAL["pine_deep"]}" opacity="0.38"/>')
        # monitor
        s.append(f'<rect x="{x + 88}" y="452" width="150" height="96" rx="8" fill="{PAL["pine"]}"/>')
        s.append(f'<rect x="{x + 96}" y="460" width="134" height="80" rx="4" fill="{PAL["sage"]}" opacity="0.85"/>')
        s.append(f'<rect x="{x + 152}" y="548" width="22" height="14" fill="{PAL["pine"]}"/>')
        # chair
        s.append(f'<rect x="{x + 118}" y="640" width="90" height="18" rx="9" fill="{PAL["pine"]}" opacity="0.7"/>')
        s.append(f'<rect x="{x + 126}" y="566" width="74" height="76" rx="18" fill="{PAL["pine"]}" opacity="0.55"/>')
        s.append(f'<rect x="{x + 157}" y="658" width="12" height="40" rx="5" fill="{PAL["pine_deep"]}" opacity="0.45"/>')
        s.append(f'<ellipse cx="{x + 163}" cy="702" rx="42" ry="9" fill="{PAL["pine_deep"]}" opacity="0.2"/>')

    # floor sheen
    s.append(f'<path d="M0 900 L360 620 L640 620 L200 900 Z" fill="#ffffff" opacity="0.16"/>')
    s.append(f'<path d="M420 900 L760 620 L860 620 L520 900 Z" fill="#ffffff" opacity="0.1"/>')

    for (cx, cy, r, op) in [(1080, 200, 24, 0.85), (1020, 280, 13, 0.6), (150, 730, 20, 0.5)]:
        s.append(sparkle(cx, cy, r, PAL["marigold"], op))
    s.append("</svg>")
    return "".join(s)


def carpet(dull=False):
    """Close-up carpet with a vacuum track."""
    base_a = "#8e8370" if dull else "#c9b9a0"
    base_b = "#6f6757" if dull else "#b3a288"
    s = [head()]
    s.append(defs("c", base_a, base_b))
    s.append(f'<rect width="{W}" height="{H}" fill="url(#c)"/>')

    rng = random.Random(11)
    # pile texture — drawn once into a 150px tile, then repeated. Keeps the
    # file a few KB instead of a quarter of a megabyte.
    tile = []
    T = 150
    for _ in range(110):
        x = rng.uniform(0, T)
        y = rng.uniform(0, T)
        ln = rng.uniform(5, 13)
        op = rng.uniform(0.05, 0.16)
        col = "#5b5244" if rng.random() < 0.5 else "#e4d8c2"
        tile.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + rng.uniform(-3, 3):.1f}" '
                    f'y2="{y + ln:.1f}" stroke="{col}" stroke-width="2.4" opacity="{op:.2f}"/>')
    s.append(f'<defs><pattern id="pile" width="{T}" height="{T}" patternUnits="userSpaceOnUse">'
             + "".join(tile) + "</pattern></defs>")
    s.append(f'<rect width="{W}" height="{H}" fill="url(#pile)"/>')

    if dull:
        for _ in range(16):
            x = rng.uniform(80, W - 80)
            y = rng.uniform(80, H - 80)
            s.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rng.uniform(40, 130):.0f}" '
                     f'ry="{rng.uniform(26, 80):.0f}" fill="#4a3c26" opacity="{rng.uniform(0.10, 0.24):.2f}"/>')
        s.append(f'<rect width="{W}" height="{H}" fill="#57492f" opacity="0.14"/>')
    else:
        # vacuum tracks
        for i in range(7):
            x = i * 172
            s.append(f'<rect x="{x}" y="0" width="86" height="{H}" fill="#ffffff" opacity="0.13"/>')
            s.append(f'<rect x="{x + 86}" y="0" width="86" height="{H}" fill="#7a6a52" opacity="0.06"/>')
        s.append(f'<rect width="{W}" height="{H}" fill="#fff6e6" opacity="0.10"/>')
        for (cx, cy, r, op) in [(240, 190, 28, 0.85), (330, 280, 15, 0.6), (960, 640, 24, 0.7), (860, 730, 13, 0.5)]:
            s.append(sparkle(cx, cy, r, PAL["marigold"], op))

    s.append("</svg>")
    return "".join(s)


def kitchen():
    s = [head()]
    s.append(defs("w", "#f1ece1", "#e0d9cb"))
    s.append(f'<rect width="{W}" height="{H}" fill="url(#w)"/>')
    # backsplash tiles
    for r in range(4):
        for c in range(16):
            x = 40 + c * 72 + (36 if r % 2 else 0)
            y = 180 + r * 62
            s.append(f'<rect x="{x}" y="{y}" width="64" height="54" rx="6" fill="{PAL["paper"]}" opacity="0.7"/>')
    # counter
    s.append(f'<rect y="440" width="{W}" height="42" rx="6" fill="{PAL["pine_deep"]}" opacity="0.6"/>')
    s.append(f'<rect y="440" width="{W}" height="12" fill="{PAL["paper"]}" opacity="0.25"/>')
    # cabinets
    s.append(f'<rect y="482" width="{W}" height="300" fill="{PAL["sage_deep"]}" opacity="0.65"/>')
    for i in range(6):
        x = 20 + i * 196
        s.append(f'<rect x="{x}" y="500" width="176" height="264" rx="8" fill="{PAL["paper"]}" opacity="0.45"/>')
        s.append(f'<rect x="{x + 140}" y="530" width="12" height="52" rx="6" fill="{PAL["pine_deep"]}" opacity="0.45"/>')
    # floor
    s.append(f'<rect y="782" width="{W}" height="118" fill="{PAL["bone"]}"/>')
    s.append(f'<path d="M0 900 L300 782 L440 782 L120 900 Z" fill="#ffffff" opacity="0.45"/>')
    # sink + tap
    s.append(f'<rect x="430" y="446" width="200" height="30" rx="10" fill="{PAL["pine_deep"]}" opacity="0.45"/>')
    s.append(f'<path d="M530 446 L530 360 Q530 330 566 330 L604 330" fill="none" stroke="{PAL["pine_deep"]}" stroke-width="12" stroke-linecap="round" opacity="0.6"/>')
    # jars
    s.append(f'<rect x="820" y="376" width="52" height="64" rx="8" fill="{PAL["marigold"]}" opacity="0.75"/>')
    s.append(f'<rect x="886" y="358" width="46" height="82" rx="8" fill="{PAL["pine"]}" opacity="0.55"/>')
    for (cx, cy, r, op) in [(160, 150, 26, 0.85), (250, 230, 14, 0.6), (1060, 520, 22, 0.7)]:
        s.append(sparkle(cx, cy, r, PAL["marigold"], op))
    s.append("</svg>")
    return "".join(s)


def bathroom():
    s = [head()]
    s.append(defs("w", "#eef2ef", "#dae4dd"))
    s.append(f'<rect width="{W}" height="{H}" fill="url(#w)"/>')
    # tile grid
    for r in range(9):
        for c in range(12):
            s.append(f'<rect x="{c * 100 + 6}" y="{r * 100 + 6}" width="88" height="88" rx="5" '
                     f'fill="{PAL["paper"]}" opacity="{0.30 + ((r + c) % 3) * 0.08:.2f}"/>')
    # bathtub
    s.append(f'<rect x="120" y="520" width="620" height="230" rx="60" fill="{PAL["paper"]}"/>')
    s.append(f'<rect x="160" y="556" width="540" height="160" rx="44" fill="{PAL["sage"]}" opacity="0.8"/>')
    s.append(f'<rect x="120" y="520" width="620" height="230" rx="60" fill="none" stroke="{PAL["pine_deep"]}" stroke-width="5" opacity="0.2"/>')
    # tap
    s.append(f'<path d="M700 520 L700 430 Q700 404 730 404 L772 404" fill="none" stroke="{PAL["pine_deep"]}" stroke-width="13" stroke-linecap="round" opacity="0.55"/>')
    # mirror
    s.append(f'<rect x="850" y="140" width="270" height="320" rx="135" fill="{PAL["paper"]}" opacity="0.9"/>')
    s.append(f'<rect x="850" y="140" width="270" height="320" rx="135" fill="none" stroke="{PAL["pine"]}" stroke-width="8" opacity="0.45"/>')
    s.append(f'<path d="M880 400 Q985 300 1090 400" fill="none" stroke="#ffffff" stroke-width="16" opacity="0.7"/>')
    # towels
    s.append(f'<rect x="880" y="530" width="90" height="150" rx="12" fill="{PAL["marigold"]}" opacity="0.7"/>')
    s.append(f'<rect x="985" y="530" width="90" height="150" rx="12" fill="{PAL["pine"]}" opacity="0.4"/>')
    # floor
    s.append(f'<rect y="760" width="{W}" height="140" fill="{PAL["sage_deep"]}" opacity="0.4"/>')
    s.append(f'<path d="M0 900 L260 760 L400 760 L140 900 Z" fill="#ffffff" opacity="0.35"/>')
    for (cx, cy, r, op) in [(790, 220, 26, 0.85), (700, 300, 14, 0.6), (250, 300, 20, 0.55), (1140, 640, 16, 0.5)]:
        s.append(sparkle(cx, cy, r, PAL["marigold"], op))
    s.append("</svg>")
    return "".join(s)


def crew():
    """Abstract crew figures — stand-in for a real team photo."""
    s = [head()]
    s.append(defs("w", PAL["sage"], "#c6d6c9"))
    s.append(f'<rect width="{W}" height="{H}" fill="url(#w)"/>')
    s.append(f'<circle cx="600" cy="430" r="330" fill="{PAL["paper"]}" opacity="0.45"/>')
    s.append(f'<rect y="700" width="{W}" height="200" fill="{PAL["pine"]}" opacity="0.12"/>')
    tones = [PAL["pine"], PAL["pine_lift"], PAL["pine_deep"]]
    for i, cx in enumerate((360, 600, 840)):
        t = tones[i % 3]
        top = 300 + (i % 2) * 26
        s.append(f'<circle cx="{cx}" cy="{top}" r="74" fill="{t}"/>')
        s.append(f'<path d="M{cx - 120} 780 Q{cx - 120} {top + 110} {cx} {top + 110} '
                 f'Q{cx + 120} {top + 110} {cx + 120} 780 Z" fill="{t}"/>')
        # apron stripe
        s.append(f'<rect x="{cx - 46}" y="{top + 170}" width="92" height="180" rx="14" fill="{PAL["marigold"]}" opacity="0.75"/>')
    for (cx, cy, r, op) in [(190, 210, 30, 0.8), (1020, 180, 22, 0.7), (1090, 640, 18, 0.5), (140, 600, 16, 0.45)]:
        s.append(sparkle(cx, cy, r, PAL["marigold"], op))
    s.append("</svg>")
    return "".join(s)


def window_clean():
    s = [head()]
    s.append(defs("w", "#dfeaef", "#c3d6de"))
    s.append(f'<rect width="{W}" height="{H}" fill="url(#w)"/>')
    # big window frame
    s.append(f'<rect x="90" y="70" width="1020" height="760" rx="10" fill="none" stroke="{PAL["pine_deep"]}" stroke-width="16" opacity="0.6"/>')
    s.append(f'<line x1="600" y1="70" x2="600" y2="830" stroke="{PAL["pine_deep"]}" stroke-width="14" opacity="0.6"/>')
    s.append(f'<line x1="90" y1="450" x2="1110" y2="450" stroke="{PAL["pine_deep"]}" stroke-width="14" opacity="0.6"/>')
    # sky + city
    s.append(f'<rect x="106" y="86" width="988" height="728" fill="#cfe4ec" opacity="0.7"/>')
    s.append(f'<circle cx="930" cy="230" r="58" fill="{PAL["marigold_soft"]}" opacity="0.8"/>')
    for i, (x, w, h) in enumerate([(150, 90, 200), (255, 70, 150), (340, 110, 240), (465, 60, 120)]):
        s.append(f'<rect x="{x}" y="{814 - h}" width="{w}" height="{h}" fill="{PAL["pine"]}" opacity="0.22"/>')
    # squeegee sweep
    s.append(f'<path d="M640 120 L1080 120 L1080 430 L640 430 Z" fill="#ffffff" opacity="0.42"/>')
    s.append(f'<path d="M640 120 L760 120 L700 430 L640 430 Z" fill="#ffffff" opacity="0.5"/>')
    # streak marks on the dirty half
    rng = random.Random(3)
    for _ in range(70):
        x = rng.uniform(120, 580)
        y = rng.uniform(100, 800)
        s.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x + rng.uniform(-30, 30):.0f}" '
                 f'y2="{y + rng.uniform(20, 70):.0f}" stroke="#8a8f7a" stroke-width="3" '
                 f'opacity="{rng.uniform(0.06, 0.18):.2f}"/>')
    for (cx, cy, r, op) in [(880, 540, 28, 0.85), (960, 620, 15, 0.6), (1030, 330, 20, 0.6)]:
        s.append(sparkle(cx, cy, r, PAL["marigold"], op))
    s.append("</svg>")
    return "".join(s)


def hallway():
    s = [head()]
    s.append(defs("w", "#f2eee4", "#e2dccd"))
    s.append(f'<rect width="{W}" height="{H}" fill="url(#w)"/>')
    # perspective corridor
    s.append(f'<path d="M0 0 L300 240 L300 660 L0 900 Z" fill="{PAL["sage"]}" opacity="0.75"/>')
    s.append(f'<path d="M{W} 0 L900 240 L900 660 L{W} 900 Z" fill="{PAL["sage"]}" opacity="0.55"/>')
    s.append(f'<rect x="300" y="240" width="600" height="420" fill="{PAL["bone"]}"/>')
    # floor
    s.append(f'<path d="M0 900 L300 660 L900 660 L{W} 900 Z" fill="{PAL["pine_deep"]}" opacity="0.3"/>')
    for i in range(1, 6):
        t = i / 6
        s.append(f'<line x1="{300 * (1 - t)}" y1="{900 - 240 * (1 - t)}" '
                 f'x2="{W - 300 * (1 - t)}" y2="{900 - 240 * (1 - t)}" '
                 f'stroke="#ffffff" stroke-width="2" opacity="{0.28 - i * 0.04:.2f}"/>')
    # doors
    for x in (140, 960):
        s.append(f'<rect x="{x}" y="330" width="100" height="300" rx="6" fill="{PAL["pine"]}" opacity="0.4"/>')
    # end window
    s.append(f'<rect x="490" y="330" width="220" height="220" rx="6" fill="#cfe4ec" opacity="0.8"/>')
    s.append(f'<rect x="490" y="330" width="220" height="220" rx="6" fill="none" stroke="{PAL["pine_deep"]}" stroke-width="8" opacity="0.5"/>')
    s.append(f'<path d="M490 330 L710 330 L860 900 L340 900 Z" fill="#fff8e4" opacity="0.26"/>')
    for (cx, cy, r, op) in [(380, 760, 24, 0.6), (830, 790, 18, 0.5), (600, 200, 20, 0.55)]:
        s.append(sparkle(cx, cy, r, PAL["marigold"], op))
    s.append("</svg>")
    return "".join(s)


def logo_mark():
    """Monogram used in the header, footer and favicon."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img">'
        '<rect width="64" height="64" rx="16" fill="#1c4b3a"/>'
        '<path d="M32 12 C34 24 40 30 52 32 C40 34 34 40 32 52 C30 40 24 34 12 32 C24 30 30 24 32 12 Z" '
        'fill="#e3a02c"/>'
        '<circle cx="46" cy="18" r="3.4" fill="#f6f2ea"/>'
        '<circle cx="18" cy="46" r="2.4" fill="#f6f2ea" opacity="0.8"/>'
        "</svg>"
    )


def og_image():
    """1200x630 social share card."""
    w, h = 1200, 630
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">']
    s.append(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
             f'<stop offset="0" stop-color="{PAL["pine_deep"]}"/>'
             f'<stop offset="1" stop-color="{PAL["pine"]}"/></linearGradient></defs>')
    s.append(f'<rect width="{w}" height="{h}" fill="url(#bg)"/>')
    s.append(f'<circle cx="1050" cy="90" r="300" fill="{PAL["marigold"]}" opacity="0.16"/>')
    s.append(f'<circle cx="120" cy="590" r="240" fill="{PAL["sage_deep"]}" opacity="0.14"/>')
    s.append(sparkle(1040, 470, 60, PAL["marigold"], 0.9))
    s.append(sparkle(1140, 560, 28, PAL["marigold"], 0.6))
    s.append(f'<text x="80" y="230" font-family="Georgia,serif" font-size="88" font-weight="700" '
             f'fill="{PAL["bone"]}">Fast and Perfect</text>')
    s.append(f'<text x="80" y="310" font-family="Georgia,serif" font-size="52" font-style="italic" '
             f'fill="{PAL["marigold"]}">Cleaning Services</text>')
    s.append(f'<rect x="80" y="360" width="90" height="4" fill="{PAL["marigold"]}"/>')
    s.append(f'<text x="80" y="430" font-family="Helvetica,Arial,sans-serif" font-size="30" '
             f'fill="{PAL["sage_deep"]}">Residential · Commercial · Carpet</text>')
    s.append(f'<text x="80" y="480" font-family="Helvetica,Arial,sans-serif" font-size="30" '
             f'fill="{PAL["sage_deep"]}">Edmonton &amp; surrounding areas</text>')
    s.append(f'<text x="80" y="560" font-family="Helvetica,Arial,sans-serif" font-size="26" '
             f'font-weight="bold" fill="{PAL["bone"]}">Insured · Bonded · Satisfaction guaranteed</text>')
    s.append("</svg>")
    return "".join(s)


FILES = {
    "hero-living-room.svg": lambda: living_room(False),
    "before-living-room.svg": lambda: living_room(True),
    "after-living-room.svg": lambda: living_room(False),
    "service-residential.svg": lambda: living_room(False),
    "service-commercial.svg": office,
    "service-carpet.svg": lambda: carpet(False),
    "before-carpet.svg": lambda: carpet(True),
    "after-carpet.svg": lambda: carpet(False),
    "gallery-kitchen.svg": kitchen,
    "gallery-bathroom.svg": bathroom,
    "gallery-office.svg": office,
    "gallery-carpet.svg": lambda: carpet(False),
    "gallery-window.svg": window_clean,
    "gallery-hallway.svg": hallway,
    "gallery-living.svg": lambda: living_room(False),
    "about-crew.svg": crew,
    "logo-mark.svg": logo_mark,
    "og-cover.svg": og_image,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in FILES.items():
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fn())
        print(f"{name:32s} {os.path.getsize(path):>8,} bytes")


if __name__ == "__main__":
    main()
