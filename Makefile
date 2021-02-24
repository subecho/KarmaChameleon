.PHONY: check
check:
	black --check --color --diff .

.PHONY: format
format:
	black .

.PHONY: test
test:
	pytest
