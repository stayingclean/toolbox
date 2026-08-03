# Flyer-Editor: Export als Ansicht-HTML und als Bild

Datum: 2026-08-03 · Branch: `flyer-export` · Betroffene Datei: `docs/neutral_flyer.html`

## Ziel

Der Flyer-Editor kann heute zwei Dinge: eine Arbeitskopie als HTML sichern
(`💾 Speichern`) und drucken (`🖨 Drucken`). Dazu kommen zwei Export-Wege für
fertige Flyer, die weitergegeben oder gepostet werden:

1. **Ansicht-HTML** — der Flyer ohne Editor, nicht mehr veränderbar.
2. **Bild** — Vorder- und Rückseite als PNG oder JPG, in wählbarer Auflösung.

PDF bleibt bewusst aussen vor: `Strg+P` → Ziel „Als PDF speichern" liefert bereits
ein Vektor-PDF, und `@media print` blendet die Bedienelemente dort schon aus.

## Rahmenbedingungen

- Die Datei bleibt **self-contained** (CLAUDE.md): kein externes Stylesheet, keine
  CDN-Bibliothek, Doppelklick-Betrieb ohne Server und ohne Internet.
- Der Flyer bemisst **alle Schriftgrössen in Container-Query-Einheiten**
  (`cqw`/`cqh`, ~55 Stellen, `.page{container-type:size}`). Jede Export-Technik,
  die CSS selbst nachrechnet statt den Browser rendern zu lassen (html2canvas),
  liefert hier falsche Schriftgrössen. Das schliesst diese Klasse von Bibliotheken aus.
- Die Fusszeile mit dem Urheber-Credit bleibt in der exportierten HTML erhalten.

## Bedienung

Die letzte Toolbar-Gruppe wird erweitert:

```
⌨   💾 Speichern   📄 Ansicht-HTML   📷 Bild speichern [PNG ▾] [2× ▾]   🖨 Drucken
```

- `💾 Speichern` bleibt unverändert — die Arbeitsversion zum Weiterbearbeiten.
- Der Bild-Knopf heisst `📷 Bild speichern`, nicht `🖼 Bild`: dieses Label ist in der
  Einfügen-Gruppe bereits für *Bildfeld einfügen* vergeben.
- Keine neuen Tastenkürzel — die F1-Tabelle bleibt so lang wie sie ist.

## Ansicht-HTML

Erzeugt `flyer-ansicht.html` aus einer **Kopie** des Dokuments (die Live-Seite wird
nicht angefasst):

| Was | Behandlung |
|---|---|
| Toolbar, Hinweiszeile, Drag-/Resize-Griffe, Hilfslinien, F1-Hilfe | entfernt |
| alle `<script>`-Blöcke, versteckte `input[type=file]` | entfernt |
| `contenteditable`, `tabindex`, `spellcheck`, `data-ph` an den Feldern | entfernt |
| Zustands-Klassen `active`, `multi`, `isempty` | entfernt |
| Hover-/Fokus-Umrandungen, `cursor:text`, Platzhaltertexte | per CSS-Override neutralisiert |
| `.sheets`-Innenabstand (war auf Toolbar-Höhe gesetzt) | auf festen Wert zurückgesetzt |
| Layout-CSS inkl. dynamischer `@page`-Regel, Fusszeilen-Credit | bleibt |
| `<title>` | wird zu „Flyer" |

Die Datei wird dadurch **nicht wesentlich kleiner** — die eingebetteten
Hintergrundbilder machen ~3,5 MB der ~3,7 MB aus, der Editor-Code nur ~50 KB.
Der Gewinn ist Unveränderbarkeit, nicht Dateigrösse.

## Bild-Export

Ein Klick erzeugt zwei Dateien: `flyer-vorderseite.<ext>` und `flyer-rueckseite.<ext>`.

**Technik** (ohne Fremdbibliothek):

1. Die `.page` wird geklont und von Editor-Zuständen befreit.
2. Der Klon wird per `XMLSerializer` zu XHTML serialisiert und zusammen mit dem
   gesammelten Seiten-CSS (in `<![CDATA[…]]>`) in ein
   `<svg><foreignObject>` verpackt.
3. Die Auflösung wird **in das SVG hineingebacken**: `width`/`height` = Seitenmass ×
   Faktor, dazu `viewBox` auf das Original-Seitenmass. Der Browser rastert dadurch
   direkt in Zielauflösung, statt eine kleine Bitmap hochzuskalieren.
4. Das SVG wird über eine Blob-URL in ein `<img>` geladen und auf ein `<canvas>`
   gezeichnet; `canvas.toBlob` liefert die Datei.

Entscheidend: **der Browser rendert selbst**, deshalb stimmen die `cqw`/`cqh`-Grössen.

- Formate: PNG (verlustfrei) und JPG (Qualität 0.92, mit weiss gefülltem Untergrund,
  da JPG keine Transparenz kennt).
- Faktoren: 1× / 2× (Vorgabe) / 3×. Bei 148×210 mm entspricht das 559×794 px,
  1118×1587 px bzw. 1677×2381 px.
- Die Schärfe des Hintergrundfotos begrenzt das Ergebnis — 3× macht ein gering
  aufgelöstes Hintergrundbild nicht besser.
- Während des Rasterns meldet die bestehende `flash()`-Statuszeile den Fortschritt.
- Die zwei Downloads werden zeitlich versetzt ausgelöst; Chrome fragt beim ersten Mal
  „Mehrere Dateien herunterladen?" — das ist erwartet.

### Bekannte Risiken und Umgang damit

| Risiko | Umgang |
|---|---|
| Blob-URL unter `file://` wird nicht geladen | `img.onerror` → zweiter Versuch mit Data-URI |
| Canvas wird „tainted", `toBlob` wirft `SecurityError` | Fehler abfangen, verständliche Meldung in der Statuszeile statt stiller Fehlschlag |
| Safari rendert `foreignObject`-in-SVG unzuverlässig | Zielbrowser sind Chrome/Edge/Firefox; Einschränkung wird dokumentiert, nicht kaschiert |
| Fällt die Technik ganz durch | Rückfallplan: `html-to-image` (MIT, ~30 KB) inline einbetten — gleiche Technik, mehr Sonderfall-Behandlung |

## Aufbau im Code

Beide Exporte teilen sich Hilfsfunktionen, damit die Logik nur einmal existiert:

- `stripEditorState(root)` — entfernt Editor-Attribute und -Klassen an einem Klon
- `collectCss()` — sammelt alle `<style>`-Inhalte des Dokuments
- `downloadBlob(blob, name)` — ein Download-Weg für alle drei Speicher-Funktionen
- `EXPORT_CSS` — die neutralisierenden Regeln, von beiden Exporten genutzt

`doSave()` (die bestehende Arbeitskopie) wird auf `downloadBlob` umgestellt, sonst
aber nicht angefasst.

## Verifikation

Manuell im Chrome, nicht nur „müsste gehen":

1. Datei per `file://` öffnen, Text ändern, Feld verschieben.
2. `📄 Ansicht-HTML` → Ergebnisdatei öffnen: identisches Aussehen, kein Klick
   verändert etwas, keine gestrichelten Rahmen beim Überfahren, Drucken geht.
3. `📷 Bild speichern` in PNG 2× und JPG 1× → Bildmasse und Aussehen prüfen,
   besonders Schriftgrössen (Container-Queries) und Textkontur/-schatten.
4. Konsole auf Fehler prüfen.
