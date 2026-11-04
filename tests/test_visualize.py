"""Проверки представлений и отказов внешнего рендера."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mavengraph.config import AppError
from mavengraph.graph import Graph
from mavengraph.visualize import ascii_tree, render, to_d2


class VisualizationTests(unittest.TestCase):
    """Общие узлы, циклы, изолированные узлы и ошибки D2."""

    def test_d2_escapes_labels_and_preserves_edges(self):
        """Координаты и кавычки не превращаются в синтаксис D2."""
        root = 'g:a:1"quoted'
        graph = Graph(root, {root: ["B"], "B": [root]})
        source = to_d2(graph)
        self.assertIn('n0: "g:a:1\\"quoted"', source)
        self.assertIn("n0 -> n1", source)
        self.assertIn("n1 -> n0", source)

    def test_isolated_d2(self):
        """Пакет без зависимостей остается видимым узлом."""
        self.assertIn('n0: "A"', to_d2(Graph("A", {"A": []})))

    def test_ascii_shared_and_cycle(self):
        """Дерево не разрастается повторно и останавливается на циклах."""
        graph = Graph("A", {"A": ["B", "C"], "B": ["D"],
                            "C": ["D"], "D": ["A"]})
        tree = ascii_tree(graph)
        self.assertIn("A [cycle]", tree)
        self.assertIn("D [shared]", tree)
        self.assertTrue(tree.startswith("A\n|-- B"))

    def test_render_failures_are_readable(self):
        """Нет D2, ошибка D2 и таймаут преобразуются в AppError."""
        graph = Graph("A", {"A": []})
        errors = [FileNotFoundError(),
                  subprocess.TimeoutExpired("d2", 60)]
        with tempfile.TemporaryDirectory() as temp:
            for error in errors:
                with patch("mavengraph.visualize.subprocess.run",
                           side_effect=error), self.assertRaises(AppError):
                    render(graph, Path(temp) / "graph")
            result = subprocess.CompletedProcess([], 1, "", "bad diagram")
            with patch("mavengraph.visualize.subprocess.run",
                       return_value=result), self.assertRaises(AppError):
                render(graph, Path(temp) / "graph")
