import pygame
import random
import math
from enum import Enum

class WeatherType(Enum):
    SUNNY  = "맑음"
    CLOUDY = "흐림"
    RAINY  = "비"
    STORM  = "폭풍"
    FOGGY  = "안개"

class RainDrop:
    def __init__(self, screen_w, screen_h, storm=False):
        self.x      = random.randint(0, screen_w)
        self.y      = random.randint(-screen_h, 0)
        self.speed  = random.uniform(400, 700) if storm else random.uniform(250, 450)
        self.length = random.randint(8, 18)    if storm else random.randint(5, 12)
        self.angle  = random.uniform(-0.3, -0.1) if storm else -0.05

class WeatherSystem:
    DURATIONS = {
        WeatherType.SUNNY:  (60, 120),
        WeatherType.CLOUDY: (30, 80),
        WeatherType.RAINY:  (20, 60),
        WeatherType.STORM:  (10, 30),
        WeatherType.FOGGY:  (20, 50),
    }
    TRANSITIONS = {
        WeatherType.SUNNY:  [WeatherType.CLOUDY, WeatherType.FOGGY],
        WeatherType.CLOUDY: [WeatherType.SUNNY,  WeatherType.RAINY, WeatherType.FOGGY],
        WeatherType.RAINY:  [WeatherType.CLOUDY, WeatherType.STORM],
        WeatherType.STORM:  [WeatherType.RAINY,  WeatherType.CLOUDY],
        WeatherType.FOGGY:  [WeatherType.SUNNY,  WeatherType.CLOUDY],
    }

    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.current  = WeatherType.SUNNY
        self.timer    = 0.0
        self.duration = random.uniform(*self.DURATIONS[self.current])
        self.raindrops = []
        self.overlay   = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self.game_time = 8.0
        self.time_speed = 0.5

    def update(self, dt: float):
        self.timer     += dt
        self.game_time  = (self.game_time + dt * self.time_speed / 60) % 24
        if self.timer >= self.duration:
            self._change_weather()
        if self.current in (WeatherType.RAINY, WeatherType.STORM):
            self._update_rain(dt)
        else:
            self.raindrops.clear()

    def _change_weather(self):
        self.current  = random.choice(self.TRANSITIONS[self.current])
        self.timer    = 0.0
        self.duration = random.uniform(*self.DURATIONS[self.current])
        print(f"날씨 변경 → {self.current.value}")

    def _update_rain(self, dt: float):
        storm  = self.current == WeatherType.STORM
        target = 300 if storm else 150
        while len(self.raindrops) < target:
            self.raindrops.append(RainDrop(self.screen_w, self.screen_h, storm))
        for drop in self.raindrops[:]:
            drop.y += drop.speed * dt
            drop.x += drop.speed * math.tan(drop.angle) * dt
            if drop.y > self.screen_h:
                self.raindrops.remove(drop)
                self.raindrops.append(RainDrop(self.screen_w, self.screen_h, storm))

    def draw(self, screen: pygame.Surface):
        tints = {
            WeatherType.SUNNY:  (0,   0,   0,   0),
            WeatherType.CLOUDY: (150, 150, 160, 40),
            WeatherType.RAINY:  (100, 110, 130, 70),
            WeatherType.STORM:  (60,  65,  80,  110),
            WeatherType.FOGGY:  (200, 200, 210, 90),
        }
        tint = tints[self.current]
        if tint[3] > 0:
            self.overlay.fill(tint)
            screen.blit(self.overlay, (0, 0))

        if self.current in (WeatherType.RAINY, WeatherType.STORM):
            color = (180, 200, 230) if self.current == WeatherType.RAINY else (150, 170, 210)
            for d in self.raindrops:
                ex = d.x + d.length * math.tan(d.angle)
                ey = d.y + d.length
                pygame.draw.line(screen, color, (int(d.x), int(d.y)), (int(ex), int(ey)), 1)

        if self.current == WeatherType.FOGGY:
            fog = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            fog.fill((220, 220, 230, 80))
            screen.blit(fog, (0, 0))

        self._draw_night(screen)

    def _draw_night(self, screen):
        t = self.game_time
        alpha = 0
        if t >= 20 or t < 6:
            alpha = 120
        elif 6 <= t < 8:
            alpha = int(120 * (1 - (t - 6) / 2))
        elif 18 <= t < 20:
            alpha = int(120 * (t - 18) / 2)
        if alpha > 0:
            night = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            night.fill((10, 10, 40, alpha))
            screen.blit(night, (0, 0))

    def get_speed_modifier(self) -> float:
        return {WeatherType.SUNNY:1.0, WeatherType.CLOUDY:0.95,
                WeatherType.RAINY:0.80, WeatherType.STORM:0.65,
                WeatherType.FOGGY:0.90}[self.current]

    def get_visibility_modifier(self) -> float:
        return {WeatherType.SUNNY:1.0, WeatherType.CLOUDY:0.85,
                WeatherType.RAINY:0.70, WeatherType.STORM:0.50,
                WeatherType.FOGGY:0.40}[self.current]

    @property
    def time_string(self) -> str:
        h = int(self.game_time)
        m = int((self.game_time - h) * 60)
        return f"{h:02d}:{m:02d}"