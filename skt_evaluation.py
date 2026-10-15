"""Auswertung: Stichprobe mit und ohne Kontrolle, die Experimente über feste Ströme und die Verdikte. Nur numpy, kein Streamlit."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import skt_catalog as K
import skt_constants as C
import skt_effects as E
import skt_rules as R
from kausal_generator import SplitMix64, sample


def de(x: float, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und typografischem Minuszeichen."""
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def signed(x: float, digits: int = 2) -> str:
    return ("+" if x >= 0 else "−") + de(abs(x), digits)


def ols_coefficient(y: np.ndarray, x: np.ndarray, zs=()) -> tuple[np.ndarray, np.ndarray]:
    """Koeffizient von x und Standardfehler in y ~ 1 + x + zs (kleinste Quadrate), je Wiederholung (Zeilen); Eingaben (reps, n)."""
    n = y.shape[1]
    design = np.stack([np.ones_like(y), x] + list(zs), axis=2)
    xtx = np.einsum("rni,rnj->rij", design, design)
    xty = np.einsum("rni,rn->ri", design, y)
    beta = np.linalg.solve(xtx, xty[..., None])[..., 0]
    resid = y - np.einsum("rni,ri->rn", design, beta)
    se = np.sqrt((resid ** 2).sum(axis=1) / (n - design.shape[2]) * np.linalg.inv(xtx)[:, 1, 1])
    return beta[:, 1], se


# ----------------------------------------------------------------------------- Auswertung der Einstellungen

@dataclass(frozen=True)
class Settings:
    struct: str = "mediator"
    s: float = C.DEFAULT_S
    tau: float = C.DEFAULT_TAU
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED


@dataclass
class Analysis:
    settings: Settings
    structure: K.Structure
    effects: E.Effects
    est_without: float
    se_without: float
    est_with: float
    se_with: float
    covers_without: bool
    covers_with: bool


def analyse(st: Settings) -> Analysis:
    struct = K.STRUCTURES[st.struct]
    fx = E.effects(struct, st.s, st.tau)
    d = sample(E.to_scm(struct, st.s, st.tau), st.n, SplitMix64(st.seed))
    names = struct.nodes
    yv, xv = d[names[struct.y]], d[names[struct.x]]
    e0, s0 = ols_coefficient(yv, xv, [])
    e1, s1 = ols_coefficient(yv, xv, [d[names[struct.control]]])
    z = C.Z_CRIT
    return Analysis(st, struct, fx, float(e0[0]), float(s0[0]), float(e1[0]), float(s1[0]),
                    bool(abs(e0[0] - fx.truth) <= z * s0[0]), bool(abs(e1[0] - fx.truth) <= z * s1[0]))


# ----------------------------------------------------------------------------- Experiment 1: der Zoo

def zoo_experiment(n: int = C.EXP_ZOO_N, reps: int = C.EXP_ZOO_REPS, s: float = C.DEFAULT_S, tau: float = C.DEFAULT_TAU) -> list[dict]:
    rows = []
    for i, key in enumerate(K.ORDER):
        struct = K.STRUCTURES[key]
        fx = E.effects(struct, s, tau)
        d = sample(E.to_scm(struct, s, tau), n, SplitMix64(C.SEED_BASE + 1 + i), reps)
        names = struct.nodes
        out = {}
        for tag, zs in (("without", []), ("with", [d[names[struct.control]]])):
            est, se = ols_coefficient(d[names[struct.y]], d[names[struct.x]], zs)
            out[tag] = (float(est.mean()), float(np.mean(np.abs(est - fx.truth) <= C.Z_CRIT * se)))
        rows.append({"key": key, "label": struct.label, "effects": fx, "mean_without": out["without"][0], "cover_without": out["without"][1],
                     "mean_with": out["with"][0], "cover_with": out["with"][1]})
    return rows


# ----------------------------------------------------------------------------- Experiment 2: M-Bias und Schmetterling

def mbias_experiment(strengths=C.EXP_MBIAS_STRENGTHS, tau: float = C.DEFAULT_TAU) -> list[dict]:
    rows = []
    for sv in strengths:
        m = E.effects(K.STRUCTURES["m_bias"], sv, tau)
        c = E.effects(K.STRUCTURES["confounder"], sv, tau)
        rows.append({"s": sv, "mbias": m.bias_with, "confounding": c.bias_without, "ratio": abs(m.bias_with) / abs(c.bias_without)})
    return rows


def butterfly_experiment(draws: int = C.EXP_BUTTERFLY_DRAWS, tau: float = C.DEFAULT_TAU) -> dict:
    """C ist Collider von U1 und U2 und zugleich Ursache von X und Y. Sechs Kantenstärken ±0,1 bis ±0,9 je Ziehung, die Wirkung x -> y ist `tau`;
    verglichen werden die Fehler mit und ohne C."""
    rng = SplitMix64(C.SEED_BASE + 2)
    u = rng.uniform(12 * draws).reshape(draws, 12)
    vals = (0.1 + 0.8 * u[:, :6]) * np.where(u[:, 6:] < 0.5, -1.0, 1.0)
    better = 0
    ratios = np.empty(draws)
    for k in range(draws):
        b = np.zeros((5, 5))                      # 0 U1, 1 U2, 2 C, 3 X, 4 Y
        b[2, 0], b[2, 1], b[3, 0], b[4, 1], b[3, 2], b[4, 2] = vals[k]
        b[4, 3] = tau
        cov, total = E.population(b)
        truth = float(total[4, 3])
        e_with = abs(E.coefficient(cov, 3, 4, (2,)) - truth)
        e_without = abs(E.coefficient(cov, 3, 4, ()) - truth)
        better += e_with < e_without
        ratios[k] = e_with / e_without if e_without > 0 else 0.0
    return {"draws": draws, "better": better / draws, "median_ratio": float(np.median(ratios)), "share_double": float(np.mean(ratios > 2.0))}


# ----------------------------------------------------------------------------- Experiment 3: Bias-Verstärkung

def amplification_experiment(strengths=C.EXP_AMPLIFY_STRENGTHS, s: float = C.DEFAULT_S, tau: float = C.DEFAULT_TAU) -> list[dict]:
    rows = []
    for a in strengths:
        b = np.zeros((4, 4))                      # 0 U, 1 I, 2 X, 3 Y
        b[2, 0], b[3, 0], b[2, 1], b[3, 2] = s, s, a, tau
        cov, total = E.population(b)
        truth = float(total[3, 2])
        e0 = E.coefficient(cov, 2, 3, ()) - truth
        e1 = E.coefficient(cov, 2, 3, (1,)) - truth
        rows.append({"a": a, "without": e0, "with": e1, "factor": E.amplification_factor(e0, e1)})
    return rows


# ----------------------------------------------------------------------------- Verdikte: (Art, Text)

KIND_STYLE = {"hilft": "success", "neutral": "info", "neutral, aber genauer": "success", "neutral, aber ungenauer": "info",
              "schadet": "warning", "verstärkt": "warning", "rechnet teilweise heraus": "info"}


def verdict_instance(a: Analysis) -> tuple[str, str]:
    fx, struct = a.effects, a.structure
    name = struct.nodes[struct.control]
    head = f"Kontrolle „{name}“: **{fx.kind}**. "
    if fx.kind == "hilft":
        body = f"Ohne sie liegt die Schätzung im Grenzfall um {signed(fx.bias_without)} daneben, mit ihr trifft sie die Wirkung ({de(fx.truth)})."
    elif fx.kind == "schadet":
        rel = abs(fx.bias_with / fx.truth) if fx.truth else float("inf")
        body = (f"Ohne sie trifft die Schätzung die Wirkung ({de(fx.truth)}), mit ihr liegt sie im Grenzfall um {signed(fx.bias_with)} daneben"
                + (f", das sind {de(100 * rel, 0)} % der Wirkung." if np.isfinite(rel) else "."))
    elif fx.kind == "verstärkt":
        body = (f"Der Fehler wächst von {signed(fx.bias_without)} auf {signed(fx.bias_with)}, auf das {de(E.amplification_factor(fx.bias_without, fx.bias_with), 2)}fache.")
    elif fx.kind == "rechnet teilweise heraus":
        body = f"Der Fehler sinkt von {signed(fx.bias_without)} auf {signed(fx.bias_with)}, verschwindet aber nicht."
    else:
        body = f"Beide Schätzungen treffen die Wirkung ({de(fx.truth)}); der Standardfehler ändert sich um den Faktor {de(fx.se_factor, 2)}."
    return KIND_STYLE[fx.kind], head + body


def verdict_zoo(rows: list) -> tuple[str, str]:
    bad = [r for r in rows if r["effects"].kind in ("schadet", "verstärkt")]
    good = [r for r in rows if r["effects"].kind == "hilft"]
    return "info", (f"Von {len(rows)} Strukturen helfen {len(good)} der Schätzung, {len(bad)} schaden oder verstärken die Verzerrung; die übrigen sind neutral oder rechnen "
                    f"teilweise heraus. Die Deckung fällt bei Mediator und Collider von rund 95 % auf {de(100 * max(r['cover_with'] for r in rows if r['key'] in ('mediator', 'collider')), 0)} %.")


def verdict_mbias(rows: list, butterfly: dict) -> tuple[str, str]:
    lo, hi = min(r["ratio"] for r in rows), max(r["ratio"] for r in rows)
    draws = f"{butterfly['draws']:,}".replace(",", ".")
    return "info", (f"Der M-Bias ist {de(100 * lo, 0)} bis {de(100 * hi, 0)} % so groß wie der Confounding-Fehler bei gleicher Kantenstärke. Im Schmetterling liegt "
                    f"Kontrollieren in {de(100 * butterfly['better'], 0)} % der {draws} Ziehungen näher an der Wahrheit.")


def verdict_amplification(rows: list) -> tuple[str, str]:
    r = next(r for r in rows if abs(r["a"] - 0.6) < 1e-9)
    big = rows[-1]
    return "warning", (f"Mit der Stärke a = {de(r['a'], 1)} des Instruments wächst der Fehler auf das {de(r['factor'], 2)}fache, bei a = {de(big['a'], 1)} auf das "
                       f"{de(big['factor'], 2)}fache: Je mehr harmlose Streuung des Faktors das Instrument bindet, desto größer ist der Anteil der verborgenen Störung am Rest.")


def verdict_rules(res: dict) -> tuple[str, str]:
    def share(name):
        c = res["counts"][(name, True)]
        return c[1] / c[0]

    return "info", (f"Wo unter den beobachteten Variablen eine gültige Menge existiert ({res['exists']} von {res['cases']} Fällen), ist „alle beobachteten Variablen“ nur in "
                    f"{de(100 * share('alle beobachteten Variablen'), 0)} % gültig, „alle Nicht-Nachfahren von x“ in {de(100 * share('alle beobachteten Nicht-Nachfahren von x'), 1)} %, "
                    f"das Disjunktivkriterium in {de(100 * share('Disjunktivkriterium'), 0)} %.")
