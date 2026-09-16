#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   v2.py                                                :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/16 07:45:52 by horarivo            #+#    #+#            #
#   Updated: 2026/09/16 08:57:46 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #


"""Graphical (Arcade-based) visualizer for the Fly-in drone simulation."""

import os
from typing import Dict, List, Tuple, Optional
import arcade
from arcade.application import EVENT_HANDLE_STATE
from models.network import Network
from models.zone import Zone

MARGIN = 80
ZONE_RADIUS = 22
SECONDS_PER_TURN = 1.0
DRONE_ANIM_FPS = 8
MIN_ZOOM = 0.3
MAX_ZOOM = 3.0
ZOOM_STEP = 1.1

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

_BG_PATH = os.path.join(_ASSETS_DIR, "bg.jpeg")

_DRONE_SHEET_PATH = os.path.join(_ASSETS_DIR, "Idle2.png")
_DRONE_SHEET_COLUMNS = 4

_PLATES_PATH = os.path.join(_ASSETS_DIR, "plates.png")
_PLATES_COLS, _PLATES_ROWS = 3, 2

_ITEMS_PATH = os.path.join(_ASSETS_DIR, "Items.png")
_ITEMS_COLS, _ITEMS_ROWS = 5, 2

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
        self._plates_textures: List[arcade.Texture] = self._safe_load_grid(
            _PLATES_PATH, _PLATES_COLS, _PLATES_ROWS
        )
        self._items_textures: List[arcade.Texture] = self._safe_load_grid(
            _ITEMS_PATH, _ITEMS_COLS, _ITEMS_ROWS
        )
        self._anim_timer: float = 0.0

        self._positions: Dict[str, Tuple[float, float]] = (
            self._compute_screen_positions()
        )

        self._current_turn: float = 0.0
        self._target_turn: float = 0.0
        self._playing: bool = True

        self._camera_offset_x: float = 0.0
        self._camera_offset_y: float = 0.0
        self._zoom: float = 1.0
        self._dragging: bool = False

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

    def _safe_load_grid(self, path: str, cols: int, rows: int) -> List[arcade.Texture]:
        """Load a spritesheet as a flat list of tile textures, row-major order.

        Tile index 0 is top-left, increasing left-to-right then top-to-bottom.
        Returns an empty list (caller must handle the fallback) on failure.
        """
        try:
            base_tex = arcade.load_texture(path)
        except (FileNotFoundError, OSError) as e:
            print(f"Warning: could not load spritesheet {path!r}: {e}")
            return []

        tile_w = base_tex.width // cols
        tile_h = base_tex.height // rows
        textures: List[arcade.Texture] = []

        for row in range(rows):
            for col in range(cols):
                try:
                    y_from_top = row * tile_h
                    y_from_bottom = base_tex.height - y_from_top - tile_h
                    tile = base_tex.crop(col * tile_w, y_from_bottom, tile_w, tile_h)
                except (ValueError, IndexError) as e:
                    print(
                        f"Warning: could not extract tile ({col},{row}) "
                        f"from {path!r}: {e}"
                    )
                    continue
                textures.append(tile)

        return textures

    def _tile_or_none(
        self, textures: List[arcade.Texture], index: int
    ) -> Optional[arcade.Texture]:
        """Safely fetch a tile by index, returning None if out of range."""
        if 0 <= index < len(textures):
            return textures[index]
        return None

    def _zone_texture(self, zone: Zone) -> Optional[arcade.Texture]:
        """Pick the tile texture representing a zone, based on start/end/type.

        Priority: start/end flags override zone_type. Falls back to None
        (caller draws a plain circle) if the relevant spritesheet failed
        to load or the tile index is out of range.
        """
        if zone.is_start:
            return self._tile_or_none(self._plates_textures, 0)
        if zone.is_end:
            return self._tile_or_none(self._plates_textures, 1)

        if zone.zone_type == "restricted":
            return self._tile_or_none(self._plates_textures, 2)
        if zone.zone_type == "normal":
            return self._tile_or_none(self._plates_textures, 4)
        if zone.zone_type == "priority":
            return self._tile_or_none(self._items_textures, 4)
        if zone.zone_type == "blocked":
            return self._tile_or_none(self._items_textures, 5)

        return None

    def _compute_screen_positions(self) -> Dict[str, Tuple[float, float]]:
        """
        Map each zone's (x, y) map coordinate to a base (pre-camera) screen position
        """
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

    def _to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """Apply the current camera pan and zoom to a base layout position."""
        return (
            x * self._zoom + self._camera_offset_x,
            y * self._zoom + self._camera_offset_y,
        )

    def on_resize(self, width: int, height: int) -> None:
        """Recompute zone layout when the window is resized."""
        super().on_resize(width, height)
        if hasattr(self, "_network"):
            self._positions = self._compute_screen_positions()

    def _drone_screen_position(self, drone_id: str) -> Tuple[float, float]:
        """Return the interpolated base (pre-camera) position of a drone.

        Finds the (zone, turn) segment of the drone's timed path that
        contains the current simulated turn, and interpolates linearly
        across that segment's full duration (1 turn for a normal move,
        2 turns for a restricted-zone transit, 0 for a wait).
        """
        path = self._routes[drone_id]
        t = self._current_turn

        if t <= path[0][1]:
            return self._positions[path[0][0].name]

        for i in range(len(path) - 1):
            zone_a, t1 = path[i]
            zone_b, t2 = path[i + 1]
            if t1 <= t <= t2:
                progress = 0.0 if t2 == t1 else (t - t1) / (t2 - t1)
                ax, ay = self._positions[zone_a.name]
                bx, by = self._positions[zone_b.name]
                return ax + (bx - ax) * progress, ay + (by - ay) * progress

        return self._positions[path[-1][0].name]

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
        """Draw a line for every connection in the network, camera-transformed."""
        for connection in self._network.connections:
            x1, y1 = self._to_screen(*self._positions[connection.zone1.name])
            x2, y2 = self._to_screen(*self._positions[connection.zone2.name])
            arcade.draw_line(x1, y1, x2, y2, arcade.color.LIGHT_STEEL_BLUE, 2)

    def _draw_zones(self) -> None:
        """Draw every zone as its assigned tile texture, or a fallback circle."""
        radius = ZONE_RADIUS * self._zoom
        for zone in self._network.zones:
            x, y = self._to_screen(*self._positions[zone.name])
            tex = self._zone_texture(zone)

            if tex is not None:
                size = radius * 2.2
                arcade.draw_texture_rect(tex, arcade.XYWH(x, y, size, size))
            else:
                fill_color = arcade.color.DARK_BLUE_GRAY
                if zone.color:
                    fill_color = getattr(
                        arcade.color, zone.color.upper(), _DEFAULT_COLOR
                    )
                outline_color = _ZONE_TYPE_OUTLINE.get(
                    zone.zone_type, arcade.color.WHITE
                )
                arcade.draw_circle_filled(x, y, radius, fill_color)
                arcade.draw_circle_outline(x, y, radius, outline_color, 3)

            arcade.draw_text(
                zone.name,
                x,
                y + radius + 4,
                arcade.color.WHITE,
                12,
                anchor_x="center",
                bold=True,
            )

    def _draw_drones(self) -> None:
        """Draw every drone at its current interpolated, camera-transformed position."""
        current_drone_tex: Optional[arcade.Texture] = None
        if self._drone_textures:
            frame_idx = int(self._anim_timer * DRONE_ANIM_FPS) % len(
                self._drone_textures
            )
            current_drone_tex = self._drone_textures[frame_idx]

        for drone_id in sorted(self._routes.keys()):
            x, y = self._to_screen(*self._drone_screen_position(drone_id))

            if current_drone_tex is not None:
                w = current_drone_tex.width * 1.5 * self._zoom
                h = current_drone_tex.height * 1.5 * self._zoom
                arcade.draw_texture_rect(current_drone_tex, arcade.XYWH(x, y, w, h))
                label_y = y - h / 2 - 14
            else:
                arcade.draw_circle_filled(
                    x, y, 10 * self._zoom, arcade.color.ELECTRIC_CYAN
                )
                label_y = y - 24

            arcade.draw_text(
                drone_id,
                x,
                label_y,
                arcade.color.ELECTRIC_CYAN,
                11,
                anchor_x="center",
                bold=True,
            )

    def _draw_hud(self) -> None:
        """Draw a compact sci-fi style HUD: turn fraction, progress bar, play state."""
        panel_x, panel_y = 14, self.height - 14
        panel_w, panel_h = 160, 54

        arcade.draw_lbwh_rectangle_filled(
            panel_x,
            panel_y - panel_h,
            panel_w,
            panel_h,
            (10, 14, 20, 180),
        )
        arcade.draw_lbwh_rectangle_outline(
            panel_x,
            panel_y - panel_h,
            panel_w,
            panel_h,
            arcade.color.ELECTRIC_CYAN,
            1,
        )

        turn_text = f"{int(self._current_turn):02d}/{self._max_turn:02d}"
        arcade.draw_text(
            turn_text,
            panel_x + 12,
            panel_y - 26,
            arcade.color.ELECTRIC_CYAN,
            18,
            bold=True,
            font_name="Consolas",
        )

        bar_x = panel_x + 12
        bar_y = panel_y - 34
        bar_w = panel_w - 24
        bar_h = 4
        progress = 0.0 if self._max_turn == 0 else self._current_turn / self._max_turn

        arcade.draw_lbwh_rectangle_filled(bar_x, bar_y, bar_w, bar_h, (40, 50, 60, 255))
        arcade.draw_lbwh_rectangle_filled(
            bar_x, bar_y, bar_w * progress, bar_h, arcade.color.ELECTRIC_CYAN
        )

        state_color = arcade.color.NEON_GREEN if self._playing else arcade.color.ORANGE
        state_symbol = "▶" if self._playing else "⏸"
        arcade.draw_text(
            f"{state_symbol}",
            panel_x + 12,
            panel_y - 48,
            state_color,
            12,
            bold=True,
            font_name="Consolas",
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
        """Advance the animation clock and move the current turn toward its target.

        In auto-play mode, the target turn is always the max turn and the
        current turn advances continuously. In manual step mode, the current
        turn animates smoothly toward whatever turn was last requested via
        the arrow keys, at the same pace as auto-play.
        """
        self._anim_timer += delta_time
        step = delta_time / SECONDS_PER_TURN

        if self._playing:
            self._target_turn = float(self._max_turn)

        if self._current_turn < self._target_turn:
            self._current_turn = min(self._current_turn + step, self._target_turn)
        elif self._current_turn > self._target_turn:
            self._current_turn = max(self._current_turn - step, self._target_turn)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Handle playback controls: play/pause, step, quit."""
        if symbol == arcade.key.SPACE:
            self._playing = not self._playing
            if self._playing:
                self._target_turn = float(self._max_turn)
            else:
                self._target_turn = self._current_turn
        elif symbol == arcade.key.RIGHT:
            self._playing = False
            self._target_turn = min(self._target_turn + 1, self._max_turn)
        elif symbol == arcade.key.LEFT:
            self._playing = False
            self._target_turn = max(self._target_turn - 1, 0)
        elif symbol == arcade.key.ESCAPE:
            arcade.close_window()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        """Start camera panning on left mouse button press."""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._dragging = True

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        """Stop camera panning on left mouse button release."""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._dragging = False

    def on_mouse_drag(
        self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int
    ) -> None:
        """Pan the camera by the mouse movement delta while dragging."""
        if self._dragging:
            self._camera_offset_x += dx
            self._camera_offset_y += dy

    def on_mouse_scroll(
        self, x: int, y: int, scroll_x: float, scroll_y: float
    ) -> EVENT_HANDLE_STATE:
        """
        Zoom in/out with the scroll wheel, keeping the point under the cursor fixed
        """
        if scroll_y == 0:
            return None

        factor = ZOOM_STEP if scroll_y > 0 else 1.0 / ZOOM_STEP
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, self._zoom * factor))
        if new_zoom == self._zoom:
            return None

        base_x = (x - self._camera_offset_x) / self._zoom
        base_y = (y - self._camera_offset_y) / self._zoom

        self._zoom = new_zoom
        self._camera_offset_x = x - base_x * self._zoom
        self._camera_offset_y = y - base_y * self._zoom
        return None


def run_visualizer(network: Network, routes: Dict[str, List[Tuple[Zone, int]]]) -> None:
    """Create and run the graphical visualizer until the window is closed."""
    Visualizer(network, routes)
    arcade.run()
