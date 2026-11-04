"""Точка входа: python -m mavengraph."""

import argparse
import sys
from dataclasses import asdict

from .config import AppError, load_config
from .repository import MavenRepository, root_artifact


def main(argv=None):
    """Проверить параметры и вывести конфигурацию первого этапа."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Maven")
    parser.add_argument("config", help="Путь к конфигурации CSV")
    parser.add_argument("--stage", type=int, choices=(1, 2), default=2)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.stage == 1:
            for key, value in asdict(config).items():
                print(f"{key}={value}")
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
