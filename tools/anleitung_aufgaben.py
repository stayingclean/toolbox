"""Trägt die Aufgaben aus stayingclean/ki-tasks in die Anleitung ein.

Aufruf (im Deploy, nachdem ki-tasks/anleitung/ nach docs/claude-anleitung/
kopiert wurde):

    python tools/anleitung_aufgaben.py _ki-tasks docs/claude-anleitung

Namenskonvention drüben: Zu jedem Ordner aufgaben/<name>/ mit INFO.md gehört
die Seite anleitung/<name>.html. Aus diesen beiden Dateien entsteht hier:

- die Gruppe «Aufgaben» in SEITEN (anleitung.js), zwischen den Markern
  AUFGABEN-ANFANG und AUFGABEN-ENDE. Titel = <h1> der Seite.
- die Karten auf aufgaben.html, zwischen <!-- AUFGABEN-KARTEN --> und
  <!-- /AUFGABEN-KARTEN -->. Titel = <h1>, Text = <p class="lead"> der Seite.

Reihenfolge: `reihenfolge:` aus INFO.md, dann Name.

Eine Aufgabe ohne Seite wird ausgelassen (drüben verlinkt die Download-Seite
dann direkt aufs Zip) und nur gemeldet. Eine Seite in anleitung/, die danach in
keiner Navigation steht, bricht ab: Sie wäre unerreichbar, und das fällt sonst
niemandem auf.

Keine Abhängigkeiten ausser Python, damit der Schritt im Deploy ohne
Installation läuft.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

JS_ANFANG = "/* AUFGABEN-ANFANG */"
JS_ENDE = "/* AUFGABEN-ENDE */"
HTML_ANFANG = "<!-- AUFGABEN-KARTEN -->"
HTML_ENDE = "<!-- /AUFGABEN-KARTEN -->"


class KonventionFehler(Exception):
    pass


def lies_info(datei: Path) -> dict[str, str]:
    """Dieselbe Lesart wie build.py drüben: `schluessel: wert` pro Zeile."""
    info: dict[str, str] = {}
    for zeile in datei.read_text(encoding="utf-8").splitlines():
        if ":" in zeile:
            k, v = zeile.split(":", 1)
            info[k.strip()] = v.strip()
    return info


def text_aus(seite: str, muster: str, datei: Path) -> str:
    treffer = re.search(muster, seite, re.S)
    if not treffer:
        raise KonventionFehler(f"{datei.name}: {muster!r} nicht gefunden")
    # Tags entfernen, Entitäten auflösen, Leerraum glätten
    roh = re.sub(r"<[^>]+>", "", treffer.group(1))
    return " ".join(html.unescape(roh).split())


def lies_aufgaben(ki_tasks: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Gibt die Aufgaben mit Seite zurück, dazu Meldungen zu denen ohne."""
    aufgaben, meldungen = [], []
    for info_datei in sorted((ki_tasks / "aufgaben").glob("*/INFO.md")):
        name = info_datei.parent.name
        info = lies_info(info_datei)
        seite = ki_tasks / "anleitung" / f"{name}.html"
        if not seite.exists():
            meldungen.append(f"Aufgabe {name} hat keine Seite anleitung/{name}.html")
            continue
        quelltext = seite.read_text(encoding="utf-8")
        aufgaben.append({
            "name": name,
            "href": f"{name}.html",
            "titel": text_aus(quelltext, r"<h1[^>]*>(.*?)</h1>", seite),
            "lead": text_aus(quelltext, r'<p class="lead"[^>]*>(.*?)</p>', seite),
            "reihenfolge": info.get("reihenfolge", "1000"),
        })
    aufgaben.sort(key=lambda a: (int(a["reihenfolge"]), a["name"]))
    return aufgaben, meldungen


def js_zeichenkette(text: str) -> str:
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"


def seiten_js(aufgaben: list[dict[str, str]], einzug: str) -> str:
    breite = max(len(js_zeichenkette(a["href"])) for a in aufgaben) + 1
    zeilen = [
        f"{einzug}{{ href: {(js_zeichenkette(a['href']) + ',').ljust(breite)} "
        f"titel: {js_zeichenkette(a['titel'])} }}"
        for a in aufgaben
    ]
    return ",\n".join(zeilen)


def karten_html(aufgaben: list[dict[str, str]], einzug: str) -> str:
    teile = []
    for a in aufgaben:
        teile.append(
            f'{einzug}<div class="card">\n'
            f'{einzug}  <h3><a href="{html.escape(a["href"])}">{html.escape(a["titel"])}</a></h3>\n'
            f'{einzug}  <p>{html.escape(a["lead"], quote=False)}</p>\n'
            f"{einzug}</div>"
        )
    return "\n".join(teile)


def ersetze_zwischen(text: str, anfang: str, ende: str, neu: str, datei: str) -> str:
    """Ersetzt alles zwischen den Markern. Die Marker selbst bleiben stehen;
    der Einzug vor dem End-Marker bleibt erhalten."""
    if text.count(anfang) != 1 or text.count(ende) != 1:
        raise KonventionFehler(f"{datei}: Marker {anfang} / {ende} fehlen oder doppelt")
    kopf, rest = text.split(anfang, 1)
    _, fuss = rest.split(ende, 1)
    einzug_ende = re.search(r"[ \t]*$", kopf).group(0)
    return f"{kopf}{anfang}\n{neu}\n{einzug_ende}{ende}{fuss}"


def einzug_nach(text: str, marker: str) -> str:
    """Einzug der Zeile, auf der der Marker steht: Die Einträge stehen bündig darunter."""
    if marker not in text:
        raise KonventionFehler(f"Marker {marker} fehlt")
    zeile = text[: text.index(marker)].rsplit("\n", 1)[-1]
    return re.match(r"[ \t]*", zeile).group(0)


def verlinkte_seiten(js: str) -> set[str]:
    return set(re.findall(r"href:\s*'([^']+)'", js))


def einsetzen(ki_tasks: Path, ziel: Path) -> tuple[list[str], list[str]]:
    """Gibt die eingetragenen Seiten und die Warnungen zurück."""
    aufgaben, meldungen = lies_aufgaben(ki_tasks)
    if not aufgaben:
        raise KonventionFehler("keine einzige Aufgabe mit Seite gefunden")

    js_datei = ziel / "anleitung.js"
    js = js_datei.read_text(encoding="utf-8")
    einzug = einzug_nach(js, JS_ANFANG)
    # Vor dem Anfangs-Marker steht die Übersicht samt Komma; der letzte Eintrag hat keins
    js = ersetze_zwischen(js, JS_ANFANG, JS_ENDE, seiten_js(aufgaben, einzug), js_datei.name)
    js_datei.write_text(js, encoding="utf-8")

    html_datei = ziel / "aufgaben.html"
    seite = html_datei.read_text(encoding="utf-8") if html_datei.exists() else ""
    if HTML_ANFANG not in seite:
        # Die Übersicht gehört ki-tasks; ohne Marker bleibt sie, wie sie ist
        meldungen.append(f"{html_datei.name} ohne Marker {HTML_ANFANG}, Karten nicht ersetzt")
    else:
        seite = ersetze_zwischen(
            seite, HTML_ANFANG, HTML_ENDE,
            karten_html(aufgaben, einzug_nach(seite, HTML_ANFANG)), html_datei.name,
        )
        html_datei.write_text(seite, encoding="utf-8")

    # Jede Seite aus ki-tasks muss in der Navigation stehen
    verlinkt = verlinkte_seiten(js)
    verwaist = sorted(
        p.name for p in (ki_tasks / "anleitung").glob("*.html") if p.name not in verlinkt
    )
    if verwaist:
        raise KonventionFehler(
            "Seiten ohne Eintrag in SEITEN: " + ", ".join(verwaist)
            + " — Aufgabe ohne aufgaben/<name>/INFO.md oder fehlt in anleitung.js"
        )
    return [f"{a['href']}: {a['titel']}" for a in aufgaben], meldungen


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    try:
        eingetragen, meldungen = einsetzen(Path(argv[1]), Path(argv[2]))
    except KonventionFehler as e:
        print(f"::error::{e}")
        return 1
    for z in eingetragen:
        print(z)
    for z in meldungen:
        print(f"::warning::{z}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
