"""
Level Specification: The Watchtower Silo.
Fulfills all level progression, environment, and props specifications from LevelDesign skill.
Features:
- Buoyant crate in knee-deep water
- Pendulum dynamic swinging power cable
- Catwalk, bent steel locker, and searchlight hazard
- Generator alcove with suspended Mind-Control Helmet and Master Lever
- Freight Lift multi-stage elevator platform
- Detached lower ledge with twin workers and 100 kg Battery Core
- Rusted iron ceiling hatch exit
- Rain atmosphere and water rendering via Bresenham line and rect algorithms
"""

import math
import random
from typing import List, Tuple
import pygame

from core.math2d import Matrix3x3
from core.drawing import (
    draw_bresenham_line,
    draw_bresenham_circle,
    draw_bresenham_rect,
    draw_bresenham_polygon
)
from entities.crate import CargoCrate, BatteryCore
from entities.worker import WorkerGroup
from entities.searchlight import Searchlight


class PowerCable:
    """
    Spline-based dynamic swinging rope/cable.
    Pendulum physics driven by gravity, damping, and player pump torque.
    Anchored to high ceiling truss overhead, providing a sweeping arc to launch onto the catwalk.
    """
    def __init__(self, pivot_x: float, pivot_y: float, length: float = 800.0):
        self.pivot_x = float(pivot_x)
        self.pivot_y = float(pivot_y)
        self.length = float(length)
        self.angle = 0.0  # Radians (0 = hanging straight down)
        self.angular_vel = 0.0
        self.damping = 0.38  # Smooth damping for weighty industrial feel
        self.gravity = 9.81 * 60.0
        self.max_angular_vel = 1.8  # Max rotation speed in rad/s

    def apply_swing_torque(self, torque: float, dt: float):
        self.angular_vel += torque * dt
        self.angular_vel = max(-self.max_angular_vel, min(self.max_angular_vel, self.angular_vel))

    def update(self, dt: float):
        # Pendulum equation: d^2θ/dt^2 = -(g/L) sin(θ) - damping * dθ/dt
        accel = -(self.gravity / self.length) * math.sin(self.angle) - self.damping * self.angular_vel
        self.angular_vel += accel * dt
        self.angular_vel = max(-self.max_angular_vel, min(self.max_angular_vel, self.angular_vel))
        self.angle += self.angular_vel * dt
        # Clamp maximum swing angle to ±60 degrees
        self.angle = max(-math.radians(60), min(math.radians(60), self.angle))

    def get_tip_position(self) -> Tuple[float, float]:
        tip_x = self.pivot_x + self.length * math.sin(self.angle)
        tip_y = self.pivot_y + self.length * math.cos(self.angle)
        return (tip_x, tip_y)

    def get_tangential_velocity_x(self) -> float:
        return self.length * self.angular_vel * math.cos(self.angle)

    def get_tangential_velocity_y(self) -> float:
        return -self.length * self.angular_vel * math.sin(self.angle)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        """Draws the dynamic cable as articulated chain segments."""
        num_segments = 22
        seg_len = self.length / num_segments

        prev_x = self.pivot_x - cam_x
        prev_y = self.pivot_y - cam_y

        # Ceiling girder truss supporting the pivot
        ceiling_scr_y = 80.0 - cam_y
        draw_bresenham_line(surface, prev_x, ceiling_scr_y, prev_x, prev_y, (120, 120, 120), thickness=3)

        # Anchor mount plate
        draw_bresenham_rect(surface, prev_x - 10, prev_y - 8, 20, 8, (190, 190, 190), filled=True)

        for i in range(1, num_segments + 1):
            cur_len = i * seg_len
            # Catoloid / slight pendulum curve
            sub_angle = self.angle * (i / num_segments)
            cur_x = (self.pivot_x + cur_len * math.sin(sub_angle)) - cam_x
            cur_y = (self.pivot_y + cur_len * math.cos(sub_angle)) - cam_y

            draw_bresenham_line(surface, prev_x, prev_y, cur_x, cur_y, (215, 215, 215), thickness=2)
            prev_x, prev_y = cur_x, cur_y

        # Weighted grab hook at the tip
        draw_bresenham_circle(surface, prev_x, prev_y, 4.5, (240, 240, 240), filled=True)


class FreightLiftState:
    SUSPENDED = "suspended"
    LOWERING = "lowering"
    LOWERED = "lowered"
    ASCENDING = "ascending"
    AT_ROOF = "at_roof"


class FreightLift:
    """
    Industrial freight lift kinetic platform.
    Smooth multi-stop elevator mechanism connecting Lower Ledge, Mid Catwalk, and Roof Crown.
    Reliably carries Boy, Battery Core, and Workers during both upward and downward transit.
    """
    def __init__(self, x: float, suspended_y: float, lowered_y: float, roof_y: float):
        self.x = float(x)
        self.y = float(suspended_y)
        self.width = 150.0
        self.height = 20.0

        self.suspended_y = float(suspended_y)
        self.lowered_y = float(lowered_y)
        self.roof_y = float(roof_y)

        self.state = FreightLiftState.SUSPENDED
        self.target_y = float(suspended_y)
        self.speed = 140.0
        self.has_power = True
        self.battery_installed = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def is_boy_on_lift(self, boy) -> bool:
        if not boy or not boy.is_alive:
            return False
        # Horizontal check
        if self.x - 8.0 <= boy.x <= self.x + self.width + 8.0:
            # Vertical check (feet near or on platform)
            if abs(boy.y - self.y) < 18.0 or (self.y - 12.0 <= boy.y <= self.y + 25.0):
                return True
        return False

    def trigger_lower(self, target_y: float = None):
        """Commands lift to lower down."""
        self.target_y = target_y if target_y is not None else self.lowered_y
        self.state = FreightLiftState.LOWERING

    def trigger_ascent(self, target_y: float = None):
        """Commands lift to ascend up."""
        if target_y is not None:
            self.target_y = target_y
        else:
            self.target_y = self.roof_y if self.battery_installed else self.suspended_y
        self.state = FreightLiftState.ASCENDING

    def toggle_move(self):
        """Toggles between lowering and ascending depending on current position and state."""
        # If currently lowering -> reverse to ascending
        if self.state == FreightLiftState.LOWERING:
            self.trigger_ascent()
            return
        # If currently ascending -> reverse to lowering
        if self.state == FreightLiftState.ASCENDING:
            self.trigger_lower(self.lowered_y)
            return

        # If stationary at or near lower level
        if self.y >= self.lowered_y - 20.0:
            target = self.roof_y if self.battery_installed else self.suspended_y
            self.trigger_ascent(target)
        # If stationary at or near roof
        elif self.y <= self.roof_y + 20.0:
            self.trigger_lower(self.lowered_y)
        # If stationary at catwalk
        else:
            self.trigger_lower(self.lowered_y)

    def update(self, dt: float, boy, battery):
        boy_on_lift = self.is_boy_on_lift(boy)

        # Check battery presence on lift
        if battery:
            if not self.battery_installed:
                if self.rect.inflate(16, 16).colliderect(battery.rect) or battery.is_on_lift:
                    self.battery_installed = True
                    battery.is_on_lift = True
            elif battery.is_on_lift:
                battery.x = self.x + 20.0

        # Movement execution
        if self.state == FreightLiftState.LOWERING:
            self.y += self.speed * dt
            if self.y >= self.target_y:
                self.y = self.target_y
                self.state = FreightLiftState.LOWERED
        elif self.state == FreightLiftState.ASCENDING:
            self.y -= self.speed * dt
            if self.y <= self.target_y:
                self.y = self.target_y
                if self.target_y <= self.roof_y + 15.0:
                    self.state = FreightLiftState.AT_ROOF
                else:
                    self.state = FreightLiftState.SUSPENDED

        # Solid passenger attachment: carry boy and battery smoothly
        if boy and boy_on_lift:
            boy.y = self.y
            boy.vy = 0.0
            boy.is_grounded = True
            if boy.state == "airborne":
                boy.state = "grounded"

        if battery and self.battery_installed:
            battery.y = self.y - battery.height + 2.0
            battery.vy = 0.0

        # Automatic trigger: if boy steps on lift switch with battery installed at lower level
        if self.state == FreightLiftState.LOWERED and self.battery_installed and boy_on_lift:
            self.trigger_ascent(self.roof_y)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        draw_x = self.x - cam_x
        draw_y = self.y - cam_y

        # Elevator platform tray
        color_tray = (40, 40, 40)
        color_trim = (220, 220, 220)
        draw_bresenham_rect(surface, draw_x, draw_y, self.width, self.height, color_tray, filled=True)
        draw_bresenham_rect(surface, draw_x, draw_y, self.width, self.height, color_trim, filled=False, thickness=2)

        # Suspension steel cables going up to ceiling
        ceiling_scr_y = 60.0 - cam_y
        cable_l_x = draw_x + 12
        cable_r_x = draw_x + self.width - 12
        draw_bresenham_line(surface, cable_l_x, ceiling_scr_y, cable_l_x, draw_y, (160, 160, 160), 2)
        draw_bresenham_line(surface, cable_r_x, ceiling_scr_y, cable_r_x, draw_y, (160, 160, 160), 2)

        # Platform floor switch / control pad in center
        switch_color = (255, 255, 255) if (self.state in (FreightLiftState.ASCENDING, FreightLiftState.LOWERING)) else (140, 140, 140)
        draw_bresenham_rect(surface, draw_x + self.width * 0.4, draw_y - 3, self.width * 0.2, 4, switch_color, filled=True)


class MindControlHelmet:
    """
    Ceiling-mounted suspended mind-control helmet.
    Transfers boy inputs to proxy workers.
    """
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.radius = 16.0
        self.is_active = False

    def check_interaction(self, boy) -> bool:
        """Checks if boy jumps up into helmet node."""
        # Must be jumping upward into the dome (not dropping down or already in mind control)
        if boy.vy > -20.0 or boy.state == "mind_control":
            return False
        dist = math.sqrt((boy.x - self.x) ** 2 + ((boy.y - 48.0) - self.y) ** 2)
        return dist < 26.0

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        screen_x = self.x - cam_x
        screen_y = self.y - cam_y

        # Ribbed coiled cable from ceiling
        ceiling_scr_y = (self.y - 140.0) - cam_y
        draw_bresenham_line(surface, screen_x, ceiling_scr_y, screen_x, screen_y - self.radius, (170, 170, 170), 2)

        # Glass dome helmet (upper hemisphere)
        dome_color = (255, 255, 255) if self.is_active else (200, 200, 200)
        draw_bresenham_circle(surface, screen_x, screen_y, self.radius, dome_color, filled=False)
        # Inner glowing node
        draw_bresenham_circle(surface, screen_x, screen_y - 2, 6.0, (245, 245, 245), filled=True)


class MasterLever:
    """Master generator alcove lever to reroute power and control the freight lift."""
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.is_pulled = False
        self.handle_angle = -math.radians(35)  # Points up-left

    def toggle(self):
        self.is_pulled = not self.is_pulled
        if self.is_pulled:
            self.handle_angle = math.radians(40)  # Rotates down-right
        else:
            self.handle_angle = -math.radians(35) # Rotates up-left

    def check_range(self, boy) -> bool:
        return abs(boy.x - self.x) < 36.0 and abs(boy.y - self.y) < 32.0

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        scr_x = self.x - cam_x
        scr_y = self.y - cam_y

        # Lever pedestal base
        draw_bresenham_rect(surface, scr_x - 8, scr_y - 14, 16, 14, (70, 70, 70), filled=True)
        draw_bresenham_rect(surface, scr_x - 8, scr_y - 14, 16, 14, (200, 200, 200), filled=False, thickness=1)

        # Handle rotated via custom 3x3 matrix (Rule 4)
        m_rot = Matrix3x3.translation(scr_x, scr_y - 10).multiply(Matrix3x3.rotation(self.handle_angle))
        handle_tip = m_rot.transform_point(0.0, -22.0)

        draw_bresenham_line(surface, scr_x, scr_y - 10, handle_tip[0], handle_tip[1], (230, 230, 230), thickness=2)
        draw_bresenham_circle(surface, handle_tip[0], handle_tip[1], 4.0, (255, 255, 255), filled=True)


class RustedIronHatch:
    """Silo roof access door. Opened to complete level."""
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.width = 110.0
        self.height = 16.0
        self.is_open = False
        self.open_angle = 0.0

    def open(self):
        self.is_open = True
        self.open_angle = -math.radians(75)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        scr_x = self.x - cam_x
        scr_y = self.y - cam_y

        if not self.is_open:
            # Closed hatch plate
            draw_bresenham_rect(surface, scr_x, scr_y, self.width, self.height, (45, 45, 45), filled=True)
            draw_bresenham_rect(surface, scr_x, scr_y, self.width, self.height, (210, 210, 210), filled=False, thickness=2)
            # Center lock wheel
            draw_bresenham_circle(surface, scr_x + self.width / 2, scr_y + self.height / 2, 6.0, (180, 180, 180), filled=False)
        else:
            # Open hatch swung on hinge
            m_hinge = Matrix3x3.translation(scr_x, scr_y).multiply(Matrix3x3.rotation(self.open_angle))
            tip = m_hinge.transform_point(self.width, 0.0)
            draw_bresenham_line(surface, scr_x, scr_y, tip[0], tip[1], (220, 220, 220), thickness=3)


class RainDrop:
    __slots__ = ('x', 'y', 'speed', 'length')

    def __init__(self, silo_w: float, silo_h: float):
        self.x = random.uniform(40, silo_w - 40)
        self.y = random.uniform(0, silo_h)
        self.speed = random.uniform(700, 1100)
        self.length = random.uniform(12, 22)


class SiloLevel:
    """
    The entire Watchtower Silo environment.
    Manages geometry, platforms, props, physics updates, and rendering.
    """
    def __init__(self):
        # Silo boundaries
        self.width = 1620.0
        self.height = 1450.0
        self.wall_left = 60.0
        self.wall_right = 1560.0

        # Flooded ground level
        self.water_y = 1200.0
        self.floor_y = 1260.0

        # Ruptured intake pipe (Phase 1 spawn point)
        self.spawn_x = 100.0
        self.spawn_y = 960.0

        # Props
        self.crate = CargoCrate(x=140.0, y=1160.0, width=72.0, height=52.0)
        self.power_cable = PowerCable(pivot_x=280.0, pivot_y=220.0, length=800.0)

        # Mid-level catwalk & stealth (Phase 2)
        self.catwalk_y = 720.0
        self.locker_rect = pygame.Rect(640, int(self.catwalk_y - 68), 44, 68)
        self.searchlight = Searchlight(mount_x=790.0, mount_y=450.0)

        # Generator alcove (Phase 3 & 4)
        self.helmet = MindControlHelmet(x=1010.0, y=630.0)
        self.master_lever = MasterLever(x=1080.0, y=self.catwalk_y)

        # Detached lower ledge (Phase 3 minion puzzle)
        self.lower_ledge_y = 1170.0
        self.worker_group = WorkerGroup(spawn_x=1220.0, spawn_y=self.lower_ledge_y)
        self.battery = BatteryCore(x=1360.0, y=self.lower_ledge_y - 40.0)

        # Freight Lift Platform
        self.freight_lift = FreightLift(
            x=1120.0,
            suspended_y=self.catwalk_y - 10.0,
            lowered_y=self.lower_ledge_y - 20.0,
            roof_y=160.0
        )

        # Ceiling maintenance hatch
        self.roof_hatch = RustedIronHatch(x=1140.0, y=140.0)

        # Collision platforms: list of (x, y, w, h)
        self.platforms = [
            # Ground floor
            (self.wall_left, self.floor_y, self.wall_right - self.wall_left, 60.0),
            # Catwalk grating
            (350.0, self.catwalk_y, 600.0, 16.0),
            # Generator alcove floor
            (950.0, self.catwalk_y, 170.0, 20.0),
            # Detached lower ledge
            (1190.0, self.lower_ledge_y, 370.0, 30.0),
        ]

        # Rain particle system
        self.raindrops = [RainDrop(self.width, self.height) for _ in range(160)]

        # Water ripple animation timer
        self.water_time = 0.0

    def get_solid_platforms(self) -> list:
        plats = list(self.platforms)
        # Crate top acts as a solid mantle platform when stable
        plats.append((self.crate.x, self.crate.top_y, self.crate.width, 10.0))
        # Freight lift platform acts as solid ground
        plats.append((self.freight_lift.x, self.freight_lift.y, self.freight_lift.width, self.freight_lift.height))
        return plats

    def update(self, dt: float, boy) -> bool:
        """Updates environment physics, rain, searchlight, and elevator. Returns True on boy death."""
        self.water_time += dt

        # Update rain
        for drop in self.raindrops:
            drop.y += drop.speed * dt
            if drop.y > self.height:
                drop.y = random.uniform(0, 50)
                drop.x = random.uniform(self.wall_left + 10, self.wall_right - 10)

        # Update crate physics
        self.crate.update(dt, self.water_y, self.floor_y, self.wall_left, self.wall_right)

        # Update swinging cable
        self.power_cable.update(dt)

        # Update searchlight hazard (Phase 2)
        killed = self.searchlight.update(dt, boy, self.locker_rect, self.catwalk_y)

        # Update freight lift
        self.freight_lift.update(dt, boy, self.battery)

        # Update battery physics if not loaded
        if not self.battery.is_on_lift:
            self.battery.update(dt, self.lower_ledge_y, 1190.0, self.wall_right)

        return killed

    def reset_checkpoint_phase2(self, boy):
        """Respawns boy at the starting spawn point (intake pipe) after searchlight death."""
        boy.x = self.spawn_x
        boy.y = self.spawn_y
        boy.vx = 0.0
        boy.vy = 0.0
        boy.is_alive = True
        boy.state = "airborne"
        self.searchlight.reset_alert()

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        """Renders the entire silo environment in monochrome chiaroscuro via Bresenham rasterizer."""
        # 1. Silo concrete architecture (boundary walls & ceiling)
        scr_wl = self.wall_left - cam_x
        scr_wr = self.wall_right - cam_x
        scr_ceil = 80.0 - cam_y
        scr_fl = self.floor_y - cam_y

        wall_color = (130, 130, 130)
        fill_dark = (18, 18, 18)

        # Silo outer bounds
        draw_bresenham_line(surface, scr_wl, scr_ceil, scr_wl, scr_fl + 60, wall_color, thickness=4)
        draw_bresenham_line(surface, scr_wr, scr_ceil, scr_wr, scr_fl + 60, wall_color, thickness=4)
        draw_bresenham_line(surface, scr_wl, scr_ceil, scr_wr, scr_ceil, wall_color, thickness=4)

        # Intake pipe at left wall
        scr_pipe_y = 960.0 - cam_y
        draw_bresenham_rect(surface, scr_wl - 20, scr_pipe_y - 25, 45, 50, (65, 65, 65), filled=True)
        draw_bresenham_rect(surface, scr_wl - 20, scr_pipe_y - 25, 45, 50, (190, 190, 190), filled=False, thickness=2)

        # 2. Catwalk grates
        catwalk_scr_x = 350.0 - cam_x
        catwalk_scr_y = self.catwalk_y - cam_y
        draw_bresenham_rect(surface, catwalk_scr_x, catwalk_scr_y, 600.0, 16.0, (40, 40, 40), filled=True)
        draw_bresenham_rect(surface, catwalk_scr_x, catwalk_scr_y, 600.0, 16.0, (180, 180, 180), filled=False, thickness=2)
        # Catwalk industrial grate gaps
        for gx in range(int(catwalk_scr_x) + 8, int(catwalk_scr_x + 592), 16):
            draw_bresenham_line(surface, gx, catwalk_scr_y + 2, gx, catwalk_scr_y + 14, (90, 90, 90), 1)

        # 3. Bent Steel Locker (Stealth Occluder)
        scr_lock_x = self.locker_rect.x - cam_x
        scr_lock_y = self.locker_rect.y - cam_y
        draw_bresenham_rect(surface, scr_lock_x, scr_lock_y, self.locker_rect.width, self.locker_rect.height, (35, 35, 35), filled=True)
        draw_bresenham_rect(surface, scr_lock_x, scr_lock_y, self.locker_rect.width, self.locker_rect.height, (170, 170, 170), filled=False, thickness=2)
        # Bent dent diagonal crease
        draw_bresenham_line(surface, scr_lock_x + 5, scr_lock_y + 12, scr_lock_x + self.locker_rect.width - 6, scr_lock_y + 36, (100, 100, 100), 1)

        # 4. Generator Alcove
        alcove_scr_x = 950.0 - cam_x
        draw_bresenham_rect(surface, alcove_scr_x, catwalk_scr_y, 170.0, 20.0, (45, 45, 45), filled=True)
        draw_bresenham_rect(surface, alcove_scr_x, catwalk_scr_y, 170.0, 20.0, (190, 190, 190), filled=False, thickness=2)
        # Alcove back wall frame
        draw_bresenham_line(surface, alcove_scr_x, catwalk_scr_y - 180, alcove_scr_x, catwalk_scr_y, (120, 120, 120), 2)
        draw_bresenham_line(surface, alcove_scr_x + 170, catwalk_scr_y - 180, alcove_scr_x + 170, catwalk_scr_y, (120, 120, 120), 2)

        # 5. Detached Lower Ledge
        ledge_scr_x = 1190.0 - cam_x
        ledge_scr_y = self.lower_ledge_y - cam_y
        draw_bresenham_rect(surface, ledge_scr_x, ledge_scr_y, 370.0, 30.0, (30, 30, 30), filled=True)
        draw_bresenham_rect(surface, ledge_scr_x, ledge_scr_y, 370.0, 30.0, (175, 175, 175), filled=False, thickness=2)

        # 6. Props in scene
        self.crate.draw(surface, cam_x, cam_y)
        self.power_cable.draw(surface, cam_x, cam_y)
        self.searchlight.draw(surface, cam_x, cam_y, self.catwalk_y, self.locker_rect)
        self.helmet.draw(surface, cam_x, cam_y)
        self.master_lever.draw(surface, cam_x, cam_y)
        self.battery.draw(surface, cam_x, cam_y)
        self.freight_lift.draw(surface, cam_x, cam_y)
        self.roof_hatch.draw(surface, cam_x, cam_y)

        # 7. Workers
        self.worker_group.draw(surface, cam_x, cam_y)

        # 8. Flooded knee-deep water layer & surface ripples
        water_scr_y = self.water_y - cam_y
        water_h = (self.floor_y + 60.0) - self.water_y

        # Semi-transparent dark stagnant water
        water_surf = pygame.Surface((surface.get_width(), int(water_h)), pygame.SRCALPHA)
        water_surf.fill((10, 14, 18, 150))
        surface.blit(water_surf, (0, int(water_scr_y)))

        # Bresenham water surface line with undulating ripples
        water_line_color = (200, 200, 200)
        step = 28
        for rx in range(int(scr_wl), int(scr_wr), step):
            ripple_offset = math.sin(self.water_time * 3.5 + rx * 0.05) * 2.5
            draw_bresenham_line(surface, rx, water_scr_y + ripple_offset, rx + step, water_scr_y - ripple_offset, water_line_color, 1)

        # 9. Falling cold rain streaks
        rain_color = (160, 160, 160)
        for drop in self.raindrops:
            dx = drop.x - cam_x
            dy = drop.y - cam_y
            draw_bresenham_line(surface, dx, dy, dx - 2, dy + drop.length, rain_color, 1)
