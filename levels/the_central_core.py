"""
Level 3: The Central Core (Hive Mind Overdrive) - Extended Challenging Edition
Grand Finale and Climax of INSIDE.

Fulfills all requirements from Computer Graphics & Gaming specification:
- Pure integer Bresenham Line & Midpoint Circle algorithms
- Custom 3x3 Homogeneous transformation matrices for 2D affine transformations (translation, rotation, scale)
- Scanline polygon rasterization with parity for dynamic light cones, shadows, and alarm strobes
- Dynamic pendulum swing physics with forward kinematics for the momentum crane
- Coordinated multi-worker proxy squad (6 workers) with hydraulic bridge puzzle and mobile canopy shelter
- Moving cargo hoists, lethal 550px molten abyss, kinetic obstacle course (crouch-sliding, vaulting, falling debris)
"""

import math
import random
from typing import List, Tuple, Optional
import pygame

from core.math2d import Matrix3x3
from core.drawing import (
    draw_bresenham_line,
    draw_bresenham_circle,
    draw_bresenham_rect,
    draw_bresenham_polygon
)
from entities.boy import Boy, BoyState
from entities.worker import Worker, WorkerState
from core.input_handler import Action, InputHandler


# =============================================================================
# Graphics Helpers & Scanline Utilities
# =============================================================================

def fill_scanline_shadow(surface: pygame.Surface, x: float, y: float, width: float, height: float, color=(10, 10, 12)):
    """Fills an occluded rectangular drop shadow."""
    draw_bresenham_rect(surface, x, y, width, height, color, filled=True)


# =============================================================================
# Particle System (Sparks, Steam, Reactor Discharges)
# =============================================================================

class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size')

    def __init__(self, x: float, y: float, vx: float, vy: float, life: float, color: Tuple[int, int, int], size: float = 2.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size


class CentralCoreParticles:
    def __init__(self):
        self.particles: List[Particle] = []

    def spawn(self, x: float, y: float, count: int = 8, color: Tuple[int, int, int] = (240, 240, 255), speed_scale: float = 1.0):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(40, 180) * speed_scale
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd - random.uniform(20, 60)
            life = random.uniform(0.3, 0.8)
            size = random.uniform(1.5, 3.0)
            self.particles.append(Particle(x, y, vx, vy, life, color, size))

    def update(self, dt: float):
        gravity = 500.0
        for p in self.particles[:]:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += gravity * dt
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        for p in self.particles:
            sx = p.x - cam_x
            if -10 <= sx <= 1290:
                sy = p.y - cam_y
                if -10 <= sy <= 730:
                    draw_bresenham_circle(surface, sx, sy, p.size, p.color, filled=True)


# =============================================================================
# Level Props & Interactive CG Entities
# =============================================================================

class HighVoltageGrid:
    """
    Lethal electrified floor grid spanning Zone 1.
    Renders erratic electrical arcs via Bresenham lines.
    """
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.arc_timer = 0.0

    def is_touching(self, entity_x: float, entity_y: float) -> bool:
        return (self.x <= entity_x <= self.x + self.width and
                abs(entity_y - self.y) < 18.0)

    def update(self, dt: float):
        self.arc_timer += dt

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        sx = self.x - cam_x
        sy = self.y - cam_y
        if sx + self.width < -50 or sx > 1330:
            return

        draw_bresenham_rect(surface, sx, sy + 4, self.width, self.height, (40, 40, 48), filled=True)
        draw_bresenham_line(surface, sx, sy + 4, sx + self.width, sy + 4, (120, 120, 130), thickness=2)

        for px in range(int(sx), int(sx + self.width), 50):
            draw_bresenham_line(surface, px, sy, px, sy + 14, (180, 180, 180), thickness=2)
            draw_bresenham_circle(surface, px, sy + 2, 4, (220, 220, 220), filled=False)

        num_arcs = 6
        for a in range(num_arcs):
            offset_x = ((a * 97) + int(self.arc_timer * 340)) % int(self.width - 40)
            x0 = sx + offset_x
            y0 = sy + 2
            x1 = x0 + random.uniform(25, 45)
            y1 = sy + random.uniform(-10, 4)
            mid_x = (x0 + x1) * 0.5 + random.uniform(-6, 6)
            mid_y = min(y0, y1) - random.uniform(8, 16)
            draw_bresenham_line(surface, x0, y0, mid_x, mid_y, (240, 245, 255), thickness=1)
            draw_bresenham_line(surface, mid_x, mid_y, x1, y1, (200, 220, 255), thickness=1)


class MovingCargoHoist:
    """
    Automated kinetic gantry hoist platform translating over the Zone 1 voltage grid.
    Requires timed platforming to bridge the entrance to the Overdrive Pod.
    """
    def __init__(self, min_x: float, max_x: float, y: float, width: float = 120.0, height: float = 16.0, speed: float = 85.0):
        self.min_x = min_x
        self.max_x = max_x
        self.x = min_x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.dir = 1
        self.vx = speed

    def update(self, dt: float):
        self.x += self.dir * self.speed * dt
        self.vx = self.dir * self.speed
        if self.x > self.max_x:
            self.x = self.max_x
            self.dir = -1
        elif self.x < self.min_x:
            self.x = self.min_x
            self.dir = 1

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        sx = self.x - cam_x
        sy = self.y - cam_y
        if sx + self.width < -50 or sx > 1330:
            return

        # Platform plate
        draw_bresenham_rect(surface, sx, sy, self.width, self.height, (35, 38, 48), filled=True)
        draw_bresenham_rect(surface, sx, sy, self.width, self.height, (210, 215, 230), filled=False, thickness=2)
        # Suspension cables to ceiling rail
        draw_bresenham_line(surface, sx + 15, 0 - cam_y, sx + 15, sy, (120, 120, 130), thickness=2)
        draw_bresenham_line(surface, sx + self.width - 15, 0 - cam_y, sx + self.width - 15, sy, (120, 120, 130), thickness=2)
        # Pulley wheels on platform
        draw_bresenham_circle(surface, sx + 15, sy, 5, (255, 255, 255), filled=True)
        draw_bresenham_circle(surface, sx + self.width - 15, sy, 5, (255, 255, 255), filled=True)


class OverdrivePod:
    """
    Suspended neural amplification helmet pod.
    Transports the Boy along an overhead rail from Zone 1 to Zone 3 upon meltdown.
    """
    def __init__(self, x: float, y: float):
        self.start_x = x
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.is_occupied = False
        self.pulse_phase = 0.0

    def update(self, dt: float):
        self.pulse_phase += dt * 3.5
        self.x += (self.target_x - self.x) * min(1.0, 3.5 * dt)
        self.y += (self.target_y - self.y) * min(1.0, 3.5 * dt)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        sx = self.x - cam_x
        sy = self.y - cam_y

        # Suspension conduit & rail (culled to screen)
        if 600 - cam_x <= 1330 and 2600 - cam_x >= -50:
            draw_bresenham_line(surface, 600 - cam_x, 80 - cam_y, 2600 - cam_x, 80 - cam_y, (80, 80, 90), thickness=3)

        if -50 <= sx <= 1330:
            draw_bresenham_line(surface, sx, 0 - cam_y, sx, sy - 20, (140, 140, 140), thickness=2)
            draw_bresenham_rect(surface, sx - 8, sy - 24, 16, 8, (200, 200, 200), filled=True)

            glow = int(180 + 55 * math.sin(self.pulse_phase))
            dome_color = (glow, glow, 255) if self.is_occupied else (160, 160, 170)
            draw_bresenham_circle(surface, sx, sy, 14, dome_color, filled=False)
            draw_bresenham_circle(surface, sx, sy, 11, (30, 32, 42), filled=True)

            if self.is_occupied:
                pulse_r = 16 + 4 * math.sin(self.pulse_phase * 1.5)
                draw_bresenham_circle(surface, sx, sy, pulse_r, (255, 255, 255), filled=False)
                draw_bresenham_line(surface, sx - 16, sy, sx + 16, sy, (255, 255, 255))


class ReactorCore:
    """
    Colossal background reactor core with rotating cooling vanes.
    Uses custom 3x3 Homogeneous transformation matrices for continuous rotation.
    """
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.angular_velocity = 0.6
        self.is_meltdown = False
        self.meltdown_timer = 0.0

    def trigger_meltdown(self):
        self.is_meltdown = True

    def update(self, dt: float):
        if self.is_meltdown:
            self.meltdown_timer += dt
            self.angular_velocity = min(11.0, self.angular_velocity + dt * 3.8)
        self.angle += self.angular_velocity * dt

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        bg_cam_x = cam_x * 0.7
        bg_cam_y = cam_y * 0.7
        cx = self.x - bg_cam_x
        cy = self.y - bg_cam_y

        # Viewport culling (reactor radius with vanes is ~180)
        if cx < -220 or cx > 1500 or cy < -220 or cy > 940:
            return

        draw_bresenham_circle(surface, cx, cy, 180, (28, 30, 36), filled=True)
        draw_bresenham_circle(surface, cx, cy, 180, (90, 92, 105), filled=False)
        draw_bresenham_circle(surface, cx, cy, 140, (140, 142, 155), filled=False)
        draw_bresenham_circle(surface, cx, cy, 100, (40, 42, 50), filled=True)

        num_vanes = 8
        for i in range(num_vanes):
            vane_angle = self.angle + (i * 2.0 * math.pi / num_vanes)
            rot_mat = Matrix3x3.rotation(vane_angle)

            local_pts = [
                (20.0, -8.0),
                (135.0, -18.0),
                (138.0, 18.0),
                (20.0, 8.0)
            ]

            screen_pts = []
            for lx, ly in local_pts:
                rx, ry = rot_mat.transform_point(lx, ly)
                screen_pts.append((cx + rx, cy + ry))

            blade_color = (200, 205, 215) if not self.is_meltdown else (255, 140, 140)
            draw_bresenham_polygon(surface, screen_pts, blade_color, filled=False)

        core_r = 38.0 + (6.0 * math.sin(self.meltdown_timer * 12.0) if self.is_meltdown else 2.0 * math.sin(self.angle * 4))
        core_color = (255, 240, 240) if self.is_meltdown else (180, 200, 230)
        draw_bresenham_circle(surface, cx, cy, core_r, core_color, filled=True)
        draw_bresenham_circle(surface, cx, cy, core_r + 6, (255, 255, 255), filled=False)


class SearchlightLighthouse:
    """
    Overhead sweeping searchlight lighthouse.
    Features rhythmic sweeping, thermal pulse charging, and lethal vaporizing detection.
    """
    def __init__(self, x: float, y: float, sweep_min_x: float, sweep_max_x: float, sweep_speed: float = 1.0, is_thermal: bool = False):
        self.x = x
        self.y = y
        self.sweep_min_x = sweep_min_x
        self.sweep_max_x = sweep_max_x
        self.sweep_speed = sweep_speed
        self.is_thermal = is_thermal
        self.time_t = random.uniform(0, 10)
        self.is_active = True
        self.target_floor_x = sweep_min_x
        self.beam_width = 85.0
        self.alert_timer = 0.0
        self.is_alerting = False
        self.thermal_timer = 0.0
        self.is_thermal_firing = False

    def update(self, dt: float):
        if not self.is_active:
            self.is_alerting = False
            self.is_thermal_firing = False
            return
        self.time_t += dt * self.sweep_speed
        sweep_range = (self.sweep_max_x - self.sweep_min_x) * 0.5
        mid_x = (self.sweep_min_x + self.sweep_max_x) * 0.5
        self.target_floor_x = mid_x + math.sin(self.time_t) * sweep_range

        # Thermal pulse cycle: every 4.0s, charges for 1.0s and discharges
        if self.is_thermal:
            self.thermal_timer = (self.thermal_timer + dt) % 4.5
            self.is_thermal_firing = (self.thermal_timer > 3.2)

    def check_worker_exposure(self, workers: List[Worker], cart: 'BlastShieldTrolley', dt: float) -> bool:
        if not self.is_active:
            self.is_alerting = False
            return False

        beam_left = self.target_floor_x - self.beam_width * 0.5
        beam_right = self.target_floor_x + self.beam_width * 0.5
        cart_blocks_beam = (cart.x - 15.0 <= self.target_floor_x <= cart.x + cart.width + 15.0)

        any_exposed = False
        for w in workers:
            if not w.is_linked:
                continue

            if beam_left <= w.x <= beam_right:
                is_sheltered = (cart.x - 12.0 <= w.x <= cart.x + cart.width + 12.0 and cart_blocks_beam)
                if not is_sheltered:
                    any_exposed = True
                    break

        if any_exposed:
            self.is_alerting = True
            # Thermal pulses incinerate in 0.15s, standard beams in 0.35s
            threshold = 0.15 if self.is_thermal_firing else 0.35
            self.alert_timer += dt
            if self.alert_timer >= threshold:
                return True
        else:
            self.alert_timer = max(0.0, self.alert_timer - dt * 2.5)
            self.is_alerting = False

        return False

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float, floor_y: float, cart: 'BlastShieldTrolley'):
        sx = self.x - cam_x
        sy = self.y - cam_y

        min_vis_x = min(sx - 30, self.target_floor_x - cam_x - self.beam_width * 0.5)
        max_vis_x = max(sx + 30, self.target_floor_x - cam_x + self.beam_width * 0.5)
        if max_vis_x < -50 or min_vis_x > 1330:
            return

        draw_bresenham_rect(surface, sx - 22, sy - 10, 44, 10, (140, 140, 150), filled=True)
        draw_bresenham_circle(surface, sx, sy + 6, 10, (200, 200, 210), filled=True)

        if not self.is_active:
            draw_bresenham_line(surface, sx - 10, sy + 18, sx + 10, sy + 18, (70, 70, 70), thickness=2)
            return

        dx = (self.target_floor_x - cam_x) - sx
        dy = (floor_y - cam_y) - sy
        dist = math.hypot(dx, dy)
        if dist > 0:
            nx = dx / dist
            ny = dy / dist
            draw_bresenham_line(surface, sx, sy + 6, sx + nx * 26, sy + 6 + ny * 26, (255, 255, 255), thickness=4)

        cart_intercepts = (cart.x - 15.0 <= self.target_floor_x <= cart.x + cart.width + 15.0)
        hit_y = cart.y if cart_intercepts else floor_y

        p_top_l = (sx - 12.0, sy + 8.0)
        p_top_r = (sx + 12.0, sy + 8.0)
        p_bot_r = (self.target_floor_x - cam_x + self.beam_width * 0.5, hit_y - cam_y)
        p_bot_l = (self.target_floor_x - cam_x - self.beam_width * 0.5, hit_y - cam_y)

        beam_poly = [p_top_l, p_top_r, p_bot_r, p_bot_l]

        if self.is_alerting or self.is_thermal_firing:
            glow_pulse = int(180 + 75 * math.sin(pygame.time.get_ticks() * 0.03))
            fill_col = (glow_pulse, 40, 40)
            edge_col = (255, 220, 220)
        else:
            fill_col = (38, 42, 54)
            edge_col = (210, 215, 230)

        draw_bresenham_polygon(surface, beam_poly, fill_col, filled=True)
        draw_bresenham_line(surface, p_top_l[0], p_top_l[1], p_bot_l[0], p_bot_l[1], edge_col, thickness=1)
        draw_bresenham_line(surface, p_top_r[0], p_top_r[1], p_bot_r[0], p_bot_r[1], edge_col, thickness=1)

        if cart_intercepts:
            spark_x = self.target_floor_x - cam_x
            spark_y = cart.y - cam_y
            draw_bresenham_circle(surface, spark_x, spark_y, 4, (255, 255, 200), filled=True)
            for _ in range(2):
                rx = spark_x + random.uniform(-15, 15)
                ry = spark_y - random.uniform(4, 16)
                draw_bresenham_line(surface, spark_x, spark_y, rx, ry, (255, 240, 150))


class BlastShieldTrolley:
    """
    Heavy Armored Blast-Shield Cart.
    Provides wide (160px) mobile cover from searchlights.
    Battering ram against the reactor security gate at X = 2280.
    """
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.width = 160.0
        self.height = 82.0
        self.vx = 0.0
        self.gate_breached = False
        font_hint = pygame.font.Font(None, 20)
        self.lbl = font_hint.render("ARMORED SHIELD", True, (220, 220, 220))

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def update(self, dt: float, min_x: float, max_x: float):
        self.x += self.vx * dt
        self.x = max(min_x, min(max_x, self.x))
        self.vx *= max(0.0, 1.0 - 6.0 * dt)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        sx = self.x - cam_x
        sy = self.y - cam_y
        if sx + self.width + 30 < -50 or sx - 30 > 1330:
            return

        fill_scanline_shadow(surface, sx - 10, sy + 30, self.width + 20, self.height)

        roof_poly = [
            (sx + 10.0, sy),
            (sx + self.width - 10.0, sy),
            (sx + self.width, sy + 18.0),
            (sx, sy + 18.0)
        ]
        draw_bresenham_polygon(surface, roof_poly, (65, 70, 85), filled=True)
        draw_bresenham_polygon(surface, roof_poly, (240, 240, 255), filled=False, thickness=2)

        draw_bresenham_rect(surface, sx, sy + 18, self.width, self.height - 24, (38, 42, 50), filled=True)
        draw_bresenham_rect(surface, sx, sy + 18, self.width, self.height - 24, (200, 205, 220), filled=False, thickness=2)

        draw_bresenham_line(surface, sx, sy + 18, sx + self.width, sy + self.height - 6, (130, 135, 145), thickness=1)
        draw_bresenham_line(surface, sx + self.width, sy + 18, sx, sy + self.height - 6, (130, 135, 145), thickness=1)

        draw_bresenham_line(surface, sx - 12, sy + 40, sx, sy + 40, (255, 255, 255), thickness=3)
        draw_bresenham_line(surface, sx + self.width, sy + 40, sx + self.width + 12, sy + 40, (255, 255, 255), thickness=3)

        for wx in (sx + 24, sx + self.width * 0.5, sx + self.width - 24):
            draw_bresenham_circle(surface, wx, sy + self.height, 10, (190, 195, 210), filled=True)
            draw_bresenham_circle(surface, wx, sy + self.height, 5, (50, 50, 60), filled=True)

        surface.blit(self.lbl, (sx + self.width * 0.5 - self.lbl.get_width() * 0.5, sy + 32))


class HydraulicRailBridge:
    """
    Hydraulic track drawbridge spanning the 180px maintenance pit gap (X = 1720 -> 1900).
    Requires at least 2 workers holding the counterweight pad at X = 1640 to stay lowered!
    """
    def __init__(self, x: float = 1720.0, y: float = 580.0, width: float = 180.0, height: float = 16.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_lowered = False
        self.angle_deg = -45.0  # Raised at -45 degrees initially

    def update(self, dt: float, is_weighted: bool):
        self.is_lowered = is_weighted
        target_angle = 0.0 if self.is_lowered else -45.0
        self.angle_deg += (target_angle - self.angle_deg) * min(1.0, 6.0 * dt)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        if self.x + self.width < cam_x - 50 or self.x > cam_x + 1330:
            return

        # Open maintenance chasm pit below
        draw_bresenham_rect(surface, self.x - cam_x, self.y - cam_y + 14, self.width, 140, (15, 16, 20), filled=True)
        # Hazard hazard stripes
        for x_h in range(int(self.x), int(self.x + self.width), 30):
            draw_bresenham_line(surface, x_h - cam_x, self.y - cam_y + 16, x_h + 15 - cam_x, self.y - cam_y + 35, (100, 100, 50), thickness=1)

        # Drawbridge deck using rotation matrix around hinge at (self.x, self.y)
        rot_mat = Matrix3x3.rotation_degrees(self.angle_deg)
        pivot_sx = self.x - cam_x
        pivot_sy = self.y - cam_y

        deck_local = [
            (0.0, 0.0),
            (self.width, 0.0),
            (self.width, self.height),
            (0.0, self.height)
        ]

        screen_deck = []
        for lx, ly in deck_local:
            rx, ry = rot_mat.transform_point(lx, ly)
            screen_deck.append((pivot_sx + rx, pivot_sy + ry))

        deck_color = (60, 65, 75) if self.is_lowered else (120, 90, 60)
        draw_bresenham_polygon(surface, screen_deck, deck_color, filled=True)
        draw_bresenham_polygon(surface, screen_deck, (220, 225, 240), filled=False, thickness=2)

        # Hinge gear
        draw_bresenham_circle(surface, pivot_sx, pivot_sy + 8, 8, (200, 200, 210), filled=True)


class HeavySecurityGate:
    """
    Massive reinforced reactor bulkhead gate at X = 2280.
    Breached by ramming with the armored cart.
    """
    def __init__(self, x: float = 2280.0, y: float = 420.0):
        self.x = x
        self.y = y
        self.width = 30.0
        self.height = 160.0
        self.is_open = False
        self.y_offset = 0.0

    def update(self, dt: float):
        if self.is_open and self.y_offset > -self.height:
            self.y_offset = max(-float(self.height), self.y_offset - 180.0 * dt)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        sx = self.x - cam_x
        if sx + self.width + 20 < -50 or sx - 20 > 1330:
            return

        sy = self.y - cam_y + self.y_offset

        draw_bresenham_rect(surface, self.x - cam_x - 6, self.y - cam_y - self.height, self.width + 12, self.height, (30, 32, 40), filled=True)
        draw_bresenham_rect(surface, sx, sy, self.width, self.height, (45, 48, 58), filled=True)
        draw_bresenham_rect(surface, sx, sy, self.width, self.height, (220, 220, 230), filled=False, thickness=3)

        for by in range(int(sy + 20), int(sy + self.height - 10), 25):
            draw_bresenham_line(surface, sx, by, sx + self.width, by, (160, 160, 170), thickness=2)

        beacon_col = (100, 255, 100) if self.is_open else (255, 60, 60)
        draw_bresenham_circle(surface, sx + self.width * 0.5, sy + 15, 5, beacon_col, filled=True)


class MomentumSwingingCrane:
    """
    Articulated momentum crane bridging the molten abyss over the core.
    Features true pendulum swing physics with angular acceleration, damping, and pump torque.
    Swings within easy, natural reach of the launch gantry perch (X = 2780).
    """
    def __init__(self, pivot_x: float = 2870.0, pivot_y: float = 60.0, arm_length: float = 330.0):
        self.pivot_x = pivot_x
        self.pivot_y = pivot_y
        self.arm_length = arm_length
        self.angle = -math.radians(12)  # Initial slight reach towards perch
        self.angular_vel = 0.0     # rad/s
        self.gravity = 9.81 * 85.0
        self.damping = 0.35
        self.max_angular_vel = 2.6
        self.is_active = True
        self.time_t = 0.0

    def apply_pump_torque(self, torque: float, dt: float):
        self.angular_vel += torque * dt
        self.angular_vel = max(-self.max_angular_vel, min(self.max_angular_vel, self.angular_vel))

    def update(self, dt: float, is_grabbed: bool = False):
        if not is_grabbed:
            # Ambient gentle sway reaching towards the perch edge
            self.time_t += dt * 1.8
            self.angle = -math.radians(12) + math.sin(self.time_t) * math.radians(16)
            self.angular_vel = 0.0
            return

        # Pendulum equation when held by player
        accel = -(self.gravity / self.arm_length) * math.sin(self.angle) - self.damping * self.angular_vel
        self.angular_vel += accel * dt
        self.angular_vel = max(-self.max_angular_vel, min(self.max_angular_vel, self.angular_vel))
        self.angle += self.angular_vel * dt
        self.angle = max(-math.radians(65), min(math.radians(65), self.angle))

    def get_hook_position(self) -> Tuple[float, float]:
        hook_x = self.pivot_x + self.arm_length * math.sin(self.angle)
        hook_y = self.pivot_y + self.arm_length * math.cos(self.angle)
        return (hook_x, hook_y)

    def get_tangential_velocity(self) -> Tuple[float, float]:
        vx = self.arm_length * self.angular_vel * math.cos(self.angle)
        vy = -self.arm_length * self.angular_vel * math.sin(self.angle)
        return (vx, vy)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        px = self.pivot_x - cam_x
        py = self.pivot_y - cam_y
        if px + self.arm_length + 100 < -50 or px - self.arm_length - 100 > 1330:
            return

        # Overhead gantry bridge truss
        draw_bresenham_line(surface, px - 180, py, px + 180, py, (140, 140, 150), thickness=4)
        draw_bresenham_circle(surface, px, py, 12, (220, 220, 230), filled=True)

        hook_x, hook_y = self.get_hook_position()
        hx = hook_x - cam_x
        hy = hook_y - cam_y

        # Articulated two-stage steel boom
        mid_x = (px + hx) * 0.5 + math.sin(self.angle * 0.5) * 20.0
        mid_y = (py + hy) * 0.5
        draw_bresenham_line(surface, px, py, mid_x, mid_y, (210, 215, 225), thickness=4)
        draw_bresenham_circle(surface, mid_x, mid_y, 8, (180, 180, 190), filled=True)
        draw_bresenham_line(surface, mid_x, mid_y, hx, hy, (230, 235, 245), thickness=3)

        # Hook ring
        draw_bresenham_circle(surface, hx, hy, 12, (255, 255, 255), filled=False)
        draw_bresenham_circle(surface, hx, hy, 6, (255, 255, 255), filled=True)


class FallingDebrisHazard:
    """
    Falling ceiling concrete slab hazard during the final collapse sprint.
    Rendered with rotation matrices and triggers collision knockback.
    """
    def __init__(self, x: float, delay: float):
        self.x = x
        self.y = -60.0
        self.target_y = 550.0
        self.delay = delay
        self.vy = 0.0
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(80, 180)
        self.landed = False
        self.size = 28.0

    def update(self, dt: float, boy_x: float):
        if self.delay > 0:
            self.delay -= dt
            return

        if not self.landed:
            self.vy += 850.0 * dt
            self.y += self.vy * dt
            self.angle += self.rot_speed * dt
            if self.y >= self.target_y:
                self.y = self.target_y
                self.landed = True

    def check_hit(self, boy_x: float, boy_y: float) -> bool:
        if not self.landed and self.y > 200.0:
            return abs(boy_x - self.x) < 25.0 and abs(boy_y - self.y) < 25.0
        return False

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        sx = self.x - cam_x
        if sx < -50 or sx > 1330:
            return

        if self.delay > 0:
            # Draw warning shadow on ground where slab will land
            draw_bresenham_circle(surface, self.x - cam_x, self.target_y - cam_y + 10, 14, (60, 20, 20), filled=False)
            return

        sy = self.y - cam_y

        rot_mat = Matrix3x3.rotation_degrees(self.angle)
        half = self.size * 0.5
        local_pts = [(-half, -half), (half, -half), (half, half), (-half, half)]
        screen_pts = []
        for lx, ly in local_pts:
            rx, ry = rot_mat.transform_point(lx, ly)
            screen_pts.append((sx + rx, sy + ry))

        draw_bresenham_polygon(surface, screen_pts, (80, 85, 95), filled=True)
        draw_bresenham_polygon(surface, screen_pts, (220, 220, 230), filled=False)


# =============================================================================
# Level 3 Main Class: TheCentralCoreLevel
# =============================================================================

class TheCentralCoreLevel:
    """
    Level 3: The Central Core (Hive Mind Overdrive) - Extended Challenging Edition
    """
    PHASE_1_INFILTRATION = "phase_1_infiltration"
    PHASE_2_HIVE_MIND = "phase_2_hive_mind"
    PHASE_3_MELTDOWN = "phase_3_meltdown"
    PHASE_4_BREACH = "phase_4_breach"

    def __init__(self):
        self.width = 4800
        self.height = 720
        self.wall_left = 0
        self.wall_right = 4800
        self.water_y = 9999.0

        # Spawning Boy
        self.spawn_x = 80.0
        self.spawn_y = 560.0
        self.boy = Boy(self.spawn_x, self.spawn_y)

        # Phase State Machine
        self.phase = self.PHASE_1_INFILTRATION

        # Zone 1: High Voltage & Moving Hoist
        self.voltage_grid = HighVoltageGrid(260, 560, 680, 24)
        self.moving_hoist = MovingCargoHoist(min_x=340.0, max_x=620.0, y=380.0, speed=95.0)
        self.overdrive_pod = OverdrivePod(960, 210)

        # Zone 2: Reactor Core, Swarm, Cart & Hydraulic Bridge
        self.reactor = ReactorCore(1950, 230)

        # The 6-Worker Proxy Squad
        self.workers: List[Worker] = [
            Worker(1140 + i * 36.0, 580.0, offset_idx=i)
            for i in range(6)
        ]

        # Defensive Sweeping Searchlights
        self.searchlight1 = SearchlightLighthouse(1480, 60, 1360, 1640, sweep_speed=1.2, is_thermal=False)
        self.searchlight2 = SearchlightLighthouse(2100, 60, 1960, 2240, sweep_speed=0.9, is_thermal=True)

        # Armored Shield Trolley
        self.blast_shield = BlastShieldTrolley(1240, 498)

        # Hydraulic Bridge spanning the 180px gap
        self.hydraulic_bridge = HydraulicRailBridge(1720, 580, 180, 16)
        self.bridge_weighted = False

        # Heavy Security Gate & Master Console
        self.security_gate = HeavySecurityGate(2280, 420)
        self.overload_console_x = 2400.0
        self.overload_lever_pulled = False

        # Zone 3: Molten Abyss & Momentum Crane (Pivot placed so rope hook sways right next to gantry perch)
        self.crane = MomentumSwingingCrane(pivot_x=2870.0, pivot_y=60.0, arm_length=330.0)
        self.crane_grabbed = False
        self.boost_ready = False

        # Zone 4: Collapsing Debris Corridor Obstacles
        self.falling_debris = [
            FallingDebrisHazard(3650.0, 1.2),
            FallingDebrisHazard(3920.0, 2.5),
            FallingDebrisHazard(4200.0, 3.8)
        ]
        self.breach_wall_blown = False
        self.whiteout_alpha = 0.0

        # Subsystems
        self.particle_system = CentralCoreParticles()
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.camera_shake = 0.0
        self.alarm_flash_timer = 0.0

        # Lives & Win/Loss
        self.MAX_LIVES = 3
        self.lives = self.MAX_LIVES
        self.game_over = False
        self.victory_achieved = False
        self.death_timer = 0.0
        self.respawn_delay = 1.4

        # Cached Font Prompts
        self.font_prompt = pygame.font.Font(None, 24)
        self.hint_v = self.font_prompt.render("HOLD VALVE [X=1640] TO LOWER BRIDGE", True, (255, 200, 100))
        self.hint_t = self.font_prompt.render("[HOLD E + D] PUSH SHIELD TO BLOCK LIGHT", True, (255, 255, 200))
        self.hint_b = self.font_prompt.render("PRESS SPACE TO BOOST!", True, (255, 255, 255))
        self.hint_c = self.font_prompt.render("PUMP [A / D] TO SWING, PRESS [SPACE] TO LAUNCH!", True, (255, 255, 200))
        self.hint_s = self.font_prompt.render("HOLD [S] TO CROUCH UNDER PIPE", True, (255, 255, 200))

    # -------------------------------------------------------------------------
    # Objectives & HUD
    # -------------------------------------------------------------------------

    @property
    def objective_text(self) -> str:
        if self.phase == self.PHASE_1_INFILTRATION:
            return "Time jumps onto the moving cargo hoist over the voltage grid to reach the Pod."
        elif self.phase == self.PHASE_2_HIVE_MIND:
            if not self.hydraulic_bridge.is_lowered and self.blast_shield.x >= 1680.0:
                return "Hold the Counterweight Valve [X=1640] with workers to lower the hydraulic bridge!"
            if not self.security_gate.is_open:
                return "Push the Armored Cart [E + D] to shelter from searchlights and ram the gate!"
            if not self.overload_lever_pulled:
                return "Gate breached! Pull the Master Overload Lever [E]."
            return "Overload initiated! Disengaging pod..."
        elif self.phase == self.PHASE_3_MELTDOWN:
            if self.crane_grabbed:
                return "Pump swing momentum [A / D] and release [SPACE] at forward apex to clear the abyss!"
            return "MELTDOWN! Boost with workers [SPACE], leap onto the crane hook, and swing across!"
        elif self.phase == self.PHASE_4_BREACH:
            return "TERMINAL COLLAPSE! Crouch-slide [S], vault rubble [SPACE], and sprint into the light!"
        return "Escape into the light."

    # -------------------------------------------------------------------------
    # Platform Geometry
    # -------------------------------------------------------------------------

    def get_solid_platforms(self) -> List[Tuple[float, float, float, float]]:
        platforms = [
            # Zone 1 Floor & Scaffolding
            (0, 560, 260, 160),
            (220, 470, 90, 16),
            (self.moving_hoist.x, self.moving_hoist.y, self.moving_hoist.width, self.moving_hoist.height),
            (680, 310, 120, 16),
            (860, 240, 220, 16),

            # Zone 2 Lower Floor Track 1 (before gap)
            (1080, 580, 640, 140),
            # Hive Floor Track 2 (after gap)
            (1900, 580, 640, 140),

            # Zone 3 Launch Gantry Perch (extends to X = 2780, right next to the swinging crane hook)
            (2560, 360, 220, 16),

            # Zone 3 Far Escape Ledge (after the abyss, X = 3120 -> 3360)
            (3120, 380, 240, 16),

            # Zone 4 Final Breach Corridor & Obstacles
            (3360, 560, 1440, 160),
            (4050, 520, 50, 40)  # Crushed steel rubble vault hurdle
        ]

        # Add hydraulic bridge deck if lowered
        if self.hydraulic_bridge.is_lowered:
            platforms.append((self.hydraulic_bridge.x, self.hydraulic_bridge.y, self.hydraulic_bridge.width, self.hydraulic_bridge.height))

        return platforms

    # -------------------------------------------------------------------------
    # Reset & Respawn
    # -------------------------------------------------------------------------

    def full_reset(self):
        self.phase = self.PHASE_1_INFILTRATION
        self.boy = Boy(self.spawn_x, self.spawn_y)
        self.overdrive_pod.x = self.overdrive_pod.start_x
        self.overdrive_pod.y = 210.0
        self.overdrive_pod.target_x = self.overdrive_pod.start_x
        self.overdrive_pod.target_y = 210.0
        self.overdrive_pod.is_occupied = False

        self.moving_hoist.x = self.moving_hoist.min_x
        self.moving_hoist.dir = 1

        self.reactor.is_meltdown = False
        self.reactor.angular_velocity = 0.6
        self.searchlight1.is_active = True
        self.searchlight2.is_active = True
        self.searchlight1.alert_timer = 0.0
        self.searchlight2.alert_timer = 0.0

        self.blast_shield.x = 1240.0
        self.blast_shield.vx = 0.0
        self.blast_shield.gate_breached = False

        self.hydraulic_bridge.is_lowered = False
        self.hydraulic_bridge.angle_deg = -45.0
        self.bridge_weighted = False

        self.security_gate.is_open = False
        self.security_gate.y_offset = 0.0

        self.overload_lever_pulled = False
        self.crane_grabbed = False
        self.crane.angle = 0.0
        self.crane.angular_vel = 0.0
        self.boost_ready = False
        self.breach_wall_blown = False
        self.whiteout_alpha = 0.0
        self.camera_shake = 0.0
        self.death_timer = 0.0
        self.victory_achieved = False

        for d in self.falling_debris:
            d.y = -60.0
            d.vy = 0.0
            d.landed = False

        for i, w in enumerate(self.workers):
            w.x = 1140.0 + i * 36.0
            w.y = 580.0
            w.vx = 0.0
            w.vy = 0.0
            w.facing = 1
            w.set_mind_control_active(False)

    # -------------------------------------------------------------------------
    # Update Loop
    # -------------------------------------------------------------------------

    def update(self, dt: float, input_handler: InputHandler):
        if self.game_over:
            return

        if not self.boy.is_alive:
            self.death_timer += dt
            if self.death_timer >= self.respawn_delay:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                    self.lives = 0
                else:
                    self.full_reset()
            return

        if self.camera_shake > 0:
            self.camera_shake = max(0.0, self.camera_shake - dt * 4.0)

        # Environment updates
        self.voltage_grid.update(dt)
        self.moving_hoist.update(dt)
        self.overdrive_pod.update(dt)
        self.reactor.update(dt)
        self.searchlight1.update(dt)
        self.searchlight2.update(dt)
        self.security_gate.update(dt)
        self.crane.update(dt, is_grabbed=self.crane_grabbed)
        self.particle_system.update(dt)

        # ---------------------------------------------------------------------
        # PHASE 1: INFILTRATION (Timing Moving Cargo Hoist & Voltage Surge)
        # ---------------------------------------------------------------------
        if self.phase == self.PHASE_1_INFILTRATION:
            if self.voltage_grid.is_touching(self.boy.x, self.boy.y):
                self.boy.is_alive = False
                self.particle_system.spawn(self.boy.x, self.boy.y, count=25, color=(240, 240, 255), speed_scale=2.5)

            # Check if boy is riding moving hoist
            if abs(self.boy.y - self.moving_hoist.y) < 8.0 and (self.moving_hoist.x - 5 <= self.boy.x <= self.moving_hoist.x + self.moving_hoist.width + 5):
                self.boy.x += self.moving_hoist.vx * dt

            # Interaction with Overdrive Pod
            if abs(self.boy.x - self.overdrive_pod.x) < 32.0 and abs(self.boy.y - 240.0) < 20.0:
                if input_handler.is_just_pressed(Action.INTERACT):
                    self.phase = self.PHASE_2_HIVE_MIND
                    self.overdrive_pod.is_occupied = True
                    self.boy.vx = 0.0
                    self.boy.vy = 0.0
                    self.boy.x = self.overdrive_pod.x
                    self.boy.y = self.overdrive_pod.y + 10.0
                    for w in self.workers:
                        w.set_mind_control_active(True)
                    self.particle_system.spawn(self.overdrive_pod.x, self.overdrive_pod.y, count=16, color=(200, 220, 255))

            self.boy.update(input_handler, dt, self.water_y, self.get_solid_platforms(), None, None, self.wall_left, self.wall_right)

        # ---------------------------------------------------------------------
        # PHASE 2: HIVE MIND (Hydraulic Bridge, Searchlight Pulses & Gate Ram)
        # ---------------------------------------------------------------------
        elif self.phase == self.PHASE_2_HIVE_MIND:
            self.boy.vx = 0.0
            self.boy.vy = 0.0
            self.boy.x = self.overdrive_pod.x
            self.boy.y = self.overdrive_pod.y + 10.0

            move_dir = 0
            if input_handler.is_down(Action.MOVE_LEFT):
                move_dir -= 1
            if input_handler.is_down(Action.MOVE_RIGHT):
                move_dir += 1

            is_interact = input_handler.is_down(Action.INTERACT)

            # Check if workers are on the hydraulic bridge counterweight pad (X in [1620, 1710])
            workers_on_valve = sum(1 for w in self.workers if 1620.0 <= w.x <= 1710.0 and abs(w.y - 580.0) < 20.0)
            self.bridge_weighted = (workers_on_valve >= 2 or self.blast_shield.x >= 1730.0)
            self.hydraulic_bridge.update(dt, self.bridge_weighted)

            # Workers pushing the Armored Shield Cart
            workers_near_cart = sum(
                1 for w in self.workers
                if (self.blast_shield.x - 45.0 <= w.x <= self.blast_shield.x + self.blast_shield.width + 45.0)
            )

            is_pushing_cart = (workers_near_cart >= 2 and is_interact and move_dir != 0)

            # Cart bounds: cannot cross track gap unless bridge is fully lowered!
            if not self.hydraulic_bridge.is_lowered and self.blast_shield.x < 1720.0:
                max_cart_x = 1710.0
            elif not self.security_gate.is_open:
                max_cart_x = 2270.0
            else:
                max_cart_x = 2380.0

            if is_pushing_cart:
                push_speed = 85.0
                self.blast_shield.vx = move_dir * push_speed
                if random.random() < 0.25:
                    self.particle_system.spawn(self.blast_shield.x + random.uniform(20, self.blast_shield.width - 20), 580.0, count=2, color=(160, 160, 170))

                # Ram security gate at X = 2270
                if self.blast_shield.x >= 2260.0 and not self.security_gate.is_open:
                    self.security_gate.is_open = True
                    self.blast_shield.gate_breached = True
                    self.camera_shake = 12.0
                    self.particle_system.spawn(2280.0, 520.0, count=40, color=(255, 230, 150), speed_scale=2.5)

            self.blast_shield.update(dt, 1080.0, max_cart_x)

            # Update workers
            for i, w in enumerate(self.workers):
                if is_pushing_cart:
                    target_slot_x = self.blast_shield.x + 18.0 + (i * 22.0)
                    dist_to_slot = target_slot_x - w.x
                    w.facing = 1 if move_dir > 0 else -1
                    w_vx = move_dir * 85.0 + dist_to_slot * 3.0
                    w.update(w_vx, dt, 580.0, 1080.0, 2500.0, is_pushing=True)
                else:
                    target_vx = move_dir * w.walk_speed
                    w.update(target_vx, dt, 580.0, 1080.0, 2500.0, is_pushing=False)

            # Searchlight exposure & lethal detection
            hit1 = self.searchlight1.check_worker_exposure(self.workers, self.blast_shield, dt)
            hit2 = self.searchlight2.check_worker_exposure(self.workers, self.blast_shield, dt)
            if hit1 or hit2:
                self.boy.is_alive = False
                for w in self.workers:
                    self.particle_system.spawn(w.x, w.y - 25, count=10, color=(255, 100, 100), speed_scale=2.0)

            # Pull Master Overload Lever at X = 2400
            if self.security_gate.is_open and not self.overload_lever_pulled:
                near_lever = sum(1 for w in self.workers if abs(w.x - self.overload_console_x) < 55.0)
                if near_lever >= 2 and input_handler.is_just_pressed(Action.INTERACT):
                    self.overload_lever_pulled = True
                    self.phase = self.PHASE_3_MELTDOWN
                    self.reactor.trigger_meltdown()
                    self.searchlight1.is_active = False
                    self.searchlight2.is_active = False
                    self.camera_shake = 14.0
                    self.particle_system.spawn(self.overload_console_x, 560.0, count=45, color=(255, 220, 100), speed_scale=3.0)

                    # Pod moves to X = 2380 and lowers Boy to ground
                    self.overdrive_pod.target_x = 2380.0
                    self.overdrive_pod.target_y = 530.0

        # ---------------------------------------------------------------------
        # PHASE 3: MELTDOWN (Pod Touchdown, Worker Boost & 550px Crane Abyss)
        # ---------------------------------------------------------------------
        elif self.phase == self.PHASE_3_MELTDOWN:
            self.alarm_flash_timer += dt * 5.0
            self.camera_shake = max(2.5, self.camera_shake)

            # Release Boy from pod onto feet
            if self.overdrive_pod.is_occupied:
                self.boy.x = self.overdrive_pod.x
                self.boy.y = self.overdrive_pod.y + 20.0
                if abs(self.overdrive_pod.x - 2380.0) < 30.0 and abs(self.overdrive_pod.y - 530.0) < 30.0:
                    self.overdrive_pod.is_occupied = False
                    self.boy.x = 2380.0
                    self.boy.y = 560.0
                    for w in self.workers:
                        w.set_mind_control_active(False)
                    self.particle_system.spawn(self.boy.x, self.boy.y, count=15, color=(255, 255, 255))

            # Workers rally to barrier at X = 2520 to form Launch Tower
            boost_wall_x = 2520.0
            for i, w in enumerate(self.workers):
                target_x = boost_wall_x - 40.0 + (i * 14.0)
                dist_x = target_x - w.x
                w.facing = 1
                w.vx = min(150.0, max(-150.0, dist_x * 4.0))
                w.x += w.vx * dt
                w.y = 580.0

            # Boost Launch onto Launch Gantry Perch (X = 2580, Y = 360)
            if not self.overdrive_pod.is_occupied:
                if 2450.0 <= self.boy.x <= 2560.0 and self.boy.y >= 540.0:
                    self.boost_ready = True
                    if input_handler.is_just_pressed(Action.JUMP) or input_handler.is_just_pressed(Action.INTERACT):
                        self.boy.vy = -720.0
                        self.boy.vx = 220.0
                        self.particle_system.spawn(self.boy.x, self.boy.y, count=25, color=(240, 240, 255), speed_scale=2.5)
                        self.camera_shake = 6.0
                else:
                    self.boost_ready = False

            # -----------------------------------------------------------------
            # MOLTEN ABYSS & MOMENTUM CRANE SWING
            # -----------------------------------------------------------------
            hook_x, hook_y = self.crane.get_hook_position()

            # Grab crane hook (generous, responsive grab radius)
            if not self.crane_grabbed and not self.overdrive_pod.is_occupied:
                if abs(self.boy.x - hook_x) < 80.0 and abs(self.boy.y - hook_y) < 90.0:
                    self.crane_grabbed = True
                    self.boy.vx = 0.0
                    self.boy.vy = 0.0

            if self.crane_grabbed:
                # Pump swing torque with A / D
                torque = 0.0
                if input_handler.is_down(Action.MOVE_LEFT):
                    torque -= 2.4
                if input_handler.is_down(Action.MOVE_RIGHT):
                    torque += 2.4
                self.crane.apply_pump_torque(torque, dt)

                self.boy.x = hook_x
                self.boy.y = hook_y + 35.0

                # Release / catapult on SPACE or INTERACT
                if input_handler.is_just_pressed(Action.JUMP) or input_handler.is_just_pressed(Action.INTERACT):
                    self.crane_grabbed = False
                    tan_vx, tan_vy = self.crane.get_tangential_velocity()
                    # Add forward launch impulse
                    forward_boost = 180.0 if tan_vx > 0 else 0.0
                    self.boy.vx = tan_vx + forward_boost
                    self.boy.vy = tan_vy - 160.0

            # Fall into Molten Core Pit (Instant Death)
            if not self.crane_grabbed and not self.overdrive_pod.is_occupied:
                if 2780.0 <= self.boy.x <= 3120.0 and self.boy.y >= 640.0:
                    self.boy.is_alive = False
                    self.particle_system.spawn(self.boy.x, self.boy.y, count=35, color=(255, 120, 50), speed_scale=3.0)

            if not self.crane_grabbed and not self.overdrive_pod.is_occupied:
                self.boy.update(input_handler, dt, self.water_y, self.get_solid_platforms(), None, None, self.wall_left, self.wall_right)

            # Reaching Far Escape Ledge (X >= 3120) advances to Phase 4
            if self.boy.x >= 3120.0:
                self.phase = self.PHASE_4_BREACH
                self.breach_wall_blown = True
                self.camera_shake = 16.0
                self.particle_system.spawn(4350.0, 500.0, count=50, color=(255, 255, 255), speed_scale=3.5)

        # ---------------------------------------------------------------------
        # PHASE 4: BREACH & TERMINAL ESCAPE COURSE (X = 3480 -> 4800)
        # ---------------------------------------------------------------------
        elif self.phase == self.PHASE_4_BREACH:
            self.boy.update(input_handler, dt, self.water_y, self.get_solid_platforms(), None, None, self.wall_left, self.wall_right)

            # Update falling debris blocks
            for d in self.falling_debris:
                d.update(dt, self.boy.x)
                if d.check_hit(self.boy.x, self.boy.y):
                    self.camera_shake = 10.0
                    self.boy.vx = -120.0
                    self.particle_system.spawn(self.boy.x, self.boy.y, count=12, color=(200, 200, 200))

            # Crouch-slide under low steam pipe at X = 3780
            pipe_x = 3780.0
            if abs(self.boy.x - pipe_x) < 20.0 and self.boy.y >= 540.0:
                if self.boy.state != BoyState.CROUCHING:
                    self.boy.x = pipe_x - 20.0
                    self.boy.vx = 0.0

            # Screen washes out into blazing sunlight past X = 4350
            if self.boy.x > 4350.0:
                self.whiteout_alpha = min(255.0, self.whiteout_alpha + dt * 140.0)

            # Final Climax Victory Condition
            if self.boy.x >= 4700.0 or self.whiteout_alpha >= 250.0:
                self.victory_achieved = True

        # ---------------------------------------------------------------------
        # Camera Tracking
        # ---------------------------------------------------------------------
        if self.phase == self.PHASE_2_HIVE_MIND:
            target_focus_x = self.blast_shield.x + self.blast_shield.width * 0.5
            target_focus_y = 560.0
        else:
            target_focus_x = self.boy.x
            target_focus_y = self.boy.y

        target_cam_x = target_focus_x - 1280.0 / 2.0
        target_cam_y = target_focus_y - 720.0 / 2.0 - 30.0
        target_cam_x = max(0.0, min(self.width - 1280.0, target_cam_x))
        target_cam_y = max(0.0, min(self.height - 720.0, target_cam_y))

        self.cam_x += (target_cam_x - self.cam_x) * 5.0 * dt
        self.cam_y += (target_cam_y - self.cam_y) * 5.0 * dt

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, unused_cam_x: float, unused_cam_y: float):
        shake_x = random.uniform(-self.camera_shake, self.camera_shake) if self.camera_shake > 0 else 0.0
        shake_y = random.uniform(-self.camera_shake, self.camera_shake) if self.camera_shake > 0 else 0.0
        cx = self.cam_x + shake_x
        cy = self.cam_y + shake_y

        # 1. Background Reactor Chamber Parallax Pillars
        bg_cam_x = cx * 0.25
        start_px = int((bg_cam_x // 380) * 380) - 380
        end_px = int(((bg_cam_x + 1280) // 380) * 380) + 380
        for px in range(start_px, end_px, 380):
            sx = px - bg_cam_x
            if -50 <= sx <= 1330:
                draw_bresenham_line(surface, sx, 0, sx, 720, (18, 20, 26), thickness=6)
                draw_bresenham_line(surface, sx + 80, 0, sx + 80, 720, (18, 20, 26), thickness=4)

        # 2. Central Resonant Reactor Core
        self.reactor.draw(surface, cx, cy)

        # 3. Environment Platforms & Floors
        platforms = self.get_solid_platforms()
        for px, py, pw, ph in platforms:
            sx = px - cx
            if sx + pw < -30 or sx > 1310:
                continue
            sy = py - cy
            draw_bresenham_rect(surface, sx, sy, pw, ph, (26, 28, 34), filled=True)
            draw_bresenham_line(surface, sx, sy, sx + pw, sy, (180, 185, 195), thickness=2)

        # 4. Zone 1: Voltage Grid & Scaffolding Ladders
        self.voltage_grid.draw(surface, cx, cy)
        if 220 - cx <= 1330 and 310 - cx >= -50:
            draw_bresenham_line(surface, 220 - cx, 470 - cy, 220 - cx, 560 - cy, (140, 140, 150), thickness=2)
            draw_bresenham_line(surface, 310 - cx, 470 - cy, 310 - cx, 560 - cy, (140, 140, 150), thickness=2)
            for ry in range(480, 560, 15):
                draw_bresenham_line(surface, 220 - cx, ry - cy, 310 - cx, ry - cy, (100, 100, 110), thickness=1)

        # Moving Cargo Hoist in Zone 1
        self.moving_hoist.draw(surface, cx, cy)

        # 5. Overdrive Mind-Control Pod
        self.overdrive_pod.draw(surface, cx, cy)

        # 6. Zone 2: Defensive Searchlights
        self.searchlight1.draw(surface, cx, cy, 580.0, self.blast_shield)
        self.searchlight2.draw(surface, cx, cy, 580.0, self.blast_shield)

        # 7. Hydraulic Rail Drawbridge
        self.hydraulic_bridge.draw(surface, cx, cy)
        # Counterweight valve pad at X = 1640
        if 1630 - cx <= 1330 and 1700 - cx >= -50:
            valve_col = (100, 255, 100) if self.bridge_weighted else (255, 80, 80)
            draw_bresenham_rect(surface, 1630 - cx, 574 - cy, 70, 8, (45, 48, 55), filled=True)
            draw_bresenham_rect(surface, 1630 - cx, 574 - cy, 70, 8, valve_col, filled=False, thickness=2)

        # 8. Heavy Security Bulkhead Gate & Master Console
        self.security_gate.draw(surface, cx, cy)
        mc_sx = self.overload_console_x - cx
        if -50 <= mc_sx <= 1330:
            mc_sy = 580.0 - cy
            draw_bresenham_rect(surface, mc_sx - 15, mc_sy - 35, 30, 35, (40, 42, 50), filled=True)
            draw_bresenham_rect(surface, mc_sx - 15, mc_sy - 35, 30, 35, (160, 165, 175), filled=False, thickness=2)
            lever_color = (255, 60, 60) if not self.overload_lever_pulled else (100, 255, 100)
            lever_top_y = mc_sy - (12 if self.overload_lever_pulled else 28)
            draw_bresenham_line(surface, mc_sx, mc_sy - 15, mc_sx + (10 if self.overload_lever_pulled else 0), lever_top_y, lever_color, thickness=3)

        # 9. Trolley Blast Shield
        self.blast_shield.draw(surface, cx, cy)

        # 10. 6-Worker Proxy Squad
        for w in self.workers:
            if -60 <= w.x - cx <= 1340:
                w.draw(surface, cx, cy)

        # 11. Molten Abyss Visuals (Zone 3)
        abyss_sx = 2780 - cx
        if -350 <= abyss_sx <= 1330:
            abyss_sy = 650 - cy
            # Molten superheated glowing pit
            draw_bresenham_rect(surface, abyss_sx, abyss_sy, 340, 70, (45, 15, 15), filled=True)
            for ax in range(int(abyss_sx), int(abyss_sx + 340), 30):
                draw_bresenham_line(surface, ax, abyss_sy + random.uniform(5, 20), ax + 20, abyss_sy + 5, (255, 140, 40), thickness=2)

        # 12. Momentum Swinging Crane
        self.crane.draw(surface, cx, cy)

        # 13. Zone 4 Kinetic Obstacles: Steam Pipe & Falling Debris
        if self.phase == self.PHASE_4_BREACH:
            # Low steam pipe at X = 3780 (Boy must crouch under)
            pipe_sx = 3780 - cx
            if -50 <= pipe_sx <= 1330:
                pipe_sy = 510 - cy
                draw_bresenham_line(surface, pipe_sx, 0 - cy, pipe_sx, pipe_sy, (160, 165, 175), thickness=6)
                draw_bresenham_line(surface, pipe_sx - 20, pipe_sy, pipe_sx + 20, pipe_sy, (200, 205, 215), thickness=4)
                # Steam venting
                if random.random() < 0.3:
                    self.particle_system.spawn(3780, 510, count=2, color=(200, 200, 210), speed_scale=0.5)

            # Falling debris slabs
            for d in self.falling_debris:
                d.draw(surface, cx, cy)

        # 14. Protagonist Boy Stickman
        if not (self.phase == self.PHASE_2_HIVE_MIND and self.overdrive_pod.is_occupied):
            self.boy.draw(surface, cx, cy)

        # 15. In-Game Contextual Floating Prompts
        if self.phase == self.PHASE_2_HIVE_MIND:
            if not self.hydraulic_bridge.is_lowered and self.blast_shield.x >= 1620.0:
                surface.blit(self.hint_v, self.hint_v.get_rect(center=(1665 - cx, 540 - cy)))
            elif not self.security_gate.is_open:
                cart_center_x = self.blast_shield.x + self.blast_shield.width * 0.5 - cx
                surface.blit(self.hint_t, self.hint_t.get_rect(center=(cart_center_x, self.blast_shield.y - cy - 25)))

        if self.phase == self.PHASE_3_MELTDOWN:
            if self.boost_ready:
                surface.blit(self.hint_b, self.hint_b.get_rect(center=(2520 - cx, 490 - cy)))
            elif self.crane_grabbed:
                surface.blit(self.hint_c, self.hint_c.get_rect(center=(self.boy.x - cx, self.boy.y - cy - 50)))

        if self.phase == self.PHASE_4_BREACH:
            if 3680 <= self.boy.x <= 3820:
                surface.blit(self.hint_s, self.hint_s.get_rect(center=(3780 - cx, 460 - cy)))

        # 16. Particles
        self.particle_system.draw(surface, cx, cy)

        # 17. Zone 4: Shattered Reinforced Wall & Daylight
        if self.breach_wall_blown:
            bw_sx = 4380.0 - cx
            bw_sy = 580.0 - cy
            draw_bresenham_line(surface, bw_sx, 0, bw_sx - 50, bw_sy, (255, 255, 255), thickness=4)
            draw_bresenham_line(surface, bw_sx, 0, bw_sx + 60, bw_sy, (200, 200, 200), thickness=2)

        # 18. Alarm Strobe Scanline Post-Effect during Meltdown
        if self.phase in (self.PHASE_3_MELTDOWN, self.PHASE_4_BREACH):
            strobe_intensity = int(35 * (0.5 + 0.5 * math.sin(self.alarm_flash_timer)))
            if strobe_intensity > 10:
                alarm_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
                alarm_surf.fill((255, 40, 40, strobe_intensity))
                surface.blit(alarm_surf, (0, 0))

        # 19. Radiant Whiteout Climax Transition
        if self.whiteout_alpha > 0:
            whiteout_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
            whiteout_surf.fill((255, 255, 255, int(min(255, self.whiteout_alpha))))
            surface.blit(whiteout_surf, (0, 0))
