/**
 * Reine Prüffunktionen für eingereichte Skill-Vorschläge.
 * Keine Netzwerk- oder Umgebungszugriffe, damit sie mit `node --test` prüfbar sind.
 */

export const GRENZEN = {
  titel: 60,
  beschreibung: 300,
  tipp: 200,
  von: 30,
};

// Ein einzelnes, zusammengesetztes Emoji (Geschlecht, Hautton, Familie) besteht
// aus mehreren Unicode-Codepunkten. Ohne diese Schranke waere ein Angreifer
// nicht durch die Graphem-Pruefung gebremst, wenn eine absurd lange Kette von
// Codepunkten zufaellig als eine Handvoll Grapheme durchgeht.
const EMOJI_CODEPUNKT_GRENZE = 16;

// Anzeigename (Formular) -> Schlüssel in skills-daten.json
const STUFEN = { Hoch: "hoch", Mittel: "mittel", Tief: "tief" };

// Feldschlüssel -> Bezeichnung in Fehlermeldungen (so wie im Formular beschriftet)
const FELDNAMEN = {
  emoji: "Emoji",
  titel: "Titel",
  beschreibung: "Beschreibung",
  tipp: "Tipp",
  von: "Name",
};

const TEXTFELDER = ["titel", "beschreibung", "tipp", "von"];

function text(wert) {
  return typeof wert === "string" ? wert.trim() : "";
}

function laenge(wert) {
  return Array.from(wert).length;
}

function grapheme(wert) {
  // Zaehlt sichtbare Zeichen, nicht Speichereinheiten: 🧘‍♀️ ist EIN Zeichen,
  // besteht aber aus vier Codepunkten und fuenf UTF-16-Einheiten.
  return [...new Intl.Segmenter("de", { granularity: "grapheme" }).segment(wert)].length;
}

export function pruefeVorschlag(eingabe, daten) {
  const roh = eingabe && typeof eingabe === "object" ? eingabe : {};

  // Versteckte Falle: für Menschen unsichtbar, Bots füllen sie aus.
  if (text(roh.falle)) {
    return { ok: false, fehler: "Ungültige Einreichung." };
  }

  const stufe = text(roh.stufe);
  const schluessel = STUFEN[stufe];
  if (!schluessel || !daten[schluessel]) {
    return { ok: false, fehler: "Unbekannte Stufe." };
  }

  const kategorie = text(roh.kategorie);
  const bekannt = (daten[schluessel].kategorien || []).some(
    (k) => k.label === kategorie
  );
  if (!bekannt) {
    return { ok: false, fehler: "Unbekannte Kategorie." };
  }

  const wert = {
    art: "neu",
    stufe,
    kategorie,
    emoji: text(roh.emoji),
    titel: text(roh.titel),
    beschreibung: text(roh.beschreibung),
    tipp: text(roh.tipp),
    von: text(roh.von),
  };

  for (const feld of ["emoji", "titel", "beschreibung"]) {
    if (!wert[feld]) {
      return { ok: false, fehler: `Pflichtfeld fehlt: ${FELDNAMEN[feld]}.` };
    }
  }

  // Das Emoji steht nicht in GRENZEN: das fachlich richtige Mass ist hier der
  // Graphem-Cluster (was ein Mensch als ein Zeichen sieht), nicht eine Anzahl
  // Codepunkte oder UTF-16-Einheiten – deshalb eine eigenstaendige Pruefung an
  // der Stelle, an der zuvor die Laengenpruefung fuer Emoji lief.
  if (laenge(wert.emoji) > EMOJI_CODEPUNKT_GRENZE || grapheme(wert.emoji) !== 1) {
    return { ok: false, fehler: "Bitte genau ein Emoji angeben." };
  }

  for (const [feld, grenze] of Object.entries(GRENZEN)) {
    if (laenge(wert[feld]) > grenze) {
      return { ok: false, fehler: `Zu lang: ${FELDNAMEN[feld]} (max. ${grenze} Zeichen).` };
    }
  }

  for (const feld of TEXTFELDER) {
    if (wert[feld].toLowerCase().includes("http")) {
      return { ok: false, fehler: "Links sind nicht erlaubt." };
    }
  }

  // Kommentarzeichen könnten den maschinenlesbaren Block im Issue fälschen
  // (ein zweiter <!-- vorschlag … --> im Freitext). Deshalb auch das Emoji
  // mitprüfen, nicht nur die reinen Textfelder.
  for (const feld of [...TEXTFELDER, "emoji"]) {
    if (wert[feld].includes("<!--") || wert[feld].includes("-->")) {
      return { ok: false, fehler: "Kommentarzeichen sind nicht erlaubt." };
    }
  }

  // Spitze Klammern koennten in der erzeugten Skillsliste das <script>-Element
  // beenden (dort schuetzt zwar die Ausgabecodierung in build.py, aber diese
  // Sperre ist die zweite Schicht). Kein Skilltext braucht spitze Klammern.
  for (const feld of [...TEXTFELDER, "emoji"]) {
    if (wert[feld].includes("<") || wert[feld].includes(">")) {
      return { ok: false, fehler: "Spitze Klammern sind nicht erlaubt." };
    }
  }

  return { ok: true, wert };
}
