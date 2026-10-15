"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).
Alle mit Einheitsrauschen und Kantenstärke s = 1; die direkte Wirkung tau steht je Fixture dabei."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import skt_catalog as K  # noqa: E402


@pytest.fixture
def hand():
    """Handrechnungen je Struktur bei s = 1, tau gegeben: (Struktur, tau) -> (wahre Wirkung, Koeffizient ohne, Koeffizient mit).

    confounder, tau 0: Cov(X,Y) = 1, Var(X) = 2: ohne 1/2, mit Z 0.
    mediator, tau 0: X -> M -> Y mit je 1: Gesamtwirkung 1; mit M: 0.
    collider, tau 0: Var(C) = 3, Cov(X,C) = Cov(Y,C) = 1: mit C (0 − 1/3)/(1 − 1/3) = −1/2.
    m_bias, tau 0: Var(X) = 2, Cov(X,C) = Cov(Y,C) = 1, Var(C) = 3: mit C (0 − 1/3)/(2 − 1/3) = −1/5.
    instrument_hidden, tau 0: Var(X) = 3, Cov(X,Y) = 1: ohne 1/3; mit I Var(X|I) = 2: 1/2.
    outcome_desc, tau 1: X -> Y (1), Y -> D (1): Var(D) = 3, Cov(X,D) = 1, Cov(Y,D) = 2: mit D (1 − 2/3)/(1 − 1/3) = 1/2.
    precision, tau 1: Y = X + P + e: beide Koeffizienten 1.
    instrument, tau 1: Y = X + e, X = I + e': beide Koeffizienten 1."""
    return {
        ("confounder", 0.0): (0.0, 0.5, 0.0),
        ("mediator", 0.0): (1.0, 1.0, 0.0),
        ("collider", 0.0): (0.0, 0.0, -0.5),
        ("m_bias", 0.0): (0.0, 0.0, -0.2),
        ("instrument_hidden", 0.0): (0.0, 1.0 / 3.0, 0.5),
        ("outcome_desc", 1.0): (1.0, 1.0, 0.5),
        ("precision", 1.0): (1.0, 1.0, 1.0),
        ("instrument", 1.0): (1.0, 1.0, 1.0),
    }


@pytest.fixture
def structures():
    return K.STRUCTURES
