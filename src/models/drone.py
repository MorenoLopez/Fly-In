#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   drone.py                                             :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 16:14:47 by horarivo            #+#    #+#            #
#   Updated: 2026/09/15 15:29:47 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


from models.zone import Zone


class Drone:
    def __init__(self, id: str, curr_zone: Zone) -> None:
        self.id = id
        self.curr_zone = curr_zone
        self.is_delivered: bool = False
