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

function text(wert) {
  return typeof wert === "string" ? wert.trim() : "";
}

function grapheme(wert) {
  // Zaehlt sichtbare Zeichen, nicht Speichereinheiten: 🧘‍♀️ ist EIN Zeichen,
  // besteht aber aus vier Codepunkten und fuenf UTF-16-Einheiten.
  return [...new Intl.Segmenter("de", { granularity: "grapheme" }).segment(wert)].length;
}

/**
 * Prueft die inhaltlichen Feldregeln, die fuer neue Skills und fuer Aenderungen
 * gleichermassen gelten: Pflichtfelder, Laengen, genau ein Emoji, keine Links,
 * keine Kommentarzeichen, keine spitzen Klammern.
 *
 * `namensfeld` ist der Schluessel des freiwilligen Namens – bei einem neuen
 * Skill `von`, bei einer Aenderung `erg`.
 * Liefert null, wenn alles stimmt, sonst die Fehlermeldung.
 */
function feldregeln(wert, namensfeld) {
  for (const feld of ["emoji", "titel", "beschreibung"]) {
    if (!wert[feld]) {
      return `Pflichtfeld fehlt: ${FELDNAMEN[feld]}.`;
    }
  }
  if (
    Array.from(wert.emoji).length > EMOJI_CODEPUNKT_GRENZE ||
    grapheme(wert.emoji) !== 1
  ) {
    return "Bitte genau ein Emoji angeben.";
  }
  for (const [feld, grenze] of Object.entries(GRENZEN)) {
    const inhalt = feld === "von" ? wert[namensfeld] : wert[feld];
    if (inhalt !== undefined && Array.from(inhalt).length > grenze) {
      const name = feld === "von" ? FELDNAMEN.von : FELDNAMEN[feld];
      return `Zu lang: ${name} (max. ${grenze} Zeichen).`;
    }
  }
  const textfelder = ["titel", "beschreibung", "tipp", namensfeld];
  for (const feld of textfelder) {
    if ((wert[feld] || "").toLowerCase().includes("http")) {
      return "Links sind nicht erlaubt.";
    }
  }
  for (const feld of [...textfelder, "emoji"]) {
    const inhalt = wert[feld] || "";
    if (inhalt.includes("<!--") || inhalt.includes("-->")) {
      return "Kommentarzeichen sind nicht erlaubt.";
    }
    if (inhalt.includes("<") || inhalt.includes(">")) {
      return "Spitze Klammern sind nicht erlaubt.";
    }
  }
  return null;
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

  const fehler = feldregeln(wert, "von");
  if (fehler) {
    return { ok: false, fehler };
  }
  return { ok: true, wert };
}

/**
 * Prueft eine Aenderung an einem bestehenden Skill.
 *
 * Stufe und Kategorie sind NICHT aenderbar – sie bilden zusammen mit dem
 * urspruenglichen Titel den Schluessel, ueber den das Uebernahme-Skript die
 * Zeile in der Excel wiederfindet.
 */
export function pruefeAenderung(eingabe, daten) {
  const roh = eingabe && typeof eingabe === "object" ? eingabe : {};

  if (text(roh.falle)) {
    return { ok: false, fehler: "Ungültige Einreichung." };
  }

  const stufe = text(roh.stufe);
  const schluessel = STUFEN[stufe];
  if (!schluessel || !daten[schluessel]) {
    return { ok: false, fehler: "Unbekannte Stufe." };
  }

  const kategorie = text(roh.kategorie);
  const kat = (daten[schluessel].kategorien || []).find(
    (k) => k.label === kategorie
  );
  if (!kat) {
    return { ok: false, fehler: "Unbekannte Kategorie." };
  }

  const original = text(roh.original);
  const vorhanden = (kat.skills || []).some((s) => s.t === original);
  if (!vorhanden) {
    return {
      ok: false,
      fehler: "Diesen Skill gibt es nicht mehr. Bitte die Seite neu laden.",
    };
  }

  const wert = {
    art: "aenderung",
    stufe,
    kategorie,
    original,
    emoji: text(roh.emoji),
    titel: text(roh.titel),
    beschreibung: text(roh.beschreibung),
    tipp: text(roh.tipp),
    erg: text(roh.erg),
  };

  const fehler = feldregeln(wert, "erg");
  if (fehler) {
    return { ok: false, fehler };
  }

  return { ok: true, wert };
}
