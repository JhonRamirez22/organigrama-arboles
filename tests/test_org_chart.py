"""Pruebas del árbol del organigrama. Ejecutar con: python3 -m unittest discover -s tests -v"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from organigrama import OrgChart  # noqa: E402


def build_chart():
    """Organigrama pequeño para las pruebas:

        A (director)
        ├── B
        │   ├── D
        │   └── E
        └── C
            └── F
    """
    chart = OrgChart()
    chart.add("A", "Ana", "Directora", "Dirección", 1000)
    chart.add("B", "Beto", "Gerente", "Ventas", 500, "A")
    chart.add("C", "Carla", "Gerente", "TI", 400, "A")
    chart.add("D", "Dani", "Analista", "Ventas", 200, "B")
    chart.add("E", "Elena", "Analista", "Ventas", 300, "B")
    chart.add("F", "Felipe", "Dev", "TI", 250, "C")
    return chart


class AddTests(unittest.TestCase):

    def test_root_and_children_are_linked(self):
        chart = build_chart()
        self.assertIs(chart.root, chart.get("A"))
        self.assertIs(chart.get("D").manager, chart.get("B"))
        self.assertIn(chart.get("D"), chart.get("B").reports)

    def test_duplicate_id_is_rejected(self):
        chart = build_chart()
        with self.assertRaises(ValueError):
            chart.add("D", "Otra", "x", "x", 1, "B")

    def test_second_root_is_rejected(self):
        chart = build_chart()
        with self.assertRaises(ValueError):
            chart.add("Z", "Zoe", "x", "x", 1)

    def test_unknown_manager_is_rejected(self):
        chart = build_chart()
        with self.assertRaises(KeyError):
            chart.add("Z", "Zoe", "x", "x", 1, "NOPE")

    def test_negative_salary_is_rejected(self):
        chart = build_chart()
        with self.assertRaises(ValueError):
            chart.add("Z", "Zoe", "x", "x", -1, "A")


class MoveTests(unittest.TestCase):

    def test_move_carries_the_whole_team(self):
        chart = build_chart()
        chart.move("B", "C")
        self.assertIs(chart.get("B").manager, chart.get("C"))
        self.assertNotIn(chart.get("B"), chart.get("A").reports)
        self.assertEqual(chart.depth("D"), 3)

    def test_move_under_own_descendant_is_a_cycle(self):
        chart = build_chart()
        with self.assertRaises(ValueError):
            chart.move("B", "D")

    def test_move_under_itself_is_a_cycle(self):
        chart = build_chart()
        with self.assertRaises(ValueError):
            chart.move("B", "B")

    def test_root_cannot_be_moved(self):
        chart = build_chart()
        with self.assertRaises(ValueError):
            chart.move("A", "B")


class RemoveTests(unittest.TestCase):

    def test_reports_move_up_to_the_manager(self):
        chart = build_chart()
        chart.remove("B")
        self.assertNotIn("B", chart)
        self.assertIs(chart.get("D").manager, chart.root)
        self.assertIn(chart.get("E"), chart.root.reports)

    def test_root_with_reports_cannot_be_removed(self):
        chart = build_chart()
        with self.assertRaises(ValueError):
            chart.remove("A")

    def test_leaf_root_can_be_removed_and_chart_restarted(self):
        chart = OrgChart()
        chart.add("A", "Ana", "Directora", "Dirección", 1000)
        chart.remove("A")
        self.assertIsNone(chart.root)
        chart.add("N", "Nuevo", "Director", "Dirección", 900)
        self.assertIs(chart.root, chart.get("N"))


class QueryTests(unittest.TestCase):

    def test_chain_of_command_goes_up_to_root(self):
        chart = build_chart()
        ids = [e.id for e in chart.chain_of_command("D")]
        self.assertEqual(ids, ["D", "B", "A"])

    def test_lowest_common_ancestor(self):
        chart = build_chart()
        self.assertEqual(chart.lowest_common_ancestor("D", "E").id, "B")
        self.assertEqual(chart.lowest_common_ancestor("D", "F").id, "A")
        self.assertEqual(chart.lowest_common_ancestor("B", "D").id, "B")

    def test_reports_of_returns_all_descendants(self):
        chart = build_chart()
        self.assertEqual({e.id for e in chart.reports_of("A")}, {"B", "C", "D", "E", "F"})
        self.assertEqual(chart.reports_of("D"), [])

    def test_team_budget_sums_the_subtree(self):
        chart = build_chart()
        self.assertEqual(chart.team_budget("B"), 500 + 200 + 300)
        self.assertEqual(chart.team_budget("A"), 1000 + 500 + 400 + 200 + 300 + 250)

    def test_levels_order_is_breadth_first(self):
        chart = build_chart()
        self.assertEqual([e.id for e in chart.levels_order()], ["A", "B", "C", "D", "E", "F"])

    def test_height_and_depth(self):
        chart = build_chart()
        self.assertEqual(chart.height(), 3)
        self.assertEqual(chart.depth("A"), 0)
        self.assertEqual(chart.depth("F"), 2)

    def test_search_matches_name_role_or_area(self):
        chart = build_chart()
        self.assertEqual({e.id for e in chart.search("ventas")}, {"B", "D", "E"})
        self.assertEqual([e.id for e in chart.search("felipe")], ["F"])
        self.assertEqual(chart.search("   "), [])

    def test_budget_by_area(self):
        chart = build_chart()
        totals = chart.budget_by_area()
        self.assertEqual(totals["Ventas"], 500 + 200 + 300)
        self.assertEqual(totals["TI"], 400 + 250)


class PersistenceTests(unittest.TestCase):

    def test_save_and_load_round_trip(self):
        chart = build_chart()
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "chart.json")
            chart.save(ruta)
            loaded = OrgChart.load(ruta)
        self.assertEqual(len(loaded), len(chart))
        self.assertEqual(loaded.depth("D"), chart.depth("D"))
        self.assertEqual(loaded.team_budget("A"), chart.team_budget("A"))

    def test_seed_file_loads(self):
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "organigrama.json")
        chart = OrgChart.load(ruta)
        self.assertEqual(len(chart), 15)
        self.assertEqual(chart.height(), 4)


if __name__ == "__main__":
    unittest.main()
