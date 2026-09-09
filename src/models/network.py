#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   network.py                                           :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 17:50:50 by horarivo            #+#    #+#            #
#   Updated: 2026/09/09 11:43:21 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


from typing import Optional
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
