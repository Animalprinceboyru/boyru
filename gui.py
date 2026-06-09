import pygame
import time
from typing import Optional, List, Any

COLOR_BG        = (20, 25, 20, 200)
COLOR_TEXT      = (240, 240, 240)
COLOR_HIGHLIGHT = (255, 220, 50)
COLOR_SUCCESS   = (100, 220, 120)
COLOR_HP        = (220, 60,  60)
COLOR_STAMINA   = (60,  180, 220)
COLOR_BORDER    = (100, 180, 100)

class HUD:
    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w = screen_w
        self.screen_h = screen_h

        pygame.font.init()
        try:
            self.font_title  = pygame.font.SysFont("malgungothic", 20, bold=True)
            self.font_normal = pygame.font.SysFont("malgungothic", 15)
            self.font_small  = pygame.font.SysFont("malgungothic", 12)
            self.log_font    = pygame.font.SysFont("malgungothic", 15, bold=True)
        except Exception:
            self.font_title  = pygame.font.SysFont(None, 24, bold=True)
            self.font_normal = pygame.font.SysFont(None, 18)
            self.font_small  = pygame.font.SysFont(None, 14)
            self.log_font    = pygame.font.SysFont(None, 18, bold=True)

        self.top_panel  = pygame.Surface((screen_w, 55), pygame.SRCALPHA)
        self.info_panel = pygame.Surface((340, 310), pygame.SRCALPHA)
        self.minimap    = pygame.Surface((200, 150), pygame.SRCALPHA)

        self.selected_animal: Optional[Any] = None
        self.selected_tree:   Optional[Any] = None
        
        self.logs = [] 

    # ══════════════════════════════════════════
    # 시스템 메시지 수신부
    # ══════════════════════════════════════════
    def add_log(self, text: str):
        clean_text = text.strip()
        if clean_text:
            self.logs.append((clean_text, time.time()))
            if len(self.logs) > 8:
                self.logs.pop(0)

    # ══════════════════════════════════════════
    # 메인 렌더링
    # ══════════════════════════════════════════
    def draw(self, screen, weather_system, camera, game_map, animals):
        self._draw_top_bar(screen, weather_system, camera)
        self._draw_minimap(screen, camera, game_map, animals)
        self._draw_controls(screen, weather_system)
        
        self._draw_logs(screen)
        
        # 💡 좌측 상단 개체수 현황판 렌더링 추가
        self._draw_population(screen, animals)

        if self.selected_animal is not None:
            self._draw_animal_panel(screen)
        elif self.selected_tree is not None:
            self._draw_tree_panel(screen)

    # ══════════════════════════════════════════
    # 생태계 개체수 현황판 (좌측 상단)
    # ══════════════════════════════════════════
    def _draw_population(self, screen, animals):
        counts = {}
        for a in animals:
            if getattr(a, 'alive', False):
                cname = type(a).__name__
                counts[cname] = counts.get(cname, 0) + 1
        
        # 한글 이름 매핑
        kor_names = {
            "Capybara": "카피바라", "Monkey": "원숭이", "Parrot": "앵무새", 
            "ToxicFrog": "독개구리", "Mosquito": "모기", "Anaconda": "아나콘다", 
            "Crocodile": "악어", "Tarantula": "타란튤라", "Rhino": "코뿔소", 
            "ElectricEel": "전기뱀장어"
        }
        
        pad_x, pad_y = 12, 12
        line_h = 22
        width = 170
        height = pad_y * 2 + 25 + len(counts) * line_h
        
        start_x = 16
        start_y = 65
        
        bg = pygame.Surface((width, height), pygame.SRCALPHA)
        bg.fill(COLOR_BG)
        pygame.draw.rect(bg, COLOR_BORDER, (0, 0, width, height), 2)
        screen.blit(bg, (start_x, start_y))
        
        ts = self.font_title.render("[생태계 개체수]", True, COLOR_HIGHLIGHT)
        screen.blit(ts, (start_x + pad_x, start_y + pad_y))
        
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        for i, (eng_name, cnt) in enumerate(sorted_counts):
            kor_name = kor_names.get(eng_name, eng_name)
            
            # 포식자와 피식자의 색상을 구분
            if eng_name in ["Anaconda", "Crocodile", "Tarantula", "ElectricEel", "ToxicFrog"]:
                text_color = (255, 160, 160) # 붉은 계열
            else:
                text_color = (160, 255, 160) # 푸른 계열
                
            s = self.font_normal.render(f"{kor_name} : {cnt}마리", True, text_color)
            screen.blit(s, (start_x + pad_x, start_y + pad_y + 28 + i * line_h))

    # ══════════════════════════════════════════
    # 화면 로그 렌더링
    # ══════════════════════════════════════════
    def _draw_logs(self, screen):
        current_time = time.time()
        self.logs = [(txt, t) for txt, t in self.logs if current_time - t < 7.0]

        if not self.logs:
            return

        start_x = 290
        base_y = self.screen_h - 40
        
        for i, (txt, t) in enumerate(reversed(self.logs)):
            y_pos = base_y - (i * 30)
            
            alpha = 255
            age = current_time - t
            if age > 5.0:
                alpha = max(0, int(255 * (1.0 - (age - 5.0) / 2.0)))

            surf = self.log_font.render(txt, True, (255, 255, 255))
            if alpha < 255:
                surf.set_alpha(alpha)

            bg = pygame.Surface((surf.get_width() + 16, surf.get_height() + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, min(180, alpha)))
            screen.blit(bg, (start_x, y_pos))
            screen.blit(surf, (start_x + 8, y_pos + 4))

    # ══════════════════════════════════════════
    # 상단 바
    # ══════════════════════════════════════════
    def _draw_top_bar(self, screen, weather_system, camera):
        self.top_panel.fill((15, 15, 15, 185))
        screen.blit(self.top_panel, (0, 0))

        ws = self.font_title.render(
            f"날씨: {weather_system.current.value}", True, COLOR_TEXT)
        screen.blit(ws, (16, 10))

        time_str = (f"시간: {weather_system.time_string}  "
                    f"배속: {weather_system.speed_string}")
        ts = self.font_title.render(time_str, True, COLOR_HIGHLIGHT)
        screen.blit(ts, (self.screen_w // 2 - ts.get_width() // 2, 10))

        info = (f"줌 {camera.zoom:.2f}x  |  "
                f"이동속도 {weather_system.get_speed_modifier():.2f}x  |  "
                f"시야 {weather_system.get_visibility_modifier():.2f}x")
        es = self.font_small.render(info, True, (180, 210, 180))
        screen.blit(es, (self.screen_w - es.get_width() - 16, 14))

        hint = "[ : 느리게    ] : 빠르게"
        hs = self.font_small.render(hint, True, (150, 180, 150))
        screen.blit(hs, (self.screen_w // 2 - hs.get_width() // 2, 34))

    # ══════════════════════════════════════════
    # 미니맵
    # ══════════════════════════════════════════
    def _draw_minimap(self, screen, camera, game_map, animals):
        mm_x = self.screen_w - 210
        mm_y = self.screen_h - 160
        self.minimap.fill((8, 25, 8, 220))

        try:
            from map_system import TILE_COLORS, TILE_SIZE
            sx   = 200 / game_map.pixel_width
            sy   = 150 / game_map.pixel_height
            step = 4
            for ty in range(0, game_map.map_height, step):
                for tx in range(0, game_map.map_width, step):
                    color = TILE_COLORS[game_map.tiles[ty][tx]]
                    mx_   = int(tx * TILE_SIZE * sx)
                    my_   = int(ty * TILE_SIZE * sy)
                    mw    = max(1, int(step * TILE_SIZE * sx))
                    mh    = max(1, int(step * TILE_SIZE * sy))
                    pygame.draw.rect(self.minimap, color, (mx_, my_, mw, mh))

            for animal in animals:
                if getattr(animal,'alive',False) and hasattr(animal, 'coordinate'):
                    ax = int(animal.coordinate[0] * sx)
                    ay = int(animal.coordinate[1] * sy)
                    c  = getattr(animal, 'minimap_color', COLOR_HIGHLIGHT)
                    pygame.draw.circle(self.minimap, c, (ax, ay), 3)

            vx = int(camera.x * sx)
            vy = int(camera.y * sy)
            vw = int(camera.screen_w / camera.zoom * sx)
            vh = int(camera.screen_h / camera.zoom * sy)
            pygame.draw.rect(self.minimap, (255, 255, 255), (vx, vy, vw, vh), 2)

        except ImportError:
            pygame.draw.rect(self.minimap, (50, 100, 50), (0, 0, 200, 150))

        pygame.draw.rect(self.minimap, COLOR_BORDER, (0, 0, 200, 150), 2)
        screen.blit(self.minimap, (mm_x, mm_y))
        label = self.font_small.render("미니맵", True, COLOR_SUCCESS)
        screen.blit(label, (mm_x + 6, mm_y - 18))

    # ══════════════════════════════════════════
    # 동물 패널 (우측 상단으로 위치 조정)
    # ══════════════════════════════════════════
    def _draw_animal_panel(self, screen):
        animal = self.selected_animal
        self.info_panel.fill(COLOR_BG)

        name = type(animal).__name__
        ts   = self.font_title.render(f"[동물] {name.upper()}", True, COLOR_HIGHLIGHT)
        self.info_panel.blit(ts, (12, 12))

        hp  = getattr(animal, 'hp',          100)
        mhp = getattr(animal, 'max_hp',      100)
        st  = getattr(animal, 'stamina',     100)
        mst = getattr(animal, 'max_stamina', 100)
        self._bar(self.info_panel, 12, 40, 316, 16, hp, mhp, COLOR_HP,      "체력")
        self._bar(self.info_panel, 12, 62, 316, 16, st, mst, COLOR_STAMINA, "스태미나")

        status = []
        if getattr(animal, 'is_stunned',  False): status.append("스턴")
        if getattr(animal, 'is_poisoned', False): status.append("독")
        if getattr(animal, 'is_fleeing',  False): status.append("도주중")
        if getattr(animal, 'is_hiding',   False): status.append("은신중")
        if getattr(animal, 'is_hunting',  False): status.append("사냥중")
        status_str = " / ".join(status) if status else "정상"
        sc = (220, 80, 80) if status else COLOR_SUCCESS
        ss = self.font_small.render(f"상태: {status_str}", True, sc)
        self.info_panel.blit(ss, (12, 85))

        hunger = getattr(animal, 'hunger', '?')
        thirst = getattr(animal, 'thirst', '?')
        rows = [
            ("이동속도", f"{getattr(animal, 'max_speed', '?')}"),
            ("나이",     f"{getattr(animal, 'age', '?')}"),
            ("성별",     getattr(animal, 'sex', '?')),
            ("배고픔",   f"{hunger:.0f} / 100" if isinstance(hunger, float) else str(hunger)),
            ("갈증",     f"{thirst:.0f} / 100" if isinstance(thirst, float) else str(thirst)),
            ("커플",     "있음" if getattr(animal, 'couple', None) else "없음"),
            ("집",       (f"({animal.home_coordinate[0]:.0f}, {animal.home_coordinate[1]:.0f})"
                          if getattr(animal, 'home_coordinate', None) else "없음")),
            ("위치",     (f"({animal.coordinate[0]:.0f}, {animal.coordinate[1]:.0f})"
                          if hasattr(animal, 'coordinate') else '?')),
        ]
        for i, (label, val) in enumerate(rows):
            s = self.font_normal.render(f"{label}: {val}", True, COLOR_TEXT)
            self.info_panel.blit(s, (12, 102 + i * 22))

        pygame.draw.rect(self.info_panel, COLOR_BORDER, (0, 0, 340, 310), 2)
        
        # 💡 좌측 상단 개체수 패널과 겹치지 않게 우측 상단으로 이동
        panel_x = self.screen_w - 340 - 16
        panel_y = 65
        screen.blit(self.info_panel, (panel_x, panel_y))

    # ══════════════════════════════════════════
    # 나무 패널 (우측 상단으로 위치 조정)
    # ══════════════════════════════════════════
    def _draw_tree_panel(self, screen):
        tree = self.selected_tree
        self.info_panel.fill(COLOR_BG)

        ts = self.font_title.render("[나무 정보]", True, COLOR_SUCCESS)
        self.info_panel.blit(ts, (12, 12))

        self._bar(self.info_panel, 12, 45, 316, 18,
                  tree.health, 100, COLOR_HP, "나무 체력")

        names = {"normal": "일반 나무", "tall": "키 큰 나무", "wide": "넓은 나무"}
        rows  = [
            ("종류",     names.get(tree.tree_type, "나무")),
            ("타일위치", f"({tree.tile_x}, {tree.tile_y})"),
            ("크기",     f"{tree.width_tiles} x {tree.height_tiles} 타일"),
            ("상태",     "부러짐" if tree.broken else "건강함"),
            ("둥지",     "있음"   if tree.has_nest else "없음"),
        ]
        if tree.has_nest:
            rows.append(("둥지상태",
                          "점유됨" if tree.nest_occupied else "비어있음"))

        for i, (label, val) in enumerate(rows):
            color = (COLOR_SUCCESS if "둥지" in label and tree.has_nest
                     else COLOR_TEXT)
            s = self.font_normal.render(f"{label}: {val}", True, color)
            self.info_panel.blit(s, (12, 80 + i * 26))

        guide = self.font_small.render(
            "원숭이가 수관 영역에 올라갈 수 있습니다",
            True, (150, 200, 150))
        self.info_panel.blit(guide, (12, 80 + len(rows) * 26 + 10))

        pygame.draw.rect(self.info_panel, COLOR_BORDER, (0, 0, 340, 310), 2)
        
        # 💡 좌측 상단 개체수 패널과 겹치지 않게 우측 상단으로 이동
        panel_x = self.screen_w - 340 - 16
        panel_y = 65
        screen.blit(self.info_panel, (panel_x, panel_y))

    # ══════════════════════════════════════════
    # 조작법 안내
    # ══════════════════════════════════════════
    def _draw_controls(self, screen, weather_system):
        lines = [
            ("[조작법]",              True),
            ("WASD / 방향키 : 이동",  False),
            ("Shift+WASD   : 빠른이동",False),
            ("마우스 휠     : 줌",     False),
            ("클릭          : 선택",   False),
            ("ESC           : 해제",   False),
            ("[ / ]         : 배속 조절", False),
            ("",                       False),
            ("[개발자]",              True),
            ("F1 : 맵 재생성",         False),
            ("F2 : 날씨 변경",         False),
            ("F3 : 선택 나무 파괴",    False),
            ("F4 : 시야각 표시",       False),
        ]
        lh = 20
        pw = 250
        ph = len(lines) * lh + 16
        px = 16
        py = self.screen_h - ph - 16

        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg.fill((15, 15, 15, 180))
        screen.blit(bg, (px, py))

        for i, (text, is_title) in enumerate(lines):
            if not text:
                continue
            color = COLOR_HIGHLIGHT if is_title else (180, 200, 180)
            font  = self.font_normal if is_title else self.font_small
            s = font.render(text, True, color)
            screen.blit(s, (px + 12, py + 8 + i * lh))

    # ══════════════════════════════════════════
    # 스탯 바
    # ══════════════════════════════════════════
    def _bar(self, surface, x, y, w, h, current, maximum, color, label):
        pygame.draw.rect(surface, (50, 50, 50), (x, y, w, h))
        if maximum > 0:
            fw = int(w * max(0.0, min(1.0, current / maximum)))
            if fw > 0:
                pygame.draw.rect(surface, color, (x, y, fw, h))
        pygame.draw.rect(surface, (150, 150, 150), (x, y, w, h), 1)
        ts = self.font_small.render(
            f"{label}: {int(current)} / {int(maximum)}", True, COLOR_TEXT)
        surface.blit(ts, (x + 6, y + 2))

    # ══════════════════════════════════════════
    # 클릭 처리
    # ══════════════════════════════════════════
    def handle_click(self, world_x: float, world_y: float,
                     animals: List[Any], game_map):
        best, best_dist = None, float('inf')
        for animal in animals:
            if not hasattr(animal, 'coordinate'):
                continue
            ax, ay = animal.coordinate
            d = ((ax - world_x)**2 + (ay - world_y)**2) ** 0.5
            if d < 35 and d < best_dist:
                best_dist, best = d, animal

        if best is not None:
            self.selected_animal = best
            self.selected_tree   = None
            print(f"동물 선택: {type(best).__name__} "
                  f"@ ({best.coordinate[0]:.0f}, {best.coordinate[1]:.0f})")
            return

        try:
            tree = game_map.get_tree_at_pixel(world_x, world_y)
            if tree is not None:
                self.selected_animal = None
                self.selected_tree   = tree
                print(f"나무 선택: {tree.tree_type} "
                      f"{tree.width_tiles}x{tree.height_tiles} "
                      f"@ ({tree.tile_x}, {tree.tile_y})"
                      f"{'  [둥지]' if tree.has_nest else ''}")
                return
        except Exception as e:
            print(f"나무 선택 오류: {e}")

        self.selected_animal = None
        self.selected_tree   = None