import pygame
import sys
from map_system import GameMap
from camera import Camera
from weather import WeatherSystem
from gui import HUD
from physics import PhysicsEngine

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "밀림의 왕자 보이루 - 아마존 생태계 시뮬레이터"

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    print("=== 밀림의 왕자 보이루 ===")
    print("[맵 생성 중... 잠시만 기다려주세요]")

    game_map = GameMap(map_width=180, map_height=135)
    print(f"✓ 맵 생성 완료: 나무 {len(game_map.trees)}개, "
          f"둥지 {sum(1 for t in game_map.trees if t.has_nest)}개")

    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT,
                    game_map.pixel_width, game_map.pixel_height)
    weather = WeatherSystem(SCREEN_WIDTH, SCREEN_HEIGHT)
    hud = HUD(SCREEN_WIDTH, SCREEN_HEIGHT)
    physics = PhysicsEngine()

    animals = []  # 조원들이 동물 클래스 완성 후 여기에 추가

    print("✓ 모든 시스템 초기화 완료!")
    print("🎮 WASD 이동 | 마우스 휠 줌 | 클릭 선택")

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
                    hud.selected_tree = None

                elif event.key == pygame.K_F1:
                    print("[맵 재생성 중...]")
                    game_map = GameMap(map_width=180, map_height=135)
                    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT,
                                    game_map.pixel_width, game_map.pixel_height)
                    hud.selected_animal = None
                    hud.selected_tree = None
                    print("✓ 맵 재생성 완료")

                elif event.key == pygame.K_F2:
                    weather._change_weather()

                elif event.key == pygame.K_F3:
                    if hud.selected_tree and not hud.selected_tree.broken:
                        game_map.break_tree(hud.selected_tree)
                        print("🦏 F3: 나무 파괴 테스트!")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_x, mouse_y = event.pos
                    world_x, world_y = camera.screen_to_world(mouse_x, mouse_y)
                    hud.handle_click(world_x, world_y, animals, game_map)

            elif event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                camera.handle_zoom(event.y, mouse_pos)

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
                    animal.coordinate = physics.keep_in_bounds(
                        animal.coordinate,
                        game_map.pixel_width,
                        game_map.pixel_height
                    )

        # ── 렌더링 ──
        screen.fill((20, 40, 20))

        game_map.draw(screen, camera.x, camera.y,
                      SCREEN_WIDTH, SCREEN_HEIGHT, camera.zoom)

        for animal in animals:
            if hasattr(animal, 'draw'):
                animal.draw(screen, camera)

        weather.draw(screen)
        hud.draw(screen, weather, camera, game_map, animals)

        # FPS 표시
        fps_surf = pygame.font.SysFont("consolas", 14).render(
            f"FPS: {clock.get_fps():.1f}", True, (200, 200, 200)
        )
        screen.blit(fps_surf, (SCREEN_WIDTH - 90, 52))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()