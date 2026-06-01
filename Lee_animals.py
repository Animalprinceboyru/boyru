import random
from typing import Tuple, List
from base_classes import Animal, Prey  # Animal, Prey 클래스 불러오기

TILE_SIZE = 32  # 타일 사이즈 고정

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
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned:
            return
        
        self.socialize(animals)
        
        if self.predator_detected:
            self.stress_level = min(100.0, self.stress_level + 10.0 * dt)
            self.flee_to_water(game_map, dt)
        else:
            self.stress_level = max(0.0, self.stress_level - 5.0 * dt)

import random
from typing import Tuple, List
from base_classes import Animal, Prey  # 부모 클래스 불러오기

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

    def react_to_predator(self, predators: List[Animal], game_map):
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
                self.flee_from(closest_predator, 0.1)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned:
            return

        if self.on_tree and self.current_tree and self.current_tree.broken:
            self.fall_from_tree()

        predators = self.detect_predators(animals, game_map)
        if predators:
            self.react_to_predator(predators, game_map)
        
        if self.on_tree:
            self.recover_stamina(dt, rate=20.0)
            if random.random() < 0.02 * dt:
                self.inventory = min(10, self.inventory + 1)
4. parrot.py (앵무새)
앵무새는 Animal이 아니라 위에서 만든 FlyingAnimal을 상속받아야 합니다.
code
Python
import random
from typing import Tuple, List
from base_classes import Animal, Prey  # Animal, Prey 불러오기
from flying_animal import FlyingAnimal # 1번에서 만든 비행 동물 클래스 불러오기

class Parrot(FlyingAnimal):
    SPECIES_VISION_RANGE = 400.0  
    SPECIES_VISION_ANGLE = 360.0

    def __init__(self, name: str, coordinate: Tuple[float, float], **kwargs):
        super().__init__(name, coordinate, flying_speed=180.0, danger_range=250.0, **kwargs)
        self.alert_range = 300.0
        self.max_speed = 70.0 
        
        self.fly()

    def make_alert_sound(self, animals: List[Animal]):
        print(f"🦜 {self.name}가 포식자 발견 경고음을 냅니다!!")
        for animal in animals:
            if animal is not self and animal.alive and self.distance_to(animal) <= self.alert_range:
                if isinstance(animal, Prey):
                    animal.recover_stamina(1.0, rate=50.0)
                    animal.predator_detected = True 

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        self.fly() 
        super().update(dt, game_map, weather, animals)
        
        if not self.alive or self.is_stunned:
            return

        predators = self.detect_predators(animals, game_map)
        if predators:
            closest = min(predators, key=lambda p: self.distance_to(p))
            
            if self.distance_to(closest) < self.danger_range:
                self.flee_from(closest, dt)
                
                if random.random() < 0.05: 
                    self.make_alert_sound(animals)