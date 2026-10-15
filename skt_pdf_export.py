"""PDF-Export der aktuellen Auswertung (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Pfeile und Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import skt_catalog as K
from skt_evaluation import Analysis, de

_REPLACE = {"→": "->", "←": "<-", "–": "-", "—": "-", "−": "-", "€": "EUR", "≥": ">=", "≤": "<=", "„": '"', "“": '"'}


def _s(text) -> str:
    out = str(text)
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: Analysis) -> bytes:
    st_, fx, s = a.structure, a.effects, a.settings
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Schlechte Kontrollen: wo eine Variable im Diagramm sitzt"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"Struktur: {st_.label}. Kontrolle: {st_.nodes[st_.control]}. Kantenstaerke s = {de(s.s, 1)}, direkte Wirkung tau = {de(s.tau, 1)}, "
                            f"n = {s.n}, Seed {s.seed}. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    lines = [
        f"Einordnung: {fx.kind}.",
        f"Wahre Gesamtwirkung von x auf y: {de(fx.truth, 3)}.",
        f"Grenzfall ohne Kontrolle: {de(fx.coef_without, 3)} (Fehler {de(fx.bias_without, 3)}); mit Kontrolle: {de(fx.coef_with, 3)} (Fehler {de(fx.bias_with, 3)}).",
        f"Standardfehler mit / ohne Kontrolle: Faktor {de(fx.se_factor, 2)}.",
        f"Stichprobe: ohne Kontrolle {de(a.est_without, 3)} (+-{de(1.96 * a.se_without, 3)}), mit Kontrolle {de(a.est_with, 3)} (+-{de(1.96 * a.se_with, 3)}).",
    ]
    for line in lines:
        pdf.multi_cell(0, 5, _s(line), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 4.5, _s(st_.why), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: schlechte-kontrollen-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
