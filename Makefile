VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: venv install run test

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install -r requirements.txt

run: install
	$(PY) app.py

test: install
	$(PY) -m pytest
