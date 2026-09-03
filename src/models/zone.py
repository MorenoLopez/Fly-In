#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   zone.py                                              :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/02 20:43:59 by horarivo            #+#    #+#            #
#   Updated: 2026/09/02 20:44:50 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

"""Zone model representing a node in the drone network."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Zone:
    """Represents a zone (node) in the drone routing graph.

    Attributes:
        name: Unique identifier for the zone.
        x: X coordinate for visualization.
        y: Y coordinate for visualization.
        zone_type: Type of zone (normal, blocked, restricted, priority).
        color: Optional color string for visualization.
        max_drones: Maximum number of drones allowed in this zone.
        is_start: Whether this is the start zone.
        is_end: Whether this is the end zone.
        current_drones: Set of drone IDs currently occupying the zone.
    """

    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: Optional[str] = None
    max_drones: int = 1
    is_start: bool = False
    is_end: bool = False
    current_drones: set[int] = field(default_factory=set)

    def movement_cost(self) -> int:
        """Return the turn cost to enter this zone.

        Returns:
            Cost in turns (1 for normal/priority, 2 for restricted).
            Blocked zones return a very high cost.
        """
        costs = {"normal": 1, "priority": 1, "restricted": 2, "blocked": 9999}
        return costs.get(self.zone_type, 1)

    def can_enter(self, drone_id: int) -> bool:
        """Check if a drone can enter this zone.

        Args:
            drone_id: The ID of the drone trying to enter.

        Returns:
            True if the zone has capacity or the drone is already there.
        """
        if self.zone_type == "blocked":
            return False
        if self.is_start or self.is_end:
            return True
        if drone_id in self.current_drones:
            return True
        return len(self.current_drones) < self.max_drones

    def enter(self, drone_id: int) -> None:
        """Add a drone to this zone.

        Args:
            drone_id: The drone ID to add.
        """
        self.current_drones.add(drone_id)

    def leave(self, drone_id: int) -> None:
        """Remove a drone from this zone.

        Args:
            drone_id: The drone ID to remove.
        """
        self.current_drones.discard(drone_id)

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Zone):
            return NotImplemented
        return self.name == other.name
