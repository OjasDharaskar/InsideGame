"""
Custom Bresenham Drawing & Rasterization Utilities.
Fulfills Rule 3 of Development Skill:
Objects in the scene must be made using pygame with separate functions for line drawing, circle drawing, etc.
using Bresenham line and circle algorithms.
"""

from typing import List, Sequence, Tuple
import pygame


def bresenham_line_points(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """
    Standard integer Bresenham Line Algorithm.
    Returns list of (x, y) coordinates from (x0, y0) to (x1, y1).
    """
    points = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy

    curr_x, curr_y = x0, y0
    while True:
        points.append((curr_x, curr_y))
        if curr_x == x1 and curr_y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            curr_x += sx
        if e2 <= dx:
            err += dx
            curr_y += sy

    return points


def draw_bresenham_line(
    surface: pygame.Surface,
    x0: float, y0: float,
    x1: float, y1: float,
    color: Sequence[int],
    thickness: int = 1
) -> None:
    """
    Draws a line on the pygame surface using Bresenham's line algorithm.
    Supports variable thickness by drawing parallel offset lines.
    """
    ix0, iy0 = int(round(x0)), int(round(y0))
    ix1, iy1 = int(round(x1)), int(round(y1))
    
    surf_rect = surface.get_rect()
    w, h = surf_rect.width, surf_rect.height

    if thickness <= 1:
        for px, py in bresenham_line_points(ix0, iy0, ix1, iy1):
            if 0 <= px < w and 0 <= py < h:
                surface.set_at((px, py), color)
    else:
        # Draw with perpendicular offset strokes
        half_th = thickness // 2
        for offset in range(-half_th, half_th + 1):
            # Check main axis to decide horizontal or vertical offset
            if abs(ix1 - ix0) >= abs(iy1 - iy0):
                pts = bresenham_line_points(ix0, iy0 + offset, ix1, iy1 + offset)
            else:
                pts = bresenham_line_points(ix0 + offset, iy0, ix1 + offset, iy1)
            for px, py in pts:
                if 0 <= px < w and 0 <= py < h:
                    surface.set_at((px, py), color)


def bresenham_circle_octants(xc: int, yc: int, x: int, y: int) -> List[Tuple[int, int]]:
    """Returns symmetric 8 octants for a circle centered at (xc, yc)."""
    return [
        (xc + x, yc + y), (xc - x, yc + y),
        (xc + x, yc - y), (xc - x, yc - y),
        (xc + y, yc + x), (xc - y, yc + x),
        (xc + y, yc - x), (xc - y, yc - x),
    ]


def draw_bresenham_circle(
    surface: pygame.Surface,
    xc: float, yc: float,
    radius: float,
    color: Sequence[int],
    filled: bool = False
) -> None:
    """
    Draws a circle on the pygame surface using Bresenham's Midpoint Circle Algorithm.
    Supports hollow perimeter or filled disc.
    """
    ixc, iyc = int(round(xc)), int(round(yc))
    ir = int(round(radius))

    if ir <= 0:
        surf_rect = surface.get_rect()
        if 0 <= ixc < surf_rect.width and 0 <= iyc < surf_rect.height:
            surface.set_at((ixc, iyc), color)
        return

    surf_rect = surface.get_rect()
    w, h = surf_rect.width, surf_rect.height

    x = 0
    y = ir
    d = 3 - 2 * ir

    if filled:
        # Draw horizontal scanlines for symmetry pairs
        while y >= x:
            # Pair 1: y level
            y_top = iyc - y
            y_bot = iyc + y
            x_left1 = max(0, min(w - 1, ixc - x))
            x_right1 = max(0, min(w - 1, ixc + x))
            if 0 <= y_top < h:
                for px in range(x_left1, x_right1 + 1):
                    surface.set_at((px, y_top), color)
            if 0 <= y_bot < h:
                for px in range(x_left1, x_right1 + 1):
                    surface.set_at((px, y_bot), color)

            # Pair 2: x level
            x_top = iyc - x
            x_bot = iyc + x
            x_left2 = max(0, min(w - 1, ixc - y))
            x_right2 = max(0, min(w - 1, ixc + y))
            if 0 <= x_top < h:
                for px in range(x_left2, x_right2 + 1):
                    surface.set_at((px, x_top), color)
            if 0 <= x_bot < h:
                for px in range(x_left2, x_right2 + 1):
                    surface.set_at((px, x_bot), color)

            if d > 0:
                y -= 1
                d = d + 4 * (x - y) + 10
            else:
                d = d + 4 * x + 6
            x += 1
    else:
        # Perimeter only
        while y >= x:
            for px, py in bresenham_circle_octants(ixc, iyc, x, y):
                if 0 <= px < w and 0 <= py < h:
                    surface.set_at((px, py), color)
            if d > 0:
                y -= 1
                d = d + 4 * (x - y) + 10
            else:
                d = d + 4 * x + 6
            x += 1


def draw_bresenham_rect(
    surface: pygame.Surface,
    x: float, y: float,
    width: float, height: float,
    color: Sequence[int],
    filled: bool = False,
    thickness: int = 1
) -> None:
    """
    Draws a rectangle using Bresenham line and scanline routines.
    """
    ix = int(round(x))
    iy = int(round(y))
    iw = int(round(width))
    ih = int(round(height))

    if iw <= 0 or ih <= 0:
        return

    surf_rect = surface.get_rect()
    sw, sh = surf_rect.width, surf_rect.height

    if filled:
        y_start = max(0, iy)
        y_end = min(sh, iy + ih)
        x_start = max(0, ix)
        x_end = min(sw, ix + iw)
        for cy in range(y_start, y_end):
            # Scanline
            for cx in range(x_start, x_end):
                surface.set_at((cx, cy), color)
    else:
        # 4 edges via Bresenham line
        x2 = ix + iw - 1
        y2 = iy + ih - 1
        draw_bresenham_line(surface, ix, iy, x2, iy, color, thickness)
        draw_bresenham_line(surface, x2, iy, x2, y2, color, thickness)
        draw_bresenham_line(surface, x2, y2, ix, y2, color, thickness)
        draw_bresenham_line(surface, ix, y2, ix, iy, color, thickness)


def draw_bresenham_polygon(
    surface: pygame.Surface,
    vertices: Sequence[Tuple[float, float]],
    color: Sequence[int],
    filled: bool = False,
    thickness: int = 1
) -> None:
    """
    Draws a polygon with vertices connected by Bresenham lines.
    If filled, uses scanline parity filling with Bresenham edge intersections.
    """
    n = len(vertices)
    if n < 3:
        return

    if not filled:
        for i in range(n):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % n]
            draw_bresenham_line(surface, p1[0], p1[1], p2[0], p2[1], color, thickness)
        return

    # Filled polygon via scanline rasterization
    min_y = int(round(min(p[1] for p in vertices)))
    max_y = int(round(max(p[1] for p in vertices)))
    surf_rect = surface.get_rect()
    min_y = max(0, min_y)
    max_y = min(surf_rect.height - 1, max_y)

    for y in range(min_y, max_y + 1):
        intersections = []
        for i in range(n):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % n]
            y1, y2 = p1[1], p2[1]
            x1, x2 = p1[0], p2[0]

            if y1 == y2:
                continue
            if min(y1, y2) <= y < max(y1, y2):
                # Compute x intersection
                x_inter = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                intersections.append(x_inter)

        intersections.sort()
        for i in range(0, len(intersections) - 1, 2):
            x_start = max(0, int(round(intersections[i])))
            x_end = min(surf_rect.width - 1, int(round(intersections[i + 1])))
            for px in range(x_start, x_end + 1):
                surface.set_at((px, y), color)
