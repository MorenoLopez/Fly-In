#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   connection.py                                        :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 16:45:35 by horarivo            #+#    #+#            #
#   Updated: 2026/09/15 15:36:50 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

from models.zone import Zone


class Connection:
    def __init__(self, zone1: Zone, zone2: Zone, capacity: int = 1) -> None:
        self.zone1 = zone1
        self.zone2 = zone2
        self.capacity = capacity

    def other_zone(self, zone: Zone) -> Zone:
        if zone.name == self.zone1.name:
            return self.zone2
        return self.zone1
