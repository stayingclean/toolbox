/**
 * Prüft die reinen Anteile von index.js – alles, was ohne Netz und ohne
 * Workers-Laufzeit auskommt.
 */

import test from "node:test";
import assert from "node:assert/strict";
import { issueRumpf, issueRumpfAenderung, zelle, quellen, linkBefund, mitBefunden } from "./index.js";

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
  // Kopfzeile + Trennzeile + 8 Felder = 10 Zeilen.
  assert.equal(tabelle.split("\n").length, 10);
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

const ALT = { e: "🎧", t: "Musik hören", b: "Ein Lied auflegen.", tip: "", von: "Max", erg: "" };
const NEU = {
  art: "aenderung",
  stufe: "Hoch",
  kategorie: "Ablenkung",
  original: "Musik hören",
  emoji: "🎵",
  titel: "Musik bewusst hören",
  beschreibung: "Ein Lied aussuchen und nur darauf achten.",
  tipp: "Kopfhörer bereitlegen",
  erg: "Lea",
};

test("zeigt bisher und neu nebeneinander", () => {
  const rumpf = issueRumpfAenderung(NEU, ALT);
  assert.match(rumpf, /bisher/i);
  assert.match(rumpf, /neu/i);
  assert.ok(rumpf.includes("Musik hören"), "alter Titel fehlt");
  assert.ok(rumpf.includes("Musik bewusst hören"), "neuer Titel fehlt");
  assert.ok(rumpf.includes("Ein Lied auflegen."), "alte Beschreibung fehlt");
});

test("enthält genau einen maschinenlesbaren Block mit gültigem JSON", () => {
  const rumpf = issueRumpfAenderung(NEU, ALT);
  const treffer = rumpf.match(/<!-- vorschlag/g) || [];
  assert.equal(treffer.length, 1);
  const block = rumpf.match(/<!-- vorschlag\n([\s\S]*?)\n-->/);
  const daten = JSON.parse(block[1]);
  assert.equal(daten.art, "aenderung");
  assert.equal(daten.original, "Musik hören");
  assert.equal(daten.erg, "Lea");
});

test("maskiert Trennstriche und Zeilenumbrüche in beiden Spalten", () => {
  const rumpf = issueRumpfAenderung(
    { ...NEU, beschreibung: "a | b\nc" },
    { ...ALT, b: "x | y" }
  );
  const tabelle = rumpf.split("<!-- vorschlag")[0];
  assert.ok(!/[^\\]\| b/.test(tabelle), "Trennstrich im neuen Wert nicht maskiert");
  assert.ok(!/[^\\]\| y/.test(tabelle), "Trennstrich im alten Wert nicht maskiert");
  assert.ok(!tabelle.includes("b\nc"), "Zeilenumbruch nicht maskiert");
});

test("Bezugsquellen stehen in der Tabelle eines neuen Skills", () => {
  const rumpf = issueRumpf({
    stufe: "Hoch", kategorie: "Ablenkung", emoji: "🎧",
    titel: "Musik", beschreibung: "Ein Lied", tipp: "", von: "",
    links: ["https://a.ch/x", "https://b.ch/y"],
  });
  assert.match(rumpf, /\| Bezugsquellen \| `https:\/\/a\.ch\/x`<br>`https:\/\/b\.ch\/y` \|/);
});

test("ohne Bezugsquellen steht ein Strich", () => {
  const rumpf = issueRumpf({
    stufe: "Hoch", kategorie: "Ablenkung", emoji: "🎧",
    titel: "Musik", beschreibung: "Ein Lied", tipp: "", von: "", links: [],
  });
  assert.match(rumpf, /\| Bezugsquellen \| — \|/);
});

test("die Aenderung stellt alte und neue Quellen nebeneinander", () => {
  const rumpf = issueRumpfAenderung(
    { stufe: "Hoch", kategorie: "Ablenkung", emoji: "🎧", titel: "Musik",
      beschreibung: "Neu", tipp: "", erg: "", original: "Musik",
      links: ["https://neu.ch/x"] },
    { e: "🎧", t: "Musik", b: "Alt", tip: "", links: ["https://alt.ch/x"] }
  );
  assert.match(rumpf, /\| Bezugsquellen \| `https:\/\/alt\.ch\/x` \| `https:\/\/neu\.ch\/x` \|/);
});

test("ein alter Datenstand ohne links bricht nicht", () => {
  // docs/skills-daten.json wird zwischengespeichert; eine Fassung von vor
  // dieser Neuerung darf den Worker nicht umwerfen.
  assert.equal(quellen(undefined), "—");
});

// `await lauf()` statt `return lauf()`: sonst liefe das finally schon, waehrend
// linkBefund noch auf die Antwort wartet, und das echte fetch staende wieder
// da. Heute ginge es zufaellig gut (der Aufruf faellt vor das erste await),
// aber der Test haette diesen Zufall zur Voraussetzung.
async function mitStubFetch(antwort, lauf) {
  const echt = globalThis.fetch;
  globalThis.fetch = async () => {
    if (antwort instanceof Error) throw antwort;
    return antwort;
  };
  try {
    return await lauf();
  } finally {
    globalThis.fetch = echt;
  }
}

test("200 gilt als erreichbar", async () => {
  const befund = await mitStubFetch({ ok: true, status: 200 }, () =>
    linkBefund("https://a.ch/x")
  );
  assert.match(befund, /^✓ https:\/\/a\.ch\/x — 200 OK$/);
});

test("404 wird als toter Link gemeldet", async () => {
  const befund = await mitStubFetch({ ok: false, status: 404 }, () =>
    linkBefund("https://a.ch/x")
  );
  assert.match(befund, /^⚠ /);
  assert.match(befund, /404/);
});

test("410 wird als toter Link gemeldet", async () => {
  const befund = await mitStubFetch({ ok: false, status: 410 }, () =>
    linkBefund("https://a.ch/x")
  );
  assert.match(befund, /^⚠ /);
});

test("403 ist keine Aussage – Shops sperren Bots aus", async () => {
  const befund = await mitStubFetch({ ok: false, status: 403 }, () =>
    linkBefund("https://a.ch/x")
  );
  assert.match(befund, /^· /);
  assert.match(befund, /keine Aussage/);
});

test("ein Netzwerkfehler ist keine Aussage", async () => {
  const befund = await mitStubFetch(new Error("weg"), () =>
    linkBefund("https://a.ch/x")
  );
  assert.match(befund, /^· /);
  assert.match(befund, /keine Aussage/);
});

test("ohne Befunde bleibt der Rumpf unveraendert", () => {
  assert.equal(mitBefunden("RUMPF", []), "RUMPF");
});

test("Befunde stehen NACH dem Kommentarblock", () => {
  // Der Block muss der einzige bleiben: parse_body in vorschlaege_holen.py
  // verwirft ein Issue mit mehr als einem Block.
  const rumpf = issueRumpf({
    stufe: "Hoch", kategorie: "Ablenkung", emoji: "🎧",
    titel: "Musik", beschreibung: "Ein Lied", tipp: "", von: "", links: [],
  });
  const ganz = mitBefunden(rumpf, ["✓ https://a.ch/x — 200 OK"]);
  assert.equal(ganz.match(/<!-- vorschlag/g).length, 1);
  assert.ok(ganz.indexOf("Erreichbarkeit") > ganz.indexOf("<!-- vorschlag"));
});
