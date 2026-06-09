import pygame
import sys
import random #내가 추가
from map_system import GameMap, TILE_SIZE
from camera import Camera
from weather import WeatherSystem
from gui import HUD
from physics import PhysicsEngine
from Lee_animals import Parrot, Capybara, Monkey #내가 추가
from Choi_animals import Rhino, ElectricEel, ToxicFrog #내가 추가
from Bae import Anaconda, Crocodile, Tarantula
from kim import Mosquito
import math

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60
TITLE         = "밀림의 왕자 보이루 - 아마존 생태계 시뮬레이터"

# === [핵심] 터미널 print() 출력을 가로채서 GUI로 보내는 클래스 ===
class LogCatcher:
    def __init__(self, original_stdout, hud):
        self.original_stdout = original_stdout
        self.hud = hud

    def write(self, message):
        # 1. 원래대로 터미널에도 출력
        self.original_stdout.write(message) 
        
        # 2. 게임 내 GUI HUD 에도 로그 전달
        for line in message.splitlines():
            clean_line = line.strip()
            if clean_line:
                self.hud.add_log(clean_line)

    def flush(self):
        self.original_stdout.flush()
# ==========================================================

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

    # 💡 여기서 터미널의 출력을 훔쳐서 hud 객체로 연결합니다!
    # 이후의 모든 print 문장은 게임 화면 좌측 하단에 나타나게 됩니다.
    sys.stdout = LogCatcher(sys.stdout, hud)

    animals = []
    eggs = []
    show_fov = False
    
    # === [대규모 동물 스마트 스폰 시스템] ===
    print("동물 서식지 스캔 중...")
    
    # 1. 맵 전체를 스캔하여 물 타일과 육지 타일을 분리하여 저장합니다.
    water_tiles = []
    land_tiles = []
    for ty in range(2, game_map.map_height - 2): # 맵 가장자리 제외
        for tx in range(2, game_map.map_width - 2):
            if game_map.is_water(tx, ty):
                water_tiles.append((tx, ty))
            else:
                land_tiles.append((tx, ty))

    print(f"발견된 물 구역: {len(water_tiles)} / 육지 구역: {len(land_tiles)}")

    # 2. 스폰을 쉽게 해주는 도우미 함수
    def get_random_water_pos():
        tx, ty = random.choice(water_tiles)
        return (tx * TILE_SIZE + TILE_SIZE / 2, ty * TILE_SIZE + TILE_SIZE / 2)

    def get_random_land_pos():
        tx, ty = random.choice(land_tiles)
        return (tx * TILE_SIZE + TILE_SIZE / 2, ty * TILE_SIZE + TILE_SIZE / 2)

    # 3. 수중 동물 스폰 (물 타일 위치)
    for i in range(6):
        animals.append(Anaconda(name=f"아나콘다_{i+1}", coordinate=get_random_water_pos(), sex="male" if i%2==0 else "female", age=600))
        animals.append(Crocodile(name=f"악어_{i+1}", coordinate=get_random_water_pos(), sex="female" if i%2==0 else "male", age=600))
        animals.append(ElectricEel(name=f"전기뱀장어_{i+1}", coordinate=get_random_water_pos(), sex="male" if i%2==0 else "female", age=600))

    # 4. 육상 포식자 스폰 (육지 타일 위치)
    for i in range(8):
        animals.append(Tarantula(name=f"타란튤라_{i+1}", coordinate=get_random_land_pos(), sex="female" if i%2==0 else "male", age=600))
        
    for i in range(10):
        animals.append(ToxicFrog(name=f"독개구리_{i+1}", coordinate=get_random_land_pos(), sex="male" if i%2==0 else "female", age=600))

    # 5. 육상 피식자 스폰 (육지 타일 위치 - 무리 생활을 위해 다수 스폰)
    for i in range(20):
        animals.append(Capybara(name=f"카피바라_{i+1}", coordinate=get_random_land_pos(), sex="female" if i%2==0 else "male", age=600))
        
    for i in range(15):
        animals.append(Monkey(name=f"원숭이_{i+1}", coordinate=get_random_land_pos(), sex="male" if i%2==0 else "female", age=600))
        
    for i in range(12):
        animals.append(Parrot(name=f"앵무새_{i+1}", coordinate=get_random_land_pos(), sex="female" if i%2==0 else "male", age=600))
        
    for i in range(4):
        animals.append(Rhino(name=f"코뿔소_{i+1}", coordinate=get_random_land_pos(), sex="male" if i%2==0 else "female", age=600))

    print(f"총 {len(animals)}마리의 동물이 성공적으로 배치되었습니다!")
    # ========================================

    print("모든 시스템 초기화 완료!")
    print("WASD 이동 | 마우스 휠 줌 | [ ] 시간 배속 조절")
    #내가 추가한 부분 끝

    # === [운석 충돌 시스템 변수 추가] ===
    meteor_active = False
    meteor_world_x = 0.0
    meteor_world_y = 0.0
    meteor_radius = 0.0
    meteor_speed = 1500.0  # 붉은 원이 퍼져나가는 속도 (픽셀/초)

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
                if event.button == 1:  # 좌클릭
                    mx, my = event.pos
                    
                    # 💡 [추가] gui.py에 정의된 미니맵 위치와 크기 (우측 하단)
                    mm_x = SCREEN_WIDTH - 210
                    mm_y = SCREEN_HEIGHT - 160
                    mm_w = 200
                    mm_h = 150

                    # 1. 클릭한 좌표가 미니맵 내부인지 확인
                    if mm_x <= mx <= mm_x + mm_w and mm_y <= my <= mm_y + mm_h:
                        # 미니맵 내 클릭 위치를 0.0 ~ 1.0 비율로 계산
                        ratio_x = (mx - mm_x) / mm_w
                        ratio_y = (my - mm_y) / mm_h
                        
                        # 게임 맵 전체 픽셀 크기에 비율을 곱해 실제 월드 좌표 획득
                        target_world_x = ratio_x * game_map.pixel_width
                        target_world_y = ratio_y * game_map.pixel_height
                        
                        # 카메라 포커스 이동 (camera.py의 focus_on 메서드 활용)
                        camera.focus_on(target_world_x, target_world_y)
                        
                    # 2. 미니맵 밖을 클릭했다면 기존의 동물/나무 정보 보기 로직 실행
                    else:
                        wx, wy = camera.screen_to_world(mx, my)
                        keys = pygame.key.get_pressed()
                        
                        # 💡 [핵심] C 키를 누른 상태로 클릭하면 운석 충돌 발생!
                        if keys[pygame.K_c]:
                            if not meteor_active:
                                meteor_active = True
                                meteor_world_x = wx
                                meteor_world_y = wy
                                meteor_radius = 1.0
                                print("⚠️ 운석 충돌 경고! 생태계가 곧 파괴됩니다!")
                        else:
                            # C 키를 누르지 않았다면 기존의 정보 보기 로직 실행
                            hud.handle_click(wx, wy, animals, game_map)

            elif event.type == pygame.MOUSEWHEEL:
                camera.handle_zoom(event.y, pygame.mouse.get_pos())

        # ── 업데이트 ──
        keys = pygame.key.get_pressed()
        
        # 카메라는 현실 시간에 맞춰 부드럽게 이동
        camera.update(dt, keys)
        # 날씨 시스템은 자체적으로 배속 계산
        weather.update(dt)

        # 💡 [핵심] 동물들과 맵에 적용될 '게임 내 시간(game_dt)' 계산
        game_dt = dt * weather.time_speed

        # 🍎 맵 업데이트 (사과 생성)
        game_map.update(game_dt)

        # 🐾 동물 메인 업데이트 (중복 삭제 후 딱 한 번만 실행!)
        for animal in animals:
            if hasattr(animal, 'update'):
                animal.update(game_dt, game_map, weather, animals)
            
            # ✨ 동물이 품고 있는 새 생명(알/새끼) 꺼내기
            if getattr(animal, 'pending_child', None) is not None:
                child = animal.pending_child
                if type(child).__name__ == "Egg":
                    eggs.append(child)  # 알이면 부화기에 넣기
                else:
                    animals.append(child) # 태생이면 바로 필드에 추가
                animal.pending_child = None
        
        # 🥚 알 부화 관리
        for egg in eggs[:]:
            hatched_animal = egg.update(game_dt)
            if hatched_animal:  # 부화 성공 시
                animals.append(hatched_animal)
                eggs.remove(egg)

        # 물리 엔진 및 경계선 처리
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
        
        # [레이어 1] 맵 (바닥 및 기본 나무들)
        game_map.draw(screen, camera.x, camera.y,
                      SCREEN_WIDTH, SCREEN_HEIGHT, camera.zoom)
        
        # [레이어 2 & 3] 지상 동물과 나무의 동적 Y좌표 정렬
        render_queue = []
        
        # 1. 알 수집
        for egg in eggs:
            render_queue.append(('entity', egg.coordinate[1], egg))
            
        # 2. 지상 동물 수집 (나무 위에 있거나 날고 있는 동물 제외)
        for animal in animals:
            if hasattr(animal, 'coordinate') and not getattr(animal, 'on_tree', False) and not getattr(animal, 'is_flying', False):
                render_queue.append(('entity', animal.coordinate[1], animal))
                
        # 3. 화면 안의 '모든' 나무 수집 (중심점 겹침 꼼수 제거)
        # 카메라 영역에 여유 공간을 주어 화면 밖에서 튀어나오는 나뭇잎까지 캐치합니다.
        view_rect = pygame.Rect(
            camera.x - 200, camera.y - 300,
            (SCREEN_WIDTH / camera.zoom) + 400, (SCREEN_HEIGHT / camera.zoom) + 600
        )
        for tree in game_map.trees:
            px, py = tree.pixel_pos
            if view_rect.collidepoint(px, py):
                render_queue.append(('tree', py, tree))
            
        # 4. Y좌표를 기준으로 위에서 아래 순서로(오름차순) 정렬
        render_queue.sort(key=lambda item: item[1])
        
        # 5. 정렬된 순서대로 화면에 출력 (자연스러운 2.5D 원근감)
        for item_type, y_pos, obj in render_queue:
            if item_type == 'entity':
                if hasattr(obj, 'draw'):
                    obj.draw(screen, camera)
            elif item_type == 'tree':
                game_map.draw_tree_over_animal(screen, camera.x, camera.y, camera.zoom, obj)
                
        # [레이어 4] 최상단 레이어 (공중을 날거나 나무 위에 있는 동물)
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
        
        # === [운석 충돌 효과 렌더링 및 종료 처리] ===
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