# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: horarivo <horarivo@student.42antananari    +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/08 16:01:04 by horarivo          #+#    #+#              #
#    Updated: 2026/09/22 11:55:27 by horarivo         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #



install:
	uv sync

run:
	uv run src/main.py --map data/maps/circular_loop.txt --gui

run-cli:
	uv run src/main.py --map data/maps/test.txt

debug:
	uv run python -m pdb src/main.py --map data/maps/test.txt

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

.PHONY: install run debug clean lint lint-strict