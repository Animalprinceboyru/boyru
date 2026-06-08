import pygame
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Set

class TileType(Enum):
    DEEP_WATER   = 0
    WATER        = 1
    MUD          = 2
    JUNGLE_FLOOR = 3
    UNDERGROWTH  = 4
    TREE_BASE    = 5

TILE_COLORS = {
    TileType.DEEP_WATER:   (25,  70,  85),
    TileType.WATER:        (40,  95, 115),
    TileType.MUD:          (95,  70,  45),
    TileType.JUNGLE_FLOOR: (40,  75,  30),
    TileType.UNDERGROWTH:  (25,  55,  20),
    TileType.TREE_BASE:    (15,  35,  12),
}

TILE_SIZE = 32

@dataclass
class Tree:
    tile_x:       int
    tile_y:       int
    tree_type:    str  = "normal"
    width_tiles:  int  = 2      # 2~4 타일 랜덤
    height_tiles: int  = 2
    has_nest:     bool = False
    nest_occupied:bool = False
    health:       int  = 100
    broken:       bool = False

    @property
    def pixel_pos(self) -> Tuple[int, int]:
        """나무 중심 픽셀 좌표"""
        cx = self.tile_x * TILE_SIZE + (self.width_tiles * TILE_SIZE) // 2
        cy = self.tile_y * TILE_SIZE + (self.height_tiles * TILE_SIZE) // 2
        return (cx, cy)

    @property
    def coordinate(self) -> Tuple[float, float]:
        """동물 상호작용용 중심 좌표"""
        return (float(self.tile_x * TILE_SIZE + self.width_tiles * TILE_SIZE // 2),
                float(self.tile_y * TILE_SIZE + self.height_tiles * TILE_SIZE // 2))

    def canopy_rect(self) -> pygame.Rect:
        """원숭이가 올라갈 수 있는 수관 영역 (크기에 비례)"""
        px, py    = self.pixel_pos
        cw        = TILE_SIZE * (self.width_tiles + 1)
        ch        = TILE_SIZE * self.height_tiles
        canopy_y  = py - TILE_SIZE * (self.height_tiles + 1)
        return pygame.Rect(px - cw // 2, canopy_y, cw, ch)

    def is_in_canopy(self, px: float, py: float) -> bool:
        return self.canopy_rect().collidepoint(px, py)

    def footprint_area(self) -> Set[Tuple[int, int]]:
        """나무 점유 타일 + 주변 1타일 여백 (겹침 방지)"""
        tiles = set()
        for dy in range(-1, self.height_tiles + 1):
            for dx in range(-1, self.width_tiles + 1):
                tiles.add((self.tile_x + dx, self.tile_y + dy))
        return tiles

class GameMap:
    """진짜 아마존 밀림 - 다양한 크기의 나무와 연결된 강"""

    def __init__(self, map_width: int = 180, map_height: int = 135):
        self.map_width   = map_width
        self.map_height  = map_height
        self.pixel_width  = map_width  * TILE_SIZE
        self.pixel_height = map_height * TILE_SIZE

        self.tiles = [[TileType.JUNGLE_FLOOR
                       for _ in range(map_width)]
                      for _ in range(map_height)]
        self.trees:    List[Tree] = []
        self.tree_map: dict       = {}

        self.surface      = None
        self.needs_redraw = True

        self._generate_map()

    # ══════════════════════════════════════════
    # 노이즈
    # ══════════════════════════════════════════
    def _noise(self, x: float, y: float, seed: int = 0) -> float:
        n = int(x * 374761393 + y * 668265263 + seed * 1013904223) & 0x7FFFFFFF
        n = (n ^ (n >> 13)) * 1274126177
        return ((n ^ (n >> 16)) & 0x7FFFFFFF) / 0x7FFFFFFF

    def _smooth_noise(self, x, y, seed=0, scale=0.1) -> float:
        sx, sy = x * scale, y * scale
        ix, iy = int(sx), int(sy)
        fx, fy = sx - ix, sy - iy
        v00 = self._noise(ix,   iy,   seed)
        v10 = self._noise(ix+1, iy,   seed)
        v01 = self._noise(ix,   iy+1, seed)
        v11 = self._noise(ix+1, iy+1, seed)
        ux = fx * fx * (3 - 2 * fx)
        uy = fy * fy * (3 - 2 * fy)
        return (v00*(1-ux)*(1-uy) + v10*ux*(1-uy) +
                v01*(1-ux)*uy    + v11*ux*uy)

    # ══════════════════════════════════════════
    # 맵 생성
    # ══════════════════════════════════════════
    def _generate_map(self):
        self._generate_base_terrain()
        self._generate_connected_rivers()
        self._generate_jungle_zones()
        self._generate_spaced_trees()
        self._add_nests()

    def _generate_base_terrain(self):
        for y in range(self.map_height):
            for x in range(self.map_width):
                n1 = self._smooth_noise(x, y, seed=42, scale=0.06)
                n2 = self._smooth_noise(x, y, seed=87, scale=0.12)
                v  = n1 * 0.7 + n2 * 0.3
                self.tiles[y][x] = (TileType.UNDERGROWTH
                                    if v > 0.35 else TileType.JUNGLE_FLOOR)

    def _generate_connected_rivers(self):
        main_path  = self._make_horizontal_path(
            self.map_height // 2, 0, self.map_width, 99, 3.2)
        north_path = self._make_vertical_path(
            self.map_width // 3, 0, main_path, 201, 2.0, going_up=False)
        south_path = self._make_vertical_path(
            self.map_width * 2 // 3, self.map_height - 1,
            main_path, 333, 2.0, going_up=True)

        self._carve_path(main_path,  11)
        self._carve_path(north_path,  5)
        self._carve_path(south_path,  6)

    def _make_horizontal_path(self, start_y, x_start, x_end,
                               seed, drift) -> List[Tuple[int,int]]:
        path = []
        cy   = float(start_y)
        for x in range(x_start, x_end):
            cy += (self._smooth_noise(x, 0, seed=seed, scale=0.035) - 0.5) * drift
            cy  = max(8, min(self.map_height - 8, cy))
            path.append((x, int(cy)))
        return path

    def _make_vertical_path(self, start_x, y_start, target_path,
                             seed, drift, going_up=False) -> List[Tuple[int,int]]:
        path      = []
        cx        = float(start_x)
        main_y_at = {mx: my for mx, my in target_path}
        y_range   = (range(y_start, self.map_height) if not going_up
                     else range(y_start, -1, -1))
        for y in y_range:
            cx += (self._smooth_noise(0, y, seed=seed, scale=0.04) - 0.5) * drift
            cx  = max(4, min(self.map_width - 4, cx))
            ix  = int(cx)
            my  = main_y_at.get(ix, self.map_height // 2)
            if not going_up and y >= my - 5: break
            if going_up     and y <= my + 5: break
            path.append((ix, y))
        return path

    def _carve_path(self, path: List[Tuple[int,int]], base_width: int):
        for x, y in path:
            wn = self._smooth_noise(x, y, seed=77, scale=0.07)
            w  = base_width + int((wn - 0.4) * 3)
            w  = max(base_width - 2, min(base_width + 3, w))
            if self.tiles[y][x] in (TileType.WATER, TileType.DEEP_WATER):
                w = int(w * 1.4)
            for dy in range(-w, w + 1):
                for dx in range(-w, w + 1):
                    tx, ty = x + dx, y + dy
                    if not (0 <= tx < self.map_width and 0 <= ty < self.map_height):
                        continue
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist <= w * 0.4:
                        self.tiles[ty][tx] = TileType.DEEP_WATER
                    elif dist <= w * 0.7:
                        if self.tiles[ty][tx] != TileType.DEEP_WATER:
                            self.tiles[ty][tx] = TileType.WATER
                    elif dist <= w * 0.9:
                        if self.tiles[ty][tx] not in (TileType.DEEP_WATER, TileType.WATER):
                            self.tiles[ty][tx] = TileType.MUD

    def _generate_jungle_zones(self):
        cy = self.map_height // 2
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.tiles[y][x] in (TileType.DEEP_WATER,
                                         TileType.WATER, TileType.MUD):
                    continue
                dist = abs(y - cy) / self.map_height
                if dist < 0.2 and self._noise(x, y, seed=123) > 0.25:
                    self.tiles[y][x] = TileType.UNDERGROWTH
                elif dist < 0.4 and self._noise(x, y, seed=124) > 0.5:
                    self.tiles[y][x] = TileType.UNDERGROWTH

    def _generate_spaced_trees(self):
        """2×2 ~ 4×4 타일 크기의 나무를 겹치지 않게 배치"""
        occupied: Set[Tuple[int,int]] = set()

        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.tiles[y][x] in (TileType.DEEP_WATER,
                                         TileType.WATER, TileType.MUD):
                    occupied.add((x, y))

        candidates = []
        for y in range(4, self.map_height - 4):
            for x in range(4, self.map_width - 4):
                if (x, y) not in occupied:
                    v = self._smooth_noise(x, y, seed=55, scale=0.08)
                    if v > 0.48:
                        candidates.append((x, y))
        random.shuffle(candidates)

        for tx, ty in candidates:
            tree_type = random.choices(
                ["normal", "tall", "wide"], weights=[45, 35, 20])[0]
            
            # 2×2 ~ 4×4 랜덤 크기
            width_tiles = random.randint(2, 4)
            height_tiles = random.randint(2, 4)

            tree = Tree(tile_x=tx, tile_y=ty,
                        tree_type=tree_type, 
                        width_tiles=width_tiles,
                        height_tiles=height_tiles)
            fp   = tree.footprint_area()

            # 맵 경계 체크
            if (tx + width_tiles >= self.map_width - 2 or
                    ty + height_tiles >= self.map_height - 2):
                continue

            if not fp.intersection(occupied):
                self.trees.append(tree)
                self.tree_map[(tx, ty)] = tree
                occupied.update(fp)
                for fx, fy in fp:
                    if (0 <= fx < self.map_width and 0 <= fy < self.map_height and
                            self.tiles[fy][fx] in (TileType.JUNGLE_FLOOR,
                                                    TileType.UNDERGROWTH)):
                        self.tiles[fy][fx] = TileType.TREE_BASE

    def _add_nests(self):
        probs = {"normal": 0.06, "tall": 0.12, "wide": 0.08}
        for tree in self.trees:
            if random.random() < probs.get(tree.tree_type, 0.06):
                tree.has_nest = True

    # ══════════════════════════════════════════
    # 렌더링
    # ══════════════════════════════════════════
    def render_to_surface(self):
        self.surface = pygame.Surface((self.pixel_width, self.pixel_height))

        # 1. 바닥 타일
        for y in range(self.map_height):
            for x in range(self.map_width):
                base  = TILE_COLORS[self.tiles[y][x]]
                var   = int((self._noise(x, y, seed=13) - 0.5) * 12)
                color = tuple(max(0, min(255, c + var)) for c in base)
                pygame.draw.rect(self.surface, color,
                                 (x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # 2. 밀림 바닥 디테일
        self._draw_jungle_details()

        # 3. 나무 (Y축 정렬로 깊이감)
        for tree in sorted(self.trees, key=lambda t: t.tile_y):
            self._draw_pixel_tree(tree)

        self.needs_redraw = False

    def _draw_jungle_details(self):
        """강 물결, 연잎, 고사리, 버섯 등 밀림 디테일"""
        for y in range(self.map_height):
            for x in range(self.map_width):
                tile = self.tiles[y][x]
                px   = x * TILE_SIZE
                py   = y * TILE_SIZE

                if tile in (TileType.DEEP_WATER, TileType.WATER):
                    wn = self._noise(x*2, y*2, seed=88)
                    if wn > 0.82:
                        color = ((50, 115, 135) if tile == TileType.WATER
                                 else (35, 85, 105))
                        pygame.draw.rect(
                            self.surface, color,
                            (px + int(wn*14), py + TILE_SIZE//2, TILE_SIZE//2, 2))
                    elif wn < 0.06 and tile == TileType.WATER:
                        # 연잎 (직사각형 블록 스타일)
                        pygame.draw.rect(self.surface, (45, 110, 45),
                                         (px+8, py+8, 16, 16))
                        pygame.draw.rect(self.surface, (25, 70, 25),
                                         (px+8, py+8, 16, 16), 2)

                elif tile == TileType.UNDERGROWTH:
                    fn = self._noise(x*3, y*3, seed=111)
                    if fn > 0.75:
                        # 고사리 (십자 블록)
                        pygame.draw.rect(self.surface, (30, 70, 30),
                                         (px+4, py+16, 12, 3))
                        pygame.draw.rect(self.surface, (30, 70, 30),
                                         (px+16, py+8, 3, 12))
                        pygame.draw.rect(self.surface, (40, 85, 40),
                                         (px+8, py+12, 8, 6))
                    elif fn < 0.1:
                        # 버섯 (작은 블록)
                        pygame.draw.rect(self.surface, (80, 60, 40),
                                         (px+14, py+20, 4, 6))
                        pygame.draw.rect(self.surface, (120, 80, 50),
                                         (px+11, py+16, 10, 6))

    def _draw_pixel_tree(self, tree: Tree):
        """크기(2~4타일)에 따라 다르게 렌더링되는 픽셀아트 나무"""
        px, py = tree.pixel_pos
        w_size = tree.width_tiles
        h_size = tree.height_tiles

        if tree.broken:
            pygame.draw.rect(self.surface, (55, 35, 18),
                             (px - TILE_SIZE, py, TILE_SIZE * w_size, TILE_SIZE // 2))
            return

        # 크기에 비례한 나무 치수 계산
        trunk_h  = int(TILE_SIZE * (1.5 + h_size * 0.3))
        trunk_w  = int(TILE_SIZE * (0.3 + w_size * 0.1))
        canopy_w = int(TILE_SIZE * (1.8 + w_size * 0.5))
        layers   = max(3, w_size + h_size - 1)

        # 나무 타입별 보정
        if tree.tree_type == "tall":
            trunk_h  = int(trunk_h  * 1.35)
            canopy_w = int(canopy_w * 0.85)
        elif tree.tree_type == "wide":
            trunk_h  = int(trunk_h  * 0.85)
            canopy_w = int(canopy_w * 1.30)

        canopy_base_y = py - trunk_h

        # 1. 타원형 그림자 (블록 스타일)
        shadow_w = int(canopy_w * 1.2)
        shadow_h = max(8, TILE_SIZE // 2)
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 0))
        pygame.draw.rect(shadow_surf, (0, 0, 0, 70),
                         (shadow_w//6, 0, shadow_w*2//3, shadow_h))
        pygame.draw.rect(shadow_surf, (0, 0, 0, 35),
                         (0, 0, shadow_w, shadow_h))
        self.surface.blit(shadow_surf, (px - shadow_w//2, py + TILE_SIZE//4))

        # 2. 기둥
        trunk_colors = {
            "normal": (50, 32, 18),
            "tall":   (42, 26, 14),
            "wide":   (58, 38, 22),
        }
        tc = trunk_colors.get(tree.tree_type, (50, 32, 18))
        tx = px - trunk_w // 2
        ty_trunk = py - trunk_h + TILE_SIZE

        pygame.draw.rect(self.surface, tc,
                         (tx, ty_trunk, trunk_w, trunk_h))
        # 기둥 하이라이트 (왼쪽)
        pygame.draw.rect(self.surface,
                         tuple(min(255, c + 10) for c in tc),
                         (tx + 2, ty_trunk + 4, max(2, trunk_w//5), trunk_h - 8))
        # 기둥 그림자 (오른쪽)
        pygame.draw.rect(self.surface,
                         tuple(max(0, c - 14) for c in tc),
                         (tx + trunk_w - max(3, trunk_w//5), ty_trunk,
                          max(3, trunk_w//5), trunk_h))

        # 3. 덩굴 (크기가 클수록 덩굴 많음)
        vine_count = max(1, (w_size + h_size) // 2 - 1)
        rng = tree.tile_x * 17 + tree.tile_y * 23
        for i in range(vine_count):
            vx = px + ((rng + i * 7) % canopy_w) - canopy_w // 2
            vl = TILE_SIZE + ((rng + i * 11) % TILE_SIZE)
            pygame.draw.rect(self.surface, (20, 50, 20),
                             (vx, canopy_base_y, 2, vl))
            for ly in range(canopy_base_y + 8, canopy_base_y + vl, 12):
                pygame.draw.rect(self.surface, (25, 60, 25),
                                 (vx - 2, ly, 6, 4))

        # 4. 수관 (레이어별 블록, 크기에 비례)
        canopy_palettes = {
            "normal": [(12,40,15),(18,55,20),(28,75,28),(40,95,35)],
            "tall":   [(10,35,12),(15,50,18),(25,70,25),(35,85,30),(48,105,38)],
            "wide":   [(15,45,18),(22,60,22),(32,80,30),(45,100,40),(55,120,45)],
        }
        palette = canopy_palettes.get(tree.tree_type, canopy_palettes["normal"])

        for i in range(layers):
            cw    = int(canopy_w * (1.0 - i * 0.10))
            ch    = int(cw * 0.65)
            cx    = px - cw // 2
            cy    = canopy_base_y - i * (8 + max(w_size, h_size))
            color = palette[min(i, len(palette) - 1)]
            pygame.draw.rect(self.surface, color, (cx, cy, cw, ch))

        # 수관 상단 이슬 하이라이트
        top_cw = int(canopy_w * (1.0 - (layers-1) * 0.10))
        top_cy = canopy_base_y - (layers-1) * (8 + max(w_size, h_size))
        hl     = tuple(min(255, c + 18) for c in palette[-1])
        pygame.draw.rect(self.surface, hl,
                         (px - top_cw//2 + 3, top_cy, top_cw - 6, 3))

        # 5. 둥지 (크기에 비례)
        if tree.has_nest:
            nest_w = TILE_SIZE + (max(w_size, h_size) - 2) * 6
            nest_h = TILE_SIZE // 2 + (max(w_size, h_size) - 2) * 3
            nx     = px + canopy_w // 4
            ny     = canopy_base_y + TILE_SIZE // 3
            pygame.draw.rect(self.surface, (85, 60, 25),
                             (nx, ny, nest_w, nest_h))
            pygame.draw.rect(self.surface, (115, 80, 35),
                             (nx+2, ny+2, nest_w-4, nest_h-4))
            if tree.nest_occupied:
                pygame.draw.rect(self.surface, (220, 210, 190),
                                 (nx + nest_w//4, ny+2, 8, 6))

    # ══════════════════════════════════════════
    # draw (카메라 적용)
    # ══════════════════════════════════════════
    def draw(self, screen: pygame.Surface,
             camera_x: float, camera_y: float,
             screen_w: int, screen_h: int, zoom: float = 1.0):
        if self.needs_redraw or self.surface is None:
            self.render_to_surface()

        if abs(zoom - 1.0) > 0.001:
            view_w = int(screen_w / zoom)
            view_h = int(screen_h / zoom)
            src_x  = int(max(0, min(camera_x,
                                    self.pixel_width  - view_w)))
            src_y  = int(max(0, min(camera_y,
                                    self.pixel_height - view_h)))
            aw = min(view_w, self.pixel_width  - src_x)
            ah = min(view_h, self.pixel_height - src_y)
            if aw > 0 and ah > 0:
                sub    = self.surface.subsurface(
                    pygame.Rect(src_x, src_y, aw, ah))
                scaled = pygame.transform.scale(sub, (screen_w, screen_h))
                screen.blit(scaled, (0, 0))
        else:
            src = pygame.Rect(int(camera_x), int(camera_y),
                              screen_w, screen_h)
            src.clamp_ip(pygame.Rect(0, 0,
                                     self.pixel_width, self.pixel_height))
            screen.blit(self.surface, (0, 0), src)

    # ══════════════════════════════════════════
    # 유틸리티
    # ══════════════════════════════════════════
    def get_tile(self, tx: int, ty: int) -> Optional[TileType]:
        if 0 <= tx < self.map_width and 0 <= ty < self.map_height:
            return self.tiles[ty][tx]
        return None

    def get_tree_at_pixel(self, px: float, py: float) -> Optional[Tree]:
        for tree in self.trees:
            if tree.canopy_rect().collidepoint(px, py):
                return tree
        return None

    def get_trees_in_canopy(self, px: float, py: float) -> List[Tree]:
        return [t for t in self.trees if t.is_in_canopy(px, py)]

    def break_tree(self, tree: Tree):
        tree.broken       = True
        tree.health       = 0
        self.needs_redraw = True
        print(f"나무 파괴: {tree.tree_type} "
              f"({tree.width_tiles}x{tree.height_tiles}) "
              f"@ ({tree.tile_x}, {tree.tile_y})")

    def is_walkable(self, tx: int, ty: int) -> bool:
        return self.get_tile(tx, ty) not in (TileType.DEEP_WATER,)

    def is_water(self, tx: int, ty: int) -> bool:
        return self.get_tile(tx, ty) in (TileType.WATER, TileType.DEEP_WATER)
    
    def is_in_water(self, px: float, py: float) -> bool:
        tx = int(px // TILE_SIZE)
        ty = int(py // TILE_SIZE)
        return self.is_water(tx, ty)

    def get_environment(self, px: float, py: float) -> str:
        tx = int(px // TILE_SIZE)
        ty = int(py // TILE_SIZE)
        tile = self.get_tile(tx, ty)
        if tile in (TileType.WATER, TileType.DEEP_WATER):
            return "water"
        return "land"
