#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   visualizer.py                                        :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/15 15:56:36 by horarivo            #+#    #+#            #
#   Updated: 2026/09/15 16:28:34 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

import arcade
from typing import Dict, List, Tuple
from models.network import Network
from models.zone import Zone

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 400
MARGIN = 80
ZONE_RADIUS = 22
DRONE_RADIUS = 10
SECONDS_PER_TURN = 1.0

_DEFAULT_COLOR = arcade.color.LIGHT_GRAY
_ZONE_TYPE_OUTLINE = {
    "normal": arcade.color.WHITE,
    "priority": arcade.color.GOLD,
    "restricted": arcade.color.ORANGE_RED,
    "blocked": arcade.color.DARK_GRAY,
}
_DRONE_COLORS = [
    arcade.color.BLUE,
    arcade.color.RED,
    arcade.color.GREEN,
    arcade.color.PURPLE,
    arcade.color.CYAN,
    arcade.color.MAGENTA,
    arcade.color.YELLOW,
    arcade.color.PINK,
]


class Visualizer(arcade.Window):  # type: ignore[misc]
    def __init__(
        self,
        network: Network,
        routes: Dict[str, List[Tuple[Zone, int]]],
    ) -> None:
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Fly-in Simulation")
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        self._network = network
        self._routes = routes
        self._max_turn = max(t for path in routes.values() for _, t in path)

        self._positions: Dict[str, Tuple[float, float]] = (
            self._compute_screen_positions()
        )

        self._current_turn: float = 0.0
        self._playing: bool = True

    def _compute_screen_positions(self) -> Dict[str, Tuple[float, float]]:
        xs = [z.x for z in self._network.zones]
        ys = [z.y for z in self._network.zones]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        span_x = max(max_x - min_x, 1)
        span_y = max(max_y - min_y, 1)

        usable_w = WINDOW_WIDTH - 2 * MARGIN
        usable_h = WINDOW_HEIGHT - 2 * MARGIN

        positions: Dict[str, Tuple[float, float]] = {}
        for zone in self._network.zones:
            sx = MARGIN + (zone.x - min_x) / span_x * usable_w
            sy = MARGIN + (zone.y - min_y) / span_y * usable_h
            positions[zone.name] = (sx, sy)

        return positions

    def _zone_at(self, drone_id: str, turn_int: int) -> Zone:
        path = self._routes[drone_id]
        for zone, t in path:
            if t == turn_int:
                return zone
        return path[-1][0]

    def _drone_screen_position(self, drone_id: str) -> Tuple[float, float]:
        turn_floor = int(self._current_turn)
        turn_ceil = min(turn_floor + 1, self._max_turn)
        progress = self._current_turn - turn_floor

        zone_a = self._zone_at(drone_id, turn_floor)
        zone_b = self._zone_at(drone_id, turn_ceil)

        ax, ay = self._positions[zone_a.name]
        bx, by = self._positions[zone_b.name]

        x = ax + (bx - ax) * progress
        y = ay + (by - ay) * progress
        return x, y

    def on_draw(self) -> None:
        self.clear()

        for connection in self._network.connections:
            x1, y1 = self._positions[connection.zone1.name]
            x2, y2 = self._positions[connection.zone2.name]
            arcade.draw_line(x1, y1, x2, y2, arcade.color.GRAY, 2)

        for zone in self._network.zones:
            x, y = self._positions[zone.name]
            fill_color = arcade.color.WHITE
            if zone.color:
                try:
                    fill_color = getattr(
                        arcade.color, zone.color.upper(), _DEFAULT_COLOR
                    )
                except AttributeError:
                    fill_color = _DEFAULT_COLOR

            outline_color = _ZONE_TYPE_OUTLINE.get(zone.zone_type, arcade.color.WHITE)

            arcade.draw_circle_filled(x, y, ZONE_RADIUS, fill_color)
            arcade.draw_circle_outline(x, y, ZONE_RADIUS, outline_color, 3)
            arcade.draw_text(
                zone.name,
                x,
                y + ZONE_RADIUS + 4,
                arcade.color.WHITE,
                12,
                anchor_x="center",
            )

        for i, drone_id in enumerate(sorted(self._routes.keys())):
            x, y = self._drone_screen_position(drone_id)
            color = _DRONE_COLORS[i % len(_DRONE_COLORS)]
            arcade.draw_circle_filled(x, y, DRONE_RADIUS, color)
            arcade.draw_text(
                drone_id,
                x,
                y - DRONE_RADIUS - 14,
                arcade.color.WHITE,
                10,
                anchor_x="center",
            )

        arcade.draw_text(
            f"Turn: {int(self._current_turn)} / {self._max_turn}"
            f"  {'[PLAYING]' if self._playing else '[PAUSED]'}"
            "   (SPACE=play/pause, RIGHT=step, ESC=quit)",
            10,
            WINDOW_HEIGHT - 25,
            arcade.color.WHITE,
            14,
        )

    def on_update(self, delta_time: float) -> None:
        if self._playing and self._current_turn < self._max_turn:
            self._current_turn += delta_time / SECONDS_PER_TURN
            if self._current_turn > self._max_turn:
                self._current_turn = float(self._max_turn)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == arcade.key.SPACE:
            self._playing = not self._playing
        elif symbol == arcade.key.RIGHT:
            self._playing = False
            self._current_turn = min(self._current_turn + 1, self._max_turn)
        elif symbol == arcade.key.LEFT:
            self._playing = False
            self._current_turn = max(self._current_turn - 1, 0)
        elif symbol == arcade.key.ESCAPE:
            arcade.close_window()


def run_visualizer(network: Network, routes: Dict[str, List[Tuple[Zone, int]]]) -> None:
    Visualizer(network, routes)
    arcade.run()
