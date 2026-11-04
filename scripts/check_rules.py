"""Автоматическая проверка измеримых требований методички."""

import ast
import subprocess
from pathlib import Path

from radon.complexity import cc_visit

MAX_FILE_LINES = 1000
MAX_PYTHON_LINE = 80
MAX_OTHER_LINE = 120
MAX_FUNCTION_LINES = 40
MAX_ARGUMENTS = 7
MAX_COMPLEXITY = 10
FORBIDDEN_PARTS = {"__pycache__", ".idea", ".vscode", "build", "dist"}
FORBIDDEN_SUFFIXES = {".pyc", ".zip", ".jar", ".class", ".png", ".pdf"}


def python_violations(path, source):
    """Проверить размер функций, аргументы, docstring и сложность."""
    errors = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        location = f"{path}:{node.lineno} {node.name}"
        if node.end_lineno - node.lineno + 1 > MAX_FUNCTION_LINES:
            errors.append(f"{location}: функция длиннее 40 строк")
        count = len(node.args.posonlyargs + node.args.args +
                    node.args.kwonlyargs)
        count += bool(node.args.vararg) + bool(node.args.kwarg)
        if count > MAX_ARGUMENTS:
            errors.append(f"{location}: больше 7 аргументов")
        if ast.get_docstring(node) is None:
            errors.append(f"{location}: нет docstring")
    blocks = list(cc_visit(source))
    while blocks:
        block = blocks.pop()
        blocks.extend(getattr(block, "methods", []))
        blocks.extend(getattr(block, "closures", []))
        if block.complexity > MAX_COMPLEXITY:
            errors.append(f"{path}: {block.name}: сложность > 10")
    return errors


def file_violations(path):
    """Проверить текстовый файл и отсутствие запрещенных артефактов."""
    if FORBIDDEN_PARTS.intersection(path.parts):
        return [f"{path}: служебный каталог"]
    if path.suffix in FORBIDDEN_SUFFIXES:
        return [f"{path}: бинарный/служебный файл или архив"]
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeError:
        return [f"{path}: бинарный файл"]
    lines = source.splitlines()
    errors = []
    if len(lines) > MAX_FILE_LINES:
        errors.append(f"{path}: больше 1000 строк")
    limit = MAX_PYTHON_LINE if path.suffix == ".py" else MAX_OTHER_LINE
    for index, line in enumerate(lines, 1):
        if len(line) > limit:
            errors.append(f"{path}:{index}: строка длиннее {limit}")
    if path.suffix == ".py":
        errors.extend(python_violations(path, source))
    return errors


def main():
    """Проверить индекс и новые файлы, учитывая .gitignore."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard",
         "-z"], capture_output=True, check=True,
    )
    paths = sorted(set(result.stdout.decode().strip("\0").split("\0")))
    errors = []
    for filename in paths:
        errors.extend(file_violations(Path(filename)))
    if errors:
        print("\n".join(errors))
        return 1
    print("Правила: размеры файлов/строк/функций, аргументы, docstring, "
          "сложность и состав файлов проверены.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
