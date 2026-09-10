"""
Worker Entity: The proxy minion stickmen coordinated via mind control.
Fulfills Rule 2 & Rule 4 of Development Skill:
Uses custom homogeneous transformation matrices for translation, rotation, and skeletal articulation.
Zero usage of built-in transformation functions.
Implements dormant state, psychic link activation halo, formation locomotion, and dual-actor 100 kg battery pushing.
"""

import math
from typing import List, Tuple, Optional
import pygame

from core.math2d import Matrix3x3
from core.drawing import draw_bresenham_line, draw_bresenham_circle
from core.input_handler import Action, InputHandler


class WorkerState:
    DORMANT = "dormant"
    ACTIVE = "active"
    PUSHING = "pushing"


class Worker:
    def __init__(self, x: float, y: float, offset_idx: int = 0):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.offset_idx = offset_idx  # 0 or 1 for twin formation
        self.state = WorkerState.DORMANT
        self.is_linked = False

        # Physics
        self.walk_speed = 135.0
        self.push_speed = 65.0
        self.gravity = 880.0
        self.push_capacity = 50.0  # kg (2 workers = 100 kg)

        # Animation & Joint angles (radians)
        self.anim_time = 0.0
        self.spine_angle = 0.25  # Dormant slumping
        self.left_hip_angle = 0.0
        self.left_knee_angle = 0.0
        self.right_hip_angle = 0.0
        self.right_knee_angle = 0.0
        self.left_shoulder_angle = 0.3
        self.left_elbow_angle = -0.1
        self.right_shoulder_angle = 0.3
        self.right_elbow_angle = -0.1
        self.body_angle = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - 12), int(self.y - 56), 24, 56)

    def set_mind_control_active(self, active: bool):
        self.is_linked = active
        if active:
            self.state = WorkerState.ACTIVE
            self.spine_angle = 0.05
        else:
            self.state = WorkerState.DORMANT
            self.vx = 0.0
            self.spine_angle = 0.35  # Slump head when dormant

    def update(
        self,
        target_vx: float,
        dt: float,
        floor_y: float,
        min_x: float,
        max_x: float,
        is_pushing: bool = False
    ):
        if not self.is_linked:
            # Dormant: static on ground
            self.vx = 0.0
            self.vy += self.gravity * dt
            self.y += self.vy * dt
            if self.y > floor_y:
                self.y = floor_y
                self.vy = 0.0
            self.compute_pose_dormant()
            return

        if is_pushing:
            self.state = WorkerState.PUSHING
            self.vx = target_vx
        else:
            self.state = WorkerState.ACTIVE
            self.vx += (target_vx - self.vx) * min(1.0, 10.0 * dt)

        if abs(self.vx) > 5:
            self.facing = 1 if self.vx > 0 else -1

        # Gravity
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Collision with ledge floor
        if self.y > floor_y:
            self.y = floor_y
            self.vy = 0.0

        # Silo bounds
        if self.x < min_x:
            self.x = min_x
            self.vx = 0.0
        elif self.x > max_x:
            self.x = max_x
            self.vx = 0.0

        # Animation pose
        if is_pushing:
            self.compute_pose_pushing(dt)
        elif abs(self.vx) > 10:
            self.anim_time += dt * 6.0
            self.compute_pose_walking(dt)
        else:
            self.anim_time += dt * 1.5
            self.compute_pose_idle(dt)

    def compute_pose_dormant(self):
        # Slumped forward, completely limp
        self.body_angle = 0.0
        self.spine_angle = 0.38
        self.left_shoulder_angle = 0.35
        self.left_elbow_angle = -0.15
        self.right_shoulder_angle = 0.35
        self.right_elbow_angle = -0.15
        self.left_hip_angle = 0.05
        self.left_knee_angle = 0.0
        self.right_hip_angle = -0.05
        self.right_knee_angle = 0.0

    def compute_pose_idle(self, dt: float):
        self.body_angle = 0.0
        self.spine_angle = 0.05
        self.left_shoulder_angle = 0.1
        self.left_elbow_angle = -0.05
        self.right_shoulder_angle = 0.1
        self.right_elbow_angle = -0.05
        self.left_hip_angle = 0.0
        self.left_knee_angle = 0.0
        self.right_hip_angle = 0.0
        self.right_knee_angle = 0.0

    def compute_pose_walking(self, dt: float):
        self.body_angle = 0.0
        self.spine_angle = 0.1
        phase = self.anim_time + self.offset_idx * 0.4
        self.left_hip_angle = math.sin(phase) * 0.5
        self.left_knee_angle = -abs(math.cos(phase)) * 0.4 if math.sin(phase) < 0 else 0.0
        self.right_hip_angle = -math.sin(phase) * 0.5
        self.right_knee_angle = -abs(math.cos(phase)) * 0.4 if -math.sin(phase) < 0 else 0.0

        self.left_shoulder_angle = -math.sin(phase) * 0.35
        self.left_elbow_angle = -0.1
        self.right_shoulder_angle = math.sin(phase) * 0.35
        self.right_elbow_angle = -0.1

    def compute_pose_pushing(self, dt: float):
        self.body_angle = 0.15 * self.facing
        self.spine_angle = 0.35
        # Arms extended forward against battery
        self.left_shoulder_angle = 1.4
        self.left_elbow_angle = -0.1
        self.right_shoulder_angle = 1.4
        self.right_elbow_angle = -0.1

        phase = self.anim_time * 1.2
        self.left_hip_angle = math.sin(phase) * 0.35
        self.left_knee_angle = -0.3
        self.right_hip_angle = -math.sin(phase) * 0.35
        self.right_knee_angle = -0.3

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        """Draws the worker stickman via 3x3 Homogeneous matrices and Bresenham algorithms."""
        screen_x = self.x - cam_x
        screen_y = self.y - cam_y

        m_trans = Matrix3x3.translation(screen_x, screen_y)
        m_rot = Matrix3x3.rotation(self.body_angle)
        m_scale = Matrix3x3.scale(float(self.facing), 1.0)
        base_mat = m_trans.multiply(m_rot).multiply(m_scale)

        # Grayscale palette for workers (slightly darker gray than the boy)
        color_worker = (175, 175, 175) if not self.is_linked else (225, 225, 225)
        color_head_fill = (15, 15, 15)

        # Pelvis root
        pelvis_local = (0.0, -28.0)
        pelvis_pt = base_mat.transform_point(pelvis_local[0], pelvis_local[1])

        # Spine matrix
        m_spine_trans = Matrix3x3.translation(pelvis_local[0], pelvis_local[1])
        m_spine_rot = Matrix3x3.rotation(self.spine_angle)
        spine_mat = base_mat.multiply(m_spine_trans).multiply(m_spine_rot)

        neck_pt = spine_mat.transform_point(0.0, -18.0)

        # Torso
        draw_bresenham_line(surface, pelvis_pt[0], pelvis_pt[1], neck_pt[0], neck_pt[1], color_worker, thickness=2)

        # Head circle
        head_center = spine_mat.transform_point(0.0, -26.0)
        head_radius = 6.0
        draw_bresenham_circle(surface, head_center[0], head_center[1], head_radius, color_head_fill, filled=True)
        draw_bresenham_circle(surface, head_center[0], head_center[1], head_radius, color_worker, filled=False)

        # Telepathic link halo (drawn when mind-controlled)
        if self.is_linked:
            halo_r = head_radius + 4.0
            draw_bresenham_circle(surface, head_center[0], head_center[1], halo_r, (250, 250, 250), filled=False)

        # Legs
        for side, hip_angle, knee_angle in [(-1, self.left_hip_angle, self.left_knee_angle),
                                            (1, self.right_hip_angle, self.right_knee_angle)]:
            hip_local = (side * 2.5, 0.0)
            m_hip_trans = Matrix3x3.translation(pelvis_local[0] + hip_local[0], pelvis_local[1] + hip_local[1])
            m_hip_rot = Matrix3x3.rotation(hip_angle)
            hip_mat = base_mat.multiply(m_hip_trans).multiply(m_hip_rot)

            hip_pt = hip_mat.transform_point(0.0, 0.0)
            knee_pt = hip_mat.transform_point(0.0, 14.0)

            m_knee_trans = Matrix3x3.translation(0.0, 14.0)
            m_knee_rot = Matrix3x3.rotation(knee_angle)
            knee_mat = hip_mat.multiply(m_knee_trans).multiply(m_knee_rot)
            foot_pt = knee_mat.transform_point(0.0, 14.0)

            draw_bresenham_line(surface, hip_pt[0], hip_pt[1], knee_pt[0], knee_pt[1], color_worker, thickness=2)
            draw_bresenham_line(surface, knee_pt[0], knee_pt[1], foot_pt[0], foot_pt[1], color_worker, thickness=2)

        # Arms
        for side, sh_angle, el_angle in [(-1, self.left_shoulder_angle, self.left_elbow_angle),
                                         (1, self.right_shoulder_angle, self.right_elbow_angle)]:
            sh_local = (side * 2.0, -16.0)
            m_sh_trans = Matrix3x3.translation(sh_local[0], sh_local[1])
            m_sh_rot = Matrix3x3.rotation(sh_angle)
            shoulder_mat = spine_mat.multiply(m_sh_trans).multiply(m_sh_rot)

            sh_pt = shoulder_mat.transform_point(0.0, 0.0)
            elbow_pt = shoulder_mat.transform_point(0.0, 11.0)

            m_el_trans = Matrix3x3.translation(0.0, 11.0)
            m_el_rot = Matrix3x3.rotation(el_angle)
            elbow_mat = shoulder_mat.multiply(m_el_trans).multiply(m_el_rot)
            hand_pt = elbow_mat.transform_point(0.0, 11.0)

            draw_bresenham_line(surface, sh_pt[0], sh_pt[1], elbow_pt[0], elbow_pt[1], color_worker, thickness=1)
            draw_bresenham_line(surface, elbow_pt[0], elbow_pt[1], hand_pt[0], hand_pt[1], color_worker, thickness=1)


class WorkerGroup:
    """
    Manages the twin workers as a coordinated proxy unit.
    Combined carry mass threshold >= 100 kg allows them to push the BatteryCore.
    """
    def __init__(self, spawn_x: float, spawn_y: float):
        self.workers = [
            Worker(spawn_x, spawn_y, offset_idx=0),
            Worker(spawn_x + 38.0, spawn_y, offset_idx=1)
        ]
        self.is_linked = False

    @property
    def center_x(self) -> float:
        return sum(w.x for w in self.workers) / len(self.workers)

    @property
    def center_y(self) -> float:
        return sum(w.y for w in self.workers) / len(self.workers)

    def set_mind_control(self, active: bool):
        self.is_linked = active
        for w in self.workers:
            w.set_mind_control_active(active)

    def update(
        self,
        input_handler: InputHandler,
        dt: float,
        battery,
        lift,
        floor_y: float,
        min_x: float,
        max_x: float
    ):
        if not self.is_linked:
            for w in self.workers:
                w.update(0.0, dt, floor_y, min_x, max_x, is_pushing=False)
            return

        # Player inputs routed to worker group
        move_dir = 0
        if input_handler.is_down(Action.MOVE_LEFT):
            move_dir -= 1
        if input_handler.is_down(Action.MOVE_RIGHT):
            move_dir += 1

        is_interact = input_handler.is_down(Action.INTERACT)

        # Check interaction with 100 kg battery
        near_battery_count = 0
        push_side = 0
        for w in self.workers:
            # Distance to battery
            dist_to_left = abs(w.x - battery.x)
            dist_to_right = abs(w.x - (battery.x + battery.width))
            if dist_to_left < 30.0:
                near_battery_count += 1
                push_side = 1  # Pushing rightward
            elif dist_to_right < 30.0:
                near_battery_count += 1
                push_side = -1  # Pushing leftward

        # Combined mass requirement: both workers (2) must engage to push 100 kg
        is_pushing_battery = (near_battery_count == 2 and is_interact and move_dir == push_side and not battery.is_on_lift)

        for i, w in enumerate(self.workers):
            target_vx = move_dir * (w.push_speed if is_pushing_battery else w.walk_speed)
            w.update(target_vx, dt, floor_y, min_x, max_x, is_pushing=is_pushing_battery)

        # Maintain minimum separation between workers
        w1, w2 = self.workers
        spacing = 35.0
        if w1.x > w2.x:
            w1, w2 = w2, w1
        if abs(w2.x - w1.x) < 25.0:
            w1.x -= 10.0 * dt
            w2.x += 10.0 * dt

        # Apply push force to battery
        if is_pushing_battery:
            push_force = move_dir * 80.0
            battery.vx = push_force
            # Check if battery has moved onto freight lift platform
            if lift.rect.inflate(10, 10).colliderect(battery.rect):
                # Lock battery onto lift!
                battery.is_on_lift = True
                lift.battery_installed = True
                battery.x = lift.x + 20.0
                battery.y = lift.y - battery.height + 2.0

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        for w in self.workers:
            w.draw(surface, cam_x, cam_y)
