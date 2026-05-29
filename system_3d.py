from ursina import *
from ursina.shaders import lit_with_shadows_shader  # 빛과 그림자를 적용하는 셰이더 불러오기!
from map_system_3d import GameMap3D
from camera_3d import FlyingCamera
from weather_3d import WeatherSystem3D
from gui_3d import ModernHUD 

def main():
    app = Ursina(title="Boyru 3D", size=(1280, 720), borderless=False)
    window.forced_aspect_ratio = 16/9
    window.fps_counter.enabled = False

    print("=== Boyru 3D ===")
    
    # 🌟 가장 핵심: 모든 3D 오브젝트가 빛과 그림자의 영향을 받도록 기본 설정 변경
    Entity.default_shader = lit_with_shadows_shader
    
    # 카메라가 멀리 있는 숲도 포기하지 않고 렌더링하도록 한계치 증가
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