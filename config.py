"""Central configuration: grid, colors, rewards, RL hyper-parameters and layout.

Everything the game/agent needs is defined here so the look-and-feel and the
learning dynamics can be tuned in a single place.
"""

import pygame

# ---------------------------------------------------------------------------
# Grid / world
# ---------------------------------------------------------------------------
ROWS = 6
COLS = 6
CELL = 80                       # pixel size of one grid cell

# ---------------------------------------------------------------------------
# Palette: grid & panels black/white; entities get distinct shape + colour
# (blue / green / red / orange / yellow). Path is drawn with arrows.
# ---------------------------------------------------------------------------
BG = (250, 250, 250)            # near-white page background
PANEL_BG = (255, 255, 255)      # white panels
PANEL_BORDER = (24, 24, 24)     # near-black borders
CELL_BG = (255, 255, 255)       # white floor
CELL_BG_ALT = (240, 240, 240)   # light-grey checker floor (black & white)
GRID_LINE = (205, 205, 205)     # cell border

TEXT = (22, 22, 22)             # black text
TEXT_DIM = (95, 95, 95)         # grey secondary text
TEXT_FAINT = (150, 150, 150)    # grey faint text

# Entities -> each a DIFFERENT simple shape + colour
AGENT_COLOR = (37, 99, 235)     # blue   -> SQUARE
GOAL_COLOR = (22, 163, 74)      # green  -> SQUARE (the exit)
GOLD_COLOR = (246, 150, 40)     # orange -> CIRCLE (treasure to collect)
PIT_COLOR = (30, 30, 30)        # black  -> CIRCLE (hazard)

# Percepts (Wumpus World flavour)
BREEZE_COLOR = (70, 130, 220)   # blue fill near pits

# Exploration vs exploitation accents
EXPLORE_COLOR = (22, 22, 22)    # black       = random exploration
EXPLOIT_COLOR = (246, 150, 40)  # orange      = greedy exploitation
HEAT_COLOR = (96, 145, 235)     # (kept for compatibility)

# chart line (must read clearly on white)
CHART_LINE = (40, 40, 40)
PATH_COLOR = (60, 60, 60)       # path-arrow colour

# ---------------------------------------------------------------------------
# Reinforcement-learning hyper-parameters
# ---------------------------------------------------------------------------
NUM_ACTIONS = 4
UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3
ACTIONS = (UP, DOWN, LEFT, RIGHT)
ACTION_NAMES = ("UP", "DOWN", "LEFT", "RIGHT")
ACTION_VECTORS = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}
ACTION_ARROWS = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}

ALPHA = 0.20        # learning rate
GAMMA = 0.95        # discount factor
EPS_START = 1.00    # start fully random -> maximum exploration
EPS_MIN = 0.02      # never become 100% greedy (keep exploring a little)
EPS_DECAY = 0.98    # multiplicative decay applied at the end of every episode

# ---------------------------------------------------------------------------
# Reward shaping  (two-phase Wumpus World: grab the gold, then reach the exit)
# ---------------------------------------------------------------------------
REWARD_GOLD = 100.0     # picked up the gold (treasure collected)
REWARD_GOAL = 100.0     # reached the exit while carrying the gold -> win
REWARD_HAZARD = -100.0  # pit or wumpus
REWARD_STEP = -1.0      # small cost per move -> encourages short paths
REWARD_WALL = -5.0      # bumped into a wall
MAX_STEPS = 200         # safety cap on episode length

# ---------------------------------------------------------------------------
# Fonts / window layout
# ---------------------------------------------------------------------------
FONT_STACK = ["segoeui", "Segoe UI", "calibri", "consolas", "arial"]

HEADER_H = 64
GRID_X = 28
GRID_Y = HEADER_H + 24
GRID_W = COLS * CELL
GRID_H = ROWS * CELL

PANEL_X = GRID_X + GRID_W + 24
PANEL_W = 364
PANEL_Y = GRID_Y
PANEL_H = GRID_H

WIDTH = PANEL_X + PANEL_W + 28
HEIGHT = 720
FOOTER_Y = GRID_Y + GRID_H + 18

FPS = 60
