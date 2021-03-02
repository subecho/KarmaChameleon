.PHONY: check
check:
	black --check --color --diff .
	pylint karma_chameleon tests
	flake8

.PHONY: format
format:
	black .

.PHONY: test
test:
	pytest
