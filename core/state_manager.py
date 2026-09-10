"""
State Manager: Routes inputs to Boy or Proxy Minion Workers.
Manages level progression phases, pawn swapping via Mind-Control Helmet,
checkpoint respawning, and camera focus target.
"""

from enum import Enum, auto
from typing import Tuple, Optional
import pygame

from core.input_handler import Action, InputHandler
from entities.boy import Boy, BoyState
from levels.silo_level import SiloLevel, FreightLiftState


class ControllerMode(Enum):
    BOY = auto()
    MIND_CONTROL_WORKERS = auto()


class LevelPhase(Enum):
    PHASE_1_CRATE = 1
    PHASE_2_SEARCHLIGHT = 2
    PHASE_3_BATTERY = 3
    PHASE_4_LIFT = 4
    VICTORY = 5


class StateManager:
    def __init__(self, boy: Boy, level: SiloLevel):
        self.boy = boy
        self.level = level
        self.controller = ControllerMode.BOY
        self.phase = LevelPhase.PHASE_1_CRATE

        # Camera tracking targets
        self.cam_x = 0.0
        self.cam_y = 600.0
        self.target_cam_x = 0.0
        self.target_cam_y = 600.0

        # Death / Respawn timer
        self.death_timer = 0.0
        self.respawn_delay = 1.2

        # Victory state
        self.victory_achieved = False
        self.victory_timer = 0.0

        # Objective hint string
        self.objective_text = "Drop into water. Drag crate under power cable to reach catwalk."

    def update(self, input_handler: InputHandler, dt: float):
        # Handle death and checkpoint reload
        if not self.boy.is_alive:
            self.death_timer += dt
            if self.death_timer >= self.respawn_delay:
                self.death_timer = 0.0
                self.level.reset_checkpoint_phase2(self.boy)
            return

        # ---------------------------------------------------------------------
        # Phase Detection & Objective Updates
        # ---------------------------------------------------------------------
        if self.phase == LevelPhase.PHASE_1_CRATE:
            if self.boy.y <= self.level.catwalk_y + 10.0 and self.boy.x >= 350.0:
                self.phase = LevelPhase.PHASE_2_SEARCHLIGHT
                self.objective_text = "Cross catwalk. Crouch behind locker in shadow to evade searchlight."

        elif self.phase == LevelPhase.PHASE_2_SEARCHLIGHT:
            if self.boy.x >= 950.0:  # Reached generator alcove
                self.phase = LevelPhase.PHASE_3_BATTERY
                self.objective_text = "Jump into Mind-Control Helmet to activate proxy workers."

        elif self.phase == LevelPhase.PHASE_3_BATTERY:
            if self.level.battery.is_on_lift and self.controller == ControllerMode.BOY:
                self.phase = LevelPhase.PHASE_4_LIFT
                self.objective_text = "Pull Master Lever to lower lift. Ride lift with battery to roof hatch."

        elif self.phase == LevelPhase.PHASE_4_LIFT:
            if self.level.freight_lift.state == FreightLiftState.AT_ROOF:
                self.objective_text = "Force open the rusted ceiling hatch (Press E / Interact) to escape!"

        # ---------------------------------------------------------------------
        # Input Routing & Pawn Swapping (Rule 1 & Spec Phase 3)
        # ---------------------------------------------------------------------
        if self.controller == ControllerMode.BOY:
            # Route inputs to Boy
            self.boy.update(
                input_handler,
                dt,
                self.level.water_y,
                self.level.get_solid_platforms(),
                self.level.crate,
                self.level.power_cable,
                self.level.wall_left,
                self.level.wall_right
            )

            # Check Mind-Control Helmet interaction (Entering Helmet)
            if self.level.helmet.check_interaction(self.boy):
                self.enter_mind_control()

            # Check Master Lever pull in alcove
            if self.level.master_lever.check_range(self.boy) and input_handler.is_just_pressed(Action.INTERACT):
                self.level.master_lever.pull()
                self.level.freight_lift.trigger_lower()

            # Check Roof Hatch opening
            if self.level.freight_lift.state == FreightLiftState.AT_ROOF:
                if abs(self.boy.x - (self.level.roof_hatch.x + 50)) < 70 and input_handler.is_just_pressed(Action.INTERACT):
                    self.level.roof_hatch.open()
                    self.phase = LevelPhase.VICTORY
                    self.victory_achieved = True

        elif self.controller == ControllerMode.MIND_CONTROL_WORKERS:
            # Route inputs to WorkerGroup
            self.level.worker_group.update(
                input_handler,
                dt,
                self.level.battery,
                self.level.freight_lift,
                self.level.lower_ledge_y,
                1190.0,
                self.level.wall_right
            )

            # Check for Disengage (Q or Space tap)
            if input_handler.is_just_pressed(Action.DISENGAGE):
                self.exit_mind_control()

        # Update environment physics
        killed = self.level.update(dt, self.boy)
        if killed:
            self.death_timer = 0.0

        # Update camera tracking
        self.update_camera(dt)

        if self.victory_achieved:
            self.victory_timer += dt

    def enter_mind_control(self):
        """Transfers control from Boy to proxy Workers."""
        self.controller = ControllerMode.MIND_CONTROL_WORKERS
        self.boy.state = BoyState.MIND_CONTROL
        self.boy.x = self.level.helmet.x
        self.boy.y = self.level.helmet.y + 44.0  # Suspended under dome
        self.level.helmet.is_active = True
        self.level.worker_group.set_mind_control(True)
        self.objective_text = "Control twin workers. Push 100 kg battery onto freight lift platform. (Q: Disengage)"

    def exit_mind_control(self):
        """Transfers control back to Boy."""
        self.controller = ControllerMode.BOY
        self.boy.state = BoyState.AIRBORNE
        self.boy.vy = 50.0  # Drops back to alcove floor
        self.level.helmet.is_active = False
        self.level.worker_group.set_mind_control(False)
        if self.level.battery.is_on_lift:
            self.phase = LevelPhase.PHASE_4_LIFT
            self.objective_text = "Battery secured on lift! Pull Master Lever to lower lift."
        else:
            self.objective_text = "Jump into Mind-Control Helmet to resume controlling workers."

    def update_camera(self, dt: float):
        """Smoothly interpolates camera viewport to follow the active subject."""
        screen_w = 1280.0
        screen_h = 720.0

        if self.level.freight_lift.state == FreightLiftState.ASCENDING:
            # Camera tracks freight lift ascending to the ceiling
            target_x = self.level.freight_lift.x + self.level.freight_lift.width / 2
            target_y = self.level.freight_lift.y - 40.0
        elif self.controller == ControllerMode.MIND_CONTROL_WORKERS:
            # Camera tracks proxy workers
            target_x = self.level.worker_group.center_x
            target_y = self.level.worker_group.center_y - 80.0
        else:
            # Camera tracks boy
            target_x = self.boy.x
            target_y = self.boy.y - 70.0

        self.target_cam_x = target_x - screen_w / 2
        self.target_cam_y = target_y - screen_h / 2

        # Clamp camera to silo world bounds
        self.target_cam_x = max(0.0, min(self.level.width - screen_w, self.target_cam_x))
        self.target_cam_y = max(0.0, min(self.level.height - screen_h, self.target_cam_y))

        # Smooth camera lerp
        lerp_rate = 5.5 * dt
        self.cam_x += (self.target_cam_x - self.cam_x) * min(1.0, lerp_rate)
        self.cam_y += (self.target_cam_y - self.cam_y) * min(1.0, lerp_rate)
