SHELL := bash
PROJECT = speid
PYTHON = python3.7
DOCKER = docker-compose run --rm $(PROJECT)
ISORT = venv/bin/isort -rc -ac $(PROJECT) tests
BLACK = venv/bin/black -S -l 79 --target-version py37 $(PROJECT) tests



install:
		pip install -q -r requirements.txt

install-dev: install
		pip install -q -r requirements-dev.txt

venv:
		$(PYTHON) -m venv --prompt speid venv
		venv/bin/pip install -qU pip

format:
		$(ISORT)
		$(BLACK)

lint:
		venv/bin/flake8 $(PROJECT) tests setup.py
		$(ISORT) --check-only
		$(BLACK) --check

clean-pyc:
		find . -name '__pycache__' -exec rm -r "{}" +
		find . -name '*.pyc' -delete
		find . -name '*~' -delete

test: clean-pyc lint
		pytest -vv
		coveralls

travis-test:
		pip install -q isort black flake8
		$(MAKE) lint
		$(MAKE) docker-build
		$(DOCKER) scripts/test.sh

docker-test: docker-build
		# Clean up even if there's an error
		$(DOCKER) scripts/test.sh || $(MAKE) docker-stop
		$(MAKE) docker-stop

docker-build: clean-pyc
		docker-compose build
		touch docker-build

docker-stop:
		docker-compose stop
		docker-compose rm -f

clean-docker:
		docker-compose down --rmi local
		rm docker-build

docker-shell: docker-build
		# Clean up even if there's an error
		$(DOCKER) scripts/devwrapper.sh bash || $(MAKE) docker-stop
		$(MAKE) docker-stop


.PHONY: install install-dev lint clean-pyc test docker-stop clean-docker shell
