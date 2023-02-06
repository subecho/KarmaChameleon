.PHONY: check
check:
	black --check --color --diff .
	ruff karma_chameleon tests
	flake8

.PHONY: format
format:
	black .

.PHONY: test
test:
	pytest --cov-report term-missing
