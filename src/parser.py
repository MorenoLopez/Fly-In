#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   parser.py                                            :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/02 22:13:16 by horarivo            #+#    #+#            #
#   Updated: 2026/09/02 22:13:33 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

"""Parser for the Fly-in map file format"""

import re
from pathlib import Path
from typing import Any

from src.models.zone import Zone
from src.models.connection import Connection
from src.models.map_graph import MapGraph


class ParseError(Exception):
    """Raised when a map file cannot be parsed"""

    pass


def _parse_metadata(meta_str: str) -> dict[str, Any]:
    """Parse metadata from bracketed string

    Args:
        meta_str: String like "[zone=restricted color=red max_drones=2]"

    Returns:
        Dictionary of metadata key-value pairs
    """
    result: dict[str, Any] = {}
    if not meta_str:
        return result
    # Remove outer brackets
    inner = meta_str.strip().strip("[]").strip()
    if not inner:
        return result
    # Split by spaces, respecting key=value pairs
    tokens = re.findall(r'(\w+)=(\S+)', inner)
    for key, value in tokens:
        if key in ("max_drones", "max_link_capacity"):
            try:
                result[key] = int(value)
            except ValueError:
                raise ParseError(f"Invalid integer value for {key}: {value}")
        else:
            result[key] = value
    return result


def _parse_hub_line(rest: str, line_no: int, is_start: bool, is_end: bool) -> Zone:
    """Parse a start_hub/end_hub definition line into a Zone

    Args:
        rest: The line content after the "start_hub:"/"end_hub:" prefix
        line_no: Line number, for error messages
        is_start: Whether this zone is the start zone
        is_end: Whether this zone is the end zone

    Returns:
        The constructed Zone

    Raises:
        ParseError: If the definition is malformed
    """
    meta_match = re.search(r'\[(.*?)\]', rest)
    meta: dict[str, Any] = {}
    if meta_match:
        meta = _parse_metadata(meta_match.group(0))
        rest = rest[:meta_match.start()].strip()

    tokens = rest.split()
    if len(tokens) < 3:
        raise ParseError(f"Line {line_no}: Invalid hub definition")
    name = tokens[0]
    try:
        x = int(tokens[1])
        y = int(tokens[2])
    except ValueError:
        raise ParseError(f"Line {line_no}: Invalid coordinates")

    return Zone(
        name=name,
        x=x,
        y=y,
        zone_type=meta.get("zone", "normal"),
        color=meta.get("color"),
        max_drones=meta.get("max_drones", 1),
        is_start=is_start,
        is_end=is_end,
    )


def parse_map_file(file_path: Path) -> MapGraph:
    """Parse a Fly-in map file and return a MapGraph.=

    Args:
        file_path: Path to the map file

    Returns:
        A fully constructed MapGraph

    Raises:
        ParseError: If the file format is invalid
        FileNotFoundError: If the file does not exist
    """
    graph = MapGraph()
    seen_zones: set[str] = set()
    seen_connections: set[tuple[str, str]] = set()
    line_no = 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise

    for raw_line in lines:
        line_no += 1
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # nb_drones
        if line.startswith("nb_drones:"):
            parts = line.split(":")
            if len(parts) != 2:
                raise ParseError(f"Line {line_no}: Invalid nb_drones syntax")
            try:
                graph.num_drones = int(parts[1].strip())
            except ValueError:
                raise ParseError(f"Line {line_no}: Invalid drone count")
            continue

        # start_hub
        if line.startswith("start_hub:"):
            rest = line[len("start_hub:"):].strip()
            zone = _parse_hub_line(rest, line_no, is_start=True, is_end=False)
            if zone.name in seen_zones:
                raise ParseError(f"Line {line_no}: Duplicate zone {zone.name}")
            seen_zones.add(zone.name)
            graph.start_zone = zone.name
            graph.add_zone(zone)
            continue

        # end_hub
        if line.startswith("end_hub:"):
            rest = line[len("end_hub:"):].strip()
            zone = _parse_hub_line(rest, line_no, is_start=False, is_end=True)
            if zone.name in seen_zones:
                raise ParseError(f"Line {line_no}: Duplicate zone {zone.name}")
            seen_zones.add(zone.name)
            graph.end_zone = zone.name
            graph.add_zone(zone)
            continue

        # hub (regular zone)
        if line.startswith("hub:"):
            rest = line[len("hub:"):].strip()
            # Extract metadata if present
            meta_match = re.search(r'\[(.*?)\]', rest)
            meta: dict[str, Any] = {}
            if meta_match:
                meta = _parse_metadata(meta_match.group(0))
                rest = rest[:meta_match.start()].strip()

            tokens = rest.split()
            if len(tokens) < 3:
                raise ParseError(f"Line {line_no}: Invalid hub definition")
            name = tokens[0]
            try:
                x = int(tokens[1])
                y = int(tokens[2])
            except ValueError:
                raise ParseError(f"Line {line_no}: Invalid coordinates")

            if name in seen_zones:
                raise ParseError(f"Line {line_no}: Duplicate zone {name}")
            seen_zones.add(name)

            zone = Zone(
                name=name,
                x=x,
                y=y,
                zone_type=meta.get("zone", "normal"),
                color=meta.get("color"),
                max_drones=meta.get("max_drones", 1),
                is_start=(name == graph.start_zone),
                is_end=(name == graph.end_zone),
            )
            graph.add_zone(zone)
            continue

        # connection
        if line.startswith("connection:"):
            rest = line[len("connection:"):].strip()
            meta_match = re.search(r'\[(.*?)\]', rest)
            meta = {}
            if meta_match:
                meta = _parse_metadata(meta_match.group(0))
                rest = rest[:meta_match.start()].strip()

            if "-" not in rest:
                raise ParseError(f"Line {line_no}: Invalid connection syntax")
            parts = rest.split("-")
            if len(parts) != 2:
                raise ParseError(f"Line {line_no}: Connection must have exactly two zones")
            a, b = parts[0].strip(), parts[1].strip()

            key = tuple(sorted([a, b]))
            if key in seen_connections:
                raise ParseError(f"Line {line_no}: Duplicate connection {a}-{b}")
            seen_connections.add(key)

            conn = Connection(
                zone_a=a,
                zone_b=b,
                max_link_capacity=meta.get("max_link_capacity", 1),
            )
            graph.add_connection(conn)
            continue

        raise ParseError(f"Line {line_no}: Unrecognized line format")

    if graph.num_drones <= 0:
        raise ParseError("Number of drones must be a positive integer")
    if not graph.start_zone:
        raise ParseError("Missing start_hub definition")
    if not graph.end_zone:
        raise ParseError("Missing end_hub definition")
    if graph.start_zone not in graph.zones:
        raise ParseError(f"Start zone '{graph.start_zone}' not defined")
    if graph.end_zone not in graph.zones:
        raise ParseError(f"End zone '{graph.end_zone}' not defined")

    return graph
