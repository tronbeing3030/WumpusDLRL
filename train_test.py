"""Headless training test: proves the agent learns over many episodes.

Runs the Q-learning agent for N episodes on a fixed dungeon and prints the
explore/exploit split plus the average reward of the first vs last episodes.
A well-behaved run shows reward climbing as epsilon decays (more exploitation).

Run:  py -3.13 train_test.py
"""

import numpy as np

from environment import WumpusEnv
from agent import QLearningAgent
from config import MAX_STEPS


def run(num_episodes=600, seed=7):
    env = WumpusEnv(seed=seed)
    agent = QLearningAgent()
    agent.seed(seed)

    rewards = []
    for ep in range(num_episodes):
        state = env.reset()
        total = 0.0
        done = False
        while not done:
            action, is_explore = agent.choose_action(state)
            nxt, reward, done = env.step(action)
            agent.learn(state, action, reward, nxt, done)
            agent.record_visit(nxt, is_explore)
            state = nxt
            total += reward
        agent.decay()
        rewards.append(total)

    rewards = np.array(rewards)
    k = 20
    first = rewards[:k].mean()
    last = rewards[-k:].mean()
    print(f"episodes          : {num_episodes}")
    print(f"final epsilon     : {agent.epsilon:.4f}")
    print(f"explore / exploit : {agent.explore_count} / {agent.exploit_count}")
    print(f"avg reward (first {k}): {first:8.2f}")
    print(f"avg reward (last  {k}): {last:8.2f}")
    print(f"improvement       : {last - first:8.2f}")
    # A learned, mostly-exploiting policy should reach the gold (+100) at least
    # sometimes in the tail, and the tail average must beat the (random) head.
    assert last > first, "agent did not improve over training!"
    print("OK: agent learned to improve cumulative reward.")


if __name__ == "__main__":
    run()
