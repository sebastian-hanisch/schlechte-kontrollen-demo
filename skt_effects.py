"""Population: Koeffizient von x in der Regression auf x (und die Kontrolle), Fehler gegen die Gesamtwirkung, Standardfehler-Faktor, Verstärkung, Einordnung.
Nur numpy, kein Streamlit. Jede Einheit eine reine Funktion."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

import skt_catalog as K
import skt_constants as C
from kausal_generator import Scm


def build(struct: K.Structure, s: float, tau: float):
    """(Elterntupel, B-Matrix) der Struktur; B[kind, eltern] = Koeffizient."""
    n = len(struct.nodes)
    parents = [[] for _ in range(n)]
    b = np.zeros((n, n))
    for p, c, kind in struct.edges:
        parents[c].append(p)
        b[c, p] = K.coefficient(kind, s, tau)
    return tuple(tuple(sorted(p)) for p in parents), b


def to_scm(struct: K.Structure, s: float, tau: float) -> Scm:
    parents, b = build(struct, s, tau)
    n = len(struct.nodes)
    return Scm(names=struct.nodes, parents=parents, coefs=tuple(tuple(float(b[j, p]) for p in parents[j]) for j in range(n)),
               intercepts=(0.0,) * n, noise_sd=(1.0,) * n, binary=(False,) * n)


def population(b: np.ndarray):
    """Kovarianz Σ = (I − B)⁻¹(I − B)⁻ᵀ und Gesamtwirkungen T = (I − B)⁻¹ − I bei Einheitsrauschen."""
    inv = np.linalg.inv(np.eye(len(b)) - b)
    return inv @ inv.T, inv - np.eye(len(b))


def coefficient(cov: np.ndarray, x: int, y: int, z=()) -> float:
    """Koeffizient von x in der Regression von y auf x und z (Population)."""
    idx = [x] + list(z)
    return float(np.linalg.solve(cov[np.ix_(idx, idx)], cov[idx, y])[0])


def se_scale(cov: np.ndarray, x: int, y: int, z=()) -> float:
    """sqrt(Restvarianz von y / Restvarianz von x): der Standardfehler des Koeffizienten ist diese Größe geteilt durch sqrt(n)."""
    idx = [x] + list(z)
    c = cov[idx, y]
    beta = np.linalg.solve(cov[np.ix_(idx, idx)], c)
    res_y = cov[y, y] - c @ beta
    if z:
        zz = list(z)
        bx = np.linalg.solve(cov[np.ix_(zz, zz)], cov[zz, x])
        res_x = cov[x, x] - cov[zz, x] @ bx
    else:
        res_x = cov[x, x]
    return math.sqrt(res_y / res_x)


@dataclass(frozen=True)
class Effects:
    truth: float            # Gesamtwirkung von x auf y
    coef_without: float
    coef_with: float
    bias_without: float
    bias_with: float
    se_factor: float        # Standardfehler mit Kontrolle / ohne Kontrolle bei gleichem n
    kind: str               # Einordnung


def classify(bias_without: float, bias_with: float, se_factor: float) -> str:
    """Einordnung der Kontrolle nach dem Fehler im Grenzfall: hilft, neutral (genauer / ungenauer), schadet, verstärkt, rechnet teilweise heraus."""
    b0, b1 = abs(bias_without) > C.EPS, abs(bias_with) > C.EPS
    if not b0 and not b1:
        if se_factor < 0.95:
            return "neutral, aber genauer"
        if se_factor > 1.05:
            return "neutral, aber ungenauer"
        return "neutral"
    if b0 and not b1:
        return "hilft"
    if not b0 and b1:
        return "schadet"
    return "verstärkt" if abs(bias_with) > abs(bias_without) + C.EPS else "rechnet teilweise heraus"


def effects(struct: K.Structure, s: float, tau: float) -> Effects:
    _, b = build(struct, s, tau)
    cov, total = population(b)
    truth = float(total[struct.y, struct.x])
    c0 = coefficient(cov, struct.x, struct.y, ())
    c1 = coefficient(cov, struct.x, struct.y, (struct.control,))
    factor = se_scale(cov, struct.x, struct.y, (struct.control,)) / se_scale(cov, struct.x, struct.y, ())
    return Effects(truth, c0, c1, c0 - truth, c1 - truth, factor, classify(c0 - truth, c1 - truth, factor))


def amplification_factor(bias_without: float, bias_with: float) -> float:
    """Verhältnis der Fehler mit und ohne Kontrolle (nur sinnvoll, wenn der Fehler ohne Kontrolle nicht 0 ist)."""
    return bias_with / bias_without
