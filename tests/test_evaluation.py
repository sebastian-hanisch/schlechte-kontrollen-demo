"""Auswertung: Stichprobe, Experimente (feste Ströme), Verdikte, Formatierung."""

import numpy as np
import pytest

import skt_catalog as K
import skt_constants as C
import skt_effects as E
import skt_evaluation as ev
import skt_rules as R
from kausal_generator import SplitMix64, sample


@pytest.fixture(scope="module")
def zoo():
    return ev.zoo_experiment()


def test_number_format():
    assert ev.de(1.5, 1) == "1,5" and ev.de(-0.25) == "−0,25"
    assert ev.signed(0.3) == "+0,30" and ev.signed(-0.3) == "−0,30" and ev.signed(0.0) == "+0,00"


def test_ols_against_numpy_lstsq():
    st = K.STRUCTURES["confounder"]
    d = sample(E.to_scm(st, 0.6, 0.5), 400, SplitMix64(8), reps=3)
    est, se = ev.ols_coefficient(d["Servicegrad"], d["Faktor"], [d["Schwankung"]])
    for r in range(3):
        design = np.column_stack([np.ones(400), d["Faktor"][r], d["Schwankung"][r]])
        coef, res, *_ = np.linalg.lstsq(design, d["Servicegrad"][r], rcond=None)
        assert est[r] == pytest.approx(coef[1], rel=1e-9)
        assert se[r] == pytest.approx(np.sqrt(res[0] / (400 - 3) * np.linalg.inv(design.T @ design)[1, 1]), rel=1e-9)


def test_analyse_is_deterministic_and_consistent():
    a, b = ev.analyse(ev.Settings()), ev.analyse(ev.Settings())
    assert (a.est_with, a.est_without) == (b.est_with, b.est_without)
    assert a.covers_without == (abs(a.est_without - a.effects.truth) <= C.Z_CRIT * a.se_without)
    assert a.covers_with == (abs(a.est_with - a.effects.truth) <= C.Z_CRIT * a.se_with)
    assert ev.analyse(ev.Settings(seed=36)).est_with != a.est_with


def test_analyse_every_structure_at_the_slider_edges():
    for key in K.ORDER:
        for s, tau, n in ((C.S_MIN, C.TAU_MIN, C.N_MIN), (C.S_MAX, C.TAU_MAX, C.N_MAX)):
            a = ev.analyse(ev.Settings(key, s, tau, n, 1))
            assert np.isfinite([a.est_without, a.est_with, a.se_without, a.se_with]).all()


def test_the_sample_estimate_converges_to_the_population_value():
    for key in ("confounder", "mediator", "collider", "instrument_hidden"):
        a = ev.analyse(ev.Settings(key, 0.6, 0.5, 5000, 3))
        assert a.est_without == pytest.approx(a.effects.coef_without, abs=0.12), key
        assert a.est_with == pytest.approx(a.effects.coef_with, abs=0.12), key


def test_zoo_structure_and_coverage(zoo):
    assert [r["key"] for r in zoo] == list(K.ORDER)
    by = {r["key"]: r for r in zoo}
    assert by["confounder"]["cover_without"] < 0.2 and by["confounder"]["cover_with"] > 0.88
    assert by["mediator"]["cover_without"] > 0.88 and by["mediator"]["cover_with"] < 0.2
    assert by["precision"]["cover_without"] > 0.88 and by["precision"]["cover_with"] > 0.88
    assert by["instrument_hidden"]["cover_with"] < 0.2
    for r in zoo:
        assert 0.0 <= r["cover_without"] <= 1.0 and 0.0 <= r["cover_with"] <= 1.0


def test_zoo_is_reproducible():
    a, b = ev.zoo_experiment(reps=20), ev.zoo_experiment(reps=20)
    assert [(r["mean_without"], r["mean_with"]) for r in a] == [(r["mean_without"], r["mean_with"]) for r in b]


def test_mbias_is_smaller_than_confounding_for_every_strength():
    rows = ev.mbias_experiment()
    assert [r["s"] for r in rows] == list(C.EXP_MBIAS_STRENGTHS)
    for r in rows:
        assert r["ratio"] < 1 and r["mbias"] < 0 < r["confounding"]
        assert r["ratio"] == pytest.approx(abs(r["mbias"]) / r["confounding"])
    assert rows[0]["ratio"] < rows[-1]["ratio"]


def test_butterfly_counts_are_fractions_and_reproducible():
    a = ev.butterfly_experiment(draws=500)
    assert a == ev.butterfly_experiment(draws=500)
    assert a["draws"] == 500 and 0 <= a["better"] <= 1 and 0 <= a["share_double"] <= 1 and a["median_ratio"] > 0
    assert (a["better"] * 500) % 1 == pytest.approx(0, abs=1e-9) or (a["better"] * 500) % 1 == pytest.approx(1, abs=1e-9)


def test_amplification_rows():
    rows = ev.amplification_experiment()
    assert [r["a"] for r in rows] == list(C.EXP_AMPLIFY_STRENGTHS)
    assert rows[0]["factor"] == pytest.approx(1.0)
    assert all(rows[i]["factor"] < rows[i + 1]["factor"] for i in range(len(rows) - 1))
    assert all(r["with"] >= r["without"] for r in rows)


def test_verdicts_mention_the_numbers_they_show():
    kind, text = ev.verdict_instance(ev.analyse(ev.Settings()))
    assert kind == "warning" and "**schadet**" in text and "0,86" in text and "−0,36" in text
    kind, text = ev.verdict_instance(ev.analyse(ev.Settings("confounder")))
    assert kind == "success" and "**hilft**" in text and "+0,26" in text
    kind, text = ev.verdict_instance(ev.analyse(ev.Settings("instrument_hidden")))
    assert kind == "warning" and "**verstärkt**" in text and "fache" in text
    kind, text = ev.verdict_instance(ev.analyse(ev.Settings("precision")))
    assert kind == "success" and "genauer" in text
    kind, text = ev.verdict_instance(ev.analyse(ev.Settings("instrument")))
    assert kind == "info" and "ungenauer" in text


def test_verdict_with_zero_truth_has_no_percentage():
    a = ev.analyse(ev.Settings("collider", 0.6, 0.0, 500, 35))
    assert a.effects.truth == 0.0
    text = ev.verdict_instance(a)[1]
    assert "%" not in text and "schadet" in text


def test_zoo_and_rule_verdicts(zoo):
    kind, text = ev.verdict_zoo(zoo)
    assert kind == "info" and "Von 10 Strukturen helfen 1" in text
    res = R.rules_experiment(cases=200)
    assert res["cases"] == 200 and ev.verdict_rules(res)[0] == "info"


def test_rules_counts_are_consistent():
    res = R.rules_experiment(cases=300)
    for name in R.RULE_NAMES:
        assert sum(res["counts"][(name, e)][0] for e in (True, False)) == 300
        assert res["counts"][(name, True)][0] == res["exists"]
        assert res["counts"][(name, False)][1] == 0       # ohne gültige Menge kann keine Regel gültig sein
    assert res["counts"][("Disjunktivkriterium", True)][1] == res["exists"]
