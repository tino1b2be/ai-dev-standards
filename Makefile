.PHONY: check test sync check-all

# Thin wrappers around scripts/assemble-pack.py and pytest. These exist
# for convenience; every target can be run directly with python or pytest.

check: check-all

check-all:
	python scripts/assemble-pack.py check-all

test:
	pytest tests/

sync:
	python scripts/assemble-pack.py sync-steering
