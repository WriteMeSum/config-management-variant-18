"""Проверки CSV и ошибок всех пяти параметров."""

import tempfile
import unittest
from pathlib import Path

from mavengraph.config import AppError, load_config


class ConfigTests(unittest.TestCase):
    """Валидная конфигурация и поврежденные пользовательские значения."""

    def prepare_config(self):
        """Создать изолированный каталог входных файлов."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "config.csv"
        self.values = {
            "package": "junit:junit",
            "repository": "https://repo.maven.apache.org/maven2",
            "test_mode": "false", "version": "4.13.2",
            "ascii_tree": "true",
        }

    def write(self, extra=""):
        """Записать конфигурацию с возможной поврежденной строкой."""
        lines = ["key,value"]
        lines += [f"{key},{value}" for key, value in self.values.items()]
        self.path.write_text("\n".join(lines) + "\n" + extra)
        return self.path

    def test_valid(self):
        """Корректные пять настроек читаются."""
        self.prepare_config()
        config = load_config(self.write())
        self.assertEqual(config.package, "junit:junit")
        self.assertTrue(config.ascii_tree)

    def test_every_parameter_rejected_when_invalid(self):
        """Для каждого параметра есть отдельный ошибочный пример."""
        self.prepare_config()
        invalid = {"package": "bad", "repository": "ftp://host",
                   "test_mode": "yes", "version": "[1;2]",
                   "ascii_tree": "1"}
        for key, value in invalid.items():
            with self.subTest(key=key):
                original = self.values[key]
                self.values[key] = value
                with self.assertRaises(AppError):
                    load_config(self.write())
                self.values[key] = original

    def test_duplicate_and_missing(self):
        """Повтор и отсутствие обязательного ключа запрещены."""
        self.prepare_config()
        with self.assertRaises(AppError):
            load_config(self.write("package,junit:junit\n"))
        del self.values["version"]
        with self.assertRaises(AppError):
            load_config(self.write())

    def test_missing_file(self):
        """Ошибка открытия файла не раскрывает traceback."""
        self.prepare_config()
        with self.assertRaises(AppError):
            load_config(self.path)
