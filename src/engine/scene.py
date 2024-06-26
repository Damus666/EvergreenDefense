import pygame
import sys
import asyncio

from . import ctx, camera

class Scene:
    name: str
    
    def __init__(self, manager: "SceneManager", *init_args):
        self.manager = manager
        self.clear_color = (0, 0, 0, 1)
        self.init(*init_args)

    def window_resized(self):
        ...
    
    def init(self, *init_args):
        ...
        
    def update(self):
        ...
        
    def render(self):
        ...
        
    def event(self, event):
        ...
        
    def __init_subclass__(cls) -> None:
        scenes[cls.__name__] = cls
        cls.name = cls.__name__

scenes: dict[str, type] = {}

class SceneManager:        
    def load_scene(self, name, *init_args):
        camera.zoom = 1
        camera.position = pygame.Vector2(0, 0)
        camera.unpause()
        camera.make_proj()
        camera.update_view()
        camera.update_mouse()
        
        self.scene: Scene = scenes[name](self, *init_args)
        
    def on_quit(self):
        ...
        
    def quit(self):
        self.on_quit()
        pygame.quit()
        sys.exit()
        
    async def run(self):
        camera.dt = 0
        while True:
            ctx.new_frame()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.VIDEORESIZE:
                    camera.window_resized(event.w, event.h)
                    
                self.scene.event(event)
            
            ctx.clear(self.scene.clear_color) 
            camera.update_mouse()
            camera.update_view()
            self.scene.update()
            self.pre_render()
            self.scene.render()
            ctx.end_frame()
            self.post_render()
        
            await asyncio.sleep(0)

    def pre_render(self):
        ...

    def post_render(self):
        ...
            