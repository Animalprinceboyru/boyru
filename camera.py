import pygame
from typing import Tuple

class Camera:
    """WASD 이동 + 마우스 커서 고정 줌"""

    def __init__(self, screen_w: int, screen_h: int,
                 map_w: int, map_h: int):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.map_w    = map_w
        self.map_h    = map_h

        # 줌
        self.zoom        = 1.0
        self.min_zoom    = 0.4
        self.max_zoom    = 3.0

        # 카메라 위치 (맵 중앙 시작)
        self.x = float(map_w // 2 - screen_w // 2)
        self.y = float(map_h // 2 - screen_h // 2)
        self.target_x = self.x
        self.target_y = self.y

        self.speed     = 400.0
        self.smoothing = 0.18

        self._clamp()

    # ── 매 프레임 업데이트 ──
    def update(self, dt: float, keys):
        spd = self.speed * dt / self.zoom

        if keys[pygame.K_w] or keys[pygame.K_UP]:    self.target_y -= spd
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  self.target_y += spd
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self.target_x -= spd
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.target_x += spd

        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            boost = spd * 1.6
            if keys[pygame.K_w] or keys[pygame.K_UP]:    self.target_y -= boost
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:  self.target_y += boost
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self.target_x -= boost
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.target_x += boost

        # 위치 부드럽게 이동
        self._clamp_target()
        self.x += (self.target_x - self.x) * self.smoothing
        self.y += (self.target_y - self.y) * self.smoothing
        self._clamp()

    # ── 마우스 휠 줌 (커서 위치 고정) ──
    def handle_zoom(self, wheel_y: int, mouse_pos: Tuple[int, int]):
        """마우스 커서가 가리키는 월드 좌표를 고정하여 줌"""
        old_zoom = self.zoom
        new_zoom = max(self.min_zoom,
                       min(self.max_zoom,
                           self.zoom + wheel_y * 0.15))

        if abs(new_zoom - old_zoom) < 0.001:
            return

        mx, my = mouse_pos

        # 마우스 커서가 가리키는 월드 좌표 (현재 줌 기준)
        world_x = self.x + mx / self.zoom
        world_y = self.y + my / self.zoom

        # 새 줌에서 같은 월드 좌표가 같은 화면 위치에 오도록 카메라 이동
        self.zoom = new_zoom
        self.x = world_x - mx / new_zoom
        self.y = world_y - my / new_zoom
        self.target_x = self.x
        self.target_y = self.y

        self._clamp()
        self._clamp_target()

    # ── 좌표 변환 ──
    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        return (int((wx - self.x) * self.zoom),
                int((wy - self.y) * self.zoom))

    def screen_to_world(self, sx: int, sy: int) -> Tuple[float, float]:
        return (sx / self.zoom + self.x,
                sy / self.zoom + self.y)

    def focus_on(self, wx: float, wy: float):
        hw = self.screen_w / self.zoom / 2
        hh = self.screen_h / self.zoom / 2
        self.target_x = wx - hw
        self.target_y = wy - hh
        self._clamp_target()

    # ── 경계 제한 ──
    def _clamp(self):
        max_x = max(0.0, self.map_w - self.screen_w / self.zoom)
        max_y = max(0.0, self.map_h - self.screen_h / self.zoom)
        self.x = max(0.0, min(max_x, self.x))
        self.y = max(0.0, min(max_y, self.y))

    def _clamp_target(self):
        max_x = max(0.0, self.map_w - self.screen_w / self.zoom)
        max_y = max(0.0, self.map_h - self.screen_h / self.zoom)
        self.target_x = max(0.0, min(max_x, self.target_x))
        self.target_y = max(0.0, min(max_y, self.target_y))