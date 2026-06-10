import pygame
import random
import math
from typing import Tuple, Optional, List
from animal import Animal, Predator, Prey, Egg
import camera
from map_system import TileType

CHOI_IMAGE_CACHE={}

# ==========================================
# 1. 비행 동물 부모 클래스 (앵무새, 모기 등의 부모)
# ==========================================
class FlyingAnimal(Prey):
    SPECIES_VISION_RANGE: float = 200.0
    SPECIES_VISION_ANGLE: float = 160.0
    HATCH_TIME: float = 10.0 
    
    def __init__(self, name: str, coordinate: Tuple[float, float], flying_speed: float = 120.0, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.flying_speed = flying_speed
        self.can_fly = True
        self.is_flying = False
        self.hp = self.max_hp
    
    def move(self, dt: float, target: Optional[Tuple[float, float]] = None, speed_multiplier: float = 1.0):
        if self.is_flying:
            speed_ratio = self.flying_speed / self.max_speed
            super().move(dt, target, speed_multiplier=speed_ratio * speed_multiplier)
            self.use_stamina(2.0 * dt)
            if self.stamina <= 0:
                self.is_flying = False
        else:
            super().move(dt, target, speed_multiplier=speed_multiplier)
    
    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        """비행 중일 때는 전기/독 공격을 제외하고 70% 확률로 회피 (30% 확률로 피격)"""
        if self.is_flying:
            # 1. 확정 명중 공격 (전기 광역기, 독개구리 즉사기)
            if source == "electric_shock" or (attacker and attacker.__class__.__name__ in ["ElectricEel", "ToxicFrog"]):
                super().take_damage(amount, source, attacker)
            # 2. 모기를 포함한 일반 공격은 70% 확률로 회피 작동!
            else:
                if random.random() < 0.70:
                    atk_name = attacker.name if attacker else source
                    print(f"💨 🦅 [{self.name}]가 뛰어난 비행 기동력으로 {atk_name}의 공격을 휙 피했습니다! (70% 회피 성공)")
                    return
                else:
                    super().take_damage(amount, source, attacker)
        else:
            # 지상에 있을 때는 평범하게 데미지를 받음
            super().take_damage(amount, source, attacker)

    def attack(self, target: Optional[Animal] = None, base_damage: float = 15.0):
        if target and target.alive:
            if self.is_flying:
                extra_damage = self.flying_speed * 0.15
                final_damage = base_damage + extra_damage
                print(f"🦅 {self.name}이(가) 공중에서 고속({self.flying_speed:.1f})으로 강하하며 {target.name}에게 가속도가 붙은 강력한 타격({final_damage:.1f})을 입힙니다!")
                target.take_damage(final_damage, source="flying_attack", attacker=self)
            else:
                print(f"🦅 {self.name}이(가) 지상에서 부리로 {target.name}을(를) 쪼아 공격({base_damage:.1f})합니다!")
                target.take_damage(base_damage, source="peck_attack", attacker=self)
        elif target is not None:
            super().attack(target, base_damage)
    
    def make_child(self): 
        breed_cost = 20.0
        if self.stamina < breed_cost or (self.couple and self.couple.stamina < breed_cost): return None
        self.use_stamina(breed_cost)
        if self.couple: self.couple.use_stamina(breed_cost)
        print(f"🥚 {self.name}이(가) 알을 낳았습니다!")
        return Egg(self.coordinate, self, hatch_time=self.HATCH_TIME)

    def _spawn_child(self):
        child_sex = random.choice(["male", "female"])
        child = type(self)(name=f"{self.name}_child", coordinate=self.coordinate[:], sex=child_sex)
        child.max_hp = int(self.max_hp * random.uniform(0.9, 1.1))
        child.hp = child.max_hp
        child.max_stamina = self.max_stamina * random.uniform(0.9, 1.1)
        child.max_speed = max(self.max_speed * random.uniform(0.9, 1.1), 20)
        child.flying_speed = self.flying_speed * random.uniform(0.9, 1.1)
        return child

    def can_see(self, target: "Animal", game_map) -> bool:
        if not target.alive: return False
        if self.distance_to(target) > self.vision_range: return False
        if self.vision_angle < 360:
            ox, oy = self.coordinate
            tx, ty = target.coordinate
            target_angle = math.atan2(ty - oy, tx - ox)
            diff = (target_angle - self.facing_angle) % (2 * math.pi)
            if diff > math.pi: diff -= 2 * math.pi
            if abs(diff) > math.radians(self.vision_angle / 2): return False
        return True

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: return
        if not self.is_flying and self.stamina > 20: self.is_flying = True

# ==========================================
# 2. 코뿔소 (Rhino)
# ==========================================
class Rhino(Animal):
    SPECIES_VISION_RANGE: float = 400.0
    SPECIES_VISION_ANGLE: float = 100.0
    minimap_color = (150, 150, 150)
    
    def __init__(self, name: str, coordinate: Tuple[float, float], crash_power: float = 50.0, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.crash_power = crash_power
        self.max_speed = 90.0
        self.size=random.uniform(100,200)
        self.max_hp=600
        self.hp=self.max_hp
        self.max_speed=80
        
        self.is_charging = False
        self.charge_target_tree = None
        
        self.image_path = "rhino.png" 
        self.image = None
        if self.image_path not in CHOI_IMAGE_CACHE:
            try:
                CHOI_IMAGE_CACHE[self.image_path] = pygame.image.load(self.image_path).convert_alpha()
                CHOI_IMAGE_CACHE[self.image_path] = pygame.transform.flip(CHOI_IMAGE_CACHE[self.image_path], True, False)
            except Exception: CHOI_IMAGE_CACHE[self.image_path] = None
            
        orig_img = CHOI_IMAGE_CACHE[self.image_path]
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
        else: super().draw(screen,camera)

    def make_child(self):
        breed_cost = 40.0
        if self.stamina < breed_cost or (self.couple and self.couple.stamina < breed_cost): return None
        self.use_stamina(breed_cost)
        if self.couple: self.couple.use_stamina(breed_cost)
        child_sex = random.choice(["male", "female"])
        child = type(self)(name=f"{self.name}_child", coordinate=self.coordinate[:], sex=child_sex)
        child.max_hp = int(self.max_hp * random.uniform(0.9, 1.1))
        child.hp = child.max_hp
        child.max_stamina = self.max_stamina * random.uniform(0.9, 1.1)
        child.max_speed = self.max_speed * random.uniform(0.9, 1.1)
        child.crash_power = self.crash_power * random.uniform(0.9, 1.1)
        print(f"🦏 {self.name}이(가) 건강한 새끼를 낳았습니다!")
        return child
    
    def start_charge(self, attacker: Animal):
        if not self.is_charging and self.use_stamina(30.0):
            self.is_charging = True
            self.charge_attacker = attacker
            self.charge_target_coord = (attacker.coordinate[0], attacker.coordinate[1])
            print(f"🦏 🔥 [{self.name}]가 치명상을 입고 격노하여 {attacker.name}이(가) 있던 위치로 맹렬히 돌진합니다!!")

    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        super().take_damage(amount, source, attacker)
        if self.alive and self.hp <= self.max_hp * 0.35 and attacker and attacker.alive:
            if not self.is_charging: self.start_charge(attacker)

    def _stop_charge(self):
        self.is_charging = False
        self.charge_target_coord = None
        self.charge_attacker = None
        self.stop()

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: return

        if self.is_charging and self.charge_target_coord:
            self.move(dt, self.charge_target_coord, speed_multiplier=25/8)
            if self.charge_attacker and self.charge_attacker.alive:
                if self.distance_to(self.charge_attacker) <= 30.0:
                    print(f"💥 🦏 [{self.name}]의 초강력 박치기가 경로 상에 있던 {self.charge_attacker.name}에게 적중했습니다!")
                    self.charge_attacker.take_damage(self.crash_power, source="rhino_crash", attacker=self)
                    self._stop_charge()
                    return
            tree = game_map.get_tree_at_pixel(self.coordinate[0], self.coordinate[1])
            if tree and not tree.broken:
                print(f"💥 쾅! [{self.name}]가 돌진 중 나무를 들이받아 부쉈습니다!")
                game_map.break_tree(tree)
                for animal in animals:
                    if type(animal).__name__ == "Monkey" and getattr(animal, 'on_tree', False):
                        if self.distance_to(animal) < 60.0:
                            animal.on_tree = False
                            animal.current_tree = None
                            if hasattr(animal, 'apply_stun'): animal.apply_stun(2.0)
                            print(f"쿵! 나무가 부서져 {animal.name}가 땅으로 떨어졌습니다!")
                self._stop_charge()
                return

            dist_to_target = math.hypot(self.coordinate[0] - self.charge_target_coord[0], self.coordinate[1] - self.charge_target_coord[1])
            if dist_to_target < 10.0: self._stop_charge()
        
        if not getattr(self, 'is_hunting', False) and not getattr(self, 'is_fleeing', False):
            # 💡 [추가] 집 찾기 로직
            if self.try_return_home(dt):
                self.target_coord = None
                return
                
            if not getattr(self, 'target_coord', None):
                if random.random() < 0.5: 
                    rx = self.coordinate[0] + random.uniform(-2000.0, 2000.0)
                    ry = self.coordinate[1] + random.uniform(-2000.0, 2000.0)
                    rx = max(50.0, min(float(game_map.pixel_width - 50.0), rx))
                    ry = max(50.0, min(float(game_map.pixel_height - 50.0), ry))
                    self.target_coord = [rx, ry]
            if getattr(self, 'target_coord', None):
                self.move(dt, target=self.target_coord, speed_multiplier=0.5) 
                if self.distance_to(self.target_coord) < 15.0: self.target_coord = None


# ==========================================
# 3. 전기뱀장어 (Electric Eel) - 포식자
# ==========================================
class ElectricEel(Predator):
    SPECIES_VISION_RANGE: float = 500.0
    SPECIES_VISION_ANGLE: float = 360.0
    minimap_color = (0, 255, 255)
    HUNT_TARGETS={"Capybara","Monkey"}
    
    def __init__(self, name: str, coordinate: Tuple[float, float], electric_power: float = 30.0, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.electric_power = electric_power
        self.max_speed = 110.0
        self.size=random.uniform(80,140)
        self.max_hp=150
        self.hp=self.max_hp
        
        self.image_path = "eel.png" 
        self.image = None
        if self.image_path not in CHOI_IMAGE_CACHE:
            try:
                CHOI_IMAGE_CACHE[self.image_path] = pygame.image.load(self.image_path).convert_alpha()
                CHOI_IMAGE_CACHE[self.image_path] = pygame.transform.flip(CHOI_IMAGE_CACHE[self.image_path], True, False)
                CHOI_IMAGE_CACHE[self.image_path] = pygame.transform.rotate(CHOI_IMAGE_CACHE[self.image_path], 20)
            except Exception: CHOI_IMAGE_CACHE[self.image_path] = None
        orig_img = CHOI_IMAGE_CACHE[self.image_path]
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
    
    def move(self, dt: float, target: Optional[Tuple[float, float]] = None, speed_multiplier: float = 1.0):
        if getattr(self, 'environment_status', '') == 'water':
            super().move(dt, target, speed_multiplier=speed_multiplier * 1.6)
        else:
            super().move(dt, target, speed_multiplier=speed_multiplier * 0.4)
    
    def make_child(self):
        breed_cost = 25.0
        if self.stamina < breed_cost or (self.couple and self.couple.stamina < breed_cost): return None
        self.use_stamina(breed_cost)
        if self.couple: self.couple.use_stamina(breed_cost)
        print(f"🥚 {self.name}이(가) 물속에 알을 낳았습니다!")
        return Egg(self.coordinate, self, hatch_time=10.0)

    def _spawn_child(self):
        child_sex = random.choice(["male", "female"])
        child = type(self)(name=f"{self.name}_child", coordinate=self.coordinate[:], sex=child_sex)
        child.max_hp = int(self.max_hp * random.uniform(0.9, 1.1))
        child.hp = child.max_hp
        child.max_stamina = self.max_stamina * random.uniform(0.9, 1.1)
        child.max_speed = self.max_speed * random.uniform(0.9, 1.1)
        child.electric_power = self.electric_power * random.uniform(0.9, 1.1)
        return child

    def swim(self, dt: float, target: Optional[Tuple[float, float]] = None):
        self.move(dt, target, speed_multiplier=1.4)

    def electric_attack(self, target: Animal, animals: List[Animal], weather=None):
        base_damage = 30.0
        aoe_radius = 150.0 
        max_aoe_damage = 25.0
        is_raining = False
        if weather and hasattr(weather, 'current'):
            if getattr(weather.current, 'name', '') in ["RAINY", "STORM"]: is_raining = True

        if is_raining:
            base_damage *= 1.5; aoe_radius *= 2.0; max_aoe_damage *= 1.5
            print(f"⛈️ 궂은 날씨로 인해 [{self.name}]의 전기 공격 반경이 2배로 넓어집니다!")

        target.take_damage(base_damage, source=self.name, attacker=self)
        target.apply_stun(duration=2.5) 
        
        if self.environment_status == "water":
            for a in animals:
                if a is not self and a is not target and a.alive and getattr(a, 'environment_status', 'land') == "water":
                    dist = self.distance_to(a)
                    if dist <= aoe_radius:
                        dist = max(1.0, dist) 
                        shock_damage = max_aoe_damage * (1.0 - (dist / aoe_radius))
                        if shock_damage > 0:
                            a.take_damage(shock_damage, source="electric_shock", attacker=self)
                            a.apply_stun(duration=1.5)
                            print(f"⚡ [{a.name}]이(가) 물을 타고 흐른 전기에 감전되었습니다! (피해량: {shock_damage:.1f})")

    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        super().take_damage(amount, source, attacker)
        if attacker and attacker.alive and self.alive and self.use_stamina(10.0):
            print(f"⚡ [{self.name}]이(가) 자신을 공격한 {attacker.name}에게 방어적 방전을 일으킵니다!")
            attacker.take_damage(15.0, source="defensive_shock", attacker=self)
            attacker.apply_stun(duration=2.0)

    def try_attack(self, target: Animal, base_damage: float = 20.0, food_value: float = 60.0) -> bool:
        if not target.alive:
            self.stop_hunt(); return False
        if self.distance_to(target) <= self.attack_range:
            if getattr(target, 'is_stunned', False):
                print(f"💥 [{self.name}]이(가) 기절한 {target.name}에게 치명적인 일격을 가합니다!")
                self.attack(target, base_damage * 2.0)
                if not target.alive: self.eat(target.FOOD_VALUE)   # 💡 사냥감 종류별 영양값
                return True
            else: return super().try_attack(target, base_damage, food_value)
        return False
    
    def check_competition(self, animals: List[Animal]):
        if not getattr(self, 'is_hunting', False) or self.hunting_target is None: return
        if self.hunting_target.__class__.__name__ == "Crocodile": return

        for a in animals:
            if a is self or not a.alive: continue
            if a.__class__.__name__ == "Crocodile":
                croc_state, croc_target = getattr(a, '_state', ''), getattr(a, '_target', None)
                if croc_state in ("rushing", "chasing", "death_roll"):
                    if self.distance_to(a) <= 250.0:
                        print(f"⚡🐊 [영역 다툼] {self.name}와 {a.name}가 {self.hunting_target.name}을(를) 두고 격돌합니다!")
                        self.hunting_target = a
                        a._set_state("chasing", self)
                        break

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: return

        self.check_competition(animals)
        if self.is_hunting and self.hunting_target:
            if self.distance_to(self.hunting_target) <= self.attack_range + 20:
                if random.random() < 0.05: self.electric_attack(self.hunting_target, animals, weather)
        
        if not getattr(self, 'is_hunting', False) and not getattr(self, 'is_fleeing', False):
            # 💡 [추가] 집 찾기 로직
            if self.try_return_home(dt):
                self.target_coord = None
                return
                
            if not getattr(self, 'target_coord', None):
                if random.random() < 0.05:
                    cx, cy = int(self.coordinate[0] // 32), int(self.coordinate[1] // 32)
                    water_tiles = []
                    for dy in range(-15, 16):
                        for dx in range(-15, 16):
                            tx, ty = cx + dx, cy + dy
                            if 0 <= tx < game_map.map_width and 0 <= ty < game_map.map_height:
                                tile = game_map.get_tile(tx, ty)
                                if tile in (TileType.WATER, TileType.DEEP_WATER): water_tiles.append((tx, ty))

                    if water_tiles:
                        chosen_tx, chosen_ty = random.choice(water_tiles)
                        target_x, target_y = chosen_tx * 32 + 16.0, chosen_ty * 32 + 16.0
                    else:
                        target_x, target_y = self.coordinate[0] + random.uniform(-300.0, 300.0), self.coordinate[1] + random.uniform(-300.0, 300.0)
                    
                    target_x = max(50.0, min(float(game_map.pixel_width - 50.0), target_x))
                    target_y = max(50.0, min(float(game_map.pixel_height - 50.0), target_y))
                    self.target_coord = [target_x, target_y]
                        
            if getattr(self, 'target_coord', None):
                if getattr(self, 'swim_boost_timer', 0) > 0: self.swim_boost_timer -= dt
                if (self.environment_status == "water" and self.stamina >= 30.0 and getattr(self, 'swim_boost_timer', 0) <= 0 and random.random() < 0.02):
                    self.use_stamina(5.0); self.swim_boost_timer = 1.5
                if getattr(self, 'swim_boost_timer', 0) > 0: self.swim(dt, target=self.target_coord)
                else: self.move(dt, target=self.target_coord)
                if self.distance_to(self.target_coord) < 15.0: self.target_coord = None


# ==========================================
# 4. 독개구리 (Toxic Frog)
# ==========================================
class ToxicFrog(Prey):
    SPECIES_VISION_RANGE: float = 500.0
    SPECIES_VISION_ANGLE: float = 180.0
    minimap_color = (144, 238, 144) # 오타 수정
    HATCH_TIME: float = 10.0
    
    def __init__(self, name: str, coordinate: Tuple[float, float], poison_amount: float = 4.0, **kwargs):
        super().__init__(name, coordinate, danger_range=150.0, **kwargs) # 💡 Prey 생성자 호환성 맞춤
        self.poison_amount = poison_amount
        self.max_speed = 50.0
        self.size = random.uniform(30,60)
        self.max_hp=50
        self.hp=self.max_hp

        self.image_path = "frog.png"
        self.image = None
        if self.image_path not in CHOI_IMAGE_CACHE:
            try:
                CHOI_IMAGE_CACHE[self.image_path] = pygame.image.load(self.image_path).convert_alpha()
                CHOI_IMAGE_CACHE[self.image_path] = pygame.transform.rotate(CHOI_IMAGE_CACHE[self.image_path],340)
            except Exception: CHOI_IMAGE_CACHE[self.image_path] = None
        orig_img = CHOI_IMAGE_CACHE[self.image_path]
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
    
    def make_child(self):
        breed_cost = 15.0
        if self.stamina < breed_cost or (self.couple and self.couple.stamina < breed_cost): return None
        self.use_stamina(breed_cost)
        if self.couple: self.couple.use_stamina(breed_cost)
        print(f"🥚 {self.name}이(가) 끈적한 알을 낳았습니다!")
        return Egg(self.coordinate, self, hatch_time=self.HATCH_TIME)

    def _spawn_child(self):
        child_sex = random.choice(["male", "female"])
        child = type(self)(name=f"{self.name}_child", coordinate=self.coordinate[:], sex=child_sex)
        child.max_hp = int(self.max_hp * random.uniform(0.9, 1.1))
        child.hp = child.max_hp
        child.max_stamina = self.max_stamina * random.uniform(0.9, 1.1)
        child.max_speed = self.max_speed * random.uniform(0.9, 1.1)
        child.poison_amount = self.poison_amount * random.uniform(0.9, 1.1)
        return child

    def jump(self, dt: float, target: Optional[Tuple[float, float]] = None):
        self.move(dt, target, speed_multiplier=2.5)

    def poison(self, attacker: Animal):
        print(f"☠️ [{self.name}]의 맹독이 {attacker.name}에게 퍼집니다!")
        attacker.apply_poison(duration=8.0, dps=self.poison_amount)
        attacker.stamina = max(0, attacker.stamina - 20.0)
        attacker.max_speed = max(10.0, attacker.max_speed * 0.8)

    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        super().take_damage(amount, source, attacker) 
        if attacker and attacker.alive: self.poison(attacker)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: return
        
        if self.hunger>30.0:
            for a in animals:
                if a.__class__.__name__ == "Mosquito" and a.alive:
                    dist = self.distance_to(a)
                    if dist<30.0:
                        print(f"🐸 {self.name}이(가) {a.name}을(를) 잡아먹었습니다!")
                        a.take_damage(999.0, source="toxic_frog_eat", attacker=self) # 💡 attacker 전달로 모기 즉사 성공!
                        self.eat(a.FOOD_VALUE)   # 💡 사냥감(모기) 종류별 영양값
                        break
                    elif dist <= 120.0 and self.stamina >= 10.0:
                        self.use_stamina(10.0 * dt)
                        self.jump(dt, target=a.coordinate)
                        break
                        
        if not getattr(self, 'is_hunting', False) and not getattr(self, 'is_fleeing', False):
            # 💡 [추가] 집 찾기 로직
            if self.try_return_home(dt):
                self.target_coord = None
                return
                
            if self.hunger > 30.0 and game_map.apples:
                closest_apple = min(game_map.apples, key=lambda a: self.distance_to((a.x, a.y)), default=None)
                if closest_apple and self.distance_to((closest_apple.x, closest_apple.y)) < self.vision_range:
                    if self.distance_to((closest_apple.x, closest_apple.y)) < 25.0:
                        print(f"🍎 [{self.name}]가 긴 혀로 사과를 날름 삼켰습니다!")
                        self.eat(closest_apple.heal_amount)
                        if closest_apple in game_map.apples: game_map.apples.remove(closest_apple) # 💡 사과 증발 버그 제거
                        self.target_coord = None
                    else:
                        self.target_coord = [closest_apple.x, closest_apple.y]
                        self.move(dt, self.target_coord, speed_multiplier=0.8)
                    return
            
            if self.is_seeking_water and getattr(self, '_water_target', None):
                self.move(dt, self._water_target)
                self.target_coord = None
                return
                
            couple_tgt = self.couple_follow()
            if couple_tgt:
                self.move(dt, couple_tgt)
                self.target_coord = None
                return
                
            if not getattr(self, 'target_coord', None):
                if random.random() < 0.05: 
                    rx = self.coordinate[0] + random.uniform(-150.0, 150.0)
                    ry = self.coordinate[1] + random.uniform(-150.0, 150.0)
                    rx = max(50.0, min(float(game_map.pixel_width - 50.0), rx))
                    ry = max(50.0, min(float(game_map.pixel_height - 50.0), ry))
                    self.target_coord = [rx, ry]
            
            if getattr(self, 'target_coord', None):
                if getattr(self, 'jump_boost_timer', 0) > 0: self.jump_boost_timer -= dt
                if (self.environment_status != "water" and self.stamina >= 40.0 and getattr(self, 'jump_boost_timer', 0) <= 0 and random.random() < 0.02):
                    self.use_stamina(10.0)
                    self.jump_boost_timer = 0.8
                
                if getattr(self, 'jump_boost_timer', 0) > 0: self.jump(dt, target=self.target_coord)
                else: self.move(dt, target=self.target_coord)
                    
                if self.distance_to(self.target_coord) < 15.0: self.target_coord = None
