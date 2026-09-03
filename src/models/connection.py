#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   connection.py                                        :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/02 20:46:30 by horarivo            #+#    #+#            #
#   Updated: 2026/09/02 20:47:51 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

"""Connection model representing an edge between two zones."""

from dataclasses import dataclass, field


@dataclass
class Connection:
    """Represents a bidirectional connection between two zones.

    Attributes:
        zone_a: Name of the first zone.
        zone_b: Name of the second zone.
        max_link_capacity: Maximum drones that can traverse simultaneously.
        current_transit: Number of drones currently in transit on this link.
    """

    zone_a: str
    zone_b: str
    max_link_capacity: int = 1
    current_transit: int = 0

    def can_traverse(self) -> bool:
        """Check if the connection has available capacity.

        Returns:
            True if more drones can traverse this connection.
        """
        return self.current_transit < self.max_link_capacity

    def add_transit(self) -> None:
        """Increment the transit counter."""
        self.current_transit += 1

    def remove_transit(self) -> None:
        """Decrement the transit counter."""
        self.current_transit = max(0, self.current_transit - 1)

    def other_end(self, zone_name: str) -> str:
        """Return the zone name at the other end of this connection.

        Args:
            zone_name: The zone name to start from.

        Returns:
            The name of the connected zone.
        """
        if zone_name == self.zone_a:
            return self.zone_b
        return self.zone_a
