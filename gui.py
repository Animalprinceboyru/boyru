import pygame
import time
from typing import Optional, List, Any

# 공통 색상
COLOR_TEXT      = (240, 240, 240)
COLOR_HIGHLIGHT = (255, 220, 50)
COLOR_SUCCESS   = (100, 220, 120)
COLOR_HP        = (220, 60,  60)
COLOR_STAMINA   = (60,  180, 220)

# 전역 텍스트 기본 투명도 (0 ~ 255, 255가 완전 불투명)
TEXT_ALPHA = 200 

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

        self.info_panel = pygame.Surface((340, 310), pygame.SRCALPHA)
        self.minimap    = pygame.Surface((200, 150), pygame.SRCALPHA)

        self.selected_animal: Optional[Any] = None
        self.selected_tree:   Optional[Any] = None
        
        self.logs = [] 

    # ══════════════════════════════════════════
    # 텍스트 + 얇은 그림자 렌더링 (배경이 없어도 잘 보이게)
    # ══════════════════════════════════════════
    def _render_text(self, font, text, color, alpha=TEXT_ALPHA):
        text_surf = font.render(text, True, color).convert_alpha()
        shadow_surf = font.render(text, True, (0, 0, 0)).convert_alpha()
        
        # 글씨 및 그림자 투명도 설정
        text_surf.set_alpha(alpha)
        shadow_surf.set_alpha(int(alpha * 0.7)) 
        
        w, h = text_surf.get_size()
        # 그림자를 1픽셀 뒤에 깔아서 합침
        final_surf = pygame.Surface((w + 1, h + 1), pygame.SRCALPHA)
        final_surf.blit(shadow_surf, (1, 1))
        final_surf.blit(text_surf, (0, 0))
        
        return final_surf

    def add_log(self, text: str):
        clean_text = text.strip()
        if clean_text:
            self.logs.append((clean_text, time.time()))
            if len(self.logs) > 8:
                self.logs.pop(0)

    def draw(self, screen, weather_system, camera, game_map, animals):
        self._draw_top_bar(screen, weather_system, camera)
        self._draw_minimap(screen, camera, game_map, animals)
        self._draw_controls(screen, weather_system)
        
        self._draw_logs(screen)
        self._draw_population(screen, animals)

        if self.selected_animal is not None:
            self._draw_animal_panel(screen)
        elif self.selected_tree is not None:
            self._draw_tree_panel(screen)

    # ══════════════════════════════════════════
    # 생태계 개체수 현황판 (배경 제거 완료)
    # ══════════════════════════════════════════
    def _draw_population(self, screen, animals):
        counts = {}
        total_animals = 0
        for a in animals:
            if getattr(a, 'alive', False):
                cname = type(a).__name__
                counts[cname] = counts.get(cname, 0) + 1
                total_animals += 1
        
        kor_names = {
            "Capybara": "카피바라", "Monkey": "원숭이", "Parrot": "앵무새", 
            "ToxicFrog": "독개구리", "Mosquito": "모기", "Anaconda": "아나콘다", 
            "Crocodile": "악어", "Tarantula": "타란튤라", "Rhino": "코뿔소", 
            "ElectricEel": "전기뱀장어"
        }
        
        pad_x, pad_y = 12, 12
        line_h = 22
        start_x = 16
        start_y = 65
        
        ts = self._render_text(self.font_title, f"[총 개체수: {total_animals}마리]", COLOR_HIGHLIGHT)
        screen.blit(ts, (start_x + pad_x, start_y + pad_y))
        
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        max_bar_width = 80 
        
        for i, (eng_name, cnt) in enumerate(sorted_counts):
            kor_name = kor_names.get(eng_name, eng_name)
            
            # 글씨
            name_surf = self._render_text(self.font_small, f"{kor_name[:4]}", (200, 200, 200))
            y_offset = start_y + pad_y + 28 + i * line_h
            screen.blit(name_surf, (start_x + pad_x, y_offset + 2))
            
            # 투명한 바(Bar) 그래프
            bar_color = (220, 80, 80) if eng_name in ["Anaconda", "Crocodile", "Tarantula", "ElectricEel", "ToxicFrog"] else (100, 220, 120)
            ratio = cnt / max(total_animals, 1)
            bar_w = int(max_bar_width * ratio)
            bar_x = start_x + pad_x + 50
            
            bar_surf = pygame.Surface((max_bar_width, 10), pygame.SRCALPHA)
            pygame.draw.rect(bar_surf, (50, 50, 50, 100), (0, 0, max_bar_width, 10)) 
            if bar_w > 0:
                pygame.draw.rect(bar_surf, (*bar_color, 160), (0, 0, bar_w, 10))
            screen.blit(bar_surf, (bar_x, y_offset + 4))
                
            # 숫자
            cnt_surf = self._render_text(self.font_small, f"{cnt}", (255, 255, 255))
            screen.blit(cnt_surf, (bar_x + max_bar_width + 8, y_offset + 1))

    # ══════════════════════════════════════════
    # 화면 로그 렌더링 (배경 제거 완료)
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
            
            alpha = TEXT_ALPHA
            age = current_time - t
            if age > 5.0:
                alpha = max(0, int(TEXT_ALPHA * (1.0 - (age - 5.0) / 2.0)))

            surf = self._render_text(self.log_font, txt, (255, 255, 255), alpha)
            screen.blit(surf, (start_x + 8, y_pos + 4))

    # ══════════════════════════════════════════
    # 상단 바 (배경 제거 완료)
    # ══════════════════════════════════════════
    def _draw_top_bar(self, screen, weather_system, camera):
        ws = self._render_text(self.font_title, f"날씨: {weather_system.current.value}", COLOR_TEXT)
        screen.blit(ws, (16, 10))

        time_str = f"시간: {weather_system.time_string}  배속: {weather_system.speed_string}"
        ts = self._render_text(self.font_title, time_str, COLOR_HIGHLIGHT)
        screen.blit(ts, (self.screen_w // 2 - ts.get_width() // 2, 10))

        info = f"줌 {camera.zoom:.2f}x  |  이동속도 {weather_system.get_speed_modifier():.2f}x  |  시야 {weather_system.get_visibility_modifier():.2f}x"
        es = self._render_text(self.font_small, info, (180, 210, 180))
        screen.blit(es, (self.screen_w - es.get_width() - 16, 14))

        hint = "[ : 느리게    ] : 빠르게"
        hs = self._render_text(self.font_small, hint, (150, 180, 150))
        screen.blit(hs, (self.screen_w // 2 - hs.get_width() // 2, 34))

    # ══════════════════════════════════════════
    # 미니맵 (배경은 투명, 내용물은 약간 투명하게)
    # ══════════════════════════════════════════
    def _draw_minimap(self, screen, camera, game_map, animals):
        mm_x = self.screen_w - 210
        mm_y = self.screen_h - 160
        self.minimap.fill((0, 0, 0, 0)) # 배경 완전 투명

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
                    # 맵 픽셀들에도 투명도를 줌
                    pygame.draw.rect(self.minimap, (*color, 160), (mx_, my_, mw, mh))

            for animal in animals:
                if getattr(animal,'alive',False) and hasattr(animal, 'coordinate'):
                    ax = int(animal.coordinate[0] * sx)
                    ay = int(animal.coordinate[1] * sy)
                    c  = getattr(animal, 'minimap_color', COLOR_HIGHLIGHT)
                    pygame.draw.circle(self.minimap, (*c, 200), (ax, ay), 3)

            vx = int(camera.x * sx)
            vy = int(camera.y * sy)
            vw = int(camera.screen_w / camera.zoom * sx)
            vh = int(camera.screen_h / camera.zoom * sy)
            pygame.draw.rect(self.minimap, (255, 255, 255, 120), (vx, vy, vw, vh), 2)

        except ImportError:
            pass

        screen.blit(self.minimap, (mm_x, mm_y))
        label = self._render_text(self.font_small, "미니맵", COLOR_SUCCESS)
        screen.blit(label, (mm_x + 6, mm_y - 18))

    # ══════════════════════════════════════════
    # 동물 패널 (배경 제거 완료)
    # ══════════════════════════════════════════
    def _draw_animal_panel(self, screen):
        animal = self.selected_animal
        self.info_panel.fill((0, 0, 0, 0)) # 배경 완전 투명

        name = type(animal).__name__
        ts   = self._render_text(self.font_title, f"[동물] {name.upper()}", COLOR_HIGHLIGHT)
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
        ss = self._render_text(self.font_small, f"상태: {status_str}", sc)
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
            s = self._render_text(self.font_normal, f"{label}: {val}", COLOR_TEXT)
            self.info_panel.blit(s, (12, 102 + i * 22))

        panel_x = self.screen_w - 340 - 16
        panel_y = 65
        screen.blit(self.info_panel, (panel_x, panel_y))

    # ══════════════════════════════════════════
    # 나무 패널 (배경 제거 완료)
    # ══════════════════════════════════════════
    def _draw_tree_panel(self, screen):
        tree = self.selected_tree
        self.info_panel.fill((0, 0, 0, 0)) # 배경 완전 투명

        ts = self._render_text(self.font_title, "[나무 정보]", COLOR_SUCCESS)
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
            rows.append(("둥지상태", "점유됨" if tree.nest_occupied else "비어있음"))

        for i, (label, val) in enumerate(rows):
            color = (COLOR_SUCCESS if "둥지" in label and tree.has_nest else COLOR_TEXT)
            s = self._render_text(self.font_normal, f"{label}: {val}", color)
            self.info_panel.blit(s, (12, 80 + i * 26))

        guide = self._render_text(self.font_small, "원숭이가 수관 영역에 올라갈 수 있습니다", (150, 200, 150))
        self.info_panel.blit(guide, (12, 80 + len(rows) * 26 + 10))

        panel_x = self.screen_w - 340 - 16
        panel_y = 65
        screen.blit(self.info_panel, (panel_x, panel_y))

    # ══════════════════════════════════════════
    # 조작법 안내 (배경 제거 완료)
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
        ph = len(lines) * lh + 16
        px = 16
        py = self.screen_h - ph - 16

        for i, (text, is_title) in enumerate(lines):
            if not text:
                continue
            color = COLOR_HIGHLIGHT if is_title else (180, 200, 180)
            font  = self.font_normal if is_title else self.font_small
            s = self._render_text(font, text, color)
            screen.blit(s, (px + 12, py + 8 + i * lh))

    # ══════════════════════════════════════════
    # 스탯 바 (투명도 적용)
    # ══════════════════════════════════════════
    def _bar(self, surface, x, y, w, h, current, maximum, color, label):
        bar_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bar_surf, (50, 50, 50, 100), (0, 0, w, h))
        if maximum > 0:
            fw = int(w * max(0.0, min(1.0, current / maximum)))
            if fw > 0:
                pygame.draw.rect(bar_surf, (*color, 160), (0, 0, fw, h))
        pygame.draw.rect(bar_surf, (150, 150, 150, 100), (0, 0, w, h), 1)
        surface.blit(bar_surf, (x, y))
        
        ts = self._render_text(self.font_small, f"{label}: {int(current)} / {int(maximum)}", COLOR_TEXT)
        surface.blit(ts, (x + 6, y + 2))

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