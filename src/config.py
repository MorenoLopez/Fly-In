#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   config.py                                            :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/02 20:31:38 by horarivo            #+#    #+#            #
#   Updated: 2026/09/02 20:32:45 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

"""Project configuration and constants."""

from pathlib import Path
from typing import Final

DEFAULT_MAP_FILE: Final[Path] = Path("data/maps/easy_linear.txt")
DEFAULT_OUTPUT_DIR: Final[Path] = Path("data/output")
SCREEN_WIDTH: Final[int] = 1200
SCREEN_HEIGHT: Final[int] = 800
FPS: Final[int] = 30
NODE_RADIUS: Final[int] = 26
DRONE_RADIUS: Final[int] = 9

# Layout margins reserved around the graph so it never collides with the
# top/bottom UI panels, regardless of the coordinate range used in map files.
TOP_MARGIN: Final[int] = 110
BOTTOM_MARGIN: Final[int] = 70
SIDE_MARGIN: Final[int] = 90
MAX_LAYOUT_SCALE: Final[float] = 160.0
MIN_LAYOUT_SCALE: Final[float] = 8.0

COLORS: Final[dict[str, tuple[int, int, int]]] = {
    "normal": (94, 138, 227),
    "blocked": (107, 114, 128),
    "restricted": (231, 76, 90),
    "priority": (46, 196, 132),
    "start": (255, 196, 61),
    "end": (255, 138, 61),
    "drone": (32, 201, 214),
    "drone_transit": (236, 96, 172),
    "background": (18, 21, 30),
    "background_alt": (24, 28, 40),
    "text": (235, 238, 245),
    "text_dim": (150, 158, 176),
    "edge": (76, 84, 104),
    "edge_full": (231, 76, 90),
    "panel_bg": (28, 32, 46),
    "panel_border": (52, 58, 78),
    "node_border": (12, 14, 20),
    "shadow": (0, 0, 0),
}