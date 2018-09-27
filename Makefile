SHELL := bash
PATH := ./venv/bin:${PATH}
PYTHON=python3.7


default: install

venv:
		$(PYTHON) -m venv --prompt speid venv
		source venv/bin/activate
		pip install --quiet --upgrade pip

clean:
		rm -rf venv/

clean-pyc:
		find . -name '*.pyc' -exec rm -f {} +
		find . -name '*.pyo' -exec rm -f {} +
		find . -name '*~' -exec rm -f {} +

install:
		pip install --quiet --upgrade -r requirements.txt

install-dev: install
		pip install --quiet --upgrade -r requirements-dev.txt

test: install-dev lint
		pytest -v speid/test/test.py

lint:
		pycodestyle --ignore=E402 speid migrations
