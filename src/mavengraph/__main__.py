"""CLI для пяти этапов практической работы."""

import argparse
import sys
from dataclasses import asdict

from .config import AppError, load_config
from .graph import configured_graph, edge_lines
from .order import loading_order
from .repository import MavenRepository, root_artifact
from .test_repository import TestRepository
from .visualize import ascii_tree, render, show_image


class Stage:
    """Номера демонстрационных этапов задания."""

    config = 1
    direct = 2
    graph = 3
    order = 4
    visualize = 5


def arguments(argv):
    """Прочитать конфигурацию и операционные флаги CLI."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Maven")
    parser.add_argument("config", help="Путь к конфигурации CSV")
    stages = range(Stage.config, Stage.visualize + 1)
    parser.add_argument("--stage", type=int, choices=stages,
                        default=Stage.visualize,
                        help="Этап 1-5 (по умолчанию 5)")
    parser.add_argument("--output", default="output/dependencies",
                        help="Путь для D2/SVG без расширения")
    parser.add_argument("--no-open", action="store_true",
                        help="Создать SVG без открытия браузера")
    return parser.parse_args(argv)


def direct_dependencies(config):
    """Вывести только прямые зависимости для второго этапа."""
    if config.test_mode:
        repository = TestRepository(config.repository)
        dependencies = repository.edges(config.package, frozenset(), True)
        return [str(child) for child, _ in dependencies]
    repository = MavenRepository(config.repository, include_all_scopes=True)
    return [str(dep.artifact)
            for dep in repository.dependencies(root_artifact(config))]


def execute(config, args):
    """Выполнить этап; временные отладочные выводы изолированы флагом."""
    if args.stage == Stage.config:
        for key, value in asdict(config).items():
            print(f"{key}={value}")
        return
    if args.stage == Stage.direct:
        print("\n".join(direct_dependencies(config)))
        return
    graph = configured_graph(config)
    if args.stage == Stage.graph:
        print("\n".join(edge_lines(graph)))
        for source, target in graph.cycles:
            print(f"Цикл: {source} -> {target}")
    elif args.stage == Stage.order:
        print(" -> ".join(str(node) for node in loading_order(graph)))
    else:
        source, image = render(graph, args.output)
        print(f"D2: {source}\nSVG: {image}")
        if config.ascii_tree:
            print(ascii_tree(graph))
        if not args.no_open:
            show_image(image)


def main(argv=None):
    """Запустить CLI с понятной ошибкой и ненулевым статусом при сбое."""
    args = arguments(argv)
    try:
        execute(load_config(args.config), args)
        return 0
    except AppError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
