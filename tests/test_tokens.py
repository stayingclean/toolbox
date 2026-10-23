"""Wächter für den gemeinsamen Token-Satz in docs/tokens.css.

Mehrere Seiten der Toolbox beziehen ihre Farben und Schriften aus einer
Datei, statt sie je Seite neu zu deklarieren. Diese Tests halten fest, was
in der Datei steht. Spätere Aufgaben benutzen die Namen aus diesem Modul
(`TOKENS`, `MIGRIERT`, `tokens_der_datei` ...) und tragen sich in `MIGRIERT`
selbst ein, sobald eine Seite umgestellt ist.
"""

import hashlib  # noqa: F401  (von den Wächtern der Folgeaufgaben benutzt)
import re
import subprocess  # noqa: F401
import sys  # noqa: F401
from pathlib import Path

import pytest  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
TOKEN_DATEI = ROOT / "docs" / "tokens.css"
SKILLSLISTE = ROOT / "docs" / "skillsliste.html"

# Der vereinbarte Satz, erhoben am Stand ec04785. Signalfarben (--warn, --ok
# ...), Radien, Abstände und Übergänge gehören bewusst nicht dazu.
TOKENS: dict[str, str] = {
    "--bg": "#FAF8F5",
    "--card": "#FFFFFF",
    "--card-hover": "#F5FAFA",
    "--border": "#E8E4DF",
    "--text": "#1C1C1C",
    "--muted": "#7A7268",
    "--accent": "#008080",
    "--accent-dark": "#006666",
    "--accent-tint": "#E6F2F2",
    "--font-display": "'Playfair Display', Georgia, serif",
    "--font-body": (
        "'Inter', -apple-system, BlinkMacSystemFont, "
        '"Segoe UI", Roboto, sans-serif'
    ),
}

# Repo-relativer POSIX-Pfad -> Token, die diese Datei selbst setzen darf.
# Leer heisst: keine. Jede umgestellte Seite trägt sich hier selbst ein.
MIGRIERT: dict[str, set[str]] = {}


def tokens_der_datei(pfad: Path) -> dict[str, str]:
    """Die Deklarationen des ersten `:root { ... }`-Blocks der Datei.

    Werte kommen mit zusammengefasstem Weissraum zurück, sonst schlüge ein
    Vergleich schon an der Einrückung fehl. Ohne `:root`-Block: leeres dict.
    """
    text = re.sub(r"/\*.*?\*/", "", pfad.read_text(encoding="utf-8"), flags=re.S)
    block = re.search(r":root\s*\{([^}]*)\}", text)
    if block is None:
        return {}
    ergebnis: dict[str, str] = {}
    for deklaration in block.group(1).split(";"):
        name, doppelpunkt, wert = deklaration.partition(":")
        if doppelpunkt and name.strip():
            ergebnis[name.strip()] = " ".join(wert.split())
    return ergebnis


def test_tokens_css_haelt_genau_den_vereinbarten_satz():
    """Die Werte stammen aus den vier Seiten, die sie heute schon teilen.
    Ändert sich hier einer, ändert sich das Aussehen der halben Website --
    das soll auffallen."""
    assert tokens_der_datei(TOKEN_DATEI) == TOKENS
