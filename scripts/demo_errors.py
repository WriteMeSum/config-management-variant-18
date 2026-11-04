"""Воспроизводимая демонстрация ошибок пяти параметров CSV."""

import csv
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = {
    "package": "junit:junit",
    "repository": "https://repo.maven.apache.org/maven2",
    "test_mode": "false",
    "version": "4.13.2",
    "ascii_tree": "true",
}
INVALID = {"package": "bad", "repository": "ftp://host",
           "test_mode": "yes", "version": "[1,2)", "ascii_tree": "1"}


def main():
    """Подменить по одному параметру и проверить отказ первого этапа."""
    with tempfile.TemporaryDirectory(prefix="mavengraph-errors-") as temp:
        path = Path(temp) / "invalid.csv"
        for key, invalid in INVALID.items():
            values = dict(BASE, **{key: invalid})
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(("key", "value"))
                writer.writerows(values.items())
            command = ["sh", "run.sh", str(path), "--stage", "1"]
            result = subprocess.run(command, capture_output=True, text=True,
                                    check=False)
            print(f"{key}={invalid}; exit={result.returncode}")
            print(result.stderr.strip())
            if not result.returncode:
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
