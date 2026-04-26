DISPLAY_NAME = "Quetsy Batsy"

import random
from collections import deque
from OpenGL.GLUT import GLUT_KEY_LEFT, GLUT_KEY_RIGHT, GLUT_KEY_UP, GLUT_KEY_DOWN
from engine.input import is_key, is_special
from engine.renderer import (
    draw_circle,
    draw_filled_circle,
    draw_filled_polygon,
    draw_polygon,
    draw_rect,
    draw_text,
)
from engine.window import WORLD_LEFT, WORLD_RIGHT, WORLD_BOTTOM, WORLD_TOP


# ─────────────────────────────────────────────
#  MAZE
# ─────────────────────────────────────────────

class Maze:
    """Generates and manages a maze using recursive backtracking."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        # 0 = wall, 1 = path, 2 = spikes, 3 = roost, 4 = wind
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        self.obstacles = {}
        self._generate()
        self._create_loops()
        self._add_obstacles()

    def _generate(self):
        start_x, start_y = 1, 1
        self.grid[start_y][start_x] = 1
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack[-1]
            neighbors = []
            for dx, dy in [(0, -2), (2, 0), (0, 2), (-2, 0)]:
                nx, ny = x + dx, y + dy
                if 0 < nx < self.width - 1 and 0 < ny < self.height - 1:
                    if self.grid[ny][nx] == 0:
                        neighbors.append((nx, ny, dx, dy))

            if neighbors:
                nx, ny, dx, dy = random.choice(neighbors)
                self.grid[y + dy // 2][x + dx // 2] = 1
                self.grid[ny][nx] = 1
                stack.append((nx, ny))
            else:
                stack.pop()

    def _create_loops(self):
        path_tiles = []
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[y][x] == 1:
                    path_tiles.append((x, y))

        loop_count = max(1, len(path_tiles) // 15)
        for _ in range(loop_count):
            if not path_tiles:
                break
            x, y = random.choice(path_tiles)
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            random.shuffle(directions)
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                mid_x, mid_y = x + dx // 2, y + dy // 2
                if (0 < nx < self.width - 1 and 0 < ny < self.height - 1 and
                        self.grid[ny][nx] == 1 and self.grid[mid_y][mid_x] == 0):
                    self.grid[mid_y][mid_x] = 1
                    break

    def _add_obstacles(self):
        path_tiles = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 1:
                    path_tiles.append((x, y))

        cluster_count = max(1, len(path_tiles) // 100)
        for _ in range(cluster_count):
            if not path_tiles:
                break
            cx, cy = random.choice(path_tiles)
            for dx, dy in [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)]:
                x, y = cx + dx, cy + dy
                if (x, y) in path_tiles and random.random() < 0.6:
                    path_tiles.remove((x, y))
                    self.grid[y][x] = 2

        spike_count = len(path_tiles) // 25
        for _ in range(spike_count):
            if not path_tiles:
                break
            x, y = random.choice(path_tiles)
            path_tiles.remove((x, y))
            self.grid[y][x] = 2

        roost_count = len(path_tiles) // 35
        for _ in range(roost_count):
            if not path_tiles:
                break
            x, y = random.choice(path_tiles)
            path_tiles.remove((x, y))
            self.grid[y][x] = 3

        wind_count = len(path_tiles) // 30
        for _ in range(wind_count):
            if not path_tiles:
                break
            x, y = random.choice(path_tiles)
            path_tiles.remove((x, y))
            self.grid[y][x] = 4
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
            self.obstacles[(x, y)] = {
                "type": "wind",
                "direction": random.choice(directions),
            }

    def is_walkable(self, x, y):
        return (0 <= x < self.width and 0 <= y < self.height and
                self.grid[y][x] in (1, 2, 3, 4))

    def find_path_between(self, start, end):
        queue = deque([start])
        visited = {start}
        parent = {start: None}

        while queue:
            current = queue.popleft()
            if current == end:
                path = []
                while current is not None:
                    path.append(current)
                    current = parent[current]
                return path[::-1]

            x, y = current
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                next_pos = (nx, ny)
                if self.is_walkable(nx, ny) and next_pos not in visited:
                    visited.add(next_pos)
                    parent[next_pos] = current
                    queue.append(next_pos)

        return []


# ─────────────────────────────────────────────
#  GAME STATE
# ─────────────────────────────────────────────

_state = {}

BAT_COLORS = {
    1: {"body": (0.0, 1.0, 1.0), "wing": (0.0, 0.7, 0.9)},      # Cyan
    2: {"body": (0.9, 0.3, 1.0), "wing": (0.7, 0.1, 0.9)},      # Magenta
    3: {"body": (1.0, 1.0, 0.0), "wing": (0.9, 0.85, 0.0)},     # Yellow
}


def _key_just_pressed(key):
    current = is_key(key)
    prev = _state["prev_keys"].get(key, False)
    _state["prev_keys"][key] = current
    return current and not prev


def _special_just_pressed(key):
    current = is_special(key)
    prev = _state["prev_special"].get(key, False)
    _state["prev_special"][key] = current
    return current and not prev


def init():
    maze_w = 31
    maze_h = 23

    _state.clear()
    _state["maze"] = Maze(maze_w, maze_h)
    _state["maze_w"] = maze_w
    _state["maze_h"] = maze_h

    _state["player"] = _find_start(_state["maze"])
    _state["exit"] = _find_exit(_state["maze"], _state["player"])

    _state["health"] = 100
    _state["max_health"] = 100

    _state["revealed"] = set()
    _state["quantum_revealed"] = set()
    _state["sonar_range"] = 2
    _state["vision_range"] = 1
    _state["sonar_cooldown"] = 0
    _state["sonar_max_cooldown"] = 2

    _state["echo_charges"] = 3
    _state["echo_segment_len"] = 8

    _state["tunnel_charges"] = 1
    _state["tunneling"] = False

    _state["moves"] = 0
    _state["game_over"] = False
    _state["won"] = False

    _state["time"] = 0

    _state["prev_keys"] = {}
    _state["prev_special"] = {}

    _state["bat_color_index"] = 2  # Default to Magenta

    _state["hud_h"] = 70
    _state["cell_size"] = _calc_cell_size(maze_w, maze_h, _state["hud_h"])
    _state["origin_x"] = WORLD_LEFT + 20
    _state["origin_y"] = WORLD_BOTTOM + _state["hud_h"] + 10

    _reveal_around_player()


def _calc_cell_size(maze_w, maze_h, hud_h):
    world_w = WORLD_RIGHT - WORLD_LEFT - 40
    world_h = WORLD_TOP - WORLD_BOTTOM - hud_h - 20
    return min(world_w / maze_w, world_h / maze_h)


def _find_start(maze):
    for y in range(1, maze.height - 1):
        for x in range(1, maze.width - 1):
            if maze.is_walkable(x, y):
                return (x, y)
    return (1, 1)


def _find_exit(maze, player_pos):
    max_distance = 0
    exit_pos = player_pos
    for _ in range(120):
        x = random.randrange(1, maze.width - 1)
        y = random.randrange(1, maze.height - 1)
        if maze.is_walkable(x, y):
            dist = abs(x - player_pos[0]) + abs(y - player_pos[1])
            if dist > max_distance:
                max_distance = dist
                exit_pos = (x, y)
    return exit_pos


def _reveal_around_player():
    px, py = _state["player"]
    r = _state["vision_range"]
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            nx, ny = px + dx, py + dy
            if 0 <= nx < _state["maze_w"] and 0 <= ny < _state["maze_h"]:
                _state["revealed"].add((nx, ny))


def _use_sonar():
    if _state["sonar_cooldown"] > 0:
        return

    _state["sonar_cooldown"] = _state["sonar_max_cooldown"]
    px, py = _state["player"]
    r = _state["sonar_range"]
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            nx, ny = px + dx, py + dy
            if 0 <= nx < _state["maze_w"] and 0 <= ny < _state["maze_h"]:
                if _state["maze"].is_walkable(nx, ny):
                    _state["revealed"].add((nx, ny))


def _use_echo():
    if _state["echo_charges"] <= 0:
        return

    path = _state["maze"].find_path_between(_state["exit"], _state["player"])
    if not path:
        return

    segment_start = min(len(path) // 3, _state["echo_segment_len"])
    segment_end = min(segment_start + _state["echo_segment_len"], max(len(path) - 4, segment_start))

    for pos in path[segment_start:segment_end]:
        _state["quantum_revealed"].add(pos)

    _state["echo_charges"] -= 1


def _activate_tunnel():
    if _state["tunnel_charges"] <= 0:
        return

    _state["tunneling"] = True
    _state["tunnel_charges"] -= 1


def _apply_obstacle_effects(x, y):
    tile = _state["maze"].grid[y][x]

    if tile == 2:
        _state["health"] -= 15
    elif tile == 3:
        heal = min(20, _state["max_health"] - _state["health"])
        _state["health"] += heal
        _state["maze"].grid[y][x] = 1
    elif tile == 4:
        obstacle = _state["maze"].obstacles.get((x, y))
        if obstacle:
            dx, dy = obstacle["direction"]
            nx, ny = x + dx, y + dy
            if _state["maze"].is_walkable(nx, ny):
                _state["player"] = (nx, ny)
                _reveal_around_player()

    if _state["health"] <= 0:
        _state["game_over"] = True


def _move_player(dx, dy):
    if _state["game_over"]:
        return

    px, py = _state["player"]
    nx, ny = px + dx, py + dy
    maze = _state["maze"]

    if _state["tunneling"]:
        if 0 < nx < maze.width - 1 and 0 < ny < maze.height - 1:
            _state["player"] = (nx, ny)
            _state["tunneling"] = False
        else:
            return
    else:
        if not maze.is_walkable(nx, ny):
            return
        _state["player"] = (nx, ny)

    _state["moves"] += 1
    if _state["sonar_cooldown"] > 0:
        _state["sonar_cooldown"] -= 1

    _reveal_around_player()
    _apply_obstacle_effects(nx, ny)

    if _state["player"] == _state["exit"]:
        _state["won"] = True
        _state["game_over"] = True


# ─────────────────────────────────────────────
#  ENGINE API
# ─────────────────────────────────────────────


def update():
    if not _state:
        init()

    _state["time"] += 1

    if _state["game_over"]:
        if _key_just_pressed(b"r") or _key_just_pressed(b"R"):
            init()
        return

    if _key_just_pressed(b" "):
        _use_sonar()

    if _key_just_pressed(b"q") or _key_just_pressed(b"Q"):
        _use_echo()

    if _key_just_pressed(b"e") or _key_just_pressed(b"E"):
        _activate_tunnel()

    if _key_just_pressed(b"c") or _key_just_pressed(b"C"):
        _state["bat_color_index"] = 1
    elif _key_just_pressed(b"m") or _key_just_pressed(b"M"):
        _state["bat_color_index"] = 2
    elif _key_just_pressed(b"y") or _key_just_pressed(b"Y"):
        _state["bat_color_index"] = 3

    if _key_just_pressed(b"w") or _special_just_pressed(GLUT_KEY_UP):
        _move_player(0, -1)
    elif _key_just_pressed(b"s") or _special_just_pressed(GLUT_KEY_DOWN):
        _move_player(0, 1)
    elif _key_just_pressed(b"a") or _special_just_pressed(GLUT_KEY_LEFT):
        _move_player(-1, 0)
    elif _key_just_pressed(b"d") or _special_just_pressed(GLUT_KEY_RIGHT):
        _move_player(1, 0)


def _cell_to_world(x, y):
    origin_x = _state["origin_x"]
    origin_y = _state["origin_y"]
    cell = _state["cell_size"]
    world_x = origin_x + x * cell
    world_y = origin_y + (_state["maze_h"] - 1 - y) * cell
    return world_x, world_y


def _draw_bat(px, py):
    cell = _state["cell_size"]
    cx = px + cell * 0.5
    cy = py + cell * 0.5
    wing_offset = 2.0 * (1 + ((-1) ** (_state["time"] // 8)))

    colors = BAT_COLORS.get(_state["bat_color_index"], BAT_COLORS[2])
    body_color = colors["body"]
    wing_color = colors["wing"]

    draw_filled_circle(cx, cy, cell * 0.28, color=body_color)

    left_wing = [
        (cx - cell * 0.15, cy + wing_offset),
        (cx - cell * 0.65, cy + cell * 0.25 + wing_offset),
        (cx - cell * 0.35, cy - cell * 0.05),
    ]
    right_wing = [
        (cx + cell * 0.15, cy + wing_offset),
        (cx + cell * 0.65, cy + cell * 0.25 + wing_offset),
        (cx + cell * 0.35, cy - cell * 0.05),
    ]
    draw_filled_polygon(left_wing, color=wing_color)
    draw_filled_polygon(right_wing, color=wing_color)

    draw_filled_circle(cx - cell * 0.1, cy + cell * 0.05, cell * 0.05, color=(1.0, 0.7, 0.7))
    draw_filled_circle(cx + cell * 0.1, cy + cell * 0.05, cell * 0.05, color=(1.0, 0.7, 0.7))


def draw():
    if not _state:
        init()

    maze = _state["maze"]
    cell = _state["cell_size"]

    draw_rect(WORLD_LEFT, WORLD_BOTTOM, WORLD_RIGHT - WORLD_LEFT, WORLD_TOP - WORLD_BOTTOM,
              color=(0.03, 0.03, 0.06), filled=True)

    for y in range(_state["maze_h"]):
        for x in range(_state["maze_w"]):
            wx, wy = _cell_to_world(x, y)
            rect_color = (0.05, 0.05, 0.08)
            pos = (x, y)
            tile = maze.grid[y][x]

            if pos == _state["exit"] and (pos in _state["revealed"] or pos in _state["quantum_revealed"]):
                rect_color = (0.1, 0.5, 0.2)
            elif pos in _state["revealed"]:
                if tile == 0:
                    rect_color = (0.2, 0.2, 0.25)
                elif tile == 1:
                    rect_color = (0.12, 0.14, 0.22)
                elif tile == 2:
                    rect_color = (0.3, 0.1, 0.1)
                elif tile == 3:
                    rect_color = (0.12, 0.25, 0.12)
                elif tile == 4:
                    rect_color = (0.15, 0.18, 0.3)
            elif pos in _state["quantum_revealed"]:
                rect_color = (0.18, 0.12, 0.28)

            draw_rect(wx, wy, cell, cell, color=rect_color, filled=True)
            draw_rect(wx, wy, cell, cell, color=(0.08, 0.08, 0.1), width=1.0)

            if pos in _state["revealed"]:
                if tile == 2:
                    spike = [
                        (wx + cell * 0.15, wy + cell * 0.1),
                        (wx + cell * 0.5, wy + cell * 0.85),
                        (wx + cell * 0.85, wy + cell * 0.1),
                    ]
                    draw_polygon(spike, color=(0.7, 0.25, 0.25), width=2.0)
                elif tile == 3:
                    draw_circle(wx + cell * 0.5, wy + cell * 0.5, cell * 0.3, color=(0.3, 0.8, 0.3))
                elif tile == 4:
                    wind = maze.obstacles.get((x, y))
                    if wind:
                        dx, dy = wind["direction"]
                        start = (wx + cell * 0.2, wy + cell * 0.5)
                        end = (wx + cell * 0.8, wy + cell * 0.5)
                        if dx != 0:
                            start = (wx + cell * (0.2 if dx < 0 else 0.8), wy + cell * 0.5)
                            end = (wx + cell * (0.8 if dx < 0 else 0.2), wy + cell * 0.5)
                        if dy != 0:
                            start = (wx + cell * 0.5, wy + cell * (0.2 if dy < 0 else 0.8))
                            end = (wx + cell * 0.5, wy + cell * (0.8 if dy < 0 else 0.2))
                        draw_polygon([start, end], color=(0.6, 0.6, 0.9), width=2.0, closed=False)

    px, py = _state["player"]
    player_x, player_y = _cell_to_world(px, py)
    if not _state["game_over"] or _state["won"]:
        if _state["tunneling"]:
            draw_circle(player_x + cell * 0.5, player_y + cell * 0.5, cell * 0.6, color=(0.9, 0.6, 0.9))
        _draw_bat(player_x, player_y)

    if _state["sonar_cooldown"] == 0:
        draw_circle(player_x + cell * 0.5, player_y + cell * 0.5, cell * 1.2, color=(0.3, 0.6, 0.8))

    hud_y = WORLD_BOTTOM + 10
    draw_rect(WORLD_LEFT, WORLD_BOTTOM, WORLD_RIGHT - WORLD_LEFT, _state["hud_h"],
              color=(0.08, 0.08, 0.12), filled=True)

    hp_text = f"HP: {_state['health']}/{_state['max_health']}"
    move_text = f"Moves: {_state['moves']}"
    sonar_text = "Sonar: Ready" if _state["sonar_cooldown"] == 0 else f"Sonar: CD {_state['sonar_cooldown']}"
    echo_text = f"Echo: {_state['echo_charges']}"
    tunnel_text = "Tunnel: Active" if _state["tunneling"] else f"Tunnel: {_state['tunnel_charges']}"

    draw_text(WORLD_LEFT + 20, hud_y + 40, hp_text, color=(0.8, 0.9, 0.8))
    draw_text(WORLD_LEFT + 20, hud_y + 18, move_text, color=(0.7, 0.7, 0.8))
    draw_text(WORLD_LEFT + 180, hud_y + 40, sonar_text, color=(0.6, 0.8, 0.95))
    draw_text(WORLD_LEFT + 180, hud_y + 18, echo_text, color=(0.7, 0.6, 0.9))
    draw_text(WORLD_LEFT + 360, hud_y + 40, tunnel_text, color=(0.9, 0.6, 0.9))

    draw_text(WORLD_RIGHT - 320, hud_y + 40, "WASD / Arrows to move", color=(0.7, 0.7, 0.7))
    draw_text(WORLD_RIGHT - 320, hud_y + 18, "Space: Sonar  Q: Echo  E: Tunnel  R: Restart", color=(0.7, 0.7, 0.7))

    color_names = {1: "Cyan", 2: "Magenta", 3: "Yellow"}
    current_color = color_names.get(_state["bat_color_index"], "Unknown")
    bat_color_display = BAT_COLORS.get(_state["bat_color_index"], BAT_COLORS[2])["body"]
    bat_text = f"Bat: {current_color}  (C/M/Y to change)"
    draw_text(WORLD_LEFT + 20, hud_y - 5, bat_text, color=bat_color_display)

    if _state["won"]:
        draw_rect(-180, -20, 360, 60, color=(0.1, 0.3, 0.1, 0.8), filled=True)
        draw_text(-120, 15, f"Victory! {_state['moves']} moves", color=(0.8, 1.0, 0.8))
        draw_text(-130, -5, "Press R to play again", color=(0.9, 0.9, 0.9))
    elif _state["game_over"]:
        draw_rect(-180, -20, 360, 60, color=(0.3, 0.1, 0.1, 0.8), filled=True)
        draw_text(-130, 15, "Game Over", color=(1.0, 0.7, 0.7))
        draw_text(-130, -5, "Press R to retry", color=(0.9, 0.9, 0.9))
