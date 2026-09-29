"""Build the Chrome Web Store ZIP for Wistful Violet Theme.

`manifest.json` must sit at the archive root and the archive must hold only the
extension body: store screenshots, promo tiles, store listing text, the render
scripts and the local browser cache are separate Chrome Web Store uploads, so
they stay out of the package.

The output folder is derived from the project location (../..), never hardcoded,
and the same folder is the user's default download folder for release archives.
"""

import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = Path(os.path.abspath(os.path.join(ROOT, os.pardir, os.pardir)))

# only the extension body ships; everything else is a separate store upload
INCLUDE = ["manifest.json", "README.md", "LICENSE", "logo"]
ALWAYS_EXCLUDE = {
    "store-assets",
    "scripts",
    ".git",
    ".codebuddy",
    ".gitignore",
    "Cached Theme.pak",
    "__pycache__",
}


def manifest_refs(m):
    """Every file path the manifest points at, so we can prove they exist."""
    refs = list((m.get("icons") or {}).values())
    theme = m.get("theme") or {}
    refs += list((theme.get("images") or {}).values())
    return refs


def collect():
    files = []
    for rel in INCLUDE:
        p = ROOT / rel
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.relative_to(ROOT).parts[0] not in ALWAYS_EXCLUDE:
                    files.append(f.relative_to(ROOT).as_posix())
        elif p.is_file():
            files.append(rel)
    return files


def main():
    m = json.loads((ROOT / "manifest.json").read_text("utf-8-sig"))

    # 1. manifest must be MV3 and carry a version
    assert m["manifest_version"] == 3, "manifest_version must be 3"
    version = m["version"]
    assert isinstance(version, str) and version, "manifest version missing"

    # 2. every file the manifest references must exist
    missing = [r for r in manifest_refs(m) if not (ROOT / r).exists()]
    assert not missing, f"manifest references missing files: {missing}"

    files = collect()
    assert "manifest.json" in files, "manifest.json must be packaged"

    zip_path = DEFAULT_OUT / f"{ROOT.name}-{version}.zip"
    DEFAULT_OUT.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in files:
            z.write(ROOT / rel, rel)          # arcname=rel keeps it at the root

    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        # 3. manifest.json sits at the archive root, not inside a folder
        assert "manifest.json" in names, "manifest.json is not at the archive root"
        # 4. parse the packaged manifest, not the local one
        inside = json.loads(z.read("manifest.json").decode("utf-8"))
        assert inside["name"] == m["name"], "packaged manifest name mismatch"
        assert inside["version"] == version, "packaged manifest version mismatch"
        for ref in manifest_refs(m):
            assert ref in names, f"manifest reference {ref} is missing from the archive"
        assert not [n for n in names if n.split("/")[0] in ALWAYS_EXCLUDE], \
            "excluded content leaked into the archive"

    # 5. the archive on disk is readable and non-empty
    assert zip_path.stat().st_size > 0, "archive is empty"

    print(f"{zip_path.name}  {zip_path.stat().st_size:,} bytes")
    print("folder:", zip_path.parent)
    print("contents:", ", ".join(sorted(names)))


if __name__ == "__main__":
    main()
