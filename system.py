import pygame
import sys
import random #내가 추가
from map_system import GameMap
from camera import Camera
from weather import WeatherSystem
from gui import HUD
from physics import PhysicsEngine

from Choi_animals import Rhino, ElectricEel, ToxicFrog #내가 추가
from Bae import Anaconda

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60
TITLE         = "밀림의 왕자 보이루 - 아마존 생태계 시뮬레이터"

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    print("=== 밀림의 왕자 보이루 ===")
    print("[맵 생성 중... 잠시만 기다려주세요]")

    game_map = GameMap(map_width=180, map_height=135)
    print(f"맵 생성 완료: 나무 {len(game_map.trees)}개, "
          f"둥지 {sum(1 for t in game_map.trees if t.has_nest)}개")

    camera  = Camera(SCREEN_WIDTH, SCREEN_HEIGHT,
                     game_map.pixel_width, game_map.pixel_height)
    weather = WeatherSystem(SCREEN_WIDTH, SCREEN_HEIGHT)
    hud     = HUD(SCREEN_WIDTH, SCREEN_HEIGHT)
    physics = PhysicsEngine()

    animals = []
    show_fov = False
    
    #내가 추가
    animals.append(Rhino(name="대장코뿔소", coordinate=(400.0, 500.0)))
    animals.append(ToxicFrog(name="화살독개구리", coordinate=(350.0, 450.0)))
    animals.append(Anaconda(name="아나콘다", coordinate=(600.0, 400.0)))
    i = 0
    while i <10:
        rx = int(random.uniform(100.0, 1800.0))
        ry = int(random.uniform(100.0, 1350.0))
        if game_map.is_water(rx, ry):
            animals.append(Anaconda(name=f"아나콘다_{i+1}", coordinate=(rx, ry)))
            i += 1
    # 전기뱀장어는 물 타일 근처에 스폰하는 것이 자연스럽습니다.
    animals.append(ElectricEel(name="전기뱀장어A", coordinate=(200.0, 200.0)))

    # 2. 반복문을 이용해 여러 마리를 랜덤 위치에 대량 스폰하기
    for i in range(5):
        # 안전하게 맵 중앙 부근(500 ~ 1500 픽셀 사이)에 랜덤 배치
        rx = random.uniform(500.0, 1500.0)
        ry = random.uniform(500.0, 1500.0)
        animals.append(ToxicFrog(name=f"독개구리_{i+1}", coordinate=(rx, ry)))
        
    for i in range(2):
        rx = random.uniform(600.0, 1200.0)
        ry = random.uniform(600.0, 1200.0)
        animals.append(Rhino(name=f"돌진코뿔소_{i+1}", coordinate=(rx, ry)))

    print("모든 시스템 초기화 완료!")
    print("WASD 이동 | 마우스 휠 줌 | [ ] 시간 배속 조절")
    #내가 추가한 부분 끝

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        # ── 이벤트 처리 ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    hud.selected_animal = None
                    hud.selected_tree   = None

                elif event.key == pygame.K_LEFTBRACKET:   # [ 키: 시간 느리게
                    weather.adjust_time_speed(-1)

                elif event.key == pygame.K_RIGHTBRACKET:  # ] 키: 시간 빠르게
                    weather.adjust_time_speed(1)

                elif event.key == pygame.K_F1:
                    print("[맵 재생성 중...]")
                    game_map = GameMap(map_width=180, map_height=135)
                    camera   = Camera(SCREEN_WIDTH, SCREEN_HEIGHT,
                                      game_map.pixel_width, game_map.pixel_height)
                    hud.selected_animal = None
                    hud.selected_tree   = None
                    print("맵 재생성 완료")

                elif event.key == pygame.K_F2:
                    weather._change_weather()

                elif event.key == pygame.K_F3:
                    if hud.selected_tree and not hud.selected_tree.broken:
                        game_map.break_tree(hud.selected_tree)
                        print("나무 파괴 테스트!")

                elif event.key == pygame.K_F4:
                    show_fov = not show_fov
                    print(f"시야 표시 {'ON' if show_fov else 'OFF'}")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    wx, wy = camera.screen_to_world(mx, my)
                    hud.handle_click(wx, wy, animals, game_map)

            elif event.type == pygame.MOUSEWHEEL:
                camera.handle_zoom(event.y, pygame.mouse.get_pos())

        # ── 업데이트 ──
        keys = pygame.key.get_pressed()
        camera.update(dt, keys)
        weather.update(dt)

        for animal in animals:
            if hasattr(animal, 'update'):
                animal.update(dt, game_map, weather, animals)

        if animals:
            physics.apply_separation(animals)
            for animal in animals:
                if hasattr(animal, 'coordinate'):
                    animal.coordinate = list(physics.keep_in_bounds(
                        animal.coordinate,
                        game_map.pixel_width, game_map.pixel_height
                    )) #list() 추가

        # ── 렌더링 ──
        screen.fill((15, 30, 15))
        game_map.draw(screen, camera.x, camera.y,
                      SCREEN_WIDTH, SCREEN_HEIGHT, camera.zoom)

        for animal in animals:
            if hasattr(animal, 'draw'):
                animal.draw(screen, camera)
        
        if show_fov:
                for animal in animals:
                    if hasattr(animal, 'draw_fov_debug'):
                        animal.draw_fov_debug(screen, camera, color = (80, 80, 0), alpha = 80)

        weather.draw(screen)
        hud.draw(screen, weather, camera, game_map, animals)

        fps_surf = pygame.font.SysFont("consolas", 14).render(
            f"FPS: {clock.get_fps():.1f}", True, (200, 200, 200)
        )
        screen.blit(fps_surf, (SCREEN_WIDTH - 90, 52))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()