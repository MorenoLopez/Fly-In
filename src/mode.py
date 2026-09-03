#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   mode.py                                              :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/02 21:01:32 by horarivo            #+#    #+#            #
#   Updated: 2026/09/02 21:01:35 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

"""Main orchestration for the Fly-in drone routing system."""

import sys
from pathlib import Path
from typing import Any

from src.models.map_graph import MapGraph
from src.parser import parse_map_file, ParseError
from src.algorithms.simulator import Simulator
from src.visualizer import Visualizer


def run_simulation(map_file: Path, use_gui: bool = True) -> dict[str, Any]:
    """Run the complete drone routing simulation.

    Args:
        map_file: Path to the map file.
        use_gui: Whether to launch the Pygame visualizer.

    Returns:
        Dictionary with simulation results.
    """
    try:
        graph = parse_map_file(map_file)
    except (ParseError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return {"error": str(exc), "turns": 0}

    simulator = Simulator(graph)

    if use_gui:
        visualizer = Visualizer(graph)
        visualizer.set_drones(simulator.drones)

        try:
            while visualizer.running:
                advance = visualizer.handle_events()
                if not visualizer.running:
                    break

                if visualizer.reset_requested:
                    visualizer.reset_requested = False
                    # Re-parse the map file for a fully clean graph: zone
                    # occupancy and connection transit counters must not
                    # carry over from the previous run.
                    graph = parse_map_file(map_file)
                    simulator = Simulator(graph)
                    visualizer.graph = graph
                    visualizer.turn = 0
                    visualizer.set_drones(simulator.drones)
                    visualizer._compute_layout()
                    continue

                should_advance = visualizer.render(advance=advance)
                if should_advance and not simulator.all_delivered:
                    simulator.step()
                    visualizer.turn = simulator.turn
        finally:
            visualizer.close()
    else:
        simulator.run()
        for i, turn_log in enumerate(simulator.get_history(), 1):
            print(f"Turn {i}: {' '.join(turn_log)}")

    return {
        "turns": simulator.turn,
        "history": simulator.get_history(),
        "all_delivered": simulator.all_delivered,
    }


def run_cli(map_file: Path, output_file: Path | None = None) -> int:
    """Run the simulation in CLI mode and optionally save output.

    Args:
        map_file: Path to the map file.
        output_file: Optional path to save turn logs.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        graph = parse_map_file(map_file)
    except (ParseError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    simulator = Simulator(graph)
    simulator.run()

    print(f"Simulation completed in {simulator.turn} turns")
    for i, turn_log in enumerate(simulator.get_history(), 1):
        line = " ".join(turn_log)
        print(f"Turn {i}: {line}")

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            for turn_log in simulator.get_history():
                f.write(" ".join(turn_log) + "\n")
        print(f"Output saved to {output_file}")

    return 0
