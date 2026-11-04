"""Только эталонное сравнение; не используется основным приложением."""

import argparse
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

SAMPLES = (
    ("junit", "junit", "junit", "4.13.2"),
    ("commons-text", "org.apache.commons", "commons-text", "1.10.0"),
    ("commons-io", "commons-io", "commons-io", "2.11.0"),
)
PLUGIN = "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree"


def wrapper_pom(group, name, version):
    """Создать отдельный проект с одной исследуемой зависимостью."""
    group, name, version = map(escape, (group, name, version))
    return f'''<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId><artifactId>comparison</artifactId>
  <version>1.0</version><dependencies><dependency>
  <groupId>{group}</groupId><artifactId>{name}</artifactId>
  <version>{version}</version></dependency></dependencies>
</project>
'''


def compare_sample(sample, destination):
    """Запустить эталонный Maven и сохранить проверяемый текст дерева."""
    label, group, name, version = sample
    output = destination / f"{label}-maven.txt"
    with tempfile.TemporaryDirectory(prefix="mavengraph-reference-") as temp:
        pom = Path(temp) / "pom.xml"
        pom.write_text(wrapper_pom(group, name, version), encoding="utf-8")
        command = ["mvn", "-B", "-q", "-f", str(pom), PLUGIN,
                   "-Dscope=runtime", "-DoutputType=text",
                   f"-DoutputFile={output}"]
        subprocess.run(command, check=True, timeout=300)
    print(output.read_text(encoding="utf-8"))


def main():
    """Сохранить результаты трех независимых эталонных запусков."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="docs/comparison")
    args = parser.parse_args()
    destination = Path(args.output).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for sample in SAMPLES:
        compare_sample(sample, destination)


if __name__ == "__main__":
    main()
