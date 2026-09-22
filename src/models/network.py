#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   network.py                                           :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 17:50:50 by horarivo            #+#    #+#            #
#   Updated: 2026/09/22 11:42:15 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


"""The full network of zones, connections and drones."""

from typing import Optional, List
from models.drone import Drone
from models.connection import Connection
from models.zone import Zone


class Network:
    """Holds all zones, connections, drones, and the start/end zones."""

    def __init__(self) -> None:
        """Create an empty network."""
        self.zones: list[Zone] = []
        self.connections: list[Connection] = []
        self.drones: list[Drone] = []
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None

    def connections_of(self, zone: Zone) -> List[Connection]:
        """Return all connections attached to the given zone."""
        return [
            c
            for c in self.connections
            if c.zone1.name == zone.name or c.zone2.name == zone.name
        ]

    def get_zone_by_name(self, name: str) -> Zone:
        """Return the zone with the given name."""
        for zone in self.zones:
            if zone.name == name:
                return zone
        raise KeyError(f"No zone named {name!r} in network")

    def get_connection_by_names(
        self, zone_a_name: str, zone_b_name: str
    ) -> Connection:
        """Return the connection between two named zones."""
        for connection in self.connections:
            names = {connection.zone1.name, connection.zone2.name}
            if names == {zone_a_name, zone_b_name}:
                return connection
        raise KeyError(
            f"No connection between {zone_a_name!r} and {zone_b_name!r}"
        )
