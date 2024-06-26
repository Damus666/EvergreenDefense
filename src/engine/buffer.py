from .usezen import USE_ZEN, zengl, moderngl
import math
import numpy
from . import ctx
from . import camera

DEFAULT_UV = [
    (0, 0),
    (1, 0),
    (0, 1),
    (1, 1)
]

def rect_positions_topleft(tx, ty, sx, sy, a=0):
    if a == 0:
        return [
            (tx, ty),
            (tx + sx, ty),
            (tx, ty + sy),
            (tx + sx, ty + sy)
        ]
    cx, cy = (tx+sx/2, ty+sy/2)
    cos, sin = math.cos(math.radians(a)), math.sin(math.radians(a))
    sx2, sy2 = sx/2, sy/2
    sx2cos, sx2sin, sy2cos, sy2sin = sx2*cos, sx2*sin, sy2*cos, sy2*sin
    return [
            (-sx2cos+sy2sin+cx, -sx2sin-sy2cos+cy),
            (sx2cos+sy2sin+cx, sx2sin-sy2cos+cy),
            (-sx2cos-sy2sin+cx, -sx2sin+sy2cos+cy),
            (sx2cos-sy2sin+cx, sx2sin+sy2cos+cy),
        ]
    
def rect_positions_center(cx, cy, sx, sy, a=0):
    return rect_positions_topleft(cx-sx/2, cy-sy/2, sx, sy, a)

def empty_vertices(buffer_data: list, amount):
    buffer_data.extend([0]*(amount*4*9))#[0 for _ in range()]
    
def rect_indices(amount):
    res = []
    offset = 0
    for _ in range(amount):
        res += [0+offset, 1+offset, 2+offset, 2+offset, 1+offset, 3+offset]
        offset += 4
    return numpy.fromiter(res, dtype=numpy.uint32)

def rect_uvs_sheet(cell_index, cell_width, sheet_width):
    return [
        ((cell_width*cell_index)/sheet_width, 0),
        ((cell_width*cell_index+cell_width)/sheet_width, 0),
        ((cell_width*cell_index)/sheet_width, 1),
        ((cell_width*cell_index+cell_width)/sheet_width, 1)
    ]
    
def rect_uvs_atlas(aw, ah, w, h, x, y):
    return [
        (x/aw, y/ah),
        ((x+w)/aw, y/ah),
        (x/aw, (y+h)/ah),
        ((x+w)/aw, (y+h)/ah),
    ]
    
def uvs_flipx(uvs):
    return [uvs[1], uvs[0], uvs[3], uvs[2]]

def uvs_flipy(uvs):
    return [uvs[2], uvs[3], uvs[0], uvs[1]]

class RectObj:
    def __init__(self, center=(0,0), topleft=None, size=(1,1), color=None, tex_id=0, uv=None, angle=0):
        self.color = color if color is not None else (1, 1, 1, 1)
        self.tex_id = tex_id
        self.uv = uv if uv is not None else DEFAULT_UV.copy()
        self.update_positions(center, topleft, size, angle)
        self._ = False
    
    def update_positions(self, center=(0,0), topleft=None, size=(1,1), angle=0):
        self.pos = center if center else topleft
        self.size = size
        self.positions = (rect_positions_center(*center, *size, angle)
                          if center is not None else 
                          rect_positions_topleft(*topleft, *size, angle))
        pos0, pos1, pos2, pos3 = self.positions
        uv0, uv1, uv2, uv3 = self.uv
        color, tex_id = self.color, self.tex_id

        self.buffer_data = [
            *pos0, *color, *uv0, tex_id,
            *pos1, *color, *uv1, tex_id,
            *pos2, *color, *uv2, tex_id,
            *pos3, *color, *uv3, tex_id,
        ]
        
    def update_buffer_data(self):
        pos0, pos1, pos2, pos3 = self.positions
        uv0, uv1, uv2, uv3 = self.uv
        color, tex_id = self.color, self.tex_id

        self.buffer_data = [
            *pos0, *color, *uv0, tex_id,
            *pos1, *color, *uv1, tex_id,
            *pos2, *color, *uv2, tex_id,
            *pos3, *color, *uv3, tex_id,
        ]
                
    @staticmethod
    def null():
        return RectObj((0,0), None, (0,0), (0, 0, 0, 0), 0, None)
    
"""
        self.buffer_data = [
            *self.positions[0], *self.color, *self.uv[0], self.tex_id,
            *self.positions[1], *self.color, *self.uv[1], self.tex_id,
            *self.positions[2], *self.color, *self.uv[2], self.tex_id,
            *self.positions[3], *self.color, *self.uv[3], self.tex_id,
        ]
        """
    
"""
[
            [self.positions[0][0], self.positions[0][1], self.color[0], self.color[1], self.color[2], self.color[3] , self.uv[0][0], self.uv[0][1], self.tex_id],
            [self.positions[1][0], self.positions[1][1], self.color[0], self.color[1], self.color[2], self.color[3], self.uv[1][0], self.uv[1][1], self.tex_id],
            [self.positions[2][0], self.positions[2][1], self.color[0], self.color[1], self.color[2], self.color[3], self.uv[2][0], self.uv[2][1], self.tex_id],
            [self.positions[3][0], self.positions[3][1], self.color[0], self.color[1], self.color[2], self.color[3], self.uv[3][0], self.uv[3][1], self.tex_id],
        ]
"""

def zen_tex(i):
    return {"name": f"textures[{i}]", "binding": i}

class FixedRectsBatch:
    def __init__(self, rect_objs: list[RectObj], dynamic: bool = False, amount=None):
        self.rect_objs = rect_objs
        self.rects_amount = len(self.rect_objs) if not amount else amount
        self.dynamic = dynamic
        self.pipeline = None
        self.create_buffers()
        
    def get_buffer_data(self):
        buffer_data = []
        for rect in self.rect_objs:
            buffer_data.extend(rect.buffer_data)
        empty_vertices(buffer_data, self.rects_amount-len(self.rect_objs))
        return numpy.fromiter(buffer_data, dtype=numpy.float32)
        
    def create_buffers(self):
        ibo_data = rect_indices(self.rects_amount)
        vbo_data = self.get_buffer_data() if len(self.rect_objs) > 0 else None
        reserve = (self.rects_amount*9*4*4 if len(self.rect_objs) <= 0 else 0)
        if USE_ZEN:
            
            self.ibo = ctx.ctx.buffer(ibo_data, index=True)
            if reserve > 0:
                self.vbo = ctx.ctx.buffer(None, size=reserve)
            else:
                self.vbo = ctx.ctx.buffer(vbo_data)
        else:
            self.ibo = ctx.ctx.buffer(ibo_data, dynamic=False)
            self.vbo = ctx.ctx.buffer(vbo_data, dynamic=self.dynamic, reserve=reserve)
        return self
        
    def create_vao(self, shader_name, *shader_uniforms):
        if USE_ZEN:
            if self.pipeline is not None:
                ctx.unregister_pipeline(self.pipeline)
            self.pipeline = ctx.make_pipeline(shader_name, self.vbo, self.ibo, shader_uniforms[0], self.vbo.size // zengl.calcsize(shader_uniforms[0]), [zen_tex(i) for i in range(3)])
            ctx.register_pipeline(self.pipeline, shader_name)
        else:
            self.vao = ctx.ctx.vertex_array(ctx.get_shader(shader_name), [(self.vbo, *shader_uniforms)], index_buffer=self.ibo)
        return self
        
    def update_rects(self, rect_objs: list[RectObj]=None):
        self.rect_objs = rect_objs if rect_objs is not None else self.rect_objs
        if len(self.rect_objs) > self.rects_amount:
            raise RuntimeError(f"Tried to add more rects to a fixed rect batch. Max size: {self.rects_amount}, attempt: {len(self.rect_objs)}")
        self.vbo.write(self.get_buffer_data())
        
    def free_rect_objs(self):
        self.rect_objs = []
        
    def render(self):
        if USE_ZEN:
            self.pipeline.viewport = (0, 0, camera.win_w, camera.win_h)
            self.pipeline.render()
        else:
            self.vao.render()
        
class GrowingRectsBatch:
    def __init__(self, shader_name, *shader_uniforms):
        self.shader_name, self.shader_uniforms = shader_name, shader_uniforms
        self.rect_objs: list[RectObj] = []
        self.reserved_amount = 5
        self.pipeline = None
        self.create_arrays()
        self.update_rects()

    def create_arrays(self):
        ibo_data = rect_indices(self.reserved_amount)
        reserve = self.reserved_amount*9*4*4
        if USE_ZEN:
            self.ibo = ctx.ctx.buffer(ibo_data, index=True)
            self.vbo = ctx.ctx.buffer(None, size=reserve)
            if self.pipeline is not None:
                ctx.unregister_pipeline(self.pipeline)
            self.pipeline = ctx.make_pipeline(self.shader_name, self.vbo, self.ibo, self.shader_uniforms[0], self.vbo.size // zengl.calcsize(self.shader_uniforms[0]), [zen_tex(i) for i in range(3)])
            ctx.register_pipeline(self.pipeline, self.shader_name)
        else:
            self.ibo = ctx.ctx.buffer(ibo_data, dynamic=False)
            self.vbo = ctx.ctx.buffer(reserve=reserve, dynamic=False)
            self.vao = ctx.ctx.vertex_array(ctx.get_shader(self.shader_name), [(self.vbo, *self.shader_uniforms)], index_buffer=self.ibo)
        
    def update_rects(self, rect_objs: list[RectObj]=None):
        self.rect_objs = rect_objs if rect_objs else self.rect_objs
        if len(self.rect_objs) > self.reserved_amount:
            self.reserved_amount = len(self.rect_objs)
            self.create_arrays()
        buffer_data = []
        for rect in self.rect_objs:
            buffer_data.extend(rect.buffer_data)
        empty_vertices(buffer_data, self.reserved_amount-len(self.rect_objs))
        self.vbo.write(numpy.fromiter(buffer_data, dtype=numpy.float32))
        
    def render(self):
        if USE_ZEN:
            self.pipeline.viewport = (0, 0, camera.win_w, camera.win_h)
            self.pipeline.render()
        else:
            self.vao.render()
        
    def free_rect_objs(self):
        self.rect_objs = []
