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
Repos, wird dort geprüft und erscheint nach Freigabe in der Skillsliste.

## Getroffene Entscheidungen

| Frage | Entscheidung | Begründung |
|---|---|---|
| Wer darf einreichen? | Alle, ohne Konto | Ein GitHub-Konto ist für die Zielgruppe eine reale Hürde |
| Anonym? | Ja, zwingend | Wer aus eigener Erfahrung beiträgt, soll sich nicht outen müssen |
| Nach Freigabe | Halbautomatisch | Excel bleibt Datenquelle, kein Umbau der Pipeline; Push bleibt beim Menschen |
| Posteingang | Öffentliches Repo `stayingclean/toolbox-vorschlaege` | Transparenz gewünscht; getrennt vom Code-Repo |
| Name der einreichenden Person | Optionales Feld, Anzeige nur im Detail-Dialog | Kein Tooltip: auf Touch-Geräten unsichtbar |

## Ablauf

```
Besucher/in                    Cloudflare              Betreuung
────────────                   ──────────              ─────────
skill-vorschlagen.html
  Stufe ▾ Kategorie ▾
  Emoji, Titel,
  Beschreibung, Tipp,
  Name (optional)
  [Absenden] ──────────────▶  Worker prüft
                              (Turnstile, Länge,
                               Pflichtfelder, keine Links)
                                     │
                                     ▼
                              Issue in
                              stayingclean/toolbox-vorschlaege
                                                        │
                              GitHub-App ◀──────────────┘
                              liest, entscheidet,
                              Label „freigegeben"
                                     │
   Skillsliste ◀── push ◀── build.py ◀── vorschlaege.bat
   ist aktuell     (manuell)            holt Freigegebene,
                                        hängt sie an die Excel
```

## Bausteine

### `template-vorschlag.html` → `docs/skill-vorschlagen.html`

Die Formularseite wird **generiert**, nicht von Hand gepflegt — gleiche
Konvention wie die Skillsliste. `build.py` bekommt eine zweite Vorlage und setzt
die aktuellen Stufen und Kategorien als Auswahllisten ein. Damit passen die
Listen im Formular immer zur veröffentlichten Skillsliste; ändert sich eine
Kategorie in der Excel, ändert sie sich beim nächsten Build auch im Formular.

Die Kategorie-Auswahl hängt von der gewählten Stufe ab und filtert sich
entsprechend.

**Felder:**

| Feld | Typ | Pflicht | Grenze |
|---|---|---|---|
| Stufe | Auswahl (Hoch/Mittel/Tief) | ja | fester Wertebereich |
| Kategorie | Auswahl, abhängig von Stufe | ja | fester Wertebereich |
| Emoji | Text | ja | 2 Zeichen |
| Titel | Text | ja | 60 Zeichen |
| Beschreibung | Mehrzeilig | ja | 300 Zeichen |
| Tipp | Mehrzeilig | nein | 200 Zeichen |
| Name | Text | nein | 30 Zeichen |

Beim Namensfeld steht unübersehbar dabei, dass er **öffentlich und dauerhaft**
auf der Skillsliste erscheint und ein Vorname oder Spitzname genügt.

Nach dem Absenden erscheint eine Dankesmeldung mit dem ehrlichen Hinweis, dass
es keine Rückmeldung geben kann — bei echter Anonymität gibt es keine Adresse.
Wer wissen will, ob der Vorschlag angenommen wurde, schaut in ein paar Tagen auf
die Skillsliste.

**Abweichung von der Projektkonvention:** Diese Seite ist die erste in `docs/`,
die Internet benötigt. Der Spam-Schutz lädt ein Skript von Cloudflare, und
Absenden geht ohne Netz ohnehin nicht. CSS bleibt eingebettet, aber die Regel
„funktioniert lokal ohne Server/Internet" lässt sich für ein Einreichformular
nicht halten. Das ist bewusst so.

### `docs/kategorien.json`

Wird von `build.py` miterzeugt und enthält die gültigen Stufen mit ihren
Kategorien. Der Worker liest diese Datei (zwischengespeichert) und prüft
eingehende Werte dagegen. So bleibt die Prüfung automatisch synchron, ohne dass
der Worker je wieder angefasst werden muss.

### Cloudflare Worker

Rund 60 Zeilen JavaScript, Quelltext unter `worker/` im Repo versioniert, aber
nicht in `docs/` und damit nicht veröffentlicht.

Aufgaben:

1. Turnstile-Token prüfen — ohne gültiges Token wird nichts angenommen
2. Versteckte Falle prüfen (unsichtbares Feld; ausgefüllt = Bot)
3. Pflichtfelder, Maximallängen, Stufe und Kategorie gegen `kategorien.json`
4. Jede Einreichung ablehnen, die `http` enthält (wirksamster Einzelfilter,
   weil praktisch aller Spam Links transportieren will)
5. Ratenbegrenzung: höchstens fünf Einreichungen pro Stunde und Absender
   (Zähler in Cloudflare KV, Schlüssel = Hashwert der IP, Ablauf nach 1 Stunde)
6. Issue anlegen über ein GitHub-Token (Bot), das als Secret im Worker liegt

**Keine Aufwachzeit:** Workers laufen als Isolate im Cloudflare-Netz und starten
in unter einer Millisekunde — anders als schlafende Server bei Render oder
Heroku. Die Seite selbst liegt statisch auf GitHub Pages; der Worker wird erst
beim Klick auf „Absenden" angesprochen. Gratis-Kontingent: 100'000 Aufrufe/Tag.

**Anonymität:** Der Worker schreibt weder IP-Adresse noch Browserkennung
irgendwohin — nicht ins Issue, nicht in ein Log. Für die Ratenbegrenzung wird
die IP nur als Hashwert mit einer Stunde Gültigkeit gehalten und verfällt dann.
Das Issue enthält ausschliesslich die Formularfelder. Die einreichende Person
ist damit auch für die Betreuung nicht identifizierbar; das ist gewollt.

### `stayingclean/toolbox-vorschlaege`

Neues, öffentliches Repo. Enthält keinen Code und keinen Workflow, nur Issues
als Posteingang. Zwei Labels: `freigegeben` und `abgelehnt`. Ein Issue ohne
Label ist „noch nicht angeschaut".

Vorteil gegenüber einer eigenen Freigabe-Oberfläche: Es gibt die GitHub-App
fürs Handy, es ist nichts zu bauen und nichts zu warten.

**Issue-Format:** Titel = der vorgeschlagene Skill-Titel. Rumpf = die Felder als
Tabelle für Menschen, darunter ein maschinenlesbarer JSON-Block — dieselbe
Konvention wie bei den Formularen der Toolbox („Als HTML speichern"):
menschenlesbar oben, JSON eingebettet unten.

**Bekanntes Restrisiko:** Bei einem öffentlichen Posteingang ist jede
Einreichung sofort sichtbar, auch ungeprüfte. Ein hartnäckiger Mensch, der
Turnstile löst, bekommt eine Zeile Text öffentlich, bis das Issue gelöscht wird.
Notbremse: Issues im Vorschlags-Repo abschalten — die Formularseite zeigt dann
eine Hinweismeldung statt des Formulars. Das Toolbox-Repo bleibt davon
unberührt.

### `tools/vorschlaege_holen.py` + `vorschlaege.bat`

Doppelklick genügt, gleiche Bedienlogik wie `build.bat`.

1. `gh issue list --repo stayingclean/toolbox-vorschlaege --label freigegeben
   --state open` — holt die freigegebenen, noch offenen Vorschläge
2. JSON-Block aus jedem Issue lesen
3. Jede Zeile ans Blatt `Skills` der Excel anhängen
4. Die übernommenen Issues schliessen
5. `build.py` aufrufen

Der Push bleibt bewusst manuell. Nichts geht online, ohne dass es jemand
gesehen hat.

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

## Änderungen am bestehenden Projekt

| Datei | Was |
|---|---|
| `template-vorschlag.html` | neu — Vorlage der Formularseite, CSS eingebettet |
| `worker/` | neu — Quelltext des Workers, versioniert, nicht veröffentlicht |
| `tools/vorschlaege_holen.py`, `vorschlaege.bat` | neu — Freigegebene in die Excel übernehmen |
| `build.py` | erzeugt zusätzlich `docs/skill-vorschlagen.html` und `docs/kategorien.json`; liest Spalte `Von` |
| `template.html` | Detail-Dialog zeigt „Vorgeschlagen von …" |
| `tools/seed_excel.py` | schreibt Spalte `Von` mit |
| `skills_daten.xlsx` | neue Spalte `Von` im Blatt `Skills` |
| `docs/index.html` | neue Karte mit Verweis auf das Formular |
| `CLAUDE.md`, `ANLEITUNG.md` | Ablauf dokumentieren |

Unverändert bleiben `docs/skillsliste.html` (weiterhin generiert), der
Deploy-Workflow und alle übrigen Seiten.

## Bewusst nicht enthalten

- Bestehende Skills über das Formular ändern oder löschen
- Neue Kategorien vorschlagen (nur bestehende sind wählbar)
- Rückmeldung an die einreichende Person über den Stand — bei echter Anonymität
  gibt es keine Adresse
- Automatisches Veröffentlichen ohne manuellen Push
- Konto, Anmeldung oder Profil für Einreichende

## Prüfen vor Abschluss

- Formular auf Handy und Rechner bedienbar, Kategorie-Auswahl filtert korrekt
- Worker lehnt ab: fehlendes Turnstile-Token, ausgefüllte Falle, Link im Text,
  zu lange Felder, unbekannte Kategorie, sechste Einreichung innert einer Stunde
- Issue enthält weder IP noch Browserkennung
- `vorschlaege.bat` übernimmt mehrere Vorschläge in einem Durchgang, schliesst
  die Issues und erzeugt eine korrekte Skillsliste
- Bestehende Excel ohne Spalte `Von` baut weiterhin fehlerfrei
- Detail-Dialog zeigt die Namenszeile nur bei vorhandenem Namen
