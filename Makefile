.PHONY: clean-pyc clean-build docs

COMMIT_ID = $(shell git rev-parse HEAD)
COMMIT_MSG = $(shell git log -1 --pretty=%B)
VERSION = $(shell grep "current_version" .bumpversion.cfg | cut -d' ' -f3-)


clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info
	rm -fr htmlcov
	rm -f *.db
	rm -f *.mo

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

config: clean
	pipenv install --dev

release:
	pipenv run zappa update dev

format:
	pipenv run black .

lint: ## check style with flake8
	pipenv run black --check .
	pipenv run python -m pytest --pylint --pylint-error-types=EFCRW app

migration:
	export FLASK_APP=app/application.py && pipenv run flask data_migration
