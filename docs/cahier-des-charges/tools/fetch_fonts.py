#!/usr/bin/env python3
"""
fetch_fonts.py — télécharge les polices du thème PDF (Inter, JetBrains Mono).

Les binaires ne sont pas versionnés : ce script les récupère depuis GitHub
(api.github.com), les convertit en TTF si nécessaire et les place dans
`docs/cahier-des-charges/.fonts/` (ignoré par Git).

Usage : python tools/fetch_fonts.py [--dest .fonts]
Dépendances : fonttools, brotli (uniquement pour les sources WOFF2).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

INTER = ["Inter-Light", "Inter-Regular", "Inter-Medium", "Inter-SemiBold",
         "Inter-Bold", "Inter-Italic", "Inter-MediumItalic",
         "Inter-SemiBoldItalic", "Inter-BoldItalic"]
MONO = ["JetBrainsMono-Regular", "JetBrainsMono-Medium", "JetBrainsMono-Bold"]


def download(repo: str, path: str) -> bytes:
    quoted = urllib.parse.quote(path, safe="")
    url = f"https://api.github.com/repos/{repo}/contents/{quoted}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.raw",
        "User-Agent": "myrdv-cahier-des-charges",
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def convert_woff2(src: Path, dest: Path) -> None:
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        sys.exit("fonttools manquant : pip install fonttools brotli")
    font = TTFont(str(src))
    font.flavor = None
    font.save(str(dest))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", default=str(Path(__file__).resolve().parent.parent / ".fonts"))
    args = parser.parse_args()
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    for name in INTER:
        target = dest / f"{name}.ttf"
        if target.exists():
            continue
        woff2 = dest / f"{name}.woff2"
        woff2.write_bytes(download("rsms/inter", f"docs/font-files/{name}.woff2"))
        convert_woff2(woff2, target)
        woff2.unlink()
        print("✔", target.name)

    for name in MONO:
        target = dest / f"{name}.ttf"
        if target.exists():
            continue
        target.write_bytes(download("JetBrains/JetBrainsMono", f"fonts/ttf/{name}.ttf"))
        print("✔", target.name)

    print(f"Polices disponibles dans {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
