from ursina import *
from ursina.shaders import lit_with_shadows_shader
from map_system_3d import GameMap3D
from camera_3d import FlyingCamera
from weather_3d import WeatherSystem3D
from gui_3d import ModernHUD 

def main():
    # 🌟 핵심 수정: fullscreen=True를 넣어서 전체 화면으로 시작! (F11로 전환 가능)
    app = Ursina(title="Boyru 3D", fullscreen=True)
    window.fps_counter.enabled = False

    print("=== Boyru 3D ===")
    
    Entity.default_shader = lit_with_shadows_shader
    camera.clip_plane_far = 2000

    ambient = AmbientLight(color=color.rgba(0.5, 0.5, 0.5, 1))
    sun = DirectionalLight()
    sun.look_at(Vec3(1, -1, 1))

    print("Generating Jungle... (Takes a few seconds)")
    map_size = 150
    game_map = GameMap3D(width=map_size, height=map_size)
    
    free_camera = FlyingCamera(map_w=map_size, map_h=map_size)
    
    weather = WeatherSystem3D(sun_light=sun, ambient_light=ambient)
    hud = ModernHUD(weather_sys=weather, camera_ref=free_camera, map_size=map_size)

    print("✓ All systems go!")
    app.run()

if __name__ == '__main__':
    main()