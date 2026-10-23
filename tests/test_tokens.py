"""Wächter für den gemeinsamen Token-Satz in docs/tokens.css.

Mehrere Seiten der Toolbox beziehen ihre Farben und Schriften aus einer
Datei, statt sie je Seite neu zu deklarieren. Diese Tests halten fest, was
in der Datei steht. Spätere Aufgaben benutzen die Namen aus diesem Modul
(`TOKENS`, `MIGRIERT`, `tokens_der_datei` ...) und tragen sich in `MIGRIERT`
selbst ein, sobald eine Seite umgestellt ist.
"""

import re
from pathlib import Path

import pytest

import build

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
MIGRIERT: dict[str, set[str]] = {
    "docs/index.html": set(),
    "docs/skill-vorschlagen.html": set(),
    "docs/claude-anleitung/stil.css": set(),
}


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


@pytest.mark.parametrize("pfad", sorted(MIGRIERT))
def test_migrierte_seite_bindet_die_tokens_ein(pfad):
    assert re.search(
        r"""(?:<link[^>]*href\s*=|@import\s+url\()\s*["']?[^"')]*tokens\.css""",
        (ROOT / pfad).read_text(encoding="utf-8"),
    )


@pytest.mark.parametrize("pfad", sorted(MIGRIERT))
def test_migrierte_seite_deklariert_keinen_token_neu(pfad):
    """Eine Seite, die einen Token nochmals selbst setzt, läuft wieder
    auseinander -- und niemand sieht es. Erlaubt sind nur die in MIGRIERT
    eingetragenen, begründeten Ausnahmen."""
    doppelt = set(tokens_der_datei(ROOT / pfad)) & set(TOKENS) - MIGRIERT[pfad]
    assert not doppelt, f"{pfad} setzt selbst: {sorted(doppelt)}"


def test_wachposten_build_liefert_die_eingecheckte_skillsliste(monkeypatch, tmp_path):
    """Wächter gegen ein Mitändern der Skillsliste (Entscheid 2).

    Nicht Rot-Grün: der Test besteht schon vor der Umstellung und soll es
    danach weiter tun. `build.py` erzeugt Skillsliste und Vorschlagsformular
    im selben Lauf; wer die Quelle des Formulars ändert, darf die Skillsliste
    dabei nicht verändern.

    Der Build schreibt nach `tmp_path`, verglichen wird die frisch gebaute
    Skillsliste mit der eingecheckten Datei -- also gegen den Soll-Stand, nicht
    gegen den eigenen Vorzustand. Ein Vergleich derselben Datei vor und nach
    dem Bauen würde heilen, was er bewachen soll: weicht der Build ab, wäre
    sie ab dem zweiten Lauf überschrieben und der Test grün. Im Arbeitsbaum
    wird nichts angefasst.
    """
    gebaut = tmp_path / "skillsliste.html"
    monkeypatch.setattr(build, "OUTPUT", gebaut)
    monkeypatch.setattr(build, "OUTPUT_VORSCHLAG", tmp_path / "skill-vorschlagen.html")
    monkeypatch.setattr(build, "DATEN_JSON", tmp_path / "skills-daten.json")

    # Dieselbe Folge wie build.main(), ohne dessen Ausgabe (die rechnet
    # Pfade relativ zu ROOT und scheiterte an tmp_path).
    daten = build.load_data()
    build.render(daten, build.lade_favicons(daten))
    build.render_vorschlag(daten)
    build.write_daten_json(daten)

    assert gebaut.read_bytes() == SKILLSLISTE.read_bytes()
