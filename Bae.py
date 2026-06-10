import math
import random
import pygame
from typing import Tuple, Optional, List
import copy
from animal import Animal, Predator, Prey, Egg
from map_system import TileType, TILE_SIZE

Bae={}

# ════════════════════════════════════════════════
#  물 관련 모듈 레벨 유틸 (Crocodile 등에서 공용 사용)
# ════════════════════════════════════════════════

_WATER_TILES = (TileType.WATER, TileType.DEEP_WATER)

def _is_water(game_map, tx: int, ty: int) -> bool:
    return game_map.get_tile(tx, ty) in _WATER_TILES

def _find_shore_positions(game_map, cx: float, cy: float, search_radius_tiles: int = 20, max_candidates: int = 12):
    origin_tx = int(cx // TILE_SIZE)
    origin_ty = int(cy // TILE_SIZE)
    candidates = []
    for dy in range(-search_radius_tiles, search_radius_tiles + 1):
        for dx in range(-search_radius_tiles, search_radius_tiles + 1):
            tx, ty = origin_tx + dx, origin_ty + dy
            if not _is_water(game_map, tx, ty):
                continue
            if any(not _is_water(game_map, tx + ndx, ty + ndy) for ndx, ndy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px = (tx + 0.5) * TILE_SIZE
                py = (ty + 0.5) * TILE_SIZE
                dist = math.hypot(px - cx, py - cy)
                candidates.append((dist, px, py))
    candidates.sort()
    return [(px, py) for _, px, py in candidates[:max_candidates]]

# ════════════════════════════════════════════════
#  Anaconda
# ════════════════════════════════════════════════

class Anaconda(Predator):
    SPECIES_VISION_RANGE: float = 600.0
    SPECIES_VISION_ANGLE: float = 120.0
    minimap_color = (255, 255, 0)

    _STATE_IDLE    = "idle"
    _STATE_WAITING = "waiting"
    _STATE_RUSHING = "rushing"
    _STATE_CHASING = "chasing"

    HUNT_TARGETS     = {"Capybara", "Monkey", "Parrot", "ToxicFrog","Rhino"}
    HATCH_TIME       = 90.0
    WATER_PREY_RANGE = 160.0

    def __init__(self, name: str, coordinate: Tuple[float, float], choke_range: float = 35.0, ambush_wait_time: float = 2.0,
                 water_max_speed: float = 120.0, water_max_accelerate: float = 260.0,
                 land_max_speed: float = 55.0, land_max_accelerate: float = 110.0, land_stamina_drain: float = 6.0, **kwargs):
        super().__init__(name=name, coordinate=coordinate, attack_range=35.0, hunt_range=220.0, attack_success_rate=0.55,
                         hunger_limit=40.0, chase_speed_mul=1.3, max_speed=water_max_speed, max_accelerate=water_max_accelerate, **kwargs)
        self.max_hp=250
        self.choke_range: float = choke_range
        self.hidden: bool = False
        self.water_max_speed      = water_max_speed
        self.water_max_accelerate = water_max_accelerate
        self.land_max_speed       = land_max_speed
        self.land_max_accelerate  = land_max_accelerate
        self.land_stamina_drain   = land_stamina_drain

        self._state: str = self._STATE_IDLE
        self._ambush_timer: float = 0.0
        self._ambush_wait_time: float = ambush_wait_time
        self._ambush_rush_speed: float = 2.5
        self._target: Optional[Animal] = None

        self._wander_target: Optional[Tuple[float, float]] = None
        self._wander_timer: float = 0.0

        self.image_path = "anaconda.png"
        self.image = None
        if self.image_path not in Bae:
            try:
                Bae[self.image_path] = pygame.image.load(self.image_path).convert_alpha()
            except Exception as e:
                Bae[self.image_path] = None
        orig_img = Bae[self.image_path]
        if orig_img is not None:
            orig_w, orig_h = orig_img.get_size()
            target_max_size = int(self.size * 2.5)
            scale_factor = target_max_size / max(orig_w, orig_h)
            new_w = int(orig_w * scale_factor)
            new_h = int(orig_h * scale_factor)
            self.image = pygame.transform.scale(orig_img, (new_w, new_h))

    def hide(self): self.hidden = True
    def stop_hide(self): self.hidden = False

    def choke(self, target: Animal, dt: float, choke_dps: float = 15.0, stun_duration: float = 0.5):
        if not target.alive: return
        if self.distance_to(target) <= self.choke_range:
            target.take_damage(choke_dps * dt, source=f"{self.name}_choke", attacker=self)
            target.apply_stun(stun_duration)

    def _is_water_tile(self, wx: float, wy: float, game_map) -> bool:
        tx, ty = int(wx // TILE_SIZE), int(wy // TILE_SIZE)
        return game_map.is_water(tx, ty)

    def _prey_near_water(self, prey: Animal, game_map) -> bool:
        px, py = prey.coordinate
        step = TILE_SIZE
        steps = int(self.WATER_PREY_RANGE / step)
        for dx in range(-steps, steps + 1):
            for dy in range(-steps, steps + 1):
                if self._is_water_tile(px + dx * step, py + dy * step, game_map): return True
        return False

    def _nearest_water_point_to(self, target_coord: Tuple[float, float], game_map) -> Optional[Tuple[float, float]]:
        ox, oy = self.coordinate
        tx, ty = target_coord
        step = TILE_SIZE
        steps = int(self.hunt_range / step)
        best_point, best_dist = None, float('inf')
        for dx in range(-steps, steps + 1):
            for dy in range(-steps, steps + 1):
                wx, wy = ox + dx * step, oy + dy * step
                if not self._is_water_tile(wx, wy, game_map): continue
                d = math.hypot(wx - tx, wy - ty)
                if d < best_dist:
                    best_dist  = d
                    best_point = (wx + TILE_SIZE / 2, wy + TILE_SIZE / 2)
        return best_point

    def _wander(self, dt: float, game_map):
        if self.try_return_home(dt): return # 💡 귀소 본능 로직 우선 확인
        
        self._wander_timer -= dt
        if (self._wander_target is None or self._wander_timer <= 0 or self.distance_to(self._wander_target) < TILE_SIZE):
            rx, ry = self.coordinate[0] + random.uniform(-300, 300), self.coordinate[1] + random.uniform(-300, 300)
            rx = max(50.0, min(float(game_map.pixel_width - 50.0), rx))
            ry = max(50.0, min(float(game_map.pixel_height - 50.0), ry))
            water_target = self._nearest_water_point_to((rx, ry), game_map)
            self._wander_target = water_target if water_target else (rx, ry)
            self._wander_timer  = random.uniform(3.0, 6.0)
            
        if self._wander_target:
            speed_mul = 0.6 if self.environment_status == 'water' and self.stamina > 40 else 0.4
            self.move(dt, self._wander_target, speed_multiplier=speed_mul)
        else: self.move(dt)

    def _calc_ambush_success_rate(self, target: Animal) -> float:
        base = 0.55
        hunger_bonus = (self.hunger / 100.0) * 0.20
        prey_hp_bonus = (1.0 - target.hp / target.max_hp) * 0.10
        prey_stamina_bonus = (1.0 - target.stamina / target.max_stamina) * 0.10
        self_stamina_penalty = (1.0 - self.stamina / self.max_stamina) * 0.15
        return max(0.05, min(0.95, base + hunger_bonus + prey_hp_bonus + prey_stamina_bonus - self_stamina_penalty))

    def _apply_environment_stats(self, game_map):
        tx, ty = int(self.coordinate[0] // TILE_SIZE), int(self.coordinate[1] // TILE_SIZE)
        if game_map.is_water(tx, ty):
            self.environment_status = "water"
            self.max_speed, self.max_accelerate = self.water_max_speed, self.water_max_accelerate
        else:
            self.environment_status = "land"
            self.max_speed, self.max_accelerate = self.land_max_speed, self.land_max_accelerate

    def _apply_land_stamina_drain(self, dt: float):
        if self.environment_status != "water": self.stamina = max(0.0, self.stamina - self.land_stamina_drain * dt)

    def _set_state(self, state: str, target: Optional[Animal] = None):
        self._state, self._ambush_timer, self._target = state, 0.0, target

    def _update_behavior(self, dt: float, animals: List[Animal], game_map):
        state = self._state
        if state == self._STATE_IDLE:
            self.hide()
            if self.hunger < self.hunger_limit:
                self._wander(dt, game_map)
                return
            prey_list = [a for a in animals if self._is_prey(a) and a.alive and self.distance_to(a) <= self.hunt_range and self.can_see(a, game_map) and self._prey_near_water(a, game_map)]
            if not prey_list:
                self._wander(dt, game_map)
                return
            closest = min(prey_list, key=lambda a: self.distance_to(a))
            approach = self._nearest_water_point_to(closest.coordinate, game_map)
            if approach and self.distance_to(approach) > self.attack_range: self.move(dt, approach)
            else:
                self._set_state(self._STATE_WAITING, closest)
                self.stop()
        elif state == self._STATE_WAITING:
            self.stop()
            t = self._target
            if t is None or not t.alive or not self._prey_near_water(t, game_map):
                self._set_state(self._STATE_IDLE); return
            self._ambush_timer += dt
            if self._ambush_timer >= self._ambush_wait_time: self._set_state(self._STATE_RUSHING, t)
        elif state == self._STATE_RUSHING:
            t = self._target
            if t is None or not t.alive:
                self._set_state(self._STATE_IDLE); self.stop_hide(); return
            self.stop_hide()
            self.move(dt, t.coordinate, self._ambush_rush_speed)
            if self.distance_to(t) <= self.attack_range:
                if random.random() < self._calc_ambush_success_rate(t):
                    self.choke(t, dt)
                    self.attack(t, damage=30.0)
                    if not t.alive:
                        self.eat(45.0)
                        self._set_state(self._STATE_IDLE)
                else:
                    self._set_state(self._STATE_CHASING, t)
            if self.distance_to(t) > self.hunt_range * 1.5: self._set_state(self._STATE_IDLE)
        elif state == self._STATE_CHASING:
            t = self._target
            if t is None or not t.alive or not self.can_see(t, game_map):
                self._set_state(self._STATE_IDLE); return
            self.move(dt, t.coordinate, self.chase_speed_mul)
            self.use_stamina(8.0 * dt)
            self.choke(t, dt)
            if self.distance_to(t) <= self.attack_range:
                if random.random() < self.attack_success_rate:
                    self.attack(t, damage=25.0)
                    if not t.alive:
                        self.eat(40.0)
                        self._set_state(self._STATE_IDLE)
            if self.distance_to(t) > self.hunt_range * 1.5 or self.stamina <= 0: self._set_state(self._STATE_IDLE)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        Animal.update(self, dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: return # 💡 기절 시 FSM 정지 완벽 해결

        self._apply_environment_stats(game_map)
        self._apply_land_stamina_drain(dt)

        if self.environment_status == "water": self._update_behavior(dt, animals, game_map)
        else:
            if self.hidden: self.stop_hide()
            if self._state == self._STATE_CHASING: self._update_behavior(dt, animals, game_map)
            else:
                self._wander(dt, game_map)
                if self._state != self._STATE_IDLE: self._set_state(self._STATE_IDLE)

    def make_child(self) -> "Egg":
        return Egg(coordinate=self.home_coordinate or tuple(self.coordinate), parent=self, hatch_time=self.HATCH_TIME)

    def _spawn_child(self) -> "Anaconda":
        return Anaconda(name=f"Anaconda_{random.randint(1000, 9999)}", coordinate=tuple(self.coordinate))

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

# ════════════════════════════════════════════════
#  Crocodile
# ════════════════════════════════════════════════

class Crocodile(Predator):
    SPECIES_VISION_RANGE = 800.0
    SPECIES_VISION_ANGLE = 140.0
    HUNT_TARGETS = {"Capybara", "Monkey", "Parrot", "ToxicFrog"}
    HATCH_TIME   = 120.0
    minimap_color = (0, 128, 128)
    WATER_PREY_RANGE = 160.0

    _IDLE          = "idle"
    _SEEKING_SHORE = "seeking_shore"
    _LURKING       = "lurking"
    _RUSHING       = "rushing"
    _DEATH_ROLL    = "death_roll"
    _CHASING       = "chasing"

    def __init__(self, name, coordinate, water_max_speed=120.0, water_max_accel=260.0,
                 rush_max_speed=200.0, rush_max_accel=450.0, land_stamina_drain=12.0,
                 drink_range=160.0, lurk_timeout=30.0, death_roll_dps=35.0, death_roll_duration=2.5, **kwargs):
        super().__init__(name=name, coordinate=coordinate, attack_range=45.0, hunt_range=260.0,
            attack_success_rate=0.60, hunger_limit=45.0, chase_speed_mul=1.4, max_speed=water_max_speed, max_accelerate=water_max_accel,
            hp=200, max_hp=200, max_stamina=130.0, stamina=130.0, environment_status="water", **kwargs)
        self.water_max_speed, self.water_max_accel = water_max_speed, water_max_accel
        self.rush_max_speed, self.rush_max_accel = rush_max_speed, rush_max_accel
        self.land_stamina_drain = land_stamina_drain
        self.drink_range, self.lurk_timeout = drink_range, lurk_timeout
        self.death_roll_dps, self.death_roll_duration = death_roll_dps, death_roll_duration
        self.max_hp=350

        self.submerged   = False
        self._state      = self._IDLE
        self._target     = None
        self._shore_pos  = None
        self._lurk_timer = 0.0
        self._roll_timer = 0.0

        self._wander_target = None
        self._wander_timer  = 0.0

        self.image_path = "crocodile.png"
        self.image = None
        if self.image_path not in Bae:
            try: Bae[self.image_path] = pygame.image.load(self.image_path).convert_alpha()
            except Exception: Bae[self.image_path] = None
        orig_img = Bae[self.image_path]
        if orig_img is not None:
            orig_w, orig_h = orig_img.get_size()
            scale_factor = int(self.size * 2.5) / max(orig_w, orig_h)
            self.image = pygame.transform.scale(orig_img, (int(orig_w * scale_factor), int(orig_h * scale_factor)))

    def _prey_near_water(self, prey, game_map) -> bool:
        px, py = prey.coordinate
        ptx, pty = int(px // TILE_SIZE), int(py // TILE_SIZE)
        steps = int(self.WATER_PREY_RANGE / TILE_SIZE)
        for dx in range(-steps, steps + 1):
            for dy in range(-steps, steps + 1):
                if _is_water(game_map, ptx + dx, pty + dy): return True
        return False

    def _nearest_water_point_to(self, target_coord, game_map):
        ox, oy = self.coordinate
        tx, ty = target_coord
        otx, oty = int(ox // TILE_SIZE), int(oy // TILE_SIZE)
        steps = int(self.hunt_range / TILE_SIZE)
        best, best_d = None, float('inf')
        for dx in range(-steps, steps + 1):
            for dy in range(-steps, steps + 1):
                wtx, wty = otx + dx, oty + dy
                if not _is_water(game_map, wtx, wty): continue
                wx, wy = wtx * TILE_SIZE + TILE_SIZE / 2, wty * TILE_SIZE + TILE_SIZE / 2
                d = math.hypot(wx - tx, wy - ty)
                if d < best_d: best_d, best = d, (wx, wy)
        return best

    def _set_state(self, state, target=None):
        self._state, self._target, self._roll_timer, self._lurk_timer = state, target, 0.0, 0.0
        if state not in (self._LURKING, self._SEEKING_SHORE): self.submerged = False
        if state == self._RUSHING: self.max_speed, self.max_accelerate = self.rush_max_speed, self.rush_max_accel
        else: self.max_speed, self.max_accelerate = self.water_max_speed, self.water_max_accel

    def _pick_shore(self, game_map):
        shores = _find_shore_positions(game_map, self.coordinate[0], self.coordinate[1])
        return shores[0] if shores else None

    def _do_death_roll(self, target, dt):
        self._roll_timer += dt
        if target.alive:
            target.take_damage(self.death_roll_dps * dt, source=f"{self.name}_death_roll", attacker=self)
            target.apply_stun(0.3)
        return self._roll_timer >= self.death_roll_duration

    def _ambush_rate(self, target):
        b = 0.15 if self.submerged else 0.0
        b += (self.hunger / 100.0) * 0.10 + (1.0 - target.hp / target.max_hp) * 0.10 - (1.0 - self.stamina / self.max_stamina) * 0.15
        return max(0.05, min(0.95, 0.65 + b))

    def _apply_land_drain(self, dt):
        if self.environment_status != "water" and math.hypot(*self.velocity) > 5.0:
            self.stamina = max(0.0, self.stamina - self.land_stamina_drain * dt)

    def _wander(self, dt, game_map):
        if self.try_return_home(dt): return # 💡 귀소 본능 로직 추가
        
        self._wander_timer -= dt
        if (self._wander_target is None or self._wander_timer <= 0 or self.distance_to(self._wander_target) < TILE_SIZE):
            cx, cy = int(self.coordinate[0] // TILE_SIZE), int(self.coordinate[1] // TILE_SIZE)
            self._wander_target = None
            for _ in range(25):
                tx, ty = cx + random.randint(-10, 10), cy + random.randint(-10, 10)
                if (0 <= tx < game_map.map_width and 0 <= ty < game_map.map_height and game_map.is_water(tx, ty)):
                    self._wander_target = (tx * TILE_SIZE + TILE_SIZE / 2, ty * TILE_SIZE + TILE_SIZE / 2)
                    break
            if not self._wander_target:
                back = self._nearest_water_point_to(tuple(self.coordinate), game_map)
                self._wander_target = back if back else (self.coordinate[0], self.coordinate[1])
            self._wander_timer = random.uniform(3.0, 6.0)

        if self._wander_target:
            speed_mul = 0.6 if self.environment_status == 'water' and self.stamina > 50 else 0.4
            self.move(dt, self._wander_target, speed_multiplier=speed_mul)
        else: self.move(dt)

    def _update_behavior(self, dt, animals, game_map):
        s = self._state
        if s == self._IDLE:
            self.submerged = False
            self._wander(dt, game_map)
            if self.hunger >= self.hunger_limit:
                shore = self._pick_shore(game_map)
                if shore:
                    self._shore_pos = shore
                    self._set_state(self._SEEKING_SHORE)
        elif s == self._SEEKING_SHORE:
            if self._shore_pos is None: self._set_state(self._IDLE); return
            self.move(dt, self._shore_pos)
            if self.distance_to(self._shore_pos) < TILE_SIZE:
                self.stop(); self.submerged = True; self._set_state(self._LURKING)
            if self.hunger < self.hunger_limit * 0.5: self._set_state(self._IDLE)
        elif s == self._LURKING:
            self.stop(); self.submerged = True; self._lurk_timer += dt
            nearby = [a for a in animals if isinstance(a, Prey) and a.alive and self.distance_to(a) <= self.drink_range and self._prey_near_water(a, game_map)]
            if nearby:
                self._set_state(self._RUSHING, min(nearby, key=lambda a: self.distance_to(a))); return
            if self.hunger < self.hunger_limit * 0.5: self._set_state(self._IDLE)
            elif self._lurk_timer >= self.lurk_timeout:
                shore = self._pick_shore(game_map)
                if shore and shore != self._shore_pos: self._shore_pos = shore; self._set_state(self._SEEKING_SHORE)
                else: self._set_state(self._IDLE)
        elif s == self._RUSHING:
            t = self._target
            if t is None or not t.alive or not self._prey_near_water(t, game_map): self._set_state(self._IDLE); return
            approach = self._nearest_water_point_to(t.coordinate, game_map)
            self.move(dt, approach if approach else t.coordinate, 1.0)
            if self.distance_to(t) <= self.attack_range:
                if random.random() < self._ambush_rate(t): self._set_state(self._DEATH_ROLL, t)
                else: self._set_state(self._CHASING, t)
                return
            if self.distance_to(t) > self.hunt_range: self._set_state(self._IDLE)
        elif s == self._DEATH_ROLL:
            t = self._target
            if t is None: self._set_state(self._IDLE); return
            self.stop()
            done = self._do_death_roll(t, dt)
            if not t.alive: self.eat(55.0); self._set_state(self._IDLE)
            elif done: self._set_state(self._CHASING, t)
        elif s == self._CHASING:
            t = self._target
            if t is None or not t.alive or not self.can_see(t, game_map) or not self._prey_near_water(t, game_map):
                self._set_state(self._IDLE); return
            approach = self._nearest_water_point_to(t.coordinate, game_map)
            self.move(dt, approach if approach else t.coordinate, self.chase_speed_mul)
            self.use_stamina(12.0 * dt)
            if self.distance_to(t) <= self.attack_range:
                if random.random() < self.attack_success_rate:
                    self.attack(t, damage=40.0)
                    if not t.alive: self.eat(50.0); self._set_state(self._IDLE)
            if self.distance_to(t) > self.hunt_range or self.stamina <= 0: self._set_state(self._IDLE)

    def update(self, dt, game_map, weather, animals):
        Animal.update(self, dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: return # 💡 기절 시 FSM 정지 완벽 해결

        self._apply_land_drain(dt)
        tx, ty = int(self.coordinate[0] // TILE_SIZE), int(self.coordinate[1] // TILE_SIZE)
        if not game_map.is_water(tx, ty):
            self.environment_status = "land"
            if self._state != self._IDLE: self._set_state(self._IDLE)
            self._wander(dt, game_map)
            return

        if self._state == self._LURKING and self.environment_status != "water": self._set_state(self._IDLE)
        self._update_behavior(dt, animals, game_map)

    def make_child(self): return Egg(coordinate=self.home_coordinate or tuple(self.coordinate), parent=self, hatch_time=self.HATCH_TIME)
    def _spawn_child(self) -> "Crocodile": return Crocodile(name=f"Crocodile_{random.randint(1000, 9999)}", coordinate=tuple(self.coordinate))

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

# ════════════════════════════════════════════════
#  Tarantula
# ════════════════════════════════════════════════

class Tarantula(Predator):
    SPECIES_VISION_RANGE: float = 400.0
    SPECIES_VISION_ANGLE: float = 360.0
    HUNT_TARGETS = {"Capybara", "Monkey"}
    HATCH_TIME   = 60.0
    minimap_color = (140, 70, 20)

    _STATE_WANDER = "wander"
    _STATE_AMBUSH = "ambush"

    def __init__(self, name: str, coordinate: Tuple[float, float], web_range: float = 150.0,
                 web_slow_ratio: float = 0.45, bite_damage: float = 12.0, bite_interval: float = 1.0,
                 poison_duration: float = 8.0, poison_dps: float = 5.0, poison_speed_mul: float = 0.5,
                 ambush_relocate_time: float = 20.0, **kwargs):
        super().__init__(name=name, coordinate=coordinate, attack_range=30.0, hunt_range=web_range, attack_success_rate=1.0,
                         hunger_limit=40.0, chase_speed_mul=1.2, max_speed=60.0, max_accelerate=160.0, hp=80, max_hp=80, size=60.0, **kwargs)
        self.hidden: bool = False
        self.web_range: float = web_range
        self.web_slow_ratio: float = web_slow_ratio
        self.web_center: Optional[Tuple[float, float]] = None
        self.web_active: bool = False

        self.bite_damage, self.bite_interval = bite_damage, bite_interval
        self.poison_duration, self.poison_dps, self.poison_speed_mul = poison_duration, poison_dps, poison_speed_mul
        self.ambush_relocate_time: float = ambush_relocate_time

        self._state: str = self._STATE_WANDER
        self._ambush_timer: float = 0.0
        self._bite_cd: dict = {}
        self._bitten_nonprey: set = set()

        self._wander_target: Optional[Tuple[float, float]] = None
        self._wander_timer: float = 0.0

        self.image_path = "tarantula.png"
        self.image = None
        if self.image_path not in Bae:
            try: Bae[self.image_path] = pygame.image.load(self.image_path).convert_alpha()
            except Exception: Bae[self.image_path] = None
        orig_img = Bae[self.image_path]
        if orig_img is not None:
            orig_w, orig_h = orig_img.get_size()
            scale_factor = int(self.size * 2.5) / max(orig_w, orig_h)
            self.image = pygame.transform.scale(orig_img, (int(orig_w * scale_factor), int(orig_h * scale_factor)))

    def hide(self): self.hidden = True
    def stop_hide(self): self.hidden = False

    def make_web(self):
        self.web_center = (self.coordinate[0], self.coordinate[1])
        self.web_active = True
        self._bite_cd.clear(); self._bitten_nonprey.clear()

    def clear_web(self):
        self.web_center = None
        self.web_active = False
        self._bite_cd.clear(); self._bitten_nonprey.clear()

    def _slow(self, a: Animal):
        spd = math.hypot(a.velocity[0], a.velocity[1])
        limit = a.max_speed * self.web_slow_ratio
        if spd > limit and spd > 0:
            scale = limit / spd
            a.velocity[0] *= scale; a.velocity[1] *= scale

    def bite(self, target: Animal) -> bool:
        if not target.alive: return False
        target.take_damage(self.bite_damage, source=f"{self.name}_bite", attacker=self)
        target.apply_poison(duration=self.poison_duration, dps=self.poison_dps, speed_multiplier=self.poison_speed_mul)
        target.apply_stun(0.3)
        return True

    def _feed(self, food_value: float = 55.0):
        self.eat(food_value)
        self.thirst = max(0.0, self.thirst - 25.0)

    def _process_web(self, animals: List[Animal], dt: float) -> bool:
        if not self.web_active or self.web_center is None: return False
        cx, cy = self.web_center
        for k in list(self._bite_cd):
            self._bite_cd[k] -= dt
            if self._bite_cd[k] <= 0: del self._bite_cd[k]
        caught = False
        in_web_ids = set()

        for a in animals:
            if a is self or not a.alive: continue
            if type(a) is type(self) or type(a).__name__ == "Parrot": continue
            if math.hypot(a.coordinate[0] - cx, a.coordinate[1] - cy) > self.web_range: continue
            in_web_ids.add(id(a))

            if self._is_prey(a):
                self._slow(a); caught = True
                if id(a) not in self._bite_cd:
                    self.bite(a)
                    self._bite_cd[id(a)] = self.bite_interval
                    if not a.alive:
                        self._feed()
                        in_web_ids.discard(id(a))
            else:
                if id(a) not in self._bitten_nonprey:
                    self._slow(a); self.bite(a); self._bitten_nonprey.add(id(a)); caught = True

        self._bitten_nonprey &= in_web_ids
        return caught

    def _wander(self, dt: float, game_map):
        if self.try_return_home(dt): return # 💡 귀소 본능 로직 추가
        
        self._wander_timer -= dt
        if (self._wander_target is None or self._wander_timer <= 0 or self.distance_to(self._wander_target) < TILE_SIZE):
            cx, cy = int(self.coordinate[0] // TILE_SIZE), int(self.coordinate[1] // TILE_SIZE)
            target = None
            for _ in range(25):
                tx, ty = cx + random.randint(-8, 8), cy + random.randint(-8, 8)
                if (0 <= tx < game_map.map_width and 0 <= ty < game_map.map_height and not game_map.is_water(tx, ty)):
                    target = (tx * TILE_SIZE + TILE_SIZE / 2, ty * TILE_SIZE + TILE_SIZE / 2)
                    break
            if target is None: target = (self.coordinate[0], self.coordinate[1])
            self._wander_target = target
            self._wander_timer = random.uniform(3.0, 6.0)
        self.move(dt, self._wander_target, speed_multiplier=0.4)

    def _set_state(self, state: str):
        self._state, self._ambush_timer = state, 0.0

    def _update_behavior(self, dt: float, animals: List[Animal], game_map):
        if self.is_seeking_water and self._water_target is not None:
            self.stop_hide()
            if self.web_active: self.clear_web()
            self._state = self._STATE_WANDER
            self.move(dt, self._water_target, speed_multiplier=0.7)
            return

        state = self._state
        if state == self._STATE_WANDER:
            self.stop_hide()
            if (self._wander_target is not None and self.distance_to(self._wander_target) < TILE_SIZE * 1.5):
                self.stop(); self.make_web(); self._set_state(self._STATE_AMBUSH)
            else: self._wander(dt, game_map)
        elif state == self._STATE_AMBUSH:
            self.hide(); self.stop()
            caught = self._process_web(animals, dt)
            if caught: self._ambush_timer = 0.0
            else:
                self._ambush_timer += dt
                if self._ambush_timer >= self.ambush_relocate_time:
                    self.clear_web(); self._set_state(self._STATE_WANDER)

    def update(self, dt: float, game_map, weather, animals: List[Animal]):
        Animal.update(self, dt, game_map, weather, animals)
        if not self.alive or self.is_stunned: # 💡 기절 시 FSM 정지 완벽 해결
            self.clear_web()
            return
        self._update_behavior(dt, animals, game_map)

    def make_child(self) -> "Egg": return Egg(coordinate=self.home_coordinate or tuple(self.coordinate), parent=self, hatch_time=self.HATCH_TIME)
    def _spawn_child(self) -> "Tarantula": return Tarantula(name=f"Tarantula_{random.randint(1000, 9999)}", coordinate=tuple(self.coordinate))

    def draw(self, screen: pygame.Surface, camera):
        if not self.alive: return
        sx, sy = camera.world_to_screen(self.coordinate[0], self.coordinate[1])
        margin = 100
        if self.web_active and self.web_center is not None:
            wcx, wcy = camera.world_to_screen(self.web_center[0], self.web_center[1])
            web_r = max(1, int(self.web_range * camera.zoom))
            if -web_r < wcx < camera.screen_w + web_r and -web_r < wcy < camera.screen_h + web_r:
                if not hasattr(self.__class__, '_web_cache'): self.__class__._web_cache = {}
                zoom_key = round(camera.zoom, 1)
                cache_key = (zoom_key, web_r)
                if cache_key not in self.__class__._web_cache:
                    web_surf = pygame.Surface((web_r * 2 + 2, web_r * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(web_surf, (230, 230, 230, 40), (web_r + 1, web_r + 1), web_r)
                    pygame.draw.circle(web_surf, (230, 230, 230, 90), (web_r + 1, web_r + 1), web_r, 1)
                    self.__class__._web_cache[cache_key] = web_surf
                cached_web = self.__class__._web_cache[cache_key]
                screen.blit(cached_web, (int(wcx) - web_r - 1, int(wcy) - web_r - 1))
                
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