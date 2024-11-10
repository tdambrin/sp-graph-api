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

mypy:
	$(PYTHON) -m mypy .

flake8:
	$(PYTHON) -m flake8 .

bandit:
	$(PYTHON) -m bandit -r app

lint: isort black mypy flake8 bandit

install: install-deps

dev-install:  update-dev-deps
	$(PYTHON) -m pip install -r requirements.dev.txt

api:
	uvicorn api:spg_api --host 127.0.0.1 --port 8502

web_internal:
	streamlit run app.py

web:
	${MAKE} -B web_internal
run:
	${MAKE} -B -j 2 api web