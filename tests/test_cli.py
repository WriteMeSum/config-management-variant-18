"""Проверки CLI и временных выводов разных этапов."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from mavengraph.__main__ import main
from mavengraph.pom import parse_xml


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

    def test_stage_two_includes_test_dependencies(self):
        """Прямой вывод включает test, а runtime-граф его исключает."""
        pom = parse_xml(b"""<project><dependencies><dependency>
          <groupId>g</groupId><artifactId>test-lib</artifactId>
          <version>1</version><scope>test</scope>
        </dependency></dependencies></project>""")
        args = ["examples/junit.csv", "--stage"]
        with patch("mavengraph.repository.MavenRepository.fetch",
                   return_value=pom) as fetch:
            direct = io.StringIO()
            with redirect_stdout(direct):
                self.assertEqual(main([*args, "2"]), 0)
            self.assertEqual(fetch.call_count, 1)
            graph = io.StringIO()
            with redirect_stdout(graph):
                self.assertEqual(main([*args, "3"]), 0)
        self.assertEqual(direct.getvalue().strip(), "g:test-lib:1")
        self.assertEqual(graph.getvalue().strip(), "junit:junit:4.13.2")

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
