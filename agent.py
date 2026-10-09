"""Tabular Q-learning agent.

The agent learns an action-value function Q(state, action).  Action selection
uses an epsilon-greedy policy:

  * with probability epsilon   -> pick a RANDOM action   (EXPLORATION)
  * otherwise                  -> pick argmax Q(s, a)    (EXPLOITATION)

epsilon starts at 1.0 (pure exploration) and decays each episode so the agent
gradually shifts toward exploiting what it has learned.
"""

import numpy as np

from config import (
    ROWS, COLS, NUM_ACTIONS,
    ALPHA, GAMMA, EPS_START, EPS_MIN, EPS_DECAY,
)


class QLearningAgent:
    def __init__(self, rows=ROWS, cols=COLS):
        self.rows = rows
        self.cols = cols
        # Q[has_gold, row, col, action]
        self.q = np.zeros((2, rows, cols, NUM_ACTIONS), dtype=float)

        # exploration bookkeeping
        self.epsilon = EPS_START
        self.explore_count = 0
        self.exploit_count = 0
        # per-cell visitation grids (for the exploration visualisations)
        self.visits = np.zeros((rows, cols), dtype=int)
        self.explore_grid = np.zeros((rows, cols), dtype=int)
        self.exploit_grid = np.zeros((rows, cols), dtype=int)

    # --------------------------------------------------------------- policy
    def choose_action(self, state, greedy=False):
        """state = (row, col, has_gold). Returns (action, is_explore)."""
        r, c, g = state
        if not greedy and self._rng_float() < self.epsilon:
            self.explore_count += 1
            return int(self._rng_int(NUM_ACTIONS)), True
        self.exploit_count += 1
        return int(np.argmax(self.q[g, r, c])), False

    # --------------------------------------------------------------- learning
    def learn(self, s, a, r, s2, done):
        r1, c1, g1 = s
        r2, c2, g2 = s2
        target = r if done else r + GAMMA * np.max(self.q[g2, r2, c2])
        self.q[g1, r1, c1, a] += ALPHA * (target - self.q[g1, r1, c1, a])

    def record_visit(self, state, is_explore):
        r, c, _g = state
        self.visits[r, c] += 1
        if is_explore:
            self.explore_grid[r, c] += 1
        else:
            self.exploit_grid[r, c] += 1

    def decay(self):
        self.epsilon = max(EPS_MIN, self.epsilon * EPS_DECAY)

    def reset(self):
        """Fresh start: clear Q-table and all statistics."""
        self.q[:] = 0.0
        self.epsilon = EPS_START
        self.explore_count = 0
        self.exploit_count = 0
        self.visits[:] = 0
        self.explore_grid[:] = 0
        self.exploit_grid[:] = 0

    # ------------------------------------------------------- seeded RNG (test)
    def seed(self, value):
        self._rng = np.random.default_rng(value)

    def _rng_float(self):
        if not hasattr(self, "_rng"):
            self._rng = np.random.default_rng()
        return float(self._rng.random())

    def _rng_int(self, n):
        if not hasattr(self, "_rng"):
            self._rng = np.random.default_rng()
        return int(self._rng.integers(n))
