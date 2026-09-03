#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   drone.py                                             :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/02 20:35:35 by horarivo            #+#    #+#            #
#   Updated: 2026/09/02 20:39:11 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

"""Drone model representing a single drone in the simulation"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Drone:
    """Represents a drone in the simulation

    Attributes:
        drone_id: Unique identifier for the drone
        current_zone: Name of the zone where the drone currently is
        path: List of zone names representing the planned route
        path_index: Current position along the path
        in_transit: Whether the drone is currently moving between zones
        transit_connection: The connection being traversed (for restricted zones)
        transit_remaining: Turns remaining to complete transit
        delivered: Whether the drone has reached the end zone
    """

    drone_id: int
    current_zone: str
    path: list[str] = field(default_factory=list)
    path_index: int = 0
    in_transit: bool = False
    transit_connection: Optional[str] = None
    transit_remaining: int = 0
    delivered: bool = False

    def next_zone(self) -> Optional[str]:
        """Return the next zone in the planned path

        Returns:
            The next zone name or None if at the end
        """
        if self.path_index + 1 < len(self.path):
            return self.path[self.path_index + 1]
        return None

    def advance(self) -> None:
        """
            Move to the next zone in the path
        """
        if self.path_index + 1 < len(self.path):
            self.path_index += 1
            self.current_zone = self.path[self.path_index]

    def start_transit(self, connection_name: str, cost: int) -> None:
        """Begin transit on a connection

        Args:
            connection_name: Name of the connection being traversed
            cost: Number of turns required to complete transit
        """
        self.in_transit = True
        self.transit_connection = connection_name
        self.transit_remaining = cost - 1

    def tick_transit(self) -> bool:
        """Decrement transit timer

        Returns:
            True if transit is complete
        """
        if self.transit_remaining > 0:
            self.transit_remaining -= 1
            return False
        self.in_transit = False
        self.transit_connection = None
        return True
