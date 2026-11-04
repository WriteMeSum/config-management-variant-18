"""Проверки ошибок файлового JSON-репозитория."""

import tempfile
import unittest
from pathlib import Path

from mavengraph.config import AppError
from mavengraph.test_repository import TestRepository


class TestRepositoryTests(unittest.TestCase):
    """Поврежденный граф отклоняется до обхода."""

    def test_invalid_graphs(self):
        """Проверить JSON, имена, типы, отсутствующие узлы и дубликаты."""
        invalid = ('{', '[]', '{}', '{"a":[]}', '{"A":1}',
                   '{"A":["B"]}', '{"A":[1]}', '{"A":[],"A":[]}')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "graph.json"
            for data in invalid:
                with self.subTest(data=data):
                    path.write_text(data, encoding="utf-8")
                    with self.assertRaises(AppError):
                        TestRepository(path)

    def test_missing_package(self):
        """Неизвестный корень дает диагностируемую ошибку."""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "graph.json"
            path.write_text('{"A":[]}', encoding="utf-8")
            repository = TestRepository(path)
            with self.assertRaises(AppError):
                repository.edges("Z", frozenset(), True)
