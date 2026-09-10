"""
Boy Entity: The main protagonist stickman figure.
Fulfills Rule 2 & Rule 4 of Development Skill:
Uses custom homogeneous transformation matrices for translation, rotation, and hierarchical skeletal articulation.
Zero usage of built-in transformation functions.
Implements locomotion, water drag, crouch, mantle, crate dragging, cable swinging, and mind-control trance states.
"""

import math
from typing import Optional, Tuple
import pygame

from core.math2d import Matrix3x3
from core.drawing import draw_bresenham_line, draw_bresenham_circle
from core.input_handler import Action, InputHandler


class BoyState:
    GROUNDED = "grounded"
    AIRBORNE = "airborne"
    SWIMMING = "swimming"
    WADING = "wading"
    CROUCHING = "crouching"
    DRAGGING = "dragging"
    SWINGING = "swinging"
    MIND_CONTROL = "mind_control"
    DEAD = "dead"


class Boy:
    def __init__(self, x: float, y: float):
        # World coordinates (ground point between feet)
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1  # 1 for right, -1 for left
        self.body_angle = 0.0  # Angle in radians (for rope swinging / leaning)

        # State
        self.state = BoyState.AIRBORNE
        self.is_alive = True
        self.is_grounded = False
        self.in_water = False
        self.water_depth = 0.0  # Depth submerged in water

        # Kinematic / animation timers
        self.anim_time = 0.0
        self.dragged_crate = None
        self.swinging_cable = None
        self.cable_length_grabbed = 0.0
        self.cable_grab_cooldown = 0.0
        self.helmet_node = None

        # Dimensions & physics constants
        self.height_standing = 56.0
        self.height_crouching = 32.0
        self.width = 20.0
        self.walk_speed = 175.0
        self.sprint_speed = 280.0
        self.wade_speed = 95.0
        self.drag_speed = 70.0
        self.jump_impulse = -435.0
        self.gravity = 880.0

        # Limb rotation angles (in radians relative to parent joint)
        self.left_hip_angle = 0.0
        self.left_knee_angle = 0.0
        self.right_hip_angle = 0.0
        self.right_knee_angle = 0.0
        self.left_shoulder_angle = 0.0
        self.left_elbow_angle = 0.0
        self.right_shoulder_angle = 0.0
        self.right_elbow_angle = 0.0
        self.spine_angle = 0.0

    @property
    def current_height(self) -> float:
        if self.state == BoyState.CROUCHING:
            return self.height_crouching
        return self.height_standing

    @property
    def bounding_box(self) -> pygame.Rect:
        h = self.current_height
        return pygame.Rect(int(self.x - self.width / 2), int(self.y - h), int(self.width), int(h))

    def update_locomotion(
        self,
        input_handler: InputHandler,
        dt: float,
        water_y: float,
        platforms: list,
        silo_left: float,
        silo_right: float
    ):
        """Standard locomotion, water drag, crouch, and ground collisions."""
        # Check water submergence
        if self.y > water_y:
            self.in_water = True
            self.water_depth = self.y - water_y
        else:
            self.in_water = False
            self.water_depth = 0.0

        # Horizontal input
        move_dir = 0
        if input_handler.is_down(Action.MOVE_LEFT):
            move_dir -= 1
        if input_handler.is_down(Action.MOVE_RIGHT):
            move_dir += 1

        if move_dir != 0:
            self.facing = move_dir

        is_crouching = input_handler.is_down(Action.CROUCH) and self.is_grounded
        is_sprinting = input_handler.is_down(Action.SPRINT) and not self.in_water and not is_crouching and self.is_grounded

        # Speed calculation based on environment / water drag
        if self.in_water:
            # Water drag limits movement; sprinting prohibited
            speed = self.wade_speed
        elif is_crouching:
            speed = self.walk_speed * 0.5
        elif is_sprinting:
            speed = self.sprint_speed
        else:
            speed = self.walk_speed

        # Acceleration and movement
        target_vx = move_dir * speed
        accel = 12.0 if self.is_grounded else 6.0
        self.vx += (target_vx - self.vx) * min(1.0, accel * dt)

        # Jump mechanics - strictly grounded only (prevents infinite air jumping)
        if input_handler.is_just_pressed(Action.JUMP) and self.is_grounded and not is_crouching:
            # Full launch impulse from floor or water
            self.vy = self.jump_impulse
            self.is_grounded = False
            self.state = BoyState.AIRBORNE

        # Apply gravity only when airborne
        if not self.is_grounded:
            if self.in_water:
                # Damped buoyancy in knee-deep water
                self.vy += (self.gravity * 0.5) * dt
                self.vy *= (1.0 - 4.0 * dt)
            else:
                self.vy += self.gravity * dt

        # Custom Translation integration (Rule 2)
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Silo horizontal bounds
        half_w = self.width / 2
        if self.x - half_w < silo_left:
            self.x = silo_left + half_w
            self.vx = 0.0
        elif self.x + half_w > silo_right:
            self.x = silo_right - half_w
            self.vx = 0.0

        # Platform collisions (one-way, solid floors, and ledge mantle)
        was_grounded = False
        foot_y = self.y
        for plat in platforms:
            plat_left, plat_top, plat_w, plat_h = plat
            plat_right = plat_left + plat_w

            if plat_left - 14.0 <= self.x <= plat_right + 14.0:
                # Standard landing on top of platform
                if self.vy >= 0 and (foot_y - self.vy * dt - 6.0) <= plat_top + 12.0 and foot_y >= plat_top - 6.0:
                    self.y = plat_top
                    self.vy = 0.0
                    was_grounded = True
                    break
                # Ledge mantle assist (hands reaching top rim of crate or elevated platform)
                elif plat_h <= 50.0 and (-12.0 <= foot_y - plat_top <= 54.0) and self.vy > -320.0:
                    self.y = plat_top
                    self.vy = 0.0
                    was_grounded = True
                    if self.x < plat_left:
                        self.x = plat_left + 8.0
                    elif self.x > plat_right:
                        self.x = plat_right - 8.0
                    break

        self.is_grounded = was_grounded
        if not self.is_grounded:
            self.state = BoyState.AIRBORNE
        else:
            self.cable_grab_cooldown = 0.0
            if is_crouching:
                self.state = BoyState.CROUCHING
            elif self.in_water:
                self.state = BoyState.WADING
            else:
                self.state = BoyState.GROUNDED

        # Advance locomotion animation cycle
        if abs(self.vx) > 10 and self.state in (BoyState.GROUNDED, BoyState.WADING):
            self.anim_time += dt * (abs(self.vx) / 20.0)
        else:
            self.anim_time += dt * 2.0

    def update(
        self,
        input_handler: InputHandler,
        dt: float,
        water_y: float,
        platforms: list,
        crate,
        cable,
        silo_left: float,
        silo_right: float
    ):
        if not self.is_alive:
            self.state = BoyState.DEAD
            return

        # Mind-control trance state
        if self.state == BoyState.MIND_CONTROL:
            self.vx = 0.0
            self.vy = 0.0
            # Hang limply suspended in helmet
            self.compute_pose_trance(dt)
            return

        # Cable swinging state
        if self.state == BoyState.SWINGING and cable is not None:
            self.update_cable_swing(input_handler, dt, cable)
            return

        # Crate dragging state
        if self.state == BoyState.DRAGGING and crate is not None:
            self.update_crate_dragging(input_handler, dt, crate, water_y, platforms, silo_left, silo_right)
            return

        if self.cable_grab_cooldown > 0.0:
            self.cable_grab_cooldown -= dt

        # Check for cable grab initiation
        if cable is not None and self.state == BoyState.AIRBORNE and self.cable_grab_cooldown <= 0.0:
            tip_x, tip_y = cable.get_tip_position()
            dist_sq = (self.x - tip_x) ** 2 + ((self.y - 30.0) - tip_y) ** 2
            # Responsive grab: when holding E, holding Jump, or airborne contact near hook
            wants_grab = input_handler.is_down(Action.INTERACT) or input_handler.is_down(Action.JUMP) or (dist_sq < 42.0 ** 2)
            if wants_grab and dist_sq < 75.0 ** 2:
                self.state = BoyState.SWINGING
                self.swinging_cable = cable
                self.vx = 0.0
                self.vy = 0.0
                return

        # Check for crate grab initiation
        if crate is not None and input_handler.is_down(Action.INTERACT):
            crate_rect = crate.rect
            dist_to_crate = abs(self.x - (crate.x + crate.width / 2))
            if dist_to_crate < 65.0 and abs(self.y - (crate.y + crate.height)) < 40.0:
                self.state = BoyState.DRAGGING
                self.dragged_crate = crate
                crate.is_grabbed = True
                crate.grabbed_by = self
                return

        # Standard locomotion
        self.update_locomotion(input_handler, dt, water_y, platforms, silo_left, silo_right)
        self.compute_pose_locomotion(dt)

    def update_cable_swing(self, input_handler: InputHandler, dt: float, cable):
        """Swings on the dynamic rope/cable using pendulum kinematics."""
        # Release input
        if input_handler.is_just_pressed(Action.DISENGAGE) or input_handler.is_just_pressed(Action.JUMP):
            tip_x, tip_y = cable.get_tip_position()
            feet_y = tip_y + 40.0
            catwalk_y = 720.0
            catwalk_right = 950.0

            # Forward swing release (towards the upper deck / catwalk)
            if cable.angular_vel > 0 or cable.angle > 0.05:
                height_diff = feet_y - catwalk_y
                if height_diff > 20.0:
                    needed_vy = -math.sqrt(2.0 * 980.0 * (height_diff + 24.0))
                    launch_vy = max(-820.0, min(-340.0, needed_vy))
                elif height_diff > -10.0:
                    launch_vy = -220.0
                else:
                    launch_vy = -80.0

                # Gentle forward speed carrying boy onto catwalk
                launch_vx = max(110.0, min(190.0, (880.0 - tip_x) * 0.35))
            else:
                # Backward swing release (back toward flooded ground)
                launch_vx = min(-120.0, cable.get_tangential_velocity_x())
                launch_vy = -280.0

            self.state = BoyState.AIRBORNE
            self.vx = launch_vx
            self.vy = launch_vy
            self.body_angle = 0.0
            self.swinging_cable = None
            self.cable_grab_cooldown = 1.0  # Cooldown prevents mid-flight re-grab
            return

        # Pumping swing momentum with Move Left / Move Right
        pump_torque = 0.0
        if input_handler.is_down(Action.MOVE_LEFT):
            pump_torque -= 5.5
            self.facing = -1
        elif input_handler.is_down(Action.MOVE_RIGHT):
            pump_torque += 5.5
            self.facing = 1

        cable.apply_swing_torque(pump_torque, dt)

        # Attach boy's hands to cable tip
        tip_x, tip_y = cable.get_tip_position()
        self.x = tip_x
        self.y = tip_y + 40.0  # Feet hang 40px below hands
        self.body_angle = cable.angle  # Body tilts with the rope rotation (Rule 4)

        self.compute_pose_swinging(cable.angle)

    def update_crate_dragging(
        self,
        input_handler: InputHandler,
        dt: float,
        crate,
        water_y: float,
        platforms: list,
        silo_left: float,
        silo_right: float
    ):
        """Dragging the buoyant crate through water."""
        if not input_handler.is_down(Action.INTERACT):
            # Release crate
            self.state = BoyState.GROUNDED
            if self.dragged_crate:
                self.dragged_crate.is_grabbed = False
                self.dragged_crate.grabbed_by = None
                self.dragged_crate = None
            return

        move_dir = 0
        if input_handler.is_down(Action.MOVE_LEFT):
            move_dir -= 1
        if input_handler.is_down(Action.MOVE_RIGHT):
            move_dir += 1

        if move_dir != 0:
            self.facing = move_dir

        # Drag speed
        self.vx = move_dir * self.drag_speed
        self.x += self.vx * dt
        crate.x += self.vx * dt

        # Maintain connection distance
        if self.facing == 1:
            crate.x = self.x + 10
        else:
            crate.x = self.x - crate.width - 10

        self.compute_pose_dragging(dt)

    # -------------------------------------------------------------------------
    # Custom 3x3 Homogeneous Matrix Skeletal Poses (Rule 2 & Rule 4)
    # -------------------------------------------------------------------------

    def compute_pose_locomotion(self, dt: float):
        self.body_angle = 0.0
        if self.state == BoyState.CROUCHING:
            self.spine_angle = 0.35
            self.left_hip_angle = 1.0
            self.left_knee_angle = -1.2
            self.right_hip_angle = 1.0
            self.right_knee_angle = -1.2
            self.left_shoulder_angle = 0.6
            self.left_elbow_angle = -0.5
            self.right_shoulder_angle = 0.6
            self.right_elbow_angle = -0.5
        elif self.state == BoyState.AIRBORNE:
            self.spine_angle = 0.05
            self.left_hip_angle = 0.4
            self.left_knee_angle = -0.6
            self.right_hip_angle = -0.3
            self.right_knee_angle = -0.4
            self.left_shoulder_angle = -1.2
            self.left_elbow_angle = -0.3
            self.right_shoulder_angle = -1.2
            self.right_elbow_angle = -0.3
        elif abs(self.vx) > 10:
            # Walking / running sinusoidal cycle
            phase = self.anim_time
            leg_amp = 0.65 if abs(self.vx) > 150 else 0.45
            self.left_hip_angle = math.sin(phase) * leg_amp
            self.left_knee_angle = -abs(math.cos(phase)) * 0.5 if math.sin(phase) < 0 else 0.0
            self.right_hip_angle = -math.sin(phase) * leg_amp
            self.right_knee_angle = -abs(math.cos(phase)) * 0.5 if -math.sin(phase) < 0 else 0.0

            arm_amp = 0.5
            self.left_shoulder_angle = -math.sin(phase) * arm_amp
            self.left_elbow_angle = -0.2
            self.right_shoulder_angle = math.sin(phase) * arm_amp
            self.right_elbow_angle = -0.2
            self.spine_angle = 0.15  # Lean forward slightly when running
        else:
            # Idle breathing pose
            t = self.anim_time * 0.5
            self.spine_angle = math.sin(t) * 0.03
            self.left_hip_angle = 0.05
            self.left_knee_angle = 0.0
            self.right_hip_angle = -0.05
            self.right_knee_angle = 0.0
            self.left_shoulder_angle = 0.1
            self.left_elbow_angle = -0.1
            self.right_shoulder_angle = 0.1
            self.right_elbow_angle = -0.1

    def compute_pose_swinging(self, cable_angle: float):
        self.body_angle = cable_angle
        self.spine_angle = 0.0
        # Arms raised overhead gripping cable
        self.left_shoulder_angle = -2.7
        self.left_elbow_angle = -0.1
        self.right_shoulder_angle = -2.7
        self.right_elbow_angle = -0.1
        # Legs bent backwards with wind
        self.left_hip_angle = 0.4
        self.left_knee_angle = -0.6
        self.right_hip_angle = 0.3
        self.right_knee_angle = -0.5

    def compute_pose_dragging(self, dt: float):
        self.body_angle = -0.2 if self.facing == 1 else 0.2
        self.spine_angle = 0.3
        # Arms extended forward holding crate
        self.left_shoulder_angle = 1.3
        self.left_elbow_angle = -0.1
        self.right_shoulder_angle = 1.3
        self.right_elbow_angle = -0.1

        phase = self.anim_time * 1.5
        self.left_hip_angle = math.sin(phase) * 0.4
        self.left_knee_angle = -abs(math.cos(phase)) * 0.4 if math.sin(phase) < 0 else 0.0
        self.right_hip_angle = -math.sin(phase) * 0.4
        self.right_knee_angle = -abs(math.cos(phase)) * 0.4 if -math.sin(phase) < 0 else 0.0

    def compute_pose_trance(self, dt: float):
        self.body_angle = 0.0
        # Slumped head, limp hanging body
        self.spine_angle = 0.25
        self.left_shoulder_angle = 0.2
        self.left_elbow_angle = -0.1
        self.right_shoulder_angle = 0.2
        self.right_elbow_angle = -0.1
        self.left_hip_angle = 0.1
        self.left_knee_angle = -0.2
        self.right_hip_angle = 0.05
        self.right_knee_angle = -0.1

    # -------------------------------------------------------------------------
    # Render Stickman via Bresenham Algorithms and 3x3 Matrices
    # -------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        """
        Renders the boy stickman using basic monochrome geometric shapes:
        - Head: Bresenham circle
        - Spine & Limbs: Bresenham lines
        - Joint hierarchy: 3x3 Homogeneous transformation matrices
        """
        # Screen position
        screen_x = self.x - cam_x
        screen_y = self.y - cam_y

        # Base world matrix: Translation to (screen_x, screen_y), Rotation by body_angle, Facing scale
        m_trans = Matrix3x3.translation(screen_x, screen_y)
        m_rot = Matrix3x3.rotation(self.body_angle)
        m_scale = Matrix3x3.scale(float(self.facing), 1.0)
        base_mat = m_trans.multiply(m_rot).multiply(m_scale)

        # Monochrome palette: crisp white stickman lines (255, 255, 255)
        color_boy = (245, 245, 245)
        color_head_fill = (20, 20, 20)

        # Pelvis root point in local space (0, -28)
        pelvis_local = (0.0, -28.0)
        pelvis_pt = base_mat.transform_point(pelvis_local[0], pelvis_local[1])

        # Spine matrix
        m_spine_trans = Matrix3x3.translation(pelvis_local[0], pelvis_local[1])
        m_spine_rot = Matrix3x3.rotation(self.spine_angle)
        spine_mat = base_mat.multiply(m_spine_trans).multiply(m_spine_rot)

        # Neck point (18 units above pelvis along spine)
        neck_pt = spine_mat.transform_point(0.0, -18.0)

        # Draw Torso (Bresenham line)
        draw_bresenham_line(surface, pelvis_pt[0], pelvis_pt[1], neck_pt[0], neck_pt[1], color_boy, thickness=2)

        # Head (circle at 8 units above neck)
        head_center = spine_mat.transform_point(0.0, -26.0)
        head_radius = 6.5
        draw_bresenham_circle(surface, head_center[0], head_center[1], head_radius, color_head_fill, filled=True)
        draw_bresenham_circle(surface, head_center[0], head_center[1], head_radius, color_boy, filled=False)

        # Legs (Left & Right Hips from pelvis)
        for side, hip_angle, knee_angle in [(-1, self.left_hip_angle, self.left_knee_angle),
                                            (1, self.right_hip_angle, self.right_knee_angle)]:
            hip_local = (side * 2.5, 0.0)
            m_hip_trans = Matrix3x3.translation(pelvis_local[0] + hip_local[0], pelvis_local[1] + hip_local[1])
            m_hip_rot = Matrix3x3.rotation(hip_angle)
            hip_mat = base_mat.multiply(m_hip_trans).multiply(m_hip_rot)

            hip_pt = hip_mat.transform_point(0.0, 0.0)
            knee_pt = hip_mat.transform_point(0.0, 14.0)

            # Calf matrix
            m_knee_trans = Matrix3x3.translation(0.0, 14.0)
            m_knee_rot = Matrix3x3.rotation(knee_angle)
            knee_mat = hip_mat.multiply(m_knee_trans).multiply(m_knee_rot)
            foot_pt = knee_mat.transform_point(0.0, 14.0)

            draw_bresenham_line(surface, hip_pt[0], hip_pt[1], knee_pt[0], knee_pt[1], color_boy, thickness=2)
            draw_bresenham_line(surface, knee_pt[0], knee_pt[1], foot_pt[0], foot_pt[1], color_boy, thickness=2)

        # Arms (Left & Right Shoulders from neck)
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

            draw_bresenham_line(surface, sh_pt[0], sh_pt[1], elbow_pt[0], elbow_pt[1], color_boy, thickness=1)
            draw_bresenham_line(surface, elbow_pt[0], elbow_pt[1], hand_pt[0], hand_pt[1], color_boy, thickness=1)
