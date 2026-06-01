import pygame
import random
from typing import Tuple, Optional, List
from animal import Animal, Predator

# ==========================================
# 1. 비행 동물 부모 클래스 (앵무새, 모기 등의 부모)
# ==========================================
class FlyingAnimal(Animal):
    def __init__(self, name: str, coordinate: Tuple[float, float], flying_speed: float = 120.0, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.flying_speed = flying_speed
        self.can_fly = True
        self.is_flying = False

    def fly(self, dt: float, target: Optional[Tuple[float, float]] = None):
        """비행 이동: 기본 이동(move)을 사용하되 flying_speed에 비례해 속도를 높입니다."""
        self.is_flying = True
        # max_speed 대비 flying_speed의 비율로 스피드 버프 적용
        speed_ratio = self.flying_speed / self.max_speed
        self.move(dt, target, speed_multiplier=speed_ratio)
        self.use_stamina(2.0 * dt)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        # 스태미나가 충분하면 기본적으로 비행 상태 유지
        if not self.is_flying and self.stamina > 20:
            self.is_flying = True


# ==========================================
# 2. 코뿔소 (Rhino)
# ==========================================
class Rhino(Animal):
    def __init__(self, name: str, coordinate: Tuple[float, float], crash_power: float = 50.0, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.crash_power = crash_power
        self.max_speed = 90.0

    def crash(self, target_tree, game_map, animals: List[Animal]):
        """돌진하여 나무를 부수고 나무 위 원숭이를 강제로 떨어뜨립니다."""
        if self.use_stamina(30.0):
            print(f"[{self.name}]가 {target_tree.tree_type} 나무로 돌진합니다!")
            game_map.break_tree(target_tree)
            
            # 주변 동물 탐색: 나무 위에 있는 원숭이 추락 처리
            for animal in animals:
                if type(animal).__name__ == "Monkey" and getattr(animal, 'on_tree', False):
                    if self.distance_to(animal) < 60.0:
                        animal.on_tree = False
                        animal.apply_stun(2.0)
                        print(f"쿵! 나무가 부서져 {animal.name}가 땅으로 떨어졌습니다!")

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        # 포식자에게 공격받을 시 돌진(crash)을 방어 기제로 사용하는 로직 등을 여기에 추가


# ==========================================
# 3. 전기뱀장어 (Electric Eel) - 포식자
# ==========================================
class ElectricEel(Predator): # 사냥 AI가 포함된 Predator 상속
    def __init__(self, name: str, coordinate: Tuple[float, float], electric_power: float = 30.0, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.electric_power = electric_power
        self.environment_status = "water" # 기본 서식지는 물
        self.max_speed = 70.0

    def swim(self, dt: float, target: Optional[Tuple[float, float]] = None):
        """수중 이동: 물가나 물속에서 속도 증가 버프를 받습니다."""
        self.move(dt, target, speed_multiplier=1.4)

    def electric_attack(self, target: Animal):
        """특수 공격: 데미지와 함께 기절(stun) 부여"""
        if self.use_stamina(15.0):
            print(f"⚡ [{self.name}]가 {target.name}에게 전기 공격을 방출했습니다!")
            target.take_damage(self.electric_power, source=self.name)
            target.apply_stun(duration=2.5)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        super().update(dt, game_map, weather, animals)
        
        # 사냥(Hunting) 중 타겟에 접근 시 일정 확률로 전기 공격
        if self.is_hunting and self.hunting_target:
            if self.distance_to(self.hunting_target) <= self.attack_range + 20:
                if random.random() < 0.05: # 프레임당 낮은 확률로 발동
                    self.electric_attack(self.hunting_target)


# ==========================================
# 4. 독개구리 (Toxic Frog)
# ==========================================
class ToxicFrog(Animal):
    def __init__(self, name: str, coordinate: Tuple[float, float], poison_amount: float = 4.0, **kwargs):
        super().__init__(name, coordinate, **kwargs)
        self.poison_amount = poison_amount
        self.max_speed = 45.0

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
        # 모기(Mosquito)가 시야에 있으면 사냥(Jump 등 활용)하는 AI 로직 추가 가능