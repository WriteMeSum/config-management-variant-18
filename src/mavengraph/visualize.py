"""Текст D2, отображение SVG и ASCII-дерево с защитой от циклов."""

import json
import subprocess
import sys
import webbrowser
from pathlib import Path

from .config import AppError

RENDER_TIMEOUT_SECONDS = 60


def to_d2(graph):
    """Сформировать D2 с безопасными идентификаторами и подписями."""
    identifiers = {node: f"n{index}"
                   for index, node in enumerate(graph.adjacency)}
    lines = ["direction: down"]
    for node, identifier in identifiers.items():
        label = json.dumps(str(node), ensure_ascii=False)
        lines.append(f"{identifier}: {label}")
    root = identifiers[graph.root]
    lines.extend([f'{root}.style.fill: "#dbeafe"',
                  f'{root}.style.stroke: "#2563eb"'])
    for node, children in graph.adjacency.items():
        for child in children:
            lines.append(f"{identifiers[node]} -> {identifiers[child]}")
    return "\n".join(lines) + "\n"


def ascii_tree(graph):
    """Нарисовать дерево стеком; отметить циклы и повторные поддеревья."""
    lines = [str(graph.root)]
    expanded = {graph.root}
    stack = [(graph.root, "", iter(graph.adjacency[graph.root]))]
    active = {graph.root}
    while stack:
        node, prefix, children = stack[-1]
        child = next(children, None)
        if child is None:
            active.remove(node)
            stack.pop()
            continue
        last = child == graph.adjacency[node][-1]
        branch = "`-- " if last else "|-- "
        suffix = ""
        if child in active:
            suffix = " [cycle]"
        elif child in expanded:
            suffix = " [shared]"
        lines.append(prefix + branch + str(child) + suffix)
        if not suffix:
            expanded.add(child)
            active.add(child)
            next_prefix = prefix + ("    " if last else "|   ")
            stack.append((child, next_prefix,
                          iter(graph.adjacency[child])))
    return "\n".join(lines)


def render(graph, output):
    """Сохранить D2 и вызвать только визуализатор d2 для создания SVG."""
    source = Path(output).resolve().with_suffix(".d2")
    target = source.with_suffix(".svg")
    try:
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(to_d2(graph), encoding="utf-8")
        result = subprocess.run(
            ["d2", "--layout=dagre", str(source), str(target)],
            capture_output=True, text=True, timeout=RENDER_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as error:
        raise AppError(f"Установите D2 CLI. Исходник: {source}") from error
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AppError(f"Ошибка создания изображения: {error}") from error
    if result.returncode:
        raise AppError(f"D2: {result.stderr.strip()}")
    if not target.is_file():
        raise AppError("D2 не создал SVG")
    return source, target


def show_image(path):
    """Открыть SVG в Firefox на macOS либо в системном браузере."""
    try:
        if sys.platform == "darwin":
            result = subprocess.run(["open", "-a", "Firefox", str(path)],
                                    capture_output=True, timeout=10)
            opened = result.returncode == 0
        else:
            opened = webbrowser.open(path.as_uri())
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AppError(f"Не удалось открыть изображение: {path}") from error
    if not opened:
        raise AppError(f"Откройте изображение вручную: {path}")
