# Skills ohne Git-Wissen vorschlagen

**Datum:** 2026-08-03
**Status:** Entwurf, freigegeben zur Planung

## Problem

Die Skillsliste wird aus `skills_daten.xlsx` erzeugt. Wer einen Skill beitragen
will, braucht heute das Repo, Git und `build.bat`. Für die Zielgruppe — Menschen
aus dem Suchtbereich ohne Entwicklungshintergrund — ist das eine Hürde, an der
Beiträge scheitern.

## Ziel

Eine Person besucht die Toolbox, füllt ein Formular aus, klickt „Absenden".
Ohne Konto, ohne Anmeldung, ohne Git. Der Vorschlag landet bei der Betreuung des
Repos, wird dort geprüft und erscheint nach Freigabe in der Skillsliste. Wer
mag, hinterlässt einen Namen und wird auf der Skillsliste genannt.

## Getroffene Entscheidungen

| Frage | Entscheidung | Begründung |
|---|---|---|
| Wer darf einreichen? | Alle, ohne Konto | Ein GitHub-Konto ist für die Zielgruppe eine reale Hürde |
| Anonym? | Ja, zwingend | Wer aus eigener Erfahrung beiträgt, soll sich nicht outen müssen |
| Nach Freigabe | Halbautomatisch | Excel bleibt Datenquelle, kein Umbau der Pipeline; Push bleibt beim Menschen |
| Posteingang | Öffentliches Repo `stayingclean/skills-suggestions` | Transparenz gewünscht; getrennt vom Code-Repo |
| Rückmeldung | Link auf das eigene Issue | Öffentlicher Posteingang macht Statusverfolgung ohne Konto möglich |
| Name der einreichenden Person | Optionales Feld, Anzeige nur im Detail-Dialog | Kein Tooltip: auf Touch-Geräten unsichtbar |
| Änderungen an bestehenden Skills | Zweiter Reiter auf derselben Seite | Gemeinsame Gestaltung, ein Link in der Übersicht, weniger Doppelcode |
| Duplikatprüfung | Optional per KI im Übernahme-Skript, mit Rückfrage | Voller Bestand liegt lokal vor, Schlüssel bleibt auf dem eigenen Rechner |
| Kaffeekasse | Fusszeile plus eigene Seite | Zurückhaltend, aber erklärt wofür |

## Ablauf

```
Besucher/in                    Cloudflare              Betreuung
────────────                   ──────────              ─────────
skill-vorschlagen.html
 ┌ Neuer Skill ┬ Bestehenden ergänzen ┐
 │ Stufe ▾     │ Stufe ▾ Kategorie ▾  │
 │ Kategorie ▾ │ Skill ▾ (vorausgef.) │
 │ Emoji,Titel,Beschreibung,Tipp,Name │
 └────── [Absenden] ─────────────────┘
             │
             └──────────────────▶  Worker prüft
                                   (Turnstile, Länge,
                                    Pflichtfelder, keine Links)
                                          │
                                          ▼
                                   Issue in
                                   stayingclean/skills-suggestions
                                          │
   Dankesmeldung ◀── Link aufs Issue ──────┤
   („Stand hier verfolgen")                │
                                           ▼
                                   GitHub-App: Label
                                   „freigegeben"
                                           │
   Skillsliste ◀── push ◀── build.py ◀── vorschlaege.bat
   ist aktuell     (manuell)            holt Freigegebene,
                                        prüft auf Duplikate,
                                        schreibt in die Excel
```

Für die einreichende Person ist es eine Seite, ein Formular, ein Klick — und ein
Link, unter dem sie den Stand selbst nachsehen kann. Für die Betreuung ein
Label-Klick auf dem Handy und ein Doppelklick auf eine `.bat`, wenn sich etwas
angesammelt hat.

## Bausteine

### `template-vorschlag.html` → `docs/skill-vorschlagen.html`

Die Formularseite wird **generiert**, nicht von Hand gepflegt — gleiche
Konvention wie die Skillsliste. `build.py` bekommt eine zweite Vorlage und setzt
den aktuellen Datenbestand ein. Damit passen die Auswahllisten immer zur
veröffentlichten Skillsliste; ändert sich etwas in der Excel, ändert es sich
beim nächsten Build auch im Formular.

Die Seite hat **zwei Reiter**:

**Reiter 1 — Neuer Skill**

| Feld | Typ | Pflicht | Grenze |
|---|---|---|---|
| Stufe | Auswahl (Hoch/Mittel/Tief) | ja | fester Wertebereich |
| Kategorie | Auswahl, abhängig von Stufe | ja | fester Wertebereich |
| Emoji | Text | ja | 2 Zeichen |
| Titel | Text | ja | 60 Zeichen |
| Beschreibung | Mehrzeilig | ja | 300 Zeichen |
| Tipp | Mehrzeilig | nein | 200 Zeichen |
| Name | Text | nein | 30 Zeichen |

**Reiter 2 — Bestehenden ergänzen**

Stufe → Kategorie → Skill auswählen; die vorhandenen Texte erscheinen
vorausgefüllt und sind bearbeitbar. Gesendet werden sowohl der ursprüngliche
Titel (als Schlüssel) als auch die geänderten Felder, damit die Betreuung im
Issue sieht, was sich ändern soll. Das Namensfeld gibt es hier ebenfalls.

Beim Namensfeld steht unübersehbar dabei, dass er **öffentlich und dauerhaft**
auf der Skillsliste erscheint und ein Vorname oder Spitzname genügt.

Nach dem Absenden erscheint eine Dankesmeldung mit dem **Link auf das erzeugte
Issue** und einem Kopieren-Knopf, dazu der Hinweis: „Wir können dich nicht
benachrichtigen — merk dir diesen Link, dort siehst du den Stand." Die drei
Labels werden auf der Seite kurz erklärt.

**Abweichung von der Projektkonvention:** Diese Seite ist die erste in `docs/`,
die Internet benötigt. Der Spam-Schutz lädt ein Skript von Cloudflare, und
Absenden geht ohne Netz ohnehin nicht. CSS bleibt eingebettet, aber die Regel
„funktioniert lokal ohne Server/Internet" lässt sich für ein Einreichformular
nicht halten. Das ist bewusst so.

### Regel: Ausgabecodierung beim Einsetzen in den `<script>`-Block

`build.py` setzt den Datenbestand als JSON in einen `<script>`-Block von
`template.html` und `template-vorschlag.html`. `json.dumps` maskiert `<` und `/`
**nicht** — eine eingereichte Beschreibung wie `…</script><script>…` beendet
sonst wörtlich im Erzeugnis das Skriptelement, und der Rest läuft als fremder
Code auf `stayingclean.github.io`.

Deshalb gilt als feste Regel: **vor dem Einsetzen werden `<`, `>` und `&` im
JSON-Text durch die Escape-Form `\u003c`, `\u003e` und `\u0026` ersetzt.** Das
bleibt gültiges JSON und verändert die Werte nicht — der Browser setzt die
Escapes beim Parsen zurück. Die Regel gilt für jeden künftigen Platzhalter, der
Daten in ein Skriptelement schreibt.

### `docs/skills-daten.json`

Wird von `build.py` miterzeugt und enthält den vollständigen Bestand: Stufen,
Kategorien und alle Skills mit ihren Texten. Zwei Nutzer:

- Die Formularseite füllt daraus die Auswahllisten und den Bearbeiten-Reiter.
- Der Worker liest die Datei (zwischengespeichert) und prüft eingehende Werte
  dagegen. So bleibt die Prüfung automatisch synchron, ohne dass der Worker je
  wieder angefasst werden muss.

### Cloudflare Worker

Rund 80 Zeilen JavaScript, Quelltext unter `worker/` im Repo versioniert, aber
nicht in `docs/` und damit nicht veröffentlicht.

Aufgaben:

1. Turnstile-Token prüfen — ohne gültiges Token wird nichts angenommen
2. Versteckte Falle prüfen (unsichtbares Feld; ausgefüllt = Bot)
3. Pflichtfelder, Maximallängen, Stufe/Kategorie/Skill gegen `skills-daten.json`
4. Jede Einreichung ablehnen, die `http` enthält (wirksamster Einzelfilter,
   weil praktisch aller Spam Links transportieren will)
5. Ratenbegrenzung: höchstens fünf Einreichungen pro Stunde und Absender
   (Zähler in Cloudflare KV, Schlüssel = Hashwert der IP, Ablauf nach 1 Stunde)
6. Issue anlegen über ein GitHub-Token (Bot), das als Secret im Worker liegt
7. Die Adresse des angelegten Issues an die Seite zurückgeben

**Reichweite dieser Prüfung:** `validate.js` ist die Prüfinstanz **für
Einreichungen über das Formular** — nicht für alles, was im Vorschlags-Repo
landet. Weil das Repo öffentlich ist, kann jede Person mit GitHub-Konto dort von
Hand ein Issue eröffnen, mit einem eigenen `<!-- vorschlag … -->`-Block, den die
gerenderte Ansicht unsichtbar macht. Der Worker sieht davon nichts. Deshalb prüft
das Übernahme-Skript zusätzlich die **Herkunft** (nur Issues des Bot-Kontos) und
die **Felder** noch einmal — Letzteres fängt auch den Fall ab, dass eine
Kategorie zwischen Einreichung und Freigabe umbenannt oder gelöscht wurde.

**Keine Aufwachzeit:** Workers laufen als Isolate im Cloudflare-Netz und starten
in unter einer Millisekunde — anders als schlafende Server bei Render oder
Heroku. Die Seite selbst liegt statisch auf GitHub Pages; der Worker wird erst
beim Klick auf „Absenden" angesprochen. Gratis-Kontingent: 100'000 Aufrufe/Tag.

**Anonymität:** Der Worker schreibt weder IP-Adresse noch Browserkennung
irgendwohin — nicht ins Issue, nicht in ein Log. Die Workers Logs werden dafür in
`wrangler.toml` ausdrücklich abgeschaltet (`[observability] enabled = false`),
weil sie bei neuen Workers sonst eingeschaltet wären und die Anfrage samt IP
mehrere Tage vorhielten. Für die Ratenbegrenzung wird die IP nur als Hashwert mit
einer Stunde Gültigkeit gehalten und verfällt dann. Das Issue enthält
ausschliesslich die Formularfelder. Die einreichende Person ist damit auch für
die Betreuung nicht identifizierbar; das ist gewollt.

Eine Ausnahme gehört genannt: Die IP-Adresse wird als `remoteip` an Cloudflares
eigene Turnstile-Prüfung mitgeschickt — an denselben Anbieter, der die Verbindung
ohnehin terminiert und die IP damit ohnehin sieht. Sie verlässt den Weg der
Anfrage also nicht, aber „irgendwohin geschrieben" ist an dieser einen Stelle zu
absolut formuliert.

### `stayingclean/skills-suggestions`

Neues, öffentliches Repo. Enthält keinen Code und keinen Workflow, nur Issues
als Posteingang. Weil der Link zum Issue die einzige Rückmeldung ist, sind die
Labels für Menschen lesbar:

| Label | Bedeutung für die einreichende Person |
|---|---|
| *(kein Label)* | Eingegangen, noch nicht angeschaut |
| `in Prüfung` | Wird gerade angeschaut |
| `freigegeben` | Kommt in die Skillsliste (Issue schliesst sich beim Übernehmen) |
| `abgelehnt` | Wird nicht übernommen; Begründung als Kommentar |

Vorteil gegenüber einer eigenen Freigabe-Oberfläche: Es gibt die GitHub-App
fürs Handy, es ist nichts zu bauen und nichts zu warten.

**Issue-Format:** Titel = der vorgeschlagene Skill-Titel, bei Änderungen mit
Präfix `[Änderung]`. Rumpf = die Felder als Tabelle für Menschen (bei Änderungen
alt/neu nebeneinander), darunter ein maschinenlesbarer JSON-Block mit einem Feld
`art` (`neu` oder `aenderung`) — dieselbe Konvention wie bei den Formularen der
Toolbox: menschenlesbar oben, JSON eingebettet unten.

**Bekanntes Restrisiko:** Bei einem öffentlichen Posteingang ist jede
Einreichung sofort sichtbar, auch ungeprüfte. Ein hartnäckiger Mensch, der
Turnstile löst, bekommt eine Zeile Text öffentlich, bis das Issue gelöscht wird.
Notbremse: Issues im Vorschlags-Repo abschalten — die Formularseite zeigt dann
eine Hinweismeldung statt des Formulars. Das Toolbox-Repo bleibt davon
unberührt.

### `tools/vorschlaege_holen.py` + `vorschlaege.bat`

Doppelklick genügt, gleiche Bedienlogik wie `build.bat`. Das Skript läuft
interaktiv im Konsolenfenster.

1. `gh issue list --repo stayingclean/skills-suggestions --label freigegeben
   --state open --json number,title,body,author` — holt die freigegebenen, noch
   offenen Vorschläge
2. **Herkunft prüfen:** nur Issues, die unter dem Bot-Konto angelegt wurden.
   Alles andere ist von Hand eröffnet und nie durch den Worker gelaufen
3. JSON-Block aus jedem Issue lesen
4. **Felder prüfen** (Pflichtfelder, Längen, keine Links, keine Kommentarzeichen
   und keine spitzen Klammern, Stufe und Kategorie gegen `skills-daten.json`) —
   **vor** dem Schreiben in die Excel, damit kein Abbruch eine halb geschriebene
   Excel mit offenen Issues hinterlässt
5. **Optionale Duplikatprüfung** (siehe unten)
6. Übernehmen:
   - `art: neu` → Zeile ans Blatt `Skills` anhängen
   - `art: aenderung` → bestehende Zeile suchen (Schlüssel: Stufe + Kategorie +
     ursprünglicher Titel) und die geänderten Felder ersetzen. Wird die Zeile
     nicht gefunden, bleibt das Issue offen und das Skript meldet es
5. Die übernommenen Issues schliessen
6. `build.py` aufrufen

Der Push bleibt bewusst manuell. Nichts geht online, ohne dass es jemand
gesehen hat.

### Duplikatprüfung mit KI (optional)

Ist die Umgebungsvariable `ANTHROPIC_API_KEY` gesetzt, prüft das Skript vor der
Übernahme jeden neuen Vorschlag gegen den bestehenden Bestand. Ist sie nicht
gesetzt, entfällt der Schritt kommentarlos und das Skript läuft wie sonst.

- Modell: `claude-opus-5` (Standard). Der Modellname steht als Konstante oben im
  Skript, damit ein günstigeres Modell eine Einzeiler-Änderung ist.
- Aufruf über das offizielle `anthropic`-Paket, Antwort per `output_config.format`
  auf ein festes JSON-Schema festgelegt (Treffer ja/nein, Titel des ähnlichen
  Skills, kurze Begründung).
- Kosten: der ganze Bestand plus die neuen Vorschläge liegen deutlich unter
  100'000 Zeichen — ein Durchgang kostet einige Rappen.

Bei einem Treffer fragt das Skript pro Fall nach:

```
⚠ „Musik bewusst hören" ähnelt „Lieblingslied auflegen" (Hoch / Ablenkung)
   Begründung: Beide beschreiben gezieltes Musikhören zur Ablenkung.
   [ü]bernehmen  [w]eiter (überspringen)  [ä]ls Änderung einarbeiten  ?
```

„Als Änderung einarbeiten" ersetzt die Felder des bestehenden Skills durch die
des Vorschlags, statt eine zweite Zeile anzulegen. Übersprungene Issues bleiben
offen und behalten ihr Label.

### Namensfeld in der Datenkette

- **Excel, Blatt `Skills`:** neue Spalte `Von`. `build.py` liest sie
  **tolerant** — fehlt die Spalte, bleibt das Feld für alle leer und der Build
  läuft weiter. So bricht keine bestehende Excel.
- **Datenstruktur:** neuer Schlüssel `von` je Skill.
- **`template.html`:** der Detail-Dialog bekommt unter dem 💡-Tipp eine dezente
  Zeile „Vorgeschlagen von …", die nur erscheint, wenn ein Name vorhanden ist.
  Die Übersichtskarte bleibt unverändert (Emoji, Titel, Pfeil).
- **`tools/seed_excel.py`:** muss die neue Spalte mitschreiben, sonst gehen die
  Namen bei einem Reset verloren.

### `docs/unterstuetzen.html` + Fusszeilen-Link

Kurze Seite im Toolbox-Design, die erklärt, wofür die Unterstützung verwendet
wird, und die Wege auflistet. Kein eingebettetes Widget — nur schlichte Links,
sonst lädt die Seite fremde Skripte.

- **Buy Me a Coffee** — `https://buymeacoffee.com/stayingclean` (aus dem
  Dashboard des Kontoinhabers). Die Adresse antwortet am 2026-08-03 von aussen
  mit 404, die Seite ist also vermutlich noch nicht veröffentlicht — vor dem
  Push freischalten und prüfen, siehe Abschlussliste.
- **TWINT/PayPal** — Abschnitt wird vorbereitet und bleibt ausgeblendet, bis das
  Konto eingerichtet ist.

Der Ton bleibt zurückhaltend („unterstützt die laufenden Kosten"), nicht
werblich — im Suchtkontext kommt ein forscher Spendenaufruf schlecht an.

Die Fusszeilen-Konvention in `CLAUDE.md` wird um einen zweiten Link neben dem
Urheber-Credit erweitert. Betroffen sind alle Seiten in `docs/` sowie
`template.html`.

## Ausbaustufen

Die Umsetzung erfolgt in drei Schritten, jeder für sich lauffähig:

1. **Einreichen** — Formular (nur Reiter „Neuer Skill"), Worker, Vorschlags-Repo,
   Übernahme-Skript ohne KI, Namensfeld in der ganzen Kette, Statuslink.
2. **Ändern** — zweiter Reiter, Erweiterung des Übernahme-Skripts um `art`
   und das Ersetzen bestehender Zeilen.
3. **Ergänzungen** — Duplikatprüfung mit KI, Kaffeekasse.

Schritt 3 ist unabhängig von 1 und 2 und kann vorgezogen werden.

## Änderungen am bestehenden Projekt

| Datei | Was |
|---|---|
| `template-vorschlag.html` | neu — Vorlage der Formularseite, CSS eingebettet |
| `worker/` | neu — Quelltext des Workers, versioniert, nicht veröffentlicht |
| `tools/vorschlaege_holen.py`, `vorschlaege.bat` | neu — Freigegebene in die Excel übernehmen |
| `docs/unterstuetzen.html` | neu — Kaffeekasse |
| `build.py` | erzeugt zusätzlich `docs/skill-vorschlagen.html` und `docs/skills-daten.json`; liest Spalte `Von` |
| `template.html` | Detail-Dialog zeigt „Vorgeschlagen von …"; Fusszeile mit Unterstützungs-Link |
| `tools/seed_excel.py` | schreibt Spalte `Von` mit |
| `skills_daten.xlsx` | neue Spalte `Von` im Blatt `Skills` |
| `docs/index.html` | neue Karte mit Verweis auf das Formular; Fusszeile |
| `docs/budgetvorlage.html`, `docs/asrs-v1-1.html`, `docs/neutral_flyer.html` | Fusszeile mit Unterstützungs-Link |
| `CLAUDE.md`, `ANLEITUNG.md` | Ablauf und erweiterte Fusszeilen-Konvention dokumentieren |

Unverändert bleiben `docs/skillsliste.html` (weiterhin generiert) und der
Deploy-Workflow.

## Bewusst nicht enthalten

- Bestehende Skills über das Formular löschen
- Neue Kategorien vorschlagen (nur bestehende sind wählbar)
- Benachrichtigung an die einreichende Person — bei echter Anonymität gibt es
  keine Adresse; der Statuslink ersetzt sie
- Automatisches Veröffentlichen ohne manuellen Push
- Konto, Anmeldung oder Profil für Einreichende
- Duplikatprüfung schon beim Absenden (bräuchte den Schlüssel im Worker und
  kostete pro Einreichung)

## Prüfen vor Abschluss

- Formular auf Handy und Rechner bedienbar, Kategorie-Auswahl filtert korrekt,
  Reiterwechsel verliert keine Eingaben
- Bearbeiten-Reiter füllt die vorhandenen Texte korrekt vor
- Worker lehnt ab: fehlendes Turnstile-Token, ausgefüllte Falle, Link im Text,
  zu lange Felder, unbekannte Kategorie, unbekannter Skill, sechste Einreichung
  innert einer Stunde
- Issue enthält weder IP noch Browserkennung; die Dankesmeldung zeigt den Link
- `vorschlaege.bat` übernimmt mehrere Vorschläge in einem Durchgang, schliesst
  die Issues und erzeugt eine korrekte Skillsliste
- Eine Änderung ersetzt die bestehende Zeile, statt eine zweite anzulegen; ein
  nicht auffindbarer Skill lässt das Issue offen und wird gemeldet
- Ohne `ANTHROPIC_API_KEY` läuft die Übernahme unverändert durch; mit Schlüssel
  erscheint bei einem Duplikat die Rückfrage, und alle drei Antworten tun das
  Richtige
- Bestehende Excel ohne Spalte `Von` baut weiterhin fehlerfrei
- Detail-Dialog zeigt die Namenszeile nur bei vorhandenem Namen
- Fusszeilen-Link erscheint auf allen Seiten in `docs/`
- Der Buy-Me-a-Coffee-Link führt auf eine erreichbare Seite (nicht 404), bevor
  `docs/unterstuetzen.html` gepusht wird
