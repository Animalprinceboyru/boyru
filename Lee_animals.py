import random
import pygame
import math
from typing import Tuple, List, Optional

# base_classes 대신 실제 파일인 animal에서 import
from animal import Animal, Prey, TILE_SIZE
import camera 

# 최강빈 조원이 만든 클래스가 Choi_animals.py 에 있으므로 정상 참조
try:
    from Choi_animals import FlyingAnimal
except ImportError:
    # FlyingAnimal이 없을 경우 오류 방지를 위한 폴백
    FlyingAnimal = Animal 

Lee = {}


# ==========================================
# 1. 카피바라 (Capybara)
# ==========================================
class Capybara(Prey):
    SPECIES_VISION_RANGE = 200.0
    SPECIES_VISION_ANGLE = 270.0
    minimap_color = (210, 180, 140)  # 미니맵에 표시할 갈색

    def __init__(self, name: str, coordinate: Tuple[float, float], **kwargs):
        super().__init__(name, coordinate, danger_range=150.0, **kwargs)
        self.stress_level = 0.0
        self.group_size = 1
        
        self.max_hp = 120
        self.hp = 120
        self.max_speed = 60.0
        self.escape_success_rate = 0.5
        
        # 평상시 배회를 위한 변수
        self.target_coord: Optional[List[float]] = None
        self.wander_timer = 0.0

        # 💡 1. 여기서 카피바라 전용 이미지를 설정
        self.image_path = "capybara.png"  # 카피바라 이미지 파일명
        self.image = None
        
        # 이미지가 캐시에 없으면 최초 1회 로드
        if self.image_path not in Lee:
            try:
                loaded_img = pygame.image.load(self.image_path).convert_alpha()
                Lee[self.image_path] = loaded_img
            except Exception as e:
                print(f"⚠️ {name} 이미지 로드 실패: {e}")
                # 💡 [핵심] 실패하더라도 딕셔너리에 None을 넣어줘야함
                Lee[self.image_path] = None
        orig_img = Lee[self.image_path]
        if orig_img is not None:
            orig_w, orig_h = orig_img.get_size() # 원본 이미지의 가로, 세로 픽셀
                
            # 동물의 크기(size)를 기준으로 최대 렌더링 크기 설정
            target_max_size = int(self.size * 2.5)
                
            # 가로와 세로 중 더 긴 쪽을 기준으로 축소/확대 비율(scale_factor)을 계산
            scale_factor = target_max_size / max(orig_w, orig_h)
                
            # 구한 비율을 가로, 세로에 똑같이 곱해주어 비율 유지
            new_w = int(orig_w * scale_factor)
            new_h = int(orig_h * scale_factor)
                
            # 새로운 가로, 세로 크기로 스케일링
            self.image = pygame.transform.scale(orig_img, (new_w, new_h))
        else:
            self.image = None # 이미지가 없으면 None으로 유지 (draw 메서드에서 부모의 원형 그리기로 대체됨)

    def draw(self, screen: pygame.Surface, camera):
        if not self.alive:
            return
        
        # 1. 화면 좌표를 먼저 계산합니다.
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        
        # 💡 [최적화 핵심] 동물이 화면을 완전히 벗어났다면 아예 연산(스케일, 회전)을 하지 않고 종료합니다.
        # 여유 공간(margin)을 약 100픽셀 정도 두어 자연스럽게 사라지도록 합니다.
        margin = 100
        if not (-margin < sx < camera.screen_w + margin and -margin < sy < camera.screen_h + margin):
            return

        if self.image:
            # 만약 이미지가 정상적으로 로드되었다면 이미지로 그림
            # 화면 좌표 계산
            sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
            
            # 💡 [핵심 수정] 이미지의 현재 가로, 세로 길이에 각각 카메라 줌 비율을 곱해줍니다!
            new_w = int(self.image.get_width() * camera.zoom)
            new_h = int(self.image.get_height() * camera.zoom)
                
            # 비율이 유지된 채로 줌인/줌아웃 되도록 스케일링
            scaled_image = pygame.transform.scale(self.image, (new_w, new_h))
            scaled_image = pygame.transform.flip(scaled_image, True, False) # 뱀장어는 이미지 바라보는 방향이 반대라 좌우 반전
            scaled_image = pygame.transform.rotate(scaled_image, 20) # 뱀장어는 살짝 기울어져 있음

            # 💡 2. 진행 방향(facing_angle)을 기준으로 회전 적용
            angle_deg = math.degrees(-self.facing_angle)
            rotated_image = pygame.transform.rotate(scaled_image, angle_deg)
                
            # 이미지 출력 (중심점 맞추기)
            rect = rotated_image.get_rect(center=(sx, sy))
            screen.blit(rotated_image, rect)
                
            # 체력바 렌더링
            hp_ratio = self.hp / self.max_hp
            bar_w = 30 * camera.zoom
            bar_h = 4 * camera.zoom
            # 체력바 위치도 이미지 세로 크기에 맞춰 유동적으로 조절
            pygame.draw.rect(screen, (220, 60, 60), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w, bar_h))
            pygame.draw.rect(screen, (100, 220, 120), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w * hp_ratio, bar_h))
        else:
            # 이미지 로드 실패 시 기본 원으로 그리기(부모 클래스)
            super().draw(screen, camera)

    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        """
        [계획서 사양 구현] 다수의 개체가 모이면 group_size 속성이 증가하여,
        포식자의 공격 성공 확률을 낮추는 방어 버프(회피)를 얻습니다.
        """
        evade_chance = min(0.60, 0.12 * (self.group_size - 1))
        if evade_chance > 0 and random.random() < evade_chance:
            print(f"🛡️ [{self.name}]가 무리 방어 버프(방어 확률: {evade_chance:.1%})로 포식자의 공격을 무력화했습니다!")
            return
        super().take_damage(amount, source)

    def socialize(self, animals: List[Animal]):
        """주변의 카피바라와 모여 그룹 사이즈를 늘리고 생존율(방어 버프)을 높입니다."""
        nearby_capybaras = [
            a for a in animals 
            if isinstance(a, Capybara) and a is not self and a.alive and self.distance_to(a) < 120.0
        ]
        self.group_size = 1 + len(nearby_capybaras)
        
        if self.group_size > 1:
            self.stress_level = max(0.0, self.stress_level - 1.5)
            self.escape_success_rate = min(0.95, 0.5 + 0.1 * len(nearby_capybaras))

    def flee_to_water(self, game_map, dt: float, predator: Animal):
        """가까운 물가 방향을 찾아 우선적으로 도망칩니다."""
        tx, ty = int(self.coordinate[0] // TILE_SIZE), int(self.coordinate[1] // TILE_SIZE)
        
        water_target = None
        min_dist = float('inf')
        search_radius = 8
        
        for dy in range(-search_radius, search_radius + 1):
            for dx in range(-search_radius, search_radius + 1):
                nx, ny = tx + dx, ty + dy
                if 0 <= nx < game_map.map_width and 0 <= ny < game_map.map_height:
                    if game_map.is_water(nx, ny):
                        dist = dx*dx + dy*dy
                        if dist < min_dist:
                            min_dist = dist
                            water_target = (nx * TILE_SIZE + TILE_SIZE/2, ny * TILE_SIZE + TILE_SIZE/2)
                            
        if water_target:
            self.move(dt, water_target, self.flee_speed_mul * self.escape_success_rate)
        else:
            self.flee_from(predator, dt)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        # 이중 이동 방지를 위해 super().update 대신 Animal.update 직접 호출
        Animal.update(self, dt, game_map, weather, animals)
        if not self.alive or self.is_stunned:
            return
        
        self.socialize(animals)
        predators = self.detect_predators(animals, game_map)
        
        if predators:
            self.predator_detected = True
            self.stress_level = min(100.0, self.stress_level + 12.0 * dt)
            closest = min(predators, key=lambda p: self.distance_to(p))
            
            # 이미 물속이라면 포식자(전기뱀장어 등) 반대 방향으로 회피
            if getattr(self, 'environment_status', '') == 'water':
                self.flee_from(closest, dt)
            else:
                self.flee_to_water(game_map, dt, closest)
            self.target_coord = None
        else:
            self.predator_detected = False
            self.stress_level = max(0.0, self.stress_level - 6.0 * dt)

            # 🍎 [추가] 사과 탐색 및 섭취 로직
            if self.hunger > 30.0 and game_map.apples:
                closest_apple = min(game_map.apples, key=lambda a: self.distance_to((a.x, a.y)), default=None)
                if closest_apple and self.distance_to((closest_apple.x, closest_apple.y)) < self.vision_range:
                    if self.distance_to((closest_apple.x, closest_apple.y)) < 25.0:
                        print(f"🍎 [{self.name}]가 사과를 오물오물 먹었습니다!")
                        self.eat(closest_apple.heal_amount)
                        game_map.apples.remove(closest_apple)
                        self.target_coord = None
                    else:
                        self.target_coord = [closest_apple.x, closest_apple.y]
                        self.move(dt, self.target_coord, speed_multiplier=0.8)
                    return # 사과를 향해 갈 때는 기본 배회 로직을 건너뜁니다
            
            # Lee_animals.py - Capybara 클래스 update 메서드 하단 배회 부분
            self.wander_timer -= dt
            
            # Lee_animals.py - Capybara 클래스 update 메서드 하단 배회 부분
            self.wander_timer -= dt
            if self.wander_timer <= 0 or not self.target_coord:
                self.wander_timer = random.uniform(3.0, 6.0)
                rx = self.coordinate[0] + random.uniform(-200.0, 200.0)
                ry = self.coordinate[1] + random.uniform(-200.0, 200.0)
                
                # 맵 영역을 벗어나지 않도록 좌표 제한
                rx = max(50.0, min(float(game_map.pixel_width - 50.0), rx))
                ry = max(50.0, min(float(game_map.pixel_height - 50.0), ry))
                self.target_coord = [rx, ry]
            
            self.move(dt, self.target_coord, speed_multiplier=0.6)
            if self.distance_to(self.target_coord) < 15.0:
                self.target_coord = None


# ==========================================
# 2. 원숭이 (Monkey)
# ==========================================
class Monkey(Prey):
    SPECIES_VISION_RANGE = 250.0
    SPECIES_VISION_ANGLE = 200.0
    minimap_color = (139, 69, 19)  # 초콜릿색

    def __init__(self, name: str, coordinate: Tuple[float, float], **kwargs):
        super().__init__(name, coordinate, danger_range=200.0, **kwargs)
        self.on_tree = False
        self.inventory = 5          
        self.throw_power = 20.0     
        self.max_speed = 85.0
        self.current_tree = None
        
        self.target_coord: Optional[List[float]] = None
        self.wander_timer = 0.0
        self.throw_cooldown = 0.0

        # 💡 1. 여기서 원숭이 전용 이미지를 설정
        self.image_path = "monkey.png"  # 원숭이 이미지 파일명
        self.image = None
        
        # 이미지가 캐시에 없으면 최초 1회 로드
        if self.image_path not in Lee:
            try:
                loaded_img = pygame.image.load(self.image_path).convert_alpha()
                Lee[self.image_path] = loaded_img
            except Exception as e:
                print(f"⚠️ {name} 이미지 로드 실패: {e}")
                # 💡 [핵심] 실패하더라도 딕셔너리에 None을 넣어줘야함
                Lee[self.image_path] = None
        orig_img = Lee[self.image_path]
        if orig_img is not None:
            orig_w, orig_h = orig_img.get_size() # 원본 이미지의 가로, 세로 픽셀
                
            # 동물의 크기(size)를 기준으로 최대 렌더링 크기 설정
            target_max_size = int(self.size * 2.5)
                
            # 가로와 세로 중 더 긴 쪽을 기준으로 축소/확대 비율(scale_factor)을 계산
            scale_factor = target_max_size / max(orig_w, orig_h)
                
            # 구한 비율을 가로, 세로에 똑같이 곱해주어 비율 유지
            new_w = int(orig_w * scale_factor)
            new_h = int(orig_h * scale_factor)
                
            # 새로운 가로, 세로 크기로 스케일링
            self.image = pygame.transform.scale(orig_img, (new_w, new_h))
        else:
            self.image = None # 이미지가 없으면 None으로 유지 (draw 메서드에서 부모의 원형 그리기로 대체됨)

    def draw(self, screen: pygame.Surface, camera):
        if not self.alive:
            return
        
        # 1. 화면 좌표를 먼저 계산합니다.
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        
        # 💡 [최적화 핵심] 동물이 화면을 완전히 벗어났다면 아예 연산(스케일, 회전)을 하지 않고 종료합니다.
        # 여유 공간(margin)을 약 100픽셀 정도 두어 자연스럽게 사라지도록 합니다.
        margin = 100
        if not (-margin < sx < camera.screen_w + margin and -margin < sy < camera.screen_h + margin):
            return

        if self.image:
            # 만약 이미지가 정상적으로 로드되었다면 이미지로 그림
            # 화면 좌표 계산
            sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
            
            # 💡 [핵심 수정] 이미지의 현재 가로, 세로 길이에 각각 카메라 줌 비율을 곱해줍니다!
            new_w = int(self.image.get_width() * camera.zoom)
            new_h = int(self.image.get_height() * camera.zoom)
                
            # 비율이 유지된 채로 줌인/줌아웃 되도록 스케일링
            scaled_image = pygame.transform.scale(self.image, (new_w, new_h))
            scaled_image = pygame.transform.flip(scaled_image, True, False) # 뱀장어는 이미지 바라보는 방향이 반대라 좌우 반전
            scaled_image = pygame.transform.rotate(scaled_image, 20) # 뱀장어는 살짝 기울어져 있음

            # 💡 2. 진행 방향(facing_angle)을 기준으로 회전 적용
            angle_deg = math.degrees(-self.facing_angle)
            rotated_image = pygame.transform.rotate(scaled_image, angle_deg)
                
            # 이미지 출력 (중심점 맞추기)
            rect = rotated_image.get_rect(center=(sx, sy))
            screen.blit(rotated_image, rect)
                
            # 체력바 렌더링
            hp_ratio = self.hp / self.max_hp
            bar_w = 30 * camera.zoom
            bar_h = 4 * camera.zoom
            # 체력바 위치도 이미지 세로 크기에 맞춰 유동적으로 조절
            pygame.draw.rect(screen, (220, 60, 60), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w, bar_h))
            pygame.draw.rect(screen, (100, 220, 120), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w * hp_ratio, bar_h))
        else:
            # 이미지 로드 실패 시 기본 원으로 그리기(부모 클래스)
            super().draw(screen, camera)

    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        """
        [계획서 사양 구현] 지상 포식자 공격은 80% 확률로 자동 회피합니다.
        """
        if attacker and attacker.alive:
            is_ground_predator = not getattr(attacker, 'can_fly', False) and getattr(attacker, 'environment_status', 'land') != 'water'
            if is_ground_predator and random.random() < 0.80:
                print(f"🐒 [{self.name}]가 지상 포식자 {attacker.name}의 습격을 가볍게 백덤블링으로 피했습니다! (80% 회피 작동)")
                return
        super().take_damage(amount, source)

    def climb(self, tree):
        if tree and not tree.broken:
            self.on_tree = True
            self.current_tree = tree
            self.coordinate = list(tree.coordinate)
            self.environment_status = "tree"
            self.stop_fleeing()
            self.target_coord = None
            print(f"🐒 [{self.name}]가 {tree.tree_type} 나무 꼭대기로 도망쳤습니다.")

    def fall_from_tree(self):
        self.on_tree = False
        self.current_tree = None
        self.environment_status = "land"
        self.take_damage(15.0, source="falling")
        self.apply_stun(2.0)
        print(f"🐒 [{self.name}]가 추락 부상을 입고 충격으로 기절했습니다!")

    def throw_fruit(self, target: Animal):
        """[계획서 사양 구현] 포식자에게 과일을 던져 기절시키고 사냥을 강제 중단시킵니다."""
        if self.inventory > 0 and target.alive and self.throw_cooldown <= 0:
            self.inventory -= 1
            self.throw_cooldown = 2.0  # 무한 투척 방지 쿨타임
            print(f"🐒 [{self.name}]가 조준하여 포식자 {target.name}의 머리에 단단한 야생 과일을 던졌습니다!")
            target.apply_stun(2.0)               
            target.use_stamina(15.0)
            if hasattr(target, 'stop_hunt'):
                target.stop_hunt()

    def react_to_predator(self, dt: float, predators: List[Animal], game_map):
        closest_predator = min(predators, key=lambda p: self.distance_to(p))
        dist = self.distance_to(closest_predator)

        # 멀리 있는 포식자 견제 및 방해 (사거리: 60 ~ 180)
        if self.inventory > 0 and 60.0 < dist < 180.0:
            if random.random() < 0.08:  
                self.throw_fruit(closest_predator)

        # 포식자가 일정 거리 이하로 인접했을 때의 대처
        if not self.on_tree:
            if dist <= 60.0:
                trees = game_map.get_trees_in_canopy(self.coordinate[0], self.coordinate[1])
                if trees and random.random() < 0.8:
                    self.climb(trees[0])
                else:
                    self.flee_from(closest_predator, dt)
            else:
                self.flee_from(closest_predator, dt)
        else:
            # 나무 위에 앉아 있는 상태라면 근접한 포식자에게 과일 투척
            if dist <= 100.0 and self.inventory > 0:
                self.throw_fruit(closest_predator)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        Animal.update(self, dt, game_map, weather, animals)
        if not self.alive or self.is_stunned:
            return

        if self.throw_cooldown > 0:
            self.throw_cooldown -= dt

        # [계획서 사양 구현] 나무가 부서지면 낙하 처리
        if self.on_tree and self.current_tree and self.current_tree.broken:
            self.fall_from_tree()

        predators = self.detect_predators(animals, game_map)
        if predators:
            self.react_to_predator(dt, predators, game_map)
            self.target_coord = None
        else:
            # Lee_animals.py - Monkey 클래스 update 메서드 하단 배회 부분
            if not self.on_tree:
                # 🍎 [추가] 사과 탐색 및 섭취 로직
                if self.hunger > 30.0 and game_map.apples:
                    closest_apple = min(game_map.apples, key=lambda a: self.distance_to((a.x, a.y)), default=None)
                    if closest_apple and self.distance_to((closest_apple.x, closest_apple.y)) < self.vision_range:
                        if self.distance_to((closest_apple.x, closest_apple.y)) < 25.0:
                            print(f"🍎 [{self.name}]가 사과를 잽싸게 주워 먹었습니다!")
                            self.eat(closest_apple.heal_amount)
                            game_map.apples.remove(closest_apple)
                            self.target_coord = None
                        else:
                            self.target_coord = [closest_apple.x, closest_apple.y]
                            self.move(dt, self.target_coord, speed_multiplier=0.9)
                        return
                self.wander_timer -= dt
                if self.wander_timer <= 0 or not self.target_coord:
                    self.wander_timer = random.uniform(3.0, 6.0)
                    nearby_trees = [t for t in game_map.trees if not t.broken and self.distance_to(t.coordinate) < 400.0]
                    
                    # 60% 확률로 주변 나무를 목표로, 40% 확률로 자유 배회
                    if nearby_trees and random.random() < 0.6:
                        self.target_coord = list(random.choice(nearby_trees).coordinate)
                    else:
                        rx = self.coordinate[0] + random.uniform(-250.0, 250.0)
                        ry = self.coordinate[1] + random.uniform(-250.0, 250.0)
                        rx = max(50.0, min(float(game_map.pixel_width - 50.0), rx))
                        ry = max(50.0, min(float(game_map.pixel_height - 50.0), ry))
                        self.target_coord = [rx, ry]
                
                self.move(dt, self.target_coord, speed_multiplier=0.75)
                
                trees = game_map.get_trees_in_canopy(self.coordinate[0], self.coordinate[1])
                if trees and random.random() < 0.05:
                    self.climb(trees[0])
            else:
                # 나무 위 휴식 중: 스태미나 고속 회복 및 일정 간격으로 야생 과일 채집
                self.recover_stamina(dt, rate=20.0)
                if random.random() < 0.06 * dt:
                    self.inventory = min(10, self.inventory + 1)
                
                # 심각하게 배고파지면 나무 밑으로 하강
                if self.hunger > 70 and random.random() < 0.02 * dt:
                    self.on_tree = False
                    self.current_tree = None
                    self.environment_status = "land"
                    print(f"🐒 [{self.name}]가 먹이를 구하러 지상으로 내려왔습니다.")


# ==========================================
# 3. 앵무새 (Parrot)
# ==========================================
class Parrot(FlyingAnimal, Prey):
    SPECIES_VISION_RANGE = 400.0  
    SPECIES_VISION_ANGLE = 360.0
    minimap_color = (255, 50, 50)  # 미니맵에 표시할 밝은 빨간색

    def __init__(self, name: str, coordinate: Tuple[float, float], **kwargs):
        super().__init__(name, coordinate, danger_range=250.0, **kwargs)
        self.alert_range = 300.0
        self.max_speed = 70.0 
        self.flying_speed = 180.0
        
        self.target_coord: Optional[List[float]] = None
        self.wander_timer = 0.0
        self.alert_cooldown = 0.0

        # 💡 1. 여기서 앵무새 전용 이미지를 설정
        self.image_path = "parrot.png"  # 앵무새 이미지 파일명
        self.image = None
        
        # 이미지가 캐시에 없으면 최초 1회 로드
        if self.image_path not in Lee:
            try:
                loaded_img = pygame.image.load(self.image_path).convert_alpha()
                Lee[self.image_path] = loaded_img
            except Exception as e:
                print(f"⚠️ {name} 이미지 로드 실패: {e}")
                # 💡 [핵심] 실패하더라도 딕셔너리에 None을 넣어줘야함
                Lee[self.image_path] = None
        orig_img = Lee[self.image_path]
        if orig_img is not None:
            orig_w, orig_h = orig_img.get_size() # 원본 이미지의 가로, 세로 픽셀
                
            # 동물의 크기(size)를 기준으로 최대 렌더링 크기 설정
            target_max_size = int(self.size * 2.5)
                
            # 가로와 세로 중 더 긴 쪽을 기준으로 축소/확대 비율(scale_factor)을 계산
            scale_factor = target_max_size / max(orig_w, orig_h)
                
            # 구한 비율을 가로, 세로에 똑같이 곱해주어 비율 유지
            new_w = int(orig_w * scale_factor)
            new_h = int(orig_h * scale_factor)
                
            # 새로운 가로, 세로 크기로 스케일링
            self.image = pygame.transform.scale(orig_img, (new_w, new_h))
        else:
            self.image = None # 이미지가 없으면 None으로 유지 (draw 메서드에서 부모의 원형 그리기로 대체됨)

    def draw(self, screen: pygame.Surface, camera):
        if not self.alive:
            return
        # 1. 화면 좌표를 먼저 계산합니다.
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        
        # 💡 [최적화 핵심] 동물이 화면을 완전히 벗어났다면 아예 연산(스케일, 회전)을 하지 않고 종료합니다.
        # 여유 공간(margin)을 약 100픽셀 정도 두어 자연스럽게 사라지도록 합니다.
        margin = 100
        if not (-margin < sx < camera.screen_w + margin and -margin < sy < camera.screen_h + margin):
            return

        if self.image:
            # 만약 이미지가 정상적으로 로드되었다면 이미지로 그림
            # 화면 좌표 계산
            sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
            
            # 💡 [핵심 수정] 이미지의 현재 가로, 세로 길이에 각각 카메라 줌 비율을 곱해줍니다!
            new_w = int(self.image.get_width() * camera.zoom)
            new_h = int(self.image.get_height() * camera.zoom)
                
            # 비율이 유지된 채로 줌인/줌아웃 되도록 스케일링
            scaled_image = pygame.transform.scale(self.image, (new_w, new_h))
            scaled_image = pygame.transform.flip(scaled_image, True, False) # 뱀장어는 이미지 바라보는 방향이 반대라 좌우 반전
            scaled_image = pygame.transform.rotate(scaled_image, 20) # 뱀장어는 살짝 기울어져 있음

            # 💡 2. 진행 방향(facing_angle)을 기준으로 회전 적용
            angle_deg = math.degrees(-self.facing_angle)
            rotated_image = pygame.transform.rotate(scaled_image, angle_deg)
                
            # 이미지 출력 (중심점 맞추기)
            rect = rotated_image.get_rect(center=(sx, sy))
            screen.blit(rotated_image, rect)
                
            # 체력바 렌더링
            hp_ratio = self.hp / self.max_hp
            bar_w = 30 * camera.zoom
            bar_h = 4 * camera.zoom
            # 체력바 위치도 이미지 세로 크기에 맞춰 유동적으로 조절
            pygame.draw.rect(screen, (220, 60, 60), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w, bar_h))
            pygame.draw.rect(screen, (100, 220, 120), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w * hp_ratio, bar_h))
        else:
            # 이미지 로드 실패 시 기본 원으로 그리기(부모 클래스)
            super().draw(screen, camera)

    def make_alert_sound(self, animals: List[Animal]):
        """[계획서 사양 구현] 포식자 탐색 후 주변 동물들에게 알람을 보내 스피드 증가 및 스태미나를 보충해줍니다."""
        if self.alert_cooldown <= 0:
            self.alert_cooldown = 6.0  # 알람 간격 제한
            print(f"🦜 [{self.name}]가 크고 날카로운 경고 비명을 지릅니다! 근처 동물들의 이동 속도가 증가합니다!")
            
            for animal in animals:
                if animal is not self and animal.alive and self.distance_to(animal) <= self.alert_range:
                    if isinstance(animal, Prey):
                        # 스태미나 긴급 주입 및 도주 본능 자극
                        animal.recover_stamina(1.0, rate=60.0)
                        animal.predator_detected = True 
                        
                        # 일시적인 도망 전용 가속 버프 타이머 부여 (이미 존재하지 않을 때만 중첩 제한으로 작동)
                        if not hasattr(animal, 'speed_boost_timer'):
                            animal.speed_boost_timer = 5.0
                            animal.max_speed *= 1.35  # 이동 속도 35% 증폭
                            print(f"  ⚡ [{animal.name}]이(가) 공중 경보를 전해 듣고 가속 버프를 얻어 기민하게 움직입니다!")

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        if self.alert_cooldown > 0:
            self.alert_cooldown -= dt

        # 버프가 걸린 대상 동물들의 속도를 제한 시간 경과 후 정상으로 돌려놓는 스케줄링 처리
        for animal in animals:
            if hasattr(animal, 'speed_boost_timer'):
                animal.speed_boost_timer -= dt
                if animal.speed_boost_timer <= 0:
                    animal.max_speed /= 1.35
                    delattr(animal, 'speed_boost_timer')
                    print(f"  🐢 [{animal.name}]의 앵무새 경고 가속 버프가 만료되었습니다.")

        # FlyingAnimal의 비행/활공 물리학 및 에너지를 유지하기 위해 부모 업데이트 실행
        FlyingAnimal.update(self, dt, game_map, weather, animals)
        
        if not self.alive or self.is_stunned:
            return

        predators = self.detect_predators(animals, game_map)
        if predators:
            closest = min(predators, key=lambda p: self.distance_to(p))
            if self.distance_to(closest) < self.danger_range:
                self.flee_from(closest, dt)
                if random.random() < 0.15: 
                    self.make_alert_sound(animals)
            self.target_coord = None
        else:
            # 🍎 [추가] 사과 탐색 및 섭취 로직
            if self.hunger > 30.0 and game_map.apples:
                closest_apple = min(game_map.apples, key=lambda a: self.distance_to((a.x, a.y)), default=None)
                if closest_apple and self.distance_to((closest_apple.x, closest_apple.y)) < self.vision_range:
                    if self.distance_to((closest_apple.x, closest_apple.y)) < 25.0:
                        print(f"🍎 [{self.name}]가 날아와서 사과를 쪼아 먹었습니다!")
                        self.eat(closest_apple.heal_amount)
                        game_map.apples.remove(closest_apple)
                        self.target_coord = None
                    else:
                        self.target_coord = [closest_apple.x, closest_apple.y]
                        self.move(dt, self.target_coord, speed_multiplier=1.0)
                    return
            # Lee_animals.py - Parrot 클래스 update 메서드 하단 배회 부분
            self.wander_timer -= dt
            if self.wander_timer <= 0 or not self.target_coord:
                self.wander_timer = random.uniform(4.0, 7.5)
                rx = self.coordinate[0] + random.uniform(-400.0, 400.0)
                ry = self.coordinate[1] + random.uniform(-400.0, 400.0)
                
                # 맵 이탈 완전 봉쇄
                rx = max(50.0, min(float(game_map.pixel_width - 50.0), rx))
                ry = max(50.0, min(float(game_map.pixel_height - 50.0), ry))
                self.target_coord = [rx, ry]
            
            self.move(dt, self.target_coord)
            if self.distance_to(self.target_coord) < 15.0:
                self.target_coord = None