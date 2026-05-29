import pygame
from typing import Tuple

class Camera:
    def __init__(self, screen_w: int, screen_h: int, map_w: int, map_h: int):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.map_w    = map_w
        self.map_h    = map_h

        self.x = float(map_w // 2 - screen_w // 2)
        self.y = float(map_h // 2 - screen_h // 2)
        self.target_x = self.x
        self.target_y = self.y

        self.zoom        = 1.0
        self.target_zoom = 1.0
        self.min_zoom    = 0.5
        self.max_zoom    = 2.5

        self.speed     = 350
        self.smoothing = 0.15

        self._clamp_position()

    def update(self, dt: float, keys):
        move_speed = self.speed * dt / self.zoom

        if keys[pygame.K_w] or keys[pygame.K_UP]:    self.target_y -= move_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  self.target_y += move_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self.target_x -= move_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.target_x += move_speed

        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            boost = move_speed * 1.5
            if keys[pygame.K_w] or keys[pygame.K_UP]:    self.target_y -= boost
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:  self.target_y += boost
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self.target_x -= boost
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.target_x += boost

        self.zoom += (self.target_zoom - self.zoom) * 0.2
        self._clamp_target()

        self.x += (self.target_x - self.x) * self.smoothing
        self.y += (self.target_y - self.y) * self.smoothing
        self._clamp_position()

    def handle_zoom(self, wheel_y: int, mouse_pos: Tuple[int, int]):
        old_zoom = self.target_zoom
        self.target_zoom = max(self.min_zoom,
                               min(self.max_zoom, self.target_zoom + wheel_y * 0.15))
        if self.target_zoom != old_zoom:
            mx, my = mouse_pos
            wx = mx / old_zoom + self.target_x
            wy = my / old_zoom + self.target_y
            self.target_x = wx - mx / self.target_zoom
            self.target_y = wy - my / self.target_zoom
            self._clamp_target()

    def _clamp_position(self):
        max_x = max(0.0, self.map_w - self.screen_w / self.zoom)
        max_y = max(0.0, self.map_h - self.screen_h / self.zoom)
        self.x = max(0.0, min(max_x, self.x))
        self.y = max(0.0, min(max_y, self.y))

    def _clamp_target(self):
        max_x = max(0.0, self.map_w - self.screen_w / self.target_zoom)
        max_y = max(0.0, self.map_h - self.screen_h / self.target_zoom)
        self.target_x = max(0.0, min(max_x, self.target_x))
        self.target_y = max(0.0, min(max_y, self.target_y))

    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        return int((wx - self.x) * self.zoom), int((wy - self.y) * self.zoom)

    def screen_to_world(self, sx: int, sy: int) -> Tuple[float, float]:
        return sx / self.zoom + self.x, sy / self.zoom + self.y

    def focus_on(self, wx: float, wy: float):
        self.target_x = wx - self.screen_w / self.zoom / 2
        self.target_y = wy - self.screen_h / self.zoom / 2
        self._clamp_target()

    @property
    def int_x(self): return int(self.x)
    @property
    def int_y(self): return int(self.y)
