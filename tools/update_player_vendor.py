"""Download the Scratch runtime that `kitty run` serves, into kitty_player/vendor/.

    python tools/update_player_vendor.py

Kitty bundles the last BSD-3-Clause releases of Scratch's libraries. Later
releases are AGPL-3.0-only, so do not raise these versions without changing
Kitty's license plan. The files are the exact ones published on npm, fetched
through the jsDelivr CDN, and SOURCES.txt records each URL and SHA-256.
"""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "kitty_player" / "vendor"
CDN = "https://cdn.jsdelivr.net/npm"

# (package@version, file in the package, name in vendor/)
FILES = [
    ("scratch-vm@4.8.115", "dist/web/scratch-vm.js", "scratch-vm.js"),
    ("scratch-render@1.2.126", "dist/web/scratch-render.js", "scratch-render.js"),
    ("scratch-storage@3.0.39", "dist/web/scratch-storage.js", "scratch-storage.js"),
    ("scratch-storage@3.0.39", "dist/web/chunks/fetch-worker.0fa0968cc994fb298693.js", "chunks/fetch-worker.0fa0968cc994fb298693.js"),
    ("scratch-storage@3.0.39", "dist/web/chunks/fetch-worker.cd3a909d7b876aabf94a.js", "chunks/fetch-worker.cd3a909d7b876aabf94a.js"),
    ("scratch-svg-renderer@2.5.46", "dist/web/scratch-svg-renderer.js", "scratch-svg-renderer.js"),
    ("scratch-audio@1.0.332", "dist.js", "scratch-audio.js"),
    ("scratch-vm@4.8.115", "LICENSE", "licenses/scratch-vm.LICENSE"),
    ("scratch-vm@4.8.115", "TRADEMARK", "licenses/scratch-vm.TRADEMARK"),
    ("scratch-render@1.2.126", "LICENSE", "licenses/scratch-render.LICENSE"),
    ("scratch-render@1.2.126", "TRADEMARK", "licenses/scratch-render.TRADEMARK"),
    ("scratch-storage@3.0.39", "LICENSE", "licenses/scratch-storage.LICENSE"),
    ("scratch-svg-renderer@2.5.46", "LICENSE", "licenses/scratch-svg-renderer.LICENSE"),
    ("scratch-audio@1.0.332", "LICENSE", "licenses/scratch-audio.LICENSE"),
]


def main():
    lines = [
        "The Scratch runtime that `kitty run` serves. Each file is unchanged from the npm package.",
        "Refresh with: python tools/update_player_vendor.py",
        "",
    ]
    for spec, source, name in FILES:
        url = f"{CDN}/{spec}/{source}"
        with urllib.request.urlopen(url, timeout=120) as response:
            data = response.read()
        target = VENDOR / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        lines.append(f"{name}  {hashlib.sha256(data).hexdigest()}  {url}")
        print(f"{len(data):>10}  {name}")
    (VENDOR / "SOURCES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
