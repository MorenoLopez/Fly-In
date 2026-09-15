#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   network.py                                           :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 17:50:50 by horarivo            #+#    #+#            #
#   Updated: 2026/09/15 10:40:44 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


from typing import Optional, List
from src.models.drone import Drone
from src.models.connection import Connection
from src.models.zone import Zone


class Network:
    def __init__(self) -> None:
        self.zones: list[Zone] = []
        self.connections: list[Connection] = []
        self.drones: list[Drone] = []
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None


    def connections_of(self, zone: Zone) -> List[Connection]:
            return [
                c for c in self.connections
                if c.zone1.name == zone.name or c.zone2.name == zone.name
            ]