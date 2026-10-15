"""Die zehn Kontrolltypen als feste Mini-Diagramme. Knoten in topologischer Reihenfolge; Kanten (eltern, kind, art) mit art "s" (Kantenstärke) oder "tau" (direkte
Wirkung von x auf y). Rolle der Kontrolle `control`; `hidden` sind unbeobachtet (nur für die Zeichnung und für die Frage, was man festhalten kann)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Structure:
    key: str
    label: str
    nodes: tuple
    edges: tuple            # (eltern, kind, art)
    x: int
    y: int
    control: int
    hidden: tuple
    pos: tuple
    why: str                # ein Satz: was passiert und warum


STRUCTURES = {
    "confounder": Structure(
        "confounder", "Confounder (Z → X, Z → Y)", ("Schwankung", "Faktor", "Servicegrad"),
        ((0, 1, "s"), (0, 2, "s"), (1, 2, "tau")), 1, 2, 0, (), ((0.5, 1.0), (0.0, 0.0), (1.0, 0.0)),
        "Die Schwankung bewegt Faktor und Servicegrad zugleich. Wer sie festhält, schließt die Hintertür; ohne sie bleibt der Rückweg offen.",
    ),
    "precision": Structure(
        "precision", "Präzisionsvariable (P → Y)", ("Wetter", "Faktor", "Servicegrad"),
        ((0, 2, "s"), (1, 2, "tau")), 1, 2, 0, (), ((0.5, 1.0), (0.0, 0.0), (1.0, 0.0)),
        "Das Wetter bewegt nur den Servicegrad. Es verzerrt nichts, aber es erklärt einen Teil der Streuung: Mit ihm ist die Schätzung genauer.",
    ),
    "instrument": Structure(
        "instrument", "Instrument ohne Störung (I → X)", ("Zuteilungsregel", "Faktor", "Servicegrad"),
        ((0, 1, "s"), (1, 2, "tau")), 1, 2, 0, (), ((0.0, 1.0), (0.5, 0.0), (1.0, 0.0)),
        "Die Zuteilungsregel bewegt nur den Faktor. Ohne verborgene Störung verzerrt sie nichts, macht die Schätzung aber ungenauer, weil sie Streuung des Faktors bindet.",
    ),
    "instrument_hidden": Structure(
        "instrument_hidden", "Instrument mit verborgener Störung (I → X, U → X, U → Y)", ("Standortqualität", "Zuteilungsregel", "Faktor", "Servicegrad"),
        ((0, 2, "s"), (0, 3, "s"), (1, 2, "s"), (2, 3, "tau")), 2, 3, 1, (0,), ((0.5, 1.0), (0.0, 0.5), (0.5, 0.0), (1.0, 0.0)),
        "Die Standortqualität ist verborgen und bewegt Faktor und Servicegrad. Die Zuteilungsregel nimmt dem Faktor die harmlose Streuung, und die Verzerrung bleibt: Sie wird relativ größer.",
    ),
    "mediator": Structure(
        "mediator", "Mediator (X → M → Y)", ("Faktor", "Bestand", "Servicegrad"),
        ((0, 1, "s"), (1, 2, "s"), (0, 2, "tau")), 0, 2, 1, (), ((0.0, 0.5), (0.5, 1.0), (1.0, 0.5)),
        "Der Faktor wirkt direkt und über den Bestand. Wer den Bestand festhält, rechnet den Umweg heraus und schätzt nur den direkten Weg.",
    ),
    "collider": Structure(
        "collider", "Collider nach der Behandlung (X → C ← Y)", ("Faktor", "Servicegrad", "Beschwerden"),
        ((0, 1, "tau"), (0, 2, "s"), (1, 2, "s")), 0, 1, 2, (), ((0.0, 1.0), (1.0, 1.0), (0.5, 0.0)),
        "Beschwerden sind Folge von Faktor und Servicegrad. Wer sie festhält, öffnet einen Pfad zwischen beiden, den es ohne sie nicht gab.",
    ),
    "m_bias": Structure(
        "m_bias", "M-Bias (U1 → X, U1 → C, U2 → C, U2 → Y)", ("Lage", "Kundenmix", "Auslastung", "Faktor", "Servicegrad"),
        ((0, 2, "s"), (1, 2, "s"), (0, 3, "s"), (1, 4, "s"), (3, 4, "tau")), 3, 4, 2, (0, 1),
        ((0.0, 1.0), (1.0, 1.0), (0.5, 0.5), (0.0, 0.0), (1.0, 0.0)),
        "Die Auslastung liegt vor der Behandlung, ist aber Folge zweier verborgener Ursachen. Wer sie festhält, verbindet diese und öffnet einen Pfad; die Verzerrung ist klein.",
    ),
    "collider_desc": Structure(
        "collider_desc", "Nachfahre des Colliders (C → D)", ("Faktor", "Servicegrad", "Beschwerden", "Rückfragen"),
        ((0, 1, "tau"), (0, 2, "s"), (1, 2, "s"), (2, 3, "s")), 0, 1, 3, (), ((0.0, 1.0), (1.0, 1.0), (0.5, 0.5), (0.5, 0.0)),
        "Auch eine Folge des Colliders öffnet den Pfad, nur schwächer: Die Rückfragen tragen einen Teil der Information der Beschwerden.",
    ),
    "outcome_desc": Structure(
        "outcome_desc", "Nachfahre der Wirkung (Y → D)", ("Faktor", "Servicegrad", "Bonus"),
        ((0, 1, "tau"), (1, 2, "s")), 0, 1, 2, (), ((0.0, 1.0), (0.5, 1.0), (1.0, 1.0)),
        "Der Bonus hängt vom Servicegrad ab. Wer ihn festhält, hält den Servicegrad zum Teil fest und schwächt die geschätzte Wirkung ab.",
    ),
    "mediator_desc": Structure(
        "mediator_desc", "Nachfahre des Mediators (M → D)", ("Faktor", "Bestand", "Servicegrad", "Lagerkosten"),
        ((0, 1, "s"), (1, 2, "s"), (0, 2, "tau"), (1, 3, "s")), 0, 2, 3, (), ((0.0, 0.5), (0.5, 1.0), (1.0, 0.5), (0.5, 0.0)),
        "Die Lagerkosten messen den Bestand mit. Wer sie festhält, hält den Bestand zum Teil fest und rechnet den Umweg zum Teil heraus.",
    ),
}
ORDER = tuple(STRUCTURES)


def coefficient(kind: str, s: float, tau: float) -> float:
    return tau if kind == "tau" else s
