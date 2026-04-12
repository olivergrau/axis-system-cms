.PHONY: docs docs-serve docs-serve-stop

docs:
	mkdocs build --clean

docs-serve:
	mkdocs serve -a 0.0.0.0:8000

docs-serve-stop:
	pkill -f "mkdocs serve" || true
