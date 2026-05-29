from ursina import *

class FlyingCamera(Entity):
    def __init__(self, map_w, map_h, **kwargs):
        super().__init__(**kwargs)
        self.map_w = map_w
        self.map_h = map_h
        
        self.position = (map_w / 2, 30, map_h / 2 - 30)
        self.rotation_x = 30
        
        camera.parent = self
        camera.position = (0, 0, 0)
        
        self.speed = 40
        self.mouse_sensitivity = 80

    def update(self):
        move_speed = self.speed * (2.0 if held_keys['shift'] else 1.0)
        
        right = held_keys['d'] or held_keys['right arrow']
        left = held_keys['a'] or held_keys['left arrow']
        forward = held_keys['w'] or held_keys['up arrow']
        backward = held_keys['s'] or held_keys['down arrow']
        upward = held_keys['space']
        downward = held_keys['c']
        
        self.position += self.forward * (forward - backward) * move_speed * time.dt
        self.position += self.right * (right - left) * move_speed * time.dt
        self.position += Vec3(0, 1, 0) * (upward - downward) * move_speed * time.dt
        
        self.x = clamp(self.x, 0, self.map_w)
        self.y = clamp(self.y, 2, 120)
        self.z = clamp(self.z, 0, self.map_h)

        # 🌟 핵심: 우클릭 중일 때 마우스를 화면에 가둬서(locked) 무한 회전 가능하게 함!
        if mouse.right:
            mouse.locked = True
            self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity
            self.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity
            self.rotation_x = clamp(self.rotation_x, -90, 90)
        else:
            mouse.locked = False

    def input(self, key):
        if key == 'scroll up':
            self.position += self.forward * 10
        if key == 'scroll down':
            self.position -= self.forward * 10