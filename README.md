<div align="center">
  <img src="https://raw.githubusercontent.com/vaxicy/wistful-violet-theme/main/logo/logo.png" alt="Wistful Violet Theme icon" width="88">
  <h1>Wistful Violet Theme</h1>
  <p>A deep violet Chrome theme with a soft lavender canvas and a quiet orchid accent.</p>
  <p>
    <img src="https://img.shields.io/badge/version-1.0.0-B273CA" alt="Version 1.0.0">
    <img src="https://img.shields.io/badge/license-Non--Commercial-lightgrey" alt="Non-Commercial License">
    <img src="https://img.shields.io/badge/Chrome%20Web%20Store-theme-B273CA?logo=googlechrome" alt="Chrome Web Store">
  </p>
</div>

---

## About

Wistful Violet Theme gives the browser the mood of a distant summer evening. A deep violet frame carries the window and tab strip, a lighter violet toolbar and bookmark bar sit just below it, and the new tab page opens on a soft lavender canvas with a dusky mauve wordmark.

Every layer is painted as one flat solid colour, so the window stays calm and uncluttered, and the text tones are tuned so tab titles, toolbar icons, bookmark labels and the address bar stay readable against the dark surfaces.

## Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| Deep Violet | `#24132E` | Window frame, tab strip, window buttons |
| Twilight Violet | `#4A3C4F` | Toolbar, bookmark bar, active tab |
| Midnight Violet | `#1D1127` | Inactive tab surfaces, incognito frame |
| Dusk Ink | `#3C3543` | Address bar background, new tab text |
| Soft Lavender | `#E1DBE5` | Toolbar icons |
| Haze Mauve | `#AFA1B8` | Bookmark labels, inactive tab text |
| Lavender Canvas | `#E9E5EB` | New tab background |

## Chrome UI Notes

Some parts of the browser are painted by Chrome itself rather than by the theme manifest. The store artwork follows what Chrome renders after installing this theme:

- **Google mark on the new tab page:** with `ntp_logo_alternate` enabled Chrome paints it as one flat tone derived from the new tab background. Against this lavender canvas it reads as a dusky mauve, close to `#A696AE`.
- **Shortcut tiles:** the round new-tab shortcuts take a muted mauve tint (`#BDB1C3`) from the theme.
- **Accent:** the violet used by the icon and the store tiles is the theme's own button tint, lifted to a readable saturation - not a second colour written by hand.
- **Address bar:** the omnibox keeps its own darker violet surface, so it stands slightly apart from the toolbar.

## Features

| Feature | Detail |
|---------|--------|
| 🌆 Violet dusk palette | Deep violet frame with a soft lavender reading surface |
| 🟣 Flat colour layers | Each surface is one solid colour |
| 👓 Tuned contrast | Tab, toolbar, bookmark and address-bar text stays readable |
| 🌇 Drawn icon | A low sun on the waterline, drawn for this theme |
| 🕶️ Incognito styling | An even deeper violet frame keeps private windows distinct |
| 🪶 Pure theme package | A manifest and an icon |

## Install

### From source (unpacked)

1. Download or clone this repository.
2. Open Chrome and navigate to `chrome://extensions`.
3. Enable **Developer mode** in the top-right corner.
4. Click **Load unpacked** and select this folder.

### From Chrome Web Store

Search for **Wistful Violet Theme** in the Chrome Web Store and install it.

## Preview

![Wistful Violet Theme browser preview](https://raw.githubusercontent.com/vaxicy/wistful-violet-theme/main/store-assets/screenshots/en/screenshot-1-browser.png)

![Wistful Violet Theme color palette](https://raw.githubusercontent.com/vaxicy/wistful-violet-theme/main/store-assets/screenshots/en/screenshot-2-introduction.png)

## Files

| File | Description |
|------|-------------|
| `manifest.json` | Chrome theme manifest (MV3) with inline `theme` config |
| `logo/logo.png` | Theme icon (128x128) |
| `store-assets/screenshots/en/` | Store listing screenshots (1280x800) |
| `store-assets/promo/` | Promo tiles (440x280 and 1400x560) |
| `store-assets/store-description.txt` | Store listing description (English) |
| `store-assets/ASSET-NOTES.md` | How the store artwork is composed and calibrated |
| `scripts/generate-logo.py` | Draws the icon (and the exploration sheet of six logo concepts) |
| `scripts/generate-store-assets.py` | Renders every store asset from one HTML/CSS source |
| `scripts/package.py` | Builds the release ZIP into the default output folder |

## Packaging

```bash
python3 scripts/package.py
```

The archive is written as `wistful-violet-theme-<version>.zip` into the default output folder (two levels above the project, derived from the script location). The version stays `1.0.0` for the first store upload.

Packaged: `manifest.json`, `README.md`, `LICENSE`, `logo/`. Left out, because Chrome Web Store takes them as separate uploads: `store-assets/` (screenshot, promo tiles, listing text), `scripts/`, `.gitignore`, `Cached Theme.pak`. The script re-reads `manifest.json` from inside the finished archive and fails if the archive root or the referenced files are wrong.

## License

Non-Commercial License — personal use permitted.

- ✅ Personal use, modification for personal use, sharing with attribution.
- ❌ Commercial use — a commercial licence is required.

Commercial licensing: contact the author.
