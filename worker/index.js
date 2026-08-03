/**
 * Nimmt Skill-Vorschläge vom Formular entgegen und legt daraus ein Issue an.
 *
 * Bewusst NICHT gespeichert oder protokolliert: IP-Adresse und Browserkennung.
 * Die IP wird ausschliesslich als Hashwert für die Ratenbegrenzung verwendet
 * und verfällt nach einer Stunde.
 */

import { pruefeVorschlag } from "./validate.js";

const HERKUNFT = "https://stayingclean.github.io";
const MAX_PRO_STUNDE = 5;

function antwort(rumpf, status = 200) {
  return new Response(JSON.stringify(rumpf), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "access-control-allow-origin": HERKUNFT,
      "access-control-allow-headers": "content-type",
      "access-control-allow-methods": "POST, OPTIONS",
    },
  });
}

async function hashe(text) {
  const roh = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text)
  );
  return [...new Uint8Array(roh)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function turnstileGeprueft(token, secret, ip) {
  if (!token) return false;
  const formular = new FormData();
  formular.append("secret", secret);
  formular.append("response", token);
  if (ip) formular.append("remoteip", ip);
  const res = await fetch(
    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
    { method: "POST", body: formular }
  );
  const ergebnis = await res.json();
  return ergebnis.success === true;
}

function issueRumpf(w) {
  const zeilen = [
    "| Feld | Wert |",
    "| --- | --- |",
    `| Stufe | ${w.stufe} |`,
    `| Kategorie | ${w.kategorie} |`,
    `| Emoji | ${w.emoji} |`,
    `| Titel | ${w.titel} |`,
    `| Beschreibung | ${w.beschreibung} |`,
    `| Tipp | ${w.tipp || "—"} |`,
    `| Name | ${w.von || "— (anonym)"} |`,
  ];
  return (
    zeilen.join("\n") +
    "\n\n<!-- vorschlag\n" +
    JSON.stringify(w) +
    "\n-->\n"
  );
}

export default {
  async fetch(anfrage, umgebung) {
    if (anfrage.method === "OPTIONS") {
      // 204 darf keinen Rumpf haben – sonst wirft die Workers-Laufzeit.
      return new Response(null, {
        status: 204,
        headers: {
          "access-control-allow-origin": HERKUNFT,
          "access-control-allow-headers": "content-type",
          "access-control-allow-methods": "POST, OPTIONS",
          "access-control-max-age": "86400",
        },
      });
    }
    if (anfrage.method !== "POST") {
      return antwort({ fehler: "Nur POST." }, 405);
    }

    const ip = anfrage.headers.get("CF-Connecting-IP") || "";

    // Ratenbegrenzung: Hashwert der IP, Ablauf nach einer Stunde.
    const schluessel = "rate:" + (await hashe(ip + umgebung.RATE_SALT));
    const bisher = Number((await umgebung.RATE.get(schluessel)) || 0);
    if (bisher >= MAX_PRO_STUNDE) {
      return antwort(
        { fehler: "Zu viele Einreichungen. Bitte in einer Stunde erneut." },
        429
      );
    }

    let eingabe;
    try {
      eingabe = await anfrage.json();
    } catch {
      return antwort({ fehler: "Ungültige Anfrage." }, 400);
    }

    if (
      !(await turnstileGeprueft(eingabe.turnstile, umgebung.TURNSTILE_SECRET, ip))
    ) {
      return antwort({ fehler: "Sicherheitsprüfung fehlgeschlagen." }, 400);
    }

    const datenRes = await fetch(umgebung.DATEN_URL, {
      cf: { cacheTtl: 300, cacheEverything: true },
    });
    if (!datenRes.ok) {
      return antwort({ fehler: "Datenstand nicht erreichbar." }, 503);
    }
    const daten = await datenRes.json();

    const geprueft = pruefeVorschlag(eingabe, daten);
    if (!geprueft.ok) {
      return antwort({ fehler: geprueft.fehler }, 400);
    }

    const issueRes = await fetch(
      `https://api.github.com/repos/${umgebung.REPO}/issues`,
      {
        method: "POST",
        headers: {
          authorization: `Bearer ${umgebung.GITHUB_TOKEN}`,
          accept: "application/vnd.github+json",
          "content-type": "application/json",
          "user-agent": "toolbox-skill-vorschlag",
        },
        body: JSON.stringify({
          title: geprueft.wert.titel,
          body: issueRumpf(geprueft.wert),
        }),
      }
    );
    if (!issueRes.ok) {
      return antwort({ fehler: "Konnte den Vorschlag nicht ablegen." }, 502);
    }
    const issue = await issueRes.json();

    await umgebung.RATE.put(schluessel, String(bisher + 1), {
      expirationTtl: 3600,
    });

    return antwort({ url: issue.html_url });
  },
};
