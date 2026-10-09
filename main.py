"""Wumpus World RL - main game loop.

Run:  py -3.13 main.py

A Q-learning agent explores a Wumpus World dungeon.  Early on it picks random
actions (exploration); epsilon decays each episode so it increasingly exploits
its learned Q-values.  The right-hand panel shows the live exploration vs
exploitation state next to the gameplay.

Controls
--------
SPACE   pause / resume auto-play
R       reset the agent (forget everything, restart learning)
N       generate a brand-new random dungeon
F       toggle fast training (skip animation delay)
1/2/3   speed presets (slow / normal / fast)
ESC     quit
"""

import os
import time

# Allow running head-less in CI/tests.
HEADLESS = os.environ.get("SDL_VIDEODRIVER") == "dummy"

import pygame

from config import (
    ROWS, COLS, CELL, GRID_X, GRID_Y, GRID_W, GRID_H,
    PANEL_X, PANEL_Y, PANEL_W, PANEL_H, WIDTH, HEIGHT, FPS,
    BG, TEXT, TEXT_DIM, TEXT_FAINT, PANEL_BORDER,
    EXPLORE_COLOR, EXPLOIT_COLOR, GOAL_COLOR, GOLD_COLOR, REWARD_GOLD,
    ACTION_NAMES,
)
from environment import WumpusEnv
from agent import QLearningAgent
import render as R


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(
            "Wumpus World RL - Exploration vs Exploitation")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.env = WumpusEnv(seed=None)
        self.agent = QLearningAgent()

        # episode / step state
        self.state = self.env.reset()
        self.trail = [tuple(self.env.agent)]   # path taken (for arrows)
        self.done = False
        self.episode = 1
        self.ep_reward = 0.0
        self.last_action = None
        self.last_explore = False
        self.message = "Exploring randomly..."
        self.message_color = EXPLORE_COLOR
        self.history = []            # per-episode total reward
        self.flash = 0.0

        # play state
        self.paused = False
        self.fast = False
        self.move_interval = 0.16    # seconds between auto moves
        self._acc = 0.0
        self._pulse = 0.0

        self.running = True

    # ------------------------------------------------------------------ loop
    def run(self):
        last = time.time()
        while self.running:
            dt = min(0.05, time.time() - last)
            last = time.time()
            self._pulse = (self._pulse + dt) % 1.0
            self.flash = max(0.0, self.flash - dt)

            self.handle_events()
            if not self.paused and not self.done:
                self._acc += dt
                if self.fast:
                    for _ in range(8):
                        if not self.done:
                            self.step()
                elif self._acc >= self.move_interval:
                    self._acc = 0.0
                    self.step()

            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    # ------------------------------------------------------------------ step
    def step(self):
        action, is_explore = self.agent.choose_action(self.state)
        next_state, reward, done = self.env.step(action)
        self.agent.learn(self.state, action, reward, next_state, done)
        self.agent.record_visit(next_state, is_explore)

        self.last_action = action
        self.last_explore = is_explore
        self.ep_reward += reward
        self.state = next_state
        self.done = done

        self.trail.append(self.env.agent_pos)
        if len(self.trail) > 120:
            self.trail.pop(0)

        if reward == REWARD_GOLD:
            self.message = "Grabbed the gold!"
            self.message_color = GOLD_COLOR

        if done:
            self._on_episode_end()

    def _on_episode_end(self):
        self.history.append(round(self.ep_reward, 1))
        if len(self.history) > 300:
            self.history.pop(0)

        pos = (self.state[0], self.state[1])
        if pos == self.env.goal and self.env.has_gold:
            self.message = "Escaped with the gold! +200"
            self.message_color = GOAL_COLOR
        elif pos in self.env.pits:
            self.message = "Fell into a pit! -100"
            self.message_color = (30, 30, 30)
        else:
            self.message = "Ran out of steps."
            self.message_color = TEXT_DIM
        self.flash = 0.9

    def next_episode(self):
        self.agent.decay()
        self.state = self.env.reset()
        self.trail = [tuple(self.env.agent)]
        self.ep_reward = 0.0
        self.done = False
        self.episode += 1

    # ---------------------------------------------------------------- events
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.on_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.done:
                    self.next_episode()

    def on_key(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_r:
            self._reset_all("Agent reset - learning from scratch", EXPLORE_COLOR)
        elif key == pygame.K_n:
            self.env.new_layout()
            self._reset_all("New dungeon generated", EXPLOIT_COLOR)
        elif key == pygame.K_f:
            self.fast = not self.fast
        elif key == pygame.K_1:
            self.move_interval = 0.4
        elif key == pygame.K_2:
            self.move_interval = 0.16
        elif key == pygame.K_3:
            self.move_interval = 0.05
        elif key in (pygame.K_RETURN, pygame.K_RIGHT) and self.done:
            self.next_episode()

    def _reset_all(self, message, color):
        self.agent.reset()
        self.state = self.env.reset()
        self.trail = [tuple(self.env.agent)]
        self.ep_reward = 0.0
        self.done = False
        self.episode = 1
        self.history.clear()
        self.message = message
        self.message_color = color

    # ------------------------------------------------------------------ draw
    def draw(self):
        self.screen.fill(BG)
        self.draw_header()
        self.draw_grid()
        self.draw_panel()
        self.draw_footer()
        pygame.display.flip()

    def draw_header(self):
        R.draw_text(self.screen, "WUMPUS WORLD", GRID_X, 18, 30, TEXT,
                    bold=True)
        R.draw_text(self.screen,
                    "Q-Learning agent: random exploration -> learned "
                    "exploitation", GRID_X, 52, 16, TEXT_DIM)

        if self.last_explore:
            badge, col = "EXPLORING", TEXT
        else:
            badge, col = "EXPLOITING", TEXT_DIM
        R.draw_text(self.screen, badge, WIDTH - 28, 30, 20, col, bold=True,
                    anchor="right")
        stats = f"Episode {self.episode}    epsilon {self.agent.epsilon:.3f}"
        R.draw_text(self.screen, stats, WIDTH - 28, 54, 14, TEXT_DIM,
                    anchor="right")

    def draw_grid(self):
        frame = pygame.Rect(GRID_X - 6, GRID_Y - 6, GRID_W + 12, GRID_H + 12)
        pygame.draw.rect(self.screen, PANEL_BORDER, frame, 2, border_radius=12)

        R.draw_grid_background(self.screen,
                               self.agent.explore_grid, self.agent.exploit_grid)
        R.draw_trail(self.screen, self.trail)
        R.draw_percepts(self.screen, self.env)
        R.draw_pits(self.screen, self.env)
        R.draw_gold(self.screen, self.env)
        R.draw_goal(self.screen, self.env)
        R.draw_agent(self.screen, self.env.agent_pos,
                     has_gold=self.env.has_gold, pulse=self._pulse)

        if self.last_action is not None:
            cx, cy = R.cell_center(*self.env.agent_pos)
            col = TEXT if self.last_explore else TEXT_DIM
            R.draw_text(self.screen, ACTION_NAMES[self.last_action],
                        cx, cy - CELL * 0.55, 13, col, bold=True,
                        anchor="center")

    def draw_panel(self):
        rect = pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
        R.draw_panel_frame(self.screen, rect)
        x = PANEL_X + 18
        w = PANEL_W - 36

        y = PANEL_Y + 16
        y = R.draw_section_title(self.screen, x, y,
                                 "exploration <-> exploitation", w)
        gauge = pygame.Rect(x, y, w, 78)
        R.draw_epsilon_gauge(self.screen, gauge, self.agent.epsilon)

        y = gauge.bottom + 14
        y = R.draw_section_title(self.screen, x, y, "action selection ratio",
                                 w)
        R.draw_donut(self.screen, (x + 52, y + 48), 44,
                     self.agent.explore_count, self.agent.exploit_count)
        ex, ey = x + 116, y + 22
        R.draw_text(self.screen, "random / explore", ex, ey, 14, EXPLORE_COLOR,
                    bold=True)
        R.draw_text(self.screen, str(self.agent.explore_count), x + w, ey, 16,
                    TEXT, bold=True, anchor="right")
        R.draw_text(self.screen, "greedy / exploit", ex, ey + 24, 14,
                    TEXT_DIM, bold=True)
        R.draw_text(self.screen, str(self.agent.exploit_count), x + w, ey + 24,
                    16, TEXT, bold=True, anchor="right")

        y = y + 104
        y = R.draw_section_title(self.screen, x, y, "learned policy (greedy)",
                                 w)
        policy_rect = pygame.Rect(x, y, w, 120)
        R.draw_policy_map(self.screen, policy_rect, self.agent)

        y = policy_rect.bottom + 14
        y = R.draw_section_title(self.screen, x, y, "episode reward history",
                                 w)
        chart = pygame.Rect(x, y, w, PANEL_Y + PANEL_H - 26 - y)
        R.draw_reward_chart(self.screen, chart, self.history)

    def draw_footer(self):
        R.draw_legend(self.screen, GRID_X, HEIGHT - 26)
        if self.message:
            R.draw_text(self.screen, self.message, WIDTH - 28, HEIGHT - 26, 15,
                        self.message_color, bold=True, anchor="right")
        hint = ("SPACE pause   R reset   N new dungeon   F fast   "
                "1/2/3 speed   ESC quit")
        R.draw_text(self.screen, hint, GRID_X, HEIGHT - 50, 13, TEXT_FAINT)


def main():
    game = Game()
    if HEADLESS:
        for _ in range(3):
            game.handle_events()
            game.step()
            game.draw()
        pygame.quit()
        return
    game.run()


if __name__ == "__main__":
    main()

