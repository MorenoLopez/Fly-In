#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   algorithms.py                                        :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/09 14:41:20 by horarivo            #+#    #+#            #
#   Updated: 2026/09/09 15:39:27 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


from typing import Dict, Tuple, List
from src.models.zone import Zone


class ReservationTable:

    def __init__(self) -> None:
        self._zone_occupancy: Dict[Tuple[str, int], int] = {}
        self._edge_occupancy: Dict[Tuple[Tuple[str, str], int], int] = {}

    def _get_canonical_edge(self, zone_a_name: str, zone_b_name: str) -> Tuple[str, str]:
        if zone_a_name < zone_b_name:
            return (zone_a_name, zone_b_name)
        return (zone_b_name, zone_a_name)

    def is_zone_available(self, zone: Zone, turn: int) -> bool:
        if zone.is_start or zone.is_end:
            return True

        current_count = self._zone_occupancy.get((zone.name, turn), 0)
        return current_count < zone.max_drones

    def is_connection_available(
        self, zone_a: Zone, zone_b: Zone, turn: int, max_capacity: int
    ) -> bool:
        edge = self._get_canonical_edge(zone_a.name, zone_b.name)

        if self._edge_occupancy.get((edge, turn), 0) >= max_capacity:
            return False

        if zone_b.zone_type == "restricted":
            if self._edge_occupancy.get((edge, turn + 1), 0) >= max_capacity:
                return False

        return True

    def reserve_zone(self, zone_name: str, turn: int) -> None:
        key = (zone_name, turn)
        self._zone_occupancy[key] = self._zone_occupancy.get(key, 0) + 1

    def reserve_connection(self, zone_a_name: str, zone_b_name: str, turn: int) -> None:
        edge = self._get_canonical_edge(zone_a_name, zone_b_name)
        key = (edge, turn)
        self._edge_occupancy[key] = self._edge_occupancy.get(key, 0) + 1

    def reserve_path(self, timed_path: List[Tuple[Zone, int]]) -> None:
        start_zone, start_turn = timed_path[0]
        self.reserve_zone(start_zone.name, start_turn)

        for i in range(len(timed_path) - 1):
            curr_zone, curr_turn = timed_path[i]
            next_zone, next_turn = timed_path[i + 1]

            if curr_zone.name == next_zone.name:
                self.reserve_zone(curr_zone.name, next_turn)

            elif next_zone.zone_type == "restricted":
                self.reserve_connection(curr_zone.name, next_zone.name, curr_turn)
                self.reserve_connection(curr_zone.name, next_zone.name, curr_turn + 1)
                self.reserve_zone(next_zone.name, next_turn)

            else:
                self.reserve_connection(curr_zone.name, next_zone.name, curr_turn)
                self.reserve_zone(next_zone.name, next_turn)