"""Проверки CLI и временных выводов разных этапов."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from mavengraph.__main__ import main


class CliTests(unittest.TestCase):
    """Ошибки не дают traceback, финальный режим не печатает отладку."""

    def test_bad_config_returns_error(self):
        """Нечитаемый файл возвращает ненулевой статус и stderr."""
        error = io.StringIO()
        with redirect_stderr(error):
            status = main(["missing-config.csv"])
        self.assertEqual(status, 1)
        self.assertIn("Ошибка:", error.getvalue())
        self.assertNotIn("Traceback", error.getvalue())

    def test_stage_one_prints_all_settings(self):
        """Все пять параметров видны в режиме этапа 1."""
        output = io.StringIO()
        with redirect_stdout(output):
            status = main(["examples/diamond.csv", "--stage", "1"])
        self.assertEqual(status, 0)
        for name in ("package", "repository", "test_mode", "version",
                     "ascii_tree"):
            self.assertIn(f"{name}=", output.getvalue())

    def test_final_stage_has_no_temporary_output(self):
        """Финальный режим ограничивается D2/SVG и запрошенным деревом."""
        output = io.StringIO()
        with patch("mavengraph.__main__.render", return_value=("d2", "svg")):
            with redirect_stdout(output):
                status = main(["examples/diamond.csv", "--no-open"])
        self.assertEqual(status, 0)
        self.assertIn("D [shared]", output.getvalue())
        self.assertNotIn("test_mode=", output.getvalue())
        self.assertNotIn("D -> B -> C -> A", output.getvalue())

    def test_cycle_order_error(self):
        """Невозможный порядок загрузки объясняется через stderr."""
        error = io.StringIO()
        with redirect_stderr(error):
            status = main(["examples/cycle.csv", "--stage", "4"])
        self.assertEqual(status, 1)
        self.assertIn("цикл", error.getvalue())
