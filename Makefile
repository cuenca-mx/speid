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

install-dev: venv install
		pip install --quiet --upgrade -r requirements-dev.txt

lint:
		pycodestyle --ignore=E402 stpmex_handler migrations

