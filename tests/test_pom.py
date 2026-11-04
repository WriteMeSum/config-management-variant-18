"""Проверки собственного XML-парсера без сети."""

import unittest

from mavengraph.config import AppError
from mavengraph.model import Artifact, Pom
from mavengraph.pom import build_pom, expand, parse_xml


class PomTests(unittest.TestCase):
    """Свойства, области видимости, management, namespace и ошибки."""

    def model(self, xml):
        """Разобрать минимальный POM в контексте фиксированного корня."""
        artifact = Artifact("org.example", "root", "1.0")
        return build_pom(parse_xml(xml.encode()), Pom(), artifact, None)

    def test_properties_management_and_scopes(self):
        """Версия берется из management, test-зависимости исключаются."""
        xml = '''<project xmlns="http://maven.apache.org/POM/4.0.0">
        <properties><v>2.0</v></properties><dependencyManagement>
        <dependencies><dependency><groupId>g</groupId><artifactId>a</artifactId>
        <version>${v}</version></dependency></dependencies>
        </dependencyManagement><dependencies><dependency><groupId>g</groupId>
        <artifactId>a</artifactId></dependency><dependency><groupId>g</groupId>
        <artifactId>test</artifactId><scope>test</scope></dependency>
        </dependencies></project>'''
        dependencies = self.model(xml).dependencies
        self.assertEqual([str(dep.artifact) for dep in dependencies],
                         ["g:a:2.0"])

    def test_optional_and_exclusions(self):
        """Метаданные ребра не теряются при разборе."""
        xml = '''<project><dependencies><dependency><groupId>g</groupId>
        <artifactId>a</artifactId><version>1</version><optional>true</optional>
        <exclusions><exclusion><groupId>g</groupId><artifactId>b</artifactId>
        </exclusion></exclusions></dependency></dependencies></project>'''
        dependency = self.model(xml).dependencies[0]
        self.assertTrue(dependency.optional)
        self.assertEqual(dependency.exclusions, frozenset({"g:b"}))

    def test_bad_xml_and_entities(self):
        """Некорректный XML и объявления DTD отклоняются."""
        for data in (b"<project>", b'<!DOCTYPE x><project/>', b"<other/>"):
            with self.subTest(data=data), self.assertRaises(AppError):
                parse_xml(data)

    def test_unresolved_and_cyclic_properties(self):
        """Нельзя выдавать неразрешенные версии за реальные координаты."""
        for properties in ({}, {"x": "${x}"}):
            with self.assertRaises(AppError):
                expand("${x}", properties)

    def test_exact_versions(self):
        """Диапазоны и пустые версии сообщаются как ограничения."""
        for version in ("", "[1,2)", "${missing}", "../1"):
            with self.assertRaises(AppError):
                Artifact("g", "a", version)
