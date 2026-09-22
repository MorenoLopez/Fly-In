#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   main.py                                              :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 16:15:20 by horarivo            #+#    #+#            #
#   Updated: 2026/09/16 16:47:26 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


"""Entry point for the Fly-in drone routing simulation."""

import sys
import argparse
from simulate import SimulationEngine
from parser import Parser, ParseError
from algorithms import (
    PathFinder,
    ReservationTable,
    RoutingManager,
    RoutingError,
)


def parse_args() -> argparse.Namespace:
    """Parse and return the command-line arguments for the simulation."""
    arg_parser = argparse.ArgumentParser(
        description="Fly-in drone routing simulation"
    )
    arg_parser.add_argument(
        "--map", required=True, help="Path to the map file to load"
    )
    arg_parser.add_argument(
        "--gui", action="store_true", help="Launch graphical visualization"
    )
    return arg_parser.parse_args()


def main() -> None:
    """Parse a map, route all drones, and display the resulting simulation."""
    args = parse_args()

    try:
        parsedmap = Parser().parse(args.map)
    except (OSError, ParseError, ValueError) as e:
        print(f"Error while parsing map file: {e}", file=sys.stderr)
        sys.exit(1)

    assert (
        parsedmap.start_zone is not None
    ), "start_zone should never be None after parsing"
    assert (
        parsedmap.end_zone is not None
    ), "end_zone should never be None after parsing"

    pathfinder = PathFinder(parsedmap)
    reservation_table = ReservationTable()
    manager = RoutingManager(pathfinder, reservation_table)

    try:
        routes = manager.route_all_drones(
            parsedmap.drones, parsedmap.start_zone, parsedmap.end_zone
        )
    except RoutingError as e:
        print(f"Error while routing drones: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.gui:
            from visualizer import run_visualizer

            engine = SimulationEngine(routes, parsedmap, reservation_table)
            for line in engine.generate_turns():
                print(line)
            run_visualizer(parsedmap, routes)
        else:
            engine = SimulationEngine(routes, parsedmap, reservation_table)
            for line in engine.generate_turns():
                print(line)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
