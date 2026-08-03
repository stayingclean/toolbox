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
4. Das SVG wird als **Data-URI** in ein `<img>` geladen und auf ein `<canvas>`
   gezeichnet; `canvas.toBlob` liefert die Datei.

**Data-URI, nicht Blob-URL** — im Test messbar belegt: ein SVG mit `<foreignObject>`
aus einer Blob-URL macht den Canvas „tainted", `toBlob()` wirft danach einen
`SecurityError`. Aus einer Data-URI geladen bleibt der Canvas sauber:

| Quelle | ohne foreignObject | mit foreignObject |
|---|---|---|
| Blob-URL | sauber | **SecurityError** |
| Data-URI | sauber | sauber |

Die Blob-URL bleibt nur als Notnagel, falls die Data-URI an einer Längenbegrenzung
scheitert.

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

| Risiko | Umgang | Stand |
|---|---|---|
| Canvas „tainted", `toBlob` wirft `SecurityError` | Data-URI statt Blob-URL; Fehler wird zusätzlich abgefangen und als Meldung in der Statuszeile angezeigt statt still zu scheitern | gelöst |
| Data-URI lädt nicht (Längenbegrenzung) | `img.onerror` → zweiter Versuch mit Blob-URL | abgesichert |
| Betrieb unter `file://` (Doppelklick, ohne Server) | headless getestet: beide Exporte funktionieren | verifiziert |
| Safari rendert `foreignObject`-in-SVG unzuverlässig | Zielbrowser sind Chrome/Edge/Firefox; Einschränkung wird dokumentiert, nicht kaschiert | offen, dokumentiert |
| Fällt die Technik ganz durch | Rückfallplan: `html-to-image` (MIT, ~30 KB) inline einbetten | nicht nötig |

## Aufbau im Code

Beide Exporte teilen sich Hilfsfunktionen, damit die Logik nur einmal existiert:

- `stripEditorState(root)` — entfernt Editor-Attribute und -Klassen an einem Klon
- `collectCss()` — sammelt alle `<style>`-Inhalte des Dokuments
- `downloadBlob(blob, name)` — ein Download-Weg für alle drei Speicher-Funktionen
- `EXPORT_CSS` — die neutralisierenden Regeln, von beiden Exporten genutzt

`doSave()` (die bestehende Arbeitskopie) wird auf `downloadBlob` umgestellt, sonst
aber nicht angefasst.

## Verifikation — Ergebnis

Im Browser durchgeführt (Chromium), nicht nur „müsste gehen":

| Prüfung | Ergebnis |
|---|---|
| JS-Syntax (`node --check`) | fehlerfrei |
| PNG 2×, A5 hoch | 1118×1588 px, 3.6 MB / 3.0 MB — Schriftgrössen, Schriftarten und Positionen stimmen mit der Bildschirmdarstellung überein |
| JPG 1×, A5 hoch | 559×794 px, 167 KB / 132 KB |
| PNG 2×, A4 quer | 2246×1588 px — Formatwechsel wird korrekt übernommen |
| QR-Feld (Inline-SVG) im Bild | vollständig und scharf gerastert |
| Ansicht-HTML | 0 `<script>`, 0 `contenteditable`, 0 Editor-Elemente, 2 Seiten, 6 Felder, `@page`-Regel und Urheber-Credit erhalten, `cursor:default`, `isContentEditable === false` |
| Betrieb unter `file://` | beide Exporte funktionieren (headless verifiziert) |
| `💾 Speichern` nach dem Umbau auf `downloadBlob` | unverändert funktionsfähig |
| Browser-Konsole | keine Fehler |

Nicht abgedeckt: Safari (siehe Risiken) und eingefügte Bildfelder mit selbst
gewählter Datei — technisch identisch zu den eingebetteten Hintergrundbildern,
die im Test korrekt gerastert wurden.
