SHELL := bash
PROJECT = speid
PYTHON = python3.7
DOCKER = docker-compose run --rm $(PROJECT)
isort = isort -rc -ac $(PROJECT) tests
black = black -S -l 79 --target-version py37 $(PROJECT) tests

default: install

install:
		pip install -q -r requirements.txt

install-dev: install
		pip install -q -r requirements-dev.txt

venv:
		$(PYTHON) -m venv --prompt $(PROJECT) venv
		source venv/bin/activate; \
		pip install -qU pip;

format:
		$(isort)
		$(black)

lint:
		flake8 $(PROJECT) tests
		$(isort) --check-only
		$(black) --check
		mypy $(PROJECT) tests

clean-pyc:
		find . -name '__pycache__' -exec rm -r "{}" +
		find . -name '*.pyc' -delete
		find . -name '*~' -delete

test: clean-pyc lint
		pytest --cov-report term-missing tests/ --cov=speid
		coveralls

travis-test:
		$(MAKE) install-dev
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
