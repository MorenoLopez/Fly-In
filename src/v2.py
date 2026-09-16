#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   v2.py                                                :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/16 07:45:52 by horarivo            #+#    #+#            #
#   Updated: 2026/09/16 07:52:23 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


"""Graphical (Arcade-based) visualizer for the Fly-in drone simulation."""

import os
from typing import Dict, List, Tuple, Optional
import arcade
from models.network import Network
from models.zone import Zone


MARGIN = 80
ZONE_RADIUS = 22
SECONDS_PER_TURN = 1.0
DRONE_ANIM_FPS = 8

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
_BG_PATH = os.path.join(_ASSETS_DIR, "bg.jpeg")
_DRONE_SHEET_PATH = os.path.join(_ASSETS_DIR, "Idle2.png")
_DRONE_SHEET_COLUMNS = 4

_DEFAULT_COLOR = arcade.color.LIGHT_GRAY
_ZONE_TYPE_OUTLINE = {
    "normal": arcade.color.WHITE,
    "priority": arcade.color.GOLD,
    "restricted": arcade.color.ORANGE_RED,
    "blocked": arcade.color.DARK_GRAY,
}


class Visualizer(arcade.Window):  # type: ignore[misc]
    """Arcade window that renders the drone network and animates drone movement."""

    def __init__(
        self,
        network: Network,
        routes: Dict[str, List[Tuple[Zone, int]]],
    ) -> None:
        """Build the visualizer window, load assets and precompute layout.

        Args:
            network: The parsed map (zones and connections) to display.
            routes: Mapping of drone id to its timed path, as produced by
                RoutingManager.route_all_drones.
        """
        screen_w, screen_h = arcade.get_display_size()
        window_w = int(screen_w * 0.85)
        window_h = int(screen_h * 0.85)

        super().__init__(window_w, window_h, "Fly-in Simulation", resizable=True)

        self._network = network
        self._routes = routes
        self._max_turn = max(
            (t for path in routes.values() for _, t in path), default=0
        )

        self._bg_texture: Optional[arcade.Texture] = self._safe_load_texture(_BG_PATH)
        self._drone_textures: List[arcade.Texture] = self._safe_load_spritesheet(
            _DRONE_SHEET_PATH, columns=_DRONE_SHEET_COLUMNS
        )
        self._anim_timer: float = 0.0

        self._positions: Dict[str, Tuple[float, float]] = (
            self._compute_screen_positions()
        )

        self._current_turn: float = 0.0
        self._playing: bool = True

    def _safe_load_texture(self, path: str) -> Optional[arcade.Texture]:
        """Load a texture from disk, returning None (with a warning) on failure."""
        try:
            return arcade.load_texture(path)
        except (FileNotFoundError, OSError) as e:
            print(f"Warning: could not load texture {path!r}: {e}")
            return None

    def _safe_load_spritesheet(self, path: str, columns: int) -> List[arcade.Texture]:
        """Load a horizontal spritesheet as a list of frame textures.

        Falls back to an empty list (drones drawn as plain circles) if the
        file is missing or malformed.
        """
        try:
            base_tex = arcade.load_texture(path)
        except (FileNotFoundError, OSError) as e:
            print(f"Warning: could not load spritesheet {path!r}: {e}")
            return []

        frame_w = base_tex.width // columns
        frame_h = base_tex.height
        textures: List[arcade.Texture] = []

        for col in range(columns):
            try:
                frame = base_tex.crop(col * frame_w, 0, frame_w, frame_h)
            except (ValueError, IndexError) as e:
                print(f"Warning: could not extract frame {col} from {path!r}: {e}")
                continue
            textures.append(frame)

        return textures

    def _compute_screen_positions(self) -> Dict[str, Tuple[float, float]]:
        """Map each zone's (x, y) map coordinate to a screen pixel position."""
        xs = [z.x for z in self._network.zones]
        ys = [z.y for z in self._network.zones]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        span_x = max(max_x - min_x, 1)
        span_y = max(max_y - min_y, 1)

        usable_w = self.width - 2 * MARGIN
        usable_h = self.height - 2 * MARGIN

        positions: Dict[str, Tuple[float, float]] = {}
        for zone in self._network.zones:
            sx = MARGIN + (zone.x - min_x) / span_x * usable_w
            sy = MARGIN + (zone.y - min_y) / span_y * usable_h
            positions[zone.name] = (sx, sy)

        return positions

    def on_resize(self, width: int, height: int) -> None:
        """Recompute zone layout when the window is resized."""
        super().on_resize(width, height)
        if hasattr(self, "_network"):
            self._positions = self._compute_screen_positions()

    def _zone_at(self, drone_id: str, turn_int: int) -> Zone:
        """Return the zone a given drone occupies at or before a given turn."""
        path = self._routes[drone_id]
        current_zone = path[0][0]
        for zone, t in path:
            if t <= turn_int:
                current_zone = zone
            else:
                break
        return current_zone

    def _drone_screen_position(self, drone_id: str) -> Tuple[float, float]:
        """Return the interpolated screen position of a drone at the current turn."""
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

    def _draw_background(self) -> None:
        """Draw the background texture, or a plain fill if it failed to load."""
        if self._bg_texture is not None:
            arcade.draw_texture_rect(
                self._bg_texture,
                arcade.XYWH(self.width / 2, self.height / 2, self.width, self.height),
            )
        else:
            arcade.draw_lbwh_rectangle_filled(
                0, 0, self.width, self.height, arcade.color.DARK_SLATE_GRAY
            )

    def _draw_connections(self) -> None:
        """Draw a line for every connection in the network."""
        for connection in self._network.connections:
            x1, y1 = self._positions[connection.zone1.name]
            x2, y2 = self._positions[connection.zone2.name]
            arcade.draw_line(x1, y1, x2, y2, arcade.color.LIGHT_STEEL_BLUE, 2)

    def _draw_zones(self) -> None:
        """Draw every zone as a colored, outlined circle with its name."""
        for zone in self._network.zones:
            x, y = self._positions[zone.name]
            fill_color = arcade.color.DARK_BLUE_GRAY
            if zone.color:
                fill_color = getattr(arcade.color, zone.color.upper(), _DEFAULT_COLOR)

            outline_color = _ZONE_TYPE_OUTLINE.get(zone.zone_type, arcade.color.WHITE)

            arcade.draw_circle_filled(x, y, ZONE_RADIUS, fill_color)
            arcade.draw_circle_outline(x, y, ZONE_RADIUS, outline_color, 3)
            arcade.draw_text(
                zone.name, x, y + ZONE_RADIUS + 4,
                arcade.color.WHITE, 12, anchor_x="center", bold=True,
            )

    def _draw_drones(self) -> None:
        """Draw every drone at its current interpolated position."""
        current_drone_tex: Optional[arcade.Texture] = None
        if self._drone_textures:
            frame_idx = int(self._anim_timer * DRONE_ANIM_FPS) % len(
                self._drone_textures
            )
            current_drone_tex = self._drone_textures[frame_idx]

        for drone_id in sorted(self._routes.keys()):
            x, y = self._drone_screen_position(drone_id)

            if current_drone_tex is not None:
                arcade.draw_texture_rect(
                    current_drone_tex,
                    arcade.XYWH(
                        x, y,
                        current_drone_tex.width * 1.5,
                        current_drone_tex.height * 1.5,
                    ),
                )
                label_y = y - (current_drone_tex.height * 0.75) - 14
            else:
                arcade.draw_circle_filled(x, y, 10, arcade.color.ELECTRIC_CYAN)
                label_y = y - 24

            arcade.draw_text(
                drone_id, x, label_y,
                arcade.color.ELECTRIC_CYAN, 11, anchor_x="center", bold=True,
            )

    def _draw_hud(self) -> None:
        """Draw the turn counter, play state and control hints."""
        arcade.draw_text(
            f"Turn: {int(self._current_turn)} / {self._max_turn}"
            f"  {'[PLAYING]' if self._playing else '[PAUSED]'}"
            "   (SPACE=play/pause, RIGHT=step, ESC=quit)",
            10, self.height - 25, arcade.color.WHITE, 14,
        )

    def on_draw(self) -> None:
        """Render one full frame: background, connections, zones, drones, HUD."""
        self.clear()
        self._draw_background()
        self._draw_connections()
        self._draw_zones()
        self._draw_drones()
        self._draw_hud()

    def on_update(self, delta_time: float) -> None:
        """Advance the animation clock and, if playing, the simulation turn."""
        self._anim_timer += delta_time
        if self._playing and self._current_turn < self._max_turn:
            self._current_turn += delta_time / SECONDS_PER_TURN
            if self._current_turn > self._max_turn:
                self._current_turn = float(self._max_turn)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Handle playback controls: play/pause, step, quit."""
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
    """Create and run the graphical visualizer until the window is closed."""
    Visualizer(network, routes)
    arcade.run()
