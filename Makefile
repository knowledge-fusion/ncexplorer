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
	pip install -e . --process-dependency-links

release:
	zappa update dev
	curl https://finance-news.knowledge-fusion.science/reset_cache

build:
	docker build -t knowledgefusion1/nlp:master .
	docker push knowledgefusion1/nlp:master
