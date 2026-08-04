import test from "node:test";
import assert from "node:assert/strict";
import { pruefeVorschlag, pruefeAenderung } from "./validate.js";

const DATEN = {
  hoch: { kategorien: [{ id: "ablenkung", label: "Ablenkung", skills: [] }] },
  mittel: { kategorien: [] },
  tief: { kategorien: [] },
};

const GUELTIG = {
  stufe: "Hoch",
  kategorie: "Ablenkung",
  emoji: "🎧",
  titel: "Musik hören",
  beschreibung: "Ein Lied auflegen und nur darauf achten.",
  tipp: "Kopfhörer bereitlegen",
  von: "Max",
  falle: "",
};

test("nimmt einen gültigen Vorschlag an", () => {
  const r = pruefeVorschlag(GUELTIG, DATEN);
  assert.equal(r.ok, true);
  assert.equal(r.wert.art, "neu");
  assert.equal(r.wert.titel, "Musik hören");
  assert.equal(r.wert.von, "Max");
});

test("trimmt Leerzeichen", () => {
  const r = pruefeVorschlag({ ...GUELTIG, titel: "  Musik hören  " }, DATEN);
  assert.equal(r.wert.titel, "Musik hören");
});

test("Tipp und Name sind freiwillig", () => {
  const r = pruefeVorschlag({ ...GUELTIG, tipp: "", von: "" }, DATEN);
  assert.equal(r.ok, true);
  assert.equal(r.wert.tipp, "");
  assert.equal(r.wert.von, "");
});

test("lehnt ausgefüllte Falle ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, falle: "bot" }, DATEN);
  assert.equal(r.ok, false);
});

test("lehnt unbekannte Stufe ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, stufe: "Sehr hoch" }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Stufe/);
});

test("lehnt unbekannte Kategorie ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, kategorie: "Erfunden" }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Kategorie/);
});

test("lehnt leeren Titel ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, titel: "   " }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Titel/);
});

test("lehnt zu langen Titel ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, titel: "x".repeat(61) }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Titel/);
});

test("erlaubt genau 60 Zeichen im Titel", () => {
  const r = pruefeVorschlag({ ...GUELTIG, titel: "x".repeat(60) }, DATEN);
  assert.equal(r.ok, true);
});

test("zählt Emoji nach Zeichen, nicht nach Bytes", () => {
  const r = pruefeVorschlag({ ...GUELTIG, emoji: "🎧" }, DATEN);
  assert.equal(r.ok, true);
});

test("nimmt ein zusammengesetztes Emoji an (Graphem-Cluster statt UTF-16-Einheiten)", () => {
  // 🧘‍♀️ ist EIN sichtbares Zeichen, aber vier Codepunkte und fuenf
  // UTF-16-Einheiten – genau der Fall, den maxlength="2" bzw. das alte
  // GRENZEN.emoji faelschlich blockiert hat.
  const r = pruefeVorschlag({ ...GUELTIG, emoji: "🧘‍♀️" }, DATEN);
  assert.equal(r.ok, true);
});

test("lehnt ein leeres Emoji ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, emoji: "" }, DATEN);
  assert.equal(r.ok, false);
});

test("lehnt zwei einfache Zeichen als Emoji ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, emoji: "ab" }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /genau ein Emoji/);
});

test("lehnt drei Emoji ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, emoji: "🎧🎧🎧" }, DATEN);
  assert.equal(r.ok, false);
});

test("lehnt eine sehr lange Emoji-Kette ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, emoji: "🎧".repeat(20) }, DATEN);
  assert.equal(r.ok, false);
});

test("lehnt Links ab", () => {
  for (const feld of ["titel", "beschreibung", "tipp", "von"]) {
    const r = pruefeVorschlag({ ...GUELTIG, [feld]: "siehe HTTP://spam.example" }, DATEN);
    assert.equal(r.ok, false, `${feld} muss Links ablehnen`);
    assert.match(r.fehler, /Link/);
  }
});

test("verträgt fehlende Felder ohne Absturz", () => {
  const r = pruefeVorschlag({}, DATEN);
  assert.equal(r.ok, false);
});

test("erlaubt genau 300 Zeichen in der Beschreibung", () => {
  const r = pruefeVorschlag({ ...GUELTIG, beschreibung: "x".repeat(300) }, DATEN);
  assert.equal(r.ok, true);
});

test("lehnt 301 Zeichen in der Beschreibung ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, beschreibung: "x".repeat(301) }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Beschreibung/);
});

test("erlaubt genau 30 Zeichen im Namen", () => {
  const r = pruefeVorschlag({ ...GUELTIG, von: "x".repeat(30) }, DATEN);
  assert.equal(r.ok, true);
});

test("lehnt 31 Zeichen im Namen ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, von: "x".repeat(31) }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Name/);
});

test("lehnt Kommentarzeichen in allen Textfeldern ab", () => {
  for (const feld of ["titel", "beschreibung", "tipp", "von"]) {
    const auf = pruefeVorschlag({ ...GUELTIG, [feld]: "a <!-- b" }, DATEN);
    assert.equal(auf.ok, false, `${feld} muss <!-- ablehnen`);
    assert.match(auf.fehler, /Kommentarzeichen/);
    const zu = pruefeVorschlag({ ...GUELTIG, [feld]: "a --> b" }, DATEN);
    assert.equal(zu.ok, false, `${feld} muss --> ablehnen`);
  }
});

test("lehnt einen gefaelschten Vorschlagsblock in der Beschreibung ab", () => {
  const gift = 'Harmlos. <!-- vorschlag {"titel":"EINGESCHLEUST"} -->';
  const r = pruefeVorschlag({ ...GUELTIG, beschreibung: gift }, DATEN);
  assert.equal(r.ok, false);
});

test("lehnt spitze Klammern in allen Textfeldern und im Emoji ab", () => {
  for (const feld of ["titel", "beschreibung", "tipp", "von", "emoji"]) {
    // Das Emoji darf nur 2 Zeichen lang sein – dort ohne Umgebungstext pruefen,
    // sonst schlaegt zuerst die Laengengrenze zu.
    const [mitAuf, mitZu] = feld === "emoji" ? ["<", ">"] : ["a<b", "a>b"];
    const auf = pruefeVorschlag({ ...GUELTIG, [feld]: mitAuf }, DATEN);
    assert.equal(auf.ok, false, `${feld} muss < ablehnen`);
    assert.match(auf.fehler, /Spitze Klammern/);
    const zu = pruefeVorschlag({ ...GUELTIG, [feld]: mitZu }, DATEN);
    assert.equal(zu.ok, false, `${feld} muss > ablehnen`);
    assert.match(zu.fehler, /Spitze Klammern/);
  }
});

test("lehnt einen Ausbruch aus dem script-Block ab", () => {
  const gift = "harmlos</script><script>alert(1)</script>";
  const r = pruefeVorschlag({ ...GUELTIG, beschreibung: gift }, DATEN);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Spitze Klammern/);
});

test("gibt nur die erlaubten Schlüssel zurück", () => {
  const r = pruefeVorschlag({ ...GUELTIG, art: "aenderung", extra: "x" }, DATEN);
  assert.equal(r.ok, true);
  assert.deepEqual(
    Object.keys(r.wert).sort(),
    ["art", "beschreibung", "emoji", "kategorie", "stufe", "tipp", "titel", "von"].sort()
  );
  // Die Art setzt der Worker selbst – eine mitgeschickte Art wird ignoriert.
  assert.equal(r.wert.art, "neu");
});

const DATEN_MIT_SKILL = {
  hoch: {
    kategorien: [
      {
        id: "ablenkung",
        label: "Ablenkung",
        skills: [
          { e: "🎧", t: "Musik hören", b: "Ein Lied auflegen.", tip: "", von: "Max", erg: "" },
        ],
      },
    ],
  },
  mittel: { kategorien: [] },
  tief: { kategorien: [] },
};

const AENDERUNG = {
  stufe: "Hoch",
  kategorie: "Ablenkung",
  original: "Musik hören",
  emoji: "🎧",
  titel: "Musik bewusst hören",
  beschreibung: "Ein Lied aussuchen und nur darauf achten.",
  tipp: "Kopfhörer bereitlegen",
  erg: "Lea",
  falle: "",
};

test("nimmt eine gültige Änderung an", () => {
  const r = pruefeAenderung(AENDERUNG, DATEN_MIT_SKILL);
  assert.equal(r.ok, true);
  assert.equal(r.wert.art, "aenderung");
  assert.equal(r.wert.original, "Musik hören");
  assert.equal(r.wert.titel, "Musik bewusst hören");
  assert.equal(r.wert.erg, "Lea");
});

test("liefert nur die erlaubten Schlüssel zurück", () => {
  const r = pruefeAenderung({ ...AENDERUNG, art: "neu", extra: "x" }, DATEN_MIT_SKILL);
  assert.deepEqual(
    Object.keys(r.wert).sort(),
    ["art", "beschreibung", "emoji", "erg", "kategorie", "original", "stufe", "tipp", "titel"].sort()
  );
  assert.equal(r.wert.art, "aenderung");
});

test("lehnt eine Änderung an einem unbekannten Skill ab", () => {
  const r = pruefeAenderung({ ...AENDERUNG, original: "Gibt es nicht" }, DATEN_MIT_SKILL);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /nicht mehr|unbekannt/i);
});

test("lehnt eine Änderung in unbekannter Kategorie ab", () => {
  const r = pruefeAenderung({ ...AENDERUNG, kategorie: "Erfunden" }, DATEN_MIT_SKILL);
  assert.equal(r.ok, false);
  assert.match(r.fehler, /Kategorie/);
});

test("lehnt eine Änderung mit ausgefüllter Falle ab", () => {
  const r = pruefeAenderung({ ...AENDERUNG, falle: "bot" }, DATEN_MIT_SKILL);
  assert.equal(r.ok, false);
});

test("wendet dieselben Feldregeln an wie bei einem neuen Skill", () => {
  for (const [feld, wert, muster] of [
    ["titel", "x".repeat(61), /Titel/],
    ["beschreibung", "x".repeat(301), /Beschreibung/],
    ["erg", "x".repeat(31), /Name/],
    ["titel", "siehe http://spam.example", /Link/],
    ["beschreibung", "a <!-- b", /Kommentarzeichen/],
    ["tipp", "a < b", /Klammern/],
  ]) {
    const r = pruefeAenderung({ ...AENDERUNG, [feld]: wert }, DATEN_MIT_SKILL);
    assert.equal(r.ok, false, `${feld} muss abgelehnt werden`);
    assert.match(r.fehler, muster);
  }
});

test("verlangt genau ein Emoji auch bei einer Änderung", () => {
  assert.equal(pruefeAenderung({ ...AENDERUNG, emoji: "🧘‍♀️" }, DATEN_MIT_SKILL).ok, true);
  assert.equal(pruefeAenderung({ ...AENDERUNG, emoji: "ab" }, DATEN_MIT_SKILL).ok, false);
});

test("der Name des Ergänzenden ist freiwillig", () => {
  const r = pruefeAenderung({ ...AENDERUNG, erg: "" }, DATEN_MIT_SKILL);
  assert.equal(r.ok, true);
  assert.equal(r.wert.erg, "");
});
