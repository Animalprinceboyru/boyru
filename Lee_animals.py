import random
import pygame
import math
from typing import Tuple, List, Optional
from animal import Animal, Prey, TILE_SIZE
import camera 

try: from Choi_animals import FlyingAnimal
except ImportError: FlyingAnimal = Animal 

Lee = {}

# ==========================================
# 1. 카피바라 (Capybara)
# ==========================================
class Capybara(Prey):
    SPECIES_VISION_RANGE = 700.0
    SPECIES_VISION_ANGLE = 270.0
    minimap_color = (210, 180, 140)

    def __init__(self, name: str, coordinate: Tuple[float, float], **kwargs):
        super().__init__(name, coordinate, danger_range=150.0, **kwargs)
        self.stress_level = 0.0
        self.group_size = 1
        self.max_hp = 200
        self.max_speed = 90.0
        self.escape_success_rate = 0.5
        self.target_coord: Optional[List[float]] = None
        self.wander_timer = 0.0

        self.image_path = "capybara.png"
        self.image = None
        if self.image_path not in Lee:
            try: Lee[self.image_path] = pygame.image.load(self.image_path).convert_alpha()
            except Exception: Lee[self.image_path] = None
        orig_img = Lee[self.image_path]
        if orig_img is not None:
            orig_w, orig_h = orig_img.get_size()
            scale_factor = int(self.size * 2.5) / max(orig_w, orig_h)
            self.image = pygame.transform.scale(orig_img, (int(orig_w * scale_factor), int(orig_h * scale_factor)))

    def draw(self, screen: pygame.Surface, camera):
        if not self.alive: return
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        margin = 100
        if not (-margin < sx < camera.screen_w + margin and -margin < sy < camera.screen_h + margin): return

        if self.image:
            if not hasattr(self.__class__, '_shared_img_cache'): self.__class__._shared_img_cache = {}
            zoom_key = round(camera.zoom, 2)
            angle_deg = math.degrees(-self.facing_angle)
            angle_key = int(angle_deg / 5) * 5 
            is_hidden = getattr(self, 'is_hiding', False)
            cache_key = (zoom_key, angle_key, is_hidden)
            if cache_key not in self.__class__._shared_img_cache:
                new_w, new_h = int(self.image.get_width() * camera.zoom), int(self.image.get_height() * camera.zoom)
                scaled = pygame.transform.scale(self.image, (new_w, new_h))
                final_rotated = pygame.transform.rotate(scaled, angle_key)
                if is_hidden: final_rotated.set_alpha(110)
                self.__class__._shared_img_cache[cache_key] = final_rotated
            final_image = self.__class__._shared_img_cache[cache_key]
            rect = final_image.get_rect(center=(sx, sy))
            screen.blit(final_image, rect)
            hp_ratio = self.hp / self.max_hp
            bar_w, bar_h = 30 * camera.zoom, 4 * camera.zoom
            new_h = int(self.image.get_height() * camera.zoom)
            pygame.draw.rect(screen, (220, 60, 60), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w, bar_h))
            pygame.draw.rect(screen, (100, 220, 120), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w * hp_ratio, bar_h))
        else: super().draw(screen, camera)

    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        evade_chance = min(0.60, 0.12 * (self.group_size - 1))
        if evade_chance > 0 and random.random() < evade_chance:
            print(f"🛡️ [{self.name}]가 무리 방어 버프(방어 확률: {evade_chance:.1%})로 포식자의 공격을 무력화했습니다!")
            return
        super().take_damage(amount, source, attacker)

    def socialize(self, animals: List[Animal]):
        nearby_capybaras = [a for a in animals if isinstance(a, Capybara) and a is not self and a.alive and self.distance_to(a) < 120.0]
        self.group_size = 1 + len(nearby_capybaras)
        if self.group_size > 1:
            self.stress_level = max(0.0, self.stress_level - 1.5)
            self.escape_success_rate = min(0.95, 0.5 + 0.1 * len(nearby_capybaras))

    def flee_to_water(self, game_map, dt: float, predator: Animal):
        tx, ty = int(self.coordinate[0] // TILE_SIZE), int(self.coordinate[1] // TILE_SIZE)
        water_target, min_dist, search_radius = None, float('inf'), 8
        for dy in range(-search_radius, search_radius + 1):
            for dx in range(-search_radius, search_radius + 1):
                nx, ny = tx + dx, ty + dy
                if 0 <= nx < game_map.map_width and 0 <= ny < game_map.map_height:
                    if game_map.is_water(nx, ny):
                        dist = dx*dx + dy*dy
                        if dist < min_dist:
                            min_dist = dist
                            water_target = (nx * TILE_SIZE + TILE_SIZE/2, ny * TILE_SIZE + TILE_SIZE/2)
        if water_target: self.move(dt, water_target, self.flee_speed_mul * self.escape_success_rate)
        else: self.flee_from(predator, dt)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        Animal.update(self, dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: return
        
        self.socialize(animals)
        predators = self.detect_predators(animals, game_map)
        if predators:
            self.predator_detected = True
            self.stress_level = min(100.0, self.stress_level + 12.0 * dt)
            closest = min(predators, key=lambda p: self.distance_to(p))
            if getattr(self, 'environment_status', '') == 'water':
                if random.random()<0.1: self.flee_from(closest, dt)
            else: self.flee_to_water(game_map, dt, closest)
            self.target_coord = None
        else:
            self.predator_detected = False
            self.stress_level = max(0.0, self.stress_level - 6.0 * dt)
            
            # 💡 [추가] 집 찾기 로직
            if self.try_return_home(dt):
                self.target_coord = None
                return

            if self.hunger > 30.0 and game_map.apples:
                closest_apple = min(game_map.apples, key=lambda a: self.distance_to((a.x, a.y)), default=None)
                if closest_apple and self.distance_to((closest_apple.x, closest_apple.y)) < self.vision_range:
                    if self.distance_to((closest_apple.x, closest_apple.y)) < 25.0:
                        print(f"🍎 [{self.name}]가 사과를 오물오물 먹었습니다!")
                        self.eat(closest_apple.heal_amount)
                        if closest_apple in game_map.apples: game_map.apples.remove(closest_apple) # 💡 사과 증발 버그 제거
                        self.target_coord = None
                    else:
                        self.target_coord = [closest_apple.x, closest_apple.y]
                        self.move(dt, self.target_coord, speed_multiplier=0.8)
                    return
            
            self.wander_timer -= dt
            if self.wander_timer <= 0 or not self.target_coord:
                self.wander_timer = random.uniform(3.0, 6.0)
                rx, ry = self.coordinate[0] + random.uniform(-200.0, 200.0), self.coordinate[1] + random.uniform(-200.0, 200.0)
                rx = max(50.0, min(float(game_map.pixel_width - 50.0), rx))
                ry = max(50.0, min(float(game_map.pixel_height - 50.0), ry))
                self.target_coord = [rx, ry]
            
            self.move(dt, self.target_coord, speed_multiplier=0.6)
            if self.distance_to(self.target_coord) < 15.0: self.target_coord = None


# ==========================================
# 2. 원숭이 (Monkey)
# ==========================================
class Monkey(Prey):
    SPECIES_VISION_RANGE = 800.0
    SPECIES_VISION_ANGLE = 200.0
    minimap_color = (139, 69, 19)

    def __init__(self, name: str, coordinate: Tuple[float, float], **kwargs):
        super().__init__(name, coordinate, danger_range=200.0, **kwargs)
        self.on_tree = False
        self.inventory = 5          
        self.throw_power = 20.0
        self.max_hp=120
        self.max_speed = 85.0
        self.current_tree = None
        self.target_coord: Optional[List[float]] = None
        self.wander_timer = 0.0
        self.throw_cooldown = 0.0

        self.image_path = "monkey.png"
        self.image = None
        if self.image_path not in Lee:
            try: Lee[self.image_path] = pygame.image.load(self.image_path).convert_alpha()
            except Exception: Lee[self.image_path] = None
        orig_img = Lee[self.image_path]
        if orig_img is not None:
            orig_w, orig_h = orig_img.get_size()
            scale_factor = int(self.size * 2.5) / max(orig_w, orig_h)
            self.image = pygame.transform.scale(orig_img, (int(orig_w * scale_factor), int(orig_h * scale_factor)))

    def draw(self, screen: pygame.Surface, camera):
        if not self.alive: return
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        margin = 100
        if not (-margin < sx < camera.screen_w + margin and -margin < sy < camera.screen_h + margin): return

        if self.image:
            if not hasattr(self.__class__, '_shared_img_cache'): self.__class__._shared_img_cache = {}
            zoom_key = round(camera.zoom, 2)
            angle_deg = math.degrees(-self.facing_angle)
            angle_key = int(angle_deg / 5) * 5 
            is_hidden = getattr(self, 'is_hiding', False)
            cache_key = (zoom_key, angle_key, is_hidden)
            if cache_key not in self.__class__._shared_img_cache:
                new_w, new_h = int(self.image.get_width() * camera.zoom), int(self.image.get_height() * camera.zoom)
                scaled = pygame.transform.scale(self.image, (new_w, new_h))
                final_rotated = pygame.transform.rotate(scaled, angle_key)
                if is_hidden: final_rotated.set_alpha(110)
                self.__class__._shared_img_cache[cache_key] = final_rotated
            final_image = self.__class__._shared_img_cache[cache_key]
            rect = final_image.get_rect(center=(sx, sy))
            screen.blit(final_image, rect)
            hp_ratio = self.hp / self.max_hp
            bar_w, bar_h = 30 * camera.zoom, 4 * camera.zoom
            new_h = int(self.image.get_height() * camera.zoom)
            pygame.draw.rect(screen, (220, 60, 60), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w, bar_h))
            pygame.draw.rect(screen, (100, 220, 120), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w * hp_ratio, bar_h))
        else: super().draw(screen, camera)

    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        if attacker and attacker.alive:
            is_ground_predator = not getattr(attacker, 'can_fly', False) and getattr(attacker, 'environment_status', 'land') != 'water'
            if is_ground_predator and random.random() < 0.80:
                print(f"🐒 [{self.name}]가 지상 포식자 {attacker.name}의 습격을 가볍게 백덤블링으로 피했습니다! (80% 회피 작동)")
                return
        super().take_damage(amount, source, attacker)

    def climb(self, tree):
        if tree and not tree.broken:
            self.on_tree, self.current_tree = True, tree
            self.coordinate = list(tree.coordinate)
            self.environment_status = "tree"
            self.stop_fleeing(); self.target_coord = None
            print(f"🐒 [{self.name}]가 {tree.tree_type} 나무 꼭대기로 도망쳤습니다.")

    def fall_from_tree(self):
        self.on_tree, self.current_tree, self.environment_status = False, None, "land"
        self.take_damage(15.0, source="falling", attacker=self)
        self.apply_stun(2.0)
        print(f"🐒 [{self.name}]가 추락 부상을 입고 충격으로 기절했습니다!")

    def throw_fruit(self, target: Animal):
        if self.inventory > 0 and target.alive and self.throw_cooldown <= 0:
            self.inventory -= 1
            self.throw_cooldown = 2.0 
            print(f"🐒 [{self.name}]가 조준하여 포식자 {target.name}의 머리에 단단한 야생 과일을 던졌습니다!")
            target.apply_stun(2.0)               
            target.use_stamina(15.0)
            if hasattr(target, 'stop_hunt'): target.stop_hunt()

    def react_to_predator(self, dt: float, predators: List[Animal], game_map):
        closest_predator = min(predators, key=lambda p: self.distance_to(p))
        dist = self.distance_to(closest_predator)
        if self.inventory > 0 and 60.0 < dist < 180.0:
            if random.random() < 0.08: self.throw_fruit(closest_predator)

        if not self.on_tree:
            if dist <= 60.0:
                trees = game_map.get_trees_in_canopy(self.coordinate[0], self.coordinate[1])
                if trees and random.random() < 0.8: self.climb(trees[0])
                else: self.flee_from(closest_predator, dt)
            else: self.flee_from(closest_predator, dt)
        else:
            if dist <= 100.0 and self.inventory > 0: self.throw_fruit(closest_predator)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        Animal.update(self, dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: return
        if self.throw_cooldown > 0: self.throw_cooldown -= dt
        if self.on_tree and self.current_tree and self.current_tree.broken: self.fall_from_tree()

        predators = self.detect_predators(animals, game_map)
        if predators:
            self.react_to_predator(dt, predators, game_map)
            self.target_coord = None
        else:
            if not self.on_tree:
                # 💡 [추가] 집 찾기 로직
                if self.try_return_home(dt):
                    self.target_coord = None
                    return
                    
                if self.hunger > 30.0 and game_map.apples:
                    closest_apple = min(game_map.apples, key=lambda a: self.distance_to((a.x, a.y)), default=None)
                    if closest_apple and self.distance_to((closest_apple.x, closest_apple.y)) < self.vision_range:
                        if self.distance_to((closest_apple.x, closest_apple.y)) < 25.0:
                            print(f"🍎 [{self.name}]가 사과를 잽싸게 주워 먹었습니다!")
                            self.eat(closest_apple.heal_amount)
                            if closest_apple in game_map.apples: game_map.apples.remove(closest_apple) # 💡 사과 증발 버그 제거
                            self.target_coord = None
                        else:
                            self.target_coord = [closest_apple.x, closest_apple.y]
                            self.move(dt, self.target_coord, speed_multiplier=0.9)
                        return
                
                self.wander_timer -= dt
                if self.wander_timer <= 0 or not self.target_coord:
                    self.wander_timer = random.uniform(3.0, 6.0)
                    nearby_trees = [t for t in game_map.trees if not t.broken and self.distance_to(t.coordinate) < 400.0]
                    if nearby_trees and random.random() < 0.6: self.target_coord = list(random.choice(nearby_trees).coordinate)
                    else:
                        rx, ry = self.coordinate[0] + random.uniform(-250.0, 250.0), self.coordinate[1] + random.uniform(-250.0, 250.0)
                        rx = max(50.0, min(float(game_map.pixel_width - 50.0), rx))
                        ry = max(50.0, min(float(game_map.pixel_height - 50.0), ry))
                        self.target_coord = [rx, ry]
                
                self.move(dt, self.target_coord, speed_multiplier=0.75)
                trees = game_map.get_trees_in_canopy(self.coordinate[0], self.coordinate[1])
                if trees and random.random() < 0.05: self.climb(trees[0])
            else:
                self.recover_stamina(dt, rate=20.0)
                if random.random() < 0.06 * dt: self.inventory = min(10, self.inventory + 1)
                if self.hunger > 70 and random.random() < 0.02 * dt:
                    self.on_tree, self.current_tree, self.environment_status = False, None, "land"
                    print(f"🐒 [{self.name}]가 먹이를 구하러 지상으로 내려왔습니다.")


# ==========================================
# 3. 앵무새 (Parrot)
# ==========================================
class Parrot(FlyingAnimal, Prey):
    SPECIES_VISION_RANGE = 1200.0  
    SPECIES_VISION_ANGLE = 300.0
    minimap_color = (255, 50, 50)

    def __init__(self, name: str, coordinate: Tuple[float, float], **kwargs):
        super().__init__(name, coordinate, danger_range=250.0, **kwargs)
        self.alert_range = 300.0
        self.flying_speed = 180.0
        self.max_hp=60
        self.max_speed=100
        self.target_coord: Optional[List[float]] = None
        self.wander_timer = 0.0
        self.alert_cooldown = 0.0

        self.image_path = "parrot.png"
        self.image = None
        if self.image_path not in Lee:
            try: Lee[self.image_path] = pygame.image.load(self.image_path).convert_alpha()
            except Exception: Lee[self.image_path] = None
        orig_img = Lee[self.image_path]
        if orig_img is not None:
            orig_w, orig_h = orig_img.get_size()
            scale_factor = int(self.size * 2.5) / max(orig_w, orig_h)
            self.image = pygame.transform.scale(orig_img, (int(orig_w * scale_factor), int(orig_h * scale_factor)))

    def draw(self, screen: pygame.Surface, camera):
        if not self.alive: return
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        margin = 100
        if not (-margin < sx < camera.screen_w + margin and -margin < sy < camera.screen_h + margin): return

        if self.image:
            if not hasattr(self.__class__, '_shared_img_cache'): self.__class__._shared_img_cache = {}
            zoom_key = round(camera.zoom, 2)
            angle_deg = math.degrees(-self.facing_angle)
            angle_key = int(angle_deg / 5) * 5 
            is_hidden = getattr(self, 'is_hiding', False)
            cache_key = (zoom_key, angle_key, is_hidden)
            if cache_key not in self.__class__._shared_img_cache:
                new_w, new_h = int(self.image.get_width() * camera.zoom), int(self.image.get_height() * camera.zoom)
                scaled = pygame.transform.scale(self.image, (new_w, new_h))
                final_rotated = pygame.transform.rotate(scaled, angle_key)
                if is_hidden: final_rotated.set_alpha(110)
                self.__class__._shared_img_cache[cache_key] = final_rotated
            final_image = self.__class__._shared_img_cache[cache_key]
            rect = final_image.get_rect(center=(sx, sy))
            screen.blit(final_image, rect)
            hp_ratio = self.hp / self.max_hp
            bar_w, bar_h = 30 * camera.zoom, 4 * camera.zoom
            new_h = int(self.image.get_height() * camera.zoom)
            pygame.draw.rect(screen, (220, 60, 60), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w, bar_h))
            pygame.draw.rect(screen, (100, 220, 120), (sx - bar_w/2, sy - (new_h/2) - 10, bar_w * hp_ratio, bar_h))
        else: super().draw(screen, camera)

    def make_alert_sound(self, animals: List[Animal]):
        if self.alert_cooldown <= 0:
            self.alert_cooldown = 6.0 
            print(f"🦜 [{self.name}]가 크고 날카로운 경고 비명을 지릅니다! 근처 동물들의 이동 속도가 증가합니다!")
            for animal in animals:
                if animal is not self and animal.alive and self.distance_to(animal) <= self.alert_range:
                    if isinstance(animal, Prey):
                        animal.recover_stamina(1.0, rate=60.0)
                        animal.predator_detected = True 
                        if not hasattr(animal, 'speed_boost_timer'):
                            animal.speed_boost_timer = 5.0
                            animal.max_speed *= 1.35 
                            print(f"  ⚡ [{animal.name}]이(가) 공중 경보를 전해 듣고 가속 버프를 얻어 기민하게 움직입니다!")

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        if self.alert_cooldown > 0: self.alert_cooldown -= dt
        
        # 💡 [핵심 수정] 여기서 모든 동물의 버프 타이머를 삭제하던 끔찍한 연산을 제거했습니다.
        # 타이머 증발 버그는 이걸 지우고 animal.py의 본인 업데이트에서 타이머를 깎게 만들어 완벽히 해결했습니다.

        FlyingAnimal.update(self, dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: return

        predators = self.detect_predators(animals, game_map)
        if predators:
            closest = min(predators, key=lambda p: self.distance_to(p))
            if self.distance_to(closest) < self.danger_range:
                self.flee_from(closest, dt)
                if random.random() < 0.15: self.make_alert_sound(animals)
            self.target_coord = None
        else:
            # 💡 [추가] 집 찾기 로직
            if self.try_return_home(dt):
                self.target_coord = None
                return
                
            if self.hunger > 30.0 and game_map.apples:
                closest_apple = min(game_map.apples, key=lambda a: self.distance_to((a.x, a.y)), default=None)
                if closest_apple and self.distance_to((closest_apple.x, closest_apple.y)) < self.vision_range:
                    if self.distance_to((closest_apple.x, closest_apple.y)) < 25.0:
                        print(f"🍎 [{self.name}]가 날아와서 사과를 쪼아 먹었습니다!")
                        self.eat(closest_apple.heal_amount)
                        if closest_apple in game_map.apples: game_map.apples.remove(closest_apple) # 💡 사과 증발 버그 제거
                        self.target_coord = None
                    else:
                        self.target_coord = [closest_apple.x, closest_apple.y]
                        self.move(dt, self.target_coord, speed_multiplier=1.0)
                    return
            
            self.wander_timer -= dt
            if self.wander_timer <= 0 or not self.target_coord:
                self.wander_timer = random.uniform(4.0, 7.5)
                rx, ry = self.coordinate[0] + random.uniform(-400.0, 400.0), self.coordinate[1] + random.uniform(-400.0, 400.0)
                rx = max(50.0, min(float(game_map.pixel_width - 50.0), rx))
                ry = max(50.0, min(float(game_map.pixel_height - 50.0), ry))
                self.target_coord = [rx, ry]
            
            self.move(dt, self.target_coord)
            if self.distance_to(self.target_coord) < 15.0: self.target_coord = None