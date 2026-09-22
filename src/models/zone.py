#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   zone.py                                              :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 16:28:02 by horarivo            #+#    #+#            #
#   Updated: 2026/09/22 11:29:45 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


"""A single zone in the drone network."""

from typing import Optional


class Zone:
    """A zone with a position, a type, a capacity, and a color."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: str = "normal",
        max_drones: int = 1,
        color: Optional[str] = None,
    ) -> None:
        """Create a zone with its name, coordinates, type and capacity."""
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.max_drones = max_drones
        self.color = color
        self.is_start: bool = False
        self.is_end: bool = False
