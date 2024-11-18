ENV ?=
include .env
-include .env.$(ENV)

MAKE = make
PYTHON = python

check-deps:  ## Check new versions and update deps
	$(PYTHON) -m pur -r requirements-dev.txt -d

update-dev-deps:  ## Check new versions and update deps
	$(PYTHON) -m pur -r requirements.dev.txt

install-deps:  ## Install dependencies
	$(PYTHON) -m pip install -r requirements.txt

isort:
	$(PYTHON) -m isort --check-only .

black:
	$(PYTHON) -m black --check .

mypy-install:
	$(PYTHON) -m mypy --install-types

mypy:
	$(PYTHON) -m mypy .

flake8:
	$(PYTHON) -m flake8 .

bandit:
	$(PYTHON) -m bandit -r app

lint: isort black mypy flake8 bandit

install: install-deps

enable-pre-commit:
	pre-commit install

dev-install-deps:
	$(PYTHON) -m pip install -r requirements.dev.txt

dev-install: dev-install-deps update-dev-deps mypy-install enable-pre-commit

check-env:
ifndef SPG_API_HOST
abort:
	@echo "SPG_API_HOST" not set
endif


set-api-in-template: check-env
	sed -i '' -e "s/SPG_API_HOST/$(SPG_API_HOST)/g" templates/template.html
	sed -i '' -e "s/SPG_API_PORT/$(SPG_API_PORT)/g" templates/template.html

api:
	uvicorn api:spg_api --host 127.0.0.1 --port 8502 --workers 1

web_internal:
	streamlit run app.py -- --env $(ENV)

web: set-api-in-template
	${MAKE} -B web_internal

web-local:
	${MAKE} set-api-in-template ENV=local
	${MAKE} -B web_internal ENV=local

run:
	${MAKE} -B web

run-local:
	${MAKE} -B -j 2 api web-local
