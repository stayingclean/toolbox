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
    # Die Seite laedt keine Schrift von aussen und ueberschreibt darum beide
    # Schrift-Token (siehe test_plakat_ueberschreibt_die_schrift_tokens).
    "docs/plakat.html": {"--font-body", "--font-display"},
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
    # Pfade relativ zu ROOT und scheiterte an tmp_path). Beides muss
    # gemeinsam gepflegt werden: bekommt main() einen Schritt dazu, der die
    # Skillsliste verändert, geht er an diesem Wächter vorbei, solange er hier
    # nicht ebenfalls steht.
    daten = build.load_data()
    build.render(daten, build.lade_favicons(daten))
    build.render_vorschlag(daten)
    build.write_daten_json(daten)

    assert gebaut.read_bytes() == SKILLSLISTE.read_bytes()


@pytest.mark.parametrize(
    "gebaut_als, eingecheckt",
    [
        ("skill-vorschlagen.html", ROOT / "docs" / "skill-vorschlagen.html"),
        ("skills-daten.json", ROOT / "docs" / "skills-daten.json"),
    ],
)
def test_wachposten_build_liefert_die_uebrigen_eingecheckten_generate(
    monkeypatch, tmp_path, gebaut_als, eingecheckt
):
    """Wie der Wächter oben, für die beiden anderen Dateien des Builds.

    Wer `template-vorschlag.html` ändert und das Bauen vergisst, veröffentlicht
    ein veraltetes Formular -- online fehlte dann der `<link>` auf
    `tokens.css`, und die Seite stünde ohne Farben da. `skills-daten.json` ist
    mit dabei, weil es fast nichts kostet; das Risiko ist kleiner, denn die
    Datei wird nicht von Hand bearbeitet.

    Gebaut wird ausschliesslich nach `tmp_path`: der Arbeitsbaum bleibt bei
    jedem Testlauf unberührt.
    """
    monkeypatch.setattr(build, "OUTPUT", tmp_path / "skillsliste.html")
    monkeypatch.setattr(build, "OUTPUT_VORSCHLAG", tmp_path / "skill-vorschlagen.html")
    monkeypatch.setattr(build, "DATEN_JSON", tmp_path / "skills-daten.json")

    # Dieselbe Folge wie build.main() -- siehe Kommentar im Wächter oben.
    daten = build.load_data()
    build.render(daten, build.lade_favicons(daten))
    build.render_vorschlag(daten)
    build.write_daten_json(daten)

    # Zeilenenden angleichen: im Repo liegen die Dateien mit LF, ein Checkout
    # unter Windows macht (autocrlf) CRLF daraus, während der Build -- bei der
    # JSON-Datei bewusst -- LF schreibt. Verglichen wird der Inhalt.
    def inhalt(pfad):
        return pfad.read_bytes().replace(b"\r\n", b"\n")

    assert inhalt(tmp_path / gebaut_als) == inhalt(eingecheckt), (
        f"{eingecheckt.name} ist veraltet: build.py (bzw. uv run build.py) "
        "ausführen und das Ergebnis einchecken"
    )


# Seiten, die bewusst keine Token aus tokens.css beziehen -- mit Grund.
AUSGENOMMEN: dict[str, str] = {
    "docs/skillsliste.html": "muss in sich geschlossen bleiben (ohne Netz benutzbar)",
    "docs/flyer-editor.html": "exportiert sich selbst als Datei, alles muss im Dokument stehen",
    "docs/budgetvorlage.html": "wird getrennt umgebaut",
    "docs/neutral_flyer.html": "blosse Weiterleitung",
}


def test_jede_seite_ist_migriert_ausgenommen_oder_faellt_auf():
    """Der Wachposten gegen das Vergessen: eine neue Seite in docs/, die
    eigene Farben oder Schriften setzt, muss entweder in MIGRIERT oder in
    AUSGENOMMEN stehen. Sonst läuft sie auseinander und niemand sieht es.

    Geprüft werden HTML- und CSS-Dateien (ein neues gemeinsames Stylesheet
    wäre derselbe Fall). `docs/altbau/` ist ein fremder Viewer mit eigenem
    `vendor/` und bleibt aussen vor, `tokens.css` ist die Quelle selbst.
    """
    seiten = sorted([*(ROOT / "docs").rglob("*.html"), *(ROOT / "docs").rglob("*.css")])
    for seite in seiten:
        rel = seite.relative_to(ROOT).as_posix()
        if (
            seite == TOKEN_DATEI
            or rel in MIGRIERT
            or rel in AUSGENOMMEN
            or rel.startswith("docs/altbau/")
        ):
            continue
        assert not (set(tokens_der_datei(seite)) & set(TOKENS)), (
            f"{rel} setzt eigene Token, steht aber weder in MIGRIERT noch in "
            "AUSGENOMMEN -- in tokens.css einbinden oder begründet ausnehmen"
        )


VERWEIS = re.compile(
    r"""(?:<link[^>]*href=["']|@import\s+url\(["']?)([^"')]*tokens\.css)"""
)


@pytest.mark.parametrize("pfad", sorted(MIGRIERT))
def test_jeder_verweis_auf_die_tokens_zeigt_auf_die_datei(pfad):
    """Ein Tippfehler im Pfad fällt sonst niemandem auf -- die Seite erscheint
    einfach ohne Farben. Der Verweis ist relativ zur verweisenden Datei."""
    quelle = ROOT / pfad
    ziele = VERWEIS.findall(quelle.read_text(encoding="utf-8"))
    assert ziele, f"{pfad} verweist gar nicht auf tokens.css"
    for ziel in ziele:
        gemeint = (quelle.parent / ziel).resolve()
        assert gemeint == TOKEN_DATEI.resolve(), (
            f"{pfad} verweist auf {ziel} -- das ist nicht {TOKEN_DATEI.name}"
        )
        # Der Pfadvergleich allein bliebe grün, wenn die Datei umbenannt oder
        # gelöscht würde: er vergleicht zwei Namen, nicht zwei Dateien.
        assert gemeint.is_file(), f"{pfad} verweist auf {ziel}, die Datei fehlt"


def test_die_tokens_werden_mitveroeffentlicht():
    """Veröffentlicht wird nur docs/."""
    assert TOKEN_DATEI.relative_to(ROOT).parts[0] == "docs"


@pytest.mark.parametrize("pfad", sorted(MIGRIERT))
def test_die_tokens_werden_vor_dem_eigenen_stil_geladen(pfad):
    """Bei gleicher Spezifität gewinnt das später Geladene. Stünde der <link>
    nach dem <style> der Seite, übersteuerten die Token deren eigene Regeln
    -- und das Aussehen änderte sich still.

    Am schärfsten beim Plakat: es lädt keine Schrift von aussen und
    überschreibt `--font-body`/`--font-display` in seinem eigenen `:root`.
    Das gewinnt nur, weil es nach tokens.css kommt (`:root` gegen `:root`,
    gleiche Spezifität). Verrutschte der <link> hinter den <style>-Block,
    bliebe jeder andere Test grün, und die Seite zöge Inter aus tokens.css.

    Verglichen werden Stellen im Text, nicht Zeilennummern. Massgebend ist der
    erste <style>-Block.
    """
    text = (ROOT / pfad).read_text(encoding="utf-8")
    if pfad.endswith(".css"):
        # z. B. stil.css: eine Stilvorlage hat keinen <style>-Block, sie holt
        # die Token per @import (das steht ohnehin zwingend am Dateianfang).
        # Nicht am Text erkennen: ein Kommentar darf "<style>" erwähnen.
        pytest.skip(f"{pfad} ist selbst die Stilvorlage")
    stil = re.search(r"<style[\s>]", text)
    if stil is None:
        pytest.skip(f"{pfad} hat keinen <style>-Block")
    verweis = re.search(r"""<link[^>]*href=["'][^"']*tokens\.css""", text)
    assert verweis, f"{pfad} bindet tokens.css nicht per <link> ein"
    assert verweis.start() < stil.start(), (
        f"{pfad}: der <link> auf tokens.css steht hinter dem <style>-Block "
        "und übersteuerte dessen Regeln"
    )
