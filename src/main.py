#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   main.py                                              :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 16:15:20 by horarivo            #+#    #+#            #
#   Updated: 2026/09/15 11:35:12 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


import sys
from src.parser import Parser
from src.algorithms import PathFinder, ReservationTable, RoutingManager


def main() -> None:
    parsedmap = Parser().parse(sys.argv[2])

    assert parsedmap.start_zone is not None, "start_zone should never be None after parsing"
    assert parsedmap.end_zone is not None, "end_zone should never be None after parsing"

    print(f"nb_drones: {len(parsedmap.drones)}")
    print(f"zones: {[z.name for z in parsedmap.zones]}")
    print(f"connections: {[(c.zone1.name, c.zone2.name) for c in parsedmap.connections]}")
    print(f"start: {parsedmap.start_zone.name}, end: {parsedmap.end_zone.name}")

    pathfinder = PathFinder(parsedmap)
    reservation_table = ReservationTable()
    manager = RoutingManager(pathfinder, reservation_table)

    routes = manager.route_all_drones(
        parsedmap.drones, parsedmap.start_zone, parsedmap.end_zone
    )

    for drone_id, timed_path in routes.items():
        path_str = " -> ".join(f"{zone.name}@t{turn}" for zone, turn in timed_path)
        print(f"{drone_id}: {path_str}")


if __name__ == "__main__":
    main()