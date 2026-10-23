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


@pytest.fixture(scope="module")
def frisch_gebaut(tmp_path_factory):
    """Das Ergebnis eines Builds, ausschliesslich nach einem Temp-Ordner.

    Der Arbeitsbaum wird nicht angefasst. Verglichen wird später gegen die
    eingecheckten Dateien -- also gegen den Soll-Stand, nicht gegen den
    eigenen Vorzustand: ein Vergleich derselben Datei vor und nach dem Bauen
    würde heilen, was er bewachen soll (weicht der Build ab, wäre sie ab dem
    zweiten Lauf überschrieben und der Test grün).

    Einmal je Modul gebaut, nicht je Test.
    """
    ziel = tmp_path_factory.mktemp("build")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(build, "OUTPUT", ziel / "skillsliste.html")
        mp.setattr(build, "OUTPUT_VORSCHLAG", ziel / "skill-vorschlagen.html")
        mp.setattr(build, "DATEN_JSON", ziel / "skills-daten.json")

        # Dieselbe Folge wie build.main(), ohne dessen Ausgabe (die rechnet
        # Pfade relativ zu ROOT und scheiterte an tmp_path). Beides muss
        # gemeinsam gepflegt werden: bekommt main() einen Schritt dazu, der die
        # Skillsliste verändert, geht er an diesen Wächtern vorbei, solange er
        # hier nicht ebenfalls steht.
        daten = build.load_data()
        build.render(daten, build.lade_favicons(daten))
        build.render_vorschlag(daten)
        build.write_daten_json(daten)
    return ziel


def test_wachposten_build_liefert_die_eingecheckte_skillsliste(frisch_gebaut):
    """Wächter gegen ein Mitändern der Skillsliste (Entscheid 2).

    Nicht Rot-Grün: der Test besteht schon vor der Umstellung und soll es
    danach weiter tun. `build.py` erzeugt Skillsliste und Vorschlagsformular
    im selben Lauf; wer die Quelle des Formulars ändert, darf die Skillsliste
    dabei nicht verändern.
    """
    assert (frisch_gebaut / "skillsliste.html").read_bytes() == SKILLSLISTE.read_bytes()


@pytest.mark.parametrize(
    "datei, normieren",
    [("skill-vorschlagen.html", False), ("skills-daten.json", True)],
)
def test_wachposten_build_liefert_die_uebrigen_eingecheckten_generate(
    frisch_gebaut, datei, normieren
):
    """Wie der Wächter oben, für die beiden anderen Dateien des Builds.

    Wer `template-vorschlag.html` ändert und das Bauen vergisst, veröffentlicht
    ein veraltetes Formular -- online fehlte dann der `<link>` auf
    `tokens.css`, und die Seite stünde ohne Farben da. `skills-daten.json` ist
    mit dabei, weil es fast nichts kostet; das Risiko ist kleiner, denn die
    Datei wird nicht von Hand bearbeitet.

    Die JSON schreibt der Build bewusst fest mit LF; ein Windows-Checkout
    (autocrlf) macht daraus CRLF. Nur sie wird darum im Zeilenende angeglichen.
    Das HTML übernimmt die Zeilenenden der Vorlage und wird byteweise verglichen.
    """
    eingecheckt = (ROOT / "docs" / datei).read_bytes()
    gebaut = (frisch_gebaut / datei).read_bytes()
    if normieren:
        eingecheckt = eingecheckt.replace(b"\r\n", b"\n")
    assert gebaut == eingecheckt, (
        f"{datei} ist veraltet: `uv run build.py` ausführen und das Ergebnis "
        "einchecken"
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
    """Veröffentlicht wird, was der Deploy als Artefakt hochlädt.

    Der Pfad steht in `.github/workflows/deploy.yml` (`upload-pages-artifact`).
    Wer ihn ändert, veröffentlichte `tokens.css` nicht mehr, und jede Seite
    stünde online ohne Farben, während alle Tests grün blieben.
    """
    workflow = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    block = re.search(r"upload-pages-artifact[^\n]*\n\s*with:\s*\n\s*path:\s*(\S+)", workflow)
    assert block, "deploy.yml lädt kein Artefakt hoch (upload-pages-artifact mit path:)"
    hochgeladen = (ROOT / block.group(1)).resolve()
    assert TOKEN_DATEI.resolve().is_relative_to(hochgeladen), (
        f"deploy.yml lädt {block.group(1)} hoch -- tokens.css läge ausserhalb"
    )


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
        # Eine Stilvorlage hat keinen <style>-Block, sie holt die Token per
        # @import -- und das gilt nur als erste Regel der Datei. Steht davor
        # irgendeine Regel, verwirft der Browser es, und alle Seiten, die die
        # Vorlage teilen, stehen ohne Farben da.
        ohne_kommentare = re.sub(r"/\*.*?\*/", "", text, flags=re.S).lstrip()
        assert re.match(
            r"""@import\s+url\(["']?[^"')]*tokens\.css""", ohne_kommentare
        ), f"{pfad}: @import der Token ist nicht die erste Regel der Datei"
        return
    stil = re.search(r"<style[\s>]", text)
    if stil is None:
        pytest.skip(f"{pfad} hat keinen <style>-Block")
    verweis = re.search(r"""<link[^>]*href=["'][^"']*tokens\.css""", text)
    assert verweis, f"{pfad} bindet tokens.css nicht per <link> ein"
    assert verweis.start() < stil.start(), (
        f"{pfad}: der <link> auf tokens.css steht hinter dem <style>-Block "
        "und übersteuerte dessen Regeln"
    )
