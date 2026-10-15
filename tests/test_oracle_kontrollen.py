"""Orakel: Backdoor-Prüfung gegen die Graphenchirurgie (networkx), Population gegen Stichprobe, Regeln auf bekannten Diagrammen. Unter zehn Sekunden."""

import numpy as np
import pytest

nx = pytest.importorskip("networkx")

import dsep_graph as G  # noqa: E402
import skt_catalog as K  # noqa: E402
import skt_effects as E  # noqa: E402
import skt_rules as R  # noqa: E402
from kausal_generator import SplitMix64, sample  # noqa: E402


def surgery_valid(parents, x, y, z):
    if set(z) & G.descendants(parents, x):
        return False
    g = nx.DiGraph()
    g.add_nodes_from(range(len(parents)))
    g.add_edges_from((p, c) for c, ps in enumerate(parents) for p in ps if p != x)
    return bool(nx.is_d_separator(g, {x}, {y}, set(z)))


def test_backdoor_against_the_graph_surgery_on_random_diagrams():
    rng = SplitMix64(9)
    checked = 0
    for _ in range(200):
        parents = R.random_dag(6, 0.2 + 0.4 * float(rng.uniform(1)[0]), rng)
        u = rng.uniform(2)
        x, y = int(u[0] * 6), int(u[1] * 6)
        if x == y:
            continue
        others = [v for v in range(6) if v not in (x, y)]
        for z in R.subsets(others):
            assert R.backdoor_valid(parents, x, y, z) == surgery_valid(parents, x, y, z), (parents, x, y, z)
            checked += 1
    assert checked > 2500


def test_valid_sets_recover_the_total_effect_in_random_populations():
    rng = SplitMix64(11)
    valid = 0
    for _ in range(150):
        parents = R.random_dag(6, 0.3 + 0.3 * float(rng.uniform(1)[0]), rng)
        u = rng.uniform(2)
        x, y = int(u[0] * 6), int(u[1] * 6)
        if x == y:
            continue
        b = np.zeros((6, 6))
        for j, ps in enumerate(parents):
            if ps:
                w = rng.uniform(2 * len(ps))
                for k, p in enumerate(ps):
                    b[j, p] = (0.3 + 0.6 * w[k]) * (1.0 if w[len(ps) + k] < 0.5 else -1.0)
        cov, total = E.population(b)
        others = [v for v in range(6) if v not in (x, y)]
        for z in R.subsets(others):
            if R.backdoor_valid(parents, x, y, z):
                assert E.coefficient(cov, x, y, z) == pytest.approx(float(total[y, x]), abs=1e-9)
                valid += 1
    assert valid > 200


def test_population_coefficient_against_a_large_sample():
    for key in K.ORDER:
        st = K.STRUCTURES[key]
        fx = E.effects(st, 0.6, 0.5)
        n = 200000
        d = sample(E.to_scm(st, 0.6, 0.5), n, SplitMix64(5))
        names = st.nodes
        x, y, c = d[names[st.x]][0], d[names[st.y]][0], d[names[st.control]][0]
        with_ = np.linalg.lstsq(np.column_stack([np.ones(n), x, c]), y, rcond=None)[0][1]
        without = np.linalg.lstsq(np.column_stack([np.ones(n), x]), y, rcond=None)[0][1]
        assert with_ == pytest.approx(fx.coef_with, abs=0.02), key
        assert without == pytest.approx(fx.coef_without, abs=0.02), key


def test_rules_on_the_confounder_diagram():
    parents = ((), (0,), (0, 1))                       # 0 = Z, 1 = X, 2 = Y
    sets = R.rule_sets(parents, 1, 2, {0, 1, 2})
    assert sets == {"alle beobachteten Variablen": (0,), "alle beobachteten Nicht-Nachfahren von x": (0,), "Disjunktivkriterium": (0,), "leere Menge": ()}
    assert R.backdoor_valid(parents, 1, 2, ()) is False and R.backdoor_valid(parents, 1, 2, (0,)) is True


def test_rules_with_a_mediator_and_a_collider():
    parents = ((), (0,), (0, 1), (0, 2))               # 0 = X, 1 = M, 2 = Y, 3 = C (Collider von X und Y)
    sets = R.rule_sets(parents, 0, 2, {0, 1, 2, 3})
    assert sets["alle beobachteten Variablen"] == (1, 3) and sets["alle beobachteten Nicht-Nachfahren von x"] == ()
    assert sets["Disjunktivkriterium"] == ()
    assert not R.backdoor_valid(parents, 0, 2, sets["alle beobachteten Variablen"])
    assert R.backdoor_valid(parents, 0, 2, ())


def test_disjunctive_criterion_excludes_the_hidden_ancestor():
    parents = ((), (0,), (0, 1))
    sets = R.rule_sets(parents, 1, 2, {1, 2})           # 0 verborgen
    assert sets["Disjunktivkriterium"] == () and sets["alle beobachteten Variablen"] == ()
    assert not any(R.backdoor_valid(parents, 1, 2, z) for z in R.subsets([]))


def test_random_dag_is_reproducible_and_acyclic():
    a, b = R.random_dag(7, 0.4, SplitMix64(3)), R.random_dag(7, 0.4, SplitMix64(3))
    assert a == b and all(p < j for j, ps in enumerate(a) for p in ps)
    assert sum(len(p) for p in R.random_dag(7, 1.0, SplitMix64(1))) == 21 and sum(len(p) for p in R.random_dag(7, 0.0, SplitMix64(1))) == 0


def test_subsets_enumerate_the_power_set():
    s = list(R.subsets([2, 0, 1]))
    assert len(s) == 8 and s[0] == () and s[-1] == (0, 1, 2) and len(set(s)) == 8


def test_d_separation_against_networkx_and_the_path_explanation():
    rng = SplitMix64(21)
    checked = 0
    for _ in range(80):
        parents = R.random_dag(6, 0.2 + 0.4 * float(rng.uniform(1)[0]), rng)
        g = nx.DiGraph()
        g.add_nodes_from(range(6))
        g.add_edges_from((p, c) for c, ps in enumerate(parents) for p in ps)
        for x, y in ((0, 5), (1, 4), (2, 3)):
            others = [v for v in range(6) if v not in (x, y)]
            for z in R.subsets(others):
                sep = G.d_separated(parents, x, y, z)
                assert sep == bool(nx.is_d_separator(g, {x}, {y}, set(z)))
                assert sep == all(p.blocked for p in G.explain_paths(parents, x, y, z))
                checked += 1
    assert checked > 3000


def test_rules_experiment_draws_enough_diagrams_without_looping_forever():
    res = R.rules_experiment(cases=50)
    assert res["cases"] == 50 and 0 < res["exists"] <= 50
