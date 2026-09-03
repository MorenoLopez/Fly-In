#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   __main__.py                                          :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/02 20:14:11 by horarivo            #+#    #+#            #
#   Updated: 2026/09/02 21:01:57 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

"""entry point for Fly-in."""

import argparse
import sys
from pathlib import Path

from src.config import DEFAULT_MAP_FILE
from src.mode import run_simulation, run_cli


def parse_args() -> argparse.Namespace:
    """
        Parse arguments.
    """
    parser = argparse.ArgumentParser(
        description="Fly-in - Drone Routing System"
    )
    parser.add_argument(
        "--map", type=Path, default=DEFAULT_MAP_FILE,
        help="Path to the map file."
    )
    parser.add_argument(
        "--no-gui", action="store_true",
        help="Run in terminal mode only."
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Path to save simulation output."
    )
    return parser.parse_args()


def main() -> int:
    """
        Main entry point
    """
    args = parse_args()
    cli_mode = args.no_gui

    if cli_mode:
        return run_cli(args.map, args.output)
    else:
        result = run_simulation(args.map, use_gui=True)
        if "error" in result:
            return 1
        print(f"Simulation completed in {result['turns']} turns")
        return 0


if __name__ == "__main__":
    sys.exit(main())
