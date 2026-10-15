"""Plotly-Figuren und Tabellen. Alle Achsen fest (fixedrange), damit Touch-Scrollen nicht am Diagramm hängen bleibt."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

import skt_catalog as K
import skt_constants as C
from skt_evaluation import Analysis, de, signed

NODE_SIZE = 62
KIND_COLOR = {"hilft": C.COLOR_GOOD, "neutral": C.COLOR_NEUTRAL, "neutral, aber genauer": C.COLOR_GOOD, "neutral, aber ungenauer": C.COLOR_NEUTRAL,
              "schadet": C.COLOR_BAD, "verstärkt": C.COLOR_AMPLIFY, "rechnet teilweise heraus": C.COLOR_CONTROL}


def _fixed(fig: go.Figure, height: int = 380, **layout) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.2), **layout)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _arrow(fig, p0, p1, color, width=2, shrink=0.09):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    length = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / length, dy / length
    fig.add_annotation(x=x1 - ux * shrink, y=y1 - uy * shrink, ax=x0 + ux * shrink, ay=y0 + uy * shrink, xref="x", yref="y", axref="x", ayref="y",
                       showarrow=True, arrowhead=3, arrowsize=1.3, arrowwidth=width, arrowcolor=color, text="")


def build_diagram(a: Analysis) -> go.Figure:
    """Das Mini-Diagramm: Behandlung und Wirkung mit schwarzem Rand, die Kontrolle blau, verborgene Knoten grau; Kantenbeschriftung mit dem Koeffizienten."""
    st_ = a.structure
    s, tau = a.settings.s, a.settings.tau
    fig = go.Figure()
    for p, c, kind in st_.edges:
        _arrow(fig, st_.pos[p], st_.pos[c], "#6b6b6b", 2)
        mx, my = (st_.pos[p][0] + st_.pos[c][0]) / 2, (st_.pos[p][1] + st_.pos[c][1]) / 2
        fig.add_annotation(x=mx, y=my, text=de(K.coefficient(kind, s, tau), 1), showarrow=False, font=dict(size=11, color="#555555"), bgcolor="rgba(255,255,255,0.75)")
    fills, lines, widths, texts = [], [], [], []
    for v, name in enumerate(st_.nodes):
        hidden = v in st_.hidden
        fills.append(C.COLOR_HIDDEN if hidden else ("rgba(76,120,168,0.40)" if v == st_.control else "rgba(47,107,101,0.12)"))
        lines.append("#1b1b1b" if v in (st_.x, st_.y) else (C.COLOR_CONTROL if v == st_.control else C.COLOR_GOOD))
        widths.append(4 if v in (st_.x, st_.y) else 1.5)
        role = " (Behandlung)" if v == st_.x else (" (Wirkung)" if v == st_.y else (" (Kontrolle)" if v == st_.control else ""))
        texts.append(name + "<br>" + ("unbeobachtet" if hidden else role.strip()) if (hidden or role) else name)
    fig.add_trace(go.Scatter(x=[p[0] for p in st_.pos], y=[p[1] for p in st_.pos], mode="markers+text", text=texts, textposition="middle center",
                             marker=dict(size=NODE_SIZE, color=fills, line=dict(width=widths, color=lines)), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, range=[-0.25, 1.25])
    fig.update_yaxes(visible=False, range=[-0.25, 1.25])
    return _fixed(fig, 340, showlegend=False)


def build_estimates(a: Analysis) -> go.Figure:
    """Schätzung ohne und mit Kontrolle (95-%-Intervall) gegen die wahre Wirkung."""
    fx = a.effects
    labels = ["ohne Kontrolle", "mit Kontrolle"]
    est = [a.est_without, a.est_with]
    err = [C.Z_CRIT * a.se_without, C.Z_CRIT * a.se_with]
    fig = go.Figure(go.Bar(x=labels, y=est, error_y=dict(type="data", array=err, visible=True), marker_color=[C.COLOR_NEUTRAL, C.COLOR_CONTROL],
                           text=[signed(v, 2) for v in est], textposition="outside"))
    fig.add_hline(y=fx.truth, line=dict(color=C.COLOR_TRUTH, width=2), annotation_text=f"Wahrheit {de(fx.truth, 2)}", annotation_position="top left")
    fig.update_yaxes(title="Koeffizient von x", zeroline=True)
    return _fixed(fig, 340, showlegend=False)


def build_zoo_table(rows: list) -> pd.DataFrame:
    out = []
    for r in rows:
        fx = r["effects"]
        out.append({
            "Struktur": r["label"],
            "Einordnung": fx.kind,
            "Fehler ohne Kontrolle": signed(fx.bias_without, 2),
            "Fehler mit Kontrolle": signed(fx.bias_with, 2),
            "Standardfehler mit / ohne": de(fx.se_factor, 2),
            "Deckung ohne": f"{de(100 * r['cover_without'], 0)} %",
            "Deckung mit": f"{de(100 * r['cover_with'], 0)} %",
        })
    return pd.DataFrame(out)


def style_zoo_table(df: pd.DataFrame):
    def row_style(row):
        kind = row["Einordnung"]
        color = {"hilft": "rgba(47,107,101,0.18)", "schadet": "rgba(192,57,43,0.15)", "verstärkt": "rgba(214,138,46,0.20)"}.get(kind, "")
        return [f"background-color: {color}" if color else ""] * len(row)

    return df.style.apply(row_style, axis=1)


def build_zoo_chart(rows: list) -> go.Figure:
    labels = [r["label"].split(" (")[0] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="ohne Kontrolle", x=labels, y=[100 * r["cover_without"] for r in rows], marker_color=C.COLOR_NEUTRAL))
    fig.add_trace(go.Bar(name="mit Kontrolle", x=labels, y=[100 * r["cover_with"] for r in rows], marker_color=C.COLOR_CONTROL))
    fig.add_hline(y=95, line=dict(color="#888888", dash="dot"), annotation_text="versprochen: 95 %", annotation_position="top left")
    fig.update_yaxes(title="Deckung der wahren Wirkung (%)", range=[0, 110])
    fig.update_xaxes(tickangle=-35)
    fig.update_layout(barmode="group")
    return _fixed(fig, 440)


def build_mbias_chart(rows: list) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[r["s"] for r in rows], y=[abs(r["confounding"]) for r in rows], mode="lines+markers", name="Confounding ohne Kontrolle",
                             line=dict(color=C.COLOR_GOOD, width=2.5)))
    fig.add_trace(go.Scatter(x=[r["s"] for r in rows], y=[abs(r["mbias"]) for r in rows], mode="lines+markers", name="M-Bias mit Kontrolle",
                             line=dict(color=C.COLOR_BAD, width=2.5)))
    fig.update_xaxes(title="Kantenstärke s")
    fig.update_yaxes(title="Betrag des Fehlers im Grenzfall")
    return _fixed(fig, 340)


def build_amplification_chart(rows: list) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[r["a"] for r in rows], y=[r["without"] for r in rows], mode="lines+markers", name="Fehler ohne das Instrument",
                             line=dict(color=C.COLOR_NEUTRAL, width=2.5)))
    fig.add_trace(go.Scatter(x=[r["a"] for r in rows], y=[r["with"] for r in rows], mode="lines+markers", name="Fehler mit dem Instrument",
                             line=dict(color=C.COLOR_AMPLIFY, width=2.5)))
    fig.update_xaxes(title="Stärke a des Instruments auf den Faktor")
    fig.update_yaxes(title="Fehler im Grenzfall")
    return _fixed(fig, 340)


def build_rules_chart(res: dict) -> go.Figure:
    from skt_rules import RULE_NAMES

    exists = [100 * res["counts"][(n, True)][1] / res["counts"][(n, True)][0] for n in RULE_NAMES]
    fig = go.Figure(go.Bar(x=list(RULE_NAMES), y=exists, marker_color=[C.COLOR_BAD, C.COLOR_GOOD, C.COLOR_GOOD, C.COLOR_NEUTRAL],
                           text=[de(v, 1) + " %" for v in exists], textposition="outside"))
    fig.update_yaxes(title="Regel liefert eine gültige Menge (%)", range=[0, 112])
    fig.update_xaxes(tickangle=-15)
    return _fixed(fig, 380, showlegend=False)
