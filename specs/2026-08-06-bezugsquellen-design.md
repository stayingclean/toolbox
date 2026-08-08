# Bezugsquellen: Links zum Bestellen eines Skills

**Datum:** 2026-08-06
**Branch:** `worktree-feature+skill-bezugsquellen`

## Ziel

Ein Skill soll auf Wunsch zeigen, **wo man das Nötige bekommt** — etwa einen
Zauberwürfel bei einem Spielwarenhändler oder Material bei Skillsbox. Die Links
dürfen von Besuchern über das bestehende Vorschlagsformular eingereicht werden
und erscheinen nach Freigabe im Detail-Dialog der Skillsliste.

## Entscheidungen

Diese Punkte wurden im Gespräch festgelegt und begrenzen den Umfang bewusst:

- **Besucher dürfen Links einreichen** (nicht nur der Betreiber). Die Freigabe
  über das `freigegeben`-Label bleibt die Kontrolle.
- **Höchstens drei Links** je Skill.
- **Keine eigene Beschriftung.** Die Aufschrift des Knopfes ist der Hostname.
- **Erreichbarkeit wird geprüft** — einmal beim Einreichen und danach
  wiederkehrend durch einen Wächter.
- **Ohne Link kein Block.** Ein Skill ohne Bezugsquelle zeigt im Dialog keine
  Überschrift und keinen leeren Bereich.
- **Dynamische Liste im Formular** statt drei starrer Eingabefelder.

## Der Konflikt, um den herum alles gebaut ist

`worker/validate.js` und `tools/vorschlaege_holen.py` lehnen heute **jeden Text
ab, der `http` enthält** („Links sind nicht erlaubt."). Das ist die zentrale
Spam-Abwehr des Formulars: Wer eine öffentliche, anonyme Einreichung ohne Login
anbietet, wird sonst innert Wochen zur Linkschleuder für fremde Suchmaschinen-
Optimierung.

Ein Link-Feld reisst genau dieses Loch auf. Der Entwurf schliesst es an drei
Stellen wieder:

1. **Die Sperre wird nur für das neue Feld gelockert.** Titel, Beschreibung,
   Tipp und Name bleiben unverändert linkfrei. Wer in die Beschreibung eine URL
   schreibt, wird weiterhin abgewiesen.
2. **`rel="nofollow ugc"`** an jedem ausgehenden Link. Das nimmt Link-Spam sein
   Hauptmotiv: Der Link vererbt keine Suchmaschinen-Wertung. Wer bloss ranken
   will, hat von einer Einreichung nichts mehr.
3. **Menschliche Freigabe** wie bisher. Jeder Link geht durch ein Issue und
   durch ein Augenpaar, bevor er online steht.

Zusätzlich sind **Linkverkürzer gesperrt** (`bit.ly`, `tinyurl.com`, `t.co`,
`goo.gl`, `ow.ly`, `is.gd`, `buff.ly`, `rb.gy`, `cutt.ly`, `shorturl.at`,
`s.id`, `lnkd.in`). Zwei Gründe, die zusammenfallen: Ein Verkürzer verbirgt das
Ziel vor dem Freigebenden — die Prüfung im Issue wäre wertlos — und als
Knopfaufschrift wäre „bit.ly" ohnehin nichtssagend.

## Datenmodell

### Excel, Blatt `Skills`

Drei Spalten hinten angehängt: **`Link1`, `Link2`, `Link3`**, reine URLs, jede
darf leer sein.

```
… | Tipp | Von | Ergaenzt | Link1                               | Link2 | Link3
… |  …   |  …  |    …     | https://www.skillsbox.ch/p/rubik-3x3 | …     |
```

Gelesen werden sie über `optional_header` in `build.py` — **eine ältere Mappe
ohne diese Spalten baut unverändert weiter.** `tools/vorschlaege_holen.py` legt
die Spalten beim ersten Lauf über das bestehende `spalten_sichern` selbst an;
es ist kein Handgriff in Excel nötig.

**Lücken sind erlaubt.** `Link1` leer und `Link2` gefüllt ergibt eine Liste mit
einem Eintrag — die Liste wird beim Lesen zusammengeschoben. Sonst müsste
jemand, der den ersten von zwei Links entfernt, die übrigen von Hand aufrücken.
Doppelte URLs innerhalb eines Skills werden zu einer zusammengefasst.

### In `skills-daten.json` und der Skillsliste

Der Skill bekommt ein Feld **`links`** — eine Liste von Zeichenketten, **immer
vorhanden**, notfalls leer. Das folgt der bestehenden Konvention, nach der auch
`von` und `erg` immer im Datensatz stehen, selbst wenn sie leer sind. Ein
manchmal fehlender Schlüssel wäre die Ausnahme im sonst gleichförmigen Schema.

### Prüfung in `build.py`

Eine URL muss erfüllen: nur `https://` · Hostname mit mindestens einem Punkt ·
kein `@` (Benutzerangabe) · kein Port · keine IP-Adresse · höchstens 300
Zeichen. Verstösse brechen den Build ab, mit Blatt- und Zeilenangabe im Stil der
bestehenden Meldungen.

Der Build ist bewusst die strengste Stelle: Eine kaputte URL soll beim
Doppelklick auf `build.bat` auffallen, nicht später einem Besucher beim Klicken.

## Anzeige in der Skillsliste

Im Detail-Dialog, unterhalb des Tipps:

```
Bezugsquellen
[ ↗ skillsbox.ch ]   [ ↗ galaxus.ch ]

Von Besuchern vorgeschlagen · keine Empfehlung, keine Provision
```

- **Aufschrift** ist der Hostname ohne führendes `www.`, abgeleitet in
  `openModal` per `new URL(u).hostname`. Nebeneffekt, der zählt: Der Besucher
  sieht vor dem Klick, wo er landet — eine frei getippte Beschriftung könnte
  lügen.
- **Ohne Links wird der Block nicht erzeugt** — keine Überschrift, kein
  Abstand, kein leerer Platzhalter.
- **Auf den Karten erscheint nichts.** Die Übersicht bleibt dicht.
- Jeder Link: `target="_blank" rel="noopener noreferrer nofollow ugc"`.
- Der Zusatz **„Von Besuchern vorgeschlagen · keine Empfehlung, keine
  Provision"** steht am Fuss des Blocks. Er stellt klar, dass hier weder eine
  Empfehlung noch ein Partnerprogramm dahintersteckt.

Die Links stehen in `template.html`, nicht in der generierten Datei — die
Skillsliste wird erzeugt und darf nie von Hand bearbeitet werden.

## Formular: dynamische Link-Liste

In **beiden** Reitern („Neuer Skill" und „Bestehenden ergänzen"), unterhalb des
Tipps:

```
Bezugsquellen (freiwillig, höchstens 3)

  [ https://www.skillsbox.ch/p/rubik-3x3        ]  [×]
  [ https://                                     ]  [×]

  [ + Bezugsquelle hinzufügen ]
```

- Anfangs **eine** leere Zeile.
- `+` fügt eine Zeile an, bis drei erreicht sind; danach ist der Knopf
  deaktiviert (nicht versteckt — sonst springt das Layout).
- `×` entfernt eine Zeile. Die letzte Zeile lässt sich leeren, aber nicht
  entfernen, damit nie ein Zustand ohne jedes Eingabefeld entsteht.
- Felder sind `type="url"` mit `inputmode="url"`.

**Beim Ergänzen füllt `originalUebernehmen` genau so viele Zeilen, wie der Skill
Links hat.** Die Person sieht die vorhandenen Quellen, kann eine dazutun, eine
korrigieren oder eine entfernen.

### Warum das die Ergänzungs-Logik unverändert lässt

`SPALTEN_AENDERUNG` in `tools/vorschlaege_holen.py` **ersetzt** die Felder eines
Skills vollständig — es führt nichts zusammen. Beim ersten Nachdenken scheint
eine Liste damit unverträglich: Die zweite Person will meist einen Shop
*dazutun*, nicht die Liste der ersten wegwerfen.

Das Vorbefüllen löst es. Die Liste kommt **gefüllt** ins Formular und
**vollständig** zurück. Vollständiges Ersetzen ist damit das richtige Verhalten
— genau wie heute bei Titel und Beschreibung, die ebenfalls vorbefüllt
zurückkommen. **Es braucht keinen neuen Zusammenführungs-Mechanismus.**

Zwei Folgen davon, bewusst in Kauf genommen:

- Eine Ergänzung kann Links **entfernen**. Das ist gewollt (tote Quelle
  streichen) und geht ohnehin durch die Freigabe.
- Reichen zwei Personen gleichzeitig ein, gewinnt die zuletzt freigegebene. Das
  gilt heute schon für Titel und Beschreibung; die Bezugsquellen fügen dem
  keine neue Fehlerart hinzu.

### Entwurfs-Sicherung

`entwurfSichern`/`felderSetzen` halten heute je Reiter einen eigenen Entwurf,
damit ein Blick in den anderen Reiter nichts löscht. `ENTWURF_FELDER` ist eine
Liste von Feld-IDs und trägt eine Liste nicht. Die Links werden darum
**daneben** als Array gesichert und gesetzt — genau so, wie `original` bereits
gesondert behandelt wird.

## Worker

`worker/validate.js` bekommt **`pruefeLinks(rohe)`**, aufgerufen aus `pruefeVorschlag`
*und* `pruefeAenderung`. Die Funktion liefert entweder eine bereinigte Liste
oder eine Fehlermeldung im bestehenden Stil.

Regeln: höchstens 3 · nur `https:` · Hostname mit Punkt · kein `@`, kein Port,
keine IP · ≤ 300 Zeichen · keine spitzen Klammern oder Kommentarzeichen · kein
Linkverkürzer. Leere Einträge fallen still weg; Dubletten werden
zusammengefasst.

Die Regeln sind bewusst **dieselben wie in `build.py`** und werden in
`tools/vorschlaege_holen.py` ein drittes Mal gespiegelt. Das ist keine
Nachlässigkeit, sondern das im Projekt bereits etablierte Muster: Der Worker
schützt den Formularweg, das Übernahme-Skript fängt Issues ab, die nicht über
das Formular kamen, und der Build ist die letzte Schranke vor der Website.

### Erreichbarkeits-Prüfung beim Absenden

Der Worker ruft jede eingereichte URL einmal ab (5 Sekunden Zeitlimit) und
schreibt das Ergebnis als Notiz in das Issue:

```
✓ skillsbox.ch/p/rubik-3x3 — 200 OK
⚠ galaxus.ch/de/s1/12345 — 404, Link zeigt ins Leere
```

**Er lehnt deswegen nie ab.** Ein Shop, der Cloudflare-Adressen aussperrt, darf
keine ehrliche Einreichung blockieren — der Link funktioniert im Browser
tadellos, und die einreichende Person hätte keine Chance zu verstehen, was von
ihr verlangt wird. Die Notiz ist Entscheidungshilfe beim `freigegeben`-Label,
nicht mehr.

Fällt der Abruf ins Zeitlimit oder scheitert er, steht das ebenfalls dran und
gilt als „keine Aussage".

**SSRF:** Dass nur `https` ohne Port und ohne IP-Adresse durch `pruefeLinks`
kommt, ist zugleich die Absicherung dieses Abrufs — der Worker lässt sich damit
nicht auf interne Adressen richten. Die Prüfung läuft **nach** der Validierung.

## Wächter gegen Linkfäule

`.github/workflows/links-pruefen.yml` — wöchentlich per `schedule`, dazu
`workflow_dispatch` für den Knopf von Hand. Ruft `tools/links_pruefen.py`:
liest `docs/skills-daten.json`, prüft jeden Link höflich (eine Sekunde Pause
zwischen Abrufen, eigener User-Agent, der das Projekt nennt).

### Nur harte Befunde

Gemeldet werden ausschliesslich **`404`, `410` und „Domain existiert nicht
mehr"**. `403`, `429` und alle `5xx` werden schweigend übergangen.

Der Grund ist der Nutzen des Wächters selbst: Shops sind genau die Seiten, die
automatische Abrufe aussperren. Ein Prüfer, der auf `403` anspringt, meldet
dauernd Falschalarm für Links, die im Browser einwandfrei funktionieren — und
wird nach drei Wochen ignoriert. Ein Wächter, den niemand mehr liest, ist
schlechter als keiner, weil er Sicherheit vortäuscht.

### Ein Sammel-Issue, keine Flut

Ergebnis ist **ein** Issue in `stayingclean/toolbox` (Issues sind dort
aktiviert) mit dem Label `tote-links`, das bei jedem Lauf neu geschrieben wird:

```
Tote Bezugsquellen — Stand 12.08.2026

• Zauberwürfel  → galaxus.ch/de/s1/12345   404
• Duftöle       → shop-xy.ch/produkt/7     Domain gibt es nicht mehr
```

Findet ein Lauf nichts mehr, wird ein offenes Issue geschlossen. So entsteht
über die Jahre keine Issue-Halde.

Der Workflow braucht `issues: write`.

## Was mitgezogen wird

- **`tools/seed_excel.py`** — die drei Spalten in Kopfzeile und Spaltenbreiten,
  damit ein Zurücksetzen der Mappe die Links nicht verliert.
- **`CLAUDE.md`** — Abschnitt zu den Bezugsquellen; Hinweis, dass die
  Link-Regeln an drei Stellen gespiegelt sind.
- **`ANLEITUNG.md`** — wie Links in der Excel gepflegt werden und was das
  Sammel-Issue des Wächters bedeutet.

## Tests

Nach der bestehenden Aufteilung des Projekts:

| Datei | prüft |
|---|---|
| `tests/test_build.py` | fehlende Spalten brechen nicht · ungültige URL bricht mit Zeilenangabe ab · Lücken werden zusammengeschoben · Dubletten fallen weg · `links` landet in beiden Ausgaben |
| `worker/validate.test.js` | alle Link-Regeln · mehr als drei · `http://` · Verkürzer · IP · Port · Benutzerangabe · **dass Titel und Beschreibung weiterhin keine Links dürfen** |
| `tests/test_vorschlaege_holen.py` | Ergänzung ersetzt die Links vollständig · neue Skills bringen ihre Links mit · fehlende Spalten werden angelegt · Abbruch schreibt weiterhin nichts |
| `tests/test_links_pruefen.py` | **neu** — welche Antwort als tot gilt und welche nicht; Aufbau des Sammel-Issues |

`tests/test_links_pruefen.py` prüft **reine Funktionen ohne Netzwerkzugriff**.
Ein Test, der echte Shops abruft, wäre selbst unzuverlässig und schlüge
irgendwann ohne eigenes Verschulden fehl.

## Ausdrücklich nicht Teil davon

- Keine Preisangaben, keine Verfügbarkeit, keine Produktbilder.
- Keine Partnerprogramme oder Provisions-Links.
- Keine Prüfung im Browser des Besuchers — CORS lässt den Status einer fremden
  Domain nicht lesen, und es verriete jeden Seitenaufruf an die Shops.
- Kein Netzwerkzugriff in `build.py`. Der Build muss offline und per Doppelklick
  laufen; ein Shop mit Schluckauf darf die Skillsliste nicht blockieren.
