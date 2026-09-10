"""
Input Handler for Inside: The Watchtower Silo.
Maps keyboard and mouse inputs to abstract Action enums according to Phase 5 control spec.
"""

from enum import Enum, auto
from typing import Dict, List, Set
import pygame


class Action(Enum):
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    JUMP = auto()
    CROUCH = auto()
    SPRINT = auto()
    INTERACT = auto()
    SECONDARY = auto()
    DISENGAGE = auto()
    PAUSE = auto()


class InputHandler:
    def __init__(self):
        # Action mappings: Action -> tuple of keycodes
        self.key_bindings: Dict[Action, List[int]] = {
            Action.MOVE_LEFT: [pygame.K_a, pygame.K_LEFT],
            Action.MOVE_RIGHT: [pygame.K_d, pygame.K_RIGHT],
            Action.JUMP: [pygame.K_SPACE, pygame.K_w, pygame.K_UP],
            Action.CROUCH: [pygame.K_s, pygame.K_DOWN],
            Action.SPRINT: [pygame.K_LSHIFT, pygame.K_RSHIFT],
            Action.INTERACT: [pygame.K_e],
            Action.SECONDARY: [pygame.K_f],
            Action.DISENGAGE: [pygame.K_q],
            Action.PAUSE: [pygame.K_ESCAPE, pygame.K_p],
        }

        # Mouse mappings: Action -> mouse button index (1: LMB, 3: RMB)
        self.mouse_bindings: Dict[Action, int] = {
            Action.INTERACT: 1,  # Left Mouse Button
            Action.SECONDARY: 3,  # Right Mouse Button
        }

        self.current_actions: Set[Action] = set()
        self.prev_actions: Set[Action] = set()
        self.just_pressed_actions: Set[Action] = set()
        self.just_released_actions: Set[Action] = set()

        self.space_press_time = 0.0
        self.mouse_pos = (0, 0)
        self.mouse_buttons = (False, False, False)

    def process_events(self, events: List[pygame.event.Event], dt: float = 0.016) -> bool:
        """
        Processes SDL events, returns False if application should exit (QUIT event).
        """
        self.prev_actions = set(self.current_actions)
        self.just_pressed_actions.clear()
        self.just_released_actions.clear()

        # Check raw keyboard state
        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_buttons = mouse_pressed

        new_actions: Set[Action] = set()

        # Keyboard checks
        for action, key_list in self.key_bindings.items():
            if any(keys[k] for k in key_list if k < len(keys)):
                new_actions.add(action)

        # Mouse checks
        for action, btn in self.mouse_bindings.items():
            if btn == 1 and mouse_pressed[0]:
                new_actions.add(action)
            elif btn == 3 and mouse_pressed[2]:
                new_actions.add(action)

        # Handle space tap vs hold for DISENGAGE
        # In the spec: Space can act as Jump or tap to Disengage/Release
        for event in events:
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.space_press_time = 0.0
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    # Quick tap of space (< 0.25s) also registers as DISENGAGE
                    if self.space_press_time < 0.25:
                        self.just_pressed_actions.add(Action.DISENGAGE)

        if keys[pygame.K_SPACE]:
            self.space_press_time += dt

        self.current_actions = new_actions
        self.just_pressed_actions.update(self.current_actions - self.prev_actions)
        self.just_released_actions.update(self.prev_actions - self.current_actions)

        return True

    def is_down(self, action: Action) -> bool:
        """True as long as action input is held down."""
        return action in self.current_actions

    def is_just_pressed(self, action: Action) -> bool:
        """True only on the frame the action was pressed."""
        return action in self.just_pressed_actions

    def is_just_released(self, action: Action) -> bool:
        """True only on the frame the action was released."""
        return action in self.just_released_actions
