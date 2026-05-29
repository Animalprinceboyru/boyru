from ursina import *
import math

class WeatherSystem3D(Entity):
    def __init__(self, sun_light, ambient_light):
        super().__init__()
        self.current = "Sunny"
        
        self.sun_light = sun_light
        self.ambient_light = ambient_light
        self.game_time = 8.0 
        self.time_speed = 1.0 

        self.weather_filter = Entity(
            parent=camera.ui,
            model='quad',
            scale=(2, 1),
            color=color.rgba(0, 0, 0, 0),
            z=10 
        )
        self.apply_weather()

    def input(self, key):
        if key == '1': self.set_weather("Sunny")
        elif key == '2': self.set_weather("Rainy")
        elif key == '3': self.set_weather("Foggy")
        elif key == '=' or key == '+': self.time_speed += 0.5
        elif key == '-': self.time_speed = max(0.0, self.time_speed - 0.5)

    def update(self):
        self.game_time += time.dt * self.time_speed * 0.1 
        if self.game_time >= 24.0: self.game_time = 0.0

        # 태양의 높이를 sin 그래프(-1.0 ~ 1.0)로 계산
        angle = ((self.game_time - 6) / 24) * math.pi * 2
        sun_height = math.sin(angle)

        # 1. 태양광 (직사광선)
        if sun_height > 0:
            sun_r = 1.0
            sun_g = 0.4 + (0.6 * sun_height)
            sun_b = 0.1 + (0.9 * sun_height)
            self.sun_light.color = color.rgba(sun_r, sun_g, sun_b, sun_height)
        else:
            self.sun_light.color = color.rgba(0, 0, 0, 0)

        # 2. 주변광 (맵 전체의 밝기) - 핵심 수정!
        # 낮과 밤이 교차하는 지점(sun_height == 0)에서 양쪽 공식의 결과값이
        # 동일하게 r=0.25, g=0.15, b=0.20 이 나오도록 맞췄습니다.
        if sun_height > 0:
            # 낮: 태양이 높을수록 밝아짐
            amb_r = 0.25 + (0.45 * sun_height)
            amb_g = 0.15 + (0.55 * sun_height)
            amb_b = 0.20 + (0.50 * sun_height)
        else:
            # 밤: 한밤중(sun_height = -1)으로 갈수록 어두운 남색으로 변함
            night_intensity = 1.0 + sun_height  # 0(한밤중) ~ 1(일몰/일출)
            amb_r = 0.05 + (0.20 * night_intensity)
            amb_g = 0.05 + (0.10 * night_intensity)
            amb_b = 0.15 + (0.05 * night_intensity)

        self.ambient_light.color = color.rgba(amb_r, amb_g, amb_b, 1)

        # 3. 그림자(태양) 각도를 24시간 내내 멈추지 않고 360도 회전
        rotation_angle = ((self.game_time - 6) / 12) * 180
        self.sun_light.rotation_x = rotation_angle

    def set_weather(self, weather_type):
        self.current = weather_type
        self.apply_weather()

    def apply_weather(self):
        if self.current == "Sunny":
            scene.fog_density = (2000, 3000)
            camera.background_color = color.rgb32(135, 206, 235)
            self.weather_filter.color = color.rgba(0, 0, 0, 0)

        elif self.current == "Rainy":
            scene.fog_density = (50, 200)
            scene.fog_color = color.rgb32(80, 90, 100)
            camera.background_color = color.rgb32(80, 90, 100)
            self.weather_filter.color = color.rgba(0.1, 0.15, 0.2, 0.4) 

        elif self.current == "Foggy":
            scene.fog_density = (20, 100)
            scene.fog_color = color.rgb32(200, 200, 200)
            camera.background_color = color.rgb32(200, 200, 200)
            self.weather_filter.color = color.rgba(0, 0, 0, 0)