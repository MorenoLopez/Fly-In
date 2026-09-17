# Fly-in - Guide

This document retraces, step by step, how this **Fly-in** project was designed and built: the choices, the blockers encountered, the mistakes made (and why they happened), and how they were fixed. The goal is to use it as material to teach the project to someone else, showing not just the final result but **the reasoning behind every decision**.

---

## 1. Understanding the subject before coding

Before writing a single line of code, the **non-negotiable constraints** need to be extracted from the subject:

- Write in Python 3.10+, with **strict typing** (`mypy`) and `flake8` compliance.
- **No graph library** (`networkx`, `graphlib`, etc. are forbidden) - the graph has to be implemented by hand.
- The project must be **fully object-oriented**.
- The input format is a custom text file (`nb_drones:`, `start_hub:`, `end_hub:`, `hub:`, `connection:`), with optional metadata in brackets.
- Four zone types: `normal` (1 turn), `restricted` (2 turns), `priority` (1 turn, should be preferred), `blocked` (impassable).
- Capacity constraints: `max_drones` per zone, `max_link_capacity` per connection.
- Drones can move **simultaneously**, but must respect capacities and never collide.
- The output format is strict: one line per turn, `D<ID>-<zone>` or `D<ID>-<connection>` (for restricted zones in transit), stationary drones omitted.
- A **visual representation** is mandatory (colored terminal and/or GUI).

**Lesson**: reading the entire subject *before* coding avoids having to start over later. Many of the subject's constraints (such as the 2-turn cost for `restricted`, or the fact that a connection is "occupied" during transit) have deep implications for the architecture - missing them early costs a lot later.

---

## 2. Initial architecture choices

The project was structured this way:

```
src/
├── main.py
├── parser.py
├── algorithms.py       (ReservationTable, PathFinder, RoutingManager)
├── simulate.py          (SimulationEngine)
├── visualizer.py         (Arcade GUI)
└── models/
    ├── zone.py
    ├── connection.py
    ├── drone.py
    └── network.py
```

Each class has a single responsibility - a central principle for meeting the subject's "fully object-oriented" requirement, and it shows clearly in the breakdown: parsing, the data model, the pathfinding algorithm, drone scheduling, text output generation, and visualization are **five distinct responsibilities**, in five distinct places.

---

## 3. The first blocker: inconsistent imports

**What happened**: from the start, some files imported `from models.zone import Zone` (no prefix), others `from src.models.zone import Zone` (with the prefix). It seemed to work... until `mypy` blew up with:

```
error: Source file found twice under different module names: "models.zone" and "src.models.zone"
```

**Why this happens**: for Python (and mypy), `models.zone` and `src.models.zone` are **two different module names**, even though they point to the same physical file on disk. If half the project imports one way and the other half the other way, the type checker sees "two different `Zone` classes" that should be the same one.

**The lesson to teach here**: this kind of error is very common among beginners who change their folder structure mid-project without being rigorous about the import convention. **Pick ONE convention (with or without the root package prefix) and stick to it everywhere**, including in `main.py`.

A related technical point: whether or not each folder (`src/`, `src/models/`) has an `__init__.py` changes how Python and mypy resolve imports. Having an `__init__.py` in `src/models/` but not in `src/` was exactly what created this ambiguity.

---

## 4. Building the Parser: line by line, rigorously

The `Parser` was built progressively:

1. **First, just `nb_drones:`** - the basic structure (`ParseError` with a line number, `_reset()` to reuse the instance, a `_parse_line` method that routes each line by its prefix).
2. **Then, zones** (`hub:`, `start_hub:`, `end_hub:`) with parsing of the bracketed metadata.
3. **Finally, connections**, with duplicate detection (a connection `A-B` and `B-A` must be treated as the same one) and verification that both referenced zones already exist.

**Important design decision**: the parser makes **a single pass** over the file. This implies a real constraint - a connection can only reference zones **already seen before it** in the file. This isn't an arbitrary limitation: the subject states it explicitly ("*Connections must link only previously defined zones*"), so the implementation matches the requirement exactly, without unnecessary complexity (no need for "two-pass resolution").

**A real bug encountered**: at one point, the parser returned a completely empty `Network()` object, because attributes like `self.zones`, `self.start_zone`, etc., were only declared as **type annotations**, with no initial value:
```python
self.zones: list[Zone]   # ← declares the type, but assigns NOTHING
```
This compiles, but the attribute doesn't actually exist until something explicitly assigns it. The fix:
```python
self.zones: list[Zone] = []
```

**Lesson**: in Python, a type annotation alone (`x: int`) does NOT create a variable - it always needs a value attached (`x: int = 0`) for it to actually exist at runtime.

---

## 5. Designing the algorithm: rejecting over-engineering

Before coding the routing algorithm, an AI (Gemini) had proposed a "hybrid strategy" architecture combining Max-Flow (Edmonds-Karp), spatiotemporal A\*, and a BFS validation pass - three different algorithms depending on the "type" of graph detected.

**Why this proposal was rejected**:
1. Max-Flow maximizes throughput, but does **not** give a temporal schedule (who moves on which turn) - the flow would have had to be converted into a schedule afterward, doubling the work.
2. Dynamically detecting "what type of graph" adds fragile complexity, with no guarantee that the subject provides graphs that cleanly fit into these categories.
3. Three different algorithms means three times more code to maintain, test, and explain during the defense.

**The chosen decision: Cooperative A\*** ("Hierarchical Cooperative A\*", HCA\*) - a single, simpler algorithm:
- Each drone is routed **one at a time**, in a given order.
- Each drone computes its optimal path via a shortest-path search over a **time-expanded state**: not just `zone`, but `(zone, turn)`.
- Once a path is found, it is **reserved** in a shared structure (`ReservationTable`), so that subsequent drones take it into account.

**Lesson**: when an AI (or anyone) proposes a complex solution, the question to ask is "does this really solve the problem more simply, or does it just move the complexity elsewhere?". Here, Cooperative A\* achieves the same goals (distribution across multiple paths, strategic waiting, conflict avoidance, capacity constraints) with a single data structure and a single algorithm.

---

## 6. The ReservationTable: the central building block

### Design

The `ReservationTable` keeps track, for every future turn, of:
- how many drones occupy each **zone** at that turn (`{(zone_name, turn): count}`)
- how many drones traverse each **connection** at that turn (`{(canonical_edge, turn): count}`)

Two read methods (`is_zone_available`, `is_connection_available`) and two write methods (`reserve_zone`, `reserve_connection`), plus a high-level method (`reserve_path`) that posts all the reservations of a full path at once.

### The "restricted" zone trap - and the corrected mistake

I had been told that, for a 2-turn transit into a `restricted` zone, one should reserve:
- the connection at turn `t`
- **the destination zone** at turns `t+1` **AND** `t+2`

**Why this was wrong**: the subject explicitly says the drone **occupies the connection** during the 2 turns of transit - it is only physically in the destination zone **at the arrival turn** (`t+2`), not before. Reserving the zone as early as `t+1` would have needlessly blocked its capacity a turn too soon, potentially preventing another drone from legitimately entering it at that moment, even though the zone was actually still free.

**The fix applied**:
- Connection reserved at turns `t` and `t+1` (the 2 transit turns)
- Destination zone reserved **only** at `t+2`

**Lesson**: suggestions need to be checked against the exact wording of the subject. Here, carefully re-reading the sentence *"the drone occupies the connection during transit"* was enough to spot the mistake - the subject talks about the connection, not the zone, during transit.

### Start/end exception

The subject specifies that `start_hub` and `end_hub` have **no** capacity limit (all drones can coexist there). This translated into two attributes `is_start`/`is_end` on `Zone`, short-circuiting the capacity check in `is_zone_available`:
```python
def is_zone_available(self, zone: Zone, turn: int) -> bool:
    if zone.is_start or zone.is_end:
        return True
    ...
```

**Small note**: these `is_start`/`is_end` attributes were added to `Zone` *after the fact*, once I realized while designing `ReservationTable` that I needed them. The `Parser` then had to be modified after the fact to set them (`zone.is_start = True` when creating the `start_hub` zone). **This is a good illustration that project design is never perfectly linear** - needs emerge as implementation details are worked through, even with a good initial design.

---

## 7. The PathFinder: Dijkstra over a time-expanded state

### Why Dijkstra and not A\*

A true A\* would need an admissible heuristic (for example, straight-line distance divided by the minimum movement cost). Given the size of the subject's maps (at most 25 drones, a few dozen zones), a plain Dijkstra is more than fast enough, and avoids having to design/justify a heuristic. **Pragmatic decision**: don't over-optimize a part of the system that doesn't need it.

### The explored state

Each Dijkstra node isn't just "a zone", but **a pair `(zone, turn)`**. This makes it possible to represent the fact that the same zone can be free at one turn and occupied at another.

### A classic bug: popping before the loop

Here is a real bug encountered: the priority queue was drained of its single element right after being filled, **before even entering the `while` loop**:
```python
heapq.heappush(priority_queue, (0, start_zone.name, start_turn))
cost, zone_name, turn = heapq.heappop(priority_queue)   # <-- bug: pops too early

while priority_queue:   # <-- the queue is already empty here!
    ...
```
Result: the loop never ran, and the algorithm always returned "no path found", even for simple maps. A single debug `print` (`len(best_cost)`) revealed that only one state had been explored - a clear sign the loop wasn't running.

**Lesson**: when an algorithm "never finds a solution" even on a trivial case, the first thing to check isn't the algorithm's logic itself, but **whether the main loop is actually running**. A simple print of the size of the explored structures is often enough to locate the problem in 30 seconds.

### Tuple comparability in heapq

Another technical trap: `heapq` compares tuples element by element. If two entries have the same cost, Python tries to compare the next element - if it's a `Zone` object, this crashes (no ordering defined on `Zone`). **Solution**: store the zone's **name** (a string, comparable) in the queue instead of the object itself, and look up the real object via a `{name: Zone}` dictionary built once in `__init__`.

**Lesson**: this is a very common trap with `heapq` in Python - always think about what happens on a cost tie, and make sure every element of the tuple is naturally comparable (or add a counter/tie-breaker).

---

## 8. The RoutingManager: orchestrating several drones

Once `find_path` was reliable for a single drone, all drones needed to be routed, in a given order, taking previous reservations into account.

### The question of order

Some thought was given to "in what order should drones be routed to minimize total time?" - several strategies were considered (sorting by decreasing distance, multiple attempts, various heuristics).

**Important discovery**: since the subject guarantees **a single** `start_hub` and **a single** `end_hub`, shared by all drones, **the order of routing has strictly no effect** on the overall outcome - the drones are interchangeable. A "distance to goal" sorting strategy initially proposed was therefore **useless**, since this distance is identical for every drone.

**Analysis of the observed "problem"**: on a test map, the last drone routed took far more turns than the others. This looked like a flaw in the algorithm ("greedy, no global replanning"). But a manual calculation of the theoretical limit (based on the throughput of the two available parallel routes) showed that **the result obtained was already the theoretical optimum** given the network's capacity constraints - it wasn't a bug, nor a fixable inefficiency, just the physical reality of the map's bottleneck.

**Lesson**: before spending time "optimizing" an algorithm because a result "looks" bad, it's worth first checking whether a better solution actually exists - sometimes what looks like a flaw is in fact the physical limit of the problem.

### Handling failure

If `find_path` finds no path for a drone (impossible map, structural deadlock), a dedicated `RoutingError` exception is raised, with the drone's name - rather than silently continuing in an inconsistent state.

---

## 9. The SimulationEngine: turning paths into text output

This class converts the `routes` (per-drone computed paths) into output lines matching the subject's exact format.

### Conversion rule

For each consecutive pair `(current_zone, turn) → (next_zone, next_turn)` of a path:
- **Wait** (same zone) → omitted from the output
- **Normal/priority move** (+1 turn) → a single action `D<ID>-<zone>`
- **Restricted transit** (+2 turns) → **two separate actions at two different turns**: `D<ID>-<connection>` at the first transit turn, then `D<ID>-<zone>` on arrival

### Two classic "off-by-one" bugs encountered

1. **`range(len(timed_path) - 2)`** instead of `- 1` - this bug systematically **missed the very last transition** of every path (each drone's final move was never displayed).
2. **`range(1, max_turn)`** instead of `range(1, max_turn + 1)` - since `range`'s upper bound is exclusive in Python, this **missed the final turn** of the simulation (the one where the last drone arrives).

**Lesson**: "off-by-one" errors (a one-step shift) are extremely common with loops and indices in Python. The reflex to have: to iterate over every consecutive pair of a list of length N, it's always `range(N - 1)`. To include an upper bound in a `range`, always add `+ 1` to it.

---

## 10. The visual part: Arcade

### Why Arcade over pygame (the initial idea)

Arcade offers a more modern API (sprites, animations, structured event handling via `on_draw`/`on_update`/`on_key_press`) for a reasonable porting effort - a good "visual quality vs implementation complexity" trade-off for this project.

### Progressive build-up

1. **First, a minimal version**: zones as colored circles, drones as circles, one line per connection, automatic turn-by-turn playback.
2. **Then, real sprites**: a background image, a sprite sheet for the drones (cut into frames for animation), dedicated textures per zone type.
3. **Then, interactive controls**: pause/play, manual step forward/backward via keyboard, click-and-drag (pan) with the mouse, mouse-wheel zoom centered on the cursor.
4. **Finally, a compact HUD** in a "tech/space" style rather than plain raw text.

### The most interesting interpolation bug to explain

At first, a drone's on-screen position was computed by comparing the current turn to `floor(turn)` and `floor(turn) + 1` - which works for a 1-turn move, but **completely breaks** for a 2-turn `restricted` transit: the drone appeared to "pause" halfway through the transit before "jumping" to its arrival, an inconsistent visual behavior.

**The fix**: instead of comparing against fixed 1-turn intervals, the drone's full path had to be searched for the **actual segment** containing the current turn - a segment that could last 1 turn (normal move), 2 turns (restricted transit), or 0 turns (wait) - then interpolate proportionally within that segment, whatever its real duration.

**Lesson**: a "fixed-per-turn" animation is a simplification that breaks down when the domain's events (here, transit turns) don't all last the same duration. The animation's granularity needs to match the real granularity of the events, not an arbitrary unit of time.

### A poorly typed third-party library issue

`mypy --strict` refused to compile `class Visualizer(arcade.Window)`, because the Arcade library itself doesn't expose complete types for some of its classes (they show up as `Any`). Solution: a targeted `# type: ignore[misc]` comment on that specific line, and an entry in `pyproject.toml` to disable this error code specifically for the `visualizer` module:
```toml
[[tool.mypy.overrides]]
module = "visualizer"
disable_error_code = ["attr-defined", "misc"]
```

**Lesson**: when a static-analysis tool gives results that seem to change "for no reason" between two identical runs, the cache is often the culprit - it's a debugging reflex worth having for any tool that uses one (mypy, but also compilers, bundlers, etc.).

---

## 11. Robustness and error handling

The subject stresses that a robust program **must never crash abruptly** on invalid input - every error must be handled cleanly, with a clear message rather than a raw Python traceback.

### The layers of protection put in place

1. **Parsing errors** (`OSError`, `ParseError`, `ValueError`) - caught explicitly in `main()`, clear message on `stderr`, clean exit with `sys.exit(1)`.
2. **Routing errors** (`RoutingError`)
3. **Generic safety net** - a final catch-all `except Exception`, to capture anything unanticipated (including a possible initialization error from the graphics library in a display-less environment).

**Lesson**: error handling isn't an ideal "afterthought", but in this particular project, it was in fact largely dealt with toward the end, once the functional core was stable. That's a reasonable trade-off: get the logic working first, then harden it - as long as the hardening isn't forgotten before the final submission.

---

## 12. Answering the subject's reflection questions

The subject explicitly asks a series of questions to help you evaluate your own algorithm. Here are answers based on the actual implementation.

### How efficient is the algorithm?

The core of the algorithm is a classic Dijkstra, run once per drone, over a `(zone, turn)` state space rather than just `zone`. Every availability check (`is_zone_available`, `is_connection_available`) is a plain dictionary lookup, so `O(1)` amortized. The algorithm therefore stays as efficient as a standard Dijkstra, just over a slightly larger graph (the "zones × turns" product rather than just "zones").

### Can it work with a large number of drones?

Yes - tested with 25 drones on a complex map (about thirty zones, several branches, a mini-maze, `restricted`/`priority`/`blocked` zones), with no performance issue or deadlock. The only limiting factor is the safety bound on the number of turns explored (`Z * 4`, where `Z` is the number of zones), which guarantees the search always terminates, including when no path exists.

### What is the complexity?

For a single drone: `O((Z * T) * log(Z * T))`, where `Z` is the number of zones and `T` the explored turn bound (proportional to `Z`) - this is the standard complexity of Dijkstra (`O(E log V)`) applied to a state graph of size `Z * T`. To route all drones: this search is repeated `D` times (once per drone), done sequentially, so `O(D * Z * T * log(Z * T))` overall. The capacity checks (`ReservationTable`) remain `O(1)` amortized at each step, so they don't worsen this complexity.

### Are paths recalculated, or cached?

Each drone computes its path **only once** (`find_path`), and that path is then stored as-is in the `routes` dictionary returned by `RoutingManager.route_all_drones`. There is **no recalculation**: once a drone has a path, it keeps it until the end - neither `SimulationEngine` nor `Visualizer` run a new search, they just read the already-computed paths and replay/interpolate them over time.

### What is the impact on memory usage?

Three structures dominate memory usage:
- The `ReservationTable`: two dictionaries that grow proportionally to the number of reservations made, so at worst `O(D * average path length)` entries in total - stays small even with many drones, since each drone only reserves the slots of its own path.
- The temporary structures of each search (`best_cost`, `predecessor`, the priority queue): they only live for the duration of a `find_path` call, then get freed (local scope to the method) - they don't accumulate across drones.
- The final `routes`: a list of `(zone, turn)` per drone, so proportional to the number of drones multiplied by the length of their respective paths - stays very reasonable even for 25 drones on a large map.

### How does the visual representation enhance understanding of the simulation?

See part 10 for the detailed features. In short: the text output gives the raw information (who moves where, at which turn), but doesn't *visually* show congestion, detours, or how drones distribute across parallel paths. The Arcade visualization makes this immediately visible - you can spot at a glance a jam on a low-capacity `restricted` zone, or a balanced split between two competing routes, which would take much longer to notice by only reading text lines.

### Does the algorithm meet the targeted performance goals?

On the maps tested, yes, comfortably. For example, a "hard" map with 8 drones and a mini-maze was solved in 14 turns. A simpler map with 5 drones and two parallel routes (one of them via a `restricted` zone) was solved in 6 turns - a manual calculation of the network's theoretical limit confirmed this result was already the best possible outcome given the capacity constraints, not just "a good solution".

### What optimizations were implemented?

Deliberately few, by design choice: the base Dijkstra, paired with `O(1)` capacity checks, turned out to be sufficient to stay comfortably under the targeted turn thresholds without further optimization. Rather than adding algorithmic complexity (an A\* heuristic, re-optimizing the routing order, etc.) without proof that it was necessary, priority was given to the correctness and robustness of the base algorithm. One possible optimization avenue would have been sorting or reordering the drones to reduce total time - but as explained in part 8, this would have had no effect here, since the network only has a single start and end point shared by every drone.

---