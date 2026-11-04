PYTHON ?= python3

.PHONY: build test run
build:
	$(PYTHON) -m compileall -q src

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

run:
	./run.sh examples/junit.csv

.PHONY: lint demo
lint:
	$(PYTHON) -m ruff check src tests scripts
	$(PYTHON) scripts/check_rules.py

demo:
	./run.sh examples/junit.csv --output output/junit --no-open
	./run.sh examples/commons-text.csv --output output/commons-text --no-open
	./run.sh examples/commons-io.csv --output output/commons-io --no-open
