.PHONY: run test mypy

PYTHON=python3

.DEFAULT: run

run:
	${PYTHON} main.py

test:
	${PYTHON} -m unittest tests/test_*.py

mypy:
	${PYTHON} -m mypy --namespace-packages --disallow-untyped-calls --disallow-untyped-defs $(MYPY_FILE)

