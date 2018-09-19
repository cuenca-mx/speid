SHELL := bash
PATH := ./venv/bin:${PATH}
PYTHON=python3.6


default: install

venv:
		$(PYTHON) -m venv --prompt stpmex-handler venv
		source venv/bin/activate
		pip install --quiet --upgrade pip

clean:
		rm -rf venv/

install:
		pip install --quiet --upgrade -r requirements.txt

install-dev: install
		pip install --quiet --upgrade -r requirements-dev.txt

test: install-dev lint
		pytest -v /stpmex_handler/test/test.py

lint:
		pycodestyle --ignore=E402 stpmex_handler migrations
