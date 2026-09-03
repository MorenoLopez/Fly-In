.PHONY: install run debug clean lint lint-strict

install:
	uv sync

run:
	uv run python -m src --map data/maps/test.txt --gui

run-cli:
	uv run python -m src --map data/maps/easy_linear.txt --no-gui

debug:
	uv run python -m pdb -m src --map data/maps/easy_linear.txt --no-gui

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 src/
	mypy src/ --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs

lint-strict:
	flake8 src/
	mypy src/ --strict
