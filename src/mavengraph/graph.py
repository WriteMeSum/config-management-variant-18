"""Итеративный DFS с обнаружением обратных ребер и исключениями."""

from dataclasses import dataclass, field
from fnmatch import fnmatchcase

from .repository import MavenRepository, root_artifact
from .test_repository import TestRepository


@dataclass
class Graph:
    """Граф: уникальные узлы, ребра и обнаруженные обратные ребра."""

    root: object
    adjacency: dict = field(default_factory=dict)
    cycles: list = field(default_factory=list)


def is_excluded(artifact, excluded):
    """Сопоставить group:artifact, включая Maven wildcard *."""
    return any(fnmatchcase(artifact.key, pattern) for pattern in excluded)


class MavenEdges:
    """Адаптер POM к обходу с контекстом исключений на пути."""

    def __init__(self, repository):
        """Сохранить загрузчик POM."""
        self.repository = repository

    def edges(self, node, excluded, is_root):
        """Пропустить optional транзитивно и применить exclusions пути."""
        result = []
        for dep in self.repository.dependencies(node):
            if dep.optional and not is_root:
                continue
            if not is_excluded(dep.artifact, excluded):
                result.append((dep.artifact, excluded | dep.exclusions))
        return result


def build_graph(root, provider):
    """Обойти стеком DFS; каждое состояние (узел, exclusions) один раз."""
    graph = Graph(root, {root: []})
    initial = (root, frozenset())
    visited = {initial}
    active = {root}
    stack = [(root, iter(provider.edges(root, initial[1], True)))]
    while stack:
        node, children = stack[-1]
        item = next(children, None)
        if item is None:
            active.remove(node)
            stack.pop()
            continue
        child, excluded = item
        graph.adjacency.setdefault(child, [])
        if child not in graph.adjacency[node]:
            graph.adjacency[node].append(child)
        if child in active:
            graph.cycles.append((node, child))
            continue
        state = (child, excluded)
        if state not in visited:
            visited.add(state)
            active.add(child)
            edges = provider.edges(child, excluded, False)
            stack.append((child, iter(edges)))
    return graph


def configured_graph(config):
    """Выбрать файловый либо настоящий Maven-репозиторий."""
    if config.test_mode:
        return build_graph(config.package, TestRepository(config.repository))
    root = root_artifact(config)
    provider = MavenEdges(MavenRepository(config.repository))
    return build_graph(root, provider)


def edge_lines(graph):
    """Вывести ребра, включая отдельную строку для изолированного корня."""
    if not graph.adjacency[graph.root]:
        return [str(graph.root)]
    return [f"{node} -> {child}"
            for node, children in graph.adjacency.items() for child in children]
