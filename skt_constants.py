"""Konstanten: Regler-Grenzen, Experimente, Farben und Presets. Die zehn Strukturen stehen in skt_catalog.py."""

# Rechenaufwand am Maximum: eine Stichprobe mit n = 5 000 und höchstens 5 Knoten, Regression mit einer Kontrolle, unter 20 ms.
N_MIN, N_MAX, N_STEP, DEFAULT_N = 100, 5000, 100, 500
S_MIN, S_MAX, S_STEP, DEFAULT_S = 0.1, 0.9, 0.1, 0.6          # Stärke aller Kanten außer der Wirkung (Einheitsrauschen)
TAU_MIN, TAU_MAX, TAU_STEP, DEFAULT_TAU = 0.0, 1.0, 0.1, 0.5   # direkte Wirkung x -> y
SEED_MAX, DEFAULT_SEED = 999999, 35
Z_CRIT = 1.959964                                              # 95-%-Intervall, Normalnäherung (n >= 100)
EPS = 1e-9                                                     # "Fehler gleich 0" in der Population

# Experimente: feste Ströme (Seeds aus SEED_BASE), nie ein einzelner Seed als Befund.
SEED_BASE = 950000
EXP_ZOO_N, EXP_ZOO_REPS = 500, 300
EXP_MBIAS_STRENGTHS = (0.1, 0.2, 0.3, 0.5, 0.7, 0.9)
EXP_BUTTERFLY_DRAWS = 20000
EXP_AMPLIFY_STRENGTHS = (0.0, 0.3, 0.6, 0.9, 1.2, 1.8)
EXP_RULES_CASES = 3000
RULES_NODES = 7
RULES_P_LO, RULES_P_HI = 0.25, 0.5

COLOR_CONTROL = "#4c78a8"
COLOR_GOOD = "#2F6B65"
COLOR_BAD = "#c0392b"
COLOR_NEUTRAL = "#8a8a8a"
COLOR_AMPLIFY = "#D68A2E"
COLOR_TRUTH = "#D68A2E"
COLOR_HIDDEN = "#cfcfcf"

PRESETS = {
    "Mediator (Voreinstellung)": {"struct": "mediator", "s": DEFAULT_S, "tau": DEFAULT_TAU, "n": DEFAULT_N, "seed": DEFAULT_SEED},
    "Confounder (gut)": {"struct": "confounder", "s": DEFAULT_S, "tau": DEFAULT_TAU, "n": DEFAULT_N, "seed": DEFAULT_SEED},
    "Collider": {"struct": "collider", "s": DEFAULT_S, "tau": DEFAULT_TAU, "n": DEFAULT_N, "seed": DEFAULT_SEED},
    "M-Bias": {"struct": "m_bias", "s": DEFAULT_S, "tau": DEFAULT_TAU, "n": DEFAULT_N, "seed": DEFAULT_SEED},
    "Instrument verstärkt": {"struct": "instrument_hidden", "s": DEFAULT_S, "tau": DEFAULT_TAU, "n": DEFAULT_N, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Mediator (Voreinstellung)": "Die Kontrolle liegt auf dem Weg vom Faktor zum Servicegrad: Wer sie festhält, rechnet den Umweg aus der Wirkung heraus.",
    "Confounder (gut)": "Die Kontrolle ist gemeinsame Ursache von Faktor und Servicegrad: Sie festzuhalten schließt die Hintertür.",
    "Collider": "Die Kontrolle ist Folge von Faktor und Servicegrad: Sie festzuhalten öffnet einen Pfad, den es ohne sie nicht gab.",
    "M-Bias": "Die Kontrolle liegt vor der Behandlung und ist Folge zweier verborgener Ursachen: Sie festzuhalten verbindet sie, aber nur schwach.",
    "Instrument verstärkt": "Eine Variable, die nur den Faktor bewegt, schadet nicht, solange nichts verborgen mitläuft; mit verborgener Störung verstärkt sie die Verzerrung.",
}
