import math
from typing import Tuple, List, Any

class PhysicsEngine:

    @staticmethod
    def apply_separation(animals: List[Any], sep: float = 20.0):
        for i, a1 in enumerate(animals):
            if not hasattr(a1, 'coordinate'):
                continue
            for a2 in animals[i+1:]:
                if not hasattr(a2, 'coordinate'):
                    continue
                x1, y1 = a1.coordinate
                x2, y2 = a2.coordinate
                d = math.sqrt((x1-x2)**2 + (y1-y2)**2)
                if 0 < d < sep:
                    dx, dy = (x1-x2)/d, (y1-y2)/d
                    # 💡 [핵심 수정] 0.5는 너무 강하게 반발하여 진동을 일으킵니다. 0.1로 부드럽게 낮춤!
                    f = (sep - d) * 0.1 
                    a1.coordinate = [x1 + dx*f, y1 + dy*f]
                    a2.coordinate = [x2 - dx*f, y2 - dy*f]

    @staticmethod
    def keep_in_bounds(pos: Tuple[float,float],
                       map_w: int, map_h: int,
                       margin: int = 32) -> Tuple[float,float]:
        x, y = pos
        return (max(float(margin), min(float(map_w - margin), x)),
                max(float(margin), min(float(map_h - margin), y)))
