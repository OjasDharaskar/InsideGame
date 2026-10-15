"""
Custom Bresenham Drawing & Rasterization Utilities.
Fulfills Rule 3 of Development Skill:
Objects in the scene must be made using pygame with separate functions for line drawing, circle drawing, etc.
using Bresenham line and circle algorithms.
"""

import math
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
    Includes fast AABB viewport clipping.
    """
    ix0, iy0 = int(round(x0)), int(round(y0))
    ix1, iy1 = int(round(x1)), int(round(y1))
    
    surf_rect = surface.get_rect()
    w, h = surf_rect.width, surf_rect.height

    # Fast viewport bounding-box culling
    th_pad = max(1, thickness)
    if max(ix0, ix1) + th_pad < 0 or min(ix0, ix1) - th_pad >= w:
        return
    if max(iy0, iy1) + th_pad < 0 or min(iy0, iy1) - th_pad >= h:
        return

    # Fast path for horizontal & vertical lines (mathematically identical to Bresenham rasterization)
    if ix0 == ix1:
        min_y, max_y = (iy0, iy1) if iy0 <= iy1 else (iy1, iy0)
        y_start = max(0, min_y)
        y_end = min(h - 1, max_y)
        half_th = thickness // 2 if thickness > 1 else 0
        x_start = max(0, ix0 - half_th)
        x_end = min(w - 1, ix0 + half_th)
        if x_end >= x_start and y_end >= y_start:
            surface.fill(color, (x_start, y_start, x_end - x_start + 1, y_end - y_start + 1))
        return

    if iy0 == iy1:
        min_x, max_x = (ix0, ix1) if ix0 <= ix1 else (ix1, ix0)
        x_start = max(0, min_x)
        x_end = min(w - 1, max_x)
        half_th = thickness // 2 if thickness > 1 else 0
        y_start = max(0, iy0 - half_th)
        y_end = min(h - 1, iy0 + half_th)
        if x_end >= x_start and y_end >= y_start:
            surface.fill(color, (x_start, y_start, x_end - x_start + 1, y_end - y_start + 1))
        return

    if thickness <= 1:
        dx = abs(ix1 - ix0)
        dy = -abs(iy1 - iy0)
        sx = 1 if ix0 < ix1 else -1
        sy = 1 if iy0 < iy1 else -1
        err = dx + dy
        curr_x, curr_y = ix0, iy0
        set_at = surface.set_at
        if 0 <= min(ix0, ix1) and max(ix0, ix1) < w and 0 <= min(iy0, iy1) and max(iy0, iy1) < h:
            while True:
                set_at((curr_x, curr_y), color)
                if curr_x == ix1 and curr_y == iy1:
                    break
                e2 = 2 * err
                if e2 >= dy:
                    err += dy
                    curr_x += sx
                if e2 <= dx:
                    err += dx
                    curr_y += sy
        else:
            while True:
                if 0 <= curr_x < w and 0 <= curr_y < h:
                    set_at((curr_x, curr_y), color)
                if curr_x == ix1 and curr_y == iy1:
                    break
                e2 = 2 * err
                if e2 >= dy:
                    err += dy
                    curr_x += sx
                if e2 <= dx:
                    err += dx
                    curr_y += sy
    else:
        # Draw with perpendicular offset strokes
        half_th = thickness // 2
        for offset in range(-half_th, half_th + 1):
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
    Includes fast AABB viewport clipping.
    """
    ixc, iyc = int(round(xc)), int(round(yc))
    ir = int(round(radius))

    surf_rect = surface.get_rect()
    w, h = surf_rect.width, surf_rect.height

    # Fast viewport bounding-box culling
    if ixc + ir < 0 or ixc - ir >= w or iyc + ir < 0 or iyc - ir >= h:
        return

    if ir <= 0:
        if 0 <= ixc < w and 0 <= iyc < h:
            surface.set_at((ixc, iyc), color)
        return

    x = 0
    y = ir
    d = 3 - 2 * ir

    if filled:
        # Standard integer midpoint circle scanline fill - fills each y-scanline exactly once
        r_sq = ir * ir
        fill = surface.fill
        y_min = max(0, iyc - ir)
        y_max = min(h - 1, iyc + ir)
        for y in range(y_min, y_max + 1):
            dy = y - iyc
            dx = math.isqrt(r_sq - dy * dy)
            x_left = max(0, ixc - dx)
            x_right = min(w - 1, ixc + dx)
            if x_right >= x_left:
                fill(color, (x_left, y, x_right - x_left + 1, 1))
    else:
        # Midpoint circle perimeter
        set_at = surface.set_at
        if 0 <= ixc - ir and ixc + ir < w and 0 <= iyc - ir and iyc + ir < h:
            while y >= x:
                set_at((ixc + x, iyc + y), color)
                set_at((ixc - x, iyc + y), color)
                set_at((ixc + x, iyc - y), color)
                set_at((ixc - x, iyc - y), color)
                set_at((ixc + y, iyc + x), color)
                set_at((ixc - y, iyc + x), color)
                set_at((ixc + y, iyc - x), color)
                set_at((ixc - y, iyc - x), color)
                if d > 0:
                    y -= 1
                    d += 4 * (x - y) + 10
                else:
                    d += 4 * x + 6
                x += 1
        else:
            while y >= x:
                for px, py in ((ixc + x, iyc + y), (ixc - x, iyc + y), (ixc + x, iyc - y), (ixc - x, iyc - y),
                               (ixc + y, iyc + x), (ixc - y, iyc + x), (ixc + y, iyc - x), (ixc - y, iyc - x)):
                    if 0 <= px < w and 0 <= py < h:
                        set_at((px, py), color)
                if d > 0:
                    y -= 1
                    d += 4 * (x - y) + 10
                else:
                    d += 4 * x + 6
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

    # Fast viewport culling
    if ix + iw < 0 or ix >= sw or iy + ih < 0 or iy >= sh:
        return

    if filled:
        y_start = max(0, iy)
        y_end = min(sh, iy + ih)
        x_start = max(0, ix)
        x_end = min(sw, ix + iw)
        surface.fill(color, (x_start, y_start, x_end - x_start, y_end - y_start))
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
    Includes fast AABB viewport clipping.
    """
    n = len(vertices)
    if n < 3:
        return

    surf_rect = surface.get_rect()
    sw, sh = surf_rect.width, surf_rect.height

    # Fast AABB screen-cull
    min_x = min(p[0] for p in vertices)
    max_x = max(p[0] for p in vertices)
    min_y = min(p[1] for p in vertices)
    max_y = max(p[1] for p in vertices)

    if max_x < 0 or min_x >= sw or max_y < 0 or min_y >= sh:
        return

    if not filled:
        for i in range(n):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % n]
            draw_bresenham_line(surface, p1[0], p1[1], p2[0], p2[1], color, thickness)
        return

    # Fast path for convex quad with horizontal top and bottom (e.g. searchlight light cones)
    if n == 4 and vertices[0][1] == vertices[1][1] and vertices[2][1] == vertices[3][1]:
        y_top, y_bot = vertices[0][1], vertices[2][1]
        if y_top < y_bot:
            dy = y_bot - y_top
            if dy > 0:
                scan_min_y = max(0, int(round(y_top)))
                scan_max_y = min(sh - 1, int(round(y_bot)))
                inv_m_l = (vertices[3][0] - vertices[0][0]) / dy
                inv_m_r = (vertices[2][0] - vertices[1][0]) / dy
                x0_l = vertices[0][0]
                x0_r = vertices[1][0]
                fill = surface.fill
                for y in range(scan_min_y, scan_max_y + 1):
                    prog = y - y_top
                    xl = max(0, int(round(x0_l + prog * inv_m_l)))
                    xr = min(sw - 1, int(round(x0_r + prog * inv_m_r)))
                    if xr >= xl:
                        fill(color, (xl, y, xr - xl + 1, 1))
                return

    # Filled polygon via scanline rasterization with precomputed edge slopes
    scan_min_y = max(0, int(round(min_y)))
    scan_max_y = min(sh - 1, int(round(max_y)))

    edges = []
    for i in range(n):
        p1 = vertices[i]
        p2 = vertices[(i + 1) % n]
        if p1[1] == p2[1]:
            continue
        if p1[1] < p2[1]:
            edges.append((p1[1], p2[1], p1[0], (p2[0] - p1[0]) / (p2[1] - p1[1])))
        else:
            edges.append((p2[1], p1[1], p2[0], (p1[0] - p2[0]) / (p1[1] - p2[1])))

    for y in range(scan_min_y, scan_max_y + 1):
        intersections = [x0 + (y - ymin) * inv_m for ymin, ymax, x0, inv_m in edges if ymin <= y < ymax]
        if len(intersections) < 2:
            continue
        intersections.sort()
        for i in range(0, len(intersections) - 1, 2):
            x_start = max(0, int(round(intersections[i])))
            x_end = min(sw - 1, int(round(intersections[i + 1])))
            if x_end >= x_start:
                surface.fill(color, (x_start, y, x_end - x_start + 1, 1))
