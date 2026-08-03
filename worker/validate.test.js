import test from "node:test";
import assert from "node:assert/strict";
import { pruefeVorschlag } from "./validate.js";

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

test("lehnt drei Emoji ab", () => {
  const r = pruefeVorschlag({ ...GUELTIG, emoji: "🎧🎧🎧" }, DATEN);
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
