# Lantern's End — Maze Exploration Game

A Python maze game built with **Pygame**. Navigate a procedurally generated maze while managing lantern oil. The lantern reveals only nearby tiles, oil flasks restore fuel, and the exit must be found before the oil runs out.

## Features

- **Procedural maze generation:** randomized depth-first search (DFS) with backtracking.
- **Generation comparison:** randomized Prim's algorithm is also implemented for performance comparison.
- **Three game modes:**
  1. Single player
  2. Two-player race to the exit
  3. Cooperative mode, where both players must escape
- **Fog of war / lantern lighting:** only tiles near a player are illuminated; the visible radius shrinks as the oil runs out.
- **Oil management:** movement consumes oil and collecting an oil flask restores it.
- **Pathfinding hints:** A* computes a route to the exit and displays it briefly; using a hint consumes oil.
- **Four pathfinding approaches:** Breadth-First Search (BFS), Depth-First Search (DFS), Dijkstra's algorithm, and A*.
- **Procedural sound:** sound effects and ambient audio are generated in code; no separate audio files are required.
- **Performance report:** compares maze generation time and peak memory, and pathfinding nodes expanded and execution time.
- **Progressive difficulty:** each completed level increases maze size and reduces lantern radius.

## Requirements

- Python 3.9 or newer recommended
- Pygame

## Installation

1. Install Python from [python.org](https://www.python.org/) if it is not already installed.
2. Open a terminal in the project folder.
3. Install the dependency:

```bash
python -m pip install pygame
```

## Run the game

Run the Python file (use the actual filename in your local folder):

```bash
python maze_game2.py
```

If your local file is named `lantern_maze_project.py`, use:

```bash
python lantern_maze_project.py
```

Run the performance analysis without opening the game window:

```bash
python lantern_maze_project.py analyze
```

Replace the filename in these commands if needed. The repository screenshot shows `maze_game2.py` as the tracked source file.

## Controls

| Key | Action |
|---|---|
| `1` | Start single-player mode |
| `2` | Start two-player race mode |
| `3` | Start cooperative mode |
| `W`, `A`, `S`, `D` | Player 1 movement |
| Arrow keys | Player 2 movement |
| `H` | Show Player 1's A* hint (costs oil) |
| `Right Shift` | Show Player 2's A* hint (costs oil) |
| `R` | Restart the current game from level 1 |
| `P` | Open/close performance report |
| `Y`, `Enter`, or `Space` | Start the next level after completing a level |
| `N` | Return to the menu after completing a level |
| `Esc` | Quit |

In single-player mode, both WASD and arrow-key mappings can control the player.

## How to play

1. Select a game mode from the title screen.
2. Move through the maze using the controls.
3. Use the illuminated area to identify nearby corridors and walls.
4. Collect oil flasks to replenish the lantern.
5. Use a hint only when needed because it consumes oil.
6. Reach the green exit marker. In cooperative mode, both players must reach the exit.
7. Continue to the next level for a larger maze and a dimmer lantern.

## Algorithms

### Maze generation: randomized DFS with backtracking

The maze is represented as a set of directed passage pairs between adjacent grid cells. The DFS generator starts at `(0, 0)`, maintains an explicit stack, randomly chooses an unvisited neighbour, opens a passage in both directions, and backtracks when no unvisited neighbours remain.

### Alternative generator: randomized Prim

The Prim generator maintains a frontier of candidate edges. It selects a random frontier edge, adds the destination cell if it has not already been visited, opens the passage, and adds the destination's unvisited neighbours to the frontier. It is included to compare generation performance.

### Pathfinding

- **BFS:** explores in breadth-first order and finds a shortest path in an unweighted maze.
- **DFS:** explores depth-first. It can find a route, but does not generally guarantee a shortest route.
- **Dijkstra:** uses a priority queue and zero heuristic; with equal unit edge costs it finds a shortest path.
- **A\*:** uses a priority queue with Manhattan distance as its heuristic. For this four-direction grid and unit-cost movement, Manhattan distance is an appropriate heuristic.

The solver functions return a reconstructed path and the number of expanded nodes.

## Performance analysis

The built-in report evaluates maze sizes `10×10`, `20×20`, `40×40`, and `80×80`.

- **Maze generation:** elapsed time in milliseconds and peak memory in KB for DFS backtracking and randomized Prim.
- **Pathfinding:** expanded nodes and elapsed time for BFS, DFS, Dijkstra, and A*.
- The report is generated on the current machine, so values can vary between runs and hardware. The screenshot in the project materials records one run; it should not be treated as a universal benchmark.

## Project structure

```text
maze/
├── .gitignore
├── maze_game2.py       # main Pygame game source (as shown in repository screenshot)
├── README.md           # project documentation
└── npm-debug.log       # shown in the repository screenshot; normally not required for a Python-only project
```

The code supplied for documentation identifies the main module as `lantern_maze_project.py`, while the GitHub screenshot shows `maze_game2.py`. Ensure the filename used in commands matches the file actually present in the repository. The `npm-debug.log` file is not required by this Python/Pygame game and can generally be removed from version control if it was created accidentally.

## Technology stack

- **Language:** Python
- **Game / graphics library:** Pygame
- **Standard-library modules:** `array`, `heapq`, `math`, `random`, `sys`, `time`, `tracemalloc`, and `collections.deque`
- **Algorithms:** randomized DFS, randomized Prim, BFS, DFS, Dijkstra, A*
- **Version control / hosting:** Git and GitHub

## Limitations

- Performance figures vary by computer, Python version, and random maze layout.
- The game uses keyboard controls and is designed as a desktop application.
- The lantern makes navigation intentionally difficult; the maze is not fully visible at once.
- Hints consume oil, so frequent use can make completing a level harder.
- Audio initialization depends on the available audio device; the code handles audio setup failures by continuing without sound.
- The project does not currently document automated unit tests or a packaged installer.

## Future enhancements

- Add a settings screen for sound volume, difficulty, and control remapping.
- Save high scores, completion times, and best routes.
- Add additional maze-generation algorithms and benchmark repeated trials with averages.
- Add automated tests for generators, path reconstruction, movement rules, and oil accounting.
- Improve accessibility with optional high-contrast lighting and adjustable text size.
- Package the game for Windows and other desktop platforms.

