"""
Cargo Crate & Heavy Battery Core Entities.
Fulfills Phase 1 & Phase 3 specifications from LevelDesign skill.
Cargo Crate: Buoyant, draggable, climbable collision box.
Battery Core: 100 kg heavy prop requiring dual workers to push.
All rendered using basic monochrome geometric shapes via Bresenham rasterizer.
"""

from typing import Tuple, Optional
import pygame
from core.drawing import draw_bresenham_rect, draw_bresenham_line


class CargoCrate:
    """
    Buoyant cargo crate floating in knee-deep water.
    Can be dragged by the boy, and stood upon to jump and reach the hanging power cable.
    """
    def __init__(self, x: float, y: float, width: float = 70.0, height: float = 50.0):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.vx = 0.0
        self.vy = 0.0
        self.mass = 20.0
        self.is_grabbed = False
        self.grabbed_by = None  # Reference to Boy if grabbed
        self.in_water = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    @property
    def top_y(self) -> float:
        return self.y

    def update(self, dt: float, water_y: float, floor_y: float, min_x: float, max_x: float):
        # Gravity
        gravity = 750.0
        self.vy += gravity * dt

        # Water Buoyancy Mechanics (Archimedes principle)
        bottom_y = self.y + self.height
        if bottom_y > water_y:
            self.in_water = True
            submerged_depth = min(self.height, bottom_y - water_y)
            submerged_ratio = submerged_depth / self.height
            # Buoyant force overcomes gravity when submerged
            buoyancy_accel = 1200.0 * submerged_ratio
            self.vy -= buoyancy_accel * dt
            # Water damping
            self.vy *= (1.0 - 4.5 * dt)
            self.vx *= (1.0 - 5.0 * dt)
        else:
            self.in_water = False
            # Air resistance
            self.vx *= (1.0 - 1.5 * dt)

        # Apply velocity
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Floor collision
        if self.y + self.height > floor_y:
            self.y = floor_y - self.height
            self.vy = 0.0
            self.vx *= 0.7  # Ground friction

        # Silo wall bounds
        if self.x < min_x:
            self.x = min_x
            self.vx = 0.0
        elif self.x + self.width > max_x:
            self.x = max_x - self.width
            self.vx = 0.0

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        """Draws the crate using basic monochrome shapes & Bresenham lines."""
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        # Outer crate frame (white / light gray)
        color_frame = (210, 210, 210)
        color_fill = (45, 45, 45)
        color_braces = (140, 140, 140)

        # Fill body
        draw_bresenham_rect(surface, draw_x, draw_y, self.width, self.height, color_fill, filled=True)
        # Outline
        draw_bresenham_rect(surface, draw_x, draw_y, self.width, self.height, color_frame, filled=False, thickness=2)

        # Cross bracing (X mark in basic lines)
        draw_bresenham_line(surface, draw_x + 2, draw_y + 2, draw_x + self.width - 3, draw_y + self.height - 3, color_braces, 1)
        draw_bresenham_line(surface, draw_x + self.width - 3, draw_y + 2, draw_x + 2, draw_y + self.height - 3, color_braces, 1)


class BatteryCore:
    """
    Heavy 100 kg industrial battery block.
    Too heavy for a single pawn; requires dual coordinated workers to push onto the lift.
    """
    def __init__(self, x: float, y: float, width: float = 75.0, height: float = 40.0):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.vx = 0.0
        self.vy = 0.0
        self.mass = 100.0  # Exactly 100 kg
        self.is_on_lift = False
        self.pushed_by_count = 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def update(self, dt: float, floor_y: float, min_x: float, max_x: float):
        # Gravity
        self.vy += 800.0 * dt

        # High friction / resistance due to heavy mass
        self.vx *= (1.0 - 8.0 * dt)

        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y + self.height > floor_y:
            self.y = floor_y - self.height
            self.vy = 0.0

        if self.x < min_x:
            self.x = min_x
            self.vx = 0.0
        elif self.x + self.width > max_x:
            self.x = max_x - self.width
            self.vx = 0.0

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        color_body = (35, 35, 35)
        color_border = (230, 230, 230)
        color_terminals = (180, 180, 180)
        color_label = (120, 120, 120)

        # Filled battery box
        draw_bresenham_rect(surface, draw_x, draw_y, self.width, self.height, color_body, filled=True)
        draw_bresenham_rect(surface, draw_x, draw_y, self.width, self.height, color_border, filled=False, thickness=2)

        # Industrial battery terminals on top (small rectangles)
        draw_bresenham_rect(surface, draw_x + 10, draw_y - 6, 12, 6, color_terminals, filled=True)
        draw_bresenham_rect(surface, draw_x + self.width - 22, draw_y - 6, 12, 6, color_terminals, filled=True)

        # Industrial reinforcement horizontal bands
        draw_bresenham_line(surface, draw_x + 4, draw_y + self.height * 0.5, draw_x + self.width - 4, draw_y + self.height * 0.5, color_label, 1)

        # Weight mark "100kg" indication via tick marks
        draw_bresenham_line(surface, draw_x + self.width * 0.35, draw_y + 12, draw_x + self.width * 0.65, draw_y + 12, color_terminals, 2)
