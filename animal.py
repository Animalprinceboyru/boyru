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


def _line_blocked_by_trees(ox: float, oy: float,
                            tx: float, ty: float,
                            game_map) -> bool:
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
#  Animal
# ════════════════════════════════════════════════

class Animal:
    """
    공통 속성·메서드 정의. 모든 동물 클래스는 이 클래스(또는 하위 클래스)를 상속한다.

    하위 클래스에서 반드시 설정할 클래스 변수:
        SPECIES_VISION_RANGE : float  — 시야 거리 (픽셀)
        SPECIES_VISION_ANGLE : float  — 시야각 (도, 360 = 전방향)
    """

    SPECIES_VISION_RANGE: float = 150.0
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
        max_accelerate: float = 200.0,
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
        # max_accelerate: 배부를 때 최대 가속도
        # accelerate: hunger에 따라 감소하는 실제 가속도 (프로퍼티)
        self.max_accelerate = max_accelerate
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

        # 둥지
        self.home_coordinate = list(home_coordinate) if home_coordinate else None
        self.at_home = False
        self.home_threshold = 40.0      # 집 인식 거리 — 하위 클래스에서 덮어쓰기 가능
        self.home_build_prob = 0.002    # 커플일 때 매초 집 짓는 확률
        self.breed_prob = 0.001         # 집에 있을 때 매초 번식 확률
        self.home_range = 80.0          # 집 버프 적용 거리 — 하위 클래스에서 덮어쓰기 가능
        self._home_timer = 0.0

        # 상태 이상
        self.is_stunned = False
        self.stun_timer = 0.0
        self.is_poisoned = False
        self.poison_timer = 0.0
        self.poison_damage_per_sec = 2.0
        self.poison_speed_multiplier = 0.6

        # 인식
        self.detection_range = detection_range

        # 시야 (FOV)
        self.vision_range: float = self.SPECIES_VISION_RANGE
        self.vision_angle: float = self.SPECIES_VISION_ANGLE
        self.facing_angle: float = 0.0

        # 내부 타이머
        self.age_timer = 0.0
        self.hunger_timer = 0.0
        self.thirst_timer = 0.0

        # 생존
        self.alive = True

    # ── 가속도 (hunger에 따라 감소) ─────────────

    @property
    def accelerate(self) -> float:
        """
        실제 가속도 = max_accelerate * (1 - hunger/100 * 0.5)
        배고픔이 최대일 때 가속도가 절반으로 감소.
        """
        hunger_factor = 1.0 - (self.hunger / 100.0) * 0.5
        return self.max_accelerate * hunger_factor

    # ── 시야 (FOV) ─────────────────────────────

    def can_see(self, target: "Animal", game_map) -> bool:
        if not target.alive:
            return False
        return has_line_of_sight(self, target.coordinate, game_map)

    def can_see_point(self, point: Tuple[float, float], game_map) -> bool:
        return has_line_of_sight(self, point, game_map)

    def get_visible_animals(self, animals: List["Animal"], game_map) -> List["Animal"]:
        return [a for a in animals if a is not self and self.can_see(a, game_map)]

    def _update_facing(self):
        if math.hypot(*self.velocity) > 5.0:
            self.facing_angle = math.atan2(self.velocity[1], self.velocity[0])

    def draw_fov_debug(self, screen: pygame.Surface, camera,
                       color=(80, 80, 0), alpha: int = 40):
        """시야 부채꼴 디버그 렌더링. system.py에서 원하는 키에 연결해서 사용."""
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
        poison_mul = self.poison_speed_multiplier if self.is_poisoned else 1.0
        limit = self.max_speed * speed_multiplier * self._home_speed_multiplier() * poison_mul
        if spd > limit:
            self.velocity[0] = self.velocity[0] / spd * limit
            self.velocity[1] = self.velocity[1] / spd * limit

        self.coordinate[0] += self.velocity[0] * dt
        self.coordinate[1] += self.velocity[1] * dt
        self._apply_friction(dt)
        self._update_facing()

    def _apply_friction(self, dt: float):
        """accelerate를 반대 방향으로 적용해 감속."""
        spd = math.hypot(*self.velocity)
        if spd < 1.0:
            self.velocity = [0.0, 0.0]
            return
        new_spd = max(0.0, spd - self.accelerate * dt)
        self.velocity[0] = self.velocity[0] / spd * new_spd
        self.velocity[1] = self.velocity[1] / spd * new_spd

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
        if self.stamina < amount:
            return False
        self.stamina -= amount
        return True

    def recover_stamina(self, dt: float, rate: float = 10.0):
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
        if isinstance(other, Animal):
            tx, ty = other.coordinate[0], other.coordinate[1]
        else:
            tx, ty = other[0], other[1]
        return math.hypot(self.coordinate[0] - tx, self.coordinate[1] - ty)

    def is_at_home(self) -> bool:
        if self.home_coordinate is None:
            return False
        return self.distance_to(self.home_coordinate) <= self.home_threshold

    def near_home(self) -> bool:
        if self.home_coordinate is None:
            return False
        return self.distance_to(self.home_coordinate) <= self.home_range

    def _home_speed_multiplier(self) -> float:
        return 1.15 if self.near_home() else 1.0

    def detect_nearby(self, animals: List["Animal"], game_map=None) -> List["Animal"]:
        """
        game_map 있으면 FOV 기반 탐지 (거리+각도+나무 차폐).
        game_map 없으면 vision_range 이내 거리만 체크.
        """
        if game_map is not None:
            return self.get_visible_animals(animals, game_map)
        return [a for a in animals
                if a is not self and a.alive
                and self.distance_to(a) <= self.vision_range]

    # ── 집 / 번식 ───────────────────────────────

    def _update_home(self, dt: float):
        self._home_timer += dt
        if self._home_timer < 1.0:
            return
        self._home_timer = 0.0

        # 집 짓기 — 커플이 있고 집이 없을 때 현재 위치에 생성
        if (self.couple is not None and self.couple.alive
                and self.home_coordinate is None):
            if random.random() < self.home_build_prob:
                self.home_coordinate = list(self.coordinate)
                self.couple.home_coordinate = list(self.coordinate)
                print(f"{self.name} 집 생성: {self.coordinate}")

        # 번식 — 집에 있고 번식 가능할 때
        if (self.home_coordinate is not None
                and self.at_home and self.can_breed):
            if random.random() < self.breed_prob:
                child = self.make_child()
                if child:
                    print(f"{self.name} 번식 성공!")
                return child

        return None

    def _update_home_buff(self, dt: float):
        if self.near_home():
            self.heal(3.0 * dt)
            self.stamina = min(self.max_stamina, self.stamina + 5.0 * dt)

    def make_child(self) -> Optional["Animal"]:
        """
        자식 생성. 하위 클래스에서 오버라이딩.
        예시:
            def make_child(self):
                return Anaconda(coordinate=self.coordinate)
        반환된 객체는 _update_home()에서 받아 animals 리스트에 추가한다.
        """
        return None

    def _check_can_breed(self):
        self.can_breed = (
            self.is_adult
            and self.hunger < 60
            and self.hp > self.max_hp * 0.4
        )

    # ── 상태 이상 ────────────────────────────────

    def apply_stun(self, duration: float = 2.0):
        self.is_stunned = True
        self.stun_timer = max(self.stun_timer, duration)

    def apply_poison(self, duration: float = 5.0, dps: float = 2.0,
                     speed_multiplier: float = 0.6):
        """
        독 부여.
        duration         : 지속 시간 (초)
        dps              : 초당 체력 감소량 — 하위 클래스에서 결정
        speed_multiplier : 이속 배율 (0~1) — 하위 클래스에서 결정
        """
        self.is_poisoned = True
        self.poison_timer = max(self.poison_timer, duration)
        self.poison_damage_per_sec = max(self.poison_damage_per_sec, dps)
        self.poison_speed_multiplier = min(self.poison_speed_multiplier, speed_multiplier)

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
            if self.hunger >= 100.0:
                self._die(cause="starvation")   # 즉시 사망

        if self.thirst_timer >= 1.0:
            self.thirst = min(100.0, self.thirst + 1.2)
            self.thirst_timer = 0.0
            if self.thirst >= 100.0:
                self._die(cause="dehydration")  # 즉시 사망

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
                self.poison_speed_multiplier = 0.6

    def _die(self, cause: str = "unknown"):
        self.alive = False
        self.velocity = [0.0, 0.0]
        print(f"{self.name} 사망 (원인: {cause})")

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
        self._update_home(dt)
        self._update_home_buff(dt)

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
#  Predator
# ════════════════════════════════════════════════

class Predator(Animal):
    """
    포식자 공통 클래스.
    하위 클래스에서 설정: SPECIES_VISION_RANGE, SPECIES_VISION_ANGLE
    """

    def __init__(
        self,
        name: str,
        coordinate: Tuple[float, float],
        attack_range: float = 40.0,
        hunt_range: float = 200.0,
        attack_success_rate: float = 0.6,   # 공격 성공 확률
        hunger_limit: float = 50.0,
        chase_speed_mul: float = 1.4,        # 추격 시 이속 배율
        **kwargs,
    ):
        super().__init__(name, coordinate, **kwargs)
        self.attack_range = attack_range
        self.hunt_range = hunt_range
        self.attack_success_rate = attack_success_rate
        self.hunger_limit = hunger_limit
        self.chase_speed_mul = chase_speed_mul
        self.is_hunting = False
        self.hunting_target: Optional[Animal] = None

    def find_target(self, animals: List[Animal], game_map) -> Optional[Animal]:
        """시야 안에서 가장 가까운 먹잇감 반환."""
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

    def try_attack(self, target: Animal, base_damage: float = 20.0,
                   food_value: float = 30.0) -> bool:
        """
        attack_range 안에서 attack_success_rate 확률로 공격.
        target이 사망하면 eat() 호출.
        food_value: 먹잇감을 먹었을 때 배고픔 감소량 — 하위 클래스 또는 main에서 결정.
        """
        if not target.alive:
            self.stop_hunt()
            return False
        if self.distance_to(target) <= self.attack_range:
            if random.random() < self.attack_success_rate:
                self.attack(target, base_damage)
                if not target.alive:        # 공격으로 죽었을 때만 eat()
                    self.eat(food_value)
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
                self.move(dt, t.coordinate, self.chase_speed_mul)
                self.use_stamina(8.0 * dt)
        else:
            self.move(dt)


# ════════════════════════════════════════════════
#  Prey
# ════════════════════════════════════════════════

class Prey(Animal):
    """
    피식자 공통 클래스.
    하위 클래스에서 설정: SPECIES_VISION_RANGE, SPECIES_VISION_ANGLE
    """

    def __init__(
        self,
        name: str,
        coordinate: Tuple[float, float],
        danger_range: float = 180.0,
        hide_success_rate: float = 0.5,
        hide_range: float = 80.0,           # 나무를 찾는 범위
        flee_speed_mul: float = 1.5,        # 도망 시 이속 배율
        **kwargs,
    ):
        super().__init__(name, coordinate, **kwargs)
        self.predator_detected = False
        self.danger_range = danger_range
        self.is_fleeing = False
        self.is_hiding = False
        self.hide_success_rate = hide_success_rate
        self.hide_range = hide_range
        self.flee_speed_mul = flee_speed_mul
        self._hiding_from: Optional[Animal] = None  # 숨은 대상 포식자

    def detect_predators(self, animals: List[Animal], game_map) -> List[Animal]:
        """시야 안에 있는 포식자만 탐지."""
        return [
            a for a in animals
            if isinstance(a, Predator) and a.alive
            and self.distance_to(a) <= self.danger_range
            and self.can_see(a, game_map)
        ]

    def flee_from(self, predator: Animal, dt: float):
        """포식자 반대 방향으로 flee_speed_mul 배속으로 도주."""
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
        """
        도망 방향(포식자 반대) 기준 ±60° 이내 나무 중 가장 가까운 곳으로 숨기 시도.
        나무가 클수록 성공률 보정값이 높아짐.
        성공 시: 정지 + is_hiding=True + 포식자 사냥 종료.
        """
        # 도망 방향 계산 (포식자 반대)
        dx = self.coordinate[0] - predator.coordinate[0]
        dy = self.coordinate[1] - predator.coordinate[1]
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            flee_angle = 0.0
        else:
            flee_angle = math.atan2(dy, dx)

        HIDE_ANGLE_LIMIT = math.radians(60)  # ±60° 이내 나무만 탐색

        # 도망 방향 ±60° + hide_range 안 나무 탐색
        candidates = []
        for tree in game_map.trees:
            if tree.broken:
                continue
            tx, ty = tree.coordinate
            tree_dist = self.distance_to((tx, ty))
            if tree_dist > self.hide_range:
                continue
            # 나무 방향과 도망 방향의 각도 차이
            angle_to_tree = math.atan2(ty - self.coordinate[1],
                                       tx - self.coordinate[0])
            if abs(_angle_diff(flee_angle, angle_to_tree)) <= HIDE_ANGLE_LIMIT:
                candidates.append((tree, tree_dist))

        if not candidates:
            return False

        # 가장 가까운 나무 선택
        best_tree, _ = min(candidates, key=lambda x: x[1])

        # 나무 크기에 따라 성공률 보정 (2x2=기본, 4x4=최대 보정)
        size_bonus = (best_tree.width_tiles * best_tree.height_tiles - 4) * 0.05
        final_rate = min(0.95, self.hide_success_rate + size_bonus)

        if random.random() < final_rate:
            self.is_hiding = True
            self._hiding_from = predator
            self.stop()
            if hasattr(predator, 'stop_hunt'):
                predator.stop_hunt()
            return True

        return False

    def stop_hiding(self):
        self.is_hiding = False
        self._hiding_from = None

    def stop_fleeing(self):
        self.is_fleeing = False

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned:
            return

        # 은신 중: 포식자가 danger_range를 벗어날 때까지 대기
        if self.is_hiding:
            if (self._hiding_from is None
                    or not self._hiding_from.alive
                    or self.distance_to(self._hiding_from) > self.danger_range):
                self.stop_hiding()
            return  # 은신 중엔 다른 행동 없음

        predators = self.detect_predators(animals, game_map)

        if predators:
            self.predator_detected = True
            closest = min(predators, key=lambda p: self.distance_to(p))

            # 매우 가까우면 도망, 그 외엔 은신 시도
            if self.distance_to(closest) < self.danger_range * 0.5:
                self.stop_fleeing()
                self.flee_from(closest, dt)
            else:
                if not self.try_hide(game_map, closest):
                    self.flee_from(closest, dt)
        else:
            self.predator_detected = False
            self.stop_fleeing()
            self.move(dt)