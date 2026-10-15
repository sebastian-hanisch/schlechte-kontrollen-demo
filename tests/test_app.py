"""End-to-end Smoke-Test via Streamlits AppTest: lädt app.py, klickt jeden Preset-Button, fährt die Regler an die Grenzen, wechselt die Struktur und prüft,
dass kein Python-Fehler auftritt."""

import os

from streamlit.testing.v1 import AppTest

import skt_catalog as K
import skt_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = 240


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metrics(at):
    return {m.label: m.value for m in at.metric}


def test_app_loads_and_shows_the_default_verdict():
    at = _fresh_app()
    assert at.selectbox(key="struct_select").value == "mediator"
    m = _metrics(at)
    assert m["Einordnung der Kontrolle"] == "schadet" and m["Wahre Wirkung von x"] == "+0,860"
    assert any("schadet" in w.value for w in at.warning)


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_the_sliders_at_min_and_max_do_not_raise():
    for key in ("n_slider", "s_slider", "tau_slider"):
        for edge in ("min", "max"):
            at = _fresh_app()
            sl = at.slider(key=key)
            sl.set_value(sl.min if edge == "min" else sl.max).run(timeout=TIMEOUT)
            assert not at.exception, (key, edge, [str(e) for e in at.exception])


def test_every_preset_is_applied_to_the_widgets():
    labels = {b.label: i for i, b in enumerate(_fresh_app().button)}
    for name, preset in C.PRESETS.items():
        at = _fresh_app()
        at.button[labels[name]].click().run(timeout=TIMEOUT)
        assert not at.exception, (name, [str(e) for e in at.exception])
        assert at.selectbox(key="struct_select").value == preset["struct"]
        assert at.slider(key="s_slider").value == preset["s"] and at.slider(key="tau_slider").value == preset["tau"]


def test_every_structure_runs():
    at = _fresh_app()
    for key in K.ORDER:
        at.selectbox(key="struct_select").set_value(key).run(timeout=TIMEOUT)
        assert not at.exception, (key, [str(e) for e in at.exception])
        assert _metrics(at)["Einordnung der Kontrolle"] in {"hilft", "schadet", "verstärkt", "neutral", "neutral, aber genauer", "neutral, aber ungenauer",
                                                           "rechnet teilweise heraus"}


def test_the_confounder_is_good_and_the_instrument_amplifies():
    at = _fresh_app()
    at.selectbox(key="struct_select").set_value("confounder").run(timeout=TIMEOUT)
    assert _metrics(at)["Einordnung der Kontrolle"] == "hilft"
    at.selectbox(key="struct_select").set_value("instrument_hidden").run(timeout=TIMEOUT)
    assert _metrics(at)["Einordnung der Kontrolle"] == "verstärkt"


def test_pdf_is_created_only_after_the_click():
    at = _fresh_app()
    assert "pdf_made" not in at.session_state
    at.button(key="pdf_make").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    settings, data = at.session_state["pdf_made"]
    assert data[:5] == b"%PDF-" and len(data) > 1000


def test_permalink_values_are_taken_and_invalid_ones_cleaned():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params["t"] = "collider"
    at.query_params["s"] = "5"
    at.query_params["tau"] = "-1"
    at.query_params["n"] = "999999"
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    assert at.selectbox(key="struct_select").value == "collider"
    assert at.slider(key="s_slider").value == C.S_MAX and at.slider(key="tau_slider").value == C.TAU_MIN and at.slider(key="n_slider").value == C.N_MAX


def test_unknown_structure_in_the_permalink_is_ignored():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params["t"] = "nirgendwo"
    at.query_params["seed"] = "abc"
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    assert at.selectbox(key="struct_select").value == "mediator" and at.number_input(key="seed_input").value == C.DEFAULT_SEED


def test_the_address_bar_mirrors_the_settings():
    at = _fresh_app()
    at.selectbox(key="struct_select").set_value("m_bias").run(timeout=TIMEOUT)
    assert at.query_params["t"] in ("m_bias", ["m_bias"])
