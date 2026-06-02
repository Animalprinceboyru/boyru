import pygame
import random
import math
from typing import Tuple, Optional, List
from animal import Animal, Predator, Egg


CHOI_IMAGE_CACHE={}

# ==========================================
# 1. 비행 동물 부모 클래스 (앵무새, 모기 등의 부모)
# ==========================================
class FlyingAnimal(Animal):
    SPECIES_VISION_RANGE: float = 200.0
    SPECIES_VISION_ANGLE: float = 160.0
    HATCH_TIME: float = 60.0 #일단 flying_animal은 모두 HATCH_TIME 통일해놓음/ 바꾸려면 이 함수 그대로 해당 클래스에 넣으면 됨(HATCH_TIME은 새로 정의)
    def __init__(self, name: str, coordinate: Tuple[float, float], flying_speed: float = 120.0, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.flying_speed = flying_speed
        self.can_fly = True
        self.is_flying = False
    
    def move(self, dt: float, target: Optional[Tuple[float, float]] = None, speed_multiplier: float = 1.0):
        """기본 move를 오버라이딩하여 비행 상태일 때 자동으로 스피드 버프를 적용합니다."""
        if self.is_flying:
            speed_ratio = self.flying_speed / self.max_speed
            super().move(dt, target, speed_multiplier=speed_ratio * speed_multiplier)
            self.use_stamina(2.0 * dt)
            
            if self.stamina <= 0:
                self.is_flying = False
        else:
            super().move(dt, target, speed_multiplier=speed_multiplier)
    
    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        """비행 중일 때는 전기뱀장어의 전기 공격만 정상 수치로 피해를 입고, 다른 공격은 회피합니다."""
        if self.is_flying:
            if source == "electric_shock" or (attacker and attacker.__class__.__name__ == "ElectricEel"):
                # 날든 말든 대미지 수치 자체는 가중치 없이 동일하게 받음
                super().take_damage(amount, source, attacker)
            else:
                # 전기뱀장어의 공격이 아니면 공중 회피(무시)
                return
        else:
            # 지상에 있을 때는 모든 데미지를 정상적으로 받음
            super().take_damage(amount, source, attacker)
    def attack(self, target: Optional[Animal] = None, base_damage: float = 15.0):
        """날면서 다른 대상을 공격할 때, 나의 비행 속도에 비례하여 타겟에게 더 큰 피해를 입힙니다."""
        if target and target.alive:
            if self.is_flying:
                # 💡 [핵심] 내가 날고 있을 때: 상대가 받는 대미지 = 기본 대미지 + 내 비행 속도의 15%
                extra_damage = self.flying_speed * 0.15
                final_damage = base_damage + extra_damage
                
                print(f"🦅 {self.name}이(가) 공중에서 고속({self.flying_speed:.1f})으로 강하하며 "
                      f"{target.name}에게 가속도가 붙은 강력한 타격({final_damage:.1f})을 입힙니다!")
                target.take_damage(final_damage, source="flying_attack", attacker=self)
            else:
                # 지상에 있을 때: 속도 가중치 없이 기본 데미지만 가함
                print(f"🦅 {self.name}이(가) 지상에서 부리로 {target.name}을(를) 쪼아 공격({base_damage:.1f})합니다!")
                target.take_damage(base_damage, source="peck_attack", attacker=self)
        else:
            # 타겟이 지정되지 않았을 경우를 대비한 예외 처리
            super().attack()
    
    def make_child(self): 
        breed_cost = 20.0
        # 스태미나 검사
        if self.stamina < breed_cost or (self.couple and self.couple.stamina < breed_cost):
            return None
        
        # 스태미나 소모
        self.use_stamina(breed_cost)
        if self.couple:
            self.couple.use_stamina(breed_cost)
            
        print(f"🥚 {self.name}이(가) 알을 낳았습니다!")
        return Egg(self.coordinate, self, hatch_time=self.HATCH_TIME)

    def _spawn_child(self):
        # 1. 50% 확률로 성별 결정
        child_sex = random.choice(["male", "female"])
        child = type(self)(name=f"{self.name}_child", coordinate=self.coordinate[:], sex=child_sex)
        
        # 2. 부모의 능력을 ±10% 오차 범위 내에서 무작위 유전
        child.max_hp = int(self.max_hp * random.uniform(0.9, 1.1))
        child.hp = child.max_hp  # 태어날 땐 최대 체력
        child.max_stamina = self.max_stamina * random.uniform(0.9, 1.1)
        child.max_speed = self.max_speed * random.uniform(0.9, 1.1)
        child.flying_speed = self.flying_speed * random.uniform(0.9, 1.1)
        
        return child
    


    def can_see(self, target: "Animal", game_map) -> bool:
        """나무 가림막(Canopy)을 무시하고 상공에서 내려다보는 시야"""
        if not target.alive:
            return False
            
        # 1. 시야 사거리 검사
        if self.distance_to(target) > self.vision_range:
            return False
            
        # 2. 시야각(FOV) 검사
        if self.vision_angle < 360:
            ox, oy = self.coordinate
            tx, ty = target.coordinate
            
            # 타겟을 향하는 절대 각도 계산
            target_angle = math.atan2(ty - oy, tx - ox)
            
            # 내 바라보는 방향과 타겟 각도의 차이 구하기 (-180도 ~ 180도로 정규화)
            diff = (target_angle - self.facing_angle) % (2 * math.pi)
            if diff > math.pi:
                diff -= 2 * math.pi
                
            # 내 시야각(vision_angle)의 절반보다 바깥에 있으면 안 보임
            if abs(diff) > math.radians(self.vision_angle / 2):
                return False
                
        # 3. 나무 장애물 검사 없이 무조건 통과!
        return True

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        if not self.alive or self.is_stunned:
            return
            
        if not self.is_flying and self.stamina > 20:
            self.is_flying = True
# ==========================================
# 2. 코뿔소 (Rhino)
# ==========================================
class Rhino(Animal):
    SPECIES_VISION_RANGE: float = 100.0
    SPECIES_VISION_ANGLE: float = 100.0
    def __init__(self, name: str, coordinate: Tuple[float, float], crash_power: float = 50.0, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.crash_power = crash_power
        self.max_speed = 90.0
        
        # 돌진 상태 관리를 위한 변수
        self.is_charging = False
        self.charge_target_tree = None
        # 💡 1. 여기서 코뿔소 전용 이미지를 설정합니다.
        self.image_path = "rhino.png"  # 코뿔소 이미지 파일명
        self.image = None
        
        # 이미지가 캐시에 없으면 최초 1회 로드
        if CHOI_IMAGE_CACHE[self.image_path]:
            orig_img = CHOI_IMAGE_CACHE[self.image_path]
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

    # 💡 2. 부모(animal.py)의 draw 함수를 무시하고 여기서 직접 그립니다.
    def draw(self, screen: pygame.Surface, camera):
        if not self.alive:
            return

        # 만약 이미지가 정상적으로 로드되었다면 이미지로 그림
        if self.image:
            # 화면 좌표 계산
            sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
            
            # 카메라 줌(Zoom) 비율에 맞춰 이미지 크기 조절
            scaled_size = int(self.image.get_width() * camera.zoom)
            scaled_image = pygame.transform.scale(self.image, (scaled_size, scaled_size))
            
            # 이미지 출력
            rect = scaled_image.get_rect(center=(sx, sy))
            screen.blit(scaled_image, rect)
            
            # (선택) 동물의 머리 위에 체력바를 간단하게 다시 그려줍니다.
            hp_ratio = self.hp / self.max_hp
            bar_w = 30 * camera.zoom
            bar_h = 4 * camera.zoom
            pygame.draw.rect(screen, (220, 60, 60), (sx - bar_w/2, sy - (scaled_size/2) - 10, bar_w, bar_h))
            pygame.draw.rect(screen, (100, 220, 120), (sx - bar_w/2, sy - (scaled_size/2) - 10, bar_w * hp_ratio, bar_h))
            
        else:
            # 이미지가 없거나 로드에 실패하면, 부모(animal.py)의 기본 원형 그리기 사용
            super().draw(screen, camera)

    def make_child(self):
        breed_cost = 40.0
        # 스태미나 검사
        if self.stamina < breed_cost or (self.couple and self.couple.stamina < breed_cost):
            return None
            
        # 스태미나 소모
        self.use_stamina(breed_cost)
        if self.couple:
            self.couple.use_stamina(breed_cost)

        # 1. 성별 결정
        child_sex = random.choice(["male", "female"])
        child = type(self)(name=f"{self.name}_child", coordinate=self.coordinate[:], sex=child_sex)
        
        # 2. 유전 및 돌연변이 (코뿔소는 돌진 파워도 유전됨)
        child.max_hp = int(self.max_hp * random.uniform(0.9, 1.1))
        child.hp = child.max_hp
        child.max_stamina = self.max_stamina * random.uniform(0.9, 1.1)
        child.max_speed = self.max_speed * random.uniform(0.9, 1.1)
        child.crash_power = self.crash_power * random.uniform(0.9, 1.1)
        
        print(f"🦏 {self.name}이(가) 건강한 새끼를 낳았습니다!")
        return child
    
    def start_charge(self, attacker: Animal):
        """공격자를 향하는 직선 방향으로 무작정 돌진을 시작합니다."""
        if not self.is_charging and self.use_stamina(30.0):
            self.is_charging = True
            self.charge_attacker = attacker
            
            # 포식자를 향하는 방향 벡터(dx, dy) 계산
            dx = attacker.coordinate[0] - self.coordinate[0]
            dy = attacker.coordinate[1] - self.coordinate[1]
            dist = math.hypot(dx, dy)
            
            if dist == 0:
                dx, dy = 1, 0
            else:
                dx, dy = dx / dist, dy / dist
                
            # 포식자 위치를 넘어서, 같은 방향으로 아주 멀리(예: 800픽셀)를 목적지로 설정 (연장선 돌진)
            self.charge_target_coord = (
                self.coordinate[0] + dx * 800.0,
                self.coordinate[1] + dy * 800.0
            )
            print(f"🦏 🔥 [{self.name}]가 치명상을 입고 격노하여 {attacker.name} 방향으로 맹렬히 돌진합니다!!")

    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        super().take_damage(amount, source, attacker)
        
        # 체력이 35% 이하로 떨어지고 복수할 공격자가 존재할 때 격노 발동
        if self.alive and self.hp <= self.max_hp * 0.35 and attacker and attacker.alive:
            if not self.is_charging:
                self.start_charge(attacker)

    def _stop_charge(self):
        """돌진 상태를 해제하고 멈춥니다."""
        self.is_charging = False
        self.charge_target_coord = None
        self.charge_attacker = None
        self.stop()

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        
        if not self.alive or self.is_stunned:
            return

        # ── 돌진 상태 업데이트 ──
        if self.is_charging and self.charge_target_coord:
            # 1. 목표 지점(연장선 끝)을 향해 2.5배속 이동
            self.move(dt, self.charge_target_coord, speed_multiplier=2.5)

            # 2. 돌진 경로 상에 포식자가 있는지 충돌 판정
            if self.charge_attacker and self.charge_attacker.alive:
                if self.distance_to(self.charge_attacker) <= 30.0:  # 충돌 반경 이내
                    print(f"💥 🦏 [{self.name}]의 초강력 박치기가 경로 상에 있던 {self.charge_attacker.name}에게 적중했습니다!")
                    self.charge_attacker.take_damage(self.crash_power, source="rhino_crash", attacker=self)
                    self._stop_charge()
                    return

            # 3. 돌진 경로 상에 나무가 있는지 충돌 판정 (현재 내 발밑 좌표 기준)
            tree = game_map.get_tree_at_pixel(self.coordinate[0], self.coordinate[1])
            if tree and not tree.broken:
                print(f"💥 쾅! [{self.name}]가 돌진 중 나무를 들이받아 부쉈습니다!")
                game_map.break_tree(tree)
                
                # 나무 위 원숭이 추락 처리
                for animal in animals:
                    if type(animal).__name__ == "Monkey" and getattr(animal, 'on_tree', False):
                        if self.distance_to(animal) < 60.0:
                            animal.on_tree = False
                            animal.current_tree = None
                            if hasattr(animal, 'apply_stun'):
                                animal.apply_stun(2.0)
                            print(f"쿵! 나무가 부서져 {animal.name}가 땅으로 떨어졌습니다!")
                
                # 나무를 부순 직후에는 충격으로 돌진 멈춤
                self._stop_charge()
                return

            # 4. 연장선 끝(목표 좌표)에 거의 도달했다면(아무것도 못 박고 허공에 돌진 끝남)
            dist_to_target = math.hypot(self.coordinate[0] - self.charge_target_coord[0], 
                                        self.coordinate[1] - self.charge_target_coord[1])
            if dist_to_target < 10.0:
                self._stop_charge()
        if not getattr(self, 'is_hunting', False) and not getattr(self, 'is_fleeing', False):
            # 1. 목표 좌표가 없다면 낮은 확률(약 2%)로 새로운 랜덤 목표지점 생성
            if not getattr(self, 'target_coord', None):
                if random.random() < 0.02: 
                    rx = self.coordinate[0] + random.uniform(-200.0, 200.0)
                    ry = self.coordinate[1] + random.uniform(-200.0, 200.0)
                    self.target_coord = [rx, ry]
            
            # 2. 목표 좌표가 생겼다면 그곳으로 이동
            if getattr(self, 'target_coord', None):
                self.move(dt, target=self.target_coord, speed_multiplier=0.5) # 평소엔 천천히 걷기
                
                # 3. 목표 지점에 거의 도달했으면 목표 초기화 (다시 가만히 있다가 다른 곳으로 이동)
                dist_to_target = math.hypot(
                    self.coordinate[0] - self.target_coord[0],
                    self.coordinate[1] - self.target_coord[1]
                )
                if dist_to_target < 10.0:
                    self.target_coord = None
        



# ==========================================
# 3. 전기뱀장어 (Electric Eel) - 포식자
# ==========================================
class ElectricEel(Predator):
    SPECIES_VISION_RANGE: float = 130.0
    SPECIES_VISION_ANGLE: float = 130.0
    def __init__(self, name: str, coordinate: Tuple[float, float], electric_power: float = 30.0, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.electric_power = electric_power
        self.max_speed = 70.0
    
    def move(self, dt: float, target: Optional[Tuple[float, float]] = None, speed_multiplier: float = 1.0):
        """environment_status를 이용해 물에 있는지 판단하고 속도를 조정합니다."""
        if getattr(self, 'environment_status', '') == 'water':
            # 물속에서는 고속 수영 버프 (1.6배)
            super().move(dt, target, speed_multiplier=speed_multiplier * 1.6)
        else:
            # 육지 위로 올라왔을 때는 느리게 기어가는 패널티 (0.4배)
            super().move(dt, target, speed_multiplier=speed_multiplier * 0.4)
    
    def make_child(self):
        breed_cost = 25.0
        if self.stamina < breed_cost or (self.couple and self.couple.stamina < breed_cost):
            return None
            
        self.use_stamina(breed_cost)
        if self.couple:
            self.couple.use_stamina(breed_cost)
            
        print(f"🥚 {self.name}이(가) 물속에 알을 낳았습니다!")
        return Egg(self.coordinate, self, hatch_time=60.0)

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
        """수중 이동: 물가나 물속에서 속도 증가 버프를 받습니다."""
        self.move(dt, target, speed_multiplier=1.4)

    # [기능 1] 날씨 시스템 시너지 (weather 매개변수 추가)
    def electric_attack(self, target: Animal, animals: List[Animal], weather=None):
        """전기뱀장어의 특수 공격 (수중 광역 데미지 및 날씨 시너지 포함)"""
        base_damage = 30.0
        aoe_radius = 150.0      # 전류가 닿는 기본 최대 반경
        max_aoe_damage = 25.0   # 중심부 기본 최대 광역 데미지
        
        # ⛈️ 날씨 시너지: 비나 폭풍우가 내릴 때 위력과 범위 대폭 증가
        is_raining = False
        if weather and hasattr(weather, 'current'):
            # WeatherType Enum 호환성을 위해 문자열 확인
            if getattr(weather.current, 'name', '') in ["RAINY", "STORM"]:
                is_raining = True

        if is_raining:
            base_damage *= 1.5
            aoe_radius *= 2.0
            max_aoe_damage *= 1.5
            print(f"⛈️ 궂은 날씨로 인해 [{self.name}]의 전기 공격 반경이 2배로 넓어집니다!")

        # 1. 직접 공격 대상에게 데미지 및 기절 부여
        target.take_damage(base_damage, source=self.name, attacker=self)
        target.apply_stun(duration=2.5) 
        
        # 2. 자신이 물 속에 있을 경우 주변에 전류 방출
        if self.environment_status == "water":
            for a in animals:
                # 자신과 직접 타겟 제외, 살아있고 물 속에 있는 동물만 필터링
                if a is not self and a is not target and a.alive and getattr(a, 'environment_status', 'land') == "water":
                    dist = self.distance_to(a)
                    if dist <= aoe_radius:
                        # 거리에 반비례하는 데미지 계산
                        dist = max(1.0, dist) 
                        shock_damage = max_aoe_damage * (1.0 - (dist / aoe_radius))
                        
                        if shock_damage > 0:
                            a.take_damage(shock_damage, source="electric_shock", attacker=self)
                            a.apply_stun(duration=1.5) # 광역 감전 시에도 짧게 기절
                            print(f"⚡ [{a.name}]이(가) 물을 타고 흐른 전기에 감전되었습니다! (피해량: {shock_damage:.1f})")

    # [기능 2] 방어적 방전 (Defensive Discharge)
    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        """피격 시 공격자에게 전기를 방출하여 반격"""
        # 부모 클래스의 원래 데미지 받는 처리 먼저 실행
        super().take_damage(amount, source, attacker)
        
        # 공격자가 있고, 내가 아직 살아있으며, 스태미나가 충분하다면 반격!
        if attacker and attacker.alive and self.alive and self.use_stamina(10.0):
            print(f"⚡ [{self.name}]이(가) 자신을 공격한 {attacker.name}에게 방어적 방전을 일으킵니다!")
            attacker.take_damage(15.0, source="defensive_shock", attacker=self)
            attacker.apply_stun(duration=2.0)

    # 기절 연계 포식 시스템 (Execution)
    def try_attack(self, target: Animal, base_damage: float = 20.0, food_value: float = 30.0) -> bool:
        """기절한 적에게는 100% 명중 및 2배 데미지 (처형)"""
        if not target.alive:
            self.stop_hunt()
            return False
            
        if self.distance_to(target) <= self.attack_range:
            # 타겟이 기절(Stun) 상태인지 확인
            if getattr(target, 'is_stunned', False):
                print(f"💥 [{self.name}]이(가) 기절한 {target.name}에게 치명적인 일격을 가합니다!")
                # 기절 상태면 Predator의 확률 계산을 무시하고 무조건 명중, 데미지 2배
                self.attack(target, base_damage * 2.0)
                if not target.alive:
                    self.eat(food_value)
                return True
            else:
                # 기절 상태가 아니면 원래 Predator의 확률 기반 공격 로직 따름
                return super().try_attack(target, base_damage, food_value)
        return False

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        
        # 사냥(Hunting) 중 타겟에 접근 시 일정 확률로 전기 공격
        if self.is_hunting and self.hunting_target:
            if self.distance_to(self.hunting_target) <= self.attack_range + 20:
                if random.random() < 0.05: 
                    # 수정됨: weather 객체도 함께 넘겨주어 날씨 시너지 확인
                    self.electric_attack(self.hunting_target, animals, weather)


# ==========================================
# 4. 독개구리 (Toxic Frog)
# ==========================================
class ToxicFrog(Animal):
    SPECIES_VISION_RANGE: float = 130.0
    SPECIES_VISION_ANGLE: float = 140.0
    HATCH_TIME: float = 60.0
    def __init__(self, name: str, coordinate: Tuple[float, float], poison_amount: float = 4.0, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.poison_amount = poison_amount
        self.max_speed = 45.0
    
    def make_child(self):
        breed_cost = 15.0
        if self.stamina < breed_cost or (self.couple and self.couple.stamina < breed_cost):
            return None
            
        self.use_stamina(breed_cost)
        if self.couple:
            self.couple.use_stamina(breed_cost)
            
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
        """도약 이동: 스태미나를 소모해 순간적으로 거리를 벌립니다."""
        if self.use_stamina(10.0):
            self.move(dt, target, speed_multiplier=2.5) # 짧은 순간 속도 폭발

    def poison(self, attacker: Animal):
        """자신을 공격한 포식자나 모기에게 독 효과를 부여합니다."""
        print(f"☠️ [{self.name}]의 맹독이 {attacker.name}에게 퍼집니다!")
        attacker.apply_poison(duration=8.0, dps=self.poison_amount)
        
        # 프로젝트 계획서대로 상대의 체력 외에도 속도/스태미나에 패널티 부여
        attacker.stamina = max(0, attacker.stamina - 20.0)
        attacker.max_speed = max(10.0, attacker.max_speed * 0.8)

    def take_damage(self, amount: float, source: str = "unknown", attacker: Optional[Animal] = None):
        """Animal의 기본 피해 공식을 오버라이딩하여, 피해를 입으면 공격자에게 독 발동"""
        # 상위 클래스의 데미지 처리 호출
        super().take_damage(amount, source) 
        
        # 공격자(attacker) 객체가 전달되었고 살아있다면 독 발동
        if attacker and attacker.alive:
            self.poison(attacker)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        
        if not self.alive or self.is_stunned:
            return
        
        if self.hunger>30.0:
            for a in animals:
                if a.__class__.__name__ == "Mosquito" and a.alive:
                    dist = self.distance_to(a)

                    #혀가 닿는 사거리 이내일 때
                    if dist<30.0:
                        print(f"🐸 {self.name}이(가) {a.name}을(를) 잡아먹었습니다!")
                        a.take_damage(999.0, source=self.name, attacker=self) # 모기 즉사
                        self.eat(15.0) # 배고픔 15 회복
                        break

                    #도약해서 먹을 수 있을 때
                    elif dist <= 120.0 and self.stamina >= 10.0:
                        self.jump(dt, target=a.coordinate)
                        break