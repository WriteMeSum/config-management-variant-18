"""Модели координат, зависимостей и эффективного POM."""

import re
from dataclasses import dataclass, field

from .config import AppError


@dataclass(frozen=True)
class Artifact:
    """Фиксированные координаты groupId:artifactId:version."""

    group: str
    name: str
    version: str

    def __post_init__(self):
        """Не допускать диапазоны, подстановки и выход из URL-пути."""
        for value in (self.group, self.name, self.version):
            if not re.fullmatch(r"[A-Za-z0-9_+.-]+", value):
                raise AppError(f"Неподдерживаемые координаты: {self}")
            if value in {".", ".."}:
                raise AppError(f"Недопустимые координаты: {self}")

    def __str__(self):
        """Вернуть полные координаты для подписи узла."""
        return f"{self.group}:{self.name}:{self.version}"

    @property
    def key(self):
        """Идентификатор без версии."""
        return f"{self.group}:{self.name}"

    @property
    def pom_path(self):
        """Сформировать путь по стандартной раскладке Maven."""
        group = self.group.replace(".", "/")
        return f"{group}/{self.name}/{self.version}/" \
               f"{self.name}-{self.version}.pom"


@dataclass(frozen=True)
class Dependency:
    """Ребро с областью видимости, optional и исключениями."""

    artifact: Artifact
    scope: str = "compile"
    optional: bool = False
    exclusions: frozenset = frozenset()


@dataclass
class Pom:
    """Разрешенные свойства, управление версиями и зависимости."""

    properties: dict = field(default_factory=dict)
    managed: dict = field(default_factory=dict)
    dependencies: list = field(default_factory=list)
