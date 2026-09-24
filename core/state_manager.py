"""
State Manager: Routes inputs to Boy or Proxy Minion Workers.
Manages level progression phases, pawn swapping via Mind-Control Helmet,
lives tracking, full-reset respawning, Game Over state, and camera focus target.
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
    MAX_LIVES = 3

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
        self.respawn_delay = 1.4   # Slightly longer for dramatic effect

        # 3-Lives system
        self.lives = self.MAX_LIVES
        self.game_over = False

        # Victory state
        self.victory_achieved = False
        self.victory_timer = 0.0

        # Objective hint string
        self.objective_text = "Drop into water. Drag crate under power cable to reach catwalk."
        self.helmet_cooldown = 0.0

    def _do_full_reset(self):
        """
        Resets all game state for a fresh play-through after losing a life.
        All level progress is wiped.
        """
        self.level.full_reset(self.boy)
        self.phase = LevelPhase.PHASE_1_CRATE
        self.controller = ControllerMode.BOY
        self.death_timer = 0.0
        self.helmet_cooldown = 0.0
        self.objective_text = "Drop into water. Drag crate under power cable to reach catwalk."
        # Reset camera to spawn area
        self.cam_x = 0.0
        self.cam_y = 600.0

    def update(self, input_handler: InputHandler, dt: float):
        # ------------------------------------------------------------------
        # Game Over: no more updates until engine restarts the game
        # ------------------------------------------------------------------
        if self.game_over:
            return

        # ------------------------------------------------------------------
        # Handle death and life-loss
        # ------------------------------------------------------------------
        if not self.boy.is_alive:
            self.death_timer += dt
            if self.death_timer >= self.respawn_delay:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                    self.lives = 0
                else:
                    self._do_full_reset()
            return

        if self.helmet_cooldown > 0.0:
            self.helmet_cooldown -= dt
        if self.boy.is_grounded:
            self.helmet_cooldown = 0.0

        # ------------------------------------------------------------------
        # Phase Detection & Objective Updates
        # ------------------------------------------------------------------
        if self.phase == LevelPhase.PHASE_1_CRATE:
            if self.boy.y <= self.level.catwalk_y + 10.0 and self.boy.x >= 350.0:
                self.phase = LevelPhase.PHASE_2_SEARCHLIGHT
                self.objective_text = "Cross catwalk. Crouch behind the locked escape door to evade searchlight."

        elif self.phase == LevelPhase.PHASE_2_SEARCHLIGHT:
            if self.boy.x >= 950.0:  # Reached generator alcove
                self.phase = LevelPhase.PHASE_3_BATTERY
                self.objective_text = "Jump into Mind-Control Helmet to control workers. Push the battery onto the freight lift!"

        elif self.phase == LevelPhase.PHASE_3_BATTERY:
            if self.level.battery.is_on_lift:
                self.phase = LevelPhase.PHASE_4_LIFT
                if self.controller == ControllerMode.BOY:
                    self.objective_text = "Battery on lift! Pull Master Lever to send lift UP to catwalk level."
                else:
                    self.objective_text = "Battery loaded onto lift! Press Q to return to Boy. Then pull the lever."

        elif self.phase == LevelPhase.PHASE_4_LIFT:
            # Door is unlocked manually via RoofConsole
            if self.level.exit_door.is_locked:
                if self.level.freight_lift.is_boy_on_lift(self.boy):
                    if self.level.freight_lift.state == FreightLiftState.AT_ROOF:
                        if self.level.roof_console.check_range(self.boy):
                            self.objective_text = "Roof Console: Press E to activate it and unlock the escape door!"
                        else:
                            self.objective_text = "Step onto the roof platform and interact with the console."
                    elif self.level.freight_lift.state in (FreightLiftState.ASCENDING, FreightLiftState.LOWERING):
                        self.objective_text = "Riding Freight Lift… (Press E on lift to reverse direction)"
                    elif self.level.freight_lift.state == FreightLiftState.LOWERED:
                        self.objective_text = "On lower ledge. Step off, pull the Master Lever to send lift UP!"
                    else:
                        self.objective_text = "Lift is at catwalk. Press E to ride up to the roof."
                elif self.level.master_lever.check_range(self.boy):
                    self.objective_text = "Master Lever: Press E to send Freight Lift to the roof."
                else:
                    self.objective_text = "Ride the lift up to the roof with the battery."
            else:
                # Door is unlocked, player needs to reach it on the catwalk
                if not self.level.exit_door.is_open:
                    self.objective_text = "Escape door UNLOCKED! Ride the lift down to the catwalk and escape!"

        # ------------------------------------------------------------------
        # Input Routing & Pawn Swapping
        # ------------------------------------------------------------------
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
            if self.helmet_cooldown <= 0.0 and self.level.helmet.check_interaction(self.boy):
                self.enter_mind_control()

            # Check Master Lever toggle in alcove
            if self.level.master_lever.check_range(self.boy) and input_handler.is_just_pressed(Action.INTERACT):
                self.level.master_lever.toggle()
                self.level.freight_lift.toggle_move()

            # Check Roof Console interaction
            if self.level.roof_console.check_range(self.boy) and input_handler.is_just_pressed(Action.INTERACT):
                if not self.level.roof_console.is_activated and self.level.freight_lift.battery_installed:
                    self.level.roof_console.is_activated = True
                    self.level.exit_door.unlock()
            
            # Check Freight Lift toggle via E (when boy is on lift, not near exit door or console)
            elif self.level.freight_lift.is_boy_on_lift(self.boy) and not self.level.roof_console.check_range(self.boy):
                if input_handler.is_just_pressed(Action.INTERACT):
                    self.level.freight_lift.toggle_move()

            # Check Exit Door interaction (victory condition) — door is on the catwalk
            if (not self.level.exit_door.is_locked
                    and not self.level.exit_door.is_open
                    and self.level.exit_door.check_interact(self.boy)
                    and input_handler.is_just_pressed(Action.INTERACT)):
                self.level.exit_door.open()
                self.phase = LevelPhase.VICTORY
                self.victory_achieved = True
                self.objective_text = "ESCAPED! You slipped through the exit door into the cold rain."

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

            # Check for Disengage (Q or Space / Jump tap)
            if input_handler.is_just_pressed(Action.DISENGAGE) or input_handler.is_just_pressed(Action.JUMP):
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
        self.objective_text = "Control twin workers. Push battery onto freight lift platform. (Q: Disengage)"

    def exit_mind_control(self):
        """Transfers control back to Boy."""
        self.controller = ControllerMode.BOY
        self.boy.state = BoyState.AIRBORNE
        self.boy.vy = 80.0  # Drops back to alcove floor
        self.helmet_cooldown = 1.0  # Prevents immediate re-absorption
        self.level.helmet.is_active = False
        self.level.worker_group.set_mind_control(False)
        if self.level.battery.is_on_lift:
            self.phase = LevelPhase.PHASE_4_LIFT
            self.objective_text = "Battery on lift! Pull Master Lever to send lift UP to the ceiling."
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
