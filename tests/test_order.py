"""Проверки топологического порядка и отказа при циклах."""

import unittest

from mavengraph.config import AppError
from mavengraph.graph import Graph
from mavengraph.order import loading_order


class OrderTests(unittest.TestCase):
    """Проверяется смысл порядка: каждое ребро направлено назад."""

    def test_diamond_order(self):
        """Общая зависимость единственна и загружается раньше родителей."""
        graph = Graph("A", {"A": ["B", "C"], "B": ["D"],
                            "C": ["D"], "D": []})
        order = loading_order(graph)
        self.assertEqual(order, ["D", "B", "C", "A"])
        for source, children in graph.adjacency.items():
            for child in children:
                self.assertLess(order.index(child), order.index(source))

    def test_cycle_has_no_order(self):
        """Нельзя печатать ложный порядок при цикле."""
        for adjacency in ({"A": ["A"]}, {"A": ["B"], "B": ["A"]}):
            with self.assertRaises(AppError):
                loading_order(Graph("A", adjacency))

    def test_isolated(self):
        """Изолированный корень имеет единственный допустимый порядок."""
        self.assertEqual(loading_order(Graph("A", {"A": []})), ["A"])

    def test_deep_order(self):
        """Сам порядок также вычисляется без рекурсии."""
        count = 1500
        adjacency = {i: [i + 1] for i in range(count)}
        adjacency[count] = []
        self.assertEqual(loading_order(Graph(0, adjacency)),
                         list(reversed(range(count + 1))))
