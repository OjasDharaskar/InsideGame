"""
Perimeter Searchlight & High-Voltage Ceiling Grid.
Fulfills Phase 2 specifications from LevelDesign skill & Rule 4 of Development skill.
Features:
- Sweeping oscillating cone with constant-speed / sinusoidal angular rotation.
- Raycast line-of-sight calculation.
- Occlusion shadow projection behind the bent steel locker.
- Instant-kill alert trigger activating high-voltage ceiling grid electrocution arcs.
All rendered in crisp monochrome via Bresenham rasterizer and custom 3x3 transformation matrices.
"""

import math
import random
from typing import List, Tuple, Optional
import pygame

from core.math2d import Matrix3x3, custom_rotate_point
from core.drawing import draw_bresenham_line, draw_bresenham_circle, draw_bresenham_polygon, draw_bresenham_rect


class Searchlight:
    def __init__(self, mount_x: float, mount_y: float):
        self.mount_x = float(mount_x)
        self.mount_y = float(mount_y)

        # Sweeping parameters (Rule 4: Rotation)
        self.base_angle = math.radians(72.0)  # Aimed downward-left/right across catwalk
        self.sweep_amp = math.radians(38.0)
        self.sweep_speed = 0.95  # Oscillation frequency
        self.cone_half_angle = math.radians(13.0)
        self.beam_reach = 650.0

        self.current_angle = self.base_angle
        self.time = 0.0

        # Detection & Alert state
        self.is_alerted = False
        self.alert_timer = 0.0
        self.kill_delay = 0.28  # Reaction grace window before ceiling grid electrocution
        self.kill_triggered = False

        # Electric arc sparks for ceiling grid
        self.electric_arcs: List[Tuple[float, float, float, float]] = []

    def update(self, dt: float, boy, locker_rect: pygame.Rect, catwalk_y: float) -> bool:
        """
        Updates sweep oscillation, checks line-of-sight against locker occlusion.
        Returns True if boy is killed by electrocution.
        """
        self.time += dt
        # Oscillate angle
        self.current_angle = self.base_angle + self.sweep_amp * math.sin(self.time * self.sweep_speed)

        # Calculate beam ray endpoints at catwalk level
        left_angle = self.current_angle - self.cone_half_angle
        right_angle = self.current_angle + self.cone_half_angle

        # If already triggered kill
        if self.kill_triggered:
            # Generate violent electric arcs from ceiling grid to player
            self.electric_arcs.clear()
            for _ in range(6):
                arc_top_x = boy.x + random.uniform(-40, 40)
                arc_top_y = catwalk_y - 200.0  # Ceiling grid level
                self.electric_arcs.append((arc_top_x, arc_top_y, boy.x + random.uniform(-8, 8), boy.y - 25))
            return True

        # Check line-of-sight to boy
        in_light = self.check_boy_in_beam(boy, left_angle, right_angle, catwalk_y)
        is_occluded = False

        if in_light:
            # Check if boy is occluded in the shadow of the bent steel locker
            is_occluded = self.check_locker_occlusion(boy, locker_rect)

        if in_light and not is_occluded and boy.is_alive:
            self.is_alerted = True
            self.alert_timer += dt
            if self.alert_timer >= self.kill_delay:
                self.kill_triggered = True
                boy.is_alive = False
                return True
        else:
            self.is_alerted = False
            self.alert_timer = max(0.0, self.alert_timer - dt * 2.0)
            self.electric_arcs.clear()

        return False

    def check_boy_in_beam(self, boy, left_angle: float, right_angle: float, floor_y: float) -> bool:
        """Checks if boy's bounding box is illuminated by the spotlight cone."""
        dx = boy.x - self.mount_x
        dy = (boy.y - 28.0) - self.mount_y  # Boy center height

        if dy <= 0:
            return False  # Above the light

        dist = math.sqrt(dx * dx + dy * dy)
        if dist > self.beam_reach:
            return False

        angle_to_boy = math.atan2(dx, dy)
        min_angle = min(left_angle, right_angle)
        max_angle = max(left_angle, right_angle)

        return min_angle <= angle_to_boy <= max_angle

    def check_locker_occlusion(self, boy, locker_rect: pygame.Rect) -> bool:
        """
        Determines if the boy is hiding behind the locker in its shadow cast.
        Locker acts as a solid occluder. If boy is crouching behind it, safe!
        """
        if boy.state != "crouching":
            # Standing boy's head sticks out above the bent locker!
            return False

        # Ray from searchlight to locker top-left & top-right
        locker_center_x = locker_rect.centerx
        locker_top_y = locker_rect.top

        # If boy is right behind the locker and within shadow zone
        boy_box = boy.bounding_box
        if locker_rect.left - 20 <= boy.x <= locker_rect.right + 20:
            if boy_box.top >= locker_top_y - 5:
                return True

        return False

    def reset_alert(self):
        self.is_alerted = False
        self.alert_timer = 0.0
        self.kill_triggered = False
        self.electric_arcs.clear()

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float, catwalk_y: float, locker_rect: pygame.Rect):
        """Renders the searchlight fixture, sweeping chiaroscuro beam, shadow, and ceiling grid."""
        screen_mx = self.mount_x - cam_x
        screen_my = self.mount_y - cam_y

        # Searchlight housing fixture (swivel lamp rotated by current_angle)
        lamp_mat = Matrix3x3.translation(screen_mx, screen_my).multiply(Matrix3x3.rotation(self.current_angle))
        housing_pts = [
            lamp_mat.transform_point(-12, -8),
            lamp_mat.transform_point(12, -8),
            lamp_mat.transform_point(18, 14),
            lamp_mat.transform_point(-18, 14),
        ]
        draw_bresenham_polygon(surface, housing_pts, (60, 60, 60), filled=True)
        draw_bresenham_polygon(surface, housing_pts, (220, 220, 220), filled=False, thickness=2)
        # Mounting bracket
        draw_bresenham_circle(surface, screen_mx, screen_my, 7.0, (180, 180, 180), filled=True)

        # Calculate cone geometry to floor level
        left_angle = self.current_angle - self.cone_half_angle
        right_angle = self.current_angle + self.cone_half_angle

        length = self.beam_reach
        left_floor_x = self.mount_x + math.sin(left_angle) * length
        left_floor_y = self.mount_y + math.cos(left_angle) * length

        right_floor_x = self.mount_x + math.sin(right_angle) * length
        right_floor_y = self.mount_y + math.cos(right_angle) * length

        beam_screen_pts = [
            (screen_mx, screen_my),
            (left_floor_x - cam_x, left_floor_y - cam_y),
            (right_floor_x - cam_x, right_floor_y - cam_y),
        ]

        # Draw semi-transparent chiaroscuro beam using alpha surface
        beam_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        beam_color = (255, 255, 255, 35) if not self.is_alerted else (255, 255, 255, 90)
        pygame.draw.polygon(beam_surf, beam_color, beam_screen_pts)

        # Shadow occlusion projection behind locker
        scr_locker_left = locker_rect.left - cam_x
        scr_locker_right = locker_rect.right - cam_x
        scr_locker_top = locker_rect.top - cam_y
        scr_locker_bot = locker_rect.bottom - cam_y

        # Project shadow rays through locker corners
        dx_l = scr_locker_left - screen_mx
        dy_l = scr_locker_top - screen_my
        dx_r = scr_locker_right - screen_mx
        dy_r = scr_locker_top - screen_my

        dist_proj = 400.0
        shadow_pts = [
            (scr_locker_left, scr_locker_top),
            (scr_locker_left + dx_l * 2.0, scr_locker_top + dy_l * 2.0),
            (scr_locker_right + dx_r * 2.0, scr_locker_top + dy_r * 2.0),
            (scr_locker_right, scr_locker_top)
        ]
        # Carve out shadow from beam (pure black chiaroscuro shadow)
        pygame.draw.polygon(beam_surf, (0, 0, 0, 180), shadow_pts)
        surface.blit(beam_surf, (0, 0))

        # Bresenham beam edge lines (stark high-contrast boundary)
        edge_color = (180, 180, 180) if not self.is_alerted else (255, 255, 255)
        draw_bresenham_line(surface, screen_mx, screen_my, left_floor_x - cam_x, left_floor_y - cam_y, edge_color, 1)
        draw_bresenham_line(surface, screen_mx, screen_my, right_floor_x - cam_x, right_floor_y - cam_y, edge_color, 1)

        # High-Voltage Ceiling Grid (Lethal volume above catwalk)
        grid_y = (catwalk_y - 190.0) - cam_y
        grid_start_x = 360.0 - cam_x
        grid_end_x = 940.0 - cam_x
        grid_color = (90, 90, 90) if not self.is_alerted else (240, 240, 240)

        # Horizontal mesh wires
        draw_bresenham_line(surface, grid_start_x, grid_y, grid_end_x, grid_y, grid_color, 2)
        draw_bresenham_line(surface, grid_start_x, grid_y + 12, grid_end_x, grid_y + 12, grid_color, 1)
        draw_bresenham_line(surface, grid_start_x, grid_y + 24, grid_end_x, grid_y + 24, grid_color, 1)

        # Vertical mesh rungs
        step = 24
        cur_x = grid_start_x
        while cur_x < grid_end_x:
            draw_bresenham_line(surface, cur_x, grid_y, cur_x, grid_y + 24, grid_color, 1)
            cur_x += step

        # Render lethal electric arcs when electrocuting
        for x1, y1, x2, y2 in self.electric_arcs:
            # Segmented lightning zig-zags
            mid_x = (x1 + x2) * 0.5 + random.uniform(-18, 18)
            mid_y = (y1 + y2) * 0.5 + random.uniform(-10, 10)
            draw_bresenham_line(surface, x1 - cam_x, y1 - cam_y, mid_x - cam_x, mid_y - cam_y, (255, 255, 255), 2)
            draw_bresenham_line(surface, mid_x - cam_x, mid_y - cam_y, x2 - cam_x, y2 - cam_y, (255, 255, 255), 2)
