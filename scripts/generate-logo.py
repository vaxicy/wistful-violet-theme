"""Wistful Violet Theme - logo generator.

Two modes:

    python3 scripts/generate-logo.py candidates                    # exploration sheet
    python3 scripts/generate-logo.py final [slug] [colorway]        # the shipped 128 icon

`candidates` draws every flat-vector concept in two colorways (deep plum card +
pale lilac card) at 8x supersampling, writes 512px previews plus a 1280x800
contact sheet into store-assets/icon-candidates/.

`final` renders the chosen concept on the chosen card and writes the single
128px icon a Chrome theme needs: logo/logo.png.

Every colour is read from manifest.json (theme.colors + theme.tints) so the mark
can never drift away from the theme it belongs to.
"""

import json
import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

SS = 8                      # supersample factor
SIZE = 128                  # Chrome themes only need one icon size: 128
S = SIZE * SS
CARD_RADIUS = 0.22          # corner radius as a fraction of the icon size

# the box every mark is drawn inside, as canvas fractions. Marks are centred on
# this box (not on their own bounding box) so all six concepts share the same
# visual size and can never creep up to the card edge.
MARK_BOX = (0.16, 0.16, 0.84, 0.84)
MIN_MARGIN = 0.10           # hard floor enforced on the finished mark

# relative paths only: Pillow's save() can throw OSError 22 on this machine when
# it has to encode a non-ASCII absolute path (the project folder is Chinese).
os.chdir(Path(__file__).resolve().parents[1])
OUT = Path("store-assets") / "icon-candidates"
MANIFEST = Path("manifest.json")


# --- palette (single source of truth: manifest.json) -------------------------
def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def hsl_to_rgb(h, s, l):
    """h in 0..1 (Chrome tint hue), s and l in 0..1."""
    c = (1 - abs(2 * l - 1)) * s
    hp = (h % 1.0) * 6.0
    x = c * (1 - abs(hp % 2 - 1))
    r, g, b = ((c, x, 0), (x, c, 0), (0, c, x),
               (0, x, c), (x, 0, c), (c, 0, x))[int(hp) % 6]
    m = l - c / 2
    return tuple(int(round(v * 255)) for v in (r + m, g + m, b + m))


def load_palette():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cols = {k: tuple(v) for k, v in data["theme"]["colors"].items()}
    tints = {k: tuple(v) for k, v in data["theme"]["tints"].items()}

    frame = cols["frame"]                 # deep violet  #24132E
    incog = cols["frame_incognito"]       # near-black violet (sheet background)
    pale = cols["toolbar_button_icon"]    # ghost lavender (mark on the dark card)
    tool = cols["toolbar"]                # muted violet-grey
    ghost = cols["tab_background_text"]   # hazy lavender
    ntp = cols["ntp_background"]          # pale canvas (pale lilac card)
    ink = cols["ntp_text"]                # deep ink
    snow = cols["tab_text"]               # near white
    hue = tints["buttons"][0]             # the theme's own violet hue (0.789)

    accent = hsl_to_rgb(hue, 0.46, 0.63)      # orchid violet, reads on the dark card
    accent_d = hsl_to_rgb(hue, 0.44, 0.42)    # deeper violet, reads on the pale card
    mark_d = mix(ink, frame, 0.45)            # deep violet mark for the pale card

    colorways = {
        "plum": {"card": frame, "mark": pale, "soft": mix(pale, frame, 0.58),
                 "accent": accent, "hilite": snow, "glow": mix(accent, snow, 0.42)},
        "lilac": {"card": ntp, "mark": mark_d, "soft": mix(mark_d, ntp, 0.62),
                  "accent": accent_d, "hilite": mix(mark_d, ntp, 0.34),
                  "glow": accent_d},
    }
    ui = {"sheet": incog, "tile": mix(frame, ghost, 0.55), "head": snow,
          "sub": mix(ghost, snow, 0.22), "rule": mix(tool, ghost, 0.35)}
    return colorways, ui


# --- mask helpers ------------------------------------------------------------
def _blank():
    return Image.new("L", (S, S), 0)


def m_circle(cx, cy, r):
    m = _blank()
    ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    return m


def m_capsule(p0, p1, width):
    """Straight line with rounded ends (no sharp corners)."""
    m = _blank()
    d = ImageDraw.Draw(m)
    d.line([p0, p1], fill=255, width=int(round(width)))
    r = width / 2
    for x, y in (p0, p1):
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    return m


def m_ellipse(cx, cy, rx, ry, angle=0.0):
    m = _blank()
    ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    if angle:
        m = m.rotate(angle, resample=Image.BICUBIC, center=(cx, cy))
    return m


def m_lens(cx, cy, hw, hh, angle=0.0):
    """Pointed oval (long axis vertical) = intersection of two circles."""
    d = (hh * hh - hw * hw) / (2 * hw)
    r = hw + d
    m = ImageChops.darker(m_circle(cx - d, cy, r), m_circle(cx + d, cy, r))
    if angle:
        m = m.rotate(angle, resample=Image.BICUBIC, center=(cx, cy))
    return m


def m_ring(cx, cy, r, w):
    return ImageChops.difference(m_circle(cx, cy, r + w / 2), m_circle(cx, cy, r - w / 2))


def m_poly(pts):
    m = _blank()
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def m_rect(x0, y0, x1, y1):
    m = _blank()
    ImageDraw.Draw(m).rectangle([x0, y0, x1, y1], fill=255)
    return m


def m_star4(cx, cy, r, waist):
    """Four-point sparkle = union of a vertical and a horizontal lens."""
    v = m_lens(cx, cy, waist, r)
    return ImageChops.lighter(v, v.rotate(90, resample=Image.BICUBIC, center=(cx, cy)))


def m_below_wave(y0, amp, x0, x1, y_bottom, phase=0.0, n=200):
    """Everything under a sine edge: a soft rolling ridge silhouette."""
    pts = [(x0 + (x1 - x0) * i / n,
            y0 + amp * math.sin(phase + (i / n) * math.pi * 1.6)) for i in range(n + 1)]
    pts += [(x1, y_bottom), (x0, y_bottom)]
    m = _blank()
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def m_curve(fn, w_fn, n=260):
    """Stroke a parametric path with a varying width (round dabs)."""
    m = _blank()
    d = ImageDraw.Draw(m)
    for i in range(n + 1):
        t = i / n
        x, y = fn(t)
        r = max(w_fn(t) / 2, 1.0)
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    return m


def union(*masks):
    out = masks[0]
    for m in masks[1:]:
        out = ImageChops.lighter(out, m)
    return out


def intersect(*masks):
    out = masks[0]
    for m in masks[1:]:
        out = ImageChops.darker(out, m)
    return out


def paint(layer, mask, rgb):
    layer.paste(Image.new("RGBA", (S, S), rgb + (255,)), (0, 0), mask)


def paint_glow(layer, cx, cy, r, cw, steps=3):
    """A firefly: a bright core wrapped in rings that fade into the card."""
    for k in range(steps, 0, -1):
        paint(layer, m_circle(cx, cy, r * (1.0 + 0.30 * k)),
              mix(cw["glow"], cw["card"], 0.30 * k - 0.04))
    paint(layer, m_circle(cx, cy, r), cw["glow"])


# --- concepts ----------------------------------------------------------------
def c_moon(cw):
    """Crescent dusk: a waxing crescent in a thin halo, two sparkles in the hollow."""
    L = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cx, cy = 0.500 * S, 0.500 * S
    paint(L, m_ring(cx, cy, 0.335 * S, 0.018 * S), cw["accent"])
    disc = m_circle(cx - 0.030 * S, cy, 0.245 * S)
    bite = m_circle(cx + 0.085 * S, cy, 0.235 * S)
    paint(L, ImageChops.subtract(disc, bite), cw["mark"])
    paint(L, m_star4(cx + 0.176 * S, cy - 0.106 * S, 0.076 * S, 0.015 * S), cw["hilite"])
    paint(L, m_star4(cx + 0.196 * S, cy + 0.116 * S, 0.044 * S, 0.010 * S), cw["accent"])
    return L


def c_lavender(cw):
    """Lavender sprig: a gently bowing stem, paired buds, one leaf."""
    L = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    def stem_x(t):
        return 0.470 * S + 0.060 * S * math.sin(math.pi * (0.12 + 0.88 * t))

    def stem_y(t):
        return 0.845 * S - t * 0.620 * S

    def stem_w(t):
        return (0.028 * (1.0 - t) + 0.010) * S

    paint(L, m_curve(lambda t: (stem_x(t), stem_y(t)), stem_w), cw["mark"])

    rows = 10
    for i in range(rows):
        y = 0.690 - i * 0.0485
        t = (0.845 - y) / 0.620
        sc = 1.0 - 0.34 * i / (rows - 1)
        off = (0.048 + stem_w(t) / (2 * S)) * sc
        for sgn, ang in ((1, -32), (-1, 32)):
            paint(L, m_lens((stem_x(t) + sgn * off * S), y * S,
                            0.024 * sc * S, 0.041 * sc * S, ang), cw["accent"])

    paint(L, m_ellipse(stem_x(1.0), 0.218 * S, 0.021 * S, 0.030 * S), cw["accent"])
    paint(L, m_lens(0.575 * S, 0.780 * S, 0.024 * S, 0.078 * S, -38), cw["mark"])
    return L


def c_horizon(cw):
    """Distant summer evening: a low sun on the waterline, its light trailing away."""
    L = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    horizon = 0.520 * S
    paint(L, intersect(m_circle(0.500 * S, horizon, 0.190 * S),
                       m_rect(0, 0, S, horizon)), cw["accent"])
    paint(L, m_capsule((0.156 * S, horizon), (0.844 * S, horizon), 0.019 * S),
          cw["mark"])
    for y, hw, w, fade in ((0.604, 0.118, 0.030, 0.10),
                           (0.662, 0.074, 0.026, 0.32),
                           (0.712, 0.044, 0.022, 0.54)):
        paint(L, m_capsule(((0.5 - hw) * S, y * S), ((0.5 + hw) * S, y * S), w * S),
              mix(cw["accent"], cw["card"], fade))
    paint(L, m_star4(0.762 * S, 0.258 * S, 0.052 * S, 0.011 * S), cw["hilite"])
    paint(L, m_star4(0.245 * S, 0.300 * S, 0.042 * S, 0.009 * S), cw["accent"])
    return L


def c_plane(cw):
    """Paper plane and its fading trail: a postcard from a distant summer."""
    L = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    nose = (0.846 * S, 0.336 * S)
    tail_up = (0.312 * S, 0.256 * S)
    fold = (0.560 * S, 0.466 * S)
    tail_dn = (0.376 * S, 0.666 * S)
    paint(L, m_poly([nose, tail_up, fold]), cw["mark"])
    paint(L, m_poly([nose, fold, tail_dn]), cw["soft"])

    dots = [(0.278, 0.596, 0.030), (0.222, 0.652, 0.023),
            (0.176, 0.702, 0.017), (0.140, 0.744, 0.012)]
    for i, (x, y, r) in enumerate(dots):
        paint(L, m_circle(x * S, y * S, r * S), mix(cw["mark"], cw["card"],
                                                    0.34 + 0.17 * i))
    return L


def c_firefly(cw):
    """Fireflies drifting at dusk: three glows with short tapered tails."""
    L = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    orbs = [(0.400, 0.648, 0.082, -0.14), (0.648, 0.402, 0.056, -0.10),
            (0.286, 0.312, 0.040, 0.06)]

    for x, y, r, tilt in orbs:
        tail = m_curve(
            lambda t, x=x, y=y, r=r, tilt=tilt: (
                (x - 0.145 * t) * S,
                (y + (0.09 + tilt) * t + 0.05 * t * t) * S),
            lambda t, r=r: r * 0.62 * S * (1 - t) ** 0.75, n=140)
        paint(L, tail, mix(cw["glow"], cw["card"], 0.62))

    for x, y, r, _tilt in orbs:
        paint_glow(L, x * S, y * S, r * S, cw)

    paint(L, m_star4(0.762 * S, 0.268 * S, 0.046 * S, 0.010 * S), cw["accent"])
    paint(L, m_star4(0.196 * S, 0.756 * S, 0.034 * S, 0.008 * S), cw["accent"])
    return L


def c_dandelion(cw):
    """Dandelion clock: seeds lifting away on an evening breeze."""
    L = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cx, cy, rad = 0.440 * S, 0.560 * S, 0.290 * S

    tips = []
    for i in range(16):
        a = math.radians(i * 22.5)
        tx, ty = cx + rad * math.cos(a), cy + rad * math.sin(a)
        tips.append((tx, ty))
        paint(L, m_capsule((cx, cy), (tx, ty), 0.011 * S), cw["mark"])
    paint(L, union(*[m_circle(x, y, 0.020 * S) for x, y in tips]), cw["hilite"])
    paint(L, m_circle(cx, cy, 0.036 * S), cw["accent"])

    for x, y, sc in ((0.782, 0.286, 1.00), (0.706, 0.192, 0.82), (0.826, 0.446, 0.70)):
        paint(L, m_circle(x * S, y * S, 0.019 * sc * S), cw["accent"])
        for k in range(3):
            a = math.radians(-118 + 34 * k)
            paint(L, m_capsule((x * S, y * S),
                               (x * S + 0.075 * sc * S * math.cos(a),
                                y * S + 0.075 * sc * S * math.sin(a)), 0.009 * S),
                  cw["hilite"])
    return L


CONCEPTS = [
    ("01", "moon", "Crescent dusk", "月晕", c_moon),
    ("02", "lavender", "Lavender sprig", "薰衣草", c_lavender),
    ("03", "horizon", "Sinking sun", "落日山脊", c_horizon),
    ("04", "plane", "Paper plane", "纸飞机", c_plane),
    ("05", "firefly", "Fireflies", "萤火", c_firefly),
    ("06", "dandelion", "Dandelion clock", "蒲公英", c_dandelion),
]

NOTES = {
    "moon": "waxing crescent, thin halo, two sparkles",
    "lavender": "bowing stem, paired buds, single leaf",
    "horizon": "low sun on the waterline, light trailing away",
    "plane": "folded dart with a fading dotted trail",
    "firefly": "three glows with tapered tails",
    "dandelion": "seed clock with three seeds drifting off",
}

CHOSEN = "moon"              # recommended: the most wistful of the six
CHOSEN_CW = "plum"           # deep plum card, matching the dark browser frame


# --- composition -------------------------------------------------------------
def card(card_rgb):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    plate = _blank()
    ImageDraw.Draw(plate).rounded_rectangle([0, 0, S - 1, S - 1],
                                            radius=CARD_RADIUS * S, fill=255)
    img.paste(Image.new("RGBA", (S, S), card_rgb + (255,)), (0, 0), plate)
    return img


def compose(concept, cw):
    """Draw the mark centred on the shared MARK_BOX inside the rounded card."""
    layer = concept(cw)
    assert layer.split()[3].getbbox() is not None, "nothing drawn"
    cx = 0.5 * (MARK_BOX[0] + MARK_BOX[2]) * S
    cy = 0.5 * (MARK_BOX[1] + MARK_BOX[3]) * S
    centered = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    centered.alpha_composite(layer, (int(round(0.5 * S - cx)), int(round(0.5 * S - cy))))

    b = centered.split()[3].getbbox()
    margin = MIN_MARGIN * S
    assert b[0] >= margin and b[1] >= margin, f"mark too close to card edge: {b}"
    assert b[2] <= S - margin and b[3] <= S - margin, f"mark too close to card edge: {b}"

    out = card(cw["card"])
    out.alpha_composite(centered)
    return out


def outlined(img_rgba, color, radius_frac, width=2, alpha=80):
    """Hairline outline so a card never blends into the contact-sheet plate."""
    img = img_rgba.copy()
    ImageDraw.Draw(img).rounded_rectangle(
        [0, 0, img.width - 1, img.height - 1], radius=radius_frac * img.width,
        outline=color + (alpha,), width=width)
    return img


def load_font(size, bold=False):
    names = (("msyhbd.ttc", "segoeuib.ttf", "arialbd.ttf") if bold
             else ("msyh.ttc", "segoeui.ttf", "arial.ttf"))
    for name in names:
        p = Path("C:/Windows/Fonts") / name
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                continue
    return ImageFont.load_default()


def contact_sheet(rows, ui):
    """3 x 2 sheet; every tile shows the deep plum card next to the pale lilac card."""
    W, H = 1280, 800
    MARGIN, GAP, HEADER = 60, 40, 110
    TILE_W = (W - 2 * MARGIN - 2 * GAP) // 3          # 360
    TILE_H = (H - HEADER - GAP - MARGIN) // 2         # 295
    PREV, PREV_GAP, PAD = 148, 12, 26
    assert PAD + PREV * 2 + PREV_GAP + PAD == TILE_W
    assert 2 * PAD + PREV * 2 + PREV_GAP <= TILE_W

    sheet = Image.new("RGB", (W, H), ui["sheet"])
    d = ImageDraw.Draw(sheet)
    f_head = load_font(30, bold=True)
    f_sub = load_font(15)
    f_num = load_font(22, bold=True)
    f_name = load_font(22, bold=True)
    f_note = load_font(13)
    f_cap = load_font(14)

    d.text((MARGIN, 34), "Wistful Violet - Logo Candidates", font=f_head, fill=ui["head"])
    d.text((MARGIN, 74), "left: deep plum card   /   right: pale lilac card",
           font=f_sub, fill=ui["sub"])

    for i, (num, slug, en, cn, plum, lilac) in enumerate(rows):
        col, row = i % 3, i // 3
        x = MARGIN + col * (TILE_W + GAP)
        y = HEADER + row * (TILE_H + GAP)
        assert x + TILE_W <= W - MARGIN, "tile overflows the sheet"
        assert y + TILE_H <= H - 12, "tile overflows the sheet"

        d.rounded_rectangle([x, y, x + TILE_W, y + TILE_H], radius=22,
                            fill=ui["tile"], outline=ui["rule"], width=2)
        d.text((x + PAD, y + 20), num, font=f_num, fill=ui["head"])
        d.text((x + PAD + 42, y + 20), f"{en}   {cn}", font=f_name, fill=ui["head"])
        d.text((x + PAD, y + 52), NOTES[slug], font=f_note, fill=ui["sub"])

        px, py = x + PAD, y + 86
        for j, img in enumerate((plum, lilac)):
            tile = outlined(img.resize((PREV, PREV), Image.LANCZOS),
                            ui["head"], CARD_RADIUS)
            sheet.paste(tile, (px + j * (PREV + PREV_GAP), py), tile)
        d.text((px, py + PREV + 6), "deep plum", font=f_cap, fill=ui["sub"])
        d.text((px + PREV + PREV_GAP, py + PREV + 6), "pale lilac", font=f_cap,
               fill=ui["sub"])

    dest = OUT / "contact-sheet.png"
    sheet.save(dest)
    print(f"wrote {dest}")


def write_candidates():
    colorways, ui = load_palette()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for num, slug, en, cn, concept in CONCEPTS:
        imgs = {}
        for name in ("plum", "lilac"):
            img = compose(concept, colorways[name]).resize((512, 512), Image.LANCZOS)
            img.save(OUT / f"candidate-{num}-{slug}-{name}.png")
            imgs[name] = img
        print(f"wrote candidate-{num}-{slug} (deep plum + pale lilac)")
        rows.append((num, slug, en, cn, imgs["plum"], imgs["lilac"]))
    contact_sheet(rows, ui)


def write_final(slug=CHOSEN, colorway=CHOSEN_CW):
    colorways, _ui = load_palette()
    if colorway not in colorways:
        raise SystemExit(f"unknown colorway '{colorway}' - use plum | lilac")
    concept = next((c for _n, s, _e, _cn, c in CONCEPTS if s == slug), None)
    if concept is None:
        raise SystemExit("unknown concept '" + slug + "' - use one of: "
                         + ", ".join(s for _n, s, _e, _cn, _c in CONCEPTS))

    dest = Path("logo")
    dest.mkdir(parents=True, exist_ok=True)
    icon = compose(concept, colorways[colorway]).resize((SIZE, SIZE), Image.LANCZOS)
    icon.save(dest / "logo.png")
    assert icon.size == (SIZE, SIZE)
    print(f"wrote logo/logo.png ({SIZE}x{SIZE}) - concept '{slug}', {colorway} card")
    print('manifest icons field: "icons": { "128": "logo/logo.png" }')


def main():
    args = sys.argv[1:]
    mode = args[0] if args else "candidates"
    if mode == "candidates":
        write_candidates()
    elif mode == "final":
        write_final(*(args[1:3] or [CHOSEN, CHOSEN_CW]))
    else:
        raise SystemExit(f"unknown mode '{mode}' - use 'candidates' or 'final'")


if __name__ == "__main__":
    main()
