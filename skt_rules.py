"""Auswahlregeln für Kontrollen in Zufallsdiagrammen: Backdoor-Kriterium (über dsep_graph), Regeln und der Vergleich bei verborgenen Variablen.
Nur Standardbibliothek, numpy und dsep_graph, kein Streamlit. Zufall nur über einen übergebenen SplitMix64."""

from __future__ import annotations

import itertools

import dsep_graph as G
import skt_constants as C
from kausal_generator import SplitMix64

RULE_NAMES = (
    "alle beobachteten Variablen",
    "alle beobachteten Nicht-Nachfahren von x",
    "Disjunktivkriterium",
    "leere Menge",
)


def backdoor_valid(parents, x: int, y: int, z=()) -> bool:
    """Backdoor-Kriterium: keine Nachfahren von x in z und jeder Pfad mit einem Pfeil in x hinein ist blockiert."""
    z = set(z)
    if z & G.descendants(parents, x):
        return False
    return all(p.blocked for p in G.explain_paths(parents, x, y, z) if p.arrows and p.arrows[0] == "←")


def random_dag(n: int, p: float, rng: SplitMix64) -> tuple:
    """Zufälliges Diagramm in der Knotenreihenfolge 0..n-1 mit Kantenwahrscheinlichkeit p (ein Block Gleichverteilte)."""
    u = rng.uniform(n * (n - 1) // 2)
    k = 0
    parents = []
    for j in range(n):
        ps = []
        for i in range(j):
            if u[k] < p:
                ps.append(i)
            k += 1
        parents.append(tuple(ps))
    return tuple(parents)


def subsets(items):
    items = sorted(items)
    for k in range(len(items) + 1):
        yield from itertools.combinations(items, k)


def rule_sets(parents, x: int, y: int, observed) -> dict:
    """Die Mengen, die die Regeln aus den beobachteten Variablen bilden."""
    desc = G.descendants(parents, x)
    causes = (G.ancestors(parents, {x}) | G.ancestors(parents, {y})) - {x, y}
    others = [v for v in sorted(observed) if v not in (x, y)]
    return {
        "alle beobachteten Variablen": tuple(others),
        "alle beobachteten Nicht-Nachfahren von x": tuple(v for v in others if v not in desc),
        "Disjunktivkriterium": tuple(v for v in others if v in causes and v not in desc),
        "leere Menge": (),
    }


def rules_experiment(cases: int = C.EXP_RULES_CASES) -> dict:
    """Je Zufallsdiagramm mit kausalem Pfad x -> y werden ein oder zwei Vorfahren von x oder y verborgen. Gezählt wird, wie oft jede Regel eine gültige Menge
    liefert, getrennt nach „unter den beobachteten Variablen existiert eine gültige Menge“ und nicht."""
    rng = SplitMix64(C.SEED_BASE + 4)
    n = C.RULES_NODES
    counts = {(name, e): [0, 0] for name in RULE_NAMES for e in (True, False)}
    done = exists_total = skipped = attempts = 0
    while done < cases:
        attempts += 1
        if attempts > 100 * cases:
            raise RuntimeError("zu wenige Zufallsdiagramme mit einem kausalen Pfad von x nach y")
        parents = random_dag(n, C.RULES_P_LO + (C.RULES_P_HI - C.RULES_P_LO) * float(rng.uniform(1)[0]), rng)
        u = rng.uniform(5)
        x, y = sorted((int(u[0] * n), int(u[1] * n)))
        if x == y or y not in G.descendants(parents, x):
            continue
        causes = sorted((G.ancestors(parents, {x}) | G.ancestors(parents, {y})) - {x, y})
        if not causes:
            skipped += 1
            continue
        k = min(len(causes), 1 + int(u[2] * 2))
        hidden = {causes[int(u[3] * len(causes))]}
        if k == 2:
            rest = [v for v in causes if v not in hidden]
            hidden.add(rest[int(u[4] * len(rest))])
        observed = [v for v in range(n) if v not in hidden]
        others = [v for v in observed if v not in (x, y)]
        exists = any(backdoor_valid(parents, x, y, z) for z in subsets(others))
        exists_total += exists
        done += 1
        for name, z in rule_sets(parents, x, y, observed).items():
            c = counts[(name, exists)]
            c[0] += 1
            c[1] += backdoor_valid(parents, x, y, z)
    return {"cases": cases, "exists": exists_total, "counts": counts}
