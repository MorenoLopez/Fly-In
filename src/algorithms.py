#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   algorithms.py                                        :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/09 14:41:20 by horarivo            #+#    #+#            #
#   Updated: 2026/09/16 14:51:54 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


from models.drone import Drone
import heapq
from models.network import Network
from typing import Dict, Tuple, List, Optional
from models.zone import Zone


class ReservationTable:
    def __init__(self) -> None:
        self._zone_occupancy: Dict[Tuple[str, int], int] = {}
        self._edge_occupancy: Dict[Tuple[Tuple[str, str], int], int] = {}

    def _get_canonical_edge(
        self, zone_a_name: str, zone_b_name: str
    ) -> Tuple[str, str]:
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

    def reserve_connection(
        self, zone_a_name: str, zone_b_name: str, turn: int
    ) -> None:
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
                self.reserve_connection(
                    curr_zone.name, next_zone.name, curr_turn
                )
                self.reserve_connection(
                    curr_zone.name, next_zone.name, curr_turn + 1
                )
                self.reserve_zone(next_zone.name, next_turn)

            else:
                self.reserve_connection(
                    curr_zone.name, next_zone.name, curr_turn
                )
                self.reserve_zone(next_zone.name, next_turn)

    def zone_occupancy_at(self, turn: int) -> Dict[str, int]:
        """
        Return {zone_name: count} for every zone occupied at the given turn
        """
        return {
            zone_name: count
            for (zone_name, t), count in self._zone_occupancy.items()
            if t == turn
        }

    def edge_occupancy_at(self, turn: int) -> Dict[Tuple[str, str], int]:
        """
        Return {canonical_edge: count} for every conn used at the given turn
        """
        return {
            edge: count
            for (edge, t), count in self._edge_occupancy.items()
            if t == turn
        }


class PathFinder:
    def __init__(self, network: Network) -> None:
        self._network = network
        self._zones_by_name: Dict[str, Zone] = {
            z.name: z for z in network.zones
        }

    def find_path(
        self,
        reservation_table: ReservationTable,
        start_zone: Zone,
        end_zone: Zone,
        start_turn: int,
    ) -> Optional[List[Tuple[Zone, int]]]:
        max_turn = start_turn + len(self._network.zones) * 4

        priority_queue: List[Tuple[int, str, int]] = []
        heapq.heappush(priority_queue, (0, start_zone.name, start_turn))

        best_cost: Dict[tuple[str, int], int] = {}
        best_cost[(start_zone.name, start_turn)] = 0

        predecessor: Dict[Tuple[str, int], Tuple[Zone, int]] = {}

        while priority_queue:
            cost, curr_zone_name, curr_turn = heapq.heappop(priority_queue)
            curr_zone = self._zones_by_name[curr_zone_name]

            if curr_zone.name == end_zone.name:
                return self._reconstruct_path(
                    predecessor, curr_zone, curr_turn, start_zone, start_turn
                )

            if cost > best_cost.get((curr_zone.name, curr_turn), float("inf")):
                continue

            if curr_turn >= max_turn:
                continue

            next_turn = curr_turn + 1
            if reservation_table.is_zone_available(curr_zone, next_turn):
                self._relax(
                    best_cost,
                    predecessor,
                    priority_queue,
                    curr_zone,
                    curr_turn,
                    curr_zone,
                    next_turn,
                    cost + 1,
                )

            for connection in self._network.connections_of(curr_zone):
                neighbor = connection.other_zone(curr_zone)

                if neighbor.zone_type == "blocked":
                    continue

                if neighbor.zone_type == "restricted":
                    arrival_turn = curr_turn + 2
                    move_cost = 2
                else:
                    arrival_turn = curr_turn + 1
                    move_cost = 1

                if not reservation_table.is_connection_available(
                    curr_zone, neighbor, curr_turn, connection.capacity
                ):
                    continue

                if not reservation_table.is_zone_available(
                    neighbor, arrival_turn
                ):
                    continue

                self._relax(
                    best_cost,
                    predecessor,
                    priority_queue,
                    curr_zone,
                    curr_turn,
                    neighbor,
                    arrival_turn,
                    cost + move_cost,
                )

        return None

    def _relax(
        self,
        best_cost: Dict[Tuple[str, int], int],
        predecessor: Dict[Tuple[str, int], Tuple[Zone, int]],
        priority_queue: List[Tuple[int, str, int]],
        from_zone: Zone,
        from_turn: int,
        to_zone: Zone,
        to_turn: int,
        new_cost: int,
    ) -> None:
        key = (to_zone.name, to_turn)
        if new_cost < best_cost.get(key, float("inf")):
            best_cost[key] = new_cost
            predecessor[key] = (from_zone, from_turn)
            heapq.heappush(priority_queue, (new_cost, to_zone.name, to_turn))

    def _reconstruct_path(
        self,
        predecessor: Dict[Tuple[str, int], Tuple[Zone, int]],
        end_zone: Zone,
        end_turn: int,
        start_zone: Zone,
        start_turn: int,
    ) -> List[Tuple[Zone, int]]:
        path: List[Tuple[Zone, int]] = [(end_zone, end_turn)]
        curr_key = (end_zone.name, end_turn)

        while curr_key != (start_zone.name, start_turn):
            prev_zone, prev_turn = predecessor[curr_key]
            path.append((prev_zone, prev_turn))
            curr_key = (prev_zone.name, prev_turn)

        path.reverse()
        return path


class RoutingError(Exception):
    def __init__(self, drone_id: str, message: str) -> None:
        self.drone_id = drone_id
        self.message = message
        super().__init__(f"Drone {drone_id}: {message}")


class RoutingManager:

    def __init__(
        self, pathfinder: PathFinder, reservation_table: ReservationTable
    ) -> None:
        self._pathfinder = pathfinder
        self._reservation_table = reservation_table

    def route_all_drones(
        self,
        drones: List[Drone],
        start_zone: Zone,
        end_zone: Zone,
    ) -> Dict[str, List[Tuple[Zone, int]]]:

        sorted_drones = sorted(drones, key=lambda d: d.id)

        routes: Dict[str, List[Tuple[Zone, int]]] = {}

        for drone in sorted_drones:
            timed_path = self._pathfinder.find_path(
                self._reservation_table,
                start_zone,
                end_zone,
                start_turn=0,
            )

            if timed_path is None:
                raise RoutingError(drone.id, "no valid path found")

            self._reservation_table.reserve_path(timed_path)
            routes[drone.id] = timed_path

        return routes
