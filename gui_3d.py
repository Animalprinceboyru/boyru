from ursina import *

class ModernHUD(Entity):
    def __init__(self, weather_sys, camera_ref, map_size):
        super().__init__(parent=camera.ui)
        self.weather_sys = weather_sys
        self.camera_ref = camera_ref
        
        # 좌측 상단: 시스템 정보 (영어)
        self.info_text = Text(
            text="Loading...",
            position=window.top_left + Vec2(0.02, -0.02),
            scale=1.5,
            background=True,
            color=color.white
        )
        
        # 우측 하단: 조작법 (영어)
        self.controls_text = Text(
            text="[1] Sunny  [2] Rain  [3] Fog\n[-] Slow Time  [=] Fast Time\nWASD/Arrows: Move\nSpace/C: Up/Down\nR-Click+Drag: Look",
            position=window.bottom_right + Vec2(-0.35, 0.20),
            scale=1.1,
            background=True,
            color=color.cyan
        )

    def update(self):
        cx, cy, cz = int(self.camera_ref.x), int(self.camera_ref.y), int(self.camera_ref.z)
        fps = int(1.0 / time.dt) if time.dt > 0 else 0
        
        # 시간을 00:00 포맷으로 변환
        h = int(self.weather_sys.game_time)
        m = int((self.weather_sys.game_time - h) * 60)
        time_str = f"{h:02d}:{m:02d}"
        
        # 텍스트 실시간 업데이트
        self.info_text.text = f"""SYSTEM STATUS
------------------------
Weather: {self.weather_sys.current}
Time: {time_str} (x{self.weather_sys.time_speed:.1f})
Pos: X {cx} | Y {cy} | Z {cz}
FPS: {fps}"""