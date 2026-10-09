"""The Wumpus-free World environment (two-phase: grab the gold, then exit).

A grid dungeon containing:
  * an agent  (starts top-left)
  * the GOLD  (orange circle) - collect it for +REWARD_GOLD (non-terminal)
  * the EXIT  (green square, bottom-right) - reaching it WHILE carrying the
    gold gives +REWARD_GOAL and ends the episode (a win)
  * pits      (black circles, obstacles/hazards)   -> REWARD_HAZARD, terminal
  * walls     (the grid boundary)                  -> REWARD_WALL, no move

A classic Wumpus-World *percept* is exposed for flavour/visuals:
  * BREEZE  in cells adjacent to a pit
"""

import random

from config import (
    ROWS, COLS, ACTION_VECTORS,
    REWARD_GOLD, REWARD_GOAL, REWARD_HAZARD, REWARD_STEP, REWARD_WALL,
    MAX_STEPS,
)


class WumpusEnv:
    def __init__(self, rows=ROWS, cols=COLS, seed=None):
        self.rows = rows
        self.cols = cols
        self.rng = random.Random(seed)
        self._place()
        self.reset()

    # ------------------------------------------------------------------ setup
    def _place(self):
        """Randomly place exit, gold and pits (never on the start)."""
        self.goal = (self.rows - 1, self.cols - 1)     # the exit (green square)
        forbidden = {(0, 0), self.goal}
        pool = [(r, c) for r in range(self.rows) for c in range(self.cols)
                if (r, c) not in forbidden]
        self.rng.shuffle(pool)

        num_pits = 3
        self.pits = set(pool[:num_pits])

        # gold: somewhere reachable that is not a pit or the exit/start
        self.gold = None
        for p in pool[num_pits:]:
            if p not in self.pits:
                self.gold = p
                break
        if self.gold is None:
            for p in pool:
                if p not in self.pits:
                    self.gold = p
                    break

    def new_layout(self, seed=None):
        """Regenerate the dungeon (used by the 'new world' control)."""
        self.rng = random.Random(seed)
        self._place()
        self.reset()

    def reset(self):
        """Put the agent back at the start, drop any carried gold."""
        self.agent = [0, 0]
        self.steps = 0
        self.has_gold = False
        return self.state()

    def state(self):
        """Full RL state: cell + whether the agent is carrying the gold."""
        return (self.agent[0], self.agent[1], 1 if self.has_gold else 0)

    @property
    def agent_pos(self):
        return (self.agent[0], self.agent[1])

    # ------------------------------------------------------------------ step
    def step(self, action):
        """Apply an action. Returns (next_state, reward, done)."""
        self.steps += 1
        dr, dc = ACTION_VECTORS[action]
        nr, nc = self.agent[0] + dr, self.agent[1] + dc

        # wall / boundary
        if not (0 <= nr < self.rows and 0 <= nc < self.cols):
            return self.state(), REWARD_WALL, self.steps >= MAX_STEPS

        self.agent = [nr, nc]
        pos = tuple(self.agent)

        # phase 1: collect the gold (non-terminal)
        if pos == self.gold and not self.has_gold:
            self.has_gold = True
            return self.state(), REWARD_GOLD, False

        # phase 2: reach the exit while carrying the gold -> win
        if pos == self.goal:
            if self.has_gold:
                return self.state(), REWARD_GOAL, True
            # exit without gold: keep playing (small nudge, not terminal)
            return self.state(), REWARD_STEP, False

        # hazards
        if pos in self.pits:
            return self.state(), REWARD_HAZARD, True

        return self.state(), REWARD_STEP, self.steps >= MAX_STEPS

    # -------------------------------------------------------------- percepts
    def _adjacent(self, cell, target):
        r, c = cell
        tr, tc = target
        return abs(r - tr) + abs(c - tc) == 1

    def breeze(self, cell):
        return any(self._adjacent(cell, p) for p in self.pits)


