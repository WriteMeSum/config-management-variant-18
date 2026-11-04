"""Чтение и строгая проверка пяти параметров CSV."""

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


CSV_FIELD_COUNT = 2


class AppError(Exception):
    """Ошибка входных данных или внешнего инструмента."""


@dataclass(frozen=True)
class Config:
    """Проверенные настройки; путь считается от CSV-файла."""

    package: str
    repository: str
    test_mode: bool
    version: str
    ascii_tree: bool


def boolean(value, name):
    """Разобрать только true/false без молчаливых подстановок."""
    if value.lower() not in {"true", "false"}:
        raise AppError(f"{name}: ожидается true или false")
    return value.lower() == "true"


def read_rows(path):
    """Проверить заголовок, длину строк, уникальность ключей."""
    values = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream, strict=True)
        if next(rows, None) != ["key", "value"]:
            raise AppError("CSV: требуется заголовок key,value")
        for row in rows:
            if len(row) != CSV_FIELD_COUNT:
                raise AppError("CSV: каждая строка должна иметь два поля")
            key, value = (item.strip() for item in row)
            if key in values or not value:
                raise AppError(f"CSV: повтор ключа или пустое значение: {key}")
            values[key] = value
    if set(values) != set(Config.__annotations__):
        raise AppError("CSV: нужны только " + ", ".join(Config.__annotations__))
    return values


def validate_names(values, test_mode):
    """Проверить имя пакета и фиксированную версию без диапазонов."""
    pattern = r"[A-Z]+" if test_mode else r"[\w.-]+:[\w.-]+"
    if not re.fullmatch(pattern, values["package"], flags=re.ASCII):
        raise AppError("package: нужно groupId:artifactId или A-Z в тестах")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", values["version"]):
        raise AppError("version: нужна фиксированная версия, например 1.0")
    for part in values["package"].split(":") + [values["version"]]:
        if part in {".", ".."}:
            raise AppError("package: недопустимое имя")


def validate_repository(value, test_mode, base):
    """Проверить HTTP(S) URL либо существующий тестовый файл."""
    if test_mode:
        path = (base / value).resolve()
        if not path.is_file():
            raise AppError(f"repository: тестовый файл не найден: {path}")
        return str(path)
    url = urlsplit(value)
    if url.scheme not in {"http", "https"} or not url.hostname:
        raise AppError("repository: нужен URL http:// или https://")
    if url.query or url.fragment or url.username or url.password:
        raise AppError("repository: пароль, query и fragment запрещены")
    try:
        url.port
    except ValueError as error:
        raise AppError("repository: некорректный порт") from error
    return value.rstrip("/")


def load_config(filename):
    """Прочитать CSV и преобразовать ошибки в понятное сообщение."""
    path = Path(filename).resolve()
    try:
        values = read_rows(path)
        test_mode = boolean(values["test_mode"], "test_mode")
        ascii_tree = boolean(values["ascii_tree"], "ascii_tree")
        validate_names(values, test_mode)
        repository = validate_repository(
            values["repository"], test_mode, path.parent
        )
        return Config(values["package"], repository, test_mode,
                      values["version"], ascii_tree)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        raise AppError(f"Не удалось прочитать конфигурацию: {error}") from error
