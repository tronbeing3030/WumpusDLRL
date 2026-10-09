"""Render a screenshot (headless) so we can verify the visuals.

Trains the agent briefly so the side panel has data, then saves a PNG.

Run:  py -3.13 screenshot.py
"""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame  # noqa: E402
import main as game_main  # noqa: E402


def main():
    g = game_main.Game()
    # fast-forward training so panels/charts/history are populated
    for _ in range(400):
        if g.done:
            g.next_episode()
        g.step()
    g.draw()
    out = os.path.join(os.path.dirname(__file__), "preview.png")
    pygame.image.save(g.screen, out)
    print("saved", out, "size", g.screen.get_size())
    pygame.quit()


if __name__ == "__main__":
    main()
