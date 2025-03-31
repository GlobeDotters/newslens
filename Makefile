.PHONY: install install-dev lint test clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

lint:
	flake8 newslens tests
	black --check newslens tests
	isort --check-only --profile black newslens tests
	mypy newslens

format:
	black newslens tests
	isort --profile black newslens tests

test:
	pytest tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .coverage -exec rm -rf {} +

build:
	python setup.py sdist bdist_wheel

publish:
	python -m twine upload dist/*

run:
	newslens headlines
