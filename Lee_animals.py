import random
from typing import Tuple, List

# base_classes 대신 실제 파일인 animal에서 import
from animal import Animal, Prey, TILE_SIZE 

# ==========================================
# 1. 카피바라 (Capybara)
# ==========================================
class Capybara(Prey):
    SPECIES_VISION_RANGE = 200.0
    SPECIES_VISION_ANGLE = 270.0

    def __init__(self, name: str, coordinate: Tuple[float, float], **kwargs):
        super().__init__(name, coordinate, danger_range=150.0, escape_success_rate=0.5, **kwargs)
        self.stress_level = 0.0
        self.group_size = 1
        
        self.max_hp = 120
        self.hp = 120
        self.max_speed = 60.0

    def socialize(self, animals: List[Animal]):
        """주변의 카피바라와 모여 그룹 사이즈를 늘리고 생존율(방어 버프)을 높입니다."""
        nearby_capybaras = [
            a for a in animals 
            if isinstance(a, Capybara) and a is not self and a.alive and self.distance_to(a) < 100.0
        ]
        self.group_size = 1 + len(nearby_capybaras)
        
        if self.group_size > 1:
            self.stress_level = max(0.0, self.stress_level - 1.0)
            self.escape_success_rate = min(0.95, 0.5 + 0.1 * len(nearby_capybaras))

    def flee_to_water(self, game_map, dt: float):
        """가까운 물가 방향을 찾아 우선적으로 도망칩니다."""
        tx, ty = int(self.coordinate[0] // TILE_SIZE), int(self.coordinate[1] // TILE_SIZE)
        
        water_target = None
        min_dist = float('inf')
        search_radius = 6
        
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
            self.move(dt, water_target, self._flee_speed_mul * self.escape_success_rate)
        else:
            self.move(dt)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        # Prey.update를 부르면 이중 이동이 발생하므로 Animal.update를 호출
        Animal.update(self, dt, game_map, weather, animals)
        if not self.alive or self.is_stunned:
            return
        
        self.socialize(animals)
        predators = self.detect_predators(animals, game_map)
        
        if predators:
            self.predator_detected = True
            self.stress_level = min(100.0, self.stress_level + 10.0 * dt)
            self.flee_to_water(game_map, dt)
        else:
            self.predator_detected = False
            self.stress_level = max(0.0, self.stress_level - 5.0 * dt)
            self.move(dt) # 평상시 이동 추가


# ==========================================
# 2. 원숭이 (Monkey)
# ==========================================
class Monkey(Prey):
    SPECIES_VISION_RANGE = 250.0
    SPECIES_VISION_ANGLE = 200.0

    def __init__(self, name: str, coordinate: Tuple[float, float], **kwargs):
        super().__init__(name, coordinate, danger_range=200.0, **kwargs)
        self.on_tree = False
        self.inventory = 5          
        self.throw_power = 20.0     
        self.max_speed = 85.0
        self.current_tree = None

    def climb(self, tree):
        if tree and not tree.broken:
            self.on_tree = True
            self.current_tree = tree
            self.coordinate = list(tree.coordinate)
            self.environment_status = "tree"
            self.stop_fleeing()

    def fall_from_tree(self):
        self.on_tree = False
        self.current_tree = None
        self.environment_status = "land"
        self.take_damage(15.0, source="falling")
        self.apply_stun(2.0)

    def throw_fruit(self, target: Animal):
        if self.inventory > 0 and target.alive:
            self.inventory -= 1
            print(f"🐒 {self.name}가 {target.name}에게 과일을 던졌습니다!")
            target.apply_stun(1.5)               
            target.use_stamina(15.0)

    # 파라미터에 dt 추가
    def react_to_predator(self, dt: float, predators: List[Animal], game_map):
        closest_predator = min(predators, key=lambda p: self.distance_to(p))
        dist = self.distance_to(closest_predator)

        if self.inventory > 0 and 50 < dist < 150:
            if random.random() < 0.05:
                self.throw_fruit(closest_predator)

        if dist <= 50 and not self.on_tree:
            trees = game_map.get_trees_in_canopy(self.coordinate[0], self.coordinate[1])
            if trees and random.random() < 0.8:
                self.climb(trees[0])
            else:
                self.flee_from(closest_predator, dt) # 0.1 상수 대신 dt 사용
        elif not self.on_tree:
            self.flee_from(closest_predator, dt)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        Animal.update(self, dt, game_map, weather, animals)
        if not self.alive or self.is_stunned:
            return

        if self.on_tree and self.current_tree and self.current_tree.broken:
            self.fall_from_tree()

        predators = self.detect_predators(animals, game_map)
        if predators:
            self.react_to_predator(dt, predators, game_map)
        else:
            if not self.on_tree:
                self.move(dt) # 나무 위에 없을 때 기본 이동
        
        if self.on_tree:
            self.recover_stamina(dt, rate=20.0)
            if random.random() < 0.02 * dt:
                self.inventory = min(10, self.inventory + 1)


# ==========================================
# 3. 앵무새 (Parrot)
# ==========================================
# 최강빈 조원이 만든 클래스가 choi_animals.py 에 있다고 가정
try:
    from choi_animals import FlyingAnimal
except ImportError:
    # FlyingAnimal이 없을 경우 오류를 막기 위해 Animal 상속으로 임시 대체
    FlyingAnimal = Animal 

class Parrot(FlyingAnimal, Prey):
    SPECIES_VISION_RANGE = 400.0  
    SPECIES_VISION_ANGLE = 360.0

    def __init__(self, name: str, coordinate: Tuple[float, float], **kwargs):
        super().__init__(name, coordinate, danger_range=250.0, **kwargs)
        self.alert_range = 300.0
        self.max_speed = 70.0 
        
        # __init__에서의 self.fly()는 dt 인자가 없어 오류를 유발하므로 삭제했습니다.
        if hasattr(self, 'flying_speed'):
            self.flying_speed = 180.0

    def make_alert_sound(self, animals: List[Animal]):
        print(f"🦜 {self.name}가 포식자 발견 경고음을 냅니다!!")
        for animal in animals:
            if animal is not self and animal.alive and self.distance_to(animal) <= self.alert_range:
                if isinstance(animal, Prey):
                    animal.recover_stamina(1.0, rate=50.0)
                    animal.predator_detected = True 

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        # 다중 상속 버그 방지를 위해 Animal.update 호출
        Animal.update(self, dt, game_map, weather, animals)
        
        if not self.alive or self.is_stunned:
            return

        predators = self.detect_predators(animals, game_map)
        if predators:
            closest = min(predators, key=lambda p: self.distance_to(p))
            if self.distance_to(closest) < self.danger_range:
                self.flee_from(closest, dt)
                
                if random.random() < 0.05: 
                    self.make_alert_sound(animals)
        else:
            # 포식자가 없을 때 비행하며 이동
            if hasattr(self, 'fly'):
                self.fly(dt)
            else:
                self.move(dt)