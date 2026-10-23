# Gemeinsamer Token-Satz — Umsetzungsplan

> **Für agentische Umsetzung:** Dieser Plan wird Aufgabe für Aufgabe abgearbeitet,
> mit `superpowers:subagent-driven-development` oder `superpowers:executing-plans`.
> Die Schritte tragen Kästchen (`- [ ]`) zum Abhaken.

**Ziel:** Eine Datei `docs/tokens.css` hält die neun Farben und zwei Schriften,
die die Seiten der Toolbox schon heute gemeinsam benutzen — und vier Seiten
beziehen sie von dort statt sie je selbst zu deklarieren.

**Vorgehen:** Kein Umbau, sondern ein Herausziehen. Die vier Seiten benutzen
**bereits identische Variablennamen** (`--accent`, `--card`, `--muted` …) mit
**identischen Werten**. Es wird nichts umbenannt und keine Regel angefasst — nur
der `:root`-Block entfernt und die Datei eingebunden. Darum ist jede Aufgabe
rückgängig zu machen und das Ergebnis muss **pixelgleich** sein.

**Technik:** Reines CSS, Vanilla. Keine Bibliothek, kein Build-Schritt ausser
dem bestehenden `build.py`. Tests in pytest.

**Entwurf:** `specs/2026-10-23-stil-bibliothek-design.md` — verbindlich,
enthält die vier Entscheide des Benutzers und die Begründungen.

## Globale Randbedingungen

- **Keine fremden Bibliotheken** (`CLAUDE.md` Punkt 3, bestätigt 2026-10-23).
- **`docs/skillsliste.html` und `docs/flyer-editor.html` werden nicht
  angefasst** — Entscheid 2 des Benutzers. Nach jedem Lauf von `build.py` muss
  `docs/skillsliste.html` **byteweise unverändert** sein.
- **`docs/budgetvorlage.html` ist nicht Teil dieses Plans.** Sie wird getrennt
  umgebaut, samt der drei warmen Grauwerte (Entscheid 4).
- **Veröffentlicht wird nur `docs/`.** `docs/tokens.css` liegt darin.
- **Die Fusszeilen-Konvention bleibt** (`CLAUDE.md`): Urheber-Credit und
  Kaffee-Link in jeder Seite. Ihr CSS wird hier **nicht** vereinheitlicht — das
  wäre eine Komponente, und Entscheid 1 sagt «nur Tokens».
- **Signalfarben bleiben lokal.** `--warn`, `--warn-tint`, `--warn-border`,
  `--ok`, `--ok-tint` gehören **nicht** in `tokens.css`: Plakat und Anleitung
  haben für `--warn` und `--warn-tint` verschiedene Werte (`#8A5A2B`/`#FBF1E4`
  gegen `#B45309`/`#FFF4E5`). Welcher gilt, ist im Entwurf ausdrücklich offen.

## Der Token-Satz

Erhoben am Stand `ec04785`, nachgeprüft über alle vier Dateien.

```css
--bg:          #FAF8F5   /* Papier */
--card:        #FFFFFF   /* Karte, Fläche */
--card-hover:  #F5FAFA   /* Karte, überfahren */
--border:      #E8E4DF   /* Linie */
--text:        #1C1C1C   /* Fliesstext */
--muted:       #7A7268   /* gedämpfter Text */
--accent:      #008080   /* Akzent */
--accent-dark: #006666   /* Akzent, dunkel */
--accent-tint: #E6F2F2   /* Akzent, zart */
--font-display: 'Playfair Display', Georgia, serif
--font-body:    'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
```

**Acht davon sind in allen vier Dateien byteweise identisch.** `--card-hover`
steht heute nur in Übersicht und Anleitung, mit demselben Wert; Vorschlagsformular
und Plakat bekommen es ungenutzt dazu, was nichts kostet.

**Zwei weichen ab und brauchen eine Überschreibung:** `docs/plakat.html` setzt
`--font-body` und `--font-display` auf System- und Georgia-Schriften, weil die
Seite **keine Schrift von aussen lädt**. Ohne Überschreibung verwiese sie auf
Inter und Playfair; wer die Schriften lokal installiert hat, sähe die Seite
anders als heute. Die Überschreibung bleibt also in der Seite und wird dort
begründet.

## Dateien

| Datei | Rolle |
|---|---|
| `docs/tokens.css` | **neu** — der Token-Satz, eine `:root`-Regel, sonst nichts |
| `tests/test_tokens.py` | **neu** — nagelt die Werte fest und meldet Auseinanderlaufen |
| `docs/index.html` | `:root` raus, `<link>` rein |
| `template-vorschlag.html` | dito; `docs/skill-vorschlagen.html` entsteht daraus per `build.py` |
| `docs/plakat.html` | `:root` raus bis auf `--warn*` und die zwei Schrift-Überschreibungen |
| `docs/claude-anleitung/stil.css` | `@import` oben; die HTML-Seiten bleiben unberührt |
| `CLAUDE.md` | die neue Regel |

**Warum die Anleitung ein `@import` bekommt und keinen `<link>`:** Ihre vierzehn
Seiten binden `stil.css` ein — sechs aus diesem Repo und **acht aus
`stayingclean/ki-tasks`**, die der Deploy darüberkopiert. Ein `<link>` müsste in
alle vierzehn, also auch in ein zweites Repo. Ein `@import url("../tokens.css")`
am Kopf von `stil.css` erreicht alle, ohne dass drüben eine Zeile geändert wird.
Der Preis ist ein zusätzlicher, serialisierter Abruf für eine Datei von unter
einem Kilobyte. **Das ist meine Entscheidung, nicht die des Benutzers.**

`tokens.css` liegt bewusst in `docs/` und **nicht** in `docs/claude-anleitung/`:
der Deploy kopiert ki-tasks-Dateien über jenen Ordner und würde eine
gleichnamige Datei dort überschreiben (`CLAUDE.md`, «zwei Repos, eine
Seitenliste»).

## Prüfschwerpunkte

Fälle, die der Entwurf voraussetzt, die aber keine Aufgabe von sich aus prüft.
Jeder bekommt seinen Test in der Aufgabe, der der Code gehört.

1. **Eine neue Seite, die niemand in die Liste einträgt.** Der Wächter prüft
   nur, was in `MIGRIERT` steht. Vergisst jemand den Eintrag, deklariert die
   Seite wieder eigene Farben und niemand merkt es. → Aufgabe 6.
2. **`build.py` ändert `docs/skillsliste.html` mit.** Beide Generate entstehen
   im selben Lauf. → Aufgabe 3, Hash-Vergleich.
3. **Das Plakat verliert seine Schriftausnahme.** Würde die Überschreibung beim
   Aufräumen entfernt, zeigte die Seite Inter — bei allen, die es installiert
   haben. → Aufgabe 5.
4. **`tokens.css` lädt nicht** (Tippfehler im Pfad, Datei nicht im Deploy). Die
   Seite erschiene ohne Farben. → Aufgabe 6 prüft, dass jeder Pfad auf eine
   wirklich vorhandene Datei zeigt.
5. **Der Deploy kopiert `tokens.css` nicht mit.** Veröffentlicht wird nur
   `docs/`; die Datei liegt darin — aber geprüft hat das niemand. → Aufgabe 6.

---

### Aufgabe 1: Die Token-Datei und ihr Wächter

**Dateien:**
- Neu: `docs/tokens.css`
- Neu: `tests/test_tokens.py`

**Schnittstellen:**
- Liefert — `tests/test_tokens.py` stellt bereit, und die Aufgaben 2–6 benutzen
  genau diese Namen:
  - `ROOT: Path` — `Path(__file__).resolve().parent.parent`, wie in
    `tests/test_plakat.py`
  - `TOKEN_DATEI: Path` — `ROOT / "docs" / "tokens.css"`
  - `SKILLSLISTE: Path` — `ROOT / "docs" / "skillsliste.html"` (Aufgabe 3)
  - `TOKENS: dict[str, str]` — die elf Namen und Werte aus «Der Token-Satz»
  - `MIGRIERT: dict[str, set[str]]` — Pfad (repo-relativ, POSIX) → Menge der
    Token, die diese Datei **selbst** setzen darf. Leer heisst: keine.
  - `tokens_der_datei(pfad: Path) -> dict[str, str]`
  - Importe: `hashlib`, `re`, `subprocess`, `sys`, `pathlib.Path`, `pytest`
- **Aufgabe 5 importiert `tokens_der_datei` und `TOKENS` in
  `tests/test_plakat.py`** (`from test_tokens import TOKENS, tokens_der_datei`
  — beide Dateien liegen in `tests/`, das pytest dem Pfad hinzufügt).

- [ ] **Schritt 1: Den fehlschlagenden Test schreiben**

```python
def test_tokens_css_haelt_genau_den_vereinbarten_satz():
    """Die Werte stammen aus den vier Seiten, die sie heute schon teilen.
    Ändert sich hier einer, ändert sich das Aussehen der halben Website --
    das soll auffallen."""
    assert tokens_der_datei(TOKEN_DATEI) == TOKENS
```

Mit `TOKENS` als wörtlicher Tabelle der elf Werte aus dem Abschnitt
«Der Token-Satz» oben.

- [ ] **Schritt 2: Laufen lassen, Fehlschlag bestätigen**

Befehl: `uv run --with pytest python -m pytest tests/test_tokens.py -q`
Erwartet: FAIL — `docs/tokens.css` gibt es nicht.

- [ ] **Schritt 3: `docs/tokens.css` schreiben**

Eine einzige `:root`-Regel mit den elf Deklarationen, darüber ein Kommentar:
wozu die Datei da ist, dass Signalfarben bewusst **nicht** darin stehen, und
der Verweis auf `specs/2026-10-23-stil-bibliothek-design.md`.

- [ ] **Schritt 4: `tokens_der_datei` umsetzen**

Signatur: `tokens_der_datei(pfad: Path) -> dict[str, str]`. Liest den ersten
`:root { … }`-Block und gibt die Deklarationen zurück, Werte mit
zusammengefasstem Weissraum (`" ".join(wert.split())`) — sonst schlüge der
Vergleich an Einrückung fehl. Gibt `{}` zurück, wenn kein `:root` vorkommt.

- [ ] **Schritt 5: Laufen lassen**

Befehl: `uv run --with pytest python -m pytest tests/test_tokens.py -q`
Erwartet: PASS

- [ ] **Schritt 6: Committen**

```bash
git add docs/tokens.css tests/test_tokens.py
git commit -m "Stil: gemeinsamer Token-Satz in docs/tokens.css"
```

---

### Aufgabe 2: Die Übersicht bezieht die Token

**Dateien:**
- Ändern: `docs/index.html` (`:root`-Block im `<style>`, und der `<head>`)
- Ändern: `tests/test_tokens.py`

**Schnittstellen:**
- Benutzt: `TOKENS`, `MIGRIERT`, `tokens_der_datei` aus Aufgabe 1.

- [ ] **Schritt 1: Die zwei Wächter-Tests schreiben**

```python
@pytest.mark.parametrize("pfad", sorted(MIGRIERT))
def test_migrierte_seite_bindet_die_tokens_ein(pfad):
    assert re.search(r'(?:<link[^>]*href|@import\s+url\()\s*["\']?[^"\')]*tokens\.css',
                     (ROOT / pfad).read_text(encoding="utf-8"))

@pytest.mark.parametrize("pfad", sorted(MIGRIERT))
def test_migrierte_seite_deklariert_keinen_token_neu(pfad):
    """Eine Seite, die einen Token nochmals selbst setzt, laeuft wieder
    auseinander -- und niemand sieht es. Erlaubt sind nur die in MIGRIERT
    eingetragenen, begruendeten Ausnahmen."""
    doppelt = set(tokens_der_datei(ROOT / pfad)) & set(TOKENS) - MIGRIERT[pfad]
    assert not doppelt, f"{pfad} setzt selbst: {sorted(doppelt)}"
```

Und `MIGRIERT = {"docs/index.html": set()}`.

- [ ] **Schritt 2: Laufen lassen, Fehlschlag bestätigen**

Erwartet: beide FAIL — die Seite bindet nichts ein und deklariert alle elf selbst.

- [ ] **Schritt 3: `docs/index.html` umstellen**

`<link rel="stylesheet" href="tokens.css">` in den `<head>`, **vor** das
`<style>` (sonst gewänne bei gleicher Spezifität das später Geladene). Die elf
Deklarationen aus dem `:root`-Block entfernen. Bleibt der Block danach leer,
ganz weg.

- [ ] **Schritt 4: Laufen lassen**

Erwartet: PASS, beide Tests.

- [ ] **Schritt 5: Mit dem Auge prüfen**

Die Seite im Browser öffnen und gegen den Stand vor der Änderung vergleichen
(`git stash` ist hier gefährlich — stattdessen die alte Fassung über
`git show HEAD:docs/index.html` in den Scratchpad schreiben und nebeneinander
ansehen). Erwartet: **kein sichtbarer Unterschied.**

- [ ] **Schritt 6: Committen**

```bash
git add docs/index.html tests/test_tokens.py
git commit -m "Uebersicht bezieht die Farben aus tokens.css"
```

---

### Aufgabe 3: Das Vorschlagsformular bezieht die Token

**Dateien:**
- Ändern: `template-vorschlag.html`
- Erzeugt: `docs/skill-vorschlagen.html` (durch `build.py`)
- Ändern: `tests/test_tokens.py`

**Schnittstellen:**
- Benutzt: wie Aufgabe 2. Trägt **nur** `"docs/skill-vorschlagen.html": set()`
  in `MIGRIERT` ein.

**Warum die Quelle nicht in `MIGRIERT` steht:** `template-vorschlag.html` liegt
im Wurzelverzeichnis, sein Generat in `docs/`. Der Verweis muss `tokens.css`
lauten — richtig für `docs/`, aber von der Quelle aus aufgelöst zeigte er auf
`<wurzel>/tokens.css`, das es nicht gibt; der Pfad-Test aus Aufgabe 6 schlüge
fehl. Nötig ist der Eintrag ohnehin nicht: deklarierte die Quelle einen Token
selbst, täte es das Generat auch, und **das** wird geprüft.

- [ ] **Schritt 1: Den Test gegen das Mitändern der Skillsliste schreiben**

```python
def test_build_laesst_die_skillsliste_unveraendert():
    """build.py schreibt beide Generate im selben Lauf. Die Skillsliste wird
    in diesem Vorhaben ausdruecklich nicht angefasst (Entscheid 2)."""
    vorher = hashlib.sha256(SKILLSLISTE.read_bytes()).hexdigest()
    subprocess.run([sys.executable, str(ROOT / "build.py")], cwd=ROOT, check=True)
    assert hashlib.sha256(SKILLSLISTE.read_bytes()).hexdigest() == vorher
```

- [ ] **Schritt 2: Laufen lassen**

Erwartet: PASS schon jetzt (nichts ist geändert). Der Test ist ein Wächter für
Schritt 4, kein Rot-Grün-Paar — das wird im Testnamen und im Commit gesagt.

- [ ] **Schritt 3: Die beiden Einträge in `MIGRIERT` ergänzen und laufen lassen**

Erwartet: FAIL für beide Pfade.

- [ ] **Schritt 4: `template-vorschlag.html` umstellen, dann bauen**

Wie Aufgabe 2 Schritt 3. Danach: `uv run build.py`.

- [ ] **Schritt 5: Laufen lassen**

Befehl: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Erwartet: alles PASS — besonders `test_build_laesst_die_skillsliste_unveraendert`.

- [ ] **Schritt 6: Committen**

```bash
git add template-vorschlag.html docs/skill-vorschlagen.html tests/test_tokens.py
git commit -m "Vorschlagsformular bezieht die Farben aus tokens.css"
```

---

### Aufgabe 4: Die Anleitung bezieht die Token

**Dateien:**
- Ändern: `docs/claude-anleitung/stil.css` (erste Zeile)
- Ändern: `tests/test_tokens.py`

**Schnittstellen:**
- Benutzt: wie Aufgabe 2. Trägt `"docs/claude-anleitung/stil.css": set()` ein.

- [ ] **Schritt 1: Den Eintrag ergänzen, laufen lassen**

Erwartet: FAIL — `stil.css` bindet nichts ein und setzt neun der elf selbst.

- [ ] **Schritt 2: `stil.css` umstellen**

`@import url("../tokens.css");` als **erste Zeile** der Datei — ein `@import`
nach einer anderen Regel ist ungültig und wird stillschweigend verworfen. Die
neun gemeinsamen Deklarationen aus `:root` entfernen; `--warn`, `--warn-tint`,
`--ok`, `--ok-tint`, `--font-mono` und `--sidebar` bleiben stehen.

- [ ] **Schritt 3: Laufen lassen**

Erwartet: PASS.

- [ ] **Schritt 4: Mit dem Auge prüfen — und zwar am zusammenkopierten Stand**

`CLAUDE.md` sagt: geprüft wird die Anleitung **nicht** am Repo allein, weil acht
Seiten aus `stayingclean/ki-tasks` fehlen. Für diese Änderung genügen die sechs
hiesigen Seiten, weil alle vierzehn dieselbe `stil.css` einbinden — aber
mindestens `index.html` und eine Unterseite ansehen. Erwartet: kein sichtbarer
Unterschied, Seitenleiste in voller Breite (`--sidebar` steht noch).

- [ ] **Schritt 5: Committen**

```bash
git add docs/claude-anleitung/stil.css tests/test_tokens.py
git commit -m "Anleitung bezieht die Farben aus tokens.css"
```

---

### Aufgabe 5: Das Plakat bezieht die Token — mit seiner Schriftausnahme

**Dateien:**
- Ändern: `docs/plakat.html`
- Ändern: `tests/test_tokens.py`, `tests/test_plakat.py`

**Schnittstellen:**
- Benutzt: wie Aufgabe 2. Trägt
  `"docs/plakat.html": {"--font-body", "--font-display"}` ein — die zwei
  begründeten Überschreibungen.

- [ ] **Schritt 1: Den Test für die Schriftausnahme schreiben**

In `tests/test_plakat.py`:

```python
def test_plakat_ueberschreibt_die_schrift_tokens():
    """Die Seite laedt keine Schrift von aussen (CLAUDE.md Punkt 3). Bezoege
    sie --font-body aus tokens.css, verwiese sie auf Inter -- und wer Inter
    lokal installiert hat, saehe die Seite anders als alle anderen."""
    eigene = tokens_der_datei(SEITE)
    assert "Inter" not in eigene["--font-body"]
    assert "Playfair" not in eigene["--font-display"]
```

- [ ] **Schritt 2: Den Eintrag in `MIGRIERT` ergänzen, beide Testdateien laufen lassen**

Erwartet: die Wächter FAIL (nichts eingebunden), der Schrift-Test PASS (die
Seite setzt die Schriften heute schon selbst).

- [ ] **Schritt 3: `docs/plakat.html` umstellen**

`<link rel="stylesheet" href="tokens.css">` vor das `<style>`. Aus `:root` die
neun gemeinsamen Farben entfernen. **Stehen bleiben:** `--warn`, `--warn-tint`,
`--warn-border` und die zwei Schrift-Überschreibungen, mit einem Kommentar, der
sagt warum.

- [ ] **Schritt 4: Laufen lassen**

Befehl: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests/test_plakat.py tests/test_tokens.py -q`
Erwartet: alles PASS — besonders
`test_seite_laedt_nichts_von_aussen_ausser_dem_avatar` und
`test_eine_stilvorlage_der_seite_kaeme_aus_demselben_ordner`, die beide seit
2026-10-23 genau diesen Fall abdecken.

- [ ] **Schritt 5: PNG und PDF von Hand prüfen**

Die Seite öffnen, je einmal PNG und PDF A4 herunterladen. Erwartet: beides
funktioniert unverändert. Der Entwurf weist nach, dass das Aussehen der Seite
das Ergebnis nicht beeinflusst — hier wird es einmal wirklich ausgeführt.

- [ ] **Schritt 6: Committen**

```bash
git add docs/plakat.html tests/test_plakat.py tests/test_tokens.py
git commit -m "Plakat bezieht die Farben aus tokens.css, Schriften bleiben eigen"
```

---

### Aufgabe 6: Der Wächter gegen das Vergessen, und die Regel in CLAUDE.md

Die Aufgaben 2–5 prüfen nur, was in `MIGRIERT` steht. Diese Aufgabe schliesst
die Lücke: eine Seite, die jemand später dazustellt oder vergisst einzutragen.

**Dateien:**
- Ändern: `tests/test_tokens.py`
- Ändern: `CLAUDE.md`

- [ ] **Schritt 1: Die drei Tests schreiben**

```python
AUSGENOMMEN = {
    "docs/skillsliste.html",    # muss in sich geschlossen bleiben
    "docs/flyer-editor.html",   # exportiert sich selbst als Datei
    "docs/budgetvorlage.html",  # wird getrennt umgebaut
    "docs/neutral_flyer.html",  # blosse Weiterleitung
}

def test_jede_seite_ist_migriert_ausgenommen_oder_faellt_auf():
    """Der Wachposten gegen das Vergessen: eine neue Seite in docs/, die
    eigene Farben setzt, muss entweder in MIGRIERT oder in AUSGENOMMEN
    stehen. Sonst laeuft sie auseinander und niemand sieht es."""
    for seite in sorted((ROOT / "docs").rglob("*.html")):
        rel = seite.relative_to(ROOT).as_posix()
        if rel in MIGRIERT or rel in AUSGENOMMEN or rel.startswith("docs/altbau/"):
            continue
        assert not (set(tokens_der_datei(seite)) & set(TOKENS)), \
            f"{rel} setzt eigene Token, steht aber in keiner Liste"

VERWEIS = re.compile(
    r'(?:<link[^>]*href=["\']|@import\s+url\(["\']?)([^"\')]*tokens\.css)'
)

@pytest.mark.parametrize("pfad", sorted(MIGRIERT))
def test_jeder_verweis_auf_die_tokens_zeigt_auf_die_datei(pfad):
    """Ein Tippfehler im Pfad faellt sonst niemandem auf -- die Seite erscheint
    einfach ohne Farben. Der Verweis ist relativ zur verweisenden Datei."""
    quelle = ROOT / pfad
    ziele = VERWEIS.findall(quelle.read_text(encoding="utf-8"))
    assert ziele, f"{pfad} verweist gar nicht auf tokens.css"
    for ziel in ziele:
        assert (quelle.parent / ziel).resolve() == TOKEN_DATEI.resolve(), \
            f"{pfad} verweist auf {ziel} -- das ist nicht {TOKEN_DATEI.name}"

def test_die_tokens_werden_mitveroeffentlicht():
    """Veroeffentlicht wird nur docs/."""
    assert TOKEN_DATEI.relative_to(ROOT).parts[0] == "docs"
```

- [ ] **Schritt 2: Laufen lassen**

Erwartet: PASS — nach den Aufgaben 2–5 ist jede Seite in einer der beiden
Listen. Schlägt etwas fehl, ist eine Aufgabe unvollständig.

- [ ] **Schritt 3: Die Rotprobe, damit der Wächter nicht nur grün ist**

`docs/tokens.css` kurzzeitig in `docs/tokens-x.css` umbenennen und
`test_jeder_verweis_auf_die_tokens_zeigt_auf_die_datei` laufen lassen.
Erwartet: FAIL. Danach zurückbenennen und erneut laufen lassen: PASS.
Ein Wächter, der nie rot war, bewacht nichts.

- [ ] **Schritt 4: `CLAUDE.md` nachziehen**

In Punkt 3 des Abschnitts «Neue HTML-Seite veröffentlichen»: dass es
`docs/tokens.css` gibt, was hineingehört (nur Geteiltes) und was nicht
(Signalfarben, solange ihre Werte auseinandergehen), dass eine neue Seite sie
einbindet statt eigene Farben zu setzen, und dass `tests/test_tokens.py` das
meldet. Ausserdem im Abschnitt «Skill-Vorschläge von aussen» den Satz «das CSS
bleibt trotzdem eingebettet» richtigstellen, und bei der Anleitung das
`@import` erwähnen.

- [ ] **Schritt 5: Der volle Lauf**

Befehl: `uv run --with pytest --with openpyxl --with pypdf --with pillow python -m pytest tests -q`
Erwartet: alles PASS. Vor diesem Vorhaben waren es 458 Tests.

- [ ] **Schritt 6: Committen**

```bash
git add tests/test_tokens.py CLAUDE.md
git commit -m "Wachposten gegen vergessene Seiten, Regel in CLAUDE.md"
```

---

## Danach offen

Gehört **nicht** in diesen Plan, folgt aber daraus:

- **Die Budgetvorlage** — eigener Umbau, mit den drei warmen Grauwerten
  (`#1C1C1C`, `#7A7268`, `#E8E4DF`) und der Frage, was aus `--color-success`,
  `--color-warning` und `--color-danger` wird.
- **Die Signalfarben** — ein Wert je Bedeutung statt drei Brauntöne und zwei
  Grüns. Danach können sie in `tokens.css`.
- **Radien und Übergänge** — heute haben nur Budgetvorlage (4/8/12 px) und
  Skillsliste (14/10/7 px) welche, mit gegenläufigen Namen. Die vier Seiten
  dieses Plans benutzen gar keine, darum kommen sie hier auch nicht hinein.
- **Die drei Schriftabrufe** — drei URLs für dieselben zwei Familien, also drei
  Cache-Einträge. `Inter 300` in der Budgetvorlage ist nachweislich unbenutzt.
