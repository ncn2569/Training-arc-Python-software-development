import copy
import unittest

from planner import release_order


class PlannerTests(unittest.TestCase):
    def test_order_is_stable_and_includes_implicit_leaf(self):
        graph = {"web": ["api", "assets"], "api": ["core"], "worker": ["core"]}
        self.assertEqual(release_order(graph), ["assets", "core", "api", "web", "worker"])

    def test_cycle_raises_without_mutating_graph(self):
        graph = {"a": ["b"], "b": ["a"]}
        before = copy.deepcopy(graph)
        with self.assertRaisesRegex(ValueError, "cycle"):
            release_order(graph)
        self.assertEqual(graph, before)


if __name__ == "__main__":
    unittest.main()
