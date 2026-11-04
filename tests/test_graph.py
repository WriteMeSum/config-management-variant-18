"""Проверки DFS: глубина, общие узлы, циклы и исключения."""

import unittest

from mavengraph.graph import MavenEdges, build_graph
from mavengraph.model import Artifact, Dependency


class MemoryRepository:
    """Минимальный поставщик для проверки алгоритма без файлов и сети."""

    def __init__(self, graph):
        """Сохранить таблицу смежности."""
        self.graph = graph
        self.calls = []

    def edges(self, node, excluded, is_root):
        """Вернуть детей в исходном порядке."""
        self.calls.append(node)
        return [(child, excluded) for child in self.graph[node]]


class GraphTests(unittest.TestCase):
    """Транзитивность, циклы и отсутствие рекурсии."""

    def test_diamond_visits_shared_once(self):
        """Общий узел обходится один раз, оба ребра сохраняются."""
        provider = MemoryRepository({"A": ["B", "C"], "B": ["D"],
                                     "C": ["D"], "D": []})
        graph = build_graph("A", provider)
        self.assertEqual(provider.calls, ["A", "B", "D", "C"])
        self.assertEqual(graph.adjacency["C"], ["D"])
        self.assertFalse(graph.cycles)

    def test_cycles(self):
        """Обратное ребро и петля не приводят к бесконечному обходу."""
        for adjacency, expected in (({"A": ["A"]}, ("A", "A")),
                                    ({"A": ["B"], "B": ["A"]},
                                     ("B", "A"))):
            with self.subTest(adjacency=adjacency):
                graph = build_graph("A", MemoryRepository(adjacency))
                self.assertEqual(graph.cycles, [expected])

    def test_deep_chain(self):
        """Цепочка глубже стандартного лимита рекурсии обрабатывается."""
        count = 1500
        adjacency = {i: [i + 1] for i in range(count)}
        adjacency[count] = []
        graph = build_graph(0, MemoryRepository(adjacency))
        self.assertEqual(len(graph.adjacency), count + 1)

    def test_optional_and_wildcard_exclusion(self):
        """Адаптер исключает optional транзитивно и wildcard."""
        class Repository:
            """POM-заглушка с одним optional ребром."""

            def dependencies(self, node):
                """Вернуть фиксированное ребро."""
                return [Dependency(Artifact("g", "b", "1"),
                                   optional=True)]

        provider = MavenEdges(Repository())
        artifact = Artifact("g", "a", "1")
        self.assertEqual(provider.edges(artifact, frozenset(), False), [])
        self.assertTrue(provider.edges(artifact, frozenset(), True))
        self.assertEqual(provider.edges(artifact, frozenset({"g:*"}), True),
                         [])
