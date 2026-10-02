import pygame
from core.drawing import draw_bresenham_rect, draw_bresenham_polygon, draw_bresenham_line

class UrbanEnvironment:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
        
    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float):
        """
        Draws the silhouette of the city skyline (San Francisco inspired),
        the mansion around the gate, and the street pavement.
        """
        # --- 1. Background City Skyline (Parallax effect) ---
        bg_cam_x = cam_x * 0.3
        bg_cam_y = cam_y * 0.3
        color_bg = (10, 10, 10)  # Dark silhouette
        
        # Buildings: (x, y, w, h)
        buildings = [
            (100, 250, 120, 270),
            (250, 150, 100, 370), # Transamerica pyramid-like
            (450, 300, 150, 220),
            (700, 180, 110, 340),
            (900, 280, 200, 240),
            (1200, 200, 130, 320),
            (1450, 260, 140, 260),
            (1700, 320, 100, 200)
        ]
        
        for bx, by, bw, bh in buildings:
            if bx == 250:
                # Transamerica Pyramid
                pts = [
                    (bx - bg_cam_x, by + bh - bg_cam_y),
                    (bx + bw/2 - bg_cam_x, by - bg_cam_y),
                    (bx + bw - bg_cam_x, by + bh - bg_cam_y)
                ]
                draw_bresenham_polygon(surface, pts, color_bg, filled=True)
            else:
                draw_bresenham_rect(surface, bx - bg_cam_x, by - bg_cam_y, bw, bh, color_bg, filled=True)
                
        # Golden Gate bridge towers silhouette far back (slower parallax)
        gg_cam_x = cam_x * 0.1
        gg_cam_y = cam_y * 0.1
        gg_x = 1800 - gg_cam_x
        gg_y = 150 - gg_cam_y
        color_far_bg = (6, 6, 6)
        # Tower 1
        draw_bresenham_rect(surface, gg_x, gg_y, 15, 370, color_far_bg, filled=True)
        # Tower 2
        draw_bresenham_rect(surface, gg_x + 150, gg_y, 15, 370, color_far_bg, filled=True)
        # Crossbeams
        draw_bresenham_rect(surface, gg_x, gg_y + 80, 165, 10, color_far_bg, filled=True)
        draw_bresenham_rect(surface, gg_x, gg_y + 180, 165, 10, color_far_bg, filled=True)
        # Suspender cables (rough approximations)
        draw_bresenham_line(surface, gg_x - 200, gg_y + 150, gg_x, gg_y, color_far_bg, thickness=3)
        draw_bresenham_line(surface, gg_x + 15, gg_y, gg_x + 150, gg_y + 150, color_far_bg, thickness=3)
        draw_bresenham_line(surface, gg_x + 150, gg_y, gg_x + 350, gg_y + 150, color_far_bg, thickness=3)

        # --- 2. Mansion (Surrounding the Sector Gate) ---
        # The gate is at x=2000, y=350, width=100, height=170
        # We will build the mansion perfectly around it.
        # It is on the same layer as the player (1:1 with cam_x)
        m_x = 1800 - cam_x
        m_y = 100 - cam_y
        m_w = 500
        m_h = 420 # down to the ground y=520
        mansion_color = (139, 115, 85) # Brown/Beige (increased intensity)
        pillar_color = (110, 80, 50)
        
        # Mansion main block
        draw_bresenham_rect(surface, m_x, m_y, m_w, m_h, mansion_color, filled=True)
        
        # Mansion Roof (Triangle/Greek style)
        roof_pts = [
            (m_x - 40, m_y),
            (m_x + m_w / 2, m_y - 100),
            (m_x + m_w + 40, m_y)
        ]
        draw_bresenham_polygon(surface, roof_pts, mansion_color, filled=True)
        
        # Mansion Pillars to give depth around the gate
        # Gate is x=2000 to x=2100 (relative to world)
        # So gate is at 2000-cam_x to 2100-cam_x.
        
        # Draw pillars left of gate
        for i in range(2):
            col_x = m_x + 30 + i * 80
            draw_bresenham_rect(surface, col_x, m_y, 40, m_h, pillar_color, filled=True)
            
        # Draw pillars right of gate
        for i in range(2):
            col_x = m_x + m_w - 70 - i * 80
            draw_bresenham_rect(surface, col_x, m_y, 40, m_h, pillar_color, filled=True)
            
        # Gate opening (cutout)
        # Gate is at 2000, 350. So cutout should be exactly that.
        gate_x = 2000 - cam_x
        gate_y = 350 - cam_y
        draw_bresenham_rect(surface, gate_x - 10, gate_y - 10, 120, 180, (5, 5, 5), filled=True)

        # --- 3. Street and Pavement (Middle ground) ---
        # Ground line is y=520
        pavement_color = (18, 18, 18)
        street_color = (14, 14, 14)
        
        # Pavement (Top surface and curb face)
        draw_bresenham_rect(surface, 0, 520 - cam_y, self.width - cam_x, 20, pavement_color, filled=True)
        draw_bresenham_line(surface, 0, 520 - cam_y, self.width - cam_x, 520 - cam_y, (255, 255, 255), thickness=1) # Ground boundary for player
        
        # Street (Below pavement)
        draw_bresenham_rect(surface, 0, 540 - cam_y, self.width - cam_x, self.height, street_color, filled=True)
