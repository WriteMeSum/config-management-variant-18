"""Строгий файловый репозиторий: JSON-список смежности A-Z."""

import json
import re
from pathlib import Path

from .config import AppError


def unique_object(pairs):
    """Запретить повторные JSON-ключи вместо молчаливой перезаписи."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise AppError(f"Повторный пакет в JSON: {key}")
        result[key] = value
    return result


def validate_graph(data):
    """Проверить имена, списки и существование всех ссылок."""
    if not isinstance(data, dict) or not data:
        raise AppError("Тестовый репозиторий: нужен непустой JSON-объект")
    for name, children in data.items():
        if not re.fullmatch(r"[A-Z]+", name):
            raise AppError(f"Имя тестового пакета должно быть A-Z: {name}")
        if not isinstance(children, list):
            raise AppError(f"Зависимости {name} должны быть списком")
        for child in children:
            if not isinstance(child, str) or child not in data:
                raise AppError(f"Неизвестная зависимость {name}: {child}")
    return {name: list(dict.fromkeys(children))
            for name, children in data.items()}


class TestRepository:
    """Локальный граф для демонстрации цепочек, ромбов и циклов."""

    def __init__(self, filename):
        """Прочитать UTF-8 JSON с проверкой структуры."""
        try:
            data = json.loads(Path(filename).read_text(encoding="utf-8"),
                              object_pairs_hook=unique_object)
        except (OSError, UnicodeError, ValueError) as error:
            raise AppError(f"Не удалось прочитать тестовый граф: {error}") \
                from error
        self.graph = validate_graph(data)

    def edges(self, node, excluded, is_root):
        """Вернуть тестовые ребра; версии в этом формате не используются."""
        if node not in self.graph:
            raise AppError(f"Пакет отсутствует в тестовом репозитории: {node}")
        return [(child, frozenset()) for child in self.graph[node]]
