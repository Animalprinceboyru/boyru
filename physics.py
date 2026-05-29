import math
from typing import Tuple, List, Any

class PhysicsEngine:
    @staticmethod
    def move_towards(current_pos: Tuple[float,float],
                     target_pos:  Tuple[float,float],
                     speed: float, dt: float) -> Tuple[float,float]:
        cx, cy = current_pos
        tx, ty = target_pos
        dx, dy = tx - cx, ty - cy
        dist   = math.sqrt(dx*dx + dy*dy)
        if dist <= speed * dt or dist == 0:
            return target_pos
        return (cx + dx/dist * speed * dt,
                cy + dy/dist * speed * dt)

    @staticmethod
    def check_collision(p1, r1, p2, r2) -> bool:
        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) < r1 + r2

    @staticmethod
    def apply_separation(animals: List[Any], sep: float = 20.0):
        for i, a1 in enumerate(animals):
            if not hasattr(a1, 'coordinate'):
                continue
            for a2 in animals[i+1:]:
                if not hasattr(a2, 'coordinate'):
                    continue
                x1,y1 = a1.coordinate
                x2,y2 = a2.coordinate
                d = math.sqrt((x1-x2)**2 + (y1-y2)**2)
                if 0 < d < sep:
                    dx, dy = (x1-x2)/d, (y1-y2)/d
                    f = (sep - d) * 0.5
                    a1.coordinate = (x1 + dx*f, y1 + dy*f)
                    a2.coordinate = (x2 - dx*f, y2 - dy*f)

    @staticmethod
    def keep_in_bounds(pos: Tuple[float,float],
                       map_w: int, map_h: int,
                       margin: int = 32) -> Tuple[float,float]:
        x, y = pos
        return (max(float(margin), min(float(map_w - margin), x)),
                max(float(margin), min(float(map_h - margin), y)))
