"""Точка входа: python -m mavengraph."""

import argparse
import sys
from dataclasses import asdict

from .config import AppError, load_config
from .repository import MavenRepository, root_artifact
from .graph import configured_graph, edge_lines
from .order import loading_order


def main(argv=None):
    """Проверить параметры и вывести конфигурацию первого этапа."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Maven")
    parser.add_argument("config", help="Путь к конфигурации CSV")
    parser.add_argument("--stage", type=int, choices=(1, 2, 3, 4), default=4)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.stage == 1:
            for key, value in asdict(config).items():
                print(f"{key}={value}")
        elif args.stage == 4:
            graph = configured_graph(config)
            print(" -> ".join(str(node) for node in loading_order(graph)))
        elif args.stage == 3:
            graph = configured_graph(config)
            print("\n".join(edge_lines(graph)))
            for source, target in graph.cycles:
                print(f"Цикл: {source} -> {target}")
        else:
            if config.test_mode:
                raise AppError("Тестовый репозиторий появится на этапе 3")
            repository = MavenRepository(config.repository)
            for dependency in repository.dependencies(root_artifact(config)):
                print(dependency.artifact)
        return 0
    except AppError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
