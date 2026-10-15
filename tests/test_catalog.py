"""Katalog: zehn Strukturen, Aufbau und Rollen."""

import skt_catalog as K


def test_ten_structures_in_order():
    assert len(K.ORDER) == 10 and set(K.ORDER) == set(K.STRUCTURES)
    assert len({s.label for s in K.STRUCTURES.values()}) == 10


def test_every_structure_is_well_formed():
    for key, st in K.STRUCTURES.items():
        n = len(st.nodes)
        assert st.key == key and st.why.endswith(".")
        assert len(st.pos) == n and all(0 <= px <= 1 and 0 <= py <= 1 for px, py in st.pos)
        assert all(p < c for p, c, _ in st.edges), key                        # topologische Reihenfolge
        assert len({st.x, st.y, st.control}) == 3 and all(0 <= v < n for v in (st.x, st.y, st.control))
        assert st.x not in st.hidden and st.y not in st.hidden and st.control not in st.hidden
        assert len(set(st.edges)) == len(st.edges)
        assert {kind for _, _, kind in st.edges} <= {"s", "tau"}
        assert sum(kind == "tau" for _, _, kind in st.edges) == 1, key         # genau eine direkte Wirkung


def test_the_direct_edge_connects_x_and_y_except_for_the_collider_family():
    for key, st in K.STRUCTURES.items():
        (p, c, _), = [e for e in st.edges if e[2] == "tau"]
        assert (p, c) == (st.x, st.y), key


def test_coefficient():
    assert K.coefficient("s", 0.3, 0.8) == 0.3 and K.coefficient("tau", 0.3, 0.8) == 0.8


def test_hidden_nodes_exist_exactly_where_the_story_needs_them():
    assert {k: st.hidden for k, st in K.STRUCTURES.items() if st.hidden} == {"instrument_hidden": (0,), "m_bias": (0, 1)}
