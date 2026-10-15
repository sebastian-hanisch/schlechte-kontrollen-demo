"""Jede Zahl aus README.md und den App-Texten wird hier über dieselben Auswertungsfunktionen nachgerechnet (DEMO-PLAYBOOK §4).

Zufallsdiagramme und Ziehungen kommen aus SplitMix64 (ganzzahlig, plattformstabil): ihre Zählungen werden exakt geprüft. Stichprobenwerte (Deckung, Schätzungen) mit
Toleranz, damit Rundung und Bibliotheksversionen (CI installiert ungepinnt) nichts kippen.
"""

import pytest

import skt_catalog as K
import skt_constants as C
import skt_effects as E
import skt_evaluation as ev
import skt_rules as R


@pytest.fixture(scope="module")
def zoo():
    return {r["key"]: r for r in ev.zoo_experiment()}


@pytest.fixture(scope="module")
def mbias():
    return ev.mbias_experiment()


@pytest.fixture(scope="module")
def rules():
    return R.rules_experiment()


def fx(key):
    return E.effects(K.STRUCTURES[key], C.DEFAULT_S, C.DEFAULT_TAU)


# ----------------------------------------------------------------------------- Standard-Stichprobe

def test_default_sample_and_verdict():
    a = ev.analyse(ev.Settings())
    assert a.effects.truth == pytest.approx(0.86) and a.effects.kind == "schadet"
    assert a.est_without == pytest.approx(0.92, abs=0.005) and a.est_with == pytest.approx(0.52, abs=0.005)
    assert a.covers_without and not a.covers_with
    assert a.effects.bias_with == pytest.approx(-0.36, abs=0.0005)
    assert abs(a.effects.bias_with / a.effects.truth) == pytest.approx(0.42, abs=0.005)
    assert "42 %" in ev.verdict_instance(a)[1]


# ----------------------------------------------------------------------------- Population der zehn Strukturen

def test_population_table_of_the_ten_structures():
    expected = {                      # (Wahrheit, Fehler ohne, Fehler mit, Einordnung)
        "confounder": (0.50, 0.26, 0.0, "hilft"),
        "precision": (0.50, 0.0, 0.0, "neutral, aber genauer"),
        "instrument": (0.50, 0.0, 0.0, "neutral, aber ungenauer"),
        "instrument_hidden": (0.50, 0.21, 0.26, "verstärkt"),
        "mediator": (0.86, 0.0, -0.36, "schadet"),
        "collider": (0.50, 0.0, -0.40, "schadet"),
        "m_bias": (0.50, 0.0, -0.06, "schadet"),
        "collider_desc": (0.50, 0.0, -0.13, "schadet"),
        "outcome_desc": (0.50, 0.0, -0.13, "schadet"),
        "mediator_desc": (0.86, 0.0, -0.10, "schadet"),
    }
    for key, (truth, b0, b1, kind) in expected.items():
        f = fx(key)
        assert f.truth == pytest.approx(truth, abs=0.005), key
        assert f.bias_without == pytest.approx(b0, abs=0.005), key
        assert f.bias_with == pytest.approx(b1, abs=0.005), key
        assert f.kind == kind, key
    assert sum(fx(k).kind == "hilft" for k in K.ORDER) == 1
    assert fx("mediator").coef_with == pytest.approx(0.5) and fx("collider").coef_with == pytest.approx(0.5 - 0.397, abs=0.001)


def test_standard_error_factors():
    assert fx("precision").se_factor == pytest.approx(0.86, abs=0.005)
    assert fx("instrument").se_factor == pytest.approx(1.17, abs=0.005)
    assert fx("outcome_desc").se_factor == pytest.approx(0.89, abs=0.005)
    assert fx("collider").se_factor == pytest.approx(1.08, abs=0.005)


# ----------------------------------------------------------------------------- Experiment 1: Deckung

def test_zoo_coverage(zoo):
    pct = {k: (100 * r["cover_without"], 100 * r["cover_with"]) for k, r in zoo.items()}
    assert pct["mediator"][0] > 90 and pct["mediator"][1] < 3
    assert pct["collider"][0] > 90 and pct["collider"][1] < 3
    assert pct["confounder"][0] < 3 and pct["confounder"][1] > 88
    assert pct["m_bias"][0] > 90 and 70 <= pct["m_bias"][1] <= 84            # 94 → 77 %
    assert pct["collider_desc"][1] == pytest.approx(18, abs=7) and pct["collider_desc"][0] > 94
    assert pct["outcome_desc"][1] == pytest.approx(6, abs=5) and pct["outcome_desc"][0] > 92
    assert pct["mediator_desc"][1] == pytest.approx(53, abs=9) and pct["mediator_desc"][0] > 88
    assert pct["instrument_hidden"] == (0.0, 0.0)
    assert pct["precision"][0] > 88 and pct["precision"][1] > 88 and pct["instrument"][0] > 88 and pct["instrument"][1] > 88


# ----------------------------------------------------------------------------- Experiment 2: M-Bias und Schmetterling

def test_mbias_is_small(mbias):
    ratios = [r["ratio"] for r in mbias]
    assert round(100 * min(ratios)) == 1 and round(100 * max(ratios)) == 36
    assert fx("m_bias").bias_with == pytest.approx(-0.059, abs=0.001)
    assert "1 bis 36 %" in ev.verdict_mbias(mbias, ev.butterfly_experiment(draws=200))[1]


def test_butterfly():
    b = ev.butterfly_experiment()
    assert b["draws"] == 20000
    assert 100 * b["better"] == pytest.approx(91.6, abs=0.0501)
    assert b["median_ratio"] == pytest.approx(0.11, abs=0.005)
    assert 100 * b["share_double"] == pytest.approx(4.1, abs=0.1)


# ----------------------------------------------------------------------------- Experiment 3: Bias-Verstärkung

def test_amplification():
    rows = ev.amplification_experiment()
    assert [round(r["factor"], 2) for r in rows] == [1.0, 1.07, 1.26, 1.60, 2.06, 3.38]
    r = rows[2]
    assert r["without"] == pytest.approx(0.21, abs=0.005) and r["with"] == pytest.approx(0.26, abs=0.005)
    assert "3,38fache" in ev.verdict_amplification(rows)[1]


# ----------------------------------------------------------------------------- Experiment 4: Faustregeln

def test_rules_experiment(rules):
    c = rules["counts"]
    assert rules["cases"] == 3000 and rules["exists"] == 2493
    assert c[("alle beobachteten Variablen", True)] == [2493, 413]
    assert c[("alle beobachteten Nicht-Nachfahren von x", True)] == [2493, 2483]
    assert c[("Disjunktivkriterium", True)] == [2493, 2493]
    assert c[("leere Menge", True)] == [2493, 1989]
    assert all(c[(name, False)] == [507, 0] for name in R.RULE_NAMES)
    assert round(100 * 413 / 2493) == 17 and round(100 * 2483 / 2493, 1) == 99.6 and round(100 * 1989 / 2493) == 80
    assert rules["cases"] - rules["exists"] == 507
