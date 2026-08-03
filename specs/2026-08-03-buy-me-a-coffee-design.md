# Buy-me-a-coffee-Hinweis in allen Seiten + Flyer-Umbenennung

Datum: 2026-08-03 · Branch: `feature/buy-me-a-coffee`

## Ziel

Zwei Dinge in einem Zug:

1. Jede veröffentlichte Seite in `docs/` bekommt in der Fusszeile einen Hinweis auf
   den Buy-me-a-coffee-Account — neben dem bestehenden Urheber-Credit.
2. `docs/neutral_flyer.html` heisst künftig `docs/flyer-editor.html`; die
   zugehörigen Screenshots heissen `flyer_vorderseite.png` / `flyer_rueckseite.png`.

## Link-Ziel

`https://buymeacoffee.com/stayingclean`

**Offener Punkt:** Diese URL liefert zum Zeitpunkt der Umsetzung noch **404** — das
Konto ist noch nicht angelegt bzw. nicht veröffentlicht. Der Link ist bewusst schon
eingebaut und funktioniert, sobald das Konto existiert. Vor dem Merge nach `master`
prüfen, ob die Seite erreichbar ist.

## Markup-Konvention

Der bestehende `.footer-credit` und der neue `.footer-coffee` stehen zusammen in
einem flexiblen Container, damit auf schmalen Bildschirmen sauber umgebrochen wird:

```html
<div class="footer-links">
  <a class="footer-credit" href="https://github.com/stayingclean" target="_blank" rel="noopener">
    <img class="footer-avatar" src="https://github.com/stayingclean.png?size=80"
         alt="stayingclean" loading="lazy" width="28" height="28">
    <span>Erstellt von stayingclean</span>
  </a>
  <span class="footer-sep" aria-hidden="true">·</span>
  <a class="footer-coffee" href="https://buymeacoffee.com/stayingclean" target="_blank" rel="noopener">
    <span aria-hidden="true">☕</span><span>Kaffee spendieren</span>
  </a>
</div>
```

Dazu dieses CSS (Farben und Abstände an das Theme der jeweiligen Seite anpassen):

```css
.footer-links{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;margin-top:12px}
.footer-credit{margin-top:0}                    /* Abstand wandert in den Container */
.footer-coffee{display:inline-flex;align-items:center;gap:6px;
  color:var(--muted);text-decoration:none;transition:color .15s ease}
.footer-coffee:hover{color:var(--accent)}
@media (max-width:480px){.footer-sep{display:none}}
```

Begründung der Entscheidungen:

- **Emoji statt offiziellem BMC-Button.** Kein externes Bild und kein zusätzliches
  Base64 — jede Seite bleibt offline lauffähig und self-contained. Das gelbe
  Original passt zudem farblich zu keinem der Seiten-Themes.
- **Separator als eigenes `<span>`, unter 480 px ausgeblendet.** Sonst bleibt nach
  dem Zeilenumbruch ein baumelndes „·" am Ende der ersten Zeile stehen.
- **Kein `aria-label`.** Der sichtbare Text „Kaffee spendieren" ist bereits der
  Linktext; das Emoji ist mit `aria-hidden` von der Vorlesung ausgenommen.

## Betroffene Dateien

| Datei | Fusszeile | Anmerkung |
|---|---|---|
| `docs/index.html` | `<footer>` | Übersicht |
| `docs/asrs-v1-1.html` | `<footer class="colophon">` | |
| `docs/budgetvorlage.html` | `<footer class="footer">` | |
| `docs/flyer-editor.html` | `<footer class="site-credit">` | siehe Abschnitt Flyer |
| `template.html` | `<footer>` | Quelle für `docs/skillsliste.html` |
| `template-vorschlag.html` | `<footer>` | Quelle für `docs/skill-vorschlagen.html` |

`docs/skillsliste.html` und `docs/skill-vorschlagen.html` werden **nicht** von Hand
editiert, sondern nach der Template-Änderung über `build.bat` (`uv run build.py`)
neu erzeugt.

**Bewusst nicht angefasst:** `docs/budgetvorlag_aktuell.html` — alte Restdatei,
nirgends verlinkt und schon heute ohne Urheber-Credit. Ob sie gelöscht oder
mitgepflegt wird, ist eine separate Entscheidung.

## Flyer-Editor: Wohin mit dem Hinweis

Die Datei hat am Ende von `<body>` bereits einen `<footer class="site-credit">` mit
Base64-eingebettetem Avatar. Dieser Footer liegt **ausserhalb** von `#sheets`.
Daraus ergibt sich ohne Sonderbehandlung genau das gewünschte Verhalten:

| Kontext | Hinweis sichtbar | Warum |
|---|---|---|
| Editor-Ansicht | ja | normaler Seiteninhalt |
| „Speichern" (Arbeitskopie) | ja | vollständiger DOM-Klon |
| „Ansicht-HTML" (fertiger Flyer) | ja | `.site-credit` steht nicht in der `kill`-Liste von `doExportHtml` |
| „Bild speichern" (PNG/JPG) | nein | `pageToSvg` klont nur `.page` |
| Drucken / PDF | nein | `@media print{.site-credit{display:none!important}}` |

Der Hinweis landet also nie auf dem gedruckten oder als Bild exportierten Flyer des
Benutzers.

Der Flyer ist der eine Sonderfall beim Markup: `.site-credit` **ist** bereits der
Flex-Container, ein zusätzliches `.footer-links` entfällt. Der Kaffee-Link wird als
zweites `<a>` direkt hineingehängt und erbt das vorhandene `.site-credit a`-CSS;
ergänzt wird nur `flex-wrap:wrap` am Container und `.footer-sep` samt der
480-px-Regel. Ein eigener `.footer-coffee`-Block ist hier nicht nötig.

## Umbenennung

```
docs/neutral_flyer.html              → docs/flyer-editor.html
assets/neutral_flyer_vorderseite.png → assets/flyer_vorderseite.png
assets/neutral_flyer_rueckseite.png  → assets/flyer_rueckseite.png
```

Alles per `git mv`, damit die Historie erhalten bleibt.

Nachzuziehende Verweise:

- `docs/index.html` — Karte „Flyer-Editor" (`href`)
- `README.md` — Tabellenzeile mit Link, Screenshot-Tabelle, Anleitungsschritt
- `CLAUDE.md` — Abschnitt „Aufbau"
- `docs/flyer-editor.html` — interner Download-Name der Arbeitskopie:
  `neutral_flyer_bearbeitet.html` → `flyer-bearbeitet.html` (passt zum bereits
  vorhandenen `flyer-ansicht.html`)

Der `<title>` („Flyer-Editor – Neutrale Vorlage (stayingclean)") bleibt unverändert;
„neutrale Vorlage" beschreibt weiterhin korrekt den Inhalt.

### Weiterleitung der alten URL

`https://stayingclean.github.io/toolbox/neutral_flyer.html` wurde möglicherweise
schon geteilt. Deshalb bleibt unter dem alten Namen eine winzige Weiterleitungsseite
stehen:

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Flyer-Editor – verschoben</title>
  <link rel="canonical" href="flyer-editor.html">
  <meta http-equiv="refresh" content="0; url=flyer-editor.html">
</head>
<body>
  <p>Diese Seite heisst jetzt <a href="flyer-editor.html">flyer-editor.html</a>.</p>
</body>
</html>
```

Diese Stub-Datei ist von der Credit-Konvention ausgenommen — sie ist keine Inhalts-
seite, sondern nur eine Weiche, und wird typischerweise nie gesehen.

## Dokumentation

`CLAUDE.md` bekommt im Abschnitt „Konvention: Fusszeile mit Urheber-Credit" den
Kaffee-Link als Teil der Konvention ergänzt, damit künftige Seiten ihn von Anfang an
mitbringen. Die Überschrift wird zu „Konvention: Fusszeile mit Urheber-Credit und
Kaffee-Link".

## Prüfung

1. `uv run pytest` — die bestehenden Build-Tests müssen grün bleiben.
2. Nach `build.bat` prüfen, dass `docs/skillsliste.html` und
   `docs/skill-vorschlagen.html` den neuen Footer enthalten.
3. Alle sechs Seiten lokal im Browser öffnen: Fusszeile korrekt, Link-Ziel korrekt,
   Umbruch bei schmalem Fenster ohne baumelndes „·".
4. Beim Flyer zusätzlich: „Speichern", „Ansicht-HTML" und „Bild speichern" auslösen
   und in den erzeugten Dateien nachsehen, dass sich der Hinweis wie in der Tabelle
   oben verhält.
5. `grep -rn "neutral_flyer"` darf ausser in der Weiterleitungsdatei und in älteren
   Spec-Dokumenten keine Treffer mehr liefern.

## Abschluss

Commit auf `feature/buy-me-a-coffee`, Push, Pull Request. Der Merge nach `master`
erfolgt durch den Benutzer.
