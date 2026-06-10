import math
import random
import pygame
from typing import Tuple, Optional, List

TILE_SIZE = 32

# ════════════════════════════════════════════════
#  FOV 유틸리티
# ════════════════════════════════════════════════

def _angle_diff(a: float, b: float) -> float:
    d = (b - a) % (2 * math.pi)
    if d > math.pi:
        d -= 2 * math.pi
    return d

def _line_blocked_by_trees(ox: float, oy: float, tx: float, ty: float, game_map) -> bool:
    dist = math.hypot(tx - ox, ty - oy)
    if dist < 1.0: return False
    steps = max(4, int(dist / 24))
    dx = (tx - ox) / steps
    dy = (ty - oy) / steps
    for i in range(1, steps):
        sx = ox + dx * i
        sy = oy + dy * i
        tree = game_map.tree_map.get((int(sx // TILE_SIZE), int(sy // TILE_SIZE)))
        if tree and not tree.broken and tree.canopy_rect().collidepoint(sx, sy):
            return True
    return False

def has_line_of_sight(observer, target_coord: Tuple[float, float], game_map) -> bool:
    ox, oy = observer.coordinate[0], observer.coordinate[1]
    tx, ty = target_coord[0], target_coord[1]
    if math.hypot(tx - ox, ty - oy) > observer.vision_range: return False
    if observer.vision_angle < 360:
        diff = abs(_angle_diff(observer.facing_angle, math.atan2(ty - oy, tx - ox)))
        if diff > math.radians(observer.vision_angle / 2): return False
    return not _line_blocked_by_trees(ox, oy, tx, ty, game_map)

# ════════════════════════════════════════════════
#  Egg
# ════════════════════════════════════════════════

EGG_IMAGE_CACHE = {}

class Egg:
    def __init__(self, coordinate: Tuple[float, float], parent: "Animal", hatch_time: float = 10.0):
        self.coordinate = list(coordinate)
        self.parent = parent
        self.hatch_time = hatch_time
        self.hatch_timer = 0.0
        self.hatched = False
        self.size = 20.0

        self.image_path = "egg.png"
        self.image = None
        if self.image_path not in EGG_IMAGE_CACHE:
            try:
                loaded_img = pygame.image.load(self.image_path).convert_alpha()
                EGG_IMAGE_CACHE[self.image_path] = loaded_img
            except Exception as e:
                print(f"⚠️ 알 이미지 로드 실패: {e}")
                EGG_IMAGE_CACHE[self.image_path] = None

        orig_img = EGG_IMAGE_CACHE[self.image_path]
        if orig_img is not None:
            orig_w, orig_h = orig_img.get_size()
            target_max_size = int(self.size * 1.5)
            scale_factor = target_max_size / max(orig_w, orig_h)
            new_w = int(orig_w * scale_factor)
            new_h = int(orig_h * scale_factor)
            self.image = pygame.transform.scale(orig_img, (new_w, new_h))

    def update(self, dt: float) -> Optional["Animal"]:
        if self.hatched: return None
        self.hatch_timer += dt
        if self.hatch_timer >= self.hatch_time:
            self.hatched = True
            spawn_fn = getattr(self.parent, '_spawn_child', self.parent.make_child)
            child = spawn_fn()
            if child:
                child.coordinate = self.coordinate[:]
                print(f"{self.parent.name}의 알이 부화했다!")
            return child
        return None

    @property
    def hatch_progress(self) -> float:
        return min(1.0, self.hatch_timer / self.hatch_time)

    def draw(self, screen: "pygame.Surface", camera):
        if self.hatched: return
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        margin = 50
        if not (-margin < sx < camera.screen_w + margin and -margin < sy < camera.screen_h + margin): return

        if self.image:
            if not hasattr(self.__class__, '_shared_img_cache'):
                self.__class__._shared_img_cache = {}
            zoom_key = round(camera.zoom, 2)
            if zoom_key not in self.__class__._shared_img_cache:
                new_w = int(self.image.get_width() * zoom_key)
                new_h = int(self.image.get_height() * zoom_key)
                self.__class__._shared_img_cache[zoom_key] = pygame.transform.scale(self.image, (new_w, new_h))
            scaled_image = self.__class__._shared_img_cache[zoom_key]
            rect = scaled_image.get_rect(center=(int(sx), int(sy)))
            screen.blit(scaled_image, rect)
            new_h = scaled_image.get_height()
            bw = 15 * camera.zoom
            bh = 3 * camera.zoom
            bx = sx - bw / 2
            by = sy - (new_h / 2) - (6 * camera.zoom)
        else:
            pygame.draw.ellipse(screen, (210, 200, 170),
                                (int(sx) - int(5*camera.zoom), int(sy) - int(4*camera.zoom),
                                 int(10*camera.zoom), int(8*camera.zoom)))
            bw = 12 * camera.zoom
            bh = 2 * camera.zoom
            bx = sx - bw / 2
            by = sy - (10 * camera.zoom)
        pygame.draw.rect(screen, (60, 60, 60), (bx, by, bw, bh))
        pygame.draw.rect(screen, (255, 200, 50), (bx, by, int(bw * self.hatch_progress), bh))

# ════════════════════════════════════════════════
#  Animal
# ════════════════════════════════════════════════

class Animal:
    SPECIES_VISION_RANGE: float = 150.0
    SPECIES_VISION_ANGLE: float = 120.0
    HATCH_TIME: float = random.uniform(50.0, 100.0)

    # 💡 종별 오버라이드 가능 — 실제 값 조정은 system.py에서 한 번에 한다
    HOME_BUILD_PROB: float = 0.8   # 둥지(집) 생성 확률 (초당 1회 판정)
    BREED_PROB: float      = 0.9   # 번식(알 낳기) 확률 (초당 1회 판정)
    FOOD_VALUE: float      = 35.0  # 💡 이 동물이 잡아먹혔을 때 포식자 배고픔을 채워주는 양 (기본값)

    def __init__(self, name: str, coordinate: Tuple[float, float], hp: int = 100, max_hp: int = 100,
                 stamina: float = 100.0, max_stamina: float = 100.0, max_speed: float = 80.0, hunger: float = 0.0,
                 thirst: float = 0.0, detection_range: float = 150.0, age: int = 0, max_age: int = 3600,
                 sex: str = "male", home_coordinate: Optional[Tuple[float, float]] = None,
                 environment_status: str = "land", max_accelerate: float = 200.0, size: float = 100.0):
        self.name = name
        self.coordinate = list(coordinate)
        self.velocity = [0.0, 0.0]
        self.size = size
        self.hp = hp
        self.max_hp = max_hp
        self.stamina = stamina
        self.max_stamina = max_stamina
        self.max_accelerate = max_accelerate
        self.max_speed = max_speed
        self.friction_land  = 6.0
        self.friction_water = 2.0
        self.hunger = hunger
        self.thirst = thirst
        self.environment_status = environment_status
        self.age = age
        self.max_age = max_age
        self.is_adult = False
        self.sex = sex
        self.couple: Optional["Animal"] = None
        self._breed_cooldown = 0.0          # 번식 후 재커플 금지 타이머
        self.can_breed = False
        self.home_coordinate = list(home_coordinate) if home_coordinate else None
        self.at_home = False
        self.home_threshold = 120.0
        self.home_range = 150.0
        self._home_timer = 0.0
        self.is_stunned = False
        self.stun_timer = 0.0
        self.is_poisoned = False
        self.poison_timer = 0.0
        self.poison_damage_per_sec = 2.0
        self.poison_speed_multiplier = 0.6
        self.detection_range = detection_range
        self.vision_range: float = self.SPECIES_VISION_RANGE
        self.vision_angle: float = self.SPECIES_VISION_ANGLE
        self.facing_angle: float = 0.0
        self.age_timer = 0.0
        self.hunger_timer = 0.0
        self.is_seeking_water = False
        self._water_target: Optional[Tuple[float, float]] = None
        self.THIRST_SEEK_THRESHOLD = 65.0
        self.alive = True

    @property
    def accelerate(self) -> float:
        hunger_factor  = 1.0 - (self.hunger / 100.0) * 0.5
        stamina_factor = 0.5 if self.stamina <= 0 else 1.0
        return self.max_accelerate * hunger_factor * stamina_factor

    def can_see(self, target: "Animal", game_map) -> bool:
        if not target.alive: return False
        if target.environment_status == "water":
            self.vision_range *= 0.5
            result = has_line_of_sight(self, target.coordinate, game_map)
            self.vision_range *= 2.0
            return result
        return has_line_of_sight(self, target.coordinate, game_map)

    def _update_facing(self):
        spd = math.hypot(*self.velocity)
        if spd > 0.1: self.facing_angle = math.atan2(self.velocity[1], self.velocity[0])

    def draw_fov_debug(self, screen: pygame.Surface, camera, color=None, alpha: int = 70):
        if not self.alive: return
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        display_range = self.vision_range * 0.5
        r = int(display_range * camera.zoom)
        if not (-r < sx < camera.screen_w + r and -r < sy < camera.screen_h + r): return
        fov_color = getattr(self, 'minimap_color', (255, 255, 255))
        if not hasattr(self.__class__, '_fov_cache'):
            self.__class__._fov_cache = {}
        zoom_key = round(camera.zoom, 1)
        angle_key = int(math.degrees(self.facing_angle) / 10) * 10
        cache_key = (zoom_key, angle_key, r)

        if cache_key not in self.__class__._fov_cache:
            max_r = min(r, 1500)
            surf = pygame.Surface((max_r * 2 + 2, max_r * 2 + 2), pygame.SRCALPHA)
            c = (max_r + 1, max_r + 1)
            if self.vision_angle >= 360:
                pygame.draw.circle(surf, (*fov_color, alpha), c, max_r)
            else:
                half = math.radians(self.vision_angle / 2)
                start = math.radians(angle_key) - half
                end   = math.radians(angle_key) + half
                pts = [c]
                for i in range(11):
                    a = start + (end - start) * i / 10
                    pts.append((c[0] + math.cos(a) * max_r, c[1] + math.sin(a) * max_r))
                pygame.draw.polygon(surf, (*fov_color, alpha), pts)
            self.__class__._fov_cache[cache_key] = surf
        cached_surf = self.__class__._fov_cache[cache_key]
        screen.blit(cached_surf, (int(sx) - r - 1, int(sy) - r - 1))

    def move(self, dt: float, target: Optional[Tuple[float, float]] = None, speed_multiplier: float = 1.0):
        if not self.alive or self.is_stunned:
            self._apply_friction(dt)
            return
        if target is not None:
            dx = target[0] - self.coordinate[0]
            dy = target[1] - self.coordinate[1]
            dist = math.hypot(dx, dy)
            # 💡 [핵심 수정] 거리가 너무 가까울 때 앞뒤로 진동(부르르 떠는 현상) 방지
            if dist > 5.0:
                self.velocity[0] += dx / dist * self.accelerate * dt
                self.velocity[1] += dy / dist * self.accelerate * dt
            else:
                # 목표 지점에 거의 도달했다면 급브레이크를 밟아 부드럽게 정지
                self.velocity[0] *= 0.5
                self.velocity[1] *= 0.5

        spd = math.hypot(*self.velocity)
        poison_mul  = self.poison_speed_multiplier if self.is_poisoned else 1.0
        stamina_mul = 0.5 if self.stamina <= 0 else 1.0
        limit = self.max_speed * speed_multiplier * self._home_speed_multiplier() * poison_mul * stamina_mul
        if spd > limit:
            self.velocity[0] = self.velocity[0] / spd * limit
            self.velocity[1] = self.velocity[1] / spd * limit

        self.coordinate[0] += self.velocity[0] * dt
        self.coordinate[1] += self.velocity[1] * dt
        self._apply_friction(dt)
        self._update_facing()

    def _apply_friction(self, dt: float):
        spd = math.hypot(*self.velocity)
        if spd < 1.0:
            self.velocity = [0.0, 0.0]
            return
        friction = (self.friction_water if self.environment_status == "water" else self.friction_land)
        factor = max(0.0, 1.0 - friction * dt)
        self.velocity[0] *= factor
        self.velocity[1] *= factor

    def stop(self):
        self.velocity = [0.0, 0.0]

    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional["Animal"] = None):
        if not self.alive: return
        self.hp = max(0, self.hp - amount)
        if self.hp == 0: self._die(cause=source)

    def heal(self, amount: float):
        if not self.alive: return
        self.hp = min(self.max_hp, self.hp + amount)

    def use_stamina(self, amount: float) -> bool:
        if self.stamina < amount: return False
        self.stamina -= amount
        return True

    def recover_stamina(self, dt: float, rate: float = 10.0, hunger_cost: float = 0.1):
        penalty = max(0.0, (self.hunger - 50) / 100)
        recovered = rate * (1.0 - penalty * 0.5) * dt
        self.stamina = min(self.max_stamina, self.stamina + recovered)
        self.hunger  = min(100.0, self.hunger + hunger_cost * dt)

    def eat(self, food_value: float = 30.0):
        self.hunger = max(0.0, self.hunger - food_value)
        self.heal(food_value)
        # 💡 [보너스] 밥을 먹었으니 에너지가 돌도록 스태미나도 50% 비율로 회복시켜 줍니다.
        self.stamina = min(self.max_stamina, self.stamina + (food_value * 0.5))

    # ── 공격 ────────────────────────────────────
    def attack(self, target: "Animal", damage: float = 10.0):
        if not self.alive or not target.alive: return
        target.take_damage(damage, source=self.name, attacker=self)

    def distance_to(self, other) -> float:
        if isinstance(other, Animal): tx, ty = other.coordinate[0], other.coordinate[1]
        else: tx, ty = other[0], other[1]
        return math.hypot(self.coordinate[0] - tx, self.coordinate[1] - ty)

    def is_at_home(self) -> bool:
        if self.home_coordinate is None: return False
        return self.distance_to(self.home_coordinate) <= self.home_threshold

    def near_home(self) -> bool:
        if self.home_coordinate is None: return False
        return self.distance_to(self.home_coordinate) <= self.home_range

    def _home_speed_multiplier(self) -> float:
        return 1.15 if self.near_home() else 1.0

    COUPLE_RANGE: float = 100.0                       # 커플 유지(리쉬) 기준 거리
    COUPLE_FORM_RANGE: float = 80.0                  # 커플 생성 범위
    COUPLE_HEADING_LIMIT: float = math.radians(30)   # 커플 이동 방향 허용 차이 (30도)
    BREED_COOLDOWN: float = 15.0                     # 번식 후 다시 커플이 될 때까지 대기 시간(초)

    def try_form_couple(self, other: "Animal") -> bool:
        if (self.is_adult and other.is_adult
                and self.couple is None and other.couple is None
                and self._breed_cooldown <= 0 and other._breed_cooldown <= 0
                and type(self) is type(other)
                and self.distance_to(other) <= self.COUPLE_FORM_RANGE
                and self.sex != other.sex):
            self.couple = other
            other.couple = self
            return True
        return False

    def couple_follow(self):
        if self.couple and self.couple.alive:
            dist = self.distance_to(self.couple)
            if dist > self.COUPLE_RANGE * 3.0:
                self.move(dt=0.1, target=self.couple.coordinate, speed_multiplier=1.2)
                target_distance = self.COUPLE_RANGE * 3.0 if self.home_coordinate else self.home_threshold * 0.5
                return self.couple.coordinate
        return None

    def _align_couple_heading(self):
        """커플 중 id가 큰 쪽(팔로워)이 상대(리더)의 이동 방향과 30도 이내가 되도록 진행 방향을 보정."""
        c = self.couple
        if not (c and c.alive): return
        if id(self) < id(c): return                 # id가 작은 쪽이 리더 → 보정하지 않음
        my_spd   = math.hypot(*self.velocity)
        lead_spd = math.hypot(*c.velocity)
        if my_spd < 1.0 or lead_spd < 1.0: return    # 한쪽이라도 거의 정지면 방향 의미 없음 → 패스
        my_ang   = math.atan2(self.velocity[1], self.velocity[0])
        lead_ang = math.atan2(c.velocity[1], c.velocity[0])
        diff = _angle_diff(lead_ang, my_ang)         # 리더 기준 내 진행 방향 차이
        limit = self.COUPLE_HEADING_LIMIT
        if abs(diff) > limit:                        # 30도를 넘으면 경계로 클램프
            new_ang = lead_ang + (limit if diff > 0 else -limit)
            self.velocity[0] = math.cos(new_ang) * my_spd
            self.velocity[1] = math.sin(new_ang) * my_spd

    def _separate_couple(self):
        """번식(알 낳기) 후 커플 관계를 끊고 서로 반대 방향으로 밀어내 헤어지게 한다."""
        c = self.couple
        if c is not None:
            dx = self.coordinate[0] - c.coordinate[0]
            dy = self.coordinate[1] - c.coordinate[1]
            d = math.hypot(dx, dy)
            if d < 1.0:
                ang = random.uniform(0, 2 * math.pi)
                dx, dy, d = math.cos(ang), math.sin(ang), 1.0
            push = self.max_speed
            self.velocity[0] += dx / d * push
            self.velocity[1] += dy / d * push
            c.velocity[0] -= dx / d * push
            c.velocity[1] -= dy / d * push
            c.couple = None
            c._breed_cooldown = c.BREED_COOLDOWN
            c.home_coordinate = None
            c.at_home = False
        self.couple = None
        self._breed_cooldown = self.BREED_COOLDOWN
        self.home_coordinate = None
        self.at_home = False
        print(f"{self.name} 💔 커플 해제 (번식 후 헤어짐)")

    def try_return_home(self, dt: float) -> bool:
        """번식을 위해 집으로 돌아가는 로직. 집으로 향하고 있으면 True 반환"""
        if self.home_coordinate and self.can_breed and self.couple and self.couple.alive:
            if not self.is_at_home():
                self.move(dt, self.home_coordinate, speed_multiplier=1.0)
                return True
        return False

    def _update_home(self, dt: float):
        self._home_timer += dt
        if self._home_timer < 1.0: return
        self._home_timer = 0.0

        c = self.couple
        if (c is not None and c.alive and self.home_coordinate is None
                and self.distance_to(c) <= self.home_threshold):
            if random.random() < self.HOME_BUILD_PROB:
                mid = [(self.coordinate[0] + c.coordinate[0]) / 2,
                       (self.coordinate[1] + c.coordinate[1]) / 2]
                self.home_coordinate = mid
                c.home_coordinate = mid[:]
                print(f"{self.name} 집 생성: {mid}")

        if (self.home_coordinate is not None and self.at_home and self.can_breed
                and c is not None and c.alive and c.at_home):
            if random.random() < self.BREED_PROB:
                result = self.make_child()
                if result:
                    self.pending_child = result
                    print(f"{self.name} 번식 성공!")
                    self._separate_couple()   # 번식(알 낳기) 직후 커플 해제 & 헤어짐
                return result
        return None

    def _update_home_buff(self, dt: float):
        if self.near_home():
            self.heal(3.0 * dt)
            self.stamina = min(self.max_stamina, self.stamina + 5.0 * dt)

    def make_child(self):
        return None

    def _check_can_breed(self):
        self.can_breed = (self.is_adult and self.hunger < 60 and self.hp > self.max_hp * 0.4)

    def apply_stun(self, duration: float = 2.0):
        self.is_stunned = True
        self.stun_timer = max(self.stun_timer, duration)

    def apply_poison(self, duration: float = 5.0, dps: float = 2.0, speed_multiplier: float = 0.6):
        self.is_poisoned = True
        self.poison_timer = max(self.poison_timer, duration)
        self.poison_damage_per_sec = max(self.poison_damage_per_sec, dps)
        self.poison_speed_multiplier = min(self.poison_speed_multiplier, speed_multiplier)

    def _update_age(self, dt: float):
        self.age_timer += dt
        if self.age_timer >= 1.0:
            self.age += int(self.age_timer)
            self.age_timer %= 1.0
        self.is_adult = self.age >= self.max_age * 0.15
        if self.age >= self.max_age: self._die(cause="old_age")

    def _update_hunger_thirst(self, dt: float):
        self.hunger_timer += dt
        if self.hunger_timer >= 1.0:
            self.hunger = min(100.0, self.hunger + 0.8)
            self.hunger_timer = 0.0
            if self.hunger >= 100.0: self._die(cause="starvation")
        if self.environment_status == "water":
            self.thirst = max(0.0, self.thirst - 8.0 * dt)
            if self.thirst <= 0:
                self.is_seeking_water = False
                self._water_target = None
        else:
            is_active = math.hypot(*self.velocity) > self.max_speed * 0.6
            rate = 2 if is_active else 1
            self.thirst = min(100.0, self.thirst + rate * dt)
            if self.thirst >= 100.0: self._die(cause="dehydration")

    def _find_nearest_water(self, game_map) -> Optional[Tuple[float, float]]:
        from map_system import TileType
        cx, cy = int(self.coordinate[0] // TILE_SIZE), int(self.coordinate[1] // TILE_SIZE)
        best, best_dist = None, float('inf')
        for dy in range(-40, 41):
            for dx in range(-40, 41):
                tx, ty = cx + dx, cy + dy
                tile = game_map.get_tile(tx, ty)
                if tile in (TileType.WATER, TileType.DEEP_WATER):
                    d = math.hypot(dx, dy)
                    if d < best_dist:
                        best_dist = d
                        best = (tx * TILE_SIZE + TILE_SIZE // 2, ty * TILE_SIZE + TILE_SIZE // 2)
        return best

    def _update_thirst_behavior(self, dt: float, game_map):
        self.environment_status = game_map.get_environment(self.coordinate[0], self.coordinate[1])
        in_water = self.environment_status == "water"
        if in_water and self.thirst <= 0:
            self.is_seeking_water = False
            self._water_target = None
        if (not in_water and self.thirst >= self.THIRST_SEEK_THRESHOLD and not self.is_seeking_water):
            self.is_seeking_water = True
            self._water_target = self._find_nearest_water(game_map)

    def _update_status_effects(self, dt: float):
        if self.is_stunned:
            self.stun_timer -= dt
            if self.stun_timer <= 0: self.is_stunned = False
        if self.is_poisoned:
            self.poison_timer -= dt
            self.take_damage(self.poison_damage_per_sec * dt, source="poison")
            if self.poison_timer <= 0:
                self.is_poisoned = False
                self.poison_speed_multiplier = 0.6
        # 💡 [핵심 최적화] 앵무새 버프 타이머 증발 버그 해결
        if hasattr(self, 'speed_boost_timer'):
            self.speed_boost_timer -= dt
            if self.speed_boost_timer <= 0:
                self.max_speed /= 1.35
                delattr(self, 'speed_boost_timer')
                print(f"  🐢 [{self.name}]의 앵무새 경고 가속 버프가 만료되었습니다.")

    def _die(self, cause: str = "unknown"):
        self.alive = False
        self.velocity = [0.0, 0.0]
        print(f"{self.name} 사망 (원인: {cause})")

    def update(self, dt: float, game_map, weather, animals: List["Animal"]):
        if not self.alive: return
        self._update_age(dt)
        self._update_thirst_behavior(dt, game_map)
        self._update_hunger_thirst(dt)
        self._update_status_effects(dt)
        self.recover_stamina(dt)
        self._check_can_breed()
        self.at_home = self.is_at_home()
        self._update_home(dt)
        self._update_home_buff(dt)
        if self._breed_cooldown > 0:                       # 번식 후 재커플 금지 시간 차감
            self._breed_cooldown = max(0.0, self._breed_cooldown - dt)
        if self.couple is None and self._breed_cooldown <= 0:
            for a in animals:
                if self.try_form_couple(a):
                    print(f"💖 {self.name}({self.sex}) ❤️ {a.name}({a.sex}) 커플 성사!")
                    break

    def draw(self, screen: pygame.Surface, camera):
        if not self.alive: return
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        pygame.draw.circle(screen, (220, 220, 220), (int(sx), int(sy)), 8)
        bw = 20
        bx, by = int(sx) - bw // 2, int(sy) - 14
        pygame.draw.rect(screen, (80, 0, 0),   (bx, by, bw, 3))
        pygame.draw.rect(screen, (0, 200, 60), (bx, by, int(bw * self.hp / self.max_hp), 3))
        if self.is_stunned:
            pygame.draw.circle(screen, (255, 255, 0),   (int(sx) + 8, int(sy) - 10), 3)
        if self.is_poisoned:
            pygame.draw.circle(screen, (100, 255, 100), (int(sx) - 8, int(sy) - 10), 3)

    def __repr__(self):
        return (f"<{self.__class__.__name__} '{self.name}' hp={self.hp}/{self.max_hp} pos=({self.coordinate[0]:.0f},{self.coordinate[1]:.0f})>")

# ════════════════════════════════════════════════
#  Predator
# ════════════════════════════════════════════════

class Predator(Animal):
    HUNT_TARGETS: set = set()

    def _is_prey(self, animal: "Animal") -> bool:
        return type(animal).__name__ in self.HUNT_TARGETS

    def __init__(self, name: str, coordinate: Tuple[float, float], attack_range: float = 40.0,
                 hunt_range: float = 200.0, attack_success_rate: float = 0.6, hunger_limit: float = 50.0,
                 chase_speed_mul: float = 1.4, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.attack_range = attack_range
        self.hunt_range = hunt_range
        self.attack_success_rate = attack_success_rate
        self.hunger_limit = hunger_limit
        self.chase_speed_mul = chase_speed_mul
        self.is_hunting = False
        self.hunting_target: Optional[Animal] = None

    def find_target(self, animals: List[Animal], game_map) -> Optional[Animal]:
        candidates = [a for a in animals if self._is_prey(a) and a.alive and self.distance_to(a) <= self.hunt_range and self.can_see(a, game_map)]
        return min(candidates, key=lambda a: self.distance_to(a), default=None)

    def start_hunt(self, target: Animal):
        self.is_hunting = True
        self.hunting_target = target

    def stop_hunt(self):
        self.is_hunting = False
        self.hunting_target = None

    def try_attack(self, target: Animal, base_damage: float = 20.0, food_value: float = 30.0) -> bool:
        if not target.alive:
            self.stop_hunt()
            return False
        if self.distance_to(target) <= self.attack_range:
            if random.random() < self.attack_success_rate:
                self.attack(target, base_damage)
                if not target.alive: self.eat(target.FOOD_VALUE)   # 💡 사냥감 종류별 영양값
                return True
        return False

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: return
        if not self.is_hunting and self.hunger >= self.hunger_limit:
            target = self.find_target(animals, game_map)
            if target: self.start_hunt(target)
        if self.is_hunting and self.hunting_target:
            t = self.hunting_target
            if not t.alive or not self.can_see(t, game_map):
                self.stop_hunt()
            else:
                self.try_attack(t)
                self.move(dt, t.coordinate, self.chase_speed_mul)
                self.use_stamina(8.0 * dt)
        elif self.is_seeking_water and self._water_target:
            self.move(dt, self._water_target)
        else:
            couple_tgt = self.couple_follow()
            self.move(dt, couple_tgt)
            if couple_tgt is None:                 # 리쉬 안쪽일 때만 진행 방향 30도 정렬
                self._align_couple_heading()

# ════════════════════════════════════════════════
#  Prey
# ════════════════════════════════════════════════

class Prey(Animal):
    def __init__(self, name: str, coordinate: Tuple[float, float], danger_range: float = 180.0,
                 hide_success_rate: float = 0.5, hide_range: float = 80.0, flee_speed_mul: float = 1.5, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.predator_detected = False
        self.danger_range = danger_range
        self.is_fleeing = False
        self.is_hiding = False
        self.hide_success_rate = hide_success_rate
        self.hide_range = hide_range
        self.flee_speed_mul = flee_speed_mul
        self._hiding_from: Optional[Animal] = None

    def detect_predators(self, animals: List[Animal], game_map) -> List[Animal]:
        return [a for a in animals if isinstance(a, Predator) and a.alive and self.distance_to(a) <= self.danger_range and self.can_see(a, game_map)]

    def flee_from(self, predator: Animal, dt: float):
        self.is_fleeing = True
        dx = self.coordinate[0] - predator.coordinate[0]
        dy = self.coordinate[1] - predator.coordinate[1]
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
            dist = 1.0
        flee_x = self.coordinate[0] + dx / dist * 200
        flee_y = self.coordinate[1] + dy / dist * 200
        self.move(dt, (flee_x, flee_y), self.flee_speed_mul)
        self.use_stamina(10.0 * dt)

    def try_hide(self, game_map, predator: "Predator") -> bool:
        dx = self.coordinate[0] - predator.coordinate[0]
        dy = self.coordinate[1] - predator.coordinate[1]
        dist = math.hypot(dx, dy)
        if dist < 1.0: flee_angle = 0.0
        else: flee_angle = math.atan2(dy, dx)
        HIDE_ANGLE_LIMIT = math.radians(60)
        candidates = []
        for tree in game_map.trees:
            if tree.broken: continue
            tx, ty = tree.coordinate
            tree_dist = self.distance_to((tx, ty))
            if tree_dist > self.hide_range: continue
            angle_to_tree = math.atan2(ty - self.coordinate[1], tx - self.coordinate[0])
            if abs(_angle_diff(flee_angle, angle_to_tree)) <= HIDE_ANGLE_LIMIT:
                candidates.append((tree, tree_dist))
        if not candidates: return False
        best_tree, _ = min(candidates, key=lambda x: x[1])
        size_bonus = (best_tree.width_tiles * best_tree.height_tiles - 4) * 0.05
        final_rate = min(0.95, self.hide_success_rate + size_bonus)
        if random.random() < final_rate:
            self.is_hiding = True
            self._hiding_from = predator
            self.stop()
            if hasattr(predator, 'stop_hunt'): predator.stop_hunt()
            return True
        return False

    def stop_hiding(self):
        self.is_hiding = False
        self._hiding_from = None

    def stop_fleeing(self):
        self.is_fleeing = False

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: return
        if self.is_hiding:
            if (self._hiding_from is None or not self._hiding_from.alive or self.distance_to(self._hiding_from) > self.danger_range):
                self.stop_hiding()
            return
        predators = self.detect_predators(animals, game_map)
        if predators:
            self.predator_detected = True
            closest = min(predators, key=lambda p: self.distance_to(p))
            if self.distance_to(closest) < self.danger_range * 0.5:
                self.stop_fleeing()
                self.flee_from(closest, dt)
            else:
                if not self.try_hide(game_map, closest):
                    self.flee_from(closest, dt)
        elif self.is_seeking_water and self._water_target:
            self.predator_detected = False
            self.stop_fleeing()
            self.move(dt, self._water_target)
        else:
            self.predator_detected = False
            self.stop_fleeing()
            couple_tgt = self.couple_follow()
            self.move(dt, couple_tgt)
            if couple_tgt is None:                 # 리쉬 안쪽일 때만 진행 방향 30도 정렬
                self._align_couple_heading()
