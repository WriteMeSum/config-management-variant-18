"""Проверки кэша, наследования, BOM и ошибок HTTP без сети."""

import unittest
from unittest.mock import patch
from urllib.error import URLError

from mavengraph.config import AppError
from mavengraph.model import Artifact
from mavengraph.pom import parse_xml
from mavengraph.repository import MavenRepository


class RepositoryTests(unittest.TestCase):
    """Эффективная модель собирается собственным кодом."""

    def test_parent_and_imported_bom(self):
        """Версия наследуется из BOM, свойство доступно из parent."""
        documents = {
            "parent": '''<project><properties><v>2</v></properties>
            </project>''',
            "bom": '''<project><dependencyManagement><dependencies>
            <dependency><groupId>g</groupId><artifactId>leaf</artifactId>
            <version>3</version></dependency></dependencies>
            </dependencyManagement></project>''',
            "root": '''<project><parent><groupId>g</groupId>
            <artifactId>parent</artifactId><version>1</version></parent>
            <dependencyManagement><dependencies><dependency>
            <groupId>g</groupId><artifactId>bom</artifactId><version>${v}
            </version><scope>import</scope><type>pom</type></dependency>
            </dependencies></dependencyManagement><dependencies><dependency>
            <groupId>g</groupId><artifactId>leaf</artifactId></dependency>
            </dependencies></project>''',
        }
        repository = MavenRepository("https://example.invalid")
        def fetch(artifact):
            """Вернуть XML из локального набора моделей."""
            return parse_xml(documents[artifact.name].encode())

        with patch.object(repository, "fetch", side_effect=fetch) as mocked:
            root = Artifact("g", "root", "1")
            self.assertEqual(str(repository.dependencies(root)[0].artifact),
                             "g:leaf:3")
            repository.dependencies(root)
            self.assertEqual(mocked.call_count, len(documents))

    def test_parent_cycle(self):
        """Цикл моделей не превращается в рекурсию до переполнения."""
        xml = b'''<project><parent><groupId>g</groupId><artifactId>root
        </artifactId><version>1</version></parent></project>'''
        repository = MavenRepository("https://example.invalid")
        with patch.object(repository, "fetch", return_value=parse_xml(xml)):
            with self.assertRaisesRegex(AppError, "Цикл parent/BOM"):
                repository.load(Artifact("g", "root", "1"))
        self.assertFalse(repository.loading)

    def test_network_error(self):
        """Сетевой сбой содержит URL и понятную ошибку."""
        repository = MavenRepository("https://example.invalid")
        with patch("mavengraph.repository.urlopen",
                   side_effect=URLError("offline")):
            with self.assertRaisesRegex(AppError, "Не удалось получить"):
                repository.fetch(Artifact("g", "root", "1"))
