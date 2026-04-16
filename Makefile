.PHONY: docs docs-serve docs-serve-stop

docs:
	mkdocs build --clean

docs-serve:
	mkdocs serve -a 0.0.0.0:8000

docs-serve-stop:
	pkill -f "mkdocs serve" || true

docs-serve-poll:
	@pip show watchdog >/dev/null 2>&1 || pip install watchdog
	@echo "Starting mkdocs with forced polling…"
	WATCHDOG_USE_POLLING=true mkdocs serve -a 0.0.0.0:8000 -f mkdocs.yml --watch docs --watch mkdocs.yml -v