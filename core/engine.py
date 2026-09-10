"""
Game Engine: Main Loop, Clock, Screen Surface, and UI Overlay.
Fulfills Rule 1 & Rule 3 of Development Skill:
Manages the Pygame lifecycle, fixed-timestep physics updates, camera viewports,
atmospheric monochrome post-effects, and UI.
"""

import sys
from typing import Optional
import pygame

from core.input_handler import Action, InputHandler
from core.state_manager import StateManager, LevelPhase, ControllerMode
from entities.boy import Boy
from levels.silo_level import SiloLevel


class Engine:
    def __init__(self, width: int = 1280, height: int = 720):
        pygame.init()
        pygame.font.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("INSIDE: The Watchtower Silo")

        self.clock = pygame.time.Clock()
        self.target_fps = 60
        self.is_running = True
        self.is_paused = False

        # Fonts
        self.font_title = pygame.font.Font(None, 40)
        self.font_ui = pygame.font.Font(None, 24)
        self.font_hint = pygame.font.Font(None, 20)

        # Instantiate Game Subsystems
        self.input_handler = InputHandler()
        self.level = SiloLevel()
        self.boy = Boy(self.level.spawn_x, self.level.spawn_y)
        self.state_manager = StateManager(self.boy, self.level)

    def run(self):
        """Main game loop."""
        while self.is_running:
            dt = self.clock.tick(self.target_fps) / 1000.0
            # Cap maximum delta time to prevent tunneling on frame spikes
            dt = min(0.05, dt)

            events = pygame.event.get()
            if not self.input_handler.process_events(events, dt):
                self.is_running = False
                break

            # Handle Pause toggle
            if self.input_handler.is_just_pressed(Action.PAUSE):
                self.is_paused = not self.is_paused

            if not self.is_paused:
                self.update(dt)

            self.render()

        pygame.quit()
        sys.exit(0)

    def update(self, dt: float):
        self.state_manager.update(self.input_handler, dt)

    def render(self):
        # 1. Clear with deep monochrome chiaroscuro tone (near pitch black)
        self.screen.fill((14, 15, 18))

        cam_x = self.state_manager.cam_x
        cam_y = self.state_manager.cam_y

        # 2. Render Environment, Props, Searchlight, Rain, Water, Workers
        self.level.draw(self.screen, cam_x, cam_y)

        # 3. Render Protagonist Boy Stickman
        self.boy.draw(self.screen, cam_x, cam_y)

        # 4. Render Atmospheric Vignette (Shadowed edges)
        self.draw_vignette()

        # 5. Render HUD / Objectives / Prompts
        self.draw_hud()

        # 6. Render Overlays (Death flash, Victory screen, Pause menu)
        if not self.boy.is_alive:
            self.draw_death_overlay()
        elif self.state_manager.victory_achieved:
            self.draw_victory_screen()
        elif self.is_paused:
            self.draw_pause_menu()

        pygame.display.flip()

    def draw_vignette(self):
        """Soft chiaroscuro vignette around the viewport."""
        vignette_color = (0, 0, 0)
        # Top and bottom letterbox border bars
        pygame.draw.rect(self.screen, vignette_color, (0, 0, self.width, 16))
        pygame.draw.rect(self.screen, vignette_color, (0, self.height - 16, self.width, 16))

    def draw_hud(self):
        """Minimalist atmospheric typography for objective and controls."""
        # Top banner: Current Objective
        obj_surf = self.font_ui.render(self.state_manager.objective_text, True, (220, 220, 220))
        obj_rect = obj_surf.get_rect(center=(self.width // 2, 34))

        # Backdrop plate
        pad_x, pad_y = 16, 6
        bg_rect = pygame.Rect(obj_rect.left - pad_x, obj_rect.top - pad_y, obj_rect.width + pad_x * 2, obj_rect.height + pad_y * 2)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((10, 10, 10, 190))
        self.screen.blit(bg_surf, bg_rect.topleft)
        pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 1)
        self.screen.blit(obj_surf, obj_rect)

        # Bottom-left: Active Controller Indicator
        if self.state_manager.controller == ControllerMode.MIND_CONTROL_WORKERS:
            ctrl_text = "MIND CONTROL ACTIVE: CONTROLLING PROXY WORKERS (Q: RELEASE)"
            ctrl_color = (255, 255, 255)
        else:
            ctrl_text = "CONTROLLING: BOY"
            ctrl_color = (160, 160, 160)

        ctrl_surf = self.font_hint.render(ctrl_text, True, ctrl_color)
        self.screen.blit(ctrl_surf, (24, self.height - 38))

        # Bottom-right: Quick Controls Cheat-sheet
        keys_hint = "A/D: Move | SPACE: Jump | S: Crouch (Cover) | E: Grab/Interact | SHIFT: Sprint | ESC: Pause"
        hint_surf = self.font_hint.render(keys_hint, True, (140, 140, 140))
        hint_rect = hint_surf.get_rect(bottomright=(self.width - 24, self.height - 24))
        self.screen.blit(hint_surf, hint_rect)

    def draw_death_overlay(self):
        """Whiteout electric shock effect upon electrocution."""
        flash_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        flash_surf.fill((255, 255, 255, 120))
        self.screen.blit(flash_surf, (0, 0))

        text_surf = self.font_title.render("ELECTROCUTED - HIGH VOLTAGE GRID", True, (20, 20, 20))
        text_rect = text_surf.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text_surf, text_rect)

    def draw_victory_screen(self):
        """Victory escape screen."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("ESCAPED THE SILO", True, (255, 255, 255))
        sub = self.font_ui.render("You forced open the roof hatch and escaped into the cold rain.", True, (190, 190, 190))
        instr = self.font_hint.render("Press ESC to exit.", True, (130, 130, 130))

        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 40)))
        self.screen.blit(sub, sub.get_rect(center=(self.width // 2, self.height // 2 + 10)))
        self.screen.blit(instr, instr.get_rect(center=(self.width // 2, self.height // 2 + 60)))

    def draw_pause_menu(self):
        """Pause overlay and full controls table."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 10, 12, 230))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 140)))

        controls = [
            ("Move Left", "A  /  Left Arrow", "Grounded, wading"),
            ("Move Right", "D  /  Right Arrow", "Grounded, wading"),
            ("Jump / Mantle", "Space  /  W  /  Up Arrow", "Near ledges, crates, ropes"),
            ("Crouch / Drop Down", "S  /  Down Arrow", "Stealth shadow cover behind locker"),
            ("Sprint", "Left Shift", "Grounded catwalk only (no sprint in water)"),
            ("Interact / Grab", "E  /  Left Mouse Button", "Drag crate, pull lever, push battery"),
            ("Disengage / Release", "Q  /  Space (Tap)", "Let go of rope, disengage helmet"),
            ("Resume Game", "Escape  /  P", "Toggle pause"),
        ]

        start_y = 210
        row_h = 32
        for i, (action, keys, note) in enumerate(controls):
            y = start_y + i * row_h
            act_s = self.font_ui.render(action, True, (220, 220, 220))
            key_s = self.font_ui.render(keys, True, (255, 255, 255))
            note_s = self.font_hint.render(f"({note})", True, (140, 140, 140))

            self.screen.blit(act_s, (self.width // 2 - 320, y))
            self.screen.blit(key_s, (self.width // 2 - 100, y))
            self.screen.blit(note_s, (self.width // 2 + 150, y))
