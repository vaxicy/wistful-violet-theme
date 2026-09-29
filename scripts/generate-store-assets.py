"""Render the Chrome Web Store artwork for Wistful Violet Theme.

    python3 scripts/generate-store-assets.py

Produces, from one HTML/CSS composer (headless Chromium, scale factor 1):

    store-assets/screenshots/en/screenshot-1-browser.png   1280x800
    store-assets/promo/440x280.png                         440x280
    store-assets/promo/1400x560.png                        1400x560

The browser mockup shows a single tab, the toolbar, the bookmark bar and the new
tab page, layer by layer like real Chrome. Theme surfaces come from
manifest.json; colours of browser-owned UI (Google mark, search field, shortcut
circles, Customize pill, window-button strip) are literals sampled from a real
install - see store-assets/ASSET-NOTES.md.
"""

import base64
import json
import os
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

# relative paths only: this project lives under a non-ASCII folder and Pillow can
# throw OSError 22 when it has to encode such a path while saving.
os.chdir(Path(__file__).resolve().parents[1])
REF = Path("store-assets") / "references"
REF.mkdir(parents=True, exist_ok=True)

M = json.loads(Path("manifest.json").read_text(encoding="utf-8"))
C = M["theme"]["colors"]
T = M["theme"]["tints"]


def color(key):
    return "#%02X%02X%02X" % tuple(C[key])


def hsl_to_rgb(h, s, l):
    """h in 0..1 (Chrome tint hue), s and l in 0..1."""
    c = (1 - abs(2 * l - 1)) * s
    hp = (h % 1.0) * 6.0
    x = c * (1 - abs(hp % 2 - 1))
    r, g, b = ((c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x))[int(hp) % 6]
    m = l - c / 2
    return "#%02X%02X%02X" % tuple(int(round(v * 255)) for v in (r + m, g + m, b + m))


# The theme's own violet, taken from its button tint - never hardcoded.
ACCENT = hsl_to_rgb(T["buttons"][0], 0.46, 0.63)      # #B273CA, reads on the dark frame
ACCENT_DEEP = hsl_to_rgb(T["buttons"][0], 0.44, 0.42)  # deeper violet, reads on light

# Browser-owned tones, sampled from a real Chrome install of this theme:
GOOGLE_MARK = "#A696AE"      # ntp_logo_alternate tint Chrome paints on this NTP
SEARCH_BG = "#FFFFFF"
SEARCH_EDGE = "#E4E1E7"
SEARCH_TEXT = "#66676C"      # new-tab search placeholder + its glyphs


def mix_key(key, key2, t):
    a, b = C[key], C[key2]
    return "#%02X%02X%02X" % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# Chrome dims the omnibox placeholder from the omnibox text tone.
OMNI_PLACEHOLDER = mix_key("omnibox_text", "omnibox_background", 0.45)
NTP_LINK = "#444746"         # "Images" link, top right of the new tab page
SHORTCUT_BG = "#BDB1C3"      # round new-tab shortcut circles
SHORTCUT_TEXT = "#5F6368"
CUSTOMIZE_BG = "#202124"     # "Customize Chrome" pill
CUSTOMIZE_TEXT = "#E8EAED"
CAPTION_BAR = "#423448"      # window-button strip Chrome/Windows paints top right
PLAY_BADGE = "#FF0033"

css = f"""
:root{{
  --frame:{color('frame')};--toolbar:{color('toolbar')};--ob:{color('omnibox_background')};
  --obt:{color('omnibox_text')};--tt:{color('tab_text')};--tbt:{color('tab_background_text')};
  --tbi:{color('toolbar_button_icon')};--bm:{color('bookmark_text')};
  --ntp:{color('ntp_background')};--nt:{color('ntp_text')};--accent:{ACCENT};
  --accent-deep:{ACCENT_DEEP};--edge:{color('button_background')};
}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:Arial,Helvetica,sans-serif;background:#fff}}

/* ---- browser mockup, one tab, layer by layer like real Chrome ---- */
.browser{{width:1280px;height:800px;background:var(--ntp);position:relative;overflow:hidden}}
.tabs{{height:40px;background:var(--frame);display:flex;align-items:flex-end;padding:0 10px;
      gap:8px;position:relative;color:var(--tbt)}}
.tab{{height:34px;padding:0 14px;font-size:13px;border-radius:12px 12px 0 0;
     display:flex;align-items:center;gap:9px;white-space:nowrap}}
.tab.active{{background:var(--toolbar);color:var(--tt);width:250px}}
.fav{{width:14px;height:14px;border-radius:50%;background:var(--accent);flex:0 0 auto}}
.tab .x{{margin-left:auto;opacity:.85;line-height:0}}
.newtab{{padding:0 6px 9px;line-height:0}}
.caption{{position:absolute;right:0;top:0;height:40px;width:104px;background:{CAPTION_BAR};
         display:flex;align-items:center;justify-content:space-around}}
.tools{{height:48px;background:var(--toolbar);display:flex;align-items:center;gap:14px;
       padding:0 14px;color:var(--tbi)}}
.tools .ico{{line-height:0;display:flex;align-items:center}}
.omni{{flex:1;height:34px;border-radius:20px;background:var(--ob);color:var(--obt);
      display:flex;align-items:center;gap:12px;padding:0 16px;font-size:13px}}
.omni .ph{{color:{OMNI_PLACEHOLDER}}}
.omni .tail{{margin-left:auto;display:flex;gap:12px;align-items:center}}
.bookmarks{{height:30px;background:var(--toolbar);color:var(--bm);font-size:12px;
           display:flex;gap:26px;padding:7px 22px;white-space:nowrap;overflow:hidden}}

/* ---- new tab page ---- */
.ntp{{position:relative;height:682px;background:var(--ntp);text-align:center;color:var(--nt)}}
.images{{position:absolute;right:26px;top:16px;font-size:13px;color:{NTP_LINK};
        display:flex;align-items:center;gap:8px}}
.google{{font-size:76px;line-height:1;letter-spacing:-3px;font-weight:500;padding-top:78px;
        color:{GOOGLE_MARK}}}
.search{{width:640px;height:50px;border-radius:26px;background:{SEARCH_BG};
        border:1px solid {SEARCH_EDGE};box-shadow:0 1px 5px rgba(0,0,0,.10);
        margin:34px auto 0;display:flex;align-items:center;gap:14px;padding:0 18px;
        color:{SEARCH_TEXT};font-size:15px}}
.search .tail{{margin-left:auto;display:flex;gap:14px;align-items:center}}
.shortcuts{{display:flex;justify-content:center;gap:44px;margin-top:34px}}
.shortcut{{width:104px;font-size:12px;color:{SHORTCUT_TEXT}}}
.shortcut .circle{{width:48px;height:48px;border-radius:50%;background:{SHORTCUT_BG};
                  margin:0 auto 10px;display:flex;align-items:center;justify-content:center;
                  line-height:0}}
.customize{{position:absolute;right:24px;bottom:16px;background:{CUSTOMIZE_BG};
           color:{CUSTOMIZE_TEXT};font-size:12px;border-radius:16px;padding:8px 14px;
           display:flex;align-items:center;gap:7px}}

/* ---- promo tiles ---- */
.small{{width:440px;height:280px;background:var(--frame);text-align:center;padding-top:20px;
       position:relative;overflow:hidden}}
.small .tile{{width:92px;height:92px;margin:0 auto;background:#fff;border-radius:22px;
             display:flex;align-items:center;justify-content:center}}
.small .tile img{{width:78px;height:78px;display:block;border-radius:16px}}
.small h1{{font:40px Georgia,serif;font-weight:normal;margin:12px 0 0;color:var(--tt)}}
.small .sub{{font-size:13px;letter-spacing:5px;margin-top:8px;color:var(--accent)}}
.small p{{font-size:12px;margin:12px 0 0;color:var(--tbt)}}
.small .bar{{position:absolute;left:0;right:0;bottom:0;height:14px;background:var(--accent)}}

.poster{{width:1400px;height:560px;background:var(--toolbar);position:relative;overflow:hidden;
        text-align:center;border-top:8px solid var(--accent)}}
.poster h1{{font:48px Georgia,serif;font-weight:normal;margin:22px 0 0;color:var(--tt)}}
.poster p{{font-size:17px;margin:8px 0 0;color:var(--accent)}}
.poster .preview{{position:absolute;left:286px;top:150px;transform:scale(.65);
                 transform-origin:top left;border:2px solid var(--accent);border-radius:16px;
                 overflow:hidden;text-align:left}}
"""


def svg(path, size, stroke=None, fill="none", width=2.2):
    p = f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">{path}</svg>'
    return p


def icon_back():
    return svg('<path d="M15 5l-7 7 7 7"/>', 18, stroke="var(--tbi)")


def icon_forward():
    return svg('<path d="M9 5l7 7-7 7"/>', 18, stroke="var(--tbi)")


def icon_reload():
    return svg('<path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v4h-4"/>', 17,
               stroke="var(--tbi)")


def icon_close():
    return svg('<path d="M6 6l12 12M18 6L6 18"/>', 12, stroke="var(--tt)")


def icon_plus(tone, size=16):
    return svg('<path d="M12 5v14M5 12h14"/>', size, stroke=tone)


def icon_search(size=18, tone=SEARCH_TEXT):
    return svg('<circle cx="11" cy="11" r="6.5"/><path d="M16 16l5 5"/>', size, stroke=tone)


def icon_star(tone="var(--tbi)"):
    return svg('<path d="M12 4l2.4 5.2 5.6.6-4.2 3.8 1.2 5.6L12 16.4 7 19.2l1.2-5.6L4 9.8l5.6-.6z"/>',
               17, stroke=tone, width=1.8)


def icon_mic(tone=SEARCH_TEXT):
    return svg('<rect x="9" y="4" width="6" height="10" rx="3"/><path d="M6 11a6 6 0 0 0 12 0"/>'
               '<path d="M12 17v3"/>', 16, stroke=tone)


def icon_lens():
    return svg('<circle cx="11" cy="11" r="6"/><path d="M16 16l5 5"/>', 16, stroke="#4285F4")
    # the Lens glyph keeps its own blue, like Chrome paints it


def icon_kebab():
    return ('<svg width="16" height="16" viewBox="0 0 24 24" fill="var(--tbi)">'
            '<circle cx="12" cy="5" r="1.8"/><circle cx="12" cy="12" r="1.8"/>'
            '<circle cx="12" cy="19" r="1.8"/></svg>')


def icon_puzzle():
    return svg('<path d="M10 4h4v3h3v4h-3v3h-4v-3H7V7h3z"/>', 17, stroke="var(--tbi)", width=1.7)


def icon_avatar():
    return ('<svg width="20" height="20" viewBox="0 0 24 24">'
            f'<circle cx="12" cy="12" r="10" fill="{ACCENT}"/>'
            '<circle cx="12" cy="10" r="3.4" fill="#F8F6F9"/>'
            '<path d="M5.4 20a7.4 7.4 0 0 1 13.2 0z" fill="#F8F6F9"/></svg>')


def icon_images():
    return svg('<path d="M4 5h16v14H4z"/><path d="M4 15l4-4 4 4 3-3 5 5"/>', 14,
               stroke=NTP_LINK, width=1.6)


def icon_pen():
    return svg('<path d="M4 20l4-1 10-10-3-3L5 16z"/>', 13, stroke=CUSTOMIZE_TEXT, width=1.8)


def icon_play_badge():
    return ('<svg width="26" height="18" viewBox="0 0 26 18">'
            f'<rect width="26" height="18" rx="5" fill="{PLAY_BADGE}"/>'
            '<path d="M10.5 5.2l7 3.8-7 3.8z" fill="#fff"/></svg>')


def icon_globe():
    return svg('<circle cx="12" cy="12" r="8"/><path d="M4 12h16"/>'
               '<path d="M12 4c2.6 3.2 2.6 12.8 0 16M12 4c-2.6 3.2-2.6 12.8 0 16"/>', 19,
               stroke="#3F6EDB", width=1.9)


def browser():
    bookmarks = "".join(f"<span>{n}</span>" for n in
                        ("Bookmarks", "Reading", "Design", "Inspiration", "Snippets", "Dev"))
    shortcuts = (
        f'<div class="shortcut"><div class="circle">{icon_play_badge()}</div>YouTube</div>'
        f'<div class="shortcut"><div class="circle">{icon_globe()}</div>Web Store</div>'
        f'<div class="shortcut"><div class="circle">{icon_plus("var(--tbi)")}</div>'
        'Add shortcut</div>')
    return (
        '<div class="browser">'
        '<div class="tabs">'
        '<div class="tab active"><span class="fav"></span>New Tab'
        f'<span class="x">{icon_close()}</span></div>'
        f'<span class="newtab">{icon_plus("var(--tbt)", 15)}</span>'
        f'<div class="caption">{icon_min()} {icon_max()} {icon_close_big()}</div>'
        '</div>'
        '<div class="tools">'
        f'<span class="ico">{icon_back()}</span><span class="ico">{icon_forward()}</span>'
        f'<span class="ico">{icon_reload()}</span>'
        '<div class="omni">' + icon_search() +
        '<span class="ph">Search Google or type a URL</span></div>'
        f'<span class="ico">{icon_star()}</span><span class="ico">{icon_puzzle()}</span>'
        f'<span class="ico">{icon_avatar()}</span><span class="ico">{icon_kebab()}</span>'
        '</div>'
        f'<div class="bookmarks">{bookmarks}</div>'
        '<div class="ntp">'
        f'<div class="images">Images {icon_images()}</div>'
        '<div class="google">Google</div>'
        '<div class="search">' + icon_search() + '<span>Search Google or type a URL</span>'
        f'<span class="tail">{icon_mic()}{icon_lens()}</span></div>'
        f'<div class="shortcuts">{shortcuts}</div>'
        f'<div class="customize">{icon_pen()}Customize Chrome</div>'
        '</div></div>')


def icon_min():
    return svg('<path d="M5 12h14"/>', 14, stroke="var(--tt)", width=1.6)


def icon_max():
    return svg('<rect x="6" y="6" width="12" height="12" rx="2"/>', 13, stroke="var(--tt)", width=1.6)


def icon_close_big():
    return svg('<path d="M6 6l12 12M18 6L6 18"/>', 14, stroke="var(--tt)", width=1.6)


LOGO_URI = "data:image/png;base64," + base64.b64encode(Path("logo/logo.png").read_bytes()).decode()

SMALL = (
    '<div class="small">'
    f'<div class="tile"><img src="{LOGO_URI}" alt=""></div>'
    '<h1>Wistful Violet</h1><div class="sub">CHROME THEME</div>'
    '<p>Nostalgic violet, like a far-off summer evening.</p>'
    '<div class="bar"></div></div>')

WIDE = (
    '<div class="poster"><h1>Wistful Violet Theme</h1>'
    '<p>Nostalgic violet tones for distant summer evenings.</p>'
    f'<div class="preview">{browser()}</div></div>')


def page(body):
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<style>{css}</style></head><body>{body}</body></html>')


JOBS = [
    ("screenshot-1-browser", 1280, 800, browser(), "store-assets/screenshots/en"),
    ("promo-440x280", 440, 280, SMALL, "store-assets/promo"),
    ("promo-1400x560", 1400, 560, WIDE, "store-assets/promo"),
]
TARGETS = {
    "screenshot-1-browser": "screenshot-1-browser.png",
    "promo-440x280": "440x280.png",
    "promo-1400x560": "1400x560.png",
}


def main():
    with sync_playwright() as p:
        engine = p.chromium.launch(headless=True)
        tab = engine.new_page(device_scale_factor=1)
        for name, w, h, body, out_dir in JOBS:
            html = page(body)
            (REF / f"{name}.html").write_text(html, "utf-8")
            tab.set_viewport_size({"width": w, "height": h})
            tab.set_content(html)
            shot = REF / f"{name}.png"
            tab.screenshot(path=str(shot))
            out = Path(out_dir)
            out.mkdir(parents=True, exist_ok=True)
            target = out / TARGETS[name]
            with Image.open(shot) as img:
                assert img.size == (w, h), f"{name}: {img.size} != {(w, h)}"
                assert img.mode in ("RGB", "RGBA"), img.mode
                temp = target.with_suffix(".new.png")
                img.convert("RGB").save(temp)
            temp.replace(target)
            print(f"wrote {target} {w}x{h}")
        engine.close()


if __name__ == "__main__":
    sys.exit(main())
