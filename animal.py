import math
import random
import pygame
from typing import Tuple, Optional, List

TILE_SIZE = 32  # map_system과 동일


# ════════════════════════════════════════════════
#  FOV 유틸리티
# ════════════════════════════════════════════════

def _angle_diff(a: float, b: float) -> float:
    """두 라디안 각도의 최소 차이 (-π ~ π)"""
    d = (b - a) % (2 * math.pi)
    if d > math.pi:
        d -= 2 * math.pi
    return d


def _line_blocked_by_trees(ox: float, oy: float,
                            tx: float, ty: float,
                            game_map) -> bool:
    """
    (ox,oy)→(tx,ty) 직선이 나무 수관에 막히면 True.
    24px 간격으로 샘플링해 tree_map의 canopy_rect()와 교차 확인.
    """
    dist = math.hypot(tx - ox, ty - oy)
    if dist < 1.0:
        return False
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


def has_line_of_sight(observer, target_coord: Tuple[float, float],
                      game_map) -> bool:
    """
    observer에서 target_coord까지 시야가 열려 있으면 True.
    ① 거리 ≤ vision_range
    ② 각도가 vision_angle 범위 안 (360이면 스킵)
    ③ 나무에 막히지 않음
    """
    ox, oy = observer.coordinate[0], observer.coordinate[1]
    tx, ty = target_coord[0], target_coord[1]

    if math.hypot(tx - ox, ty - oy) > observer.vision_range:
        return False

    if observer.vision_angle < 360:
        diff = abs(_angle_diff(observer.facing_angle,
                               math.atan2(ty - oy, tx - ox)))
        if diff > math.radians(observer.vision_angle / 2):
            return False

    return not _line_blocked_by_trees(ox, oy, tx, ty, game_map)


# ════════════════════════════════════════════════
#  Animal  —  모든 동물의 공통 부모 클래스
# ════════════════════════════════════════════════

class Animal:
    """
    공통 속성·메서드 정의. 모든 동물 클래스는 이 클래스(또는 하위 클래스)를 상속한다.

    하위 클래스에서 반드시 설정할 클래스 변수:
        SPECIES_VISION_RANGE : float  — 시야 거리 (픽셀)
        SPECIES_VISION_ANGLE : float  — 시야각 (도, 360 = 전방향)
    """

    SPECIES_VISION_RANGE: float = 150.0   # 미설정 시 폴백
    SPECIES_VISION_ANGLE: float = 120.0

    def __init__(
        self,
        name: str,
        coordinate: Tuple[float, float],
        hp: int = 100,
        max_hp: int = 100,
        stamina: float = 100.0,
        max_stamina: float = 100.0,
        max_speed: float = 80.0,
        hunger: float = 0.0,
        thirst: float = 0.0,
        detection_range: float = 150.0,
        age: int = 0,
        max_age: int = 3600,
        sex: str = "male",
        home_coordinate: Optional[Tuple[float, float]] = None,
        environment_status: str = "land",
    ):
        # 기본 정보
        self.name = name
        self.coordinate = list(coordinate)
        self.velocity = [0.0, 0.0]

        # 체력 / 스태미나
        self.hp = hp
        self.max_hp = max_hp
        self.stamina = stamina
        self.max_stamina = max_stamina

        # 이동
        self.accelerate = 200.0
        self.max_speed = max_speed

        # 욕구
        self.hunger = hunger
        self.thirst = thirst

        # 환경 / 나이
        self.environment_status = environment_status
        self.age = age
        self.max_age = max_age
        self.is_adult = False

        # 성별 / 번식
        self.sex = sex
        self.couple: Optional["Animal"] = None
        self.can_breed = False
        self.is_pregnant = False

        # 둥지
        self.home_coordinate = list(home_coordinate) if home_coordinate else None
        self.at_home = False

        # 상태 이상
        self.is_stunned = False
        self.stun_timer = 0.0
        self.is_poisoned = False
        self.poison_timer = 0.0
        self.poison_damage_per_sec = 2.0

        # 인식
        self.detection_range = detection_range

        # 시야 (FOV) — 클래스 변수에서 인스턴스 변수로 복사
        self.vision_range: float = self.SPECIES_VISION_RANGE
        self.vision_angle: float = self.SPECIES_VISION_ANGLE
        self.facing_angle: float = 0.0   # 라디안, 0 = 오른쪽

        # 내부 타이머
        self.age_timer = 0.0
        self.hunger_timer = 0.0
        self.thirst_timer = 0.0

        # 생존
        self.alive = True

    # ── 시야 (FOV) ─────────────────────────────

    def can_see(self, target: "Animal", game_map) -> bool:
        """target이 시야 안에 있으면 True (거리 + 각도 + 나무 차폐)."""
        if not target.alive:
            return False
        return has_line_of_sight(self, target.coordinate, game_map)

    def can_see_point(self, point: Tuple[float, float], game_map) -> bool:
        """좌표 하나가 시야 안에 있는지 확인."""
        return has_line_of_sight(self, point, game_map)

    def get_visible_animals(self, animals: List["Animal"], game_map) -> List["Animal"]:
        """시야 안에 있는 동물 목록."""
        return [a for a in animals if a is not self and self.can_see(a, game_map)]

    def _update_facing(self):
        """이동 방향으로 시선 갱신. 정지 중이면 유지."""
        if math.hypot(*self.velocity) > 5.0:
            self.facing_angle = math.atan2(self.velocity[1], self.velocity[0])

    def draw_fov_debug(self, screen: pygame.Surface, camera,
                       color=(80, 80, 0), alpha: int = 40):
        """시야 부채꼴 디버그 렌더링 (F4 등 디버그 키에 연결해서 사용)."""
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        r = int(self.vision_range * camera.zoom)
        surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        c = (r + 1, r + 1)
        if self.vision_angle >= 360:
            pygame.draw.circle(surf, (*color, alpha), c, r)
        else:
            half = math.radians(self.vision_angle / 2)
            start = math.degrees(self.facing_angle - half)
            end   = math.degrees(self.facing_angle + half)
            pts = [c]
            for i in range(21):
                a = math.radians(start + (end - start) * i / 20)
                pts.append((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))
            pygame.draw.polygon(surf, (*color, alpha), pts)
        screen.blit(surf, (int(sx) - r - 1, int(sy) - r - 1))

    # ── 이동 ────────────────────────────────────

    def move(self, dt: float, target: Optional[Tuple[float, float]] = None,
             speed_multiplier: float = 1.0):
        """target 방향으로 가속 이동. target=None이면 관성 감속."""
        if not self.alive or self.is_stunned:
            self._apply_friction(dt)
            return

        if target is not None:
            dx = target[0] - self.coordinate[0]
            dy = target[1] - self.coordinate[1]
            dist = math.hypot(dx, dy)
            if dist > 1.0:
                self.velocity[0] += dx / dist * self.accelerate * dt
                self.velocity[1] += dy / dist * self.accelerate * dt

        spd = math.hypot(*self.velocity)
        limit = self.max_speed * speed_multiplier
        if spd > limit:
            self.velocity[0] = self.velocity[0] / spd * limit
            self.velocity[1] = self.velocity[1] / spd * limit

        self.coordinate[0] += self.velocity[0] * dt
        self.coordinate[1] += self.velocity[1] * dt
        self._apply_friction(dt)
        self._update_facing()

    def _apply_friction(self, dt: float, friction: float = 6.0):
        f = max(0.0, 1.0 - friction * dt)
        self.velocity[0] *= f
        self.velocity[1] *= f

    def stop(self):
        self.velocity = [0.0, 0.0]

    # ── 체력 / 스태미나 ─────────────────────────

    def take_damage(self, amount: float, source: str = "unknown"):
        if not self.alive:
            return
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self._die(cause=source)

    def heal(self, amount: float):
        if not self.alive:
            return
        self.hp = min(self.max_hp, self.hp + amount)

    def use_stamina(self, amount: float) -> bool:
        """소모 성공이면 True, 스태미나 부족이면 False."""
        if self.stamina < amount:
            return False
        self.stamina -= amount
        return True

    def recover_stamina(self, dt: float, rate: float = 10.0):
        """배고픔이 높을수록 회복량 감소."""
        penalty = max(0.0, (self.hunger - 50) / 100)
        self.stamina = min(self.max_stamina,
                           self.stamina + rate * (1.0 - penalty * 0.5) * dt)

    # ── 먹기 / 마시기 ───────────────────────────

    def eat(self, food_value: float = 30.0):
        self.hunger = max(0.0, self.hunger - food_value)
        self.heal(food_value * 0.1)

    def drink(self, water_value: float = 30.0):
        self.thirst = max(0.0, self.thirst - water_value)

    # ── 공격 ────────────────────────────────────

    def attack(self, target: "Animal", damage: float = 10.0):
        """기본 공격. 하위 클래스에서 오버라이딩."""
        if not self.alive or not target.alive:
            return
        target.take_damage(damage, source=self.name)

    # ── 거리 / 위치 ─────────────────────────────

    def distance_to(self, other) -> float:
        """다른 Animal 또는 (x,y) 좌표까지의 거리."""
        if isinstance(other, Animal):
            tx, ty = other.coordinate[0], other.coordinate[1]
        else:
            tx, ty = other[0], other[1]
        return math.hypot(self.coordinate[0] - tx, self.coordinate[1] - ty)

    def is_at_home(self, threshold: float = 40.0) -> bool:
        if self.home_coordinate is None:
            return False
        return self.distance_to(self.home_coordinate) <= threshold

    def detect_nearby(self, animals: List["Animal"], game_map=None) -> List["Animal"]:
        """game_map 제공 시 FOV 기반 탐지, 없으면 거리만 체크."""
        if game_map is not None:
            return self.get_visible_animals(animals, game_map)
        return [a for a in animals
                if a is not self and a.alive
                and self.distance_to(a) <= self.vision_range]

    # ── 번식 ────────────────────────────────────

    def make_child(self) -> Optional["Animal"]:
        """자식 생성. 각 동물 클래스에서 오버라이딩."""
        return None

    def _check_can_breed(self):
        self.can_breed = (
            self.is_adult
            and not self.is_pregnant
            and self.hunger < 60
            and self.hp > self.max_hp * 0.4
        )

    # ── 내부 업데이트 ────────────────────────────

    def _update_age(self, dt: float):
        self.age_timer += dt
        if self.age_timer >= 1.0:
            self.age += int(self.age_timer)
            self.age_timer %= 1.0
        self.is_adult = self.age >= self.max_age * 0.15
        if self.age >= self.max_age:
            self._die(cause="old_age")

    def _update_hunger_thirst(self, dt: float):
        self.hunger_timer += dt
        self.thirst_timer += dt
        if self.hunger_timer >= 1.0:
            self.hunger = min(100.0, self.hunger + 0.8)
            self.hunger_timer = 0.0
            if self.hunger >= 100:
                self.take_damage(1.5, source="starvation")
        if self.thirst_timer >= 1.0:
            self.thirst = min(100.0, self.thirst + 1.2)
            self.thirst_timer = 0.0
            if self.thirst >= 100:
                self.take_damage(2.0, source="dehydration")

    def _update_status_effects(self, dt: float):
        if self.is_stunned:
            self.stun_timer -= dt
            if self.stun_timer <= 0:
                self.is_stunned = False
        if self.is_poisoned:
            self.poison_timer -= dt
            self.take_damage(self.poison_damage_per_sec * dt, source="poison")
            if self.poison_timer <= 0:
                self.is_poisoned = False

    def apply_stun(self, duration: float = 2.0):
        self.is_stunned = True
        self.stun_timer = max(self.stun_timer, duration)

    def apply_poison(self, duration: float = 5.0, dps: float = 2.0):
        self.is_poisoned = True
        self.poison_timer = max(self.poison_timer, duration)
        self.poison_damage_per_sec = max(self.poison_damage_per_sec, dps)

    def _die(self, cause: str = "unknown"):
        self.alive = False
        self.velocity = [0.0, 0.0]
        print(f"💀 {self.name} 사망 (원인: {cause})")

    # ── 메인 업데이트 ────────────────────────────

    def update(self, dt: float, game_map, weather, animals: List["Animal"]):
        """매 프레임 호출. 하위 클래스는 super().update(...)를 먼저 호출한다."""
        if not self.alive:
            return
        self._update_age(dt)
        self._update_hunger_thirst(dt)
        self._update_status_effects(dt)
        self.recover_stamina(dt)
        self._check_can_breed()
        self.at_home = self.is_at_home()

    # ── 렌더링 ──────────────────────────────────

    def draw(self, screen: pygame.Surface, camera):
        """기본 렌더링 (원 + 체력바). 하위 클래스에서 오버라이딩."""
        if not self.alive:
            return
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
        return (f"<{self.__class__.__name__} '{self.name}' "
                f"hp={self.hp}/{self.max_hp} "
                f"pos=({self.coordinate[0]:.0f},{self.coordinate[1]:.0f})>")


# ════════════════════════════════════════════════
#  Predator  —  포식자 공통 클래스
# ════════════════════════════════════════════════

class Predator(Animal):
    """
    포식자 공통 클래스. Animal을 상속.
    하위 클래스에서 설정:
        SPECIES_VISION_RANGE, SPECIES_VISION_ANGLE
    """

    def __init__(
        self,
        name: str,
        coordinate: Tuple[float, float],
        attack_range: float = 40.0,
        hunt_range: float = 200.0,
        hunt_success_rate: float = 0.6,
        hunger_limit: float = 50.0,
        **kwargs,
    ):
        super().__init__(name, coordinate, **kwargs)
        self.attack_range = attack_range
        self.hunt_range = hunt_range
        self.is_hunting = False
        self.hunting_target: Optional[Animal] = None
        self.hunt_success_rate = hunt_success_rate
        self.hunger_limit = hunger_limit
        self._chase_speed_mul = 1.4

    def find_target(self, animals: List[Animal], game_map) -> Optional[Animal]:
        """시야 안에서 가장 가까운 먹잇감을 반환."""
        candidates = [
            a for a in animals
            if a is not self and a.alive
            and not isinstance(a, self.__class__)
            and self.distance_to(a) <= self.hunt_range
            and self.can_see(a, game_map)
        ]
        return min(candidates, key=lambda a: self.distance_to(a), default=None)

    def start_hunt(self, target: Animal):
        self.is_hunting = True
        self.hunting_target = target

    def stop_hunt(self):
        self.is_hunting = False
        self.hunting_target = None

    def try_attack(self, target: Animal, base_damage: float = 20.0) -> bool:
        """attack_range 안에 있을 때 hunt_success_rate 확률로 공격. 성공 시 True."""
        if not target.alive:
            self.stop_hunt()
            return False
        if self.distance_to(target) <= self.attack_range:
            if random.random() < self.hunt_success_rate:
                self.attack(target, base_damage)
                self.eat(15.0)
                return True
        return False

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned:
            return

        if not self.is_hunting and self.hunger >= self.hunger_limit:
            target = self.find_target(animals, game_map)
            if target:
                self.start_hunt(target)

        if self.is_hunting and self.hunting_target:
            t = self.hunting_target
            if not t.alive or not self.can_see(t, game_map):
                self.stop_hunt()
            else:
                self.try_attack(t)
                self.move(dt, t.coordinate, self._chase_speed_mul)
                self.use_stamina(8.0 * dt)
        else:
            self.move(dt)


# ════════════════════════════════════════════════
#  Prey  —  피식자 공통 클래스
# ════════════════════════════════════════════════

class Prey(Animal):
    """
    피식자 공통 클래스. Animal을 상속.
    하위 클래스에서 설정:
        SPECIES_VISION_RANGE, SPECIES_VISION_ANGLE
    """

    def __init__(
        self,
        name: str,
        coordinate: Tuple[float, float],
        danger_range: float = 180.0,
        escape_success_rate: float = 0.55,
        hide_success_rate: float = 0.5,
        hide_range: float = 80.0,
        **kwargs,
    ):
        super().__init__(name, coordinate, **kwargs)
        self.predator_detected = False
        self.danger_range = danger_range
        self.escape_success_rate = escape_success_rate
        self.is_fleeing = False
        self.is_hiding = False
        self.hide_success_rate = hide_success_rate
        self.hide_range = hide_range
        self._flee_speed_mul = 1.5

    def detect_predators(self, animals: List[Animal], game_map) -> List[Animal]:
        """시야 안에 있는 포식자만 탐지. 나무 뒤는 감지 불가."""
        return [
            a for a in animals
            if isinstance(a, Predator) and a.alive
            and self.distance_to(a) <= self.danger_range
            and self.can_see(a, game_map)
        ]

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
        self.move(dt, (flee_x, flee_y), self._flee_speed_mul * self.escape_success_rate)
        self.use_stamina(10.0 * dt)

    def try_hide(self, game_map) -> bool:
        """hide_success_rate 확률로 은신 시도. 성공 시 True."""
        if random.random() < self.hide_success_rate:
            self.is_hiding = True
            self.stop()
            return True
        return False

    def stop_hiding(self):
        self.is_hiding = False

    def stop_fleeing(self):
        self.is_fleeing = False

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned:
            return

        predators = self.detect_predators(animals, game_map)

        if predators:
            self.predator_detected = True
            closest = min(predators, key=lambda p: self.distance_to(p))
            if self.distance_to(closest) < self.danger_range * 0.5:
                self.stop_hiding()
                self.flee_from(closest, dt)
            elif not self.is_hiding:
                if not self.try_hide(game_map):
                    self.flee_from(closest, dt)
        else:
            self.predator_detected = False
            self.stop_fleeing()
            self.stop_hiding()
            self.move(dt)