"""Точка входа: python -m mavengraph."""

import argparse
import sys
from dataclasses import asdict

from .config import AppError, load_config


def main(argv=None):
    """Проверить параметры и вывести конфигурацию первого этапа."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Maven")
    parser.add_argument("config", help="Путь к конфигурации CSV")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        for key, value in asdict(config).items():
            print(f"{key}={value}")
        return 0
    except AppError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
