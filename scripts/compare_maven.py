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
PLUGIN = "org.apache.maven.plugins:maven-dependency-plugin:3.8.1"


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


def compare_sample(sample, destination, resolve=False):
    """Сохранить дерево Maven или список разрешенных зависимостей."""
    label, group, name, version = sample
    goal = "resolve" if resolve else "tree"
    suffix = "resolved" if resolve else "maven"
    output = destination / f"{label}-{suffix}.txt"
    with tempfile.TemporaryDirectory(prefix="mavengraph-reference-") as temp:
        pom = Path(temp) / "pom.xml"
        pom.write_text(wrapper_pom(group, name, version), encoding="utf-8")
        options = ["-DincludeScope=runtime", "-Dsort=false"] if resolve else [
            "-Dscope=runtime", "-DoutputType=text"
        ]
        command = ["mvn", "-B", "-q", "-f", str(pom), f"{PLUGIN}:{goal}",
                   f"-DoutputFile={output}", *options]
        subprocess.run(command, check=True, timeout=300)
    print(output.read_text(encoding="utf-8"))


def main():
    """Сохранить результаты трех независимых эталонных запусков."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="docs/comparison")
    parser.add_argument("--resolve", action="store_true",
                        help="Сравнить с порядком classpath Maven")
    args = parser.parse_args()
    destination = Path(args.output).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for sample in SAMPLES:
        compare_sample(sample, destination, args.resolve)


if __name__ == "__main__":
    main()
