/**
 * Prüft die reinen Anteile von index.js – alles, was ohne Netz und ohne
 * Workers-Laufzeit auskommt.
 */

import test from "node:test";
import assert from "node:assert/strict";
import { issueRumpf, zelle } from "./index.js";

const WERT = {
  art: "neu",
  stufe: "Hoch",
  kategorie: "Ablenkung",
  emoji: "🎧",
  titel: "Musik hören",
  beschreibung: "Ein Lied auflegen und nur darauf achten.",
  tipp: "Kopfhörer bereitlegen",
  von: "Max",
};

function block(rumpf) {
  const treffer = rumpf.match(/<!-- vorschlag\n([\s\S]*?)\n-->/);
  assert.ok(treffer, "Vorschlagsblock nicht gefunden");
  return JSON.parse(treffer[1]);
}

test("zelle maskiert einen senkrechten Strich", () => {
  assert.equal(zelle("a|b"), "a\\|b");
});

test("zelle ersetzt Zeilenumbrüche durch <br>", () => {
  assert.equal(zelle("a\nb"), "a<br>b");
  assert.equal(zelle("a\r\nb"), "a<br>b");
});

test("zelle lässt harmlosen Text unverändert", () => {
  assert.equal(zelle("Musik hören"), "Musik hören");
});

test("zelle verträgt Werte, die keine Zeichenkette sind", () => {
  assert.equal(zelle(undefined), "undefined");
  assert.equal(zelle(7), "7");
});

test("der Rumpf enthält alle Felder", () => {
  const rumpf = issueRumpf(WERT);
  for (const beschriftung of [
    "Stufe",
    "Kategorie",
    "Emoji",
    "Titel",
    "Beschreibung",
    "Tipp",
    "Name",
  ]) {
    assert.ok(rumpf.includes(`| ${beschriftung} |`), `${beschriftung} fehlt`);
  }
  assert.ok(rumpf.includes("Musik hören"));
  assert.ok(rumpf.includes("Kopfhörer bereitlegen"));
  assert.ok(rumpf.includes("Max"));
});

test("leerer Tipp und leerer Name erscheinen als Platzhalter", () => {
  const rumpf = issueRumpf({ ...WERT, tipp: "", von: "" });
  assert.ok(rumpf.includes("| Tipp | — |"));
  assert.ok(rumpf.includes("| Name | — (anonym) |"));
});

test("die Tabelle maskiert senkrechte Striche und Zeilenumbrüche", () => {
  const gift = "eins | zwei\ndrei";
  const rumpf = issueRumpf({ ...WERT, beschreibung: gift });
  const tabelle = rumpf.split("\n\n<!-- vorschlag")[0];
  assert.ok(tabelle.includes("eins \\| zwei<br>drei"));
  // Die Tabelle bleibt eine Zeile je Feld – sonst zerreisst sie.
  // Kopfzeile + Trennzeile + 7 Felder = 9 Zeilen.
  assert.equal(tabelle.split("\n").length, 9);
});

test("der JSON-Block trägt die unveränderten Werte", () => {
  const gift = "eins | zwei\ndrei";
  const rumpf = issueRumpf({ ...WERT, beschreibung: gift });
  const wieder = block(rumpf);
  assert.equal(wieder.beschreibung, gift, "der Block darf nicht maskiert sein");
  assert.deepEqual(wieder, { ...WERT, beschreibung: gift });
});

test("der Rumpf enthält genau einen Vorschlagsblock", () => {
  // Kritisch: das Übernahme-Skript verwirft jeden Rumpf mit zwei Blöcken.
  const rumpf = issueRumpf(WERT);
  const treffer = rumpf.match(/<!-- vorschlag/g) || [];
  assert.equal(treffer.length, 1);
});
