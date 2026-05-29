from ursina import *
import random
import math

COLOR_DEEP_WATER = color.rgb32(25, 70, 85)
COLOR_WATER = color.rgb32(40, 95, 115)
COLOR_MUD = color.rgb32(95, 70, 45)
COLOR_JUNGLE = color.rgb32(40, 75, 30)
COLOR_TREE_TRUNK = color.rgb32(50, 32, 18)
COLOR_TREE_LEAVES = color.rgb32(28, 75, 28)

class GameMap3D:
    def __init__(self, width=150, height=150):
        self.width = width
        self.height = height
        
        # 최적화를 위해 나무와 지형을 하나로 묶어줄 부모 객체
        self.terrain_parent = Entity()
        self.tree_parent = Entity()
        
        self.generate_environment()

    def generate_environment(self):
        # 1. 밀림 바닥
        Entity(model='plane', scale=(self.width, 1, self.height), 
               color=COLOR_JUNGLE, position=(self.width/2, -0.5, self.height/2))
        
        # 2. 강과 나무 생성
        for x in range(0, self.width, 2):
            for z in range(0, self.height, 2):
                
                river_center = self.width / 2 + math.sin(z * 0.05) * 25
                dist_to_river = abs(x - river_center)
                
                if dist_to_river < 6 + math.sin(z * 0.1) * 2:
                    Entity(parent=self.terrain_parent, model='cube', color=COLOR_DEEP_WATER,
                           position=(x, -0.4, z), scale=(2, 1.1, 2))
                elif dist_to_river < 10:
                    Entity(parent=self.terrain_parent, model='cube', color=COLOR_WATER,
                           position=(x, -0.4, z), scale=(2, 1.1, 2))
                elif dist_to_river < 14:
                    Entity(parent=self.terrain_parent, model='cube', color=COLOR_MUD,
                           position=(x, -0.4, z), scale=(2, 1.2, 2))
                else:
                    tree_chance = 0.4 if dist_to_river < 35 else 0.1
                    if random.random() < tree_chance:
                        self.spawn_tree(x, z)
                        
        # 메시 합치기 (최적화)
        self.terrain_parent.combine()
        self.tree_parent.combine()

    def spawn_tree(self, x, z):
        ox = x + random.uniform(-0.8, 0.8)
        oz = z + random.uniform(-0.8, 0.8)
        height = random.uniform(2, 4.5)
        
        Entity(parent=self.tree_parent, model='cube', color=COLOR_TREE_TRUNK,
               position=(ox, height/2, oz), scale=(0.5, height, 0.5))
        Entity(parent=self.tree_parent, model='cube', color=COLOR_TREE_LEAVES,
               position=(ox, height + 0.5, oz), scale=(2.5, 2, 2.5))