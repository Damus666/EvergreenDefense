from .engine.prelude import *
import random

from .consts import *
from .settings import KC
from . import god
from . import ui

class UIRect:
    def __init__(self, size, center, topleft, name, category, settings, special_func=None, attr=None):
        if topleft is None:
            topleft = (center[0]-size[0]/2, center[1]-size[1]/2)
        self.rect = pygame.FRect(topleft, size)
        self.name, self.category = name, category
        self.was_hovered = False
        if self.name in settings.rects:
            self.was_hovered = settings.rects[self.name].hovered
        settings.rects[self.name] = self
        self.settings = settings
        self.hovered = self.was_hovered
        self.special_func, self.attr = special_func, attr
        
    def click(self):
        if self.special_func is not None:
            self.special_func(self.attr)
            return
        getattr(self.settings, f"{self.name}_click")()

class SettingsUI:
    def __init__(self, is_world=True):
        self.is_open = False
        self.is_world = is_world
        self.category = "general"
        
        self.main_batch = GrowingRectsBatch(UI_SHADER, *SHADER_UNIFORMS)
        self.general_batch = GrowingRectsBatch(UI_SHADER, *SHADER_UNIFORMS)
        self.perf_batch = GrowingRectsBatch(UI_SHADER, *SHADER_UNIFORMS)
        self.binds_batch = GrowingRectsBatch(UI_SHADER, *SHADER_UNIFORMS)
        
        self.rects: dict[str, UIRect] = {}
        self.clicked = False
        self.listening = False
        self.listen_mode = "main"
        self.listen_bind = None
        
        self.batches = {
            "general": self.general_batch,
            "performance": self.perf_batch,
            "binds": self.binds_batch
        }
                
    def build(self):
        ah, w, atop, left = camera.rect.h/1.4, camera.rect.w/2, -camera.rect.h/1.42/2, -camera.rect.w/4
        h, top = ah-MBTN_SIZE[1]-UI_S, atop+MBTN_SIZE[1]+UI_S
        left_cx, right_cx = left+w/4, left+((w/4)*3)
        main, general, perf, binds = [], [], [], []
        
        # main
        main += ui.image(None, camera.rect.size, "square", (0, 0, 0, 0.46), (0, 0))
        main += font.render_single_center(MAIN_FONT, f"{god.lang["settings"]}", (0, atop-BBTN_SIZE[1]*0.85), TITLE_SIZE)
        
        cx, cw = left, (w-UI_S*2)/3
        for category in ["general", "performance", "binds"]:
            r = UIRect((cw, MBTN_SIZE[1]), None, (cx, atop), f"{category}", "main", self, self.category_click, category)
            main += ui.button(r.rect.topleft, r.rect.size, HOVER_OUTLINE if r.was_hovered or self.category == category else UNHOVER_OUTLINE, f"{god.lang[category]}", BTN_TEXT)
            cx += cw+UI_S
            
        main += ui.panel_rect_objs((w, h), SHOP_CARD_C/2, (left, top), (0, 0, 0, 0.5))
        main += ui.panel_outline_rect_objs((w, h), SHOP_CARD_C/2, (left, top), UNHOVER_OUTLINE)
        r = UIRect(BBTN_SIZE, (0, ah/2+UI_S+BBTN_SIZE[1]/1.5), None, "back", "main", self)
        main += ui.button(None, r.rect.size, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, f"{god.lang["back"]}", 1.3, "m", r.rect.center)
        
        # general
        cy = top + UI_S*2 + BBTN_SIZE[1]/2
        general += font.render_single_center(MAIN_FONT, f"{god.lang["language"]}", (left_cx, cy), LABEL_SIZE)
        
        langs = god.lang.names()
        langsw = len(langs)*SBTN_SIZE[0]+UI_S*len(langs)
        langx = left+w-langsw
        for lang in langs:
            r = UIRect(SBTN_SIZE, (langx, cy), None, f"lang_{lang}", "general", self, self.lang_click, lang)
            general += ui.button(None, r.rect.size, HOVER_OUTLINE if r.was_hovered or god.settings.lang == lang else UNHOVER_OUTLINE, f"{lang}", BTN_TEXT, center=r.rect.center)
            langx += UI_S+SBTN_SIZE[0]

        if not USE_ZEN:
            cy += BBTN_SIZE[1]+UI_S
            general += font.render_single_center(MAIN_FONT, f"{god.lang["resolution"]}", (left_cx, cy), LABEL_SIZE)

            resw = langsw/2-UI_S
            resx = left+w-langsw+resw/2-SBTN_SIZE[0]/2
            for name, func in [("maximized", self.maximized_click), ("windowed", self.windowed_click)]:
                r = UIRect((resw, SBTN_SIZE[1]), (resx, cy), None, f"res_{name}", "general", self, func, name)
                general += ui.button(None, r.rect.size, HOVER_OUTLINE if r.was_hovered or god.settings.resolution == name else UNHOVER_OUTLINE, god.lang[name], BTN_TEXT, center=r.rect.center)
                resx += UI_S+resw

        cy += BBTN_SIZE[1]+UI_S
        general += font.render_single_center(MAIN_FONT, f"{god.lang["music"]}", (left_cx, cy), LABEL_SIZE)
        
        vol = round(god.settings.music_vol, 1)
        text = f"{god.lang["off"]}" if vol == 0 else f"{god.lang["max"]}" if vol == 1 else vol
        general += font.render_single_center(MAIN_FONT, f"{text}", (right_cx, cy), LABEL_SIZE)
        r = UIRect((SBTN_SIZE[1], SBTN_SIZE[1]), (right_cx-SBTN_SIZE[0]*1.2, cy), None, "music_minus", "general", self, self.music_click, -1)
        general += ui.button(None, r.rect.size, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, "-", BTN_TEXT, center=r.rect.center)
        r = UIRect((SBTN_SIZE[1], SBTN_SIZE[1]), (right_cx+SBTN_SIZE[0]*1.2, cy), None, "music_plus", "general", self, self.music_click, 1)
        general += ui.button(None, r.rect.size, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, "+", BTN_TEXT, center=r.rect.center)
        
        cy += BBTN_SIZE[1]+UI_S
        general += font.render_single_center(MAIN_FONT, f"{god.lang["sounds"]}", (left_cx, cy), LABEL_SIZE)
        
        vol = round(god.settings.fx_vol, 1)
        text = f"{god.lang["off"]}" if vol == 0 else f"{god.lang["max"]}" if vol == 1 else vol
        general += font.render_single_center(MAIN_FONT, f"{text}", (right_cx, cy), LABEL_SIZE)
        r = UIRect((SBTN_SIZE[1], SBTN_SIZE[1]), (right_cx-SBTN_SIZE[0]*1.2, cy), None, "fx_minus", "general", self, self.fx_click, -1)
        general += ui.button(None, r.rect.size, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, "-", BTN_TEXT, center=r.rect.center)
        r = UIRect((SBTN_SIZE[1], SBTN_SIZE[1]), (right_cx+SBTN_SIZE[0]*1.2, cy), None, "fx_plus", "general", self, self.fx_click, 1)
        general += ui.button(None, r.rect.size, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, "+", BTN_TEXT, center=r.rect.center)
        
        cy += BBTN_SIZE[1]+UI_S
        
        general += font.render_single_center(MAIN_FONT, f"{god.lang["manual-start-wave"]}", (left_cx, cy), LABEL_SIZE)
        r = UIRect((SBTN_SIZE[1], SBTN_SIZE[1]), (right_cx, cy), None, "manual_start_wave", "general", self)
        general += ui.checkbox(r.rect.center, r.rect.w, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, god.settings.manual_wave)
        
        cy = camera.rect.bottom-(camera.rect.h-h)/2-BBTN_SIZE[1]*1.5
        
        r = UIRect((BBTN_SIZE[0]*1.7, MBTN_SIZE[1]), (0, cy), None, "reset", "general", self)
        general += ui.button(r.rect.topleft, r.rect.size, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, f"{god.lang["reset-settings"]}", BTN_TEXT)
        
        cy += BBTN_SIZE[1]+UI_S/4
        
        r = UIRect((BBTN_SIZE[0]*1.7, MBTN_SIZE[1]), (0, cy), None, "delete", "general", self)
        general += ui.button(r.rect.topleft, r.rect.size, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, f"{god.lang["delete-settings"]}", BTN_TEXT)
        
        # performance
        cy = top + UI_S*2 + BBTN_SIZE[1]/2
        
        perf += font.render_single_center(MAIN_FONT, "FPS", (0, cy), LABEL_SIZE)
        cy += BBTN_SIZE[1]+UI_S
        
        optw = (len(FPS_OPTIONS)-1)*SBTN_SIZE[0]+MBTN_SIZE[0]+len(FPS_OPTIONS)*UI_S
        optx = -optw/2+SBTN_SIZE[0]/2
        for fps_option in FPS_OPTIONS:
            size = SBTN_SIZE if fps_option != 0 else (MBTN_SIZE[0], SBTN_SIZE[1])
            text = f"{fps_option}" if fps_option != 0 else god.lang["unlimited"]
            r = UIRect(size, (optx, cy), None, f"fps_{fps_option}", "performance", self, self.fps_click, fps_option)
            perf += ui.button(r.rect.topleft, r.rect.size, 
                              HOVER_OUTLINE if r.was_hovered or fps_option == god.settings.fps else UNHOVER_OUTLINE, text, BTN_TEXT)
            
            if fps_option != FPS_OPTIONS[-2]:
                optx += SBTN_SIZE[0]+UI_S
            else:
                optx += MBTN_SIZE[0]/2+UI_S+SBTN_SIZE[0]/2
        
        cy += BBTN_SIZE[1]+UI_S
        
        perf += font.render_single_center(MAIN_FONT, f"{god.lang["fps-counter"]}", (left_cx, cy), LABEL_SIZE)
        r = UIRect((SBTN_SIZE[1], SBTN_SIZE[1]), (right_cx, cy), None, "fps_counter", "performance", self)
        perf += ui.checkbox(r.rect.center, r.rect.w, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, god.settings.fps_counter)
        
        cy += BBTN_SIZE[1]+UI_S
        
        perf += font.render_single_center(MAIN_FONT, f"{god.lang["confetti"]}", (left_cx, cy), LABEL_SIZE)
        r = UIRect((SBTN_SIZE[1], SBTN_SIZE[1]), (right_cx, cy), None, "confetti", "performance", self)
        perf += ui.checkbox(r.rect.center, r.rect.w, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, god.settings.confetti)
        
        cy += BBTN_SIZE[1]+UI_S
        
        perf += font.render_single_center(MAIN_FONT, f"{god.lang["max-lights"]}", (left_cx, cy), LABEL_SIZE)
        perf += font.render_single_center(MAIN_FONT, f"{god.settings.max_lights}", (right_cx, cy), LABEL_SIZE)
        r = UIRect((SBTN_SIZE[1], SBTN_SIZE[1]), (right_cx-SBTN_SIZE[0]*1, cy), None, "lights_minus", "performance", self, self.lights_click, -1)
        perf += ui.button(None, r.rect.size, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, f"-", BTN_TEXT, center=r.rect.center)
        r = UIRect((SBTN_SIZE[1], SBTN_SIZE[1]), (right_cx+SBTN_SIZE[0]*1, cy), None, "lights_plus", "performance", self, self.lights_click, 1)
        perf += ui.button(None, r.rect.size, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, f"+", BTN_TEXT, center=r.rect.center)

        # binds
        cy = top + UI_S*1 + MBTN_SIZE[1]/2
        left_x, right_x = left_cx-w/10, right_cx-w/10
        rleft_x, rright_x = (right_x)-w/7, right_x+w/7
        
        binds += font.render_single_center(MAIN_FONT, f"{god.lang["main-key"]}", (rleft_x, cy), LABEL_SIZE)
        binds += font.render_single_center(MAIN_FONT, f"{god.lang["alt-key"]}", (rright_x, cy), LABEL_SIZE)
        
        cy += MBTN_SIZE[1]+UI_S*0.5
        
        for name, bind in god.settings.binds.items():
            if name == "ui_click":
                continue
            binds += font.render_single_center(MAIN_FONT, f"{god.lang[name]}", (left_x, cy), LABEL_SIZE)
            
            text = "Error"
            if bind.bind.type == "mouse":
                if bind.bind.code in MOUSE_CONVERSION:
                    text = f"{god.lang[MOUSE_CONVERSION[bind.bind.code]]}"
                else:
                    text = f"{god.lang["button"]} {bind.bind.code}"
            else:
                kstr = pygame.key.name(bind.bind.code).upper()
                if kstr.strip() == "":
                    kstr = f"{bind.bind.code}"
                text = f"{god.lang["key"]} {kstr}"
            if bind == self.listen_bind and self.listen_mode == "main":
                text = f"{god.lang["listening-key"]}"
            r = UIRect((MBTN_SIZE[0]*1.5, SBTN_SIZE[1]), (rleft_x, cy), None, f"{name}_main", "binds", self, self.main_bind_click, bind)
            binds += ui.button(r.rect.topleft, r.rect.size, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, text, BTN_TEXT)
            
            text = "Error"
            if len(bind.alts) > 0:
                if bind.alts[0].type == "mouse":
                    if bind.alts[0].code in MOUSE_CONVERSION:
                        text = f"{god.lang[MOUSE_CONVERSION[bind.alts[0].code]]}"
                    else:
                        text = f"{god.lang["button"]} {bind.alts[0].code}"
                else:
                    kstr = pygame.key.name(bind.alts[0].code).upper()
                    if kstr.strip() == "":
                        kstr = f"{bind.alts[0].code}"
                    text = f"{god.lang["key"]} {kstr}"
            else:
                text = f"{god.lang["unset"]}"
            if bind == self.listen_bind and self.listen_mode == "alt":
                text = f"{god.lang["listening-key"]}"
            r = UIRect((MBTN_SIZE[0]*1.5, SBTN_SIZE[1]), (rright_x, cy), None, f"{name}_alt", "binds", self, self.alt_bind_click, bind)
            binds += ui.button(r.rect.topleft, r.rect.size, HOVER_OUTLINE if r.was_hovered else UNHOVER_OUTLINE, text, BTN_TEXT)
            
            cy += MBTN_SIZE[1]+UI_S*0.5
        
        self.main_batch.update_rects(main)
        self.general_batch.update_rects(general)
        self.perf_batch.update_rects(perf)
        self.binds_batch.update_rects(binds)
        
    def render(self):
        self.main_batch.render()
        self.batches[self.category].render()
        
    def update(self):
        for name, rect in list(self.rects.items()):
            if rect.category == "main" or rect.category == self.category:
                if rect.rect.collidepoint(camera.ui_mouse):
                    if not self.clicked and god.settings.binds["ui_click"].check_frame():
                        rect.click()
                        god.sounds.play("click")
                    if not rect.hovered:
                        rect.hovered = True
                        god.sounds.play("hover", False)
                        self.build()
                else:
                    if rect.hovered:
                        rect.hovered = False
                        self.build()
        if god.settings.binds["ui_click"].check_frame():
            self.clicked = True
        else:
            self.clicked = False
            
    def event(self, event: pygame.Event):
        if not self.listening or not self.is_open:
            return
        kc = None
        if self.listen_mode == "alt" and len(self.listen_bind.alts) > 0:
            kc = self.listen_bind.bind if self.listen_mode == "main" else self.listen_bind.alts[0]
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE and self.listen_mode == "alt":
                self.listen_bind.alts = []
                self.listening = False
                self.listen_bind = None
                self.build()
                god.sounds.play("click")
                return
            if kc is None:
                kc = KC(0, "key")
                if self.listen_mode ==  "main":
                    self.listen_bind.bind = kc
                else:
                    self.listen_bind.alts.append(kc)
            kc.type = "key"
            kc.code = event.key
            self.listening = False
            self.listen_bind = None
            self.build()
            god.sounds.play("click")
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if kc is None:
                kc = KC(0, "mouse")
                if self.listen_mode ==  "main":
                    self.listen_bind.bind = kc
                else:
                    self.listen_bind.alts.append(kc)
            kc.type = "mouse"
            kc.code = event.button
            self.listening = False
            self.listen_bind = None
            self.build()
            god.sounds.play("click")

    def maximized_click(self, name):
        if USE_ZEN:
            return
        god.settings.resolution = name
        god.settings.maximize()
        if self.is_world:
            god.world.ui.build()
        else:
            god.menu.build()

    def windowed_click(self, name):
        if USE_ZEN:
            return
        god.settings.resolution = name
        god.settings.windowed()
        if self.is_world:
            god.world.ui.build()
        else:
            god.menu.build()
                        
    def back_click(self):
        self.is_open = False
        self.listening = False
        if not self.is_world:
            god.menu.close_settings()
        
    def category_click(self, category):
        self.category = category
        self.build()
        
    def lang_click(self, lang):
        god.settings.lang = lang
        if self.is_world:
            god.world.ui.build()
        else:
            god.menu.build()
        
    def music_click(self, dir):
        god.settings.music_vol += 0.1*dir
        god.settings.music_vol = pygame.math.clamp(god.settings.music_vol, 0, 1)
        self.build()
        god.sounds.update_volumes()
        
    def fx_click(self, dir):
        god.settings.fx_vol += 0.1*dir
        god.settings.fx_vol = pygame.math.clamp(god.settings.fx_vol, 0, 1)
        self.build()
        god.sounds.update_volumes()
        
    def lights_click(self, dir):
        god.settings.max_lights += 1*dir
        god.settings.max_lights = pygame.math.clamp(god.settings.max_lights, 5, MAX_LIGHTS)
        self.build()
        
    def fps_counter_click(self):
        god.settings.fps_counter = not god.settings.fps_counter
        self.build()
        
    def manual_start_wave_click(self):
        god.settings.manual_wave = not god.settings.manual_wave
        self.build()
        
    def confetti_click(self):
        god.settings.confetti = not god.settings.confetti
        self.build()
        
    def fps_click(self, fps):
        god.settings.fps = fps
        self.build()
        
    def main_bind_click(self, bind):
        self.listen_mode = "main"
        self.listening = True
        self.listen_bind = bind
        self.build()
        
    def alt_bind_click(self, bind):
        self.listen_bind = bind
        self.listening = True
        self.listen_mode = "alt"
        self.build()
        
    def reset_click(self):
        god.settings.reset_settings()
        self.build()
        
    def delete_click(self):
        god.settings.del_settings()
        self.build()

class ShopUI:
    def __init__(self):
        self.is_open = False
        self.ui_batch = GrowingRectsBatch(UI_SHADER, *SHADER_UNIFORMS)
        
        self.trees_rects = {}
        self.buildings_rects = {}
        
        self.hovered_trees = []
        self.hovered_buildings = []
        
        self.build()
                        
    def update(self):
        if not self.is_open:
            return
        
        for name, rect in self.trees_rects.items():
            if rect.collidepoint(camera.ui_mouse):
                tree = TreeData.get(name)
                can = (god.player.level >= tree.unlock_level and god.player.can_buy(tree.price)) or tree.name in god.player.inventory
                if not god.settings.tutorial.unlocked_plant():
                    can = False
                if name not in self.hovered_trees:
                    if can:
                        self.hovered_trees.append(name)
                        god.sounds.play("hover", False)
                        self.build()
                if can and god.settings.binds["ui_click"].check_frame():
                    self.close()
                    god.player.start_planting(TreeData.get(name))
                    god.sounds.play("click")
            else:
                if name in self.hovered_trees:
                    self.hovered_trees.remove(name)
                    self.build()
                    
        for name, rect in self.buildings_rects.items():
            if rect.collidepoint(camera.ui_mouse):
                building = BuildingData.get(name)
                can = god.player.can_buy(building.price) or building.name in god.player.inventory
                if not god.settings.tutorial.unlocked_building(building.name):
                    can = False
                if name not in self.hovered_buildings:
                    if can:
                        self.hovered_buildings.append(name)
                        god.sounds.play("hover", False)
                        self.build()
                if can and god.settings.binds["ui_click"].check_frame():
                    self.close()
                    god.player.start_building(BuildingData.get(name))
                    god.sounds.play("click")
            else:
                if name in self.hovered_buildings:
                    self.hovered_buildings.remove(name)
                    self.build()
            
        
    def build(self):
        rects = []
        
        hovered_name = None
        trees_amount = len(TreeData.get_all())
        total_w = SHOP_CARD_W*trees_amount+CARD_S*trees_amount
        x = -total_w/2
        y = -SHOP_CARD_W-CARD_S
        
        rects += font.render_single_center(MAIN_FONT, f"{god.lang["shop"]}", (0, y-CARD_S*6), TITLE_SIZE)
        
        for tree in sorted(TreeData.get_all(), key=lambda tree: tree.unlock_level):
            waited = not god.settings.tutorial.unlocked_plant()
            unlocked = god.player.level >= tree.unlock_level and not waited
            hovered = tree.name in self.hovered_trees
            if hovered and unlocked:
                hovered_name = tree.name
            
            rects += ui.panel_rect_objs((SHOP_CARD_W, SHOP_CARD_W), SHOP_CARD_C, (x, y), CARD_BG)
            rects += ui.panel_outline_rect_objs((SHOP_CARD_W, SHOP_CARD_W), SHOP_CARD_C, (x, y), UNHOVER_OUTLINE if not hovered else HOVER_OUTLINE)
            rects += ui.image(None, (SHOP_CARD_W/1.8, SHOP_CARD_W/1.8), tree.tex_name, WHITE if unlocked else LOCKED_IMG_COL,
                              (x+SHOP_CARD_W/2, y+SHOP_CARD_W/2))
            if not unlocked:
                rects += font.render_single_center(MAIN_FONT, f"{god.lang["wait"]}" if waited else f"{god.lang["level"]} {tree.unlock_level}", (x+SHOP_CARD_W/2, y+SHOP_CARD_W/2), 1.5)
            else:
                price = f"{tree.price}{god.lang["currency"]}" if tree.name not in god.player.inventory else f"{god.lang["free"]}"
                rects += font.render_single_center(MAIN_FONT, price, (x+SHOP_CARD_W/2, y+SHOP_CARD_W-CARD_S*2.2), 1.5, MONEY_COL)
                
            self.trees_rects[tree.name] = pygame.FRect(x, y, SHOP_CARD_W, SHOP_CARD_W)
            x += SHOP_CARD_W+CARD_S
        
        buildings_amount = len(BuildingData.get_all())
        total_w = SHOP_CARD_W*buildings_amount+CARD_S*buildings_amount
        x = -total_w/2
        y = CARD_S
        for building in [BuildingData.get(name) for name in [BOT, MINER, ENERGY_DISTRIBUTOR, ENERGY_SOURCE]]:
            hovered = building.name in self.hovered_buildings
            waited = not god.settings.tutorial.unlocked_building(building.name)
            if hovered and not waited:
                hovered_name = building.name
            
            rects += ui.panel_rect_objs((SHOP_CARD_W, SHOP_CARD_W), SHOP_CARD_C, (x, y), CARD_BG)
            rects += ui.panel_outline_rect_objs((SHOP_CARD_W, SHOP_CARD_W), SHOP_CARD_C, (x, y), UNHOVER_OUTLINE if not hovered else HOVER_OUTLINE)
            rects += ui.image(None, (SHOP_CARD_W/1.8, SHOP_CARD_W/1.8), building.tex_name, WHITE if not waited else LOCKED_IMG_COL,
                              (x+SHOP_CARD_W/2, y+SHOP_CARD_W/2))
            if not waited:
                price = f"{building.price}{god.lang["currency"]}" if building.name not in god.player.inventory else f"{god.lang["free"]}"
                rects += font.render_single_center(MAIN_FONT, price, (x+SHOP_CARD_W/2, y+SHOP_CARD_W-CARD_S*2.2), 1.5, MONEY_COL)
            else:
                rects += font.render_single_center(MAIN_FONT, f"{god.lang["wait"]}", (x+SHOP_CARD_W/2, y+SHOP_CARD_W/2), 1.5)

            self.buildings_rects[building.name] = pygame.FRect(x, y, SHOP_CARD_W, SHOP_CARD_W)
            x += SHOP_CARD_W+CARD_S
            
        if hovered_name is not None:
            desc_txt, desc_w, desc_h = font.render_full(MAIN_FONT, f"{god.lang[f"{hovered_name}-desc"]}", (0, camera.rect.h/3.5), 1, "center", camera.rect.w/6)
            txt = f"{god.lang[hovered_name]}"
            title_txt = font.render_single(MAIN_FONT, txt, (0, camera.rect.h/3.5-desc_h/2-S), 1.7, "mb")
            title_h, title_w = font.render_single_height(MAIN_FONT, 1.7), font.render_single_width(MAIN_FONT, txt, 1.7)
            cum_h, cum_w = desc_h+S*6+title_h, max(title_w+S*6, desc_w+S*6)
            center_h = ((camera.rect.h/3.5+desc_h/2)+(camera.rect.h/3.5-desc_h/2-S*7-title_h/2))/2
            tl = (0-cum_w/2, center_h-cum_h/2)
            rects += ui.panel_rect_objs((cum_w, cum_h), 0, tl, CARD_BG)
            rects += desc_txt
            rects += title_txt
        
        self.ui_batch.update_rects(rects)
        
    def render(self):
        self.ui_batch.render()
        
    def toggle(self):
        self.is_open = not self.is_open
        
    def close(self):
        self.is_open = False
        
class PauseUI:
    def __init__(self):
        self.is_open = False
        self.ui_batch = GrowingRectsBatch(UI_SHADER, *SHADER_UNIFORMS)
        self.settings = SettingsUI()
        
        self.rects = {}
        self.hovered_btns = []
        
        self.build()
        
    def build(self):
        rects = []
        
        rects += ui.image(None, camera.rect.size, "square", (0, 0, 0, 0.46), (0, 0))
        y = -BBTN_SIZE[1]*2-CARD_S*2+BBTN_SIZE[1]/2
        rects += font.render_single_center(MAIN_FONT, f"{god.lang["paused"]}", (0, y-BBTN_SIZE[1]*1.5), TITLE_SIZE-0.4)
        
        for btn in ["resume", "menu", "settings", "quit"]:
            hovered = btn in self.hovered_btns
            rects += ui.panel_rect_objs(BBTN_SIZE, BTN_C, (-BBTN_SIZE[0]/2, y-BBTN_SIZE[1]/2), BTN_BG)
            rects += ui.panel_outline_rect_objs(BBTN_SIZE, BTN_C, (-BBTN_SIZE[0]/2, y-BBTN_SIZE[1]/2), HOVER_OUTLINE if hovered else UNHOVER_OUTLINE, "m")
            rects += font.render_single_center(MAIN_FONT, f"{god.lang[btn]}", (0, y), 1.3)
            
            rect = pygame.FRect((0, 0), BBTN_SIZE)
            rect.center = (0, y)
            self.rects[btn] = rect
            
            if btn != "settings":
                y += BBTN_SIZE[1]+CARD_S
            else:
                y += BBTN_SIZE[1]*3+CARD_S
        
        self.ui_batch.update_rects(rects)
        self.settings.build()
        
    def update(self):
        if not self.is_open:
            return

        if self.settings.is_open:
            self.settings.update()
            return
        
        for btn, rect in self.rects.items():
            if rect.collidepoint(camera.ui_mouse):
                if btn not in self.hovered_btns:
                    self.hovered_btns.append(btn)
                    god.sounds.play("hover", False)
                    self.build()
                if god.settings.binds["ui_click"].check_frame():
                    getattr(self, f"{btn}_click")()
                    god.sounds.play("click")
            else:
                if btn in self.hovered_btns:
                    self.hovered_btns.remove(btn)
                    self.build()
                    
    def resume_click(self):
        self.close()
        
    def menu_click(self):
        self.close()
        god.app.load_scene("MainMenu")
        
    def settings_click(self):
        self.settings.is_open = True
        
    def quit_click(self):
        god.app.quit()
        
    def render(self):
        if self.settings.is_open:
            self.settings.render()
            return
        self.ui_batch.render()
        
    def open(self):
        self.is_open = True
        #god.sounds.play("pause")
        god.sounds.music_pause()
        camera.pause()
        
    def close(self):
        self.is_open = False
        god.sounds.music_resume()
        camera.unpause()
        
    def toggle(self):
        if self.settings.is_open:
            self.settings.is_open = False
            self.settings.listening = False
            return
        self.close() if self.is_open else self.open()

class Indicator:
    def __init__(self, type, amount):
        amount = int(amount)
        self.pos = pygame.Vector2(random.uniform(-camera.rect.w/4, camera.rect.w/4), random.uniform(-camera.rect.h/4, camera.rect.h/4))
        self.scale = random.uniform(1.4, 1.5)
        self.text = f"+{amount}{god.lang["currency"]}" if type == "money" else f"+{amount} {god.lang["xp"]}"
        self.col = MONEY_COL if type == "money" else (0, 0.6, 1, 1)
        self.speed = random.uniform(1, 2)
        self.duration = random.uniform(1.8, 2.2)
        self.born = camera.get_ticks()
        god.world.ui.indicators.append(self)
        if type == "money":
            god.sounds.play("money")
        
    def update(self):
        if camera.get_ticks() - self.born > self.duration*1000:
            god.world.ui.indicators.remove(self)
            return []
        
        self.pos += pygame.Vector2(0, -1)*self.speed*camera.dt
        return font.render_single_center(MAIN_FONT, self.text, self.pos, self.scale, self.col)
