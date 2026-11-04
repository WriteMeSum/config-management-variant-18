"""Загрузка Maven POM через urllib с кэшированием в памяти."""

from urllib.error import URLError
from urllib.request import Request, urlopen

from .config import AppError
from .model import Artifact, Pom
from .pom import build_pom, coordinates, parse_xml

TIMEOUT_SECONDS = 20
MAX_POM_BYTES = 4 * 1024 * 1024
MAX_MODEL_DEPTH = 60


class MavenRepository:
    """HTTP-репозиторий; менеджеры пакетов не вызываются."""

    def __init__(self, url):
        """Сохранить URL и создать кэш моделей POM."""
        self.url = url.rstrip("/")
        self.cache = {}
        self.loading = set()

    def fetch(self, artifact):
        """Скачать один POM с лимитом объема и таймаутом."""
        url = f"{self.url}/{artifact.pom_path}"
        request = Request(url, headers={"User-Agent": "mavengraph/1.0"})
        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                data = response.read(MAX_POM_BYTES + 1)
        except (OSError, URLError, ValueError) as error:
            raise AppError(f"Не удалось получить {url}: {error}") from error
        if len(data) > MAX_POM_BYTES:
            raise AppError(f"Слишком большой POM: {url}")
        return parse_xml(data)

    def load(self, artifact):
        """Разрешить parent/BOM; обнаружить циклы в моделях."""
        if artifact in self.cache:
            return self.cache[artifact]
        if artifact in self.loading:
            raise AppError(f"Цикл parent/BOM: {artifact}")
        if len(self.loading) >= MAX_MODEL_DEPTH:
            raise AppError("Слишком глубокая цепочка parent/BOM")
        self.loading.add(artifact)
        try:
            root = self.fetch(artifact)
            parent_node = root.find("parent")
            parent = Pom()
            if parent_node is not None:
                parent = self.load(coordinates(parent_node, {}))
            model = build_pom(root, parent, artifact, self.load)
            self.cache[artifact] = model
            return model
        finally:
            self.loading.remove(artifact)

    def dependencies(self, artifact):
        """Вернуть прямые compile/runtime зависимости версии."""
        return self.load(artifact).dependencies


def root_artifact(config):
    """Соединить имя пакета и пользовательскую версию."""
    group, name = config.package.split(":")
    return Artifact(group, name, config.version)
