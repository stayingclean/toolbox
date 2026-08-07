# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""
Symbol eines Haendlers holen
============================

Legt assets/favicons/<domain>.png an (32x32), damit build.py es einbetten kann.

Aufruf:  uv run tools/favicon_holen.py www.coop.ch

Bewusst getrennt von build.py: der Build muss offline und per Doppelklick
laufen. Dieses Skript wird einmal je Haendler von Hand gestartet.

Manche Shops sperren automatische Abrufe aus (Coop antwortet mit 403). Dann
meldet das Skript das und nennt den Weg von Hand - es ist kein Ausfall,
sondern der Normalfall bei einem Teil der Haendler.
"""

import io
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
ZIEL = ROOT / "assets" / "favicons"
KANTE = 32
ZEITLIMIT = 15
USER_AGENT = "toolbox-favicon (+https://github.com/stayingclean/toolbox)"

LINK_TAG = re.compile(
    r'<link[^>]+rel=["\'][^"\']*icon[^"\']*["\'][^>]*>', re.IGNORECASE
)
HREF = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)


def zielpfad(domain: str) -> Path:
    return ZIEL / f"{domain.removeprefix('www.')}.png"


def symbol_adressen(domain: str, html: str) -> list:
    """Kandidaten fuer das Symbol, bester zuerst.

    Zuerst der Standardort, dann was die Seite selbst angibt - manche Shops
    liefern unter /favicon.ico nichts Brauchbares mehr.
    """
    basis = f"https://{domain}/"
    adressen = [basis + "favicon.ico"]
    for tag in LINK_TAG.findall(html or ""):
        treffer = HREF.search(tag)
        if treffer:
            adressen.append(urljoin(basis, treffer.group(1)))
    return adressen


def hole(adresse: str) -> bytes:
    anfrage = urllib.request.Request(
        adresse, headers={"user-agent": USER_AGENT}
    )
    with urllib.request.urlopen(anfrage, timeout=ZEITLIMIT) as antwort:
        return antwort.read()


def main():
    if len(sys.argv) < 2:
        print("Aufruf: uv run tools/favicon_holen.py <Domain>")
        print("Beispiel: uv run tools/favicon_holen.py www.coop.ch")
        raise SystemExit(1)

    domain = sys.argv[1].strip().removeprefix("https://").removeprefix("http://").strip("/")
    ZIEL.mkdir(parents=True, exist_ok=True)
    ziel = zielpfad(domain)

    seite = ""
    try:
        seite = hole(f"https://{domain}/").decode("utf-8", "ignore")
    except (urllib.error.URLError, OSError, ValueError):
        pass  # Ohne Startseite bleibt der Standardort - das genuegt meistens.

    from PIL import Image

    for adresse in symbol_adressen(domain, seite):
        try:
            roh = hole(adresse)
            bild = Image.open(io.BytesIO(roh))
        except Exception:
            continue
        bild = bild.convert("RGBA").resize((KANTE, KANTE), Image.LANCZOS)
        bild.save(ziel, "PNG", optimize=True)
        print(f"✅ {ziel.relative_to(ROOT).as_posix()} ({ziel.stat().st_size} Byte)")
        print("   Jetzt build.bat ausfuehren, damit es eingebettet wird.")
        return

    print(f"❌ Kein Symbol von {domain} zu holen.")
    print()
    print("   Das ist bei einem Teil der Haendler normal - sie sperren")
    print("   automatische Abrufe aus. Von Hand geht es so:")
    print()
    print(f"   1. https://{domain}/ im Browser oeffnen")
    print("   2. Das Symbol im Reiter speichern (oder aus der Seite kopieren)")
    print(f"   3. Als PNG hier ablegen: {ziel.relative_to(ROOT).as_posix()}")
    print("   4. build.bat ausfuehren")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
