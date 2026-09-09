#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   zone.py                                              :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 16:28:02 by horarivo            #+#    #+#            #
#   Updated: 2026/09/09 11:51:10 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


from typing import Optional


class Zone:
    def __init__(self,
                name: str,
                x: int,
                y: int,
                zone_type: str = "normal",
                max_drones: int = 1,
                color: Optional[str] = None
                ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.max_drones = max_drones
        self.color = color
        
        