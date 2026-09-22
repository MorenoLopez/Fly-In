#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   drone.py                                             :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 16:14:47 by horarivo            #+#    #+#            #
#   Updated: 2026/09/22 11:37:49 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

"""A single drone being routed through the network."""

from models.zone import Zone


class Drone:
    """A drone identified by an id, tracking its current zone."""

    def __init__(self, id: str, curr_zone: Zone) -> None:
        """Create a drone starting at the given zone."""
        self.id = id
        self.curr_zone = curr_zone
        self.is_delivered: bool = False
