PYTHON ?= python3

.PHONY: build test run
build:
	$(PYTHON) -m compileall -q src

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

run:
	./run.sh examples/junit.csv
