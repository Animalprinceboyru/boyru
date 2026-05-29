import pygame
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Set

class TileType(Enum):
    DEEP_WATER = 0
    WATER = 1
    MUD = 2             # 진흙 (기존 SAND)
    JUNGLE_FLOOR = 3    # 밀림 바닥 (기존 GRASS)
    UNDERGROWTH = 4     # 빽빽한 하층 식생 (기존 DENSE_GRASS)
    TREE_BASE = 5       # 나무 아래 짙은 그림자

# 🌿 진짜 아마존 밀림 색상 팔레트
TILE_COLORS = {
    TileType.DEEP_WATER:   (25, 70, 85),    # 탁한 아마존 강 깊은 곳
    TileType.WATER:        (40, 95, 115),   # 탁한 아마존 강 얕은 곳
    TileType.MUD:          (95, 70, 45),    # 강변의 어두운 진흙
    TileType.JUNGLE_FLOOR: (40, 75, 30),    # 습하고 어두운 밀림 바닥
    TileType.UNDERGROWTH:  (25, 55, 20),    # 빽빽한 하층 식생
    TileType.TREE_BASE:    (15, 35, 12),    # 나무 아래 깊은 그림자
}

TILE_SIZE = 32

@dataclass
class Tree:
    tile_x: int
    tile_y: int
    tree_type: str = "normal"   # normal / tall / wide
    width_tiles: int = 2
    height_tiles: int = 2
    has_nest: bool = False
    nest_occupied: bool = False
    health: int = 100
    broken: bool = False

    @property
    def pixel_pos(self) -> Tuple[int, int]:
        return (self.tile_x * TILE_SIZE + TILE_SIZE // 2,
                self.tile_y * TILE_SIZE + TILE_SIZE // 2)

    @property
    def coordinate(self) -> Tuple[float, float]:
        return (float(self.tile_x * TILE_SIZE + TILE_SIZE),
                float(self.tile_y * TILE_SIZE + TILE_SIZE))

    def canopy_rect(self) -> pygame.Rect:
        """원숭이가 올라갈 수 있는 수관 영역"""
        px, py = self.pixel_pos
        canopy_y = py - TILE_SIZE * 2
        return pygame.Rect(px - TILE_SIZE, canopy_y,
                           TILE_SIZE * 3, TILE_SIZE * 2)

    def is_in_canopy(self, px: float, py: float) -> bool:
        return self.canopy_rect().collidepoint(px, py)

    def footprint_area(self) -> Set[Tuple[int, int]]:
        """나무 + 주변 1타일 여백 (겹침 방지)"""
        tiles = set()
        for dy in range(-1, 3):
            for dx in range(-1, 3):
                tiles.add((self.tile_x + dx, self.tile_y + dy))
        return tiles


class GameMap:
    """진짜 아마존 밀림 - 어둡고 축축하고 빽빽한 열대우림"""

    def __init__(self, map_width: int = 180, map_height: int = 135):
        self.map_width = map_width
        self.map_height = map_height
        self.pixel_width = map_width * TILE_SIZE
        self.pixel_height = map_height * TILE_SIZE

        self.tiles = [[TileType.JUNGLE_FLOOR for _ in range(map_width)]
                      for _ in range(map_height)]
        self.trees: List[Tree] = []
        self.tree_map = {}

        self.surface = None
        self.needs_redraw = True

        self._generate_map()

    # ── 노이즈 함수 ──
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

    # ── 맵 생성 ──
    def _generate_map(self):
        self._generate_base_terrain()
        self._generate_connected_rivers()
        self._generate_jungle_zones()
        self._generate_spaced_trees()
        self._add_nests()

    def _generate_base_terrain(self):
        """어두운 밀림 바닥 기본 생성"""
        for y in range(self.map_height):
            for x in range(self.map_width):
                n1 = self._smooth_noise(x, y, seed=42, scale=0.06)
                n2 = self._smooth_noise(x, y, seed=87, scale=0.12)
                v  = n1 * 0.7 + n2 * 0.3
                
                # 대부분 어두운 하층 식생으로 덮음
                self.tiles[y][x] = (TileType.UNDERGROWTH if v > 0.35 
                                    else TileType.JUNGLE_FLOOR)

    def _generate_connected_rivers(self):
        """끊기지 않는 아마존 강 네트워크"""
        main_path = self._make_horizontal_path(
            start_y=self.map_height // 2,
            x_start=0, x_end=self.map_width,
            seed=99, drift=3.2
        )

        north_path = self._make_vertical_path(
            start_x=self.map_width // 3,
            y_start=0,
            target_path=main_path,
            seed=201, drift=2.0
        )

        south_path = self._make_vertical_path(
            start_x=self.map_width * 2 // 3,
            y_start=self.map_height - 1,
            target_path=main_path,
            seed=333, drift=2.0,
            going_up=True
        )

        self._carve_path(main_path,  base_width=11)
        self._carve_path(north_path, base_width=5)
        self._carve_path(south_path, base_width=6)

    def _make_horizontal_path(self, start_y, x_start, x_end,
                               seed, drift) -> List[Tuple[int,int]]:
        path = []
        cy = float(start_y)
        for x in range(x_start, x_end):
            cy += (self._smooth_noise(x, 0, seed=seed, scale=0.035) - 0.5) * drift
            cy  = max(8, min(self.map_height - 8, cy))
            path.append((x, int(cy)))
        return path

    def _make_vertical_path(self, start_x, y_start, target_path,
                             seed, drift, going_up=False) -> List[Tuple[int,int]]:
        path = []
        cx = float(start_x)
        main_y_at = {mx: my for mx, my in target_path}

        y_range = (range(y_start, self.map_height) if not going_up 
                   else range(y_start, -1, -1))

        for y in y_range:
            cx += (self._smooth_noise(0, y, seed=seed, scale=0.04) - 0.5) * drift
            cx  = max(4, min(self.map_width - 4, cx))
            ix  = int(cx)

            main_y = main_y_at.get(ix, self.map_height // 2)
            if not going_up and y >= main_y - 5: break
            if going_up and y <= main_y + 5: break

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
        """강 중심의 밀림 밀도 구역 생성"""
        center_y = self.map_height // 2
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.tiles[y][x] in (TileType.DEEP_WATER, TileType.WATER, TileType.MUD):
                    continue

                # 강과의 거리에 따른 밀도 조절
                dist_to_center = abs(y - center_y) / self.map_height

                if dist_to_center < 0.2:  # 강 근처 = 울창한 정글
                    if self._noise(x, y, seed=123) > 0.25:
                        self.tiles[y][x] = TileType.UNDERGROWTH
                elif dist_to_center < 0.4:  # 중간 정글 벨트
                    if self._noise(x, y, seed=124) > 0.5:
                        self.tiles[y][x] = TileType.UNDERGROWTH

    def _generate_spaced_trees(self):
        """겹치지 않는 선에서 최대한 빽빽한 나무 배치"""
        occupied: Set[Tuple[int,int]] = set()

        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.tiles[y][x] in (TileType.DEEP_WATER, TileType.WATER, TileType.MUD):
                    occupied.add((x, y))

        candidates = []
        for y in range(2, self.map_height - 2):
            for x in range(2, self.map_width - 2):
                if (x, y) not in occupied:
                    v = self._smooth_noise(x, y, seed=55, scale=0.08)
                    # 밀림답게 나무 밀도 대폭 증가 (0.62 → 0.48)
                    if v > 0.48:
                        candidates.append((x, y))
        random.shuffle(candidates)

        for tx, ty in candidates:
            tree_type = random.choices(
                ["normal", "tall", "wide"], weights=[45, 35, 20]
            )[0]
            tree = Tree(tile_x=tx, tile_y=ty, tree_type=tree_type)
            fp   = tree.footprint_area()

            if not fp.intersection(occupied):
                self.trees.append(tree)
                self.tree_map[(tx, ty)] = tree
                occupied.update(fp)

                for fx, fy in fp:
                    if (0 <= fx < self.map_width and 0 <= fy < self.map_height and
                            self.tiles[fy][fx] in (TileType.JUNGLE_FLOOR, TileType.UNDERGROWTH)):
                        self.tiles[fy][fx] = TileType.TREE_BASE

    def _add_nests(self):
        probs = {"normal": 0.06, "tall": 0.12, "wide": 0.08}
        for tree in self.trees:
            if random.random() < probs.get(tree.tree_type, 0.06):
                tree.has_nest = True

    # ── 렌더링 ──
    def render_to_surface(self):
        self.surface = pygame.Surface((self.pixel_width, self.pixel_height))

        # 1. 바닥 타일
        for y in range(self.map_height):
            for x in range(self.map_width):
                base = TILE_COLORS[self.tiles[y][x]]
                # 색상 변화를 줄여서 어두운 느낌 유지
                var  = int((self._noise(x, y, seed=13) - 0.5) * 12)
                color = tuple(max(0, min(255, c + var)) for c in base)
                pygame.draw.rect(self.surface, color,
                                 (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # 2. 밀림 바닥 디테일 (고사리, 연잎 등)
        self._draw_jungle_details()

        # 3. 나무 (Y축 정렬로 깊이감)
        for tree in sorted(self.trees, key=lambda t: t.tile_y):
            self._draw_pixel_tree(tree)

        self.needs_redraw = False

    def _draw_jungle_details(self):
        """밀림 특유의 식생 디테일 렌더링"""
        for y in range(self.map_height):
            for x in range(self.map_width):
                tile = self.tiles[y][x]
                px = x * TILE_SIZE
                py = y * TILE_SIZE
                
                # 🌊 강물 디테일 (물결 & 거대 연잎)
                if tile in (TileType.DEEP_WATER, TileType.WATER):
                    wn = self._noise(x * 2, y * 2, seed=88)
                    if wn > 0.82:  # 탁한 물 반사광
                        color = (50, 115, 135) if tile == TileType.WATER else (35, 85, 105)
                        pygame.draw.rect(self.surface, color,
                                         (px + int(wn * 14), py + TILE_SIZE // 2, 
                                          TILE_SIZE // 2, 2))
                    elif wn < 0.06 and tile == TileType.WATER:  # 거대 연잎 (빅토리아 아마조니카)
                        pygame.draw.circle(self.surface, (45, 110, 45), 
                                           (px + 16, py + 16), 12)
                        pygame.draw.circle(self.surface, (25, 70, 25), 
                                           (px + 16, py + 16), 12, 2)
                        # 연잎 가장자리 톱니
                        for i in range(0, 360, 45):
                            angle = math.radians(i)
                            edge_x = px + 16 + int(10 * math.cos(angle))
                            edge_y = py + 16 + int(10 * math.sin(angle))
                            pygame.draw.circle(self.surface, (30, 80, 30), 
                                               (edge_x, edge_y), 2)
                
                # 🌿 밀림 바닥 디테일 (고사리, 버섯, 잡초)
                elif tile == TileType.UNDERGROWTH:
                    fn = self._noise(x * 3, y * 3, seed=111)
                    if fn > 0.75:  # 고사리 잎사귀 패턴
                        pygame.draw.rect(self.surface, (30, 70, 30), 
                                         (px + 4, py + 16, 12, 3))
                        pygame.draw.rect(self.surface, (30, 70, 30), 
                                         (px + 16, py + 8, 3, 12))
                        pygame.draw.rect(self.surface, (40, 85, 40), 
                                         (px + 8, py + 12, 8, 6))
                    elif fn < 0.1:  # 작은 버섯
                        pygame.draw.rect(self.surface, (80, 60, 40), 
                                         (px + 14, py + 18, 4, 6))
                        pygame.draw.circle(self.surface, (120, 80, 50), 
                                           (px + 16, py + 18), 3)

    def _draw_pixel_tree(self, tree: Tree):
        """픽셀아트 스타일 밀림 나무 (덩굴과 어두운 색상)"""
        px, py = tree.pixel_pos

        if tree.broken:
            pygame.draw.rect(self.surface, (55, 35, 18),
                             (px - TILE_SIZE, py, TILE_SIZE * 2, TILE_SIZE // 2))
            return

        specs = {
            "normal": {"trunk_h": int(TILE_SIZE * 1.9), "layers": 3, 
                       "canopy_w": int(TILE_SIZE * 2.5)},
            "tall":   {"trunk_h": int(TILE_SIZE * 2.7), "layers": 4, 
                       "canopy_w": int(TILE_SIZE * 2.1)},
            "wide":   {"trunk_h": int(TILE_SIZE * 1.7), "layers": 3, 
                       "canopy_w": int(TILE_SIZE * 3.2)},
        }
        s = specs.get(tree.tree_type, specs["normal"])

        # 1. 그림자 (나무 아래 어두운 타원형)
        shadow_surf = pygame.Surface((int(s["canopy_w"] * 1.3), TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 85), shadow_surf.get_rect())
        self.surface.blit(shadow_surf, (px - int(s["canopy_w"] * 0.65), py + TILE_SIZE // 3))

        # 2. 기둥 (어두운 열대목 색상)
        trunk_colors = {
            "normal": (50, 32, 18),
            "tall":   (45, 28, 15),
            "wide":   (55, 35, 20),
        }
        trunk_color = trunk_colors.get(tree.tree_type, (50, 32, 18))

        trunk_x = px - TILE_SIZE // 4
        trunk_y = py - s["trunk_h"] + TILE_SIZE
        trunk_w = TILE_SIZE // 2
        pygame.draw.rect(self.surface, trunk_color,
                         (trunk_x, trunk_y, trunk_w, s["trunk_h"]))

        # 기둥 왼쪽 하이라이트 (미약하게)
        pygame.draw.rect(self.surface, tuple(min(255, c + 8) for c in trunk_color),
                         (trunk_x + 2, trunk_y + 4, 3, s["trunk_h"] - 8))

        # 기둥 오른쪽 그림자
        pygame.draw.rect(self.surface, tuple(max(0, c - 12) for c in trunk_color),
                         (trunk_x + trunk_w - 5, trunk_y, 5, s["trunk_h"]))

        # 3. 덩굴 (나무에서 아래로 늘어짐)
        canopy_base_y = py - s["trunk_h"]
        vine_seed = tree.tile_x * 17 + tree.tile_y * 23  # 일관된 랜덤
        vine_count = (vine_seed % 3) + 1
        
        for i in range(vine_count):
            vine_x = px + ((vine_seed + i * 7) % s["canopy_w"]) - s["canopy_w"] // 2
            vine_length = TILE_SIZE + ((vine_seed + i * 11) % TILE_SIZE)
            # 덩굴 그리기
            pygame.draw.rect(self.surface, (20, 50, 20), 
                             (vine_x, canopy_base_y, 2, vine_length))
            # 덩굴 잎사귀
            for leaf_y in range(canopy_base_y + 8, canopy_base_y + vine_length, 12):
                pygame.draw.circle(self.surface, (25, 60, 25), 
                                   (vine_x + 1, leaf_y), 3)

        # 4. 수관 (어둡고 울창한 열대우림 색상)
        canopy_palettes = {
            "normal": [(12, 40, 15), (18, 55, 20), (28, 75, 28), (40, 95, 35)],
            "tall":   [(10, 35, 12), (15, 50, 18), (25, 70, 25), (35, 85, 30), (48, 105, 38)],
            "wide":   [(15, 45, 18), (22, 60, 22), (32, 80, 30), (45, 100, 40)],
        }
        palette = canopy_palettes.get(tree.tree_type, canopy_palettes["normal"])

        for i in range(s["layers"]):
            cw = int(s["canopy_w"] * (1.0 - i * 0.12))
            ch = int(cw * 0.7)
            cx = px - cw // 2
            cy = canopy_base_y - i * 11
            color = palette[min(i, len(palette) - 1)]
            pygame.draw.rect(self.surface, color, (cx, cy, cw, ch))

        # 수관 위 이슬 하이라이트
        top_layer_w = int(s["canopy_w"] * (1.0 - (s["layers"]-1) * 0.12))
        highlight_color = tuple(min(255, c + 15) for c in palette[-1])
        pygame.draw.rect(self.surface, highlight_color,
                         (px - top_layer_w // 2 + 3, 
                          canopy_base_y - (s["layers"]-1) * 11,
                          top_layer_w - 6, 3))

        # 5. 둥지
        if tree.has_nest:
            nest_x = px + s["canopy_w"] // 4
            nest_y = canopy_base_y + TILE_SIZE // 3
            pygame.draw.rect(self.surface, (85, 60, 25),
                             (nest_x, nest_y, TILE_SIZE, TILE_SIZE // 2))
            pygame.draw.rect(self.surface, (115, 80, 35),
                             (nest_x + 2, nest_y + 2, TILE_SIZE - 4, TILE_SIZE // 2 - 4))
            if tree.nest_occupied:
                pygame.draw.rect(self.surface, (220, 210, 190),
                                 (nest_x + TILE_SIZE // 4, nest_y + 2, 8, 6))

    def draw(self, screen: pygame.Surface, camera_x: float, camera_y: float,
             screen_w: int, screen_h: int, zoom: float = 1.0):
        if self.needs_redraw or self.surface is None:
            self.render_to_surface()

        if abs(zoom - 1.0) > 0.01:
            view_w = int(screen_w / zoom)
            view_h = int(screen_h / zoom)
            src_x  = int(max(0, min(camera_x, self.pixel_width  - view_w)))
            src_y  = int(max(0, min(camera_y, self.pixel_height - view_h)))
            aw = min(view_w, self.pixel_width  - src_x)
            ah = min(view_h, self.pixel_height - src_y)
            if aw > 0 and ah > 0:
                sub    = self.surface.subsurface(pygame.Rect(src_x, src_y, aw, ah))
                scaled = pygame.transform.scale(sub, (screen_w, screen_h))
                screen.blit(scaled, (0, 0))
        else:
            src = pygame.Rect(int(camera_x), int(camera_y), screen_w, screen_h)
            src.clamp_ip(pygame.Rect(0, 0, self.pixel_width, self.pixel_height))
            screen.blit(self.surface, (0, 0), src)

    # ── 유틸리티 ──
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
        tree.broken = True
        tree.health = 0
        self.needs_redraw = True
        print(f"🌲💥 나무 파괴! {tree.tree_type} @ ({tree.tile_x}, {tree.tile_y})")

    def is_walkable(self, tx: int, ty: int) -> bool:
        return self.get_tile(tx, ty) not in (TileType.DEEP_WATER,)

    def is_water(self, tx: int, ty: int) -> bool:
        return self.get_tile(tx, ty) in (TileType.WATER, TileType.DEEP_WATER)
