# Asset notes

## What the assets are

- `screenshots/en/screenshot-1-browser.png` (1280x800) - the browser mockup, one tab
- `screenshots/en/screenshot-2-introduction.png` (1280x800) - theme introduction with the palette sheet
- `promo/440x280.png` and `promo/1400x560.png`

All four are rendered by `scripts/generate-store-assets.py` with headless Chromium from one HTML/CSS source. They are illustrative layouts built from the real `manifest.json` colours, not native screenshots of a running Chrome window. `references/` keeps the intermediate HTML and PNG of the same run.

The palette sheet sits on `tab_text`, a theme tone that none of the four swatches uses, so no card can blend into the page behind it. Card text picks whichever of the theme's two text tones has the higher contrast, and the script asserts it stays at or above 4.5:1.

## Colors

Theme-controlled surfaces (frame, active tab, toolbar, bookmark bar, address bar, new tab page, text) are read from `manifest.json` at render time.

The violet accent used by the promo tiles and the icon is not written by hand: it is the theme's own button tint (`theme.tints.buttons[0]`, hue 0.789) lifted to a readable saturation, so it can never drift away from the manifest.

Browser-owned elements are literals, because Chrome decides them. Values were sampled from a real Chrome window with this theme installed:

| Element | Value | Note |
|---|---|---|
| Google mark on the new tab page | `#A696AE` | `ntp_logo_alternate` makes Chrome paint the mark as one flat tone; sampled from a real install |
| New tab search field | `#FFFFFF`, edge `#E4E1E7` | Rendered by the page, not the theme |
| Search placeholder + its glyphs | `#66676C` | Sampled from a real install |
| "Images" link, top right | `#444746` | Sampled from a real install |
| New tab shortcut circles | `#BDB1C3` | Chrome tints the round shortcuts from the theme; sampled |
| Shortcut labels | `#5F6368` | Sampled from a real install |
| `Customize Chrome` pill | `#202124` / `#E8EAED` | Rendered by the page, not the theme |
| Window-button strip, top right | `#423448` | Painted by Chrome/Windows above the theme frame |
| Omnibox placeholder | `omnibox_text` mixed 45% into `omnibox_background` | Chrome dims the placeholder from the omnibox text tone |

## Regenerating

    python3 scripts/generate-logo.py                 # logo/logo.png (128, sun on the waterline)
    python3 scripts/generate-logo.py candidates      # exploration sheet of six concepts
    python3 scripts/generate-store-assets.py         # screenshot + promo tiles

The composer renders all three assets in one pass; change the styling in the script and re-run instead of editing a PNG.
