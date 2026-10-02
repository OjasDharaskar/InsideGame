import math
from typing import List, Tuple
import pygame

from core.math2d import Matrix3x3
from core.drawing import draw_bresenham_line, draw_bresenham_circle
from entities.boy import Boy, BoyState
from core.input_handler import Action, InputHandler
from core.math2d import Matrix3x3
from levels.environment.urban_environment import UrbanEnvironment

def get_translation_matrix(tx, ty):
    return [
        [1, 0, tx],
        [0, 1, ty],
        [0, 0, 1]
    ]

def get_rotation_matrix(angle_degrees):
    theta = math.radians(angle_degrees)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    return [
        [cos_t, -sin_t, 0],
        [sin_t, cos_t, 0],
        [0, 0, 1]
    ]

def multiply_matrix_vector(matrix, vector):
    result = [0, 0, 0]
    for i in range(3):
        result[i] = (matrix[i][0] * vector[0] +
                     matrix[i][1] * vector[1] +
                     matrix[i][2] * vector[2])
    return result

def transform_point(x, y, matrix):
    vec = [x, y, 1]
    res = multiply_matrix_vector(matrix, vec)
    return res[0], res[1]

def scanline_fill_polygon(surface, vertices, color):
    if not vertices:
        return
    ymin = int(min(v[1] for v in vertices))
    ymax = int(max(v[1] for v in vertices))
    
    for y in range(ymin, ymax + 1):
        intersections = []
        n = len(vertices)
        for i in range(n):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % n]
            
            if (y1 <= y < y2) or (y2 <= y < y1):
                if y2 - y1 != 0:
                    x_int = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                    intersections.append(x_int)
        
        intersections.sort()
        for i in range(0, len(intersections) - 1, 2):
            x_start = int(intersections[i])
            x_end = int(intersections[i+1])
            for x in range(x_start, x_end + 1):
                try:
                    surface.set_at((x, y), color)
                except Exception:
                    pass

def fill_shadow(surface, x, y, width, height, color=(20, 20, 20)):
    vertices = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
    scanline_fill_polygon(surface, vertices, color)


class AsphaltPothole:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 25
        
    def draw(self, surface, cam_x, cam_y):
        draw_bresenham_circle(surface, self.x - cam_x, self.y - cam_y, self.radius, (255, 255, 255), filled=False)
        draw_bresenham_line(surface, self.x - cam_x - 10, self.y - cam_y, self.x - cam_x + 5, self.y - cam_y + 10, (255, 255, 255))
        draw_bresenham_line(surface, self.x - cam_x + 5, self.y - cam_y + 10, self.x - cam_x + 15, self.y - cam_y - 5, (255, 255, 255))

class DiscardedSidearm:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.picked_up = False
        
    def draw(self, surface, cam_x, cam_y):
        if not self.picked_up:
            cx, cy = self.x - cam_x, self.y - cam_y
            draw_bresenham_line(surface, cx - 10, cy, cx + 5, cy, (255, 255, 255))
            draw_bresenham_line(surface, cx + 5, cy, cx + 5, cy + 5, (255, 255, 255))

class ConcreteBarrier:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
    def draw(self, surface, cam_x, cam_y):
        cx, cy = self.x - cam_x, self.y - cam_y
        fill_shadow(surface, cx, cy, self.width, self.height)
        draw_bresenham_line(surface, cx, cy, cx + self.width, cy, (255, 255, 255))
        draw_bresenham_line(surface, cx, cy, cx, cy + self.height, (255, 255, 255))
        draw_bresenham_line(surface, cx + self.width, cy, cx + self.width, cy + self.height, (255, 255, 255))
        draw_bresenham_line(surface, cx, cy + self.height, cx + self.width, cy + self.height, (255, 255, 255))

class SecurityGuard:
    def __init__(self, x, y, patrol_range, is_elite=False):
        self.start_x = x
        self.x = x
        self.y = y
        self.patrol_range = patrol_range
        self.is_elite = is_elite
        self.alive = True
        self.dir = -1
        self.time_t = 0
        self.reload_timer = 0
        self.shoot_timer = 0
        self.health = 500 if is_elite else 100
        self.max_health = self.health
        
    def update(self, dt):
        if not self.alive:
            return
        self.time_t += dt
        
        self.x += self.dir * 40 * dt
        if self.x < self.start_x - self.patrol_range or self.x > self.start_x + self.patrol_range:
            self.dir *= -1
            
        self.reload_timer -= dt
        self.shoot_timer -= dt
        
    def draw(self, surface, cam_x, cam_y):
        if not self.alive:
            cx, cy = self.x - cam_x, self.y - cam_y + 30
            draw_bresenham_line(surface, cx - 20, cy, cx + 20, cy, (255, 255, 255))
            return
            
        cx, cy = self.x - cam_x, self.y - cam_y
        
        # Health bar
        bar_w = 30
        draw_bresenham_line(surface, cx - bar_w/2, cy - 45, cx + bar_w/2, cy - 45, (100, 0, 0), thickness=2)
        hp_w = bar_w * (max(0, self.health) / self.max_health)
        if hp_w > 0:
            draw_bresenham_line(surface, cx - bar_w/2, cy - 45, cx - bar_w/2 + hp_w, cy - 45, (255, 0, 0), thickness=2)
            
        # Head
        draw_bresenham_circle(surface, cx, cy - 30, 8, (255, 255, 255))
        # Body
        draw_bresenham_line(surface, cx, cy - 22, cx, cy + 10, (255, 255, 255))
        # Legs
        draw_bresenham_line(surface, cx, cy + 10, cx - 10, cy + 30, (255, 255, 255))
        draw_bresenham_line(surface, cx, cy + 10, cx + 10, cy + 30, (255, 255, 255))
        # Arm with gun
        gun_end_x = cx + (20 if self.dir > 0 else -20)
        draw_bresenham_line(surface, cx, cy - 10, gun_end_x, cy - 10, (255, 255, 255))
        
        if self.is_elite:
            # Armor
            draw_bresenham_line(surface, cx - 10, cy - 20, cx + 10, cy - 20, (255, 255, 255))
            draw_bresenham_line(surface, cx - 10, cy + 5, cx + 10, cy + 5, (255, 255, 255))
            draw_bresenham_line(surface, cx - 10, cy - 20, cx - 10, cy + 5, (255, 255, 255))
            draw_bresenham_line(surface, cx + 10, cy - 20, cx + 10, cy + 5, (255, 255, 255))

class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def spawn(self, x, y, count=10, color=(200, 0, 0)):
        import random
        for _ in range(count):
            vx = random.uniform(-100, 100)
            vy = random.uniform(-150, 50)
            life = random.uniform(0.2, 0.5)
            self.particles.append([x, y, vx, vy, life, color])
            
    def update(self, dt):
        for p in self.particles[:]:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 800 * dt # gravity
            p[4] -= dt
            if p[4] <= 0:
                self.particles.remove(p)
                
    def draw(self, surface, cam_x, cam_y):
        for p in self.particles:
            cx, cy = p[0] - cam_x, p[1] - cam_y
            draw_bresenham_circle(surface, cx, cy, 2, p[5], filled=True)

class SectorKey:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.picked_up = False
        
    def draw(self, surface, cam_x, cam_y):
        if not self.picked_up:
            cx, cy = self.x - cam_x, self.y - cam_y
            draw_bresenham_line(surface, cx - 5, cy, cx + 5, cy, (255, 215, 0), thickness=2)
            draw_bresenham_circle(surface, cx + 5, cy, 3, (255, 215, 0), filled=False)

class Bullet:
    def __init__(self, x, y, dir_x, dir_y=0):
        self.x = x
        self.y = y
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.speed = 800
        
    def update(self, dt):
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt
        
    def draw(self, surface, cam_x, cam_y):
        cx, cy = self.x - cam_x, self.y - cam_y
        if self.dir_x == 0 and self.dir_y == 0:
            dx, dy = 5, 0
        else:
            dx = self.dir_x * 5
            dy = self.dir_y * 5
        draw_bresenham_line(surface, cx - dx, cy - dy, cx + dx, cy + dy, (255, 255, 255))

class SectorGate:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_open = False
        self.y_offset = 0.0
        
    def draw(self, surface, cam_x, cam_y):
        if self.is_open and self.y_offset > -self.height:
            self.y_offset -= 1.0
            
        cx = self.x - cam_x
        cy = self.y - cam_y + self.y_offset
        
        for i in range(0, self.width, 15):
            draw_bresenham_line(surface, cx + i, cy, cx + i, cy + self.height, (255, 255, 255))
            
        draw_bresenham_line(surface, cx, cy, cx + self.width, cy, (255, 255, 255))

class TheUrbanOutskirtLevel:
    def __init__(self):
        self.width = 3000
        self.height = 720
        self.wall_left = 0
        self.wall_right = 3000
        self.water_y = 9999.0
        
        self.spawn_x = 100
        self.spawn_y = 520
        self.boy = Boy(self.spawn_x, self.spawn_y)
        
        self.env = UrbanEnvironment(self.width, self.height)
        
        self.pothole = AsphaltPothole(100, 520)
        self.barrier1 = ConcreteBarrier(300, 470, 60, 50)
        self.sidearm = DiscardedSidearm(380, 515)
        
        self.barrier2 = ConcreteBarrier(800, 470, 60, 50)
        self.barrier3 = ConcreteBarrier(1200, 470, 60, 50)
        
        self.guards = [
            SecurityGuard(600, 490, 100, False),
            SecurityGuard(1000, 490, 100, False),
            SecurityGuard(1600, 490, 200, True) # Elite guard
        ]
        
        self.gate = SectorGate(2000, 350, 100, 170)
        self.control_terminal_x = 1950
        
        self.bullets = []
        self.boy_has_gun = False
        self.boy_has_key = False
        
        self.boy_health = 100
        self.particle_system = ParticleSystem()
        self.sector_key = None
        
        self.time_t = 0
        self.cam_x = 0
        self.cam_y = 0
        
        self.MAX_LIVES = 3
        self.lives = self.MAX_LIVES
        self.game_over = False
        self.death_timer = 0.0
        self.respawn_delay = 1.4
        self.victory_achieved = False
        
        self.reload_timer = 0
        self.mouse_pos = (0, 0)
        
    @property
    def objective_text(self):
        if not self.boy_has_gun:
            return "Survive the emergence and secure a weapon."
        if not self.boy_has_key:
            return "Push through the alley and hunt the keyholder."
        if not self.gate.is_open:
            return "Unlock the sector gate and escape."
        return "Escape through the sector gate."
        
    def full_reset(self):
        self.boy = Boy(self.spawn_x, self.spawn_y)
        self.time_t = 0
        self.cam_x = 0
        self.cam_y = 0
        self.gate.is_open = False
        self.gate.y_offset = 0.0
        self.death_timer = 0.0
        self.victory_achieved = False
        self.boy_has_gun = False
        self.boy_has_key = False
        self.boy_health = 100
        self.sector_key = None
        self.particle_system = ParticleSystem()
        self.sidearm.picked_up = False
        self.bullets = []
        for g in self.guards:
            g.alive = True
            g.x = g.start_x
            g.health = getattr(g, 'max_health', 100)
        
    def get_solid_platforms(self):
        platforms = [
            (0, 520, 3000, 200)
        ]
        return platforms
        
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
            
        self.time_t += dt
        self.mouse_pos = input_handler.mouse_pos
        
        # Interact / Pickup
        if input_handler.is_just_pressed(Action.INTERACT):
            # Pick up sidearm
            if not self.sidearm.picked_up and abs(self.boy.x - self.sidearm.x) < 40:
                self.sidearm.picked_up = True
                self.boy_has_gun = True
                
            # Pick up key from dropped key object
            if self.sector_key and not self.sector_key.picked_up:
                if abs(self.boy.x - self.sector_key.x) < 50:
                    self.sector_key.picked_up = True
                    self.boy_has_key = True
                    
            # Open gate
            if self.boy_has_key and abs(self.boy.x - self.control_terminal_x) < 50:
                self.gate.is_open = True

        # Boy Shooting
        if self.boy_has_gun:
            # Aiming logic
            mx, my = self.mouse_pos
            mx += self.cam_x
            my += self.cam_y
            
            sh_x = self.boy.x + self.boy.facing * 2
            sh_y = self.boy.y - 44
            
            dx = mx - sh_x
            dy = my - sh_y
            
            if dx > 0:
                self.boy.facing = 1
            elif dx < 0:
                self.boy.facing = -1
                
            local_dx = dx if self.boy.facing == 1 else -dx
            aim_angle = math.atan2(-local_dx, dy)
            self._aim_angle = aim_angle

            if self.reload_timer <= 0 and input_handler.is_just_pressed(Action.FIRE):
                # Calculate aim direction vector (freely)
                dist = math.hypot(dx, dy)
                if dist != 0:
                    dir_x = dx / dist
                    dir_y = dy / dist
                else:
                    dir_x = self.boy.facing
                    dir_y = 0
                
                # bullet starts at gun tip
                tip_x = sh_x + dx/dist * 20
                tip_y = sh_y + dy/dist * 20
                self.bullets.append(Bullet(tip_x, tip_y, dir_x, dir_y))
                self.reload_timer = 0.5
                
        if self.reload_timer > 0:
            self.reload_timer -= dt

        # Guards logic
        for g in self.guards:
            g.update(dt)
            if g.alive:
                # Shoot at boy
                if abs(self.boy.x - g.x) < 600:
                    if g.reload_timer <= 0:
                        # Only shoot if boy is not hidden behind cover
                        behind_cover = False
                        if self.boy.state == BoyState.CROUCHING:
                            for b in [self.barrier1, self.barrier2, self.barrier3]:
                                # check if barrier is between boy and guard
                                if min(self.boy.x, g.x) < b.x + b.width/2 < max(self.boy.x, g.x):
                                    if abs(self.boy.x - b.x) < 100:
                                        behind_cover = True
                        
                        if not behind_cover:
                            dir_x = 1 if self.boy.x > g.x else -1
                            g.dir = dir_x
                            self.bullets.append(Bullet(g.x + dir_x*20, g.y - 10, dir_x, 0))
                            g.reload_timer = 2.0
                            
        # Bullet updates
        for b in self.bullets[:]:
            b.update(dt)
            
            # Check collisions with barriers
            hit_barrier = False
            for bar in [self.barrier1, self.barrier2, self.barrier3]:
                if bar.x < b.x < bar.x + bar.width and bar.y < b.y < bar.y + bar.height:
                    hit_barrier = True
                    break
            
            if hit_barrier:
                self.particle_system.spawn(b.x, b.y, count=3, color=(150, 150, 150)) # Spark particles
                self.bullets.remove(b)
                continue
                
            # Check collision with boy
            by = self.boy.y
            bh = self.boy.current_height
            if self.boy.x - 10 < b.x < self.boy.x + 10 and by - bh < b.y < by:
                self.boy_health -= 20
                self.particle_system.spawn(b.x, b.y, count=10, color=(200, 0, 0)) # Blood
                if self.boy_health <= 0:
                    self.boy.is_alive = False
                self.bullets.remove(b)
                continue
                    
            # Check collision with guards
            hit_guard = False
            for g in self.guards:
                if g.alive and abs(b.x - g.x) < 15 and abs(b.y - (g.y - 15)) < 25:
                    g.health -= 25
                    self.particle_system.spawn(b.x, b.y, count=10, color=(200, 0, 0)) # Blood
                    if g.health <= 0:
                        g.alive = False
                        if g.is_elite and not self.sector_key:
                            self.sector_key = SectorKey(g.x, g.y)
                    hit_guard = True
                    break
                    
            if hit_guard:
                self.bullets.remove(b)
                continue
                
            # Remove out of bounds bullets
            if b.x < 0 or b.x > self.width:
                self.bullets.remove(b)
                
        self.particle_system.update(dt)

        # Gate barrier check
        if not self.gate.is_open and self.gate.y_offset > -self.gate.height + 20:
            if self.boy.x > self.gate.x - 20:
                self.boy.x = self.gate.x - 20
                self.boy.vx = 0
                
        # Victory check
        if self.boy.x > 2100:
            self.victory_achieved = True
        
        self.boy.update(input_handler, dt, self.water_y, self.get_solid_platforms(), None, None, self.wall_left, self.wall_right)
        
        if self.boy_has_gun:
            self.boy.right_shoulder_angle = getattr(self, '_aim_angle', -math.pi / 2)
            self.boy.right_elbow_angle = 0
        
        # Camera logic
        target_cam_x = self.boy.x - 1280 / 2
        target_cam_y = self.boy.y - 720 / 2 - 50
        target_cam_x = max(0, min(self.width - 1280, target_cam_x))
        target_cam_y = max(0, min(self.height - 720, target_cam_y))
        
        self.cam_x += (target_cam_x - self.cam_x) * 5 * dt
        self.cam_y += (target_cam_y - self.cam_y) * 5 * dt
        
    def draw(self, surface, unused_cam_x, unused_cam_y):
        cx, cy = self.cam_x, self.cam_y
        
        self.env.draw(surface, cx, cy)
        
        self.pothole.draw(surface, cx, cy)
        self.barrier1.draw(surface, cx, cy)
        self.barrier2.draw(surface, cx, cy)
        self.barrier3.draw(surface, cx, cy)
        self.sidearm.draw(surface, cx, cy)
        
        for g in self.guards:
            g.draw(surface, cx, cy)
            
        for b in self.bullets:
            b.draw(surface, cx, cy)
            
        self.gate.draw(surface, cx, cy)
        
        if self.sector_key:
            self.sector_key.draw(surface, cx, cy)
            
        self.particle_system.draw(surface, cx, cy)
        
        # Draw control terminal
        ctx, cty = self.control_terminal_x - cx, 500 - cy
        draw_bresenham_line(surface, ctx, cty, ctx, cty + 20, (200, 200, 200))
        draw_bresenham_circle(surface, ctx, cty, 5, (255, 0, 0))
        
        # Draw Boy and attachments only if not fully inside the gate
        if self.boy.x < 2030:
            self.boy.draw(surface, cx, cy)
            
            # Draw Gun if equipped
            if self.boy_has_gun and self.boy.is_alive:
                m_trans = Matrix3x3.translation(self.boy.x - cx, self.boy.y - cy)
                m_rot = Matrix3x3.rotation(self.boy.body_angle)
                m_scale = Matrix3x3.scale(float(self.boy.facing), 1.0)
                base_mat = m_trans.multiply(m_rot).multiply(m_scale)
                
                pelvis_local = (0.0, -28.0)
                m_spine_trans = Matrix3x3.translation(pelvis_local[0], pelvis_local[1])
                m_spine_rot = Matrix3x3.rotation(self.boy.spine_angle)
                spine_mat = base_mat.multiply(m_spine_trans).multiply(m_spine_rot)
                
                sh_local = (2.0, -16.0) # Right shoulder side=1
                m_sh_trans = Matrix3x3.translation(sh_local[0], sh_local[1])
                m_sh_rot = Matrix3x3.rotation(self.boy.right_shoulder_angle)
                shoulder_mat = spine_mat.multiply(m_sh_trans).multiply(m_sh_rot)
                
                m_el_trans = Matrix3x3.translation(0.0, 11.0)
                m_el_rot = Matrix3x3.rotation(self.boy.right_elbow_angle)
                elbow_mat = shoulder_mat.multiply(m_el_trans).multiply(m_el_rot)
                hand_pt = elbow_mat.transform_point(0.0, 11.0)
                
                # Gun barrel pointing along the arm
                gun_end = elbow_mat.transform_point(0.0, 20.0)
                draw_bresenham_line(surface, hand_pt[0], hand_pt[1], gun_end[0], gun_end[1], (255, 255, 255), thickness=2)
                # handle
                handle_end = elbow_mat.transform_point(-3.0, 14.0)
                draw_bresenham_line(surface, hand_pt[0], hand_pt[1], handle_end[0], handle_end[1], (255, 255, 255), thickness=2)
                
            # Draw Boy Health Bar (Top left under lives, or above boy)
            # We will draw it above the boy
            bar_w = 40
            draw_bresenham_line(surface, self.boy.x - cx - bar_w/2, self.boy.y - cy - self.boy.current_height - 15, self.boy.x - cx + bar_w/2, self.boy.y - cy - self.boy.current_height - 15, (100, 0, 0), thickness=3)
            hp_w = bar_w * (max(0, self.boy_health) / 100.0)
            if hp_w > 0:
                draw_bresenham_line(surface, self.boy.x - cx - bar_w/2, self.boy.y - cy - self.boy.current_height - 15, self.boy.x - cx - bar_w/2 + hp_w, self.boy.y - cy - self.boy.current_height - 15, (0, 255, 0), thickness=3)

        # Final Guard UI
        for g in self.guards:
            if g.is_elite and g.alive and abs(self.boy.x - g.x) < 800:
                font = pygame.font.Font(None, 40)
                text = font.render("FINAL GUARD", True, (255, 0, 0))
                # draw top center
                surface.blit(text, text.get_rect(center=(1280//2, 80)))
