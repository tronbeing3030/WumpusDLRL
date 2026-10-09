"""All drawing / sprite code for the Wumpus World RL game.

Entities are drawn as distinct simple shapes:
  * Agent  -> blue square
  * Gold   -> orange circle (treasure to collect)
  * Goal   -> green square (the exit)
  * Pit    -> black circle

The path taken is highlighted with ARROWS (the grid squares are not
recoloured).  The right-hand panel visualises the exploration/exploitation
trade-off:
  * live epsilon gauge
  * explore-vs-exploit donut chart
  * cumulative counters
  * learned-policy arrows + Q-value heat-map
  * episode reward history line chart
"""

import math

import pygame

from config import (
    CELL, ROWS, COLS, GRID_X, GRID_Y,
    BG, PANEL_BG, PANEL_BORDER, CELL_BG, CELL_BG_ALT, GRID_LINE,
    TEXT, TEXT_DIM, TEXT_FAINT,
    AGENT_COLOR, GOAL_COLOR, GOLD_COLOR, PIT_COLOR,
    BREEZE_COLOR,
    EXPLORE_COLOR, EXPLOIT_COLOR, HEAT_COLOR, CHART_LINE, PATH_COLOR,
    ACTION_ARROWS, FONT_STACK,
)

_font_cache = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        f = None
        for name in FONT_STACK:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f:
                break
        _font_cache[key] = f or pygame.font.Font(None, size)
    return _font_cache[key]


def draw_text(surface, txt, x, y, size=16, color=TEXT, bold=False,
              anchor="left"):
    img = font(size, bold).render(str(txt), True, color)
    rect = img.get_rect()
    if anchor == "left":
        rect.topleft = (x, y)
    elif anchor == "right":
        rect.topright = (x, y)
    elif anchor == "center":
        rect.center = (x, y)
    elif anchor == "midleft":
        rect.midleft = (x, y)
    elif anchor == "midright":
        rect.midright = (x, y)
    elif anchor == "centerx":
        rect.centerx = x
        rect.top = y
    else:
        rect.topleft = (x, y)
    surface.blit(img, rect)
    return rect


def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------------------
# Grid + entities
# ---------------------------------------------------------------------------
def cell_rect(r, c):
    return pygame.Rect(GRID_X + c * CELL, GRID_Y + r * CELL, CELL, CELL)


def cell_center(r, c):
    rect = cell_rect(r, c)
    return rect.centerx, rect.centery


def draw_grid_background(surface, explore_grid, exploit_grid):
    """Draw the black & white dungeon floor and per-cell explore/exploit pips.

    Squares are NOT recoloured by visits - the path is shown with arrows.
    """
    for r in range(ROWS):
        for c in range(COLS):
            rect = cell_rect(r, c)
            color = CELL_BG if (r + c) % 2 == 0 else CELL_BG_ALT
            pygame.draw.rect(surface, color, rect, border_radius=8)
            pygame.draw.rect(surface, GRID_LINE, rect, 1, border_radius=8)

            if int(explore_grid[r, c]) > 0:
                _pip(surface, rect, "tl", EXPLORE_COLOR)
            if int(exploit_grid[r, c]) > 0:
                _pip(surface, rect, "br", EXPLOIT_COLOR)


def draw_trail(surface, trail):
    """Highlight the path taken with arrows between consecutive cells."""
    if len(trail) < 2:
        return
    for i in range(len(trail) - 1):
        a = cell_center(*trail[i])
        b = cell_center(*trail[i + 1])
        # shorten the segment a little so arrowheads sit under the markers
        _arrow(surface, PATH_COLOR, a, b, size=7, width=3)


def _pip(surface, rect, corner, color, rad=4):
    m = 6
    if corner == "tl":
        pos = (rect.left + m, rect.top + m)
    else:
        pos = (rect.right - m, rect.bottom - m)
    pygame.draw.circle(surface, color, pos, rad)


def draw_percepts(surface, env):
    """Breeze halo overlay (blue fill near pits)."""
    for r in range(ROWS):
        for c in range(COLS):
            rect = cell_rect(r, c)
            if env.breeze((r, c)):
                _halo(surface, rect, BREEZE_COLOR)


def _halo(surface, rect, color):
    overlay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(overlay, color + (46,), overlay.get_rect(),
                     border_radius=8)
    surface.blit(overlay, rect.topleft)


def draw_goal(surface, env):
    cx, cy = cell_center(*env.goal)
    _square(surface, GOAL_COLOR, (cx, cy), CELL * 0.30)


def draw_gold(surface, env):
    cx, cy = cell_center(*env.gold)
    if env.has_gold:
        # already collected -> faint hollow outline
        pygame.draw.circle(surface, GOLD_COLOR, (cx, cy), CELL * 0.20, 3)
    else:
        pygame.draw.circle(surface, GOLD_COLOR, (cx, cy), CELL * 0.24)
        pygame.draw.circle(surface, BG, (cx, cy), CELL * 0.10)


def draw_pits(surface, env):
    for (r, c) in env.pits:
        cx, cy = cell_center(r, c)
        pygame.draw.circle(surface, PIT_COLOR, (cx, cy), CELL * 0.26)


def draw_agent(surface, pos, has_gold=False, pulse=0.0):
    r, c = pos
    cx, cy = cell_center(r, c)
    half = int(CELL * 0.30 + pulse * 3)
    rect = pygame.Rect(cx - half, cy - half, half * 2, half * 2)
    # soft glow
    glow = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    pygame.draw.rect(glow, AGENT_COLOR + (55,),
                     pygame.Rect(CELL // 2 - half - 4, CELL // 2 - half - 4,
                                 (half + 4) * 2, (half + 4) * 2), border_radius=8)
    surface.blit(glow, (cx - CELL // 2, cy - CELL // 2))
    pygame.draw.rect(surface, AGENT_COLOR, rect, border_radius=5)
    pygame.draw.rect(surface, BG, rect, 2, border_radius=5)
    # carried-gold indicator (small orange dot)
    if has_gold:
        pygame.draw.circle(surface, GOLD_COLOR, (cx, cy), 5)


# ---------------------------------------------------------------------------
# Simple shape helpers
# ---------------------------------------------------------------------------
def _star(surface, color, center, outer, inner, points=5, outline=False):
    cx, cy = center
    pts = []
    for i in range(points * 2):
        ang = -math.pi / 2 + i * math.pi / points
        rad = outer if i % 2 == 0 else inner
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    if outline:
        pygame.draw.polygon(surface, BG, pts)         # white fill
        pygame.draw.polygon(surface, color, pts, 3)   # black outline
    else:
        pygame.draw.polygon(surface, color, pts)


def _triangle(surface, color, center, size):
    cx, cy = center
    pts = [(cx, cy - size), (cx - size, cy + size * 0.75),
           (cx + size, cy + size * 0.75)]
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.polygon(surface, BG, pts, 2)


def _square(surface, color, center, size):
    cx, cy = center
    rect = pygame.Rect(int(cx - size), int(cy - size),
                       int(size * 2), int(size * 2))
    pygame.draw.rect(surface, color, rect, border_radius=4)
    pygame.draw.rect(surface, BG, rect, 2, border_radius=4)


# ---------------------------------------------------------------------------
# Side panel: exploration / exploitation visualisations
# ---------------------------------------------------------------------------
def draw_panel_frame(surface, rect):
    pygame.draw.rect(surface, PANEL_BG, rect, border_radius=14)
    pygame.draw.rect(surface, PANEL_BORDER, rect, 2, border_radius=14)


def draw_section_title(surface, x, y, txt, w):
    draw_text(surface, txt.upper(), x, y, 15, TEXT, bold=True)
    pygame.draw.rect(surface, PANEL_BORDER, pygame.Rect(x, y + 20, w, 1))
    return y + 30


def draw_epsilon_gauge(surface, rect, epsilon):
    """Horizontal bar: orange=explore, emerald=exploit; marker at epsilon."""
    pad = 10
    bar = pygame.Rect(rect.x + pad, rect.y + 40, rect.w - 2 * pad, 20)
    pygame.draw.rect(surface, EXPLOIT_COLOR, bar, border_radius=10)
    explore_w = int(bar.w * epsilon)
    if explore_w > 0:
        exp = pygame.Rect(bar.left, bar.top, explore_w, bar.h)
        pygame.draw.rect(surface, EXPLORE_COLOR, exp, border_radius=10)
    mx = bar.left + explore_w
    pygame.draw.line(surface, TEXT, (mx, bar.top - 4), (mx, bar.bottom + 4), 3)
    draw_text(surface, "explore", bar.left, bar.top - 18, 13, TEXT)
    draw_text(surface, "exploit", bar.right, bar.top - 18, 13, TEXT_DIM,
              anchor="right")
    draw_text(surface, f"epsilon = {epsilon:.3f}", bar.left, bar.bottom + 6,
              15, TEXT, bold=True)


def draw_donut(surface, center, radius, explore, exploit, thickness=22):
    """Donut chart of explore vs exploit action counts."""
    total = explore + exploit
    cx, cy = center
    box = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
    if total == 0:
        pygame.draw.circle(surface, PANEL_BORDER, (cx, cy), radius, thickness)
        draw_text(surface, "-", cx, cy, 22, TEXT_DIM, anchor="center")
        return
    e_frac = explore / total
    x_frac = exploit / total
    start = -math.pi / 2
    end = start + x_frac * 2 * math.pi
    if x_frac > 0:
        _arc(surface, EXPLOIT_COLOR, box, start, end, thickness)
    start = end
    end = start + e_frac * 2 * math.pi
    if e_frac > 0:
        _arc(surface, EXPLORE_COLOR, box, start, end, thickness)
    draw_text(surface, f"{int(e_frac * 100)}%", cx, cy - 8, 22, TEXT, bold=True,
              anchor="center")
    draw_text(surface, "explore", cx, cy + 14, 12, TEXT_DIM, anchor="center")


def _arc(surface, color, box, start, end, thickness):
    pygame.draw.arc(surface, color, box, start, end, thickness)


def draw_policy_map(surface, rect, agent):
    """Small grid: arrows = greedy action, cell tint = Q-value magnitude."""
    gap = 6
    inner = pygame.Rect(rect.x + gap, rect.y + 26,
                        rect.w - 2 * gap, rect.h - 26 - gap)
    cw = inner.w / COLS
    ch = inner.h / ROWS
    qmax = max(1e-6, float(agent.q.max()), float(-agent.q.min()))
    for r in range(ROWS):
        for c in range(COLS):
            cell = pygame.Rect(inner.x + c * cw, inner.y + r * ch,
                               cw - 2, ch - 2)
            best = int(agent.q[0, r, c].argmax())          # phase: no gold yet
            val = agent.q[0, r, c, best]
            t = min(1.0, abs(val) / qmax)
            tint = EXPLOIT_COLOR if val >= 0 else PIT_COLOR
            base = _lerp_color(CELL_BG, tint, 0.15 + 0.55 * t)
            pygame.draw.rect(surface, base, cell, border_radius=4)
            arrow_col = BG if val < 0 else TEXT
            dx, dy = ACTION_ARROWS[best]
            ccx = cell.centerx + dx * cw * 0.22
            ccy = cell.centery + dy * ch * 0.22
            _arrow(surface, arrow_col, cell.center, (ccx, ccy))


def _arrow(surface, color, start, end, size=6, width=2):
    pygame.draw.line(surface, color, start, end, width)
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    for da in (math.pi * 0.82, -math.pi * 0.82):
        px = end[0] + size * math.cos(ang + da)
        py = end[1] + size * math.sin(ang + da)
        pygame.draw.line(surface, color, end, (px, py), width)


def draw_reward_chart(surface, rect, history):
    """Episode reward history as a filled line chart."""
    if not history:
        draw_text(surface, "no episodes yet", rect.x + 8, rect.centery, 14,
                  TEXT_FAINT)
        return
    pad_l, pad_r, pad_t, pad_b = 6, 6, 8, 8
    plot = pygame.Rect(rect.x + pad_l, rect.y + pad_t,
                       rect.w - pad_l - pad_r, rect.h - pad_t - pad_b)
    lo = min(min(history), 0)
    hi = max(max(history), 0)
    span = (hi - lo) or 1
    n = len(history)
    pts = []
    for i, v in enumerate(history):
        x = plot.x + (i / max(1, n - 1)) * plot.w
        y = plot.bottom - ((v - lo) / span) * plot.h
        pts.append((x, y))
    zy = plot.bottom - ((0 - lo) / span) * plot.h
    pygame.draw.line(surface, PANEL_BORDER, (plot.x, zy), (plot.right, zy), 1)
    if len(pts) >= 2:
        pygame.draw.lines(surface, CHART_LINE, False, pts, 2)
    if pts:
        pygame.draw.circle(surface, GOAL_COLOR,
                           (int(pts[-1][0]), int(pts[-1][1])), 3)


def draw_legend(surface, x, y):
    items = [
        ("square", AGENT_COLOR, "Agent"),
        ("circle", GOLD_COLOR, "Gold"),
        ("square", GOAL_COLOR, "Goal"),
        ("circle", PIT_COLOR, "Pit"),
    ]
    cx = x
    for shape, color, label in items:
        _legend_swatch(surface, shape, color, (cx, y))
        r = draw_text(surface, label, cx + 16, y - 7, 13, TEXT_DIM)
        cx += 16 + r.width + 22


def _legend_swatch(surface, shape, color, center):
    cx, cy = center
    if shape == "circle":
        pygame.draw.circle(surface, color, (cx, cy), 6)
    elif shape == "square":
        _square(surface, color, (cx, cy), 6)
    elif shape == "star":
        _star(surface, color, (cx, cy), 8, 3.5, outline=True)
    elif shape == "tri":
        _triangle(surface, color, (cx, cy), 7)
