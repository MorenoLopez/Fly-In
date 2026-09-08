#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   zone.py                                              :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 16:28:02 by horarivo            #+#    #+#            #
#   Updated: 2026/09/08 16:39:39 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


from typing import Optional


class Zone:
    def __init__(self,
                name: str,
                x: int,
                y: int,
                zone_type: str = "normal",
                max_drones: int,
                color: Optional[str] = None):
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: str = zone_type
        self.max_drones: int = max_drones
        self.color: Optional[str] = color
        
        