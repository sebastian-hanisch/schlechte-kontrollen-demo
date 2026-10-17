# Schlechte Kontrollen: wo eine Variable im Diagramm sitzt – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-schlechte-kontrollen-demo.streamlit.app/)**

Viertes Stück der Linie **Kausale Diagramme und Adjustierung** in der „Konzepte“-Reihe im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine Learning). Nachfolger von [backdoor-demo](https://github.com/sebastian-hanisch/backdoor-demo): Dort stand, welche Mengen die Hintertüren schließen. Hier steht, welche Variablen man besser nicht aufnimmt, und warum „alles Verfügbare kontrollieren“ keine Regel ist.

## Kernfrage

Eine Variable festzuhalten kann die Schätzung verbessern, verschlechtern oder nur ihre Genauigkeit ändern; es hängt davon ab, **wo sie im Diagramm sitzt**. Zehn feste Mini-Diagramme zeigen je eine Stellung: Confounder, Präzisionsvariable, Instrument (mit und ohne verborgene Störung), Mediator, Collider, M-Bias und die Nachfahren von Collider, Wirkung und Mediator. Wie groß ist der Fehler, wie ändert sich der Standardfehler, wie groß ist der M-Bias wirklich, und welche Faustregel hält?

## Modell

- **Strukturen:** zehn Mini-Diagramme mit drei bis fünf Knoten, je eine festgehaltene Kontrolle. Behandlung x, Wirkung y; die Kontrolle ist die Variable, deren Stellung wechselt. Zwei Regler: Kantenstärke s (alle Pfeile außer der direkten Wirkung) und direkte Wirkung τ von x auf y.
- **Daten:** lineares Normalmodell mit Einheitsrauschen (Generator `kausal_generator.py`, wortgleich in allen Stücken der Linie). Die **wahre Wirkung** ist die Summe der Pfadprodukte.
- **Ohne/mit Kontrolle:** Der Koeffizient von x in der Regression von y auf x, einmal ohne und einmal mit der Kontrolle. Der **Fehler im Grenzfall** (n → ∞) kommt aus der Kovarianz, nicht aus der Stichprobe.

## Methodik

- **Population:** Σ = (I − B)⁻¹(I − B)⁻ᵀ, Gesamtwirkungen T = (I − B)⁻¹ − I; der Koeffizient aus Σ, der Standardfehler-Faktor aus den Restvarianzen.
- **Einordnung:** hilft, schadet, verstärkt, rechnet teilweise heraus, neutral (genauer / ungenauer) – aus dem Fehler mit und ohne Kontrolle und dem Standardfehler-Faktor.
- **Experimente** laufen über feste Zufallsströme (SplitMix64, ganzzahlig, plattformstabil).
- **Faustregeln** gegen das Backdoor-Kriterium (über `dsep_graph.py`) in Zufallsdiagrammen mit 7 Knoten und ein bis zwei unbeobachteten Vorfahren von x oder y.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`; Einstellung, wenn nicht anders genannt: Kantenstärke 0,6, direkte Wirkung 0,5, n = 500.

| Frage | Befund | Test |
|---|---|---|
| Standard-Stichprobe (Mediator, Seed 35) | Wahre Wirkung 0,86 (0,5 direkt + 0,6 · 0,6 über den Bestand). Ohne Kontrolle 0,92, mit dem Bestand 0,52; der Fehler im Grenzfall ist **−0,36**, das sind 42 % der Wirkung. | `test_default_sample_and_verdict` |
| Wann hilft Festhalten? | Nur beim Confounder: Fehler +0,26 ohne, 0 mit. Alle anderen neun Stellungen sind neutral oder verschlechtern die Schätzung. | `test_population_table_of_the_ten_structures` |
| Wie ändern Mediator und Collider die Schätzung? | Mediator: 0,86 → 0,50 (Fehler −0,36). Collider: 0 → −0,40. Die Deckung des 95-%-Intervalls fällt von rund 95 % auf **0 %**. | `test_population_table_of_the_ten_structures`, `test_zoo_coverage` |
| Wie ändert sich die Genauigkeit? | Präzisionsvariable: Standardfehler ×0,86, Instrument ohne Störung: ×1,17, Nachfahre der Wirkung: ×0,89; Fehler dabei 0 bzw. −0,13. | `test_standard_error_factors` |
| Nachfahren | Nachfahre des Colliders −0,13, der Wirkung −0,13, des Mediators −0,10; Deckung 98 → 18 %, 96 → 6 %, 93 → 53 %. | `test_zoo_coverage` |
| Wie groß ist der M-Bias? | Bei gleicher Kantenstärke **1 bis 36 %** des Confounding-Fehlers (s = 0,1 bis 0,9); bei s = 0,6 liegt er bei −0,06, die Deckung fällt von 94 auf 77 %. | `test_mbias_is_small`, `test_zoo_coverage` |
| Schmetterling (Collider, der zugleich Confounder ist) | In 20 000 Ziehungen mit Kantenstärken ±0,1 bis ±0,9 liegt Kontrollieren in **92 %** näher an der Wahrheit; der Fehler ist im Median das 0,11fache, in 4,1 % mehr als das Doppelte. | `test_butterfly` |
| Bias-Verstärkung | Instrument mit verborgener Störung: Fehler 0,21 ohne, 0,26 mit. Mit wachsender Stärke des Instruments (0 bis 1,8) wächst er auf das 1,00 / 1,07 / 1,26 / 1,60 / 2,06 / **3,38**fache. | `test_amplification` |
| Faustregeln (3 000 Zufallsdiagramme, in 2 493 gibt es eine gültige Menge) | „Alle beobachteten Variablen“ ist nur in **17 %** gültig (413), „alle Nicht-Nachfahren von x“ in 99,6 % (2 483), das Disjunktivkriterium in **100 %** (2 493), die leere Menge in 80 % (1 989). In den 507 Fällen ohne gültige Menge findet keine Regel eine. | `test_rules_experiment` |

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Man kennt die Stellung** | Die Einordnung folgt aus dem Diagramm. Ist ein Pfeil falsch eingezeichnet, kann aus einer „guten“ Kontrolle eine schädliche werden. | Wie falsch darf das Diagramm sein? |
| **Die Kontrolle ist fehlerfrei gemessen** | Die Demo misst jede Variable ohne Fehler. Ein verrauschter Confounder schließt die Hintertür nur zum Teil. | Sensitivität und Falsifikation |
| **Es gibt eine gültige Menge** | In 507 von 3 000 Zufallsdiagrammen existiert unter den beobachteten Variablen keine; keine Regel findet dort eine. | Frontdoor, Instrumente |
| **Alles ist linear** | Die Beträge sind exakte lineare Rechnung; bei Nichtlinearität bleiben die Stellungen, die Größen ändern sich. | Doppelt robust und Double ML |
| **Die Wahrheit ist die Gesamtwirkung** | Wer nur den direkten Weg wissen will, braucht den Mediator; „schadet“ gilt nur für die Gesamtwirkung. | Frontdoor |
| **Mehr Genauigkeit ist ein Gewinn** | Standardfehler sind asymptotisch; bei kleinem n und starker Kollinearität weichen sie ab. | Welche Menge? |

Die Zahlen gelten für diese erfundene Welt und für Zufallsdiagramme dieser Generatorfamilie (7 Knoten, Kantenwahrscheinlichkeit 0,25 bis 0,5); „Wahrheit“ ist das simulierte Modell, nicht ein Befund über echte Standorte. Das Disjunktivkriterium ist aus dem Gedächtnis umgesetzt, die Quelle nicht geprüft.

## Bezug zu den Nachbarn im Portfolio

- [backdoor-demo](https://github.com/sebastian-hanisch/backdoor-demo): liefert Kriterium und Adjustierungsformel; die Faustregel „alle anderen Variablen“ ist dort nur in 14 % der Diagramme gültig, hier steht das Warum je Stellung.
- [d-separation-demo](https://github.com/sebastian-hanisch/d-separation-demo): liefert Pfade und Blockierungsgründe; `dsep_graph.py` ist wortgleich übernommen.
- [konfundierung-demo](https://github.com/sebastian-hanisch/konfundierung-demo): zeigt, dass der naive Vergleich daneben liegt und die Schwankung als Kontrolle hilft.

## Tests

Mini-Instanzen von Hand (Confounder, Mediator, Collider, M-Bias, Instrument mit Störung 1/3 → 1/2, Nachfahre der Wirkung 1 → 1/2, Standardfehler-Faktoren), Bias-Verstärkung gegen die geschlossene Form, Backdoor-Prüfung gegen die Graphenchirurgie (`networkx`) auf 200 Zufallsdiagrammen, Population gegen eine Stichprobe mit n = 200 000, Auswertung, jede README-Zahl in `test_claims.py`, AppTest (Presets, jede Struktur, Regler, Permalink, PDF), Footer und Laufzeit-Importe.

```bash
python -m pytest tests -q
```

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `kausal_generator.py` | gemeinsamer Generator der Linie (SplitMix64, Strukturmodell, Wirkung) |
| `dsep_graph.py` | d-Separation, Pfade, Aussagenmengen (wortgleich aus d-separation-demo) |
| `skt_catalog.py` | die zehn Mini-Diagramme |
| `skt_effects.py` | Population, Fehler, Standardfehler-Faktor, Einordnung |
| `skt_rules.py` | Backdoor-Prüfung, Zufallsdiagramme, Faustregeln, Experiment |
| `skt_evaluation.py` | Stichprobe, Experimente, Verdikte |
| `skt_visualization.py`, `skt_pdf_export.py` | Figuren, Tabellen, PDF |
| `skt_constants.py`, `skt_presets.py` | Regler, Experimente, Presets, Permalink |
| `tests/` | Mini-Instanzen, Orakel, Claims, App |

## Bewusst nicht umgesetzt

- **Messfehler in der Kontrolle:** eigene Stellung mit eigenem Mechanismus; hier ist jede Variable exakt gemessen.
- **Die Menge wählen:** unter mehreren gültigen Mengen die genaueste ist Stück 5 der Linie; hier steht nur die einzelne Kontrolle.
- **Frontdoor und Instrumente als Schätzer:** eigene Stücke; hier erscheint das Instrument nur als Kontrolle.
- **Nichtlineare Modelle, Zeitreihen, Praxisdaten:** nicht gebaut; alle Zahlen sind erzeugt.

## Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit Cloud: Python 3.12.

Gebaut mit Streamlit, Plotly, numpy, pandas und fpdf2.

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Kausale Diagramme: von Konfundierung bis Wahl](https://sebastianhanisch.net/konzepte-kausale-diagramme.html).
