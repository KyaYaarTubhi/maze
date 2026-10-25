
"""
Lantern's End - Maze Project (Python + Pygame)

Run:      pip install pygame
          python lantern_maze_project.py             (play)
          python lantern_maze_project.py analyze     (print performance tables only)

Keys:     Menu: 1 = single player, 2 = race (compete), 3 = co-op
          P1 = WASD, P2 = Arrow keys (in single player both work)
          H = hint for P1, Right Shift = hint for P2 (A* path, costs oil)
          After a level: Y or Enter = next level, N = back to menu
          P = performance report, R = restart, Esc = quit
"""
import array
import heapq
import math
import random
import sys
import time
import tracemalloc
from collections import deque

import pygame

# ----------------------------------------------------------------- settings
WIN_W, WIN_H, HUD_H = 900, 760, 56
TILE_MAX = 40
OIL_MAX, OIL_STEP, OIL_FLASK, HINT_COST = 100.0, 0.6, 40.0, 10.0
MOVE_MS = 110

BG = (12, 14, 23)
FLOOR_LIT, FLOOR_DIM = (28, 32, 53), (18, 20, 31)
WALL_LIT, WALL_DIM = (76, 74, 104), (38, 40, 58)
AMBER, AMBER_DIM = (244, 169, 65), (176, 122, 42)
GREEN, HINT = (111, 174, 140), (120, 180, 255)
TEXT, MUTED, DANGER, EDGE = (233, 220, 196), (139, 138, 163), (198, 90, 74), (51, 49, 74)
PLAYER_COLORS = [(255, 236, 190), (110, 200, 255)]


def lerp_color(a, b, t):
    """Blend color a -> b by t (0..1)."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


CONTROLS = [
    {pygame.K_w: (0, -1), pygame.K_s: (0, 1), pygame.K_a: (-1, 0), pygame.K_d: (1, 0)},
    {pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0)},
]


# ------------------------------------------- 1. procedural maze generation
# A maze is stored as a set of open passages: ((x, y), (nx, ny)) in both directions.
def grid_neighbors(n, c):
    x, y = c
    return [(x + dx, y + dy) for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0))
            if 0 <= x + dx < n and 0 <= y + dy < n]


def gen_dfs(n):
    """Randomized DFS with backtracking (iterative, explicit stack)."""
    passages, seen, stack = set(), {(0, 0)}, [(0, 0)]
    while stack:
        c = stack[-1]
        free = [nb for nb in grid_neighbors(n, c) if nb not in seen]
        if not free:
            stack.pop()                                   # dead end -> backtrack
            continue
        nb = random.choice(free)
        passages.add((c, nb))
        passages.add((nb, c))
        seen.add(nb)
        stack.append(nb)
    return passages


def gen_prim(n):
    """Randomized Prim's algorithm (used for comparison in the analysis)."""
    passages, seen = set(), {(0, 0)}
    frontier = [((0, 0), nb) for nb in grid_neighbors(n, (0, 0))]
    while frontier:
        i = random.randrange(len(frontier))
        frontier[i], frontier[-1] = frontier[-1], frontier[i]
        a, b = frontier.pop()
        if b in seen:
            continue
        seen.add(b)
        passages.add((a, b))
        passages.add((b, a))
        frontier += [(b, nb) for nb in grid_neighbors(n, b) if nb not in seen]
    return passages


# ------------------------------------------------------- 2. pathfinding
def open_neighbors(passages, c):
    x, y = c
    return [(x + dx, y + dy) for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0))
            if (c, (x + dx, y + dy)) in passages]


def build_path(prev, goal):
    path = []
    while goal is not None:
        path.append(goal)
        goal = prev[goal]
    return path[::-1]


def solve_bfs(passages, start, goal):
    prev, queue, expanded = {start: None}, deque([start]), 0
    while queue:
        c = queue.popleft()
        expanded += 1
        if c == goal:
            break
        for nb in open_neighbors(passages, c):
            if nb not in prev:
                prev[nb] = c
                queue.append(nb)
    return build_path(prev, goal), expanded


def solve_dfs(passages, start, goal):
    prev, stack, expanded = {start: None}, [start], 0
    while stack:
        c = stack.pop()
        expanded += 1
        if c == goal:
            break
        for nb in open_neighbors(passages, c):
            if nb not in prev:
                prev[nb] = c
                stack.append(nb)
    return build_path(prev, goal), expanded


def solve_heap(passages, start, goal, use_heuristic):
    """Dijkstra (use_heuristic=False) or A* with Manhattan distance (True)."""
    h = (lambda c: abs(c[0] - goal[0]) + abs(c[1] - goal[1])) if use_heuristic else (lambda c: 0)
    dist, prev, done, expanded = {start: 0}, {start: None}, set(), 0
    heap = [(h(start), start)]
    while heap:
        _, c = heapq.heappop(heap)
        if c in done:
            continue
        done.add(c)
        expanded += 1
        if c == goal:
            break
        for nb in open_neighbors(passages, c):
            nd = dist[c] + 1
            if nd < dist.get(nb, 10 ** 9):
                dist[nb], prev[nb] = nd, c
                heapq.heappush(heap, (nd + h(nb), nb))
    return build_path(prev, goal), expanded


SOLVERS = {
    "BFS": solve_bfs,
    "DFS": solve_dfs,
    "Dijkstra": lambda p, s, g: solve_heap(p, s, g, False),
    "A*": lambda p, s, g: solve_heap(p, s, g, True),
}


# ------------------------------------------------- 3. performance analysis
def measure(func, *args):
    """Returns (result, time in ms, peak memory in KB)."""
    t0 = time.perf_counter()
    out = func(*args)
    ms = (time.perf_counter() - t0) * 1000
    tracemalloc.start()
    func(*args)
    kb = tracemalloc.get_traced_memory()[1] / 1024
    tracemalloc.stop()
    return out, ms, kb


def run_analysis(sizes=(10, 20, 40, 80)):
    lines = ["MAZE GENERATION - time (ms) and peak memory (KB)",
             f"{'N x N':>7} | {'DFS backtracking':^24} | {'Randomized Prim':^24}"]
    mazes = {}
    for n in sizes:
        m, t1, k1 = measure(gen_dfs, n)
        _, t2, k2 = measure(gen_prim, n)
        mazes[n] = m
        lines.append(f"{n:>7} | {t1:>10.2f} ms {k1:>7.0f} KB | {t2:>10.2f} ms {k2:>7.0f} KB")

    lines += ["", "PATHFINDING (start to exit) - nodes expanded / time (ms)",
              f"{'N x N':>7} | " + " | ".join(f"{name:^14}" for name in SOLVERS)]
    nodes_at = {}
    for n in sizes:
        cells = []
        for name, fn in SOLVERS.items():
            (path, nodes), ms, _ = measure(fn, mazes[n], (0, 0), (n - 1, n - 1))
            nodes_at[(name, n)] = nodes
            cells.append(f"{nodes:>6}/{ms:>6.2f}")
        lines.append(f"{n:>7} | " + " | ".join(f"{c:^14}" for c in cells))

    big = sizes[-1]
    lines += ["", f"At {big}x{big}: A* expanded {nodes_at[('A*', big)] / nodes_at[('BFS', big)]:.0%} "
                  f"of the nodes BFS expanded."]
    return lines


# ------------------------------------------------------ 4. sound and music
class Audio:
    """Sound effects and ambient music generated in code (no audio files needed)."""

    def __init__(self):
        self.on, self.sounds = False, {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.rate, fmt, self.ch = pygame.mixer.get_init()
            if fmt != -16:
                return
            self.sounds = {
                "step": self.notes([(220, 25)], 0.15),
                "flask": self.notes([(660, 70), (880, 110)], 0.30),
                "hint": self.notes([(500, 60), (400, 60), (500, 90)], 0.25),
                "win": self.notes([(523, 120), (659, 120), (784, 120), (1046, 300)], 0.35),
            }
            music = self.drone()
            music.set_volume(0.25)
            music.play(-1)
            self.on = True
        except Exception:
            self.on = False

    def notes(self, seq, vol):
        buf = array.array("h")
        for freq, ms in seq:
            n = int(self.rate * ms / 1000)
            for i in range(n):
                v = int(32767 * vol * (1 - i / n) * math.sin(2 * math.pi * freq * i / self.rate))
                buf.extend([v] * self.ch)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def drone(self):
        buf = array.array("h")
        for i in range(self.rate * 4):                       # 4 s loop, whole cycles
            t = i / self.rate
            v = (math.sin(2 * math.pi * 55 * t) + 0.6 * math.sin(2 * math.pi * 82.5 * t)) \
                * (0.7 + 0.3 * math.sin(2 * math.pi * 0.5 * t))
            buf.extend([int(32767 * 0.25 * v / 1.6)] * self.ch)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play(self, name):
        if self.on:
            self.sounds[name].play()


# ------------------------------------------------------------------- game
class Game:
    def __init__(self):
        self.font = pygame.font.SysFont("segoeui,arial,sans-serif", 20)
        self.small = pygame.font.SysFont("segoeui,arial,sans-serif", 15)
        self.title = pygame.font.SysFont("georgia,cambria,serif", 46, bold=True)
        self.mono = pygame.font.SysFont("consolas,couriernew,monospace", 15)
        self.audio = Audio()
        self.glows = {}
        self.state, self.mode, self.level = "menu", 1, 1
        self.show_report, self.report = False, None
        self.players, self.particles = [], []
        self.light = {}
        self.hint_path, self.hint_ms, self.hint_info = set(), 0, ""
        self.clock_ms, self.winner = 0, None

    # ------------------------------------------------------------- setup
    def start(self, mode, level=1):
        self.mode, self.level = mode, level
        self.n = min(11 + 2 * level, 25)                       # maze grows with each level
        self.passages = gen_dfs(self.n)
        self.exit = (self.n - 1, self.n - 1)
        self.radius = max(3.2, 5.2 - 0.18 * level)             # light shrinks with each level
        self.tile = min(TILE_MAX, (WIN_W - 40) // self.n, (WIN_H - HUD_H - 30) // self.n)
        self.ox = (WIN_W - self.tile * self.n) // 2
        self.oy = HUD_H + (WIN_H - HUD_H - self.tile * self.n) // 2
        count = max(2, 4 - level // 2) + (0 if mode == 1 else 2)
        self.players = [dict(pos=(0, 0), oil=OIL_MAX, steps=0, cool=0, done=False, color=c)
                        for c in PLAYER_COLORS[:1 if mode == 1 else 2]]
        self.flasks = set()
        while len(self.flasks) < count:
            f = (random.randrange(self.n), random.randrange(self.n))
            if f not in ((0, 0), self.exit):
                self.flasks.add(f)
        self.light, self.particles = {}, []
        self.hint_path, self.hint_ms, self.hint_info = set(), 0, ""
        self.glows.clear()
        self.clock_ms, self.winner, self.state = 0, None, "play"
        self.refresh_light()

    # ---------------------------------------------------------- gameplay
    def refresh_light(self):
        """Gradual fog of war: brightness (0..1) of each tile fades with distance
        from the nearest lantern. Tiles outside every lantern are fully dark."""
        self.light = {}
        for p in self.players:
            r = self.radius if p["oil"] > 0 else 1.0           # no oil -> nearly blind
            px, py = p["pos"]
            R = int(r) + 1
            for x in range(max(0, px - R), min(self.n, px + R + 1)):
                for y in range(max(0, py - R), min(self.n, py + R + 1)):
                    d = math.hypot(x - px, y - py)
                    t = 1 - d / (r + 0.5)
                    if t <= 0:
                        continue
                    b = t * t * (3 - 2 * t)                     # smoothstep falloff
                    if b > self.light.get((x, y), 0):
                        self.light[(x, y)] = b

    def keymap(self, i):
        return {**CONTROLS[0], **CONTROLS[1]} if self.mode == 1 else CONTROLS[i]

    def move(self, i, d):
        p = self.players[i]
        new = (p["pos"][0] + d[0], p["pos"][1] + d[1])
        if (p["pos"], new) not in self.passages:               # wall blocks the move
            return False
        p["pos"] = new
        p["oil"] = max(0.0, p["oil"] - OIL_STEP)
        p["steps"] += 1
        self.audio.play("step")
        if new in self.flasks:
            self.flasks.discard(new)
            p["oil"] = min(OIL_MAX, p["oil"] + OIL_FLASK)
            self.burst(new, AMBER)
            self.audio.play("flask")
        if new == self.exit:
            p["done"] = True
            self.burst(new, GREEN)
            if self.mode != 3:                                  # solo / race: first one wins
                self.winner = i
                self.finish()
            elif all(q["done"] for q in self.players):          # co-op: both must escape
                self.finish()
        self.refresh_light()
        return True

    def finish(self):
        self.state = "won"                                      # shows the "next level?" prompt
        self.audio.play("win")

    def use_hint(self, i):
        """Show the shortest path to the exit (A*), at the cost of some oil."""
        if self.state != "play" or i >= len(self.players):
            return
        p = self.players[i]
        if p["done"] or p["oil"] < HINT_COST:
            return
        p["oil"] -= HINT_COST
        path, a_star = solve_heap(self.passages, p["pos"], self.exit, True)
        _, bfs = solve_bfs(self.passages, p["pos"], self.exit)
        self.hint_path, self.hint_ms = set(path), 3000
        self.hint_info = f"Hint: A* {a_star} nodes, BFS {bfs}"
        self.audio.play("hint")
        self.refresh_light()

    def burst(self, cell, color):
        cx, cy = self.cell_rect(cell).center
        for _ in range(14):
            a, v = random.uniform(0, 6.28), random.uniform(30, 120)
            self.particles.append([cx, cy, math.cos(a) * v, math.sin(a) * v, 600, color])

    def update(self, dt, keys):
        if self.show_report:
            return
        for q in self.particles:
            q[0] += q[2] * dt / 1000
            q[1] += q[3] * dt / 1000
            q[4] -= dt
        self.particles = [q for q in self.particles if q[4] > 0]
        if self.hint_ms > 0:
            self.hint_ms -= dt
            if self.hint_ms <= 0:
                self.hint_path = set()
        if self.state != "play":
            return
        self.clock_ms += dt
        for i, p in enumerate(self.players):
            p["cool"] = max(0, p["cool"] - dt)
            if p["cool"] == 0 and not p["done"]:
                for key, d in self.keymap(i).items():
                    if keys[key]:
                        self.move(i, d)
                        p["cool"] = MOVE_MS
                        break

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
        if key == pygame.K_p:
            self.show_report = not self.show_report
            if self.show_report and self.report is None:
                self.report = run_analysis()
                print("\n".join(self.report))
            return
        if self.show_report:
            return
        if self.state == "menu":
            if key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.start(key - pygame.K_0)
        elif self.state == "won":                               # "Play the next level?" prompt
            if key in (pygame.K_y, pygame.K_RETURN, pygame.K_SPACE):
                self.start(self.mode, self.level + 1)           # yes -> new, harder level
            elif key == pygame.K_n:
                self.state = "menu"                             # no -> back to the menu
            elif key == pygame.K_r:
                self.start(self.mode)                           # restart from level 1
        elif key == pygame.K_r:
            self.start(self.mode)
        elif key == pygame.K_h:
            self.use_hint(0)
        elif key == pygame.K_RSHIFT:
            self.use_hint(1)

    # ----------------------------------------------------------- drawing
    def cell_rect(self, c):
        return pygame.Rect(self.ox + c[0] * self.tile, self.oy + c[1] * self.tile, self.tile, self.tile)

    def glow(self, r):
        r = max(4, int(r) // 4 * 4)
        if r not in self.glows:
            surf = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
            for i in range(24, 0, -1):                          # outer -> inner
                pygame.draw.circle(surf, (*AMBER, int(60 * (1 - i / 24) ** 1.5)), (r, r), int(r * i / 24))
            self.glows[r] = surf
        return self.glows[r]

    def draw_maze(self, s):
        t = self.tile
        for c, b in self.light.items():                         # only tiles near a lantern
            r = self.cell_rect(c)
            pygame.draw.rect(s, lerp_color(BG, FLOOR_LIT, b), r)
            col = lerp_color(BG, WALL_LIT, b)
            x, y = c
            for (dx, dy), a, e in (((0, -1), r.topleft, r.topright), ((0, 1), r.bottomleft, r.bottomright),
                                   ((-1, 0), r.topleft, r.bottomleft), ((1, 0), r.topright, r.bottomright)):
                if (c, (x + dx, y + dy)) not in self.passages:
                    pygame.draw.line(s, col, a, e, 3)

        for c in self.hint_path:                                # A* hint path
            pygame.draw.circle(s, HINT, self.cell_rect(c).center, max(2, t // 8))

        ex = self.cell_rect(self.exit).center                   # exit: always visible
        pygame.draw.circle(s, GREEN, ex, int(t * 0.32), 2)
        pygame.draw.circle(s, GREEN, ex, int(t * 0.15))

        for c in self.flasks:                                   # oil flasks: always visible
            cx, cy = self.cell_rect(c).center
            col = AMBER if self.light.get(c, 0) > 0.3 else AMBER_DIM
            pygame.draw.circle(s, col, (cx, cy - t // 8), max(3, t // 6))
            pygame.draw.rect(s, col, (cx - 2, cy - t // 8, 4, max(5, t // 3)))

        for p in self.players:                                  # flickering lantern + player
            cx, cy = self.cell_rect(p["pos"]).center
            flick = 1 + 0.04 * math.sin(self.clock_ms / 90) + random.uniform(-0.015, 0.015)
            g = self.glow((self.radius + 1) * t * flick if p["oil"] > 0 else 1.6 * t)
            s.blit(g, (cx - g.get_width() // 2, cy - g.get_height() // 2))
            pygame.draw.circle(s, p["color"], (cx, cy), max(4, t // 4))

        for x, y, _, _, life, col in self.particles:            # visual effects
            pygame.draw.circle(s, col, (int(x), int(y)), 3)

    def draw_hud(self, s):
        pygame.draw.rect(s, (16, 18, 30), (0, 0, WIN_W, HUD_H))
        pygame.draw.line(s, EDGE, (0, HUD_H), (WIN_W, HUD_H))
        s.blit(self.font.render(f"Level {self.level}", True, TEXT), (16, 6))
        secs = self.clock_ms // 1000
        s.blit(self.small.render(f"{secs // 60}:{secs % 60:02d}", True, MUTED), (16, 32))
        for i, p in enumerate(self.players):
            x = 130 + i * 230
            label = "OIL" if len(self.players) == 1 else f"P{i + 1} OIL"
            s.blit(self.small.render(label, True, p["color"]), (x, 8))
            bar = pygame.Rect(x, 30, 170, 12)
            pygame.draw.rect(s, (31, 34, 51), bar, border_radius=5)
            frac = p["oil"] / OIL_MAX
            pygame.draw.rect(s, DANGER if frac < 0.2 else AMBER,
                             (bar.x, bar.y, int(bar.w * frac), bar.h), border_radius=5)
            pygame.draw.rect(s, EDGE, bar, 1, border_radius=5)
        for text, y, col in (("R restart   H hint   P report", 8, MUTED), (self.hint_info, 32, HINT)):
            img = self.small.render(text, True, col)
            s.blit(img, (WIN_W - img.get_width() - 16, y))

    def overlay(self, s, title, lines):
        shade = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        shade.fill((8, 9, 15, 230))
        s.blit(shade, (0, 0))
        t = self.title.render(title, True, TEXT)
        s.blit(t, t.get_rect(center=(WIN_W // 2, 170)))
        for i, line in enumerate(lines):
            img = self.font.render(line, True, AMBER if line.startswith("Play the next") else MUTED)
            s.blit(img, img.get_rect(center=(WIN_W // 2, 250 + i * 30)))

    def draw(self, s):
        s.fill(BG)
        if self.state != "menu":
            self.draw_maze(s)
            self.draw_hud(s)
        if self.state == "menu":
            self.overlay(s, "Lantern's End", [
                "Find the exit before your oil runs out. The exit and oil flasks glow in the dark.",
                "Your lantern lights only the tiles near you - walk away and they go dark again.", "",
                "1   Single player",
                "2   Two players - race to the exit   (P1: WASD, P2: arrow keys)",
                "3   Two players - co-op, both must escape", "",
                "H = hint (A* path, costs oil)    P = performance report    R = restart"])
        elif self.state == "won":
            if self.mode == 2:
                who = f"Player {self.winner + 1} escaped first!"
            else:
                who = "You escaped!" if self.mode == 1 else "Both players escaped!"
            steps = "   ".join(f"P{i + 1}: {p['steps']} steps" for i, p in enumerate(self.players))
            secs = self.clock_ms // 1000
            self.overlay(s, f"Level {self.level} complete!", [
                who,
                f"Time {secs // 60}:{secs % 60:02d}   {steps}",
                "",
                f"Level {self.level + 1} has a bigger maze and a dimmer lantern.",
                "Play the next level?     Y = Yes        N = No (back to menu)"])
        if self.show_report:
            shade = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            shade.fill((8, 9, 15, 245))
            s.blit(shade, (0, 0))
            s.blit(self.title.render("Performance analysis", True, TEXT), (40, 30))
            for i, line in enumerate(self.report):
                s.blit(self.mono.render(line, True, TEXT if line.startswith(("MAZE", "PATH")) else MUTED),
                       (40, 110 + i * 22))
            s.blit(self.small.render("Press P to close", True, AMBER), (40, WIN_H - 40))
        pygame.display.flip()


def main():
    if "analyze" in sys.argv:
        print("\n".join(run_analysis()))
        return
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Lantern's End")
    game, clock = Game(), pygame.time.Clock()
    while True:
        dt = clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                game.handle_key(e.key)
        game.update(dt, pygame.key.get_pressed())
        game.draw(screen)


if __name__ == "__main__":
    main()