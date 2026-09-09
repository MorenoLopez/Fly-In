#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   connection.py                                        :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 16:45:35 by horarivo            #+#    #+#            #
#   Updated: 2026/09/09 11:50:38 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from typing import Optional
from src.models.zone import Zone


class Connection:
    def __init__(self, zone1: Zone, zone2: Zone, capacity: int = 1) -> None:
        self.zone1 = zone1
        self.zone2 = zone2
        self.capacity = capacity
        