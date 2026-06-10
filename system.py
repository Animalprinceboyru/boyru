import pygame
import sys
import random 
from map_system import GameMap, TILE_SIZE
from camera import Camera
from weather import WeatherSystem
from gui import HUD
from physics import PhysicsEngine
from Lee_animals import Parrot, Capybara, Monkey 
from Choi_animals import Rhino, ElectricEel, ToxicFrog 
from Bae import Anaconda, Crocodile, Tarantula
from kim import Mosquito
import math

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60
TITLE         = "밀림의 왕자 보이루 - 아마존 생태계 시뮬레이터"

class LogCatcher:
    def __init__(self, original_stdout, hud):
        self.original_stdout = original_stdout
        self.hud = hud

    def write(self, message):
        self.original_stdout.write(message) 
        for line in message.splitlines():
            clean_line = line.strip()
            if clean_line:
                self.hud.add_log(clean_line)

    def flush(self):
        self.original_stdout.flush()

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

    sys.stdout = LogCatcher(sys.stdout, hud)

    animals = []
    eggs = []
    show_fov = False
    
    print("동물 서식지 스캔 중...")
    
    water_tiles = []
    land_tiles = []
    for ty in range(2, game_map.map_height - 2): 
        for tx in range(2, game_map.map_width - 2):
            if game_map.is_water(tx, ty):
                water_tiles.append((tx, ty))
            else:
                land_tiles.append((tx, ty))

    print(f"발견된 물 구역: {len(water_tiles)} / 육지 구역: {len(land_tiles)}")

    def get_random_water_pos():
        tx, ty = random.choice(water_tiles)
        return (tx * TILE_SIZE + TILE_SIZE / 2, ty * TILE_SIZE + TILE_SIZE / 2)

    def get_random_land_pos():
        tx, ty = random.choice(land_tiles)
        return (tx * TILE_SIZE + TILE_SIZE / 2, ty * TILE_SIZE + TILE_SIZE / 2)

    for i in range(6):
        animals.append(Anaconda(name=f"아나콘다_{i+1}", coordinate=get_random_water_pos(), sex="male" if i%2==0 else "female", age=600))
        animals.append(Crocodile(name=f"악어_{i+1}", coordinate=get_random_water_pos(), sex="female" if i%2==0 else "male", age=600))
        animals.append(ElectricEel(name=f"전기뱀장어_{i+1}", coordinate=get_random_water_pos(), sex="male" if i%2==0 else "female", age=600))

    for i in range(8):
        animals.append(Tarantula(name=f"타란튤라_{i+1}", coordinate=get_random_land_pos(), sex="female" if i%2==0 else "male", age=600))
        
    for i in range(10):
        animals.append(ToxicFrog(name=f"독개구리_{i+1}", coordinate=get_random_land_pos(), sex="male" if i%2==0 else "female", age=600))

    for i in range(20):
        animals.append(Capybara(name=f"카피바라_{i+1}", coordinate=get_random_land_pos(), sex="female" if i%2==0 else "male", age=600))
        
    for i in range(15):
        animals.append(Monkey(name=f"원숭이_{i+1}", coordinate=get_random_land_pos(), sex="male" if i%2==0 else "female", age=600))
        
    # 💡 앵무새 초기 생성 수 감소 (12마리 -> 5마리로 대폭 삭감)
    for i in range(5):
        animals.append(Parrot(name=f"앵무새_{i+1}", coordinate=get_random_land_pos(), sex="female" if i%2==0 else "male", age=600))
        
    for i in range(4):
        animals.append(Rhino(name=f"코뿔소_{i+1}", coordinate=get_random_land_pos(), sex="male" if i%2==0 else "female", age=600))

    print(f"총 {len(animals)}마리의 동물이 성공적으로 배치되었습니다!")

    print("모든 시스템 초기화 완료!")
    print("WASD 이동 | 마우스 휠 줌 | [ ] 시간 배속 조절")

    meteor_active = False
    meteor_world_x = 0.0
    meteor_world_y = 0.0
    meteor_radius = 0.0
    meteor_speed = 1500.0 

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    hud.selected_animal = None
                    hud.selected_tree   = None

                elif event.key == pygame.K_LEFTBRACKET:
                    weather.adjust_time_speed(-1)

                elif event.key == pygame.K_RIGHTBRACKET:
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
                    
                    mm_x = SCREEN_WIDTH - 210
                    mm_y = SCREEN_HEIGHT - 160
                    mm_w = 200
                    mm_h = 150

                    if mm_x <= mx <= mm_x + mm_w and mm_y <= my <= mm_y + mm_h:
                        ratio_x = (mx - mm_x) / mm_w
                        ratio_y = (my - mm_y) / mm_h
                        
                        target_world_x = ratio_x * game_map.pixel_width
                        target_world_y = ratio_y * game_map.pixel_height
                        
                        camera.focus_on(target_world_x, target_world_y)
                        
                    else:
                        wx, wy = camera.screen_to_world(mx, my)
                        keys = pygame.key.get_pressed()
                        
                        if keys[pygame.K_c]:
                            if not meteor_active:
                                meteor_active = True
                                meteor_world_x = wx
                                meteor_world_y = wy
                                meteor_radius = 1.0
                                print("⚠️ 운석 충돌 경고! 생태계가 곧 파괴됩니다!")
                        else:
                            hud.handle_click(wx, wy, animals, game_map)

            elif event.type == pygame.MOUSEWHEEL:
                camera.handle_zoom(event.y, pygame.mouse.get_pos())

        keys = pygame.key.get_pressed()
        camera.update(dt, keys)
        weather.update(dt)

        game_dt = dt * weather.time_speed
        game_map.update(game_dt)

        for animal in animals:
            if hasattr(animal, 'update'):
                animal.update(game_dt, game_map, weather, animals)
            
            if getattr(animal, 'pending_child', None) is not None:
                child = animal.pending_child
                if type(child).__name__ == "Egg":
                    eggs.append(child)
                else:
                    animals.append(child)
                animal.pending_child = None
        
        for egg in eggs[:]:
            hatched_animal = egg.update(game_dt)
            if hatched_animal:
                animals.append(hatched_animal)
                eggs.remove(egg)

        if animals:
            physics.apply_separation(animals)
            for animal in animals:
                if hasattr(animal, 'coordinate'):
                    animal.coordinate = list(physics.keep_in_bounds(
                        animal.coordinate,
                        game_map.pixel_width, game_map.pixel_height
                    ))

        screen.fill((15, 30, 15))
        
        game_map.draw(screen, camera.x, camera.y,
                      SCREEN_WIDTH, SCREEN_HEIGHT, camera.zoom)
        
        render_queue = []
        
        for egg in eggs:
            render_queue.append(('entity', egg.coordinate[1], egg))
            
        for animal in animals:
            if hasattr(animal, 'coordinate') and not getattr(animal, 'on_tree', False) and not getattr(animal, 'is_flying', False):
                render_queue.append(('entity', animal.coordinate[1], animal))
                
        view_rect = pygame.Rect(
            camera.x - 200, camera.y - 300,
            (SCREEN_WIDTH / camera.zoom) + 400, (SCREEN_HEIGHT / camera.zoom) + 600
        )
        for tree in game_map.trees:
            px, py = tree.pixel_pos
            if view_rect.collidepoint(px, py):
                render_queue.append(('tree', py, tree))
            
        render_queue.sort(key=lambda item: item[1])
        
        for item_type, y_pos, obj in render_queue:
            if item_type == 'entity':
                if hasattr(obj, 'draw'):
                    obj.draw(screen, camera)
            elif item_type == 'tree':
                game_map.draw_tree_over_animal(screen, camera.x, camera.y, camera.zoom, obj)
                
        for animal in animals:
            if getattr(animal, 'on_tree', False) or getattr(animal, 'is_flying', False):
                if hasattr(animal, 'draw'):
                    animal.draw(screen, camera)
        
        if show_fov:
            for animal in animals:
                if hasattr(animal, 'draw_fov_debug'):
                    animal.draw_fov_debug(screen, camera, alpha=80)

        weather.draw(screen)
        hud.draw(screen, weather, camera, game_map, animals)

        fps_surf = pygame.font.SysFont("consolas", 14).render(
            f"FPS: {clock.get_fps():.1f}", True, (200, 200, 200)
        )
        screen.blit(fps_surf, (SCREEN_WIDTH - 90, 52))
        
        if meteor_active:
            meteor_radius += meteor_speed * dt
            sx, sy = camera.world_to_screen(meteor_world_x, meteor_world_y)
            
            pygame.draw.circle(screen, (120, 0, 0), (int(sx), int(sy)), int(meteor_radius * camera.zoom))
            pygame.draw.circle(screen, (200, 40, 40), (int(sx), int(sy)), int(meteor_radius * camera.zoom * 0.7))
            pygame.draw.circle(screen, (255, 200, 200), (int(sx), int(sy)), int(meteor_radius * camera.zoom * 0.2))

            max_dist = max(
                math.hypot(sx - 0, sy - 0),
                math.hypot(sx - SCREEN_WIDTH, sy - 0),
                math.hypot(sx - 0, sy - SCREEN_HEIGHT),
                math.hypot(sx - SCREEN_WIDTH, sy - SCREEN_HEIGHT)
            )

            if (meteor_radius * camera.zoom) >= max_dist:
                screen.fill((0, 0, 0)) 
                pygame.display.flip()
                print("💥 운석 충돌로 인해 아마존 생태계가 멸망했습니다.")
                pygame.time.delay(2000) 
                running = False 

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()