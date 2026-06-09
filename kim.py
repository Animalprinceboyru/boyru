import random
import math
import pygame
from typing import Tuple, List, Optional

from animal import Animal, Prey, Egg, TILE_SIZE
from Choi_animals import FlyingAnimal
import camera

MOSQUITO_IMAGE_CACHE = {}

class Mosquito(FlyingAnimal):
    """
    모기 클래스 - FlyingAnimal을 상속받음
    """
    
    SPECIES_VISION_RANGE = 180.0
    SPECIES_VISION_ANGLE = 360.0
    HATCH_TIME = 40.0
    minimap_color = (255, 255, 255)

    def __init__(self, name: str, coordinate: Tuple[float, float], **kwargs):
        super().__init__(name, coordinate, flying_speed=180.0, **kwargs)
        self.max_hp = 30
        self.hp = 30
        self.max_speed = 60.0
        self.max_stamina = 50.0
        self.stamina = 50.0
        
        self.bite_damage = 5.0        
        self.bite_poison_dps = 2.0    
        self.bite_poison_duration = 5.0
        self.bite_cooldown = 0.0
        self.bite_range = 25.0
        self.bite_success_rate = 0.7
        
        self.image_path = "mosquito.png"
        self.image = None
        
        if self.image_path not in MOSQUITO_IMAGE_CACHE:
            try:
                loaded_img = pygame.image.load(self.image_path).convert_alpha()
                MOSQUITO_IMAGE_CACHE[self.image_path] = loaded_img
            except Exception as e:
                print(f"⚠️ {name} 이미지 로드 실패: {e}")
                MOSQUITO_IMAGE_CACHE[self.image_path] = None
        
        orig_img = MOSQUITO_IMAGE_CACHE[self.image_path]
        if orig_img:
            orig_w, orig_h = orig_img.get_size()
            target_max_size = int(self.size * 2.5)
            scale_factor = target_max_size / max(orig_w, orig_h)
            new_w = int(orig_w * scale_factor)
            new_h = int(orig_h * scale_factor)
            self.image = pygame.transform.scale(orig_img, (new_w, new_h))

    def draw(self, screen: pygame.Surface, camera):
        if not self.alive:
            return
        
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        margin = 100
        if not (-margin < sx < camera.screen_w + margin and -margin < sy < camera.screen_h + margin):
            return

        offset_y = -12 if self.is_flying else 0

        if self.image:
            new_w = int(self.image.get_width() * camera.zoom)
            new_h = int(self.image.get_height() * camera.zoom)
            
            scaled_image = pygame.transform.scale(self.image, (new_w, new_h))
            angle_deg = math.degrees(-self.facing_angle)
            rotated_image = pygame.transform.rotate(scaled_image, angle_deg)
            
            rect = rotated_image.get_rect(center=(sx, int(sy) + offset_y))
            screen.blit(rotated_image, rect)
            
            hp_ratio = self.hp / self.max_hp
            bar_w = int(12 * camera.zoom)
            bar_h = int(2 * camera.zoom)
            bx = int(sx) - bar_w // 2
            by = int(sy) + offset_y - int(new_h/2) - 6
            
            pygame.draw.rect(screen, (80, 0, 0), (bx, by, bar_w, bar_h))
            pygame.draw.rect(screen, (100, 220, 120), (bx, by, int(bar_w * hp_ratio), bar_h))
            
            if self.is_poisoned:
                pygame.draw.circle(screen, (100, 255, 100), (int(sx) + 3, int(sy) + offset_y - 5), 2)
        else:
            pygame.draw.circle(screen, (255, 255, 255), (int(sx), int(sy) + offset_y), max(2, int(4 * camera.zoom)))
            
            hp_ratio = self.hp / self.max_hp
            bar_w = int(12 * camera.zoom)
            bar_h = int(2 * camera.zoom)
            bx = int(sx) - bar_w // 2
            by = int(sy) + offset_y - int(8 * camera.zoom) - 6
            
            pygame.draw.rect(screen, (80, 0, 0), (bx, by, bar_w, bar_h))
            pygame.draw.rect(screen, (100, 220, 120), (bx, by, int(bar_w * hp_ratio), bar_h))
            if self.is_poisoned:
                pygame.draw.circle(screen, (100, 255, 100), (int(sx) + 3, int(sy) + offset_y - 5), 2)

    def make_child(self):
        breed_cost = 8.0
        if self.stamina < breed_cost or (self.couple and self.couple.stamina < breed_cost):
            return None
        
        self.use_stamina(breed_cost)
        if self.couple:
            self.couple.use_stamina(breed_cost)
        
        print(f"🥚 {self.name}이(가) 작은 알을 낳았습니다!")
        return Egg(self.coordinate, self, hatch_time=self.HATCH_TIME)

    def _spawn_child(self):
        child_sex = random.choice(["male", "female"])
        child = type(self)(name=f"{self.name}_child", coordinate=self.coordinate[:], sex=child_sex)
        
        child.max_hp = int(self.max_hp * random.uniform(0.9, 1.1))
        child.hp = child.max_hp
        child.max_stamina = self.max_stamina * random.uniform(0.9, 1.1)
        child.max_speed = self.max_speed * random.uniform(0.9, 1.1)
        child.flying_speed = self.flying_speed * random.uniform(0.9, 1.1)
        child.bite_damage = self.bite_damage * random.uniform(0.9, 1.1)
        
        return child

    def bite(self, target: Animal):
        if not target.alive:
            return False
        
        if self.distance_to(target) <= self.bite_range and self.bite_cooldown <= 0:
            self.bite_cooldown = 1.5
            target.take_damage(self.bite_damage, source=f"{self.name}_bite", attacker=self)
            target.apply_poison(duration=self.bite_poison_duration, dps=self.bite_poison_dps)
            self.heal(self.bite_damage * 0.6)
            self.eat(5.0)
            
            print(f"🦟 [{self.name}]이(가) {target.name}을(를) 물어 흡혈했습니다!")
            return True
        
        return False

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        if self.bite_cooldown > 0:
            self.bite_cooldown -= dt
        
        FlyingAnimal.update(self, dt, game_map, weather, animals)
        if not self.alive or self.is_stunned:
            return
        
        # 💡 [핵심 수정] 독개구리 탐지 및 공격 로직 삭제하여 자살 행위 방지!
        prey_candidates = [
            a for a in animals
            if a is not self and a.alive
            and a.__class__.__name__ != "ToxicFrog" # 독개구리에게는 일절 다가가지 않음!
            and a.__class__.__name__ != "Mosquito"
            and self.distance_to(a) <= self.vision_range
            and self.can_see(a, game_map)
        ]
        
        if prey_candidates:
            closest_prey = min(prey_candidates, key=lambda p: self.distance_to(p))
            
            if self.distance_to(closest_prey) <= self.bite_range:
                if random.random() < 0.12:
                    self.bite(closest_prey)
            else:
                self.move(dt, closest_prey.coordinate, speed_multiplier=1.2)
        else:
            # 💡 [추가] 집 찾기 로직
            if self.try_return_home(dt):
                self.target_coord = None
                return
                
            if not getattr(self, 'wander_timer', 0) or getattr(self, 'wander_timer', 0) <= 0:
                self.wander_timer = random.uniform(3.0, 6.0)
                rx = self.coordinate[0] + random.uniform(-300.0, 300.0)
                ry = self.coordinate[1] + random.uniform(-300.0, 300.0)
                
                rx = max(50.0, min(float(game_map.pixel_width - 50.0), rx))
                ry = max(50.0, min(float(game_map.pixel_height - 50.0), ry))
                self.target_coord = [rx, ry]
            
            self.wander_timer = getattr(self, 'wander_timer', 0) - dt
            
            if getattr(self, 'target_coord', None):
                self.move(dt, self.target_coord, speed_multiplier=0.8)
                if self.distance_to(self.target_coord) < 20.0:
                    self.target_coord = None

    def __repr__(self):
        return (f"<Mosquito '{self.name}' hp={self.hp}/{self.max_hp} "
                f"flying={self.is_flying}>")