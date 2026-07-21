.PHONY: sharpelab-demo-build sharpelab-demo test lint typecheck check

sharpelab-demo-build:
	PYTHONPATH=src .venv/bin/python3 scripts/build_sharpelab_demo_payloads.py

sharpelab-demo: sharpelab-demo-build
	@echo "Starting SharpeLab visual explorer server at http://localhost:8080/ui/sharpelab/index.html"
	@.venv/bin/python3 -m http.server 8080

test:
	PYTHONPATH=src .venv/bin/python3 -m pytest tests/unit tests/integration

lint:
	PYTHONPATH=src .venv/bin/ruff check src scripts tests

typecheck:
	PYTHONPATH=src .venv/bin/pyright src scripts tests

check: lint typecheck test sharpelab-demo-build
