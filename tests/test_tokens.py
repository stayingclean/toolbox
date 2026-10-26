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

# Die Farbwerte des Satzes, kleingeschrieben. Nur die neun Farben: die zwei
# Schrift-Token tragen Namenslisten, die auch eine fremde Seite zu Recht
# nennen darf (-apple-system, sans-serif).
TOKEN_FARBEN: frozenset[str] = frozenset(
    wert.lower() for wert in TOKENS.values() if wert.startswith("#")
)

# Repo-relativer POSIX-Pfad -> Token, die diese Datei selbst setzen darf.
# Leer heisst: keine. Jede umgestellte Seite trägt sich hier selbst ein.
MIGRIERT: dict[str, set[str]] = {
    # Die zehn eigenen --color-*-Namen der Seite hängen als Aliase an den
    # Token (--color-primary: var(--accent) und so fort), damit die über 300
    # var(--color-…) in ihren 2900 Zeilen CSS unberührt bleiben. Einen der
    # elf Namen setzt sie damit selbst nicht mehr.
    "docs/budgetvorlage.html": set(),
    "docs/index.html": set(),
    "docs/skill-vorschlagen.html": set(),
    "docs/claude-anleitung/stil.css": set(),
    # Die Seite laedt keine Schrift von aussen und ueberschreibt darum beide
    # Schrift-Token (siehe test_plakat_ueberschreibt_die_schrift_tokens).
    "docs/plakat.html": {"--font-body", "--font-display"},
}


def ohne_kommentare(text: str) -> str:
    """Der Text ohne HTML- und CSS-Kommentare.

    Ein auskommentierter `<link>` lädt nichts, und `/* --accent: ... */`
    deklariert nichts. Wer bloss im Rohtext nach dem Namen sucht, hält beides
    für vorhanden: genau daran blieb der Pfad-Wächter einmal grün, während
    die Seite ohne Farben online gegangen wäre.
    """
    ohne_html = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return re.sub(r"/\*.*?\*/", "", ohne_html, flags=re.S)


def _deklarationen(inhalt: str) -> list[tuple[str, str]]:
    """Die `name: wert`-Paare eines Regelblocks, Weissraum zusammengefasst.

    Zusammengefasst, weil ein Vergleich sonst schon an der Einrückung
    fehlschlüge -- `--font-body` steht in zwei Dateien über zwei Zeilen.
    """
    paare: list[tuple[str, str]] = []
    for deklaration in inhalt.split(";"):
        name, doppelpunkt, wert = deklaration.partition(":")
        if doppelpunkt and name.strip():
            paare.append((name.strip(), " ".join(wert.split())))
    return paare


def tokens_der_datei(pfad: Path) -> dict[str, str]:
    """Die Deklarationen des ersten `:root { ... }`-Blocks der Datei.

    Ohne `:root`-Block: leeres dict.

    Gedacht für den Wertvergleich von `tokens.css` selbst und dort, wo es auf
    genau diesen Block ankommt. Wer wissen will, *ob* eine Seite irgendwo
    einen Token setzt, nimmt `token_deklarationen` -- diese Funktion hier ist
    gegen einen zweiten Block und gegen jeden anderen Selektor blind.
    """
    text = ohne_kommentare(pfad.read_text(encoding="utf-8"))
    block = re.search(r":root\s*\{([^}]*)\}", text)
    if block is None:
        return {}
    return dict(_deklarationen(block.group(1)))


def token_deklarationen(pfad: Path) -> dict[str, list[str]]:
    """Jede Deklaration eines `--`-Namens, aus **allen** Blöcken und unter
    **jedem** Selektor; die Werte in Dokumentreihenfolge, Mehrfachnennungen
    bleiben erhalten.

    `tokens_der_datei` sieht nur den ersten `:root`-Block. Ein nachträglich
    angefügter Dunkel- oder Druck-Block ist aber die natürlichste Form, in
    der eine Seite wieder eigene Werte bekommt -- ein zweites `:root{...}`
    am Dateiende, ein `html{...}`, ein `@media print{:root{...}}`. Dagegen
    war der Wächter blind, bis es eine Gegenprobe zeigte.

    Gelesen werden die **innersten** Blöcke: eine `@media`-Hülle enthält
    selbst Klammern und fällt dadurch heraus, ihr Inhalt nicht.

    Die Kehrseite derselben Regel: steht eine Deklaration **neben** einem
    verschachtelten Block (`:root { --a: 1; @media ... { ... } }`), fällt
    sie mit der Hülle heraus. Verschachteltes CSS kommt in diesem Projekt
    nicht vor; die drei Rueckfallformen oben fängt er.
    """
    gefunden: dict[str, list[str]] = {}
    text = ohne_kommentare(pfad.read_text(encoding="utf-8"))
    for block in re.finditer(r"\{([^{}]*)\}", text):
        for name, wert in _deklarationen(block.group(1)):
            if name.startswith("--"):
                gefunden.setdefault(name, []).append(wert)
    return gefunden


STILVERWEIS = re.compile(
    r"""<link\b[^>]*?\bhref\s*=\s*["']([^"']*)["']"""
    r"""|@import\s+url\(\s*["']?([^"')]*)"""
    r"""|@import\s+["']([^"']*)["']"""
)


def stilverweise(text: str) -> list[tuple[int, str]]:
    """Jede geladene Stilvorlage: (Stelle im kommentarfreien Text, Ziel).

    Gefangen wird der **ganze** Attributwert, nicht der Teilstring
    `tokens.css` darin. Suchte man den Teilstring, zählte `tokens.css.bak`
    als Verweis auf die Datei: die Seite ginge ohne Farben online und der
    Wächter bliebe grün. Beides ist vorgekommen.
    """
    return [
        (treffer.start(), next(g for g in treffer.groups() if g is not None))
        for treffer in STILVERWEIS.finditer(ohne_kommentare(text))
    ]


def token_verweise(text: str) -> list[tuple[int, str]]:
    """Die Verweise, die `tokens.css` meinen -- erkannt am Dateinamen.

    Am Namen, nicht am aufgelösten Pfad: `tokens.css.bak` und
    `../tokens.css` sind gemeint und falsch, und genau das soll auffallen.
    Eine andere Stilvorlage daneben (`stil.css`) geht nicht mit.
    """
    return [
        (stelle, ziel)
        for stelle, ziel in stilverweise(text)
        if "tokens" in ziel.rsplit("/", 1)[-1]
    ]


def test_tokens_css_haelt_genau_den_vereinbarten_satz():
    """Die Werte stammen aus den vier Seiten, die sie heute schon teilen.
    Ändert sich hier einer, ändert sich das Aussehen der halben Website --
    das soll auffallen."""
    assert tokens_der_datei(TOKEN_DATEI) == TOKENS
    # Und zwar an genau einer Stelle: ein zweiter Block in der Quelldatei
    # selbst (dunkles Thema, Druck) überschriebe den Satz, ohne dass der
    # Vergleich oben etwas merkte -- der liest nur den ersten `:root`.
    ueberall = token_deklarationen(TOKEN_DATEI)
    mehrfach = sorted(name for name, werte in ueberall.items() if len(werte) > 1)
    assert not mehrfach, f"tokens.css setzt diese Token mehrfach: {mehrfach}"
    assert set(ueberall) == set(TOKENS), (
        "tokens.css deklariert ausserhalb des :root-Blocks oder Namen, die "
        f"nicht im Satz stehen: {sorted(set(ueberall) ^ set(TOKENS))}"
    )


@pytest.mark.parametrize("pfad", sorted(MIGRIERT))
def test_migrierte_seite_deklariert_keinen_token_neu(pfad):
    """Eine Seite, die einen Token nochmals selbst setzt, läuft wieder
    auseinander -- und niemand sieht es. Erlaubt sind nur die in MIGRIERT
    eingetragenen, begründeten Ausnahmen.

    Gezählt wird jeder Block und jeder Selektor, nicht nur das erste
    `:root`: ein angehängter Dunkel- oder Druck-Block wäre derselbe Rückfall.
    """
    doppelt = (set(token_deklarationen(ROOT / pfad)) & set(TOKENS)) - MIGRIERT[pfad]
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


# Seiten, die bewusst keine Token aus tokens.css beziehen -- mit Grund. Der
# Grund steht hier und nur hier, in keiner Fehlermeldung -- und er kann dort
# auch nicht stehen: eine Seite, die der Wachposten unten meldet, fehlt ja
# gerade in dieser Liste. Er richtet sich an den, der die Liste liest und
# entscheiden muss, ob eine neue Seite dazugehoert.
AUSGENOMMEN: dict[str, str] = {
    "docs/skillsliste.html": "muss in sich geschlossen bleiben (ohne Netz benutzbar)",
    "docs/flyer-editor.html": "exportiert sich selbst als Datei, alles muss im Dokument stehen",
    "docs/neutral_flyer.html": "blosse Weiterleitung",
}


def nicht_eingetragene_seiten() -> list[Path]:
    """Die Seiten in docs/, die weder in MIGRIERT noch in AUSGENOMMEN stehen.

    Also: alles Neue. Geprüft werden HTML- und CSS-Dateien (ein neues
    gemeinsames Stylesheet wäre derselbe Fall). `docs/altbau/` ist ein fremder
    Viewer mit eigenem `vendor/` und bleibt aussen vor, `tokens.css` ist die
    Quelle selbst.
    """
    seiten = sorted([*(ROOT / "docs").rglob("*.html"), *(ROOT / "docs").rglob("*.css")])
    neu = []
    for seite in seiten:
        rel = seite.relative_to(ROOT).as_posix()
        if (
            seite == TOKEN_DATEI
            or rel in MIGRIERT
            or rel in AUSGENOMMEN
            or rel.startswith("docs/altbau/")
        ):
            continue
        neu.append(seite)
    return neu


def test_jede_seite_ist_migriert_ausgenommen_oder_faellt_auf():
    """Der Wachposten gegen das Vergessen: eine neue Seite in docs/, die
    eigene Farben oder Schriften setzt, muss entweder in MIGRIERT oder in
    AUSGENOMMEN stehen. Sonst läuft sie auseinander und niemand sieht es.
    """
    for seite in nicht_eingetragene_seiten():
        rel = seite.relative_to(ROOT).as_posix()
        assert not (set(token_deklarationen(seite)) & set(TOKENS)), (
            f"{rel} setzt eigene Token, steht aber weder in MIGRIERT noch in "
            "AUSGENOMMEN -- in tokens.css einbinden oder begründet ausnehmen"
        )


def test_eine_neue_seite_schreibt_keine_token_farbe_von_hand():
    """Die zweite Hälfte derselben Regel: «Im CSS dann `var(--accent)` statt
    `#008080`.»

    Der Wachposten darüber sieht nur eigene Deklarationen der elf **Namen**.
    Die Form, in der in diesem Projekt bisher alles auseinanderlief, trägt
    aber andere Namen bei gleichen Werten -- «die Farben stimmen schon, nur
    die Namen gehen drei Wege». Hier zählt darum der Wert: steht eine der
    neun Farben als Hex in einer neuen Datei, gehört die Seite an die Token
    oder begründet nach AUSGENOMMEN.

    Geprüft wird die sechsstellige Schreibweise aus `TOKENS`. `#fff` rutscht
    durch, und das ist tragbar: abgeschrieben wird aus Budgetvorlage und
    Skillsliste, und die schreiben beide sechsstellig.

    Die Seiten in MIGRIERT sind draussen, weil dort jeder Wert angeschaut
    ist: `stil.css` setzt `#FFFFFF` für einen Code-Block, das Plakat eines
    als JPEG-Grund im JavaScript.
    """
    for seite in nicht_eingetragene_seiten():
        text = seite.read_text(encoding="utf-8").lower()
        gefunden = sorted(farbe for farbe in TOKEN_FARBEN if farbe in text)
        assert not gefunden, (
            f"{seite.relative_to(ROOT).as_posix()} schreibt Token-Farben von "
            f"Hand: {gefunden} -- tokens.css einbinden und var(...) benutzen, "
            "oder die Seite begründet in AUSGENOMMEN eintragen"
        )


@pytest.mark.parametrize("pfad", sorted(MIGRIERT))
def test_jeder_verweis_auf_die_tokens_zeigt_auf_die_datei(pfad):
    """Ein Tippfehler im Pfad fällt sonst niemandem auf -- die Seite erscheint
    einfach ohne Farben. Der Verweis ist relativ zur verweisenden Datei.

    Dass die Seite überhaupt einen Verweis trägt, steht hier mit: ein eigener
    Test dafür stand einmal daneben, mit einer zweiten, anderen Regex für
    dieselbe Regel.
    """
    quelle = ROOT / pfad
    ziele = token_verweise(quelle.read_text(encoding="utf-8"))
    assert ziele, f"{pfad} verweist gar nicht auf tokens.css"
    for _, ziel in ziele:
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
    erste <style>-Block. Gerechnet wird im kommentarfreien Text, damit ein
    auskommentierter <link> nicht als Verweis zählt.
    """
    text = (ROOT / pfad).read_text(encoding="utf-8")
    if pfad.endswith(".css"):
        # Eine Stilvorlage hat keinen <style>-Block, sie holt die Token per
        # @import -- und das gilt nur als erste Regel der Datei. Steht davor
        # irgendeine Regel, verwirft der Browser es, und alle Seiten, die die
        # Vorlage teilen, stehen ohne Farben da.
        erste_regel = re.match(
            r"""@import\s+url\(\s*["']?([^"')]*)""", ohne_kommentare(text).lstrip()
        )
        assert erste_regel, f"{pfad}: @import der Token ist nicht die erste Regel der Datei"
        gemeint = ((ROOT / pfad).parent / erste_regel.group(1)).resolve()
        assert gemeint == TOKEN_DATEI.resolve(), (
            f"{pfad}: die erste Regel holt {erste_regel.group(1)}, nicht "
            f"{TOKEN_DATEI.name}"
        )
        return
    stil = re.search(r"<style[\s>]", ohne_kommentare(text))
    if stil is None:
        pytest.skip(f"{pfad} hat keinen <style>-Block")
    verweise = token_verweise(text)
    assert verweise, f"{pfad} bindet tokens.css nicht ein"
    assert max(stelle for stelle, _ in verweise) < stil.start(), (
        f"{pfad}: der <link> auf tokens.css steht hinter dem <style>-Block "
        "und übersteuerte dessen Regeln"
    )


# --- Die Helfer selbst ---------------------------------------------------
#
# Sie tragen jeden Wächter oben. Wird einer von ihnen stumpf, werden alle
# gleichzeitig grün, ohne etwas zu bewachen -- in diesem Branch schon
# mehrfach vorgekommen. Darum bekommen sie ihre eigenen Randfälle.

PROBE_CSS = """/* Vorwort, mit :root { --accent: #000 } darin */
:root {
  --accent: #008080;   /* Kommentar im Block */
  --font-body: 'Inter', -apple-system,
               "Segoe UI", sans-serif;
}
@media print {
  :root { --accent: #111111; }
}
html[data-thema="dunkel"] { --bg: #222222; }
"""


@pytest.fixture
def probe(tmp_path):
    datei = tmp_path / "probe.css"
    datei.write_text(PROBE_CSS, encoding="utf-8")
    return datei


def test_ohne_kommentare_raeumt_beide_schreibweisen_weg():
    assert "link" not in ohne_kommentare('<!-- <link href="tokens.css"> -->')
    assert "--accent" not in ohne_kommentare(":root{/* --accent: #008080; */}")


def test_tokens_der_datei_ohne_root_block_ist_leer(tmp_path):
    datei = tmp_path / "ohne.css"
    datei.write_text("body { color: #008080; }\n", encoding="utf-8")
    assert tokens_der_datei(datei) == {}


def test_tokens_der_datei_liest_mehrzeilig_und_ohne_kommentare(probe):
    gelesen = tokens_der_datei(probe)
    assert gelesen == {
        "--accent": "#008080",
        "--font-body": "'Inter', -apple-system, \"Segoe UI\", sans-serif",
    }


def test_tokens_der_datei_sieht_den_zweiten_block_nicht(probe):
    """Festgehalten, nicht bedauert: diese Funktion ist für den Wertvergleich
    von tokens.css da. Für die Frage «setzt die Seite irgendwo einen Token?»
    gibt es `token_deklarationen` -- weil genau diese Blindheit einen Wächter
    grün hielt."""
    assert "--bg" not in tokens_der_datei(probe)


def test_token_deklarationen_sammelt_jeden_block_und_jeden_selektor(probe):
    gelesen = token_deklarationen(probe)
    assert gelesen["--accent"] == ["#008080", "#111111"]
    assert gelesen["--bg"] == ["#222222"]
    assert set(gelesen) == {"--accent", "--font-body", "--bg"}


def test_token_deklarationen_ohne_block_ist_leer(tmp_path):
    datei = tmp_path / "leer.css"
    # Mit Klammern, sonst waere der Test auch ohne `ohne_kommentare` gruen:
    # ohne Block gaebe es nichts zu finden, und die Kommentarbehandlung
    # truege nichts bei.
    datei.write_text("/* :root { --accent: #008080; } */\n", encoding="utf-8")
    assert token_deklarationen(datei) == {}


@pytest.mark.parametrize(
    "schnipsel, erwartet",
    [
        ('<link rel="stylesheet" href="tokens.css">', ["tokens.css"]),
        ("<link rel='stylesheet' href='../tokens.css'>", ["../tokens.css"]),
        # Der Fall, der den Wächter grün hielt: der ganze Wert muss kommen.
        ('<link href="tokens.css.bak">', ["tokens.css.bak"]),
        ('<!-- <link href="tokens.css"> -->', []),
        ('@import url("tokens.css");', ["tokens.css"]),
        ("@import url(tokens.css);", ["tokens.css"]),
        ('@import "tokens.css";', ["tokens.css"]),
        # Eine andere Stilvorlage ist kein Verweis auf die Token.
        ('<link rel="stylesheet" href="stil.css">', []),
    ],
)
def test_token_verweise_faengt_den_ganzen_attributwert(schnipsel, erwartet):
    assert [ziel for _, ziel in token_verweise(schnipsel)] == erwartet
