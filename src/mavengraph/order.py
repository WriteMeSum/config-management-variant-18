"""Порядок загрузки: зависимости раньше зависимых, без рекурсии."""

from .config import AppError


def loading_order(graph):
    """Вычислить DFS postorder; при цикле топологический порядок невозможен."""
    result = []
    visited = {graph.root}
    active = {graph.root}
    stack = [(graph.root, iter(graph.adjacency[graph.root]))]
    while stack:
        node, children = stack[-1]
        child = next(children, None)
        if child is None:
            active.remove(node)
            result.append(node)
            stack.pop()
        elif child in active:
            raise AppError(f"Порядок загрузки невозможен: цикл {node} -> "
                           f"{child}")
        elif child not in visited:
            visited.add(child)
            active.add(child)
            stack.append((child, iter(graph.adjacency[child])))
    return result
