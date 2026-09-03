#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   mapgraph.py                                          :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/02 20:52:09 by horarivo            #+#    #+#            #
#   Updated: 2026/09/02 20:54:15 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

"""MapGraph model representing the entire drone network"""

from typing import Optional

from src.models.zone import Zone
from src.models.connection import Connection


class MapGraph:
    """Represents the entire drone routing network

    Attributes:
        zones: Dictionary mapping zone names to Zone objects
        connections: Dictionary mapping zone names to list of Connections
        start_zone: Name of the start zone
        end_zone: Name of the end zone
        num_drones: Total number of drones to route
    """

    def __init__(self) -> None:
        self.zones: dict[str, Zone] = {}
        self.connections: dict[str, list[Connection]] = {}
        self.start_zone: Optional[str] = None
        self.end_zone: Optional[str] = None
        self.num_drones: int = 0

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the graph

        Args:
            zone: The Zone object to add
        """
        self.zones[zone.name] = zone
        self.connections.setdefault(zone.name, [])

    def add_connection(self, conn: Connection) -> None:
        """Add a bidirectional connection to the graph

        Args:
            conn: The Connection object to add
        """
        self.connections.setdefault(conn.zone_a, []).append(conn)
        self.connections.setdefault(conn.zone_b, []).append(conn)

    def get_zone(self, name: str) -> Optional[Zone]:
        """Retrieve a zone by name

        Args:
            name: The zone name

        Returns:
            The Zone object or None
        """
        return self.zones.get(name)

    def get_neighbors(self, zone_name: str) -> list[Connection]:
        """Get all connections from a zone

        Args:
            zone_name: The zone name

        Returns:
            List of Connection objects
        """
        return self.connections.get(zone_name, [])

    def get_connection(self, a: str, b: str) -> Optional[Connection]:
        """Find the connection between two zones

        Args:
            a: First zone name
            b: Second zone name

        Returns:
            The Connection object or None
        """
        for conn in self.connections.get(a, []):
            if conn.zone_a == b or conn.zone_b == b:
                return conn
        return None
