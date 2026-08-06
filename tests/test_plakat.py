"""Prüft den PDF-Kern aus docs/plakat.html und die statischen Eigenschaften
der Plakat-Seite.

Der Kern wird nicht nachgebaut, sondern aus der ausgelieferten HTML
herausgeschnitten und in Node ausgeführt (tests/plakat_pdf_treiber.mjs).
Geprüft wird damit genau der Code, der im Browser läuft.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SEITE = ROOT / "docs" / "plakat.html"
BILD = ROOT / "docs" / "plakat-skillsliste.png"
TREIBER = ROOT / "tests" / "plakat_pdf_treiber.mjs"

MM_ZU_PT = 72 / 25.4
FORMATE = {"a5": (148, 210), "a4": (210, 297), "a3": (297, 420)}

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="Node wird gebraucht, um den PDF-Kern auszuführen",
)


def idat_bytes(png: bytes) -> bytes:
    """Hängt alle IDAT-Blöcke aneinander — der zlib-Strom des Bildes."""
    pos, teile = 8, []
    while pos + 8 <= len(png):
        laenge = int.from_bytes(png[pos : pos + 4], "big")
        art = png[pos + 4 : pos + 8]
        if art == b"IDAT":
            teile.append(png[pos + 8 : pos + 8 + laenge])
        elif art == b"IEND":
            break
        pos += 8 + laenge + 4
    return b"".join(teile)


def png_masse(png: bytes) -> tuple[int, int]:
    return (
        int.from_bytes(png[16:20], "big"),
        int.from_bytes(png[20:24], "big"),
    )


def objekt_strom(pdf: bytes, nummer: int) -> bytes:
    """Liest den Datenstrom eines PDF-Objekts anhand seiner /Length."""
    start = pdf.index(f"{nummer} 0 obj".encode())
    treffer = re.search(rb"/Length (\d+)", pdf[start : start + 800])
    assert treffer, f"Objekt {nummer} hat kein /Length"
    laenge = int(treffer.group(1))
    ab = pdf.index(b"stream\n", start) + len("stream\n")
    return pdf[ab : ab + laenge]


@pytest.fixture(scope="module")
def pdfs(tmp_path_factory):
    """Erzeugt einmal je Format ein PDF aus der echten Bilddatei."""
    ziel = tmp_path_factory.mktemp("plakat")
    ergebnis = {}
    for name, (breite, hoehe) in FORMATE.items():
        pfad = ziel / f"plakat-{name}.pdf"
        lauf = subprocess.run(
            ["node", str(TREIBER), str(SEITE), str(BILD),
             str(breite), str(hoehe), str(pfad)],
            capture_output=True, text=True,
        )
        assert lauf.returncode == 0, lauf.stderr
        ergebnis[name] = pfad.read_bytes()
    return ergebnis


def test_marker_umschliessen_den_kern():
    text = SEITE.read_text(encoding="utf-8")
    assert text.count("/* == pdf-kern:anfang == */") == 1
    assert text.count("/* == pdf-kern:ende == */") == 1
    assert text.index("/* == pdf-kern:anfang == */") < text.index("/* == pdf-kern:ende == */")


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_seitenmass_entspricht_dem_papierformat(pdfs, name):
    breite_mm, hoehe_mm = FORMATE[name]
    treffer = re.search(rb"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", pdfs[name])
    assert treffer, "keine MediaBox gefunden"
    assert float(treffer.group(1)) == pytest.approx(breite_mm * MM_ZU_PT, abs=0.01)
    assert float(treffer.group(2)) == pytest.approx(hoehe_mm * MM_ZU_PT, abs=0.01)


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_bildmasse_stammen_aus_der_datei(pdfs, name):
    breite, hoehe = png_masse(BILD.read_bytes())
    kopf = pdfs[name][:2000]
    assert f"/Width {breite}".encode() in kopf
    assert f"/Height {hoehe}".encode() in kopf


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_bilddaten_wandern_unveraendert_ins_pdf(pdfs, name):
    """Die eigentliche Zusicherung von Weg A: kein Neukodieren."""
    assert objekt_strom(pdfs[name], 4) == idat_bytes(BILD.read_bytes())


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_bild_wird_eingepasst_und_zentriert(pdfs, name):
    breite_px, hoehe_px = png_masse(BILD.read_bytes())
    breite_mm, hoehe_mm = FORMATE[name]
    seite_b, seite_h = breite_mm * MM_ZU_PT, hoehe_mm * MM_ZU_PT

    inhalt = objekt_strom(pdfs[name], 5).decode("latin-1")
    treffer = re.search(r"([\d.]+) 0 0 ([\d.]+) ([\d.]+) ([\d.]+) cm", inhalt)
    assert treffer, f"keine Platzierungsmatrix in: {inhalt!r}"
    bild_b, bild_h, x, y = (float(g) for g in treffer.groups())

    # nicht verzerrt
    assert bild_b / bild_h == pytest.approx(breite_px / hoehe_px, rel=1e-4)
    # so gross wie möglich: eine der beiden Kanten stösst an den Seitenrand
    assert min(seite_b - bild_b, seite_h - bild_h) == pytest.approx(0, abs=0.01)
    # und nirgends grösser als die Seite
    assert bild_b <= seite_b + 0.01 and bild_h <= seite_h + 0.01
    # zentriert
    assert x == pytest.approx((seite_b - bild_b) / 2, abs=0.01)
    assert y == pytest.approx((seite_h - bild_h) / 2, abs=0.01)


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_querverweistabelle_zeigt_auf_die_objekte(pdfs, name):
    """Stimmen die Byteversätze nicht, öffnen strenge Leser die Datei nicht."""
    pdf = pdfs[name]
    ab = int(re.search(rb"startxref\n(\d+)", pdf).group(1))
    assert pdf[ab : ab + 4] == b"xref"
    zeilen = pdf[ab:].split(b"\n")
    for nummer in range(1, 6):
        versatz = int(zeilen[2 + nummer].split()[0])
        marke = f"{nummer} 0 obj".encode()
        assert pdf[versatz : versatz + len(marke)] == marke


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_ein_unabhaengiger_leser_oeffnet_das_pdf(pdfs, name, tmp_path):
    pypdf = pytest.importorskip("pypdf")
    pfad = tmp_path / f"{name}.pdf"
    pfad.write_bytes(pdfs[name])
    leser = pypdf.PdfReader(str(pfad))
    assert len(leser.pages) == 1
    breite_mm, hoehe_mm = FORMATE[name]
    assert float(leser.pages[0].mediabox.width) == pytest.approx(
        breite_mm * MM_ZU_PT, abs=0.01
    )


def test_bilddatei_passt_zu_weg_a():
    """Farbtyp 2 (RGB), 8 Bit, kein Interlace — sonst griffe die Rückfallebene."""
    png = BILD.read_bytes()
    assert png[:8] == bytes([137, 80, 78, 71, 13, 10, 26, 10])
    assert png[24] == 8, "Bittiefe ist nicht 8"
    assert png[25] in (0, 2), "Farbtyp ist weder Graustufen noch RGB"
    assert png[28] == 0, "PNG ist interlaced"


def test_pdf_kern_kommt_ohne_zeichen_ueber_127_aus():
    """Der Binaerkommentar muss aus ASCII-Quelltext entstehen. Staenden die vier
    Zeichen woertlich da, hienge das Ergebnis daran, dass jedes Werkzeug die
    Datei als UTF-8 liest. Dieser Test wird rot, sobald jemand dorthin
    zurueckfaellt — anders als eine Pruefung am fertigen PDF, die beide
    Schreibweisen gleich aussehen laesst."""
    text = SEITE.read_text(encoding="utf-8-sig")
    ab = text.index("/* == pdf-kern:anfang == */")
    bis = text.index("/* == pdf-kern:ende == */")
    ausreisser = sorted({z for z in text[ab:bis] if ord(z) > 127})
    assert not ausreisser, f"Zeichen ueber 127 im PDF-Kern: {ausreisser}"


@pytest.mark.parametrize("name", sorted(FORMATE))
def test_binaerkennung_steht_als_vier_bytes_im_pdf(pdfs, name):
    """Hinter %PDF-1.4 stehen vier Bytes ueber 127, an denen Werkzeuge die Datei
    als binaer erkennen. Dieser Test haelt fest, dass sie im Ergebnis ankommen —
    dass sie aus ASCII-Quelltext stammen, prueft
    test_pdf_kern_kommt_ohne_zeichen_ueber_127_aus."""
    assert pdfs[name].startswith(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
