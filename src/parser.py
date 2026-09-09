#!/usr/bin/env python3
# ########################################################################### #
#   shebang: 1                                                                #
#                                                          :::      ::::::::  #
#   parser.py                                            :+:      :+:    :+:  #
#                                                      +:+ +:+         +:+    #
#   By: horarivo <horarivo@student.42antananarivo.   +#+  +:+       +#+       #
#                                                  +#+#+#+#+#+   +#+          #
#   Created: 2026/09/08 17:56:45 by horarivo            #+#    #+#            #
#   Updated: 2026/09/09 11:51:31 by horarivo           ###   ########.fr      #
#                                                                             #
# ########################################################################### #

import re
from typing import Dict, Optional, Set, List
from src.models.zone import Zone
from src.models.drone import Drone
from src.models.connection import Connection
from src.models.network import Network


_DRONE_PATTERN = re.compile(r"^(nb_drones:\s*)?(-?\d+)\s*$")
_HUB_PATTERN = re.compile(
	r"^(start_hub|end_hub|hub):\s+([^\s\-]+)\s+(-?\d+)\s+(-?\d+)\s*(\[.*\])?\s*$"
)
_CONNECTION_PATTERN = re.compile(
	r"^connection:\s+([^\s\-]+)-([^\s\-]+)\s*(\[.*\])?\s*$"
)
_METADATA_ITEM_PATTERN = re.compile(r"^(\w+)=(\S+)$")

_VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}
_HUB_METADATA_KEYS = {"zone", "color", "max_drones"}
_CONNECTION_METADATA_KEYS = {"max_link_capacity"}


class ParseError(Exception):
	def __init__(self, line_num: int, message: str) -> None:
		self.line_num = line_num
		self.message = message
		super().__init__(f"Line {line_num}: {message}")


class Parser:

	def __init__(self) -> None:
		self._nb_drones: Optional[int] = None
		self._zones: Dict[str, Zone] = {}
		self._connection_keys: Set[tuple[str, str]] = set()
		self._connections: List[Connection] = []
		self._start_name: Optional[str] = None
		self._end_name: Optional[str] = None
		self._seen_first_line: bool = False

	def _reset(self) -> None:
		self._nb_drones = None
		self._zones = {}
		self._connection_keys = set()
		self._connections = []
		self._start_name = None
		self._end_name = None
		self._seen_first_line = False

	def _parse_nb_drones_line(self, line: str, line_num: int) -> None:
		if self._nb_drones is not None:
			raise ParseError(line_num, "nb_drones is defined more than once")

		match = _DRONE_PATTERN.match(line)
		if match is None:
			raise ParseError(line_num, f"malformed nb_drones line: {line!r}")

		value = int(match.group(1))
		if value <= 0:
			raise ParseError(line_num, "nb_drones must be a positive integer")

		self._nb_drones = value

	def _parse_metadata(
		self, meta_str: Optional[str], line_num: int, allowed_keys: Set[str]
	) -> Dict[str, str]:
		if meta_str is None:
			return {}

		inner = meta_str.strip()
		if not (inner.startswith("[") and inner.endswith("]")):
			raise ParseError(line_num, f"malformed metadata block: {meta_str!r}")

		inner = inner[1:-1].strip()
		if not inner:
			return {}

		metadata: Dict[str, str] = {}
		for token in inner.split():
			match = _METADATA_ITEM_PATTERN.match(token)
			if match is None:
				raise ParseError(line_num, f"malformed metadata entry: {token!r}")

			key, value = match.group(1), match.group(2)
			if key not in allowed_keys:
				raise ParseError(line_num, f"unknown metadata key: {key!r}")
			if key in metadata:
				raise ParseError(line_num, f"duplicate metadata key: {key!r}")

			metadata[key] = value

		return metadata

	def _parse_hub_line(self, prefix: str, line: str, line_num: int) -> None:
		match = _HUB_PATTERN.match(line)
		if match is None:
			raise ParseError(line_num, f"malformed {prefix} line: {line!r}")

		name, x_str, y_str, meta_str = (
			match.group(2), match.group(3), match.group(4), match.group(5)
		)

		if name in self._zones:
			raise ParseError(line_num, f"duplicate zone name: {name!r}")

		if prefix == "start_hub":
			if self._start_name is not None:
				raise ParseError(line_num, "start_hub is defined more than once")
			self._start_name = name
		elif prefix == "end_hub":
			if self._end_name is not None:
				raise ParseError(line_num, "end_hub is defined more than once")
			self._end_name = name

		metadata = self._parse_metadata(meta_str, line_num, _HUB_METADATA_KEYS)

		zone_type = metadata.get("zone", "normal")
		if zone_type not in _VALID_ZONE_TYPES:
			raise ParseError(line_num, f"invalid zone type: {zone_type!r}")

		max_drones_str = metadata.get("max_drones", "1")
		if not max_drones_str.isdigit() or int(max_drones_str) <= 0:
			raise ParseError(
				line_num,
				f"max_drones must be a positive integer, got {max_drones_str!r}"
			)

		zone = Zone(
			name=name,
			x=int(x_str),
			y=int(y_str),
			zone_type=zone_type,
			max_drones=int(max_drones_str),
			color=metadata.get("color"),
		)
		self._zones[name] = zone

	def _parse_connection_line(self, line: str, line_num: int) -> None:
		match = _CONNECTION_PATTERN.match(line)
		if match is None:
			raise ParseError(line_num, f"malformed connection line: {line!r}")

		name1, name2, meta_str = match.group(1), match.group(2), match.group(3)

		if name1 not in self._zones:
			raise ParseError(line_num, f"connection references undefined zone: {name1!r}")
		if name2 not in self._zones:
			raise ParseError(line_num, f"connection references undefined zone: {name2!r}")
		if name1 == name2:
			raise ParseError(line_num, f"connection cannot link a zone to itself: {name1!r}")

		name_a, name_b = sorted((name1, name2))
		key = (name_a, name_b)
		if key in self._connection_keys:
			raise ParseError(
				line_num, f"duplicate connection between {name1!r} and {name2!r}"
			)
		self._connection_keys.add(key)

		metadata = self._parse_metadata(meta_str, line_num, _CONNECTION_METADATA_KEYS)
		capacity_str = metadata.get("max_link_capacity", "1")
		if not capacity_str.isdigit() or int(capacity_str) <= 0:
			raise ParseError(
				line_num,
				f"max_link_capacity must be a positive integer, got {capacity_str!r}"
			)

		connection = Connection(
			self._zones[name1], self._zones[name2], int(capacity_str)
		)
		self._connections.append(connection)

	def _parse_line(self, raw_line: str, line_num: int) -> None:
		line = raw_line.split("#")[0].strip()

		if not line:
			return

		if not self._seen_first_line:
			if not line.startswith("nb_drones:"):
				raise ParseError(
					line_num, "the first line of the map file must define nb_drones"
				)
			self._seen_first_line = True

		if line.startswith("nb_drones:"):
			self._parse_nb_drones_line(line, line_num)
		elif line.startswith("start_hub:"):
			self._parse_hub_line("start_hub", line, line_num)
		elif line.startswith("end_hub:"):
			self._parse_hub_line("end_hub", line, line_num)
		elif line.startswith("hub:"):
			self._parse_hub_line("hub", line, line_num)
		elif line.startswith("connection:"):
			self._parse_connection_line(line, line_num)
		else:
			raise ParseError(line_num, f"unrecognized line format: {raw_line!r}")

	def parse(self, file_path: str) -> Network:
		self._reset()
		has_content = False

		try:
			with open(file_path, "r") as file:
				for line_num, line in enumerate(file, 1):
					cleaned = line.split("#")[0].strip()
					if cleaned:
						has_content = True
					self._parse_line(line, line_num)
		except OSError as e:
			raise OSError(f"Couldn't read map file {file_path}: {e}")

		if not has_content:
			raise ValueError("Map file is empty or contains no valid data")
		if self._nb_drones is None:
			raise ValueError("Missing 'nb_drones' directive in map file")
		if self._start_name is None:
			raise ValueError("Missing 'start_hub' zone in map file")
		if self._end_name is None:
			raise ValueError("Missing 'end_hub' zone in map file")

		start_zone = self._zones[self._start_name]
		end_zone = self._zones[self._end_name]
		drones = [Drone(f"D{i + 1}", start_zone) for i in range(self._nb_drones)]

		network = Network()
		network.zones = list(self._zones.values())
		network.connections = list(self._connections)
		network.drones = drones
		network.start_zone = start_zone
		network.end_zone = end_zone

		return network
