"""Самостоятельный разбор XML POM без сторонних библиотек."""

import re
from xml.etree import ElementTree

from .config import AppError
from .model import Artifact, Dependency, Pom

PROPERTY = re.compile(r"\$\{([^}]+)\}")
MAX_EXPANSIONS = 30


def parse_xml(data):
    """Разобрать XML и убрать namespace для единообразного поиска."""
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise AppError("POM: DTD и пользовательские сущности запрещены")
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as error:
        raise AppError(f"Некорректный XML POM: {error}") from error
    for node in root.iter():
        node.tag = node.tag.rsplit("}", 1)[-1]
    if root.tag != "project":
        raise AppError("POM: корневой элемент должен быть project")
    return root


def text(node, path, default=""):
    """Прочитать непустой текст дочернего XML-элемента."""
    return (node.findtext(path) or default).strip()


def expand(value, properties):
    """Разрешить вложенные свойства, сообщить о цикле или пропуске."""
    for _ in range(MAX_EXPANSIONS):
        if not PROPERTY.search(value):
            return value
        names = PROPERTY.findall(value)
        missing = set(names) - set(properties)
        if missing:
            raise AppError("Неизвестные свойства POM: " + ", ".join(missing))
        value = PROPERTY.sub(lambda match: properties[match[1]], value)
    raise AppError("Циклические или слишком глубокие свойства POM")


def coordinates(node, properties):
    """Прочитать обязательные координаты POM или зависимости."""
    values = [expand(text(node, key), properties)
              for key in ("groupId", "artifactId", "version")]
    return Artifact(*values)


def properties_for(root, parent, artifact):
    """Соединить свойства родителя, проекта и стандартные project.*."""
    properties = dict(parent.properties)
    properties.update({node.tag: (node.text or "").strip()
                       for node in root.findall("./properties/*")})
    for prefix in ("project", "pom"):
        for key, value in (("groupId", artifact.group),
                           ("artifactId", artifact.name),
                           ("version", artifact.version)):
            properties[f"{prefix}.{key}"] = value
    parent_node = root.find("parent")
    if parent_node is not None:
        for key in ("groupId", "artifactId", "version"):
            properties[f"project.parent.{key}"] = text(parent_node, key)
    return properties


def read_managed(root, properties, inherited, load):
    """Наследовать dependencyManagement и импортировать BOM."""
    managed = dict(inherited)
    entries = root.findall("./dependencyManagement/dependencies/dependency")
    local = {}
    for node in entries:
        values = {child.tag: expand((child.text or "").strip(), properties)
                  for child in node if not list(child)}
        key = f"{values.get('groupId', '')}:{values.get('artifactId', '')}"
        if values.get("scope") == "import":
            if values.get("type") != "pom":
                raise AppError("BOM import требует type=pom")
            bom = load(coordinates(node, properties))
            for name, value in bom.managed.items():
                managed.setdefault(name, value)
        else:
            local[key] = values
    managed.update(local)
    return managed


def read_dependency(node, properties, managed):
    """Получить runtime/compile ребро с версией из management."""
    group = expand(text(node, "groupId"), properties)
    name = expand(text(node, "artifactId"), properties)
    defaults = managed.get(f"{group}:{name}", {})
    scope = expand(text(node, "scope", defaults.get("scope", "compile")),
                   properties)
    if scope not in {"compile", "runtime"}:
        return None
    version = expand(text(node, "version", defaults.get("version", "")),
                     properties)
    optional = expand(text(node, "optional", "false"), properties)
    if optional not in {"true", "false"}:
        raise AppError("POM: optional должен быть true/false")
    exclusions = frozenset(
        expand(text(item, "groupId"), properties) + ":" +
        expand(text(item, "artifactId"), properties)
        for item in node.findall("./exclusions/exclusion")
    )
    return Dependency(Artifact(group, name, version), scope,
                      optional == "true", exclusions)


def build_pom(root, parent, artifact, load):
    """Построить модель с наследованием и импортами BOM."""
    properties = properties_for(root, parent, artifact)
    managed = read_managed(root, properties, parent.managed, load)
    dependencies = {dep.artifact.key: dep for dep in parent.dependencies}
    for node in root.findall("./dependencies/dependency"):
        dependency = read_dependency(node, properties, managed)
        key = expand(text(node, "groupId"), properties) + ":" + \
            expand(text(node, "artifactId"), properties)
        dependencies.pop(key, None)
        if dependency is not None:
            dependencies[key] = dependency
    return Pom(properties, managed, list(dependencies.values()))
