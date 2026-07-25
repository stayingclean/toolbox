# Toolbox

Eine Sammlung eigenständiger, **im Browser laufender HTML-Werkzeuge** – ohne
Installation, ohne Server, ohne Konto. Jede Seite ist eine einzelne HTML-Datei
mit eingebettetem CSS/JavaScript und funktioniert auch komplett offline.

**Live:** https://stayingclean.github.io/toolbox/
(Veröffentlicht via GitHub Pages aus dem Ordner [`docs/`](docs/).)

## Enthaltene Werkzeuge

| Werkzeug | Beschreibung | Link |
|---|---|---|
| **Skillsliste** | Interaktive Skills zur Krisenbewältigung (nach Anspannungsgrad). | [öffnen](https://stayingclean.github.io/toolbox/skillsliste.html) |
| **Budgetvorlage** | Einnahmen & Ausgaben erfassen, mehrere Varianten vergleichen, drucken. | [öffnen](https://stayingclean.github.io/toolbox/budgetvorlage.html) |
| **Flyer-Editor** | Flyer direkt im Browser gestalten und als HTML-Datei speichern. | [öffnen](https://stayingclean.github.io/toolbox/neutral_flyer.html) |

---

## Flyer-Editor

Ein **vollständiger Flyer-Baukasten in einer einzigen HTML-Datei**. Öffnen,
gestalten, als neue HTML-Datei speichern – fertig. Der Editor und alle Bilder
sind in der Datei eingebettet; es wird nichts nachgeladen.

| Vorderseite | Rückseite |
|:---:|:---:|
| <img src="assets/neutral_flyer_vorderseite.png" alt="Flyer Vorderseite" width="360"> | <img src="assets/neutral_flyer_rueckseite.png" alt="Flyer Rückseite" width="360"> |

### Funktionen im Detail

- **Texte bearbeiten**
  Position, **Schriftart**, **Schriftgrösse** und **Farbe** aller Texte ändern.
  Sämtliche Inhalte lassen sich frei anpassen – vom Titel bis zur Fusszeile.

- **Gestaltung frei positionieren**
  Alle Textelemente lassen sich **frei auf dem Flyer platzieren**. Verschiedene
  Schriftarten kombinieren und das Layout individuell gestalten.

- **Vorder- & Rückseite tauschen**
  Wechsle Vorder- und Rückseite mit **einem Klick** – praktisch, um beide Seiten
  aufeinander abzustimmen.

- **Foto-Einpassung (3 Modi)**
  Für jedes Bild wählbar, wie es in seinen Rahmen eingepasst wird:
  - **Original** – kein Zuschnitt, Bild in Originalproportion.
  - **Füllen (Cover)** – füllt den Rahmen vollständig, schneidet Überstand ab.
  - **Einpassen (Contain)** – zeigt das ganze Bild, ohne zu beschneiden.

- **Format wählen**
  Definiere das Flyer-Format:
  - **A4 Hochformat**
  - **A5 Hochformat**
  - **A4 Querformat**
  - **A5 Querformat**
  - oder **benutzerdefiniert** (eigene Masse)

- **Änderungen speichern**
  Speichere deinen Flyer als **neue HTML-Datei**. Diese kannst du jederzeit
  wieder öffnen und **beliebig oft weiter anpassen** – dein Zwischenstand bleibt
  erhalten.

- **Kein Download. Keine Installation.**
  Öffne die HTML-Datei einfach im Browser und leg los. Es wird keine Software,
  kein Konto und keine Internetverbindung benötigt.

### So nutzt du ihn

1. [Flyer-Editor öffnen](https://stayingclean.github.io/toolbox/neutral_flyer.html)
   (oder die HTML-Datei lokal im Browser öffnen).
2. Texte, Bilder, Format und Layout nach Wunsch anpassen.
3. Über **💾 Speichern** die fertige Datei als neue HTML-Datei sichern.
4. Zum Weiterbearbeiten die gespeicherte Datei erneut im Browser öffnen.

---

## Für Entwickler / Pflege

- Quelle liegt im Wurzelverzeichnis, das veröffentlichte Ergebnis in [`docs/`](docs/).
- Die **Skillsliste** wird generiert (`skills_daten.xlsx` → `build.bat` /
  `uv run build.py` → `docs/skillsliste.html`); Details in
  [`ANLEITUNG.md`](ANLEITUNG.md).
- Konventionen für neue Seiten (Neutralisierung, eingebettetes CSS, Urheber-Credit
  in der Fusszeile) sind in [`CLAUDE.md`](CLAUDE.md) dokumentiert.
