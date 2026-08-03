/**
 * Reine Prüffunktionen für eingereichte Skill-Vorschläge.
 * Keine Netzwerk- oder Umgebungszugriffe, damit sie mit `node --test` prüfbar sind.
 */

export const GRENZEN = {
  emoji: 2,
  titel: 60,
  beschreibung: 300,
  tipp: 200,
  von: 30,
};

// Anzeigename (Formular) -> Schlüssel in skills-daten.json
const STUFEN = { Hoch: "hoch", Mittel: "mittel", Tief: "tief" };

const TEXTFELDER = ["titel", "beschreibung", "tipp", "von"];

function text(wert) {
  return typeof wert === "string" ? wert.trim() : "";
}

function laenge(wert) {
  return Array.from(wert).length;
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
      const feldName = feld.charAt(0).toUpperCase() + feld.slice(1);
      return { ok: false, fehler: `Pflichtfeld fehlt: ${feldName}.` };
    }
  }

  for (const [feld, grenze] of Object.entries(GRENZEN)) {
    if (laenge(wert[feld]) > grenze) {
      const feldName = feld.charAt(0).toUpperCase() + feld.slice(1);
      return { ok: false, fehler: `Zu lang: ${feldName} (max. ${grenze} Zeichen).` };
    }
  }

  for (const feld of TEXTFELDER) {
    if (wert[feld].toLowerCase().includes("http")) {
      return { ok: false, fehler: "Links sind nicht erlaubt." };
    }
  }

  return { ok: true, wert };
}
