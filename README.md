*This project has been created as part of the 42 curriculum by horarivo.*

# Fly-in

Drone routing system with pathfinding and simulation.

## Description

Fly-in is a Python simulation that routes a fleet of drones from a single
central base (`start_hub`) to a single target location (`end_hub`) through a
network of connected zones, while respecting a set of turn-based movement
rules and capacity constraints.

The network is described in a custom text file format: zones can be
`normal`, `restricted` (costs 2 turns to enter), `priority` (costs 1 turn,
should be preferred by the pathfinding), or `blocked` (never enterable).
Zones and connections can define a maximum number of drones/connections
allowed to occupy them at the same time.

The program parses the map, computes a collision-free, capacity-aware route
for every drone, and outputs a turn-by-turn simulation showing every drone
movement until all drones have reached the target zone. It also provides an
optional graphical visualization of the whole simulation.

The graph itself (zones, connections, pathfinding) is implemented entirely
from scratch, without any external graph library.

## Instructions

### Requirements

- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/) (or any compatible package manager)

### Installation

```bash
make install
```

This installs all project dependencies (including `arcade` for the
graphical visualization, `flake8` and `mypy` for linting/type-checking).

### Running the simulation

```bash
make run
```

which runs (by default):

```bash
uv run src/main.py --map data/maps/test.txt
```

You can point `--map` to any map file following the format described
below, and add `--gui` to launch the graphical visualization instead of
the text output:

```bash
uv run src/main.py --map data/maps/hard_maze.txt --gui
```

### Other Makefile targets

- `make debug` - run the main script under Python's built-in debugger (`pdb`)
- `make clean` - remove `__pycache__`, `.mypy_cache` and other temporary files
- `make lint` - run `flake8` and `mypy` with the mandatory flags
- `make lint-strict` - run `flake8` and `mypy --strict` for stricter checking

### Map file format

```
nb_drones: 5

start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]

connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```

- The first non-comment line must define `nb_drones: <positive integer>`.
- There must be exactly one `start_hub:` and one `end_hub:`.
- Zone metadata (`zone`, `color`, `max_drones`) and connection metadata
  (`max_link_capacity`) are optional, in any order, inside `[...]`, and
  fall back to sensible defaults (`zone=normal`, `max_drones=1`,
  `max_link_capacity=1`).
- Lines starting with `#` are treated as comments and ignored.

### Example input and output

Given the map file shown above, running:

```bash
uv run src/main.py --map data/maps/test.txt
```

produces a turn-by-turn simulation such as:

```
D1-corridorA D2-roof1
D1-tunnelB
D1-goal D2-roof2
D2-goal
```

Each line represents one simulation turn. `D<ID>-<zone>` means the drone
moved into that zone; `D<ID>-<connection>` means the drone is still in
transit toward a `restricted` zone. Drones that don't move on a given turn
are simply omitted from that line. The simulation stops as soon as every
drone has reached `end_hub`.

## Algorithm explanation

### Data model

The network is modeled with plain object-oriented classes: `Zone`,
`Connection`, `Drone` and `Network`, with no dependency on any graph
library - connectivity is represented directly as a list of `Connection`
objects, each linking two `Zone` objects.

### Pathfinding: Cooperative A\* over a time-expanded graph

Instead of computing a single static shortest path per drone and then
trying to resolve conflicts afterward, the pathfinding works over a
**time-expanded state space**: every explored node is a pair
`(zone, turn)`, not just `zone`. This lets the algorithm naturally reason
about *when* a drone would be somewhere, not just *where*.

Concretely:

- A **`ReservationTable`** tracks, for every future turn, how many drones
  are scheduled to occupy each zone and traverse each connection. It
  exposes `is_zone_available`/`is_connection_available` (read) and
  `reserve_zone`/`reserve_connection`/`reserve_path` (write). Zones marked
  as `start_hub`/`end_hub` are always available, per the subject's rule
  that they have unlimited capacity. A move into a `restricted` zone
  occupies the connection for its full 2-turn transit, but only reserves
  the destination zone at the actual arrival turn, not before.

- A **`PathFinder`** runs a Dijkstra search (not full A\*, since the small
  map sizes involved don't warrant the extra complexity of a heuristic)
  over `(zone, turn)` states, for a single drone at a time. From any state
  it can either wait one turn in place, or move to a connected neighbor
  (1 turn for `normal`/`priority`, 2 turns for `restricted`, and `blocked`
  zones are never explored), provided the `ReservationTable` confirms the
  destination zone and connection have free capacity at that turn.

- A **`RoutingManager`** routes all drones one at a time (in a fixed,
  deterministic order): each drone's path is found against the current
  state of the `ReservationTable`, then immediately reserved before the
  next drone is planned. This is a **Cooperative A\*** approach - a single,
  simple algorithm that naturally satisfies distribution across multiple
  paths, strategic waiting, and conflict/capacity avoidance, without
  needing a separate flow algorithm or a second conflict-resolution pass.

### Complexity and design trade-offs

For a single drone, the search explores at most `O(Z * T)` states, where
`Z` is the number of zones and `T` a bounded turn horizon (the
implementation uses a safety bound of `Z * 4` turns past the current start
turn to guarantee termination even on maps with no valid path). Each state
expansion is `O(degree)`, and insertion/extraction from the priority queue
is `O(log n)`, giving an overall complexity comparable to standard Dijkstra
on a graph of that size, run once per drone.

Because the network in this project always has a single shared
`start_hub`/`end_hub`, the order in which drones are routed does not
change the outcome (drones are interchangeable) - so no additional
ordering heuristic was needed on top of the base algorithm.

### Simulation output

A **`SimulationEngine`** converts the computed per-drone timed paths into
the exact turn-by-turn output format required by the subject, grouping all
drone movements by turn and splitting a `restricted`-zone transit into its
two required lines (connection, then destination zone).

## Visual representation

In addition to the text output, the simulation can be watched through a
graphical visualization built with [Arcade](https://api.arcade.academy/),
enabled with the `--gui` flag.

Features:

- Zones are drawn using dedicated textures depending on their role/type
  (`start`, `end`, `normal`, `restricted`, `priority`, `blocked`), with a
  colored circle fallback if a texture asset is missing.
- Drones are drawn as animated sprites and **smoothly interpolate** their
  position between zones - including across a full 2-turn `restricted`
  transit, so the motion always matches the real duration of the move
  rather than jumping or pausing mid-transit.
- Playback controls: `SPACE` toggles play/pause, `LEFT`/`RIGHT` step one
  turn backward/forward (still smoothly animated, at the same pace as
  auto-play), `ESC` closes the window.
- Camera controls: click-and-drag to pan the view (useful on larger maps
  with many zones), and mouse-wheel to zoom in/out, centered on the
  cursor position.
- A compact, sci-fi-styled HUD in the top-left corner shows the current
  turn as a fraction, a progress bar, and a play/pause indicator.

This gives an intuitive, at-a-glance understanding of how drones are
distributed across parallel paths, where congestion or waiting happens,
and how zone types affect movement - which is much harder to follow from
the raw text output alone, especially on larger and more complex maps.

## Resources

- [Python `heapq` documentation](https://docs.python.org/3/library/heapq.html) - priority queue used by the Dijkstra-based pathfinder
- [Introduction to A\* (Red Blob Games)](https://www.redblobgames.com/pathfinding/a-star/introduction.html) - background reading on grid/graph pathfinding concepts
- [Cooperative pathfinding literature](https://en.wikipedia.org/wiki/Cooperative_pathfinding) - general background on multi-agent pathfinding with reservation-based conflict avoidance
- [Arcade documentation](https://api.arcade.academy/) - graphical library used for the visual representation
- [mypy documentation](https://mypy.readthedocs.io/) - static type checking
- [flake8 documentation](https://flake8.pycqa.org/) - style/lint checking
- [Path finding alforithms visualizer](https://pathfinding-algorithms-visualizer.netlify.app) - for deeper understanding about pathfinding algorithms

### AI usage

An AI assistant was used throughout this project as a design-discussion
and debugging partner.
Concretely, AI assistance was used for:

- Discussing and comparing pathfinding strategies before implementation,
  including rejecting an initially suggested Max-Flow/A\*/BFS hybrid
  approach as unnecessarily complex in favor of the simpler Cooperative
  A\* design ultimately implemented.
- Reviewing and correcting the `ReservationTable` design against the exact
  wording of the subject (in particular the handling of `restricted` zone
  transits).
- Diagnosing concrete bugs (an off-by-one loop bound, a priority queue
  popped before the main loop, a `heapq` tuple-comparison issue, an
  incorrect drone-position interpolation during multi-turn transits)
- Refining the Arcade-based visualization code, and resolving
  `mypy`/`flake8` configuration issues.
- Improving this README.

