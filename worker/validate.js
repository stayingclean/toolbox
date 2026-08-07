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

export const MAX_LINKS = 3;
export const LINK_MAX_LAENGE = 300;

// Linkverkuerzer verbergen das Ziel vor der Freigabe – die Pruefung im Issue
// waere wertlos – und ergaeben als Knopfaufschrift nur "bit.ly" statt eines
// erkennbaren Haendlers. Dieselbe Liste steht in build.py und in
// tools/vorschlaege_holen.py.
const VERKUERZER = new Set([
  "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
  "buff.ly", "rb.gy", "cutt.ly", "shorturl.at", "s.id", "lnkd.in",
]);

const IPV4 = /^\d{1,3}(\.\d{1,3}){3}$/;

// Anzeigename (Formular) -> Schlüssel in skills-daten.json
export const STUFEN = { Hoch: "hoch", Mittel: "mittel", Tief: "tief" };

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
 *
 * Die Reihenfolge der Pruefungen ist nicht beliebig: sie legt fest, welche
 * Fehlermeldung eine Eingabe bekommt, die mehrere Regeln gleichzeitig verletzt.
 * Wer die Reihenfolge umstellt, aendert damit sichtbares Verhalten.
 */
function feldregeln(wert, namensfeld) {
  for (const feld of ["emoji", "titel", "beschreibung"]) {
    if (!wert[feld]) {
      return `Pflichtfeld fehlt: ${FELDNAMEN[feld]}.`;
    }
  }
  // Das Emoji steht nicht in GRENZEN: das fachlich richtige Mass ist hier der
  // Graphem-Cluster (was ein Mensch als ein Zeichen sieht), nicht eine Anzahl
  // Codepunkte oder UTF-16-Einheiten – deshalb eine eigenstaendige Pruefung
  // statt eines Eintrags in der gemeinsamen Laengentabelle.
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
  // Kommentarzeichen könnten den maschinenlesbaren Block im Issue fälschen
  // (ein zweiter <!-- vorschlag … --> im Freitext). Deshalb auch das Emoji
  // mitprüfen, nicht nur die reinen Textfelder.
  //
  // Für "emoji" ist diese Bedingung mit der aktuellen Prüfreihenfolge in der
  // Praxis unerreichbar: Der Graphem-Check weiter oben verlangt genau EIN
  // Graphem, aber "<!--" und "-->" sind je 3–4 eigenständige ASCII-Zeichen
  // ohne verbindenden Unicode-Joiner, also nie ein einzelnes Graphem. Bewusst
  // trotzdem so belassen (nicht umsortiert) – die Klammer-Sperre direkt danach
  // deckt denselben Fall ohnehin ab, da beide Marker spitze Klammern enthalten.
  for (const feld of [...textfelder, "emoji"]) {
    const inhalt = wert[feld] || "";
    if (inhalt.includes("<!--") || inhalt.includes("-->")) {
      return "Kommentarzeichen sind nicht erlaubt.";
    }
    // Spitze Klammern koennten in der erzeugten Skillsliste das <script>-Element
    // beenden (dort schuetzt zwar die Ausgabecodierung in build.py, aber diese
    // Sperre ist die zweite Schicht). Kein Skilltext braucht spitze Klammern.
    if (inhalt.includes("<") || inhalt.includes(">")) {
      return "Spitze Klammern sind nicht erlaubt.";
    }
  }
  return null;
}

/**
 * Prueft die eingereichten Bezugsquellen.
 *
 * Das ist das EINZIGE Feld, das eine Adresse tragen darf – feldregeln() weist
 * fuer alle Textfelder weiterhin jedes "http" ab. Gespeichert wird die von
 * URL normalisierte Fassung: das codiert nebenbei spitze Klammern, die sonst
 * den Kommentarblock im Issue beenden koennten.
 *
 * Liefert {ok:true, links} oder {ok:false, fehler}.
 */
export function pruefeLinks(rohe) {
  if (rohe === undefined || rohe === null) {
    return { ok: true, links: [] };
  }
  if (!Array.isArray(rohe)) {
    return { ok: false, fehler: "Bezugsquellen sind unlesbar." };
  }
  const links = [];
  for (const eintrag of rohe) {
    const url = text(eintrag);
    if (!url) continue;
    let zerlegt;
    try {
      zerlegt = new URL(url);
    } catch {
      return { ok: false, fehler: "Bezugsquelle ist keine gültige Adresse." };
    }
    if (zerlegt.href.length > LINK_MAX_LAENGE) {
      return {
        ok: false,
        fehler: `Zu lang: Bezugsquelle (max. ${LINK_MAX_LAENGE} Zeichen).`,
      };
    }
    if (zerlegt.protocol !== "https:") {
      return { ok: false, fehler: "Bezugsquelle muss mit https:// beginnen." };
    }
    if (zerlegt.username || zerlegt.password) {
      return {
        ok: false,
        fehler: "Bezugsquelle darf keine Benutzerangabe (@) enthalten.",
      };
    }
    if (zerlegt.port) {
      return { ok: false, fehler: "Bezugsquelle darf keine Portnummer enthalten." };
    }
    const host = zerlegt.hostname.replace(/\.+$/, "");
    // Eckige Klammer: so schreibt URL eine IPv6-Adresse.
    if (host.startsWith("[") || IPV4.test(host)) {
      return { ok: false, fehler: "Bezugsquelle darf keine IP-Adresse sein." };
    }
    if (!host.includes(".")) {
      return { ok: false, fehler: "Bezugsquelle hat keinen gültigen Hostnamen." };
    }
    if (VERKUERZER.has(host.replace(/^www\./, ""))) {
      return { ok: false, fehler: "Linkverkürzer sind nicht erlaubt." };
    }
    if (!links.includes(zerlegt.href)) {
      links.push(zerlegt.href);
    }
    if (links.length > MAX_LINKS) {
      return { ok: false, fehler: `Höchstens ${MAX_LINKS} Bezugsquellen.` };
    }
  }
  return { ok: true, links };
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

  const quellen = pruefeLinks(roh.links);
  if (!quellen.ok) {
    return { ok: false, fehler: quellen.fehler };
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
    links: quellen.links,
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

  const quellen = pruefeLinks(roh.links);
  if (!quellen.ok) {
    return { ok: false, fehler: quellen.fehler };
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
    links: quellen.links,
  };

  const fehler = feldregeln(wert, "erg");
  if (fehler) {
    return { ok: false, fehler };
  }

  return { ok: true, wert };
}
