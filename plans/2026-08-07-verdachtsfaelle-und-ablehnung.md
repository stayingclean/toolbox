# Verdachtsfälle melden und Ablehnungen begründen — Ausbaustufe 3, Teil 2

> **Für agentische Umsetzer:** ERFORDERLICHE SUB-SKILL: `superpowers:subagent-driven-development`
> (empfohlen) oder `superpowers:executing-plans`. Schritte nutzen Checkbox-Syntax (`- [ ]`).

**Ziel:** Die Duplikatprüfung verschweigt Zweifelsfälle nicht mehr, sondern legt sie
dem Menschen vor — mit **beiden** Einträgen im Volltext nebeneinander. Dazu kann er
einen Vorschlag direkt ablehnen; die Begründung landet als Kommentar im Issue.

**Architektur:** Der Prompt meldet neu zwei Sicherheitsstufen. Die Rückfrage zeigt
den eingereichten und den vorhandenen Skill vollständig und bietet drei Antworten.
Alle Schreibvorgänge auf GitHub — Schliessen wie Ablehnen — passieren **erst nach**
dem erfolgreichen Schreiben in die Excel.

**Technik:** Python 3.11+, `anthropic`, `gh`, pytest.

## Globale Vorgaben

- **Schweizer Schreibweise, durchgängig `ss` statt Eszett** — auch in Kommentaren,
  Meldungen und Testnamen.
- **Die Prüfung bleibt eine Zutat, keine Voraussetzung.** Ohne Schlüssel, ohne Netz,
  bei unerwarteter Antwort läuft die Übernahme unverändert weiter.
- **Die bestehende Zusicherung bleibt unangetastet:** Bricht der Lauf ab, ist nichts
  in die Excel geschrieben **und kein Issue verändert**. Deshalb passieren alle
  GitHub-Schreibvorgänge erst **nach** `in_excel_uebernehmen`.
- **`skills_daten.xlsx` ist das einzige Original.** Tests arbeiten auf `tmp_path`,
  Versuche auf Kopien im Scratchpad.
- **Kein Netzzugriff und kein `gh`-Aufruf in Tests.** Beides wird injiziert oder
  ersetzt.
- Der API-Schlüssel darf in keiner Ausgabe erscheinen.
- Testbefehl: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -q`
  Ausgangsstand: **177 Tests grün**, dazu `(cd worker && node --test)` → **46**.
- Arbeitsverzeichnis `C:\workspace\eraschle\.worktrees\formulare-toolbox`,
  Zweig `feature/formulare-toolbox`. **Nicht pushen**, namentlich committen,
  **niemals `git add -A`**.

## Entscheidungen des Menschen

1. **Ablehnen** heisst: Begründung als Kommentar, Label `abgelehnt`, Issue schliessen.
2. **Automatische Ablehnungen** (unbekannte Kategorie, fremde Herkunft, unlesbarer
   Vorschlag) bekommen einen Kommentar — aber **nur nach Rückfrage**, und sie werden
   **nicht** geschlossen und behalten ihr Label. Grund: Diese Fälle sind oft behebbar
   („Kategorie zuerst anlegen"), und der bestehende Schlusstext sagt ausdrücklich, das
   Label `freigegeben` könne stehen bleiben.
3. **Zwei Sicherheitsstufen** in der Antwort der KI: `sicher` und `unsicher`.

## Was der Mensch dabei wissen muss

Einreichende erhalten beim Absenden einen **Link auf ihr Issue**. Ein Kommentar ist
damit für diese Person sichtbar — er ist eine Antwort an jemanden, der etwas
beitragen wollte, keine interne Notiz. Das gehört in die Dokumentation.

## Dateien

| Datei | Änderung |
|---|---|
| `tools/duplikat_prompt.md` | Zweifelsfälle melden statt verwerfen, Sicherheitsstufe erklären |
| `tools/duplikat.py` | `sicherheit` im Schema und im Pflichtfeld-Filter |
| `tools/vorschlaege_holen.py` | Anzeige beider Einträge, drei Antworten, Ablehnung ausführen |
| `tests/test_duplikat.py`, `tests/test_vorschlaege_holen.py` | Tests |
| `CLAUDE.md`, `ANLEITUNG.md` | Dokumentation |

---

### Task 1: Zweifelsfälle melden statt verwerfen

**Files:**
- Modify: `tools/duplikat_prompt.md`
- Modify: `tools/duplikat.py`
- Test: `tests/test_duplikat.py`

**Interfaces:**
- Produces: Jeder Treffer hat zusätzlich `sicherheit` mit genau einem der Werte
  `"sicher"` oder `"unsicher"`. Der Pflichtfeld-Filter verwirft Treffer, bei denen
  das Feld fehlt oder einen anderen Wert trägt.

**Der Kern dieser Aufgabe steckt im Prompt, nicht im Schema.** Bisher steht dort
„Im Zweifel: kein Treffer." Diese Zeile hatte einen guten Grund — ein fälschlich
zurückgehaltener Vorschlag kostet einen Menschen seinen Beitrag. Der Grund
verschwindet nicht, er wird nur anders eingelöst: Statt zu schweigen, meldet die KI
den Verdacht **und sagt dazu, wie sicher sie ist**. Entschieden wird am Bildschirm.

- [ ] **Schritt 1: Fehlschlagende Tests schreiben**

An `tests/test_duplikat.py` anhängen:

```python
def treffer(**abweichung):
    grund = {
        "titel": "Lieblingslied auflegen", "aehnlich_zu": "Musik hören",
        "stufe": "Hoch", "kategorie": "Ablenkung",
        "begruendung": "Beide beschreiben gezieltes Musikhoeren.",
        "sicherheit": "sicher",
    }
    grund.update(abweichung)
    return grund


def test_sicherheit_wird_durchgereicht():
    client = FakeClient({"treffer": [treffer(sicherheit="unsicher")]})
    ergebnis = duplikat.pruefe_duplikate(NEUE, BESTAND, client)
    assert ergebnis[0]["sicherheit"] == "unsicher"


def test_treffer_ohne_sicherheit_wird_verworfen():
    ohne = {k: v for k, v in treffer().items() if k != "sicherheit"}
    assert duplikat.pruefe_duplikate(NEUE, BESTAND, FakeClient({"treffer": [ohne]})) == []


def test_treffer_mit_unbekannter_sicherheit_wird_verworfen():
    """Ein erfundener Wert darf nicht als 'sicher' durchgehen."""
    client = FakeClient({"treffer": [treffer(sicherheit="vielleicht")]})
    assert duplikat.pruefe_duplikate(NEUE, BESTAND, client) == []


def test_schema_verlangt_die_sicherheit():
    client = FakeClient()
    duplikat.pruefe_duplikate(NEUE, BESTAND, client)
    eigenschaften = client.gesehen["output_config"]["format"]["schema"]
    felder = eigenschaften["properties"]["treffer"]["items"]
    assert "sicherheit" in felder["required"]
    assert felder["properties"]["sicherheit"]["enum"] == ["sicher", "unsicher"]


def test_prompt_verlangt_auch_verdachtsfaelle():
    text = duplikat.lade_prompt(duplikat.PROJEKT)
    assert "unsicher" in text
    assert "Im Zweifel: kein Treffer" not in text, "die alte Regel muss weg sein"
```

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_duplikat.py -q`
Erwartet: FAIL — mehrere, u. a. `KeyError: 'sicherheit'` bzw. eine leere Liste.

- [ ] **Schritt 3: Schema und Filter erweitern**

In `tools/duplikat.py` im `SCHEMA` bei den Eigenschaften eines Treffers ergänzen:

```python
                    "sicherheit": {"type": "string", "enum": ["sicher", "unsicher"]},
```

und in der `required`-Liste desselben Objekts `"sicherheit"` aufnehmen.

Die Konstante daneben ergänzen:

```python
PFLICHTFELDER = ("titel", "aehnlich_zu", "stufe", "kategorie", "begruendung", "sicherheit")

# Das Schema verlangt diese beiden Werte bereits. Der Filter prueft sie trotzdem
# noch einmal: Das Schema bindet die KI, nicht die Antwort, die bei uns ankommt —
# ein erfundener dritter Wert wuerde sonst wie "sicher" behandelt.
SICHERHEITSSTUFEN = ("sicher", "unsicher")
```

Im Filter am Ende von `pruefe_duplikate` die zusätzliche Bedingung aufnehmen:

```python
        and t.get("sicherheit") in SICHERHEITSSTUFEN
```

- [ ] **Schritt 4: Prompt umschreiben**

In `tools/duplikat_prompt.md` den Absatz ersetzen, der heute mit „Melde nur Faelle,
bei denen du dir sicher bist" beginnt und mit „**Im Zweifel: kein Treffer.**" endet.
Neu:

```markdown
Melde **jeden** Verdacht — auch den, bei dem du dir nicht sicher bist. Entschieden
wird nicht von dir, sondern von einem Menschen, der beide Eintraege nebeneinander
sieht. Sag ihm dafuer, wie sicher du bist:

- `sicher` — dieselbe Handlung, nur anders formuliert. Du wuerdest die beiden
  Eintraege zusammenlegen.
- `unsicher` — es koennte dasselbe sein, aber es gibt einen erkennbaren
  Unterschied, oder die Beschreibungen sind zu knapp fuer ein klares Urteil.

Nutze `unsicher` grosszuegig. Ein Verdacht, den ein Mensch in zwei Sekunden
verwirft, kostet fast nichts. Ein verschwiegener Doppeleintrag steht dauerhaft in
der Liste — und ein faelschlich als `sicher` gemeldeter Vorschlag kostet einer
Person ihren Beitrag.

Was **keine** Dublette ist, bleibt auch kein Verdachtsfall: Die Ausnahmen oben
gelten unveraendert. Melde nichts, nur um etwas zu melden.

Begruende jeden Treffer in einem kurzen Satz, der die gemeinsame Handlung nennt.
```

- [ ] **Schritt 5: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -q`
Erwartet: PASS, **182** Tests (177 + 5).

- [ ] **Schritt 6: Gegenprobe**

Setz auf einer Kopie im Scratchpad nacheinander ein und melde je das Ergebnis:

| Mutation | Erwartung |
|---|---|
| `sicherheit` aus `PFLICHTFELDER` entfernen | mindestens 1 Test rot |
| Prüfung gegen `SICHERHEITSSTUFEN` entfernen | mindestens 1 Test rot |
| `enum` aus dem Schema entfernen | mindestens 1 Test rot |

- [ ] **Schritt 7: Commit**

```bash
git add tools/duplikat.py tools/duplikat_prompt.md tests/test_duplikat.py
git commit -m "Verdachtsfaelle melden statt verwerfen"
```

---

### Task 2: Beide Einträge im Volltext zeigen

**Files:**
- Modify: `tools/vorschlaege_holen.py`
- Test: `tests/test_vorschlaege_holen.py`

**Interfaces:**
- Consumes: `treffer_je_issue(treffer, uebernehmen) -> dict` (vorhanden)
- Produces: `skill_im_bestand(bestand: dict, titel: str) -> dict | None` — sucht den
  vorhandenen Skill über **alle** Stufen und Kategorien; liefert `{"e","t","b","tip"}`
  oder `None`.
- Produces: `gegenueberstellung(neu: dict, alt: dict | None, t: dict) -> str` — der
  fertige Anzeigetext.

**Warum das die eigentliche Verbesserung ist:** Heute stehen dort nur zwei Titel.
Ob „Lieblingslied auflegen" wirklich dasselbe ist wie „Musik hören", kann daran
niemand entscheiden — die Beschreibungen sind der Unterschied. Wer nicht
entscheiden kann, drückt im Zweifel `ü`, und dann war die ganze Prüfung umsonst.

**Achtung bei der Suche:** `aehnlich_zu` ist der Titel des **vorhandenen** Skills.
Stufe und Kategorie im Treffer beziehen sich laut Prompt auf den **eingereichten**
Vorschlag — sie taugen also **nicht** zum Auffinden des alten Eintrags. Such über
den ganzen Bestand. Wird nichts gefunden, ist das kein Fehler: Dann zeigst du nur
den neuen Eintrag und schreibst dazu, dass der vorhandene nicht gefunden wurde.

- [ ] **Schritt 1: Fehlschlagende Tests schreiben**

An `tests/test_vorschlaege_holen.py` anhängen:

```python
BESTAND_ANZEIGE = {
    "hoch": {"kategorien": [{"label": "Ablenkung", "skills": [
        {"e": "🎧", "t": "Musik hören", "b": "Ein Lied auflegen und zuhoeren.",
         "tip": "💡 Kopfhoerer", "von": "Max", "erg": ""},
    ]}]},
    "mittel": {"kategorien": []},
    "tief": {"kategorien": []},
}


def test_skill_im_bestand_findet_ueber_alle_stufen():
    gefunden = vh.skill_im_bestand(BESTAND_ANZEIGE, "Musik hören")
    assert gefunden["b"] == "Ein Lied auflegen und zuhoeren."


def test_skill_im_bestand_ohne_treffer_ist_none():
    assert vh.skill_im_bestand(BESTAND_ANZEIGE, "Gibt es nicht") is None


def test_gegenueberstellung_zeigt_beide_beschreibungen():
    neu = {"emoji": "🎵", "titel": "Lieblingslied auflegen",
           "beschreibung": "Ein Lied aussuchen und nur darauf achten.",
           "tipp": "", "stufe": "Hoch", "kategorie": "Ablenkung"}
    alt = vh.skill_im_bestand(BESTAND_ANZEIGE, "Musik hören")
    t = {"titel": "Lieblingslied auflegen", "aehnlich_zu": "Musik hören",
         "stufe": "Hoch", "kategorie": "Ablenkung",
         "begruendung": "Beide beschreiben gezieltes Musikhoeren.",
         "sicherheit": "unsicher"}
    text = vh.gegenueberstellung(neu, alt, t)
    assert "Ein Lied aussuchen und nur darauf achten." in text
    assert "Ein Lied auflegen und zuhoeren." in text, "der vorhandene Text fehlt"
    assert "unsicher" in text.lower()
    assert "Beide beschreiben gezieltes Musikhoeren." in text


def test_gegenueberstellung_ohne_alten_eintrag_sagt_es():
    neu = {"emoji": "🎵", "titel": "Neu", "beschreibung": "Text.", "tipp": "",
           "stufe": "Hoch", "kategorie": "Ablenkung"}
    t = {"titel": "Neu", "aehnlich_zu": "Verschwunden", "stufe": "Hoch",
         "kategorie": "Ablenkung", "begruendung": "…", "sicherheit": "sicher"}
    text = vh.gegenueberstellung(neu, None, t)
    assert "Verschwunden" in text
    assert "nicht gefunden" in text.lower()
```

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_vorschlaege_holen.py -k "bestand or gegenueber" -q`
Erwartet: FAIL — `AttributeError: module 'vorschlaege_holen' has no attribute 'skill_im_bestand'`.

- [ ] **Schritt 3: Suche und Anzeige umsetzen**

In `tools/vorschlaege_holen.py` vor `nachfragen` ergänzen:

```python
def skill_im_bestand(bestand: dict, titel: str):
    """Sucht einen vorhandenen Skill ueber ALLE Stufen und Kategorien.

    Bewusst nicht ueber Stufe und Kategorie aus dem Treffer: die beziehen sich
    laut Prompt auf den EINGEREICHTEN Vorschlag, nicht auf den gefundenen
    Bestandsskill. Wer danach suchte, faende oft nichts.
    """
    for stufe in bestand.values():
        for kategorie in stufe.get("kategorien", []):
            for skill in kategorie.get("skills", []):
                if skill.get("t") == titel:
                    return skill
    return None


def gegenueberstellung(neu: dict, alt, t: dict) -> str:
    """Stellt den eingereichten und den vorhandenen Eintrag untereinander.

    Untereinander, nicht nebeneinander: Beschreibungen sind zu lang fuer zwei
    Spalten in einem Konsolenfenster, und umgebrochener Text laesst sich
    schlechter vergleichen als zwei ganze Absaetze.
    """
    wie_sicher = "SICHER dieselbe Handlung" if t["sicherheit"] == "sicher" else "unsicher – bitte selbst beurteilen"
    zeilen = [
        f'\n⚠ Moegliche Dublette ({wie_sicher})',
        f'   Einschaetzung: {t["begruendung"]}',
        "",
        f'   NEU eingereicht  ({t["stufe"]} / {t["kategorie"]}):',
        f'     {neu.get("emoji", "")} {neu["titel"]}',
        f'     {neu["beschreibung"]}',
    ]
    if neu.get("tipp"):
        zeilen.append(f'     Tipp: {neu["tipp"]}')
    zeilen.append("")
    if alt is None:
        zeilen.append(f'   VORHANDEN: „{t["aehnlich_zu"]}" – im Bestand nicht gefunden.')
    else:
        zeilen += [
            "   VORHANDEN bereits:",
            f'     {alt.get("e", "")} {alt.get("t", "")}',
            f'     {alt.get("b", "")}',
        ]
        if alt.get("tip"):
            zeilen.append(f'     {alt["tip"]}')
    return "\n".join(zeilen)
```

- [ ] **Schritt 4: Tests laufen lassen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -q`
Erwartet: PASS, **186** Tests (182 + 4).

- [ ] **Schritt 5: Commit**

```bash
git add tools/vorschlaege_holen.py tests/test_vorschlaege_holen.py
git commit -m "Rueckfrage zeigt beide Eintraege im Volltext"
```

---

### Task 3: Drei Antworten und die Begründung

**Files:**
- Modify: `tools/vorschlaege_holen.py`
- Test: `tests/test_vorschlaege_holen.py`

**Interfaces:**
- Ändert: `nachfragen(treffer, uebernehmen, bestand, eingabe=input) -> tuple[list, list]`
  Liefert `(ueberspringen, ablehnungen)` — `ueberspringen` sind Issue-Nummern wie
  bisher, `ablehnungen` ist eine Liste von `(nummer, grund)`.
- Der Parameter `bestand` ist **neu** und steht vor `eingabe`.

**Die tragende Eigenschaft dieser Aufgabe:** `nachfragen` **schreibt nichts** auf
GitHub. Es sammelt nur. Ausgeführt wird erst nach dem erfolgreichen Schreiben in die
Excel (Task 4). Sonst hinterliesse ein Abbruch geschlossene Issues bei ungeschriebener
Mappe — und die Zusicherung „bricht der Lauf ab, ist nichts geschrieben und kein
Issue verändert" wäre gebrochen.

- [ ] **Schritt 1: Fehlschlagende Tests schreiben**

```python
def uebernehmen_neu():
    return [({"number": 7}, {"art": "neu", "stufe": "Hoch", "kategorie": "Ablenkung",
              "titel": "Lieblingslied auflegen", "emoji": "🎵",
              "beschreibung": "Ein Lied aussuchen.", "tipp": ""})]


TREFFER_NEU = [{"titel": "Lieblingslied auflegen", "aehnlich_zu": "Musik hören",
                "stufe": "Hoch", "kategorie": "Ablenkung",
                "begruendung": "Beide beschreiben gezieltes Musikhoeren.",
                "sicherheit": "sicher"}]


def test_ablehnen_sammelt_nummer_und_grund():
    antworten = iter(["a", "Steht schon drin als Musik hören."])
    raus, ablehnungen = vh.nachfragen(TREFFER_NEU, uebernehmen_neu(), BESTAND_ANZEIGE,
                                      eingabe=lambda _: next(antworten))
    assert raus == [7], "abgelehnt heisst auch: nicht eintragen"
    assert ablehnungen == [(7, "Steht schon drin als Musik hören.")]


def test_ablehnen_verlangt_eine_begruendung():
    """Eine leere Begruendung waere fuer die einreichende Person wertlos."""
    antworten = iter(["a", "   ", "", "Doppelt."])
    raus, ablehnungen = vh.nachfragen(TREFFER_NEU, uebernehmen_neu(), BESTAND_ANZEIGE,
                                      eingabe=lambda _: next(antworten))
    assert ablehnungen == [(7, "Doppelt.")]


def test_uebernehmen_sammelt_keine_ablehnung():
    raus, ablehnungen = vh.nachfragen(TREFFER_NEU, uebernehmen_neu(), BESTAND_ANZEIGE,
                                      eingabe=lambda _: "ü")
    assert (raus, ablehnungen) == ([], [])


def test_weiter_sammelt_keine_ablehnung():
    raus, ablehnungen = vh.nachfragen(TREFFER_NEU, uebernehmen_neu(), BESTAND_ANZEIGE,
                                      eingabe=lambda _: "w")
    assert (raus, ablehnungen) == ([7], [])


def test_ohne_tastatur_wird_nicht_abgelehnt():
    """Ohne Eingabemoeglichkeit darf NICHTS auf GitHub geschrieben werden."""
    def keine_tastatur(_):
        raise EOFError

    raus, ablehnungen = vh.nachfragen(TREFFER_NEU, uebernehmen_neu(), BESTAND_ANZEIGE,
                                      eingabe=keine_tastatur)
    assert raus == [7]
    assert ablehnungen == [], "ohne Rueckfrage keine Ablehnung"


def test_abbruch_mitten_in_der_begruendung_lehnt_nicht_ab():
    """Strg+C waehrend der Begruendung darf keine halbe Ablehnung hinterlassen."""
    antworten = iter(["a"])

    def dann_schluss(_):
        try:
            return next(antworten)
        except StopIteration:
            raise EOFError

    raus, ablehnungen = vh.nachfragen(TREFFER_NEU, uebernehmen_neu(), BESTAND_ANZEIGE,
                                      eingabe=dann_schluss)
    assert ablehnungen == []
    assert raus == [7]
```

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_vorschlaege_holen.py -k "ablehn or nachfrag or tastatur or begruendung" -q`
Erwartet: FAIL — `TypeError: nachfragen() takes 2 positional arguments but 3 were given`.

- [ ] **Schritt 3: `nachfragen` umbauen**

Ersetze die bestehende Funktion durch:

```python
def nachfragen(treffer: list, uebernehmen: list, bestand: dict, eingabe=input):
    """Legt jeden Verdacht vor und sammelt die Entscheidungen.

    Liefert `(ueberspringen, ablehnungen)`:
      ueberspringen — Issue-Nummern, die NICHT eingetragen werden
      ablehnungen   — Liste von (Nummer, Begruendung)

    Diese Funktion schreibt NICHTS auf GitHub. Sie sammelt nur. Ausgefuehrt wird
    erst nach dem erfolgreichen Schreiben in die Excel — sonst hinterliesse ein
    Abbruch geschlossene Issues bei ungeschriebener Mappe.
    """
    nach_nummer = {i["number"]: d for i, d in uebernehmen}
    ueberspringen, ablehnungen = [], []
    for nummer, t in treffer_je_issue(treffer, uebernehmen).items():
        neu = nach_nummer[nummer]
        print(gegenueberstellung(neu, skill_im_bestand(bestand, t["aehnlich_zu"]), t))
        while True:
            try:
                wahl = eingabe(
                    "   [ü]bernehmen  [w]eiter (spaeter entscheiden)  "
                    "[a]blehnen (mit Begruendung)  ? "
                )
            except EOFError:
                # Kein Mensch am Bildschirm: nicht raten und nichts schreiben.
                print("   Keine Eingabe moeglich – wird uebersprungen.")
                ueberspringen.append(nummer)
                break
            wahl = wahl.strip().lower()
            if wahl in ("ü", "u", "ue"):
                break
            if wahl == "w":
                ueberspringen.append(nummer)
                break
            if wahl == "a":
                grund = begruendung_erfragen(eingabe)
                if grund is None:
                    # Abbruch waehrend der Begruendung: nicht ablehnen, nur
                    # ueberspringen. Eine Ablehnung ohne Begruendung waere fuer
                    # die einreichende Person wertlos.
                    ueberspringen.append(nummer)
                    break
                ueberspringen.append(nummer)
                ablehnungen.append((nummer, grund))
                break
            print("   Bitte ü, w oder a eingeben.")
    return ueberspringen, ablehnungen


def begruendung_erfragen(eingabe=input):
    """Fragt nach einer Begruendung. Liefert None, wenn keine kommt.

    Der Text wird als Kommentar im Issue veroeffentlicht und ist fuer die
    einreichende Person ueber ihren Statuslink sichtbar. Deshalb wird nicht
    stillschweigend eine leere Begruendung akzeptiert.
    """
    print("   Die Begruendung erscheint im Issue und ist fuer die einreichende")
    print("   Person sichtbar. Bitte kurz und freundlich.")
    while True:
        try:
            grund = eingabe("   Begruendung: ")
        except EOFError:
            return None
        grund = grund.strip()
        if grund:
            return grund
        print("   Bitte eine kurze Begruendung eingeben (oder Strg+C zum Abbrechen).")
```

- [ ] **Schritt 4: Aufrufstelle in `main()` anpassen**

Die bestehende Zeile `raus = nachfragen(treffer, uebernehmen)` wird zu:

```python
            raus, ablehnungen = nachfragen(treffer, uebernehmen, bestand)
```

`ablehnungen` muss — wie `raus` — **vor** dem `try` mit einem leeren Wert
vorbelegt werden, damit die Variable auch dann existiert, wenn der Block scheitert.

- [ ] **Schritt 5: Volle Testreihe**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -q`
Erwartet: PASS, **192** Tests (186 + 6).

- [ ] **Schritt 6: Commit**

```bash
git add tools/vorschlaege_holen.py tests/test_vorschlaege_holen.py
git commit -m "Drei Antworten bei der Rueckfrage, Begruendung beim Ablehnen"
```

---

### Task 4: Ablehnungen ausführen und automatische Fälle nachfragen

**Files:**
- Modify: `tools/vorschlaege_holen.py`
- Test: `tests/test_vorschlaege_holen.py`

**Interfaces:**
- Produces: `issue_ablehnen(nummer: int, grund: str)` — schreibt den Kommentar,
  setzt Label `abgelehnt` und schliesst das Issue.
- Produces: `issue_kommentieren(nummer: int, text: str)` — schreibt nur einen
  Kommentar.
- Produces: `automatische_ablehnungen_melden(abgelehnt: list, eingabe=input) -> list`
  — fragt je Fall nach und liefert die Liste `(nummer, text)`, die kommentiert
  werden soll.

**Wo alles hingehört — das ist der heikle Teil:** Sämtliche GitHub-Schreibvorgänge
passieren **nach** `in_excel_uebernehmen`, im selben Abschnitt, in dem heute schon
die übernommenen Issues geschlossen werden. Vorher wird nur gesammelt und gefragt.
Grund: Die dokumentierte Zusicherung lautet „Bricht der Lauf ab, ist nichts in die
Excel geschrieben und kein Issue verändert". Diese Reihenfolge ist das Einzige, was
sie hält.

**Zweitens:** Ein Fehlschlag beim Ablehnen darf den Lauf nicht abbrechen — an dieser
Stelle steht die Übernahme bereits in der Mappe. Er wird gemeldet, mit derselben
Sorgfalt wie beim bestehenden Schliessen: Der Mensch muss erfahren, was er von Hand
nachholen muss.

- [ ] **Schritt 1: Fehlschlagende Tests schreiben**

```python
def test_issue_ablehnen_kommentiert_labelt_und_schliesst(monkeypatch):
    aufrufe = []
    monkeypatch.setattr(vh.subprocess, "run",
                        lambda befehl, **k: aufrufe.append(befehl) or types.SimpleNamespace(returncode=0))
    vh.issue_ablehnen(7, "Steht schon drin.")
    flach = [" ".join(b) for b in aufrufe]
    assert any("comment" in b and "Steht schon drin." in b for b in flach)
    assert any("abgelehnt" in b for b in flach), "das Label fehlt"
    assert any("close" in b for b in flach)


def test_automatische_ablehnung_wird_nur_nach_zustimmung_kommentiert():
    faelle = [({"number": 9, "title": "Test"}, "Kategorie existiert nicht")]
    assert vh.automatische_ablehnungen_melden(faelle, eingabe=lambda _: "n") == []
    zu_schreiben = vh.automatische_ablehnungen_melden(faelle, eingabe=lambda _: "j")
    assert len(zu_schreiben) == 1
    assert zu_schreiben[0][0] == 9
    assert "Kategorie existiert nicht" in zu_schreiben[0][1]


def test_automatische_ablehnung_ohne_tastatur_schreibt_nichts():
    def keine_tastatur(_):
        raise EOFError

    faelle = [({"number": 9, "title": "Test"}, "Kategorie existiert nicht")]
    assert vh.automatische_ablehnungen_melden(faelle, eingabe=keine_tastatur) == []


def test_main_lehnt_erst_nach_dem_schreiben_ab(tmp_path, monkeypatch):
    """Die Reihenfolge ist die Zusicherung: erst die Mappe, dann GitHub."""
    reihenfolge = []
    monkeypatch.setattr(vh, "in_excel_uebernehmen",
                        lambda *a, **k: reihenfolge.append("excel") or 1)
    monkeypatch.setattr(vh, "issue_ablehnen",
                        lambda *a, **k: reihenfolge.append("ablehnen"))
    monkeypatch.setattr(vh, "issue_schliessen",
                        lambda *a, **k: reihenfolge.append("schliessen"))
    # Rest der Attrappen wie in den vorhandenen main-Tests aufsetzen,
    # mit genau einem Treffer und der Antwort "a" plus Begruendung.
    ...
    assert reihenfolge.index("excel") < reihenfolge.index("ablehnen")


def test_fehler_beim_ablehnen_bricht_den_lauf_nicht_ab(capsys, monkeypatch):
    """Die Uebernahme steht hier schon in der Mappe – ein Abbruch waere fatal."""
    ...
    ausgabe = capsys.readouterr().out
    assert "von Hand" in ausgabe
```

Die mit `...` markierten Stellen baust du nach dem Muster der vorhandenen
`main`-Tests in derselben Datei auf — sieh dort nach, welche Attrappen nötig sind,
und **erfinde keine neuen Hilfsfunktionen**, wenn es schon welche gibt.

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests/test_vorschlaege_holen.py -k "ablehn" -q`
Erwartet: FAIL — `AttributeError: module 'vorschlaege_holen' has no attribute 'issue_ablehnen'`.

- [ ] **Schritt 3: Die beiden GitHub-Funktionen**

Neben `issue_schliessen` ergänzen:

```python
def issue_kommentieren(nummer: int, text: str):
    subprocess.run(
        ["gh", "issue", "comment", str(nummer), "--repo", REPO, "--body", text],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )


def issue_ablehnen(nummer: int, grund: str):
    """Begruendung als Kommentar, Label `abgelehnt`, Issue schliessen.

    Reihenfolge mit Absicht: Erst der Kommentar. Scheitert das Schliessen
    danach, steht die Begruendung wenigstens schon da — umgekehrt waere das
    Issue zu, ohne dass jemand erfaehrt, warum.
    """
    issue_kommentieren(nummer, grund)
    subprocess.run(
        ["gh", "issue", "edit", str(nummer), "--repo", REPO,
         "--add-label", "abgelehnt", "--remove-label", LABEL],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    subprocess.run(
        ["gh", "issue", "close", str(nummer), "--repo", REPO],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
```

- [ ] **Schritt 4: Rückfrage für die automatischen Fälle**

```python
def automatische_ablehnungen_melden(faelle: list, eingabe=input) -> list:
    """Fragt je Fall, ob der Grund als Kommentar ins Issue soll.

    Der Text ist fuer die einreichende Person ueber ihren Statuslink sichtbar.
    Darum wird er vorher gezeigt und nichts ohne Zustimmung geschrieben.
    Diese Faelle werden NICHT geschlossen: Sie sind oft behebbar (etwa die
    Kategorie zuerst anlegen), und dann soll der naechste Lauf sie wieder
    anbieten.
    """
    zu_schreiben = []
    if not faelle:
        return zu_schreiben
    print("\nZu den nicht uebernommenen Vorschlaegen kannst du eine Rueckmeldung")
    print("ins Issue schreiben. Sie ist fuer die einreichende Person sichtbar.")
    for issue, grund in faelle:
        text = f"Nicht uebernommen: {grund}"
        print(f'\n   Issue #{issue["number"]} „{issue["title"]}"')
        print(f"   Vorgeschlagener Kommentar: {text}")
        try:
            wahl = eingabe("   Schreiben? [j]a  [n]ein  ? ")
        except EOFError:
            print("   Keine Eingabe moeglich – es wird nichts geschrieben.")
            return zu_schreiben
        if wahl.strip().lower() in ("j", "ja"):
            zu_schreiben.append((issue["number"], text))
    return zu_schreiben
```

- [ ] **Schritt 5: In `main()` einhängen — nach dem Schreiben**

Im Abschnitt, in dem heute die übernommenen Issues geschlossen werden, **nach**
der Schliess-Schleife ergänzen:

```python
    for nummer, grund in ablehnungen:
        try:
            issue_ablehnen(nummer, grund)
            print(f"  ✗ Issue #{nummer} abgelehnt und geschlossen.")
        except subprocess.CalledProcessError:
            print(
                f"\n⚠ Issue #{nummer} konnte nicht abgelehnt werden.\n"
                f"   Bitte von Hand auf github.com/{REPO}/issues/{nummer}\n"
                f"   das Label `abgelehnt` setzen und schliessen. Begruendung:\n"
                f"   {grund}"
            )
```

Und **danach** die Rückfrage für die automatischen Fälle.

> **⚠ Wichtig, sonst wird doppelt gefragt.** `abgelehnt` enthält **nicht nur** die
> automatisch aussortierten Vorschläge. Weiter oben in `main()` werden auch die bei
> der Duplikat-Rückfrage übersprungenen Issues dort einsortiert (mit dem Grund aus
> `gruende` bzw. dem Rückfalltext „beim Nachfragen zur Duplikatpruefung
> uebersprungen"). Würdest du die ganze Liste übergeben, bekäme der Mensch für
> genau die Issues, die er soeben beantwortet hat, **eine zweite Rückfrage** — und
> für ein „später entscheiden" womöglich einen Kommentar, den er nie wollte.
>
> Übergib deshalb nur die Fälle, die **nicht** aus der Rückfrage stammen. Die
> Issue-Nummern aus `raus` sind genau diese Menge. Prüf im Code nach, wie `raus`
> an dieser Stelle heisst und ob es dort noch verfügbar ist — und schreib einen
> Kommentar dazu, damit es niemand „vereinfacht". Ein Test muss festhalten, dass
> ein bei der Rückfrage übersprungenes Issue **kein** zweites Mal auftaucht.

```python
    aus_rueckfrage = {n for n in raus}
    automatisch = [(i, g) for i, g in abgelehnt if i["number"] not in aus_rueckfrage]
    for nummer, text in automatische_ablehnungen_melden(automatisch):
        try:
            issue_kommentieren(nummer, text)
        except subprocess.CalledProcessError:
            print(f"⚠ Der Kommentar zu Issue #{nummer} konnte nicht geschrieben werden.")
```

- [ ] **Schritt 6: Volle Testreihe und Leerlauf**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -q`
Erwartet: PASS. Nenn mir die tatsächliche Zahl.

Run: `uv run tools/vorschlaege_holen.py`
Erwartet: „Keine freigegebenen Vorschläge offen. Nichts zu tun." — unverändert.

- [ ] **Schritt 7: Gegenprobe**

Auf einer Kopie im Scratchpad, je das Ergebnis melden:

| Mutation | Erwartung |
|---|---|
| Ablehnungen **vor** `in_excel_uebernehmen` ausführen | mindestens 1 Test rot |
| `issue_ablehnen` schliesst, ohne zu kommentieren | mindestens 1 Test rot |
| Zustimmung bei den automatischen Fällen übergehen | mindestens 1 Test rot |
| Ganze `abgelehnt`-Liste statt nur der automatischen Fälle übergeben | mindestens 1 Test rot |
| `EOFError`-Zweig in `begruendung_erfragen` entfernen | mindestens 1 Test rot |

- [ ] **Schritt 8: Commit**

```bash
git add tools/vorschlaege_holen.py tests/test_vorschlaege_holen.py
git commit -m "Ablehnungen ausfuehren, automatische Faelle nach Rueckfrage kommentieren"
```

---

### Task 5: Dokumentation

**Files:**
- Modify: `ANLEITUNG.md`, `CLAUDE.md`

- [ ] **Schritt 1: `ANLEITUNG.md`**

Den Abschnitt zur Dubletten-Warnung ersetzen. Neu gehören hinein:

- Es kommen jetzt **auch Verdachtsfälle**, nicht nur sichere Treffer. In der
  Meldung steht, wie sicher die Einschätzung ist.
- Du siehst **beide Einträge vollständig** — den neuen und den vorhandenen —
  und entscheidest selbst.
- Drei Antworten: **ü** eintragen, **w** später entscheiden (Issue bleibt offen),
  **a** ablehnen mit Begründung.
- **Wichtig:** Die Begründung erscheint im Issue und ist für die einreichende
  Person über ihren Statuslink **sichtbar**. Kurz und freundlich formulieren.
- Bei abgelehnten Vorschlägen wird das Issue geschlossen und das Label gesetzt —
  das musst du nicht mehr von Hand tun.
- Zu den automatisch aussortierten Vorschlägen fragt das Programm, ob der Grund
  als Kommentar ins Issue soll. Diese Issues bleiben offen.

- [ ] **Schritt 2: `CLAUDE.md`**

Im Abschnitt zur Duplikatprüfung ergänzen:

- Zwei Sicherheitsstufen (`sicher`/`unsicher`), im Schema als `enum` gebunden und
  im Filter noch einmal geprüft.
- Die Anzeige sucht den vorhandenen Skill über **alle** Stufen, weil Stufe und
  Kategorie im Treffer zum **eingereichten** Vorschlag gehören.
- **Die Reihenfolge ist die Zusicherung:** `nachfragen` schreibt nichts auf GitHub,
  es sammelt nur. Ablehnen, Kommentieren und Schliessen passieren erst **nach**
  `in_excel_uebernehmen`. Wer das umstellt, bricht „bei Abbruch ist nichts
  geschrieben und kein Issue verändert".
- Automatische Ablehnungen werden **nicht** geschlossen (sie sind oft behebbar) und
  nur nach Rückfrage kommentiert.

- [ ] **Schritt 3: Prüfen und committen**

Run: `uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -q`
Erwartet: unverändert grün.

```bash
git add ANLEITUNG.md CLAUDE.md
git commit -m "Verdachtsfaelle und Ablehnungen dokumentieren"
```

---

## Selbstprüfung des Plans

**Abdeckung der drei Wünsche:**

| Wunsch | Aufgabe |
|---|---|
| Zweifelsfälle melden statt verwerfen | 1 |
| Beide Einträge in der Rückmeldung auflisten | 2 |
| Nachfragen, wie damit umzugehen ist | 3 |
| Bei Ablehnung nach Begründung fragen | 3 |
| Begründung ins Issue eintragen | 4 |

**Erhaltene Zusicherungen:** Die Prüfung bleibt eine Zutat (Task 3 und 4 fassen die
bestehende Absicherung nicht an); „bei Abbruch nichts geschrieben, kein Issue
verändert" wird durch die Reihenfolge in Task 4 gehalten und dort mit einem Test
festgenagelt.

**Namensabgleich:** `skill_im_bestand`, `gegenueberstellung`, `nachfragen`,
`begruendung_erfragen`, `issue_kommentieren`, `issue_ablehnen`,
`automatische_ablehnungen_melden`, `SICHERHEITSSTUFEN` — in allen Aufgaben gleich
geschrieben.

**Bewusst offen gelassen:** Die Rückfragezeile nennt weiterhin keine Issue-Nummer.
Eine frühere Prüfung hatte das angeregt; es bleibt ein Zielkonflikt mit der
zeichengleichen Beispielausgabe in `ANLEITUNG.md`. Da Task 5 diese Ausgabe ohnehin
neu beschreibt, **darf** der Umsetzer die Nummer in Task 2 ergänzen — dann aber die
Anleitung im selben Zug nachziehen.
