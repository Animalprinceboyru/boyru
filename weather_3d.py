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

        # 🌟 일출과 일몰 시간을 직접 설정! (낮을 훨씬 길게 만듦)
        sunrise = 5.0   # 새벽 5시 일출
        sunset = 20.0   # 저녁 8시(20시) 일몰
        day_length = sunset - sunrise
        night_length = 24.0 - day_length

        # 시간에 따라 태양의 고도와 회전 각도를 계산
        if sunrise <= self.game_time <= sunset:
            # 낮 시간 진행률 (0.0 ~ 1.0)
            day_progress = (self.game_time - sunrise) / day_length
            sun_height = math.sin(day_progress * math.pi)
            rotation_angle = day_progress * 180
        else:
            # 밤 시간 진행률 (0.0 ~ 1.0)
            if self.game_time > sunset:
                night_progress = (self.game_time - sunset) / night_length
            else:
                night_progress = (self.game_time + (24.0 - sunset)) / night_length
            sun_height = -math.sin(night_progress * math.pi)
            rotation_angle = 180 + (night_progress * 180)

        # 색상 및 밝기 계산 (이전의 완벽한 지구과학 셰이더 적용)
        if sun_height > 0:
            intensity = math.sqrt(sun_height)
            
            sun_r = 0.8 + (0.2 * intensity)
            sun_g = 0.3 + (0.7 * intensity)
            sun_b = 0.1 + (0.9 * (intensity ** 2)) 
            
            self.sun_light.color = color.rgba(sun_r * intensity, sun_g * intensity, sun_b * intensity, 1)

            amb_r = 0.3 + (0.55 * intensity)
            amb_g = 0.2 + (0.65 * intensity)
            amb_b = 0.25 + (0.60 * intensity)
            self.ambient_light.color = color.rgba(amb_r, amb_g, amb_b, 1)
        else:
            self.sun_light.color = color.rgba(0, 0, 0, 0)
            
            night_intensity = 1.0 + sun_height 
            amb_r = 0.05 + (0.20 * night_intensity)
            amb_g = 0.05 + (0.15 * night_intensity)
            amb_b = 0.15 + (0.10 * night_intensity)
            self.ambient_light.color = color.rgba(amb_r, amb_g, amb_b, 1)

        self.sun_light.rotation_x = rotation_angle

    def set_weather(self, weather_type):
        self.current = weather_type
        self.apply_weather()

    def apply_weather(self):
        if self.current == "Sunny":
            scene.fog_density = (2000, 3000)
            camera.background_color = color.rgb32(135, 206, 235)
            self