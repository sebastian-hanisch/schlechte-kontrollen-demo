"""Schlechte Kontrollen: wo eine Variable im Diagramm sitzt - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Viertes Stück der Linie Kausale Diagramme und Adjustierung. Zehn feste Mini-Diagramme zeigen, was das Festhalten einer Variable je nach ihrer Stellung bewirkt.
Kern: skt_effects.py, skt_rules.py; Generator: kausal_generator.py, Graph: dsep_graph.py (wortgleich aus den Vorgängerstücken).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import skt_catalog as K
import skt_constants as C
from skt_evaluation import (
    Settings,
    amplification_experiment,
    analyse,
    butterfly_experiment,
    de,
    mbias_experiment,
    signed,
    verdict_amplification,
    verdict_instance,
    verdict_mbias,
    verdict_rules,
    verdict_zoo,
    zoo_experiment,
)
from skt_pdf_export import build_pdf
from skt_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from skt_rules import RULE_NAMES, rules_experiment
from skt_visualization import (
    build_amplification_chart,
    build_diagram,
    build_estimates,
    build_mbias_chart,
    build_rules_chart,
    build_zoo_chart,
    build_zoo_table,
    style_zoo_table,
)

st.set_page_config(page_title="Schlechte Kontrollen – Sebastian Hanisch", layout="wide")

SPINNER = "Experiment rechnet über feste Zufallsströme …"


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=SPINNER)
def _zoo():
    return zoo_experiment()


@st.cache_data(show_spinner=SPINNER)
def _mbias():
    return mbias_experiment(), butterfly_experiment()


@st.cache_data(show_spinner=SPINNER)
def _amplification():
    return amplification_experiment()


@st.cache_data(show_spinner=SPINNER)
def _rules():
    return rules_experiment()


def verdict(kind_text):
    kind, text = kind_text
    getattr(st, kind)(text)


st.title("🧯 Schlechte Kontrollen: wo eine Variable im Diagramm sitzt")
st.markdown(
    """
**Mehr Variablen festzuhalten ist nicht besser, sondern es kommt darauf an, wo sie im Diagramm sitzen.** Dies ist das vierte Stück der Linie **Kausale Diagramme und
Adjustierung**. Das dritte Stück hat gezeigt, welche Mengen die Hintertüren schließen; hier geht es um die Variablen, die man besser **nicht** aufnimmt. Zehn kleine Diagramme
zeigen je eine Stellung: Was verzerrt das Festhalten, was ändert es an der Genauigkeit, und was sagt die Faustregel „alles Verfügbare kontrollieren“ dazu?

Weiter unten: vier Experimente (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So liest man die Stellung", expanded=True):
    st.markdown(
        """
1. **Davor, auf dem Rückweg.** Ist die Variable gemeinsame Ursache von Faktor und Wirkung, schließt das Festhalten die Hintertür. Das ist die gute Kontrolle.
2. **Mitten auf dem Weg.** Ein Mediator trägt einen Teil der Wirkung. Wer ihn festhält, schätzt nur den direkten Weg und lässt den Umweg weg.
3. **Dahinter.** Folgen des Faktors, der Wirkung oder beider (Collider) tragen Information von dort zurück. Festhalten öffnet Pfade, die sonst blockiert wären.
4. **Daneben.** Eine Variable, die nur die Wirkung bewegt, macht die Schätzung genauer; eine, die nur den Faktor bewegt, macht sie ungenauer; mit verborgener Störung kann
   sie die Verzerrung verstärken.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
cols = st.columns(len(C.PRESETS))
for col, name in zip(cols, C.PRESETS):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Stellung der Kontrolle**")
    key = st.selectbox("Struktur", list(K.ORDER), key="struct_select", format_func=lambda k: K.STRUCTURES[k].label,
                       help="Zehn feste Mini-Diagramme. Gezeichnet ist, welche Variable man festhält und wo sie sitzt.")
    st.markdown("**Stärken**")
    s = st.slider("Kantenstärke s", *bounds("s_slider"), step=C.S_STEP, key="s_slider", help="Stärke aller Pfeile außer der direkten Wirkung (Einheitsrauschen).")
    tau = st.slider("Direkte Wirkung τ von x auf y", *bounds("tau_slider"), step=C.TAU_STEP, key="tau_slider",
                    help="Die direkte Wirkung. Bei Mediator-Strukturen kommt der Umweg über die Kontrolle hinzu.")
    st.markdown("**Daten**")
    n = st.slider("Beobachtungen n", *bounds("n_slider"), step=C.N_STEP, key="n_slider", help="Stichprobengröße der simulierten Daten.")
    seed = st.number_input("Zufalls-Seed der Stichprobe", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Stichprobe würfeln", width="stretch", on_click=randomize_seed)

sync_query_params({"struct_select": key, "s_slider": round(float(s), 1), "tau_slider": round(float(tau), 1), "n_slider": int(n), "seed_input": int(seed)})

settings = Settings(key, round(float(s), 1), round(float(tau), 1), int(n), int(seed))
a = _analysis(settings)
fx = a.effects

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
(c1, c2), (c3, c4) = st.columns(2), st.columns(2)
c1.metric("Einordnung der Kontrolle", fx.kind, help="Was das Festhalten dieser Variable im Grenzfall (n → ∞) bewirkt.")
c2.metric("Wahre Wirkung von x", signed(fx.truth, 3), delta="aus dem Diagramm, nicht aus den Daten", delta_color="off")
c3.metric("Fehler ohne / mit Kontrolle (Grenzfall)", f"{signed(fx.bias_without, 2)} / {signed(fx.bias_with, 2)}", delta="bleibender Fehler bei n → ∞", delta_color="off",
          help="Der Koeffizient der Population minus die wahre Wirkung, einmal ohne und einmal mit der Kontrolle.")
c4.metric("Standardfehler mit / ohne", f"×{de(fx.se_factor, 2)}", delta="Genauigkeit der Schätzung", delta_color="off",
          help="Verhältnis der asymptotischen Standardfehler. Unter 1: genauer; über 1: ungenauer.")

left, right = st.columns([1.1, 1])
with left:
    st.plotly_chart(build_diagram(a), width="stretch", key="diagram_chart")
    st.caption("Dicker schwarzer Rand: Behandlung und Wirkung. Blau: die festgehaltene Kontrolle. Grauer Knoten: unbeobachtet. An den Pfeilen steht der Koeffizient.")
with right:
    st.plotly_chart(build_estimates(a), width="stretch", key="estimates_chart")
    st.caption(f"Schätzung aus {settings.n} simulierten Beobachtungen mit 95-%-Intervall. Orange Linie: wahre Wirkung. "
               f"Das Intervall ohne Kontrolle {'deckt' if a.covers_without else 'verfehlt'} die Wahrheit, mit Kontrolle {'deckt' if a.covers_with else 'verfehlt'} es sie.")
verdict(verdict_instance(a))
st.caption(K.STRUCTURES[key].why)

if st.button("📄 PDF der aktuellen Auswertung erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, build_pdf(a))
made = st.session_state.get("pdf_made")
if made and made[0] == settings:
    st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="schlechte-kontrollen.pdf", mime="application/pdf", key="pdf_download")

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Alle zehn Stellungen nebeneinander")
rows1 = _zoo()
st.caption(f"Je Struktur {C.EXP_ZOO_REPS} feste Wiederholungen mit n = {C.EXP_ZOO_N}, Kantenstärke {de(C.DEFAULT_S, 1)} und direkter Wirkung {de(C.DEFAULT_TAU, 1)}. "
           "Gezeigt ist, wie oft das 95-%-Intervall die wahre Wirkung deckt, ohne und mit der Kontrolle.")
st.plotly_chart(build_zoo_chart(rows1), width="stretch", key="zoo_chart")
verdict(verdict_zoo(rows1))
st.dataframe(style_zoo_table(build_zoo_table(rows1)), hide_index=True, width="stretch")
st.caption("„Fehler“ ist der Koeffizient im Grenzfall minus die wahre Wirkung. Standardfehler mit / ohne: unter 1 ist genauer.")

st.subheader("🔬 Experiment 2: Wie groß ist der M-Bias wirklich?")
rows2, butterfly = _mbias()
draws = f"{butterfly['draws']:,}".replace(",", ".")
st.caption("Oben die M-Struktur gegen den Confounding-Fehler bei gleicher Kantenstärke; darunter der Schmetterling (Collider, der zugleich Confounder ist) mit "
           f"{draws} zufälligen Kantenstärken ±0,1 bis ±0,9.")
st.plotly_chart(build_mbias_chart(rows2), width="stretch", key="mbias_chart")
verdict(verdict_mbias(rows2, butterfly))
st.caption(f"Im Schmetterling ist der Fehler mit Kontrolle im Median {de(butterfly['median_ratio'], 2)}-mal so groß wie ohne; in {de(100 * butterfly['share_double'], 1)} % der "
           "Ziehungen ist er mehr als doppelt so groß. Das gilt für diese Verteilung der Kantenstärken; sind die Kanten in den Collider stark und die aus ihm heraus schwach, liegt Kontrollieren deutlich seltener näher.")

st.subheader("🔬 Experiment 3: Wenn das Instrument die Verzerrung verstärkt")
rows3 = _amplification()
st.caption("Standortqualität U bewegt Faktor und Servicegrad (verborgen); das Instrument I bewegt nur den Faktor. Je stärker das Instrument, desto mehr verschlechtert das Mitführen den Fehler gegenüber dem Weglassen.")
st.plotly_chart(build_amplification_chart(rows3), width="stretch", key="amplification_chart")
verdict(verdict_amplification(rows3))
st.dataframe([{"Stärke des Instruments": de(r["a"], 1), "Fehler ohne": signed(r["without"], 3), "Fehler mit": signed(r["with"], 3), "Faktor": de(r["factor"], 2)}
              for r in rows3], hide_index=True, width="stretch")

st.subheader("🔬 Experiment 4: Welche Faustregel hält?")
res4 = _rules()
st.caption(f"{res4['cases']} zufällige Diagramme mit {C.RULES_NODES} Knoten und ein bis zwei unbeobachteten Vorfahren von x oder y. Gezählt wird, wie oft die Menge, die "
           "die Regel liefert, die Wirkung trifft (Backdoor-Kriterium).")
st.plotly_chart(build_rules_chart(res4), width="stretch", key="rules_chart")
verdict(verdict_rules(res4))
st.dataframe([{"Regel": name, "gültig": f"{res4['counts'][(name, True)][1]} von {res4['counts'][(name, True)][0]}",
               "Anteil": f"{de(100 * res4['counts'][(name, True)][1] / max(res4['counts'][(name, True)][0], 1), 1)} %"} for name in RULE_NAMES],
             hide_index=True, width="stretch")
st.caption("Das Disjunktivkriterium (VanderWeele und Shpitser) nimmt jede beobachtete Variable auf, die Faktor, Wirkung oder beide verursacht. Es ist hier nur "
           "gültig, wo überhaupt eine gültige Menge unter den beobachteten Variablen existiert; seine Quelle ist aus dem Gedächtnis, nicht geprüft.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
no_valid_hint = res4["cases"] - res4["exists"]
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Man kennt die Stellung** | Die Einordnung folgt aus dem Diagramm. Ist ein Pfeil falsch eingezeichnet, kann aus einer „guten“ Kontrolle eine schädliche werden. | Wie falsch darf das Diagramm sein? |
| **Die Kontrolle ist fehlerfrei gemessen** | Die Demo misst jede Variable ohne Fehler. Ein verrauschter Confounder schließt die Hintertür nur zum Teil. | Sensitivität und Falsifikation |
| **Es gibt eine gültige Menge** | In {no_valid_hint} von {res4['cases']} Diagrammen existiert unter den beobachteten Variablen keine; keine der Regeln findet dort eine. | Frontdoor, Instrumente |
| **Alles ist linear** | Die Beträge sind exakte lineare Rechnung. Bei nichtlinearen Zusammenhängen bleiben die Stellungen gleich, die Größen nicht. | Doppelt robust und Double ML |
| **Die Wahrheit ist die Gesamtwirkung** | Wer nur den direkten Weg wissen will, braucht den Mediator; die Einordnung „schadet“ gilt nur für die Gesamtwirkung. | Frontdoor |
| **Mehr Genauigkeit ist ein Gewinn** | Standardfehler sind asymptotisch; bei kleinem n und starker Kollinearität weichen sie ab. | Welche Menge? |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Ein linearer Graph $V = BV + \varepsilon$ mit Einheitsrauschen, $\Sigma = (I-B)^{-1}(I-B)^{-\top}$, Gesamtwirkungen $T = (I-B)^{-1} - I$. Die **wahre
Wirkung** von $x$ auf $y$ ist $T_{yx}$.

**Koeffizient im Grenzfall.** Der Koeffizient von $x$ in $y \sim x + Z$ ist
$$\beta_{yx\cdot Z} = \frac{\Sigma_{yx} - \Sigma_{yZ}\Sigma_{ZZ}^{-1}\Sigma_{Zx}}{\Sigma_{xx} - \Sigma_{xZ}\Sigma_{ZZ}^{-1}\Sigma_{Zx}}.$$
Der **Fehler** ist $\beta_{yx\cdot Z} - T_{yx}$; die Demo rechnet ihn exakt aus $\Sigma$, nicht aus der Stichprobe.

**Stellung.** Confounder: $Z \leftarrow \cdot \rightarrow$ beide, Festhalten blockiert den Rückweg. Mediator: $Z$ auf dem kausalen Pfad, Festhalten entfernt dessen Beitrag.
Collider: $Z \leftarrow x$ und $Z \leftarrow y$, Festhalten öffnet $x \leftrightarrow y$ (Berkson). M-Bias: $Z$ ist Collider verborgener Ursachen von $x$ und $y$.

**Bias-Verstärkung.** Mit einem Instrument $I \to x$ und einer verborgenen Störung $U \to x, y$ hat der Fehler ohne $I$ den Betrag $b$; mit $I$ in der Regression wächst er auf
$b/(1-R^2)$, wobei $R^2$ der Anteil der Varianz von $x$ ist, den $I$ erklärt.

**Disjunktivkriterium** (VanderWeele und Shpitser 2011). Die Demo nimmt jede beobachtete Variable auf, die $x$, $y$ oder beide verursacht und kein Nachfahre von $x$
ist. Das Kriterium garantiert eine gültige Menge, wenn es überhaupt eine unter den beobachteten Variablen gibt.

**Literatur.** J. Pearl, *Causality*, 2009; I. Shpitser, T. VanderWeele, J. Robins, *On the validity of covariate adjustment*, UAI 2010; T. VanderWeele, I. Shpitser,
*A new criterion for confounder selection*, Biometrics 67, 2011; J. Pearl, *On a class of bias-amplifying variables that endanger effect estimates*, UAI 2010; P. Ding und
L. Miratrix, *To adjust or not to adjust?*, Journal of Causal Inference 3, 2015 (alle aus dem Gedächtnis, nicht geprüft).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Kausale Diagramme: von Konfundierung bis Wahl](https://sebastianhanisch.net/konzepte-kausale-diagramme.html)."
)
