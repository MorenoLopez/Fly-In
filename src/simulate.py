#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   simulate.py                                          :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/15 14:24:19 by horarivo            #+#    #+#            #
#   Updated: 2026/09/22 11:44:05 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


"""Turns computed drone routes into turn-by-turn text output."""

from typing import Dict, List, Tuple
from models.zone import Zone
from algorithms import ReservationTable
from models.network import Network


class SimulationEngine:
    """Converts drone routes into the required text output format."""

    def __init__(
        self,
        routes: Dict[str, List[Tuple[Zone, int]]],
        network: Network,
        reservation_table: ReservationTable,
    ) -> None:
        """Store the routes, network and reservation table."""
        self._routes = routes
        self._network = network
        self._reservation_table = reservation_table

    def generate_turns(self) -> List[str]:
        """Return the simulation output as one line per turn."""
        turn_actions = self._build_turn_actions()
        max_turn = max(turn_actions.keys())
        verbose: bool = False

        lines = []
        for turn in range(1, max_turn + 1):
            actions = turn_actions.get(turn, [])
            if actions:
                lines.append(" ".join(actions))

                if verbose:
                    lines.extend(self._build_info(turn))

        return lines

    def _build_turn_actions(self) -> Dict[int, List[str]]:
        """Group every drone's moves by the turn they happen on."""
        turn_actions: Dict[int, List[str]] = {}

        for drone_id, timed_path in self._routes.items():
            for i in range(len(timed_path) - 1):
                curr_zone, curr_turn = timed_path[i]
                next_zone, next_turn = timed_path[i + 1]

                if curr_zone.name == next_zone.name:
                    continue

                elif next_turn == curr_turn + 2:
                    connection_name = f"{curr_zone.name}-{next_zone.name}"
                    turn_actions.setdefault(curr_turn + 1, []).append(
                        f"{drone_id}-{connection_name}"
                    )
                    turn_actions.setdefault(next_turn, []).append(
                        f"{drone_id}-{next_zone.name}"
                    )

                else:
                    turn_actions.setdefault(next_turn, []).append(
                        f"{drone_id}-{next_zone.name}"
                    )
        return turn_actions

    def _build_info(self, turn: int) -> List[str]:
        """Return extra per-turn zone/connection occupancy info lines."""
        lines = []

        zone_counts = self._reservation_table.zone_occupancy_at(turn)
        for zone_name, count in zone_counts.items():
            zone = self._network.get_zone_by_name(zone_name)
            lines.append(
                f"  Zone {zone_name}: {count}/{zone.max_drones} drones"
            )

        edge_counts = self._reservation_table.edge_occupancy_at(turn)
        for (zone_a, zone_b), count in edge_counts.items():
            connection = self._network.get_connection_by_names(zone_a, zone_b)
            lines.append(
                f"  Connection {zone_a}-{zone_b}: "
                f"{count}/{connection.capacity} capacity used"
            )

        return lines
