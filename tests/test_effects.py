"""Population: Koeffizient, Fehler, Standardfehler-Faktor, Einordnung; jede Einheit an den Handrechnungen aus conftest.py."""

import math

import numpy as np
import pytest

import skt_catalog as K
import skt_constants as C
import skt_effects as E


def test_the_hand_instances(hand):
    for (key, tau), (truth, without, with_) in hand.items():
        fx = E.effects(K.STRUCTURES[key], 1.0, tau)
        assert fx.truth == pytest.approx(truth, abs=1e-12), key
        assert fx.coef_without == pytest.approx(without, abs=1e-12), key
        assert fx.coef_with == pytest.approx(with_, abs=1e-12), key
        assert fx.bias_without == pytest.approx(without - truth, abs=1e-12)
        assert fx.bias_with == pytest.approx(with_ - truth, abs=1e-12)


def test_standard_error_factor_by_hand():
    """precision (s = 1, tau = 1): Restvarianz von Y nach X 2 (P und Rauschen) ohne, 1 mit P; Restvarianz von X in beiden Fällen 1: Faktor sqrt(1/2).
    instrument (s = 1, tau = 1): Restvarianz von Y 1; von X 2 ohne, 1 mit I: Faktor sqrt(2)."""
    assert E.effects(K.STRUCTURES["precision"], 1.0, 1.0).se_factor == pytest.approx(math.sqrt(0.5))
    assert E.effects(K.STRUCTURES["instrument"], 1.0, 1.0).se_factor == pytest.approx(math.sqrt(2))


def test_build_places_the_coefficients():
    parents, b = E.build(K.STRUCTURES["mediator"], 0.4, 0.7)       # 0 = Faktor, 1 = Bestand, 2 = Servicegrad
    assert parents == ((), (0,), (0, 1))
    assert b[1, 0] == 0.4 and b[2, 1] == 0.4 and b[2, 0] == 0.7 and b.sum() == pytest.approx(1.5)


def test_population_of_a_chain():
    b = np.zeros((3, 3))
    b[1, 0], b[2, 1] = 2.0, 3.0
    cov, total = E.population(b)
    assert total[2, 0] == pytest.approx(6.0) and total[1, 0] == 2.0 and total[0, 2] == 0.0
    assert np.diag(total).tolist() == [0.0, 0.0, 0.0]
    assert cov[0, 0] == 1.0 and cov[1, 1] == 5.0 and cov[2, 2] == pytest.approx(46.0) and cov[0, 2] == pytest.approx(6.0)


def test_to_scm_matches_build():
    for key, st in K.STRUCTURES.items():
        scm = E.to_scm(st, 0.3, 0.8)
        parents, b = E.build(st, 0.3, 0.8)
        assert scm.parents == parents and scm.names == st.nodes
        for j, ps in enumerate(parents):
            assert scm.coefs[j] == tuple(b[j, p] for p in ps), key


def test_classify_covers_all_cases():
    assert E.classify(0.3, 0.0, 1.0) == "hilft"
    assert E.classify(0.0, 0.2, 1.0) == "schadet"
    assert E.classify(0.2, 0.4, 1.0) == "verstärkt"
    assert E.classify(0.4, 0.2, 1.0) == "rechnet teilweise heraus"
    assert E.classify(0.0, 0.0, 0.9) == "neutral, aber genauer"
    assert E.classify(0.0, 0.0, 1.1) == "neutral, aber ungenauer"
    assert E.classify(0.0, 0.0, 1.0) == "neutral"
    assert E.classify(0.0, 0.0, 0.95) == "neutral" and E.classify(0.0, 0.0, 1.05) == "neutral"
    assert E.classify(C.EPS / 2, 0.0, 1.0) == "neutral" and E.classify(0.0, C.EPS / 2, 1.0) == "neutral"


def test_kinds_at_the_defaults():
    kinds = {k: E.effects(st, C.DEFAULT_S, C.DEFAULT_TAU).kind for k, st in K.STRUCTURES.items()}
    assert kinds == {
        "confounder": "hilft", "precision": "neutral, aber genauer", "instrument": "neutral, aber ungenauer", "instrument_hidden": "verstärkt",
        "mediator": "schadet", "collider": "schadet", "m_bias": "schadet", "collider_desc": "schadet", "outcome_desc": "schadet", "mediator_desc": "schadet",
    }


def test_amplification_follows_the_closed_form():
    """Fehler ohne I: s²/(a² + s² + 1); mit I: s²/(s² + 1); Verhältnis 1/(1 − R²) mit R² = a²/(a² + s² + 1)."""
    for s in (0.2, 0.6, 0.9):
        for a in (0.0, 0.5, 1.5):
            b = np.zeros((4, 4))
            b[2, 0], b[3, 0], b[2, 1], b[3, 2] = s, s, a, 0.5
            cov, total = E.population(b)
            e0 = E.coefficient(cov, 2, 3, ()) - total[3, 2]
            e1 = E.coefficient(cov, 2, 3, (1,)) - total[3, 2]
            assert e0 == pytest.approx(s * s / (a * a + s * s + 1))
            assert e1 == pytest.approx(s * s / (s * s + 1))
            assert E.amplification_factor(e0, e1) == pytest.approx(1 / (1 - a * a / (a * a + s * s + 1)))


def test_the_mbias_is_zero_without_a_hidden_path():
    for s in (0.1, 0.5, 0.9):
        fx = E.effects(K.STRUCTURES["m_bias"], s, 0.5)
        assert fx.bias_without == pytest.approx(0.0, abs=1e-12) and fx.bias_with < 0


def test_classify_at_the_tolerance_boundaries():
    """Genau EPS gilt noch als 0; ein Fehler mit mit-Kontrolle gleich ohne-Kontrolle plus EPS ist noch keine Verstärkung."""
    assert E.classify(C.EPS, 0.0, 1.0) == "neutral" and E.classify(0.0, C.EPS, 1.0) == "neutral"
    assert E.classify(0.2, 0.2 + C.EPS, 1.0) == "rechnet teilweise heraus"
    assert E.classify(0.2, 0.2 + 2 * C.EPS, 1.0) == "verstärkt"
