"""Presets, Reglergrenzen und Konstanten."""

import skt_catalog as K
import skt_constants as C
import skt_evaluation as ev
import skt_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, p in C.PRESETS.items():
        assert set(p) == {"struct", "s", "tau", "n", "seed"}, name
        assert C.PRESET_HELP[name]


def test_preset_values_are_valid():
    for name, p in C.PRESETS.items():
        assert p["struct"] in K.STRUCTURES, name
        assert C.S_MIN <= p["s"] <= C.S_MAX and C.TAU_MIN <= p["tau"] <= C.TAU_MAX
        assert C.N_MIN <= p["n"] <= C.N_MAX and (p["n"] - C.N_MIN) % C.N_STEP == 0 and 0 <= p["seed"] <= C.SEED_MAX


def test_the_first_preset_is_the_default_setting():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings() == ev.Settings(**first)


def test_the_presets_show_different_kinds():
    kinds = {name: ev.analyse(ev.Settings(**p)).effects.kind for name, p in C.PRESETS.items()}
    assert kinds == {"Mediator (Voreinstellung)": "schadet", "Confounder (gut)": "hilft", "Collider": "schadet", "M-Bias": "schadet",
                     "Instrument verstärkt": "verstärkt"}


def test_bounds_and_step_grid():
    assert P.bounds("n_slider") == (C.N_MIN, C.N_MAX) and P.bounds("seed_input") == (0, C.SEED_MAX)
    assert P.bounds("s_slider") == (C.S_MIN, C.S_MAX) and P.bounds("tau_slider") == (C.TAU_MIN, C.TAU_MAX)
    assert C.DEFAULT_N in range(C.N_MIN, C.N_MAX + 1, C.N_STEP)
    assert round((C.DEFAULT_S - C.S_MIN) / C.S_STEP, 9) % 1 == 0 and round((C.DEFAULT_TAU - C.TAU_MIN) / C.TAU_STEP, 9) % 1 == 0


def test_experiment_constants_are_consistent():
    assert C.EXP_ZOO_REPS >= 200 and C.EXP_BUTTERFLY_DRAWS >= 10000 and C.RULES_NODES == 7 and C.RULES_P_LO < C.RULES_P_HI
    assert tuple(sorted(C.EXP_MBIAS_STRENGTHS)) == C.EXP_MBIAS_STRENGTHS and C.EXP_AMPLIFY_STRENGTHS[0] == 0.0 and 0.6 in C.EXP_AMPLIFY_STRENGTHS
    assert all(C.S_MIN <= v <= C.S_MAX for v in C.EXP_MBIAS_STRENGTHS)


def test_permalink_specs_cover_all_widgets():
    assert {s.url_param for s in P.SETTING_SPECS.values()} == {"t", "s", "tau", "n", "seed"}
    assert P.SETTING_SPECS["struct_select"].choices == K.ORDER
