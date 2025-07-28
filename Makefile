.ONESHELL:

.PHONY: all install update test lint clean

all: install

install:
	python -m venv ./venv
	venv/bin/python --version
	venv/bin/python -m pip install --upgrade pip
	venv/bin/pip install poetry==2.1.3
	@. venv/bin/activate && \
	poetry install --no-root --with dev && \
	poetry run pre-commit install

update:
	poetry update --with dev

lint:
	poetry run ruff format
	poetry run ruff check . --fix --exit-non-zero-on-fix

clean:
	@. venv/bin/activate && \
	pre-commit uninstall && \
	rm -rf venv && \
	rm -f poetry.lock && \
	rm -f requirements.txt
