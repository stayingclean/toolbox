"""Duplikatpruefung fuer neue Skill-Vorschlaege (optional, per KI).

Dieses Modul kennt weder Excel noch GitHub noch die Konsolenfuehrung. Es
beantwortet genau eine Frage: „Aehnelt einer dieser neuen Vorschlaege einem
Skill, den es schon gibt?" — und liefert die Treffer zurueck.

Die Pruefung ist eine ZUTAT, keine Voraussetzung: Ohne Schluessel oder bei
einem Fehler der Schnittstelle laeuft die Uebernahme unveraendert weiter.
"""

import json
import os
import subprocess
from pathlib import Path

MODELL = "claude-opus-5"
VARIABLE = "ANTHROPIC_API_KEY"

PROJEKT = Path(__file__).resolve().parent.parent
PROMPT_DATEI = "duplikat_prompt.md"

# Anzeige-Name je Stufenschluessel, damit die KI dieselben Woerter sieht wie
# der Mensch in der Excel.
STUFEN_NAME = {"hoch": "Hoch", "mittel": "Mittel", "tief": "Tief"}

# Rueckfall-Muster, falls Git nicht befragt werden kann (kein Repo, kein Git
# installiert). Ohne Git gibt es aber auch kein `git add -A` -- deshalb darf
# der Rueckfall grosszuegiger sein als eine echte .gitignore-Auswertung.
_RUECKFALL_MUSTER = (".env", ".env*", "*.env", "/.env", "**/.env")


def _von_git_ignoriert(projekt: Path) -> bool | None:
    """Fragt Git direkt, ob `.env` ignoriert wird. None, wenn nicht ermittelbar.

    Nur Git kennt Negationen (`!.env`), Pfadanker (`/.env`) und `**`
    zuverlaessig -- ein Nachbau als Zeichenkettenvergleich uebersieht genau
    die Faelle, die hier sicherheitsrelevant sind (z. B. `.env*` gefolgt von
    `!.env`, was die Datei am Ende doch NICHT schuetzt).
    """
    try:
        ergebnis = subprocess.run(
            ["git", "check-ignore", "--quiet", ".env"],
            cwd=projekt,
            capture_output=True,
        )
    except OSError:
        return None
    if ergebnis.returncode == 0:
        return True
    if ergebnis.returncode == 1:
        return False
    return None  # z. B. kein Git-Repo (Exit-Code 128) -> Rueckfall


def _env_datei_lesen(pfad: Path) -> str | None:
    """Sucht den Schluessel in einer .env-Datei. Kein Fremdpaket noetig."""
    try:
        inhalt = pfad.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Keine Byte-Vorschau in der Meldung durchreichen (koennte
        # Schluesselmaterial zeigen) -- deshalb `from None` statt der
        # verketteten Ausnahme.
        raise SystemExit(
            "❌ Die Datei .env laesst sich nicht als Text lesen (kein\n"
            "   gueltiges UTF-8).\n\n"
            "   Pruefe die Datei von Hand. Es wurde nichts veraendert."
        ) from None
    for zeile in inhalt.splitlines():
        zeile = zeile.strip()
        # `zeile.startswith("#")` ist mit der heutigen Vergleichslogik durch
        # keinen Test einzeln nachweisbar: Nach partition("=") enthaelt der
        # Namensteil einer auskommentierten Zeile das "#" immer noch
        # ("# ANTHROPIC_API_KEY" != "ANTHROPIC_API_KEY"), also kann eine
        # auskommentierte Zuweisung sowieso nie treffen -- mit oder ohne
        # diese Bedingung. Sie bleibt trotzdem stehen: Sie ist die zweite
        # Schutzebene, falls die Vergleichslogik hier spaeter mal
        # nachsichtiger wird (z. B. Gross-/Kleinschreibung ignoriert). Das
        # ist bewusst so und keine Testluecke.
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        name, _, wert = zeile.partition("=")
        if name.strip() == VARIABLE:
            return wert.strip().strip('"').strip("'") or None
    return None


def schluessel_finden(projekt: Path) -> str | None:
    """Erst die Umgebungsvariable, sonst die .env-Datei. Sonst None.

    None heisst NICHT Fehler: Ohne Schluessel entfaellt die Pruefung
    kommentarlos, und das Uebernahme-Skript laeuft wie sonst auch.
    """
    aus_umgebung = os.environ.get(VARIABLE, "").strip()
    if aus_umgebung:
        return aus_umgebung

    env = projekt / ".env"
    if not env.exists():
        return None

    # Notbremse: Das Uebernahme-Skript schlaegt am Ende woertlich `git add -A`
    # vor. Deckt .gitignore die Datei nicht ab, waere der Schluessel mit einem
    # Befehl oeffentlich — und ein veroeffentlichter Schluessel laesst sich
    # nicht zurueckholen, nur sperren. Deshalb wird nach Moeglichkeit Git
    # selbst gefragt statt die Regeln nachzubauen (siehe _von_git_ignoriert).
    git_ergebnis = _von_git_ignoriert(projekt)
    if git_ergebnis is not None:
        geschuetzt = git_ergebnis
    else:
        gitignore = projekt / ".gitignore"
        # `errors="replace"` statt eines Absturzes: Fuer die Notbremse zaehlt
        # nur, ob eine der Schutzzeilen dasteht. Eine .gitignore mit einer
        # kaputten Stelle (BOM-Reste, ANSI-Zeichen aus einem alten Editor)
        # warf hier sonst einen rohen UnicodeDecodeError durch -- waehrend
        # dasselbe Problem an der .env sauber abgefangen wird. Eine ersetzte
        # Stelle kann eine Schutzzeile hoechstens unkenntlich machen, und dann
        # wird angehalten statt durchgewinkt.
        geschuetzt = gitignore.exists() and any(
            zeile.strip() in _RUECKFALL_MUSTER
            for zeile in gitignore.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()
        )
    if not geschuetzt:
        # Bewusst im Konjunktiv: Geprueft wurde nur, DASS eine .env daliegt --
        # gelesen wird sie erst danach (_env_datei_lesen). Eine leere .env
        # oder eine mit ganz anderen Eintraegen loest dieselbe Meldung aus.
        # „enthaelt einen Schluessel" waere dort schlicht falsch und macht der
        # Zielgruppe unnoetig Angst („was fuer ein Schluessel?").
        raise SystemExit(
            "❌ Im Projektordner liegt eine Datei .env, die nicht vor Git\n"
            "   geschuetzt ist. Sie koennte einen Schluessel enthalten.\n\n"
            "   Trage in .gitignore eine Zeile `.env*` ein und starte noch\n"
            "   einmal. Ohne diesen Schutz koennte der Schluessel mit dem\n"
            "   naechsten Commit oeffentlich werden.\n\n"
            "   Es wurde nichts veraendert."
        )

    return _env_datei_lesen(env)


def lade_prompt(projekt: Path) -> str:
    """Liest den Anweisungstext aus tools/duplikat_prompt.md.

    Die Datei enthaelt NUR die Anweisungen, nicht die Daten. Bestand und neue
    Vorschlaege setzt der Code als eigene Nachricht zusammen. So kann die Datei
    frei umformuliert werden, ohne dass ein Platzhalter kaputtgeht.
    """
    pfad = projekt / "tools" / PROMPT_DATEI
    if not pfad.exists():
        raise SystemExit(
            f"❌ Die Datei tools/{PROMPT_DATEI} fehlt.\n\n"
            "   In ihr steht, wonach die Duplikatpruefung suchen soll. Ohne sie\n"
            "   kann nicht geprueft werden. Hol die Datei aus dem Repo zurueck\n"
            "   (git checkout tools/) oder nimm den Schluessel weg, dann\n"
            "   entfaellt die Pruefung.\n\n"
            "   Es wurde nichts veraendert."
        )
    text = pfad.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(
            f"❌ Die Datei tools/{PROMPT_DATEI} ist leer.\n\n"
            "   Ohne Anweisung liefert die Pruefung unbrauchbare Ergebnisse.\n"
            "   Bitte den Text wiederherstellen (git checkout tools/).\n\n"
            "   Es wurde nichts veraendert."
        )
    return text


def bestand_als_text(bestand: dict) -> str:
    """Der vorhandene Bestand als kompakte Zeilenliste.

    Trennzeichen zwischen Titel und Beschreibung ist `|`, nicht der
    Gedankenstrich: 21 von 100 echten Beschreibungen (Feld `b`) enthalten
    selbst einen Gedankenstrich (docs/skills-daten.json), ein Gedankenstrich
    waere also keine eindeutige Grenze. `|` kommt in keinem der Felder
    e/t/b/tip/von/erg im echten Bestand vor -- geprueft gegen
    docs/skills-daten.json (100 Skills, Stand dieser Aenderung).
    """
    zeilen = []
    for schluessel, stufe in bestand.items():
        name = STUFEN_NAME.get(schluessel, schluessel)
        for kategorie in stufe.get("kategorien", []):
            for skill in kategorie.get("skills", []):
                zeilen.append(
                    f"{name} / {kategorie['label']}: {skill['t']} | {skill['b']}"
                )
    return "\n".join(zeilen)


# Festes Antwortschema: So kann die Antwort nicht als Fliesstext zurueckkommen,
# den wir dann raten muessten.
SCHEMA = {
    "type": "object",
    "properties": {
        "treffer": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "titel": {"type": "string"},
                    "aehnlich_zu": {"type": "string"},
                    "stufe": {"type": "string"},
                    "kategorie": {"type": "string"},
                    "begruendung": {"type": "string"},
                    "sicherheit": {"type": "string", "enum": ["sicher", "unsicher"]},
                },
                "required": ["titel", "aehnlich_zu", "stufe", "kategorie", "begruendung", "sicherheit"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["treffer"],
    "additionalProperties": False,
}

PFLICHTFELDER = ("titel", "aehnlich_zu", "stufe", "kategorie", "begruendung")

# Das Schema verlangt diese beiden Werte bereits. Der Filter prueft sie trotzdem
# noch einmal: Das Schema bindet die KI, nicht die Antwort, die bei uns ankommt —
# ein erfundener dritter Wert wuerde sonst wie "sicher" behandelt.
#
# "sicherheit" steht absichtlich NICHT in PFLICHTFELDER: Dort wuerde nur auf
# Anwesenheit als nichtleere Zeichenkette geprueft. Die Zeile unten prueft
# strenger -- auf einen der beiden erlaubten Werte --, und deckt die
# Anwesenheitspruefung damit vollstaendig mit ab. Eine zusaetzliche Nennung in
# PFLICHTFELDER waere eine Pruefung, die nie greifen kann, solange die
# strengere daneben steht -- keine echte zweite Schutzebene, nur ihr Anschein.
SICHERHEITSSTUFEN = ("sicher", "unsicher")


def client_bauen(schluessel: str):
    """Baut den Anthropic-Client. Der Import steht absichtlich hier drin:

    Ohne Schluessel wird die Funktion nie gerufen, und dann muss das Paket
    `anthropic` auch nicht installiert sein.
    """
    import anthropic

    return anthropic.Anthropic(api_key=schluessel)


def _anfrage_text(neue: list, bestand: dict) -> str:
    # Gleiches Trennzeichen wie bestand_als_text (`|` statt Gedankenstrich):
    # sonst staenden in derselben Anfrage zwei verschiedene Zeilenformate, und
    # der Gedankenstrich kommt in echten Beschreibungen selbst vor (siehe
    # Kommentar dort).
    zeilen = ["## Vorhanden", bestand_als_text(bestand), "", "## Neu"]
    for v in neue:
        zeilen.append(
            f"{v['stufe']} / {v['kategorie']}: {v['titel']} | {v['beschreibung']}"
        )
    return "\n".join(zeilen)


def pruefe_duplikate(neue: list, bestand: dict, client) -> list:
    """Fragt die KI, welche neuen Vorschlaege es schon gibt.

    Liefert IMMER eine Liste. Geht beim Aufruf ODER beim Auswerten der Antwort
    etwas schief, ist sie leer und der Lauf geht ohne Pruefung weiter — die
    Pruefung ist eine Zutat, keine Voraussetzung. Deshalb steckt die gesamte
    Auswertung mit im selben try-Block wie der Aufruf: eine leere/fehlende
    `content`-Liste oder ein unlesbarer Block sind genauso ein
    Schnittstellenfehler wie ein abgebrochenes Netz.
    """
    if not neue:
        return []

    # lade_prompt() kann SystemExit ausloesen (fehlende/leere Prompt-Datei).
    # SystemExit erbt nicht von Exception -- es landet also nie im
    # except-Zweig unten, sondern schlaegt von selbst durch. Ein eigener
    # "except SystemExit: raise" waere deshalb reine Attrappe (wurde in
    # einer frueheren Fassung entfernt, nachdem eine Pruefung genau das
    # gezeigt hat).
    try:
        antwort = client.messages.create(
            model=MODELL,
            max_tokens=2000,
            system=lade_prompt(PROJEKT),
            messages=[{"role": "user", "content": _anfrage_text(neue, bestand)}],
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        )

        # `messages.create()` liefert TextBlock-Inhalte, KEINE ParsedTextBlock
        # -- ein `parsed_output`-Feld existiert auf diesem Weg nicht (geprueft
        # gegen anthropic 0.120.2). Nur `messages.parse()` erzeugt
        # ParsedTextBlock mit echtem `parsed_output`, verlangt dafuer aber
        # einen Python-Typ als `output_format` statt eines rohen
        # JSON-Schemas -- ein groesserer Umbau, der hier nicht ansteht.
        # Ausgewertet wird deshalb ausschliesslich der Text.
        block = antwort.content[0]
        nutzlast = json.loads(block.text)

        roh = nutzlast.get("treffer") if isinstance(nutzlast, dict) else None
        if not isinstance(roh, list):
            return []

        # Nur vollstaendige Treffer: ein halber Treffer wuerde beim
        # Nachfragen eine luecken hafte Zeile ergeben, die niemand einordnen
        # kann. Ist ein Eintrag gar kein Objekt (z. B. eine Zeichenkette
        # statt eines Treffer-dicts), faellt er hier ebenfalls raus, ohne
        # dass `.get(...)` je aufgerufen wird.
        #
        # Geprueft wird der TYP, nicht nur das Vorhandensein: `str(...)` machte
        # aus JEDEM Wert eine nichtleere Zeichenkette -- `str(["x"])` ist
        # "['x']", `str(None)` ist "None", beides wahrheitswert-wahr. Ein
        # `titel`, der keine Zeichenkette ist, ueberlebte so den Filter und
        # wurde beim Nachfragen als dict-Schluessel benutzt: `TypeError:
        # unhashable type: 'list'`, roher Traceback, ganzer Uebernahmelauf tot.
        # Das Schema verlangt zwar ueberall "string", erzwingen laesst sich das
        # aber nicht -- deshalb hier.
        return [
            t for t in roh
            if isinstance(t, dict)
            and all(isinstance(t.get(f), str) and t[f].strip() for f in PFLICHTFELDER)
            and t.get("sicherheit") in SICHERHEITSSTUFEN
        ]
    except Exception as fehler:
        # Nur der Typname, nie die Ausnahme selbst oder ihre Argumente in der
        # Meldung: eine Schluessel- oder Netzwerkbibliothek koennte den
        # Schluessel in einer Fehlermeldung mitfuehren (z. B. im Header einer
        # HTTP-Anfrage). str(fehler) wird deshalb bewusst nicht ausgegeben.
        # Dieselbe Meldung deckt jetzt auch eine unerwartete Antwortform ab
        # (leerer/fehlender content, unlesbares JSON) -- fuer den Aufrufer
        # ist beides gleich: die Pruefung fiel aus, der Lauf geht weiter.
        print(
            f"\n⚠ Die Duplikatpruefung wurde uebersprungen: {type(fehler).__name__}.\n"
            "   Die Uebernahme laeuft normal weiter – sie haengt nicht daran.\n"
            "   Moegliche Ursachen: kein Internet, ein nicht mehr gueltiger\n"
            "   Schluessel oder eine unerwartete Antwort der KI."
        )
        return []
