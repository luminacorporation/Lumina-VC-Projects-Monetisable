"""
VOID RUNNER — Raycaster FPS
Requires: pip install pygame
Run:      python void_runner.py

Controls:
  W/A/S/D or Arrow Keys — Move
  Mouse                 — Look
  Left Click            — Shoot
  R                     — Reload
  Left Shift            — Sprint
  ESC                   — Quit / Pause
"""

import pygame
import sys
import math
import random
import time

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
W, H        = 1280, 720
FOV         = math.pi / 3          # 60°
HALF_FOV    = FOV / 2
NUM_RAYS    = W // 2               # one ray per 2 pixels (fast)
MAX_DEPTH   = 20
WALL_STRIP  = W // NUM_RAYS
MOVE_SPEED  = 0.055
ROT_SPEED   = 0.002               # mouse sensitivity
SPRINT_MULT = 1.7
FPS_CAP     = 60
MAX_WAVES   = 5

# colours
NEON      = (0, 255, 231)
NEON_DIM  = (0, 100, 90)
RED       = (255, 34,  68)
ORANGE    = (255, 140,  0)
PURPLE    = (180,  0, 255)
WHITE     = (255, 255, 255)
BLACK     = (0,   0,   0)
DARK      = (5,   10,  15)
MID       = (10,  21,  32)
GREY      = (30,  45,  55)

# ─────────────────────────────────────────────
#  MAP  (1 = wall, 0 = open)
# ─────────────────────────────────────────────
MAP_W, MAP_H = 16, 16
RAW_MAP = (
    "1111111111111111"
    "1000000000000001"
    "1000000000000001"
    "1001100000011001"
    "1001000000001001"
    "1000000000000001"
    "1000010001000001"
    "1000000000000001"
    "1000000000000001"
    "1000010001000001"
    "1000000000000001"
    "1001000000001001"
    "1001100000011001"
    "1000000000000001"
    "1000000000000001"
    "1111111111111111"
)
MAP = [int(c) for c in RAW_MAP]

def map_at(x, y):
    xi, yi = int(x), int(y)
    if xi < 0 or xi >= MAP_W or yi < 0 or yi >= MAP_H:
        return 1
    return MAP[yi * MAP_W + xi]

# ─────────────────────────────────────────────
#  ENEMY TYPES
# ─────────────────────────────────────────────
ENEMY_TYPES = [
    {"name": "DRONE",  "color": RED,    "speed": 0.010, "max_hp": 1, "size": 0.35, "score": 100, "atk_cd": 100},
    {"name": "GUARD",  "color": ORANGE, "speed": 0.006, "max_hp": 3, "size": 0.50, "score": 300, "atk_cd": 80 },
    {"name": "SHADE",  "color": PURPLE, "speed": 0.015, "max_hp": 1, "size": 0.28, "score": 200, "atk_cd": 70 },
]

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# ─────────────────────────────────────────────
#  RAYCASTER
# ─────────────────────────────────────────────
def cast_ray(px, py, angle):
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    # DDA step
    x, y = px, py
    for _ in range(int(MAX_DEPTH / 0.05)):
        x += cos_a * 0.05
        y += sin_a * 0.05
        if map_at(x, y):
            d = dist(px, py, x, y)
            return d
    return MAX_DEPTH

# ─────────────────────────────────────────────
#  GAME CLASS
# ─────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("VOID RUNNER")
        self.screen = pygame.display.set_mode((W, H))
        self.clock  = pygame.time.Clock()

        # fonts
        self.font_hud   = pygame.font.SysFont("Courier New", 20, bold=True)
        self.font_big   = pygame.font.SysFont("Courier New", 80, bold=True)
        self.font_med   = pygame.font.SysFont("Courier New", 36, bold=True)
        self.font_sm    = pygame.font.SysFont("Courier New", 18, bold=True)

        # off-screen 3-D buffer (half-width for speed, upscaled)
        self.surf3d = pygame.Surface((W // 2, H))
        self.z_buf  = [MAX_DEPTH] * NUM_RAYS

        self.state   = "start"   # start | play | end
        self.running = True

        self._init_player()
        self.enemies     = []
        self.particles   = []
        self.killfeed    = []   # list of (text, expire_time)
        self.wave_msg    = ""
        self.wave_msg_t  = 0
        self.hit_flash   = 0    # frames remaining
        self.muzzle_flash= 0
        self.weapon_bob  = 0.0
        self.weapon_fire = 0.0
        self.total_kills = 0
        self.start_time  = 0

    # ── player reset ────────────────────────────
    def _init_player(self):
        self.px    = 2.5
        self.py    = 2.5
        self.angle = 0.8
        self.hp    = 100
        self.max_hp= 100
        self.ammo  = 12
        self.max_ammo = 12
        self.reloading   = False
        self.reload_timer= 0
        self.score = 0
        self.wave  = 1
        self.alive = True

    # ─────────────────────────────────────────
    #  WAVE
    # ─────────────────────────────────────────
    def spawn_wave(self, wave):
        count = 4 + wave * 2
        self.enemies = []
        for _ in range(count):
            max_type = min(wave - 1, len(ENEMY_TYPES) - 1)
            t = random.choice(ENEMY_TYPES[:max_type + 1])
            while True:
                ex = 1.5 + random.random() * (MAP_W - 3)
                ey = 1.5 + random.random() * (MAP_H - 3)
                if not map_at(ex, ey) and dist(ex, ey, self.px, self.py) > 3:
                    break
            self.enemies.append({
                **t,
                "x": ex, "y": ey,
                "hp": t["max_hp"],
                "atk_timer": t["atk_cd"],
            })
        self.show_wave_msg(f"-- WAVE {wave} --")

    def show_wave_msg(self, msg):
        self.wave_msg   = msg
        self.wave_msg_t = pygame.time.get_ticks() + 2500

    def next_wave(self):
        self.wave += 1
        if self.wave > MAX_WAVES:
            self.state = "end"
            return
        self.hp = min(self.max_hp, self.hp + 30)
        self.ammo = self.max_ammo
        self.reloading = False
        self.spawn_wave(self.wave)

    # ─────────────────────────────────────────
    #  SHOOTING
    # ─────────────────────────────────────────
    def shoot(self):
        if not self.alive or self.reloading or self.ammo <= 0:
            return
        self.ammo -= 1
        self.muzzle_flash = 6
        self.weapon_fire  = 1.0

        # find closest enemy in crosshair cone
        hit    = None
        best_d = 999
        half_fov = FOV / 6   # aim cone ≈ 10°
        for e in self.enemies:
            dx  = e["x"] - self.px
            dy  = e["y"] - self.py
            d   = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            diff = ang - self.angle
            # normalise
            while diff >  math.pi: diff -= math.pi * 2
            while diff < -math.pi: diff += math.pi * 2
            if abs(diff) < half_fov and d < best_d:
                best_d = d
                hit    = e

        if hit:
            hit["hp"] -= 1
            self.spawn_particles(hit["x"], hit["y"], hit["color"], 6)
            if hit["hp"] <= 0:
                self.score += hit["score"]
                self.total_kills += 1
                self.killfeed.append((f"YOU >> {hit['name']}",
                                      pygame.time.get_ticks() + 2500))
                self.enemies.remove(hit)
                if not self.enemies:
                    pygame.time.set_timer(pygame.USEREVENT + 1, 1800, 1)

        if self.ammo == 0:
            pygame.time.set_timer(pygame.USEREVENT + 2, 400, 1)  # auto-reload

    def start_reload(self):
        if self.reloading or self.ammo == self.max_ammo:
            return
        self.reloading    = True
        self.reload_timer = pygame.time.get_ticks() + 1800

    # ─────────────────────────────────────────
    #  PARTICLES
    # ─────────────────────────────────────────
    def spawn_particles(self, x, y, color, n=5):
        for _ in range(n):
            a = random.uniform(0, math.pi * 2)
            s = random.uniform(0.03, 0.09)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(a) * s,
                "vy": math.sin(a) * s,
                "life": 1.0,
                "color": color,
                "size": random.randint(2, 5),
            })

    def update_particles(self):
        for p in self.particles:
            p["x"]    += p["vx"]
            p["y"]    += p["vy"]
            p["life"] -= 0.05
        self.particles = [p for p in self.particles if p["life"] > 0]

    # ─────────────────────────────────────────
    #  PLAYER MOVEMENT
    # ─────────────────────────────────────────
    def update_player(self, keys):
        sprint = SPRINT_MULT if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 1.0
        spd    = MOVE_SPEED * sprint
        nx, ny = self.px, self.py
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            nx += math.cos(self.angle) * spd
            ny += math.sin(self.angle) * spd
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            nx -= math.cos(self.angle) * spd
            ny -= math.sin(self.angle) * spd
        if keys[pygame.K_a]:
            nx += math.cos(self.angle - math.pi / 2) * spd
            ny += math.sin(self.angle - math.pi / 2) * spd
        if keys[pygame.K_d]:
            nx += math.cos(self.angle + math.pi / 2) * spd
            ny += math.sin(self.angle + math.pi / 2) * spd
        margin = 0.3
        if not map_at(nx, self.py): self.px = nx
        if not map_at(self.px, ny): self.py = ny

        moving = any([keys[pygame.K_w], keys[pygame.K_s],
                      keys[pygame.K_a], keys[pygame.K_d]])
        self.weapon_bob += 0.12 if moving else -0.05 * self.weapon_bob
        self.weapon_fire  = max(0.0, self.weapon_fire - 0.1)
        self.muzzle_flash = max(0,   self.muzzle_flash - 1)

    # ─────────────────────────────────────────
    #  ENEMIES
    # ─────────────────────────────────────────
    def update_enemies(self):
        for e in self.enemies:
            dx = self.px - e["x"]
            dy = self.py - e["y"]
            d  = math.hypot(dx, dy)
            if d > 0.55:
                nx = e["x"] + dx / d * e["speed"]
                ny = e["y"] + dy / d * e["speed"]
                if not map_at(nx, e["y"]): e["x"] = nx
                if not map_at(e["x"], ny): e["y"] = ny
            else:
                e["atk_timer"] -= 1
                if e["atk_timer"] <= 0:
                    self.take_damage(10)
                    e["atk_timer"] = e["atk_cd"]

    def take_damage(self, amount):
        if not self.alive: return
        self.hp = max(0, self.hp - amount)
        self.hit_flash = 8
        if self.hp <= 0:
            self.alive = False
            self.state = "end"

    # ─────────────────────────────────────────
    #  RENDER — 3-D scene
    # ─────────────────────────────────────────
    def render_scene(self):
        s = self.surf3d
        sw, sh = s.get_size()

        # ceiling
        pygame.draw.rect(s, (5, 8, 15), (0, 0, sw, sh // 2))
        # floor
        pygame.draw.rect(s, (8, 15, 22), (0, sh // 2, sw, sh // 2))

        # walls
        for col in range(NUM_RAYS):
            ray_angle = self.angle - HALF_FOV + (col / NUM_RAYS) * FOV
            raw_d     = cast_ray(self.px, self.py, ray_angle)
            # fish-eye correction
            corrected = raw_d * math.cos(ray_angle - self.angle)
            corrected = max(0.01, corrected)
            self.z_buf[col] = corrected

            wall_h = min(sh, int(sh / corrected))
            top    = (sh - wall_h) // 2
            bright = clamp(1 - corrected / MAX_DEPTH, 0, 1)
            c = lerp_color((0, 18, 25), (0, 200, 170), bright)
            pygame.draw.rect(s, c, (col, top, 1, wall_h))

        # sprites — enemies
        sprites = []
        for e in self.enemies:
            dx  = e["x"] - self.px
            dy  = e["y"] - self.py
            d   = math.hypot(dx, dy)
            ang = math.atan2(dy, dx) - self.angle
            while ang >  math.pi: ang -= math.pi * 2
            while ang < -math.pi: ang += math.pi * 2
            sprites.append((d, ang, e))

        sprites.sort(key=lambda x: -x[0])
        for d, ang, e in sprites:
            if abs(ang) > FOV * 0.6: continue
            sx     = int(sw * (0.5 + ang / FOV))
            height = min(sh, int(sh / max(0.1, d) * e["size"] * 1.4))
            width  = max(2, int(height * 0.55))
            top    = (sh - height) // 2
            # occlusion check (centre column of sprite vs z-buffer)
            ray_col = clamp(int(sx / WALL_STRIP), 0, NUM_RAYS - 1)
            if self.z_buf[ray_col] < d:
                continue
            bright = clamp(1 - d / 10, 0.1, 1.0)
            col    = tuple(int(c * bright) for c in e["color"])
            # body
            body_r = pygame.Rect(sx - width // 2, top, width, height)
            pygame.draw.rect(s, col, body_r, border_radius=4)
            # head
            hr = max(4, width // 3)
            pygame.draw.circle(s, col, (sx, top - hr // 2), hr)
            # hp bar
            max_hp = e["max_hp"]
            bar_w  = width
            bar_h  = 4
            bar_x  = sx - bar_w // 2
            bar_y  = top - 12
            pygame.draw.rect(s, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
            hp_fill = int(bar_w * e["hp"] / max_hp)
            hp_col  = NEON if e["hp"] == max_hp else RED
            pygame.draw.rect(s, hp_fill_c(e["hp"], max_hp), (bar_x, bar_y, hp_fill, bar_h))

        # particles (projected into 3D view)
        for p in self.particles:
            dx  = p["x"] - self.px
            dy  = p["y"] - self.py
            d   = math.hypot(dx, dy)
            ang = math.atan2(dy, dx) - self.angle
            while ang >  math.pi: ang -= math.pi * 2
            while ang < -math.pi: ang += math.pi * 2
            if abs(ang) > FOV: continue
            sx = int(sw * (0.5 + ang / FOV))
            sy = sh // 2
            sz = p["size"]
            alpha_col = tuple(int(c * p["life"]) for c in p["color"])
            pygame.draw.rect(s, alpha_col, (sx - sz // 2, sy - sz // 2, sz, sz))

        # blit scaled to full width
        pygame.transform.scale(s, (W, H), self.screen)

    # ─────────────────────────────────────────
    #  WEAPON MODEL
    # ─────────────────────────────────────────
    def draw_weapon(self):
        bob    = math.sin(self.weapon_bob) * 8
        recoil = self.weapon_fire * 28
        bx     = W // 2 + 170
        by     = H - 160 + int(bob) + int(recoil)

        # barrel
        pygame.draw.rect(self.screen, (20, 38, 50),  (bx - 10, by - 80, 20, 90))
        pygame.draw.rect(self.screen, (10, 25, 35),  (bx - 15, by,      30, 50))
        # neon trim
        pygame.draw.rect(self.screen, NEON,          (bx - 18, by + 8,  5,  30))
        # muzzle flash
        if self.muzzle_flash > 0:
            pygame.draw.circle(self.screen, (255, 255, 180), (bx, by - 80), 14)
            pygame.draw.circle(self.screen, WHITE,            (bx, by - 80),  7)

    # ─────────────────────────────────────────
    #  HUD
    # ─────────────────────────────────────────
    def draw_hud(self):
        # crosshair
        cx, cy = W // 2, H // 2
        for dx, dy in [(-18,0),(18,0),(0,-18),(0,18)]:
            pygame.draw.line(self.screen, NEON, (cx+dx, cy+dy),
                             (cx + dx//2, cy + dy//2), 2)
        pygame.draw.circle(self.screen, NEON, (cx, cy), 2)

        # hit flash
        if self.hit_flash > 0:
            flash = pygame.Surface((W, H), pygame.SRCALPHA)
            flash.fill((255, 34, 68, int(80 * self.hit_flash / 8)))
            self.screen.blit(flash, (0, 0))
            self.hit_flash -= 1

        # health bar
        bar_w = 220
        pygame.draw.rect(self.screen, GREY,  (24, 24, bar_w, 10), border_radius=3)
        hp_w  = int(bar_w * self.hp / self.max_hp)
        hp_c  = NEON if self.hp > 40 else RED
        pygame.draw.rect(self.screen, hp_c,  (24, 24, hp_w,  10), border_radius=3)
        self.blit_text(self.font_hud, f"HP  {self.hp}", (24, 38), NEON)

        # ammo pips
        pip_x = 24
        for i in range(self.max_ammo):
            c = NEON if i < self.ammo else GREY
            pygame.draw.rect(self.screen, c, (pip_x + i * 14, 62, 8, 18), border_radius=2)
        if self.reloading:
            self.blit_text(self.font_sm, "[ RELOADING ]", (24, 84), RED)

        # wave / score (top-right)
        self.blit_text(self.font_hud, f"WAVE   {self.wave}/{MAX_WAVES}", (W - 240, 24), NEON)
        self.blit_text(self.font_hud, f"SCORE  {self.score:,}",          (W - 240, 48), NEON)
        self.blit_text(self.font_sm,  f"KILLS  {self.total_kills}",      (W - 240, 72), NEON_DIM)

        # killfeed
        now = pygame.time.get_ticks()
        self.killfeed = [(t, e) for t, e in self.killfeed if e > now]
        for i, (text, _) in enumerate(self.killfeed[-5:]):
            self.blit_text(self.font_sm, text, (W - 260, 110 + i * 22), NEON)

        # wave announce
        if pygame.time.get_ticks() < self.wave_msg_t:
            self.blit_text_center(self.font_med, self.wave_msg, H // 3, NEON)

        # minimap
        self.draw_minimap()

    def draw_minimap(self):
        ms  = 120
        ts  = ms / MAP_W
        mx  = W - ms - 16
        my  = H - ms - 16
        mm  = pygame.Surface((ms, ms), pygame.SRCALPHA)
        mm.fill((5, 10, 15, 170))
        for gy in range(MAP_H):
            for gx in range(MAP_W):
                if MAP[gy * MAP_W + gx]:
                    pygame.draw.rect(mm, (0, 90, 80, 200),
                                     (gx * ts, gy * ts, ts - 1, ts - 1))
        for e in self.enemies:
            pygame.draw.rect(mm, e["color"],
                             (e["x"] * ts - 2, e["y"] * ts - 2, 4, 4))
        px_m = int(self.px * ts)
        py_m = int(self.py * ts)
        pygame.draw.rect(mm, NEON, (px_m - 3, py_m - 3, 6, 6))
        ex = int((self.px + math.cos(self.angle) * 2) * ts)
        ey = int((self.py + math.sin(self.angle) * 2) * ts)
        pygame.draw.line(mm, NEON, (px_m, py_m), (ex, ey), 1)
        self.screen.blit(mm, (mx, my))
        pygame.draw.rect(self.screen, NEON_DIM, (mx, my, ms, ms), 1)

    # ─────────────────────────────────────────
    #  SCREENS
    # ─────────────────────────────────────────
    def draw_start_screen(self):
        self.screen.fill(DARK)
        self._draw_grid()
        self.blit_text_center(self.font_big, "VOID RUNNER", H // 2 - 160, NEON)
        self.blit_text_center(self.font_sm,
                              "F I R S T   P E R S O N   S H O O T E R", H // 2 - 70, NEON_DIM)
        self._draw_divider(H // 2 - 40)
        self.blit_text_center(self.font_med, "[ PRESS SPACE TO DEPLOY ]", H // 2 - 10, NEON)

        controls = [
            ("MOVE",   "W A S D / ARROWS"),
            ("LOOK",   "MOUSE"),
            ("SHOOT",  "LEFT CLICK"),
            ("RELOAD", "R"),
            ("SPRINT", "SHIFT"),
            ("QUIT",   "ESC"),
        ]
        col_x = [W // 2 - 220, W // 2 + 20]
        for i, (k, v) in enumerate(controls):
            cx = col_x[i % 2]
            cy = H // 2 + 80 + (i // 2) * 32
            self.blit_text(self.font_sm, k, (cx, cy), NEON_DIM)
            self.blit_text(self.font_sm, v, (cx + 100, cy), NEON)

    def draw_end_screen(self):
        self.screen.fill(DARK)
        self._draw_grid()
        elapsed = int(time.time() - self.start_time)
        won = self.wave > MAX_WAVES

        if won:
            title_col = NEON
            title     = "V I C T O R Y"
            sub       = f"All {MAX_WAVES} waves cleared"
        else:
            title_col = RED
            title     = "Y O U   D I E D"
            sub       = f"Eliminated on Wave {self.wave}"

        self.blit_text_center(self.font_big, title, H // 2 - 180, title_col)
        self.blit_text_center(self.font_sm,  sub,   H // 2 - 90,  (180, 180, 180))
        self._draw_divider(H // 2 - 60)

        stats = [
            ("FINAL SCORE", f"{self.score:,}"),
            ("KILLS",       str(self.total_kills)),
            ("WAVE REACHED",str(self.wave)),
            ("TIME",        f"{elapsed}s"),
        ]
        for i, (k, v) in enumerate(stats):
            y = H // 2 - 30 + i * 36
            self.blit_text(self.font_sm, k, (W // 2 - 200, y), NEON_DIM)
            self.blit_text(self.font_sm, v, (W // 2 + 80,  y), NEON)

        self._draw_divider(H // 2 + 120)
        self.blit_text_center(self.font_med, "[ SPACE ] REDEPLOY   [ ESC ] QUIT",
                              H // 2 + 140, NEON)

    def _draw_grid(self):
        grid_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        for gx in range(0, W, 40):
            pygame.draw.line(grid_surf, (0, 255, 231, 15), (gx, 0), (gx, H))
        for gy in range(0, H, 40):
            pygame.draw.line(grid_surf, (0, 255, 231, 15), (0, gy), (W, gy))
        self.screen.blit(grid_surf, (0, 0))

    def _draw_divider(self, y):
        for i in range(W):
            t   = i / W
            alpha = int(255 * math.sin(t * math.pi))
            pygame.draw.line(self.screen, tuple(int(c * alpha / 255) for c in NEON),
                             (i, y), (i, y + 1))

    # ─────────────────────────────────────────
    #  TEXT HELPERS
    # ─────────────────────────────────────────
    def blit_text(self, font, text, pos, color):
        surf = font.render(text, True, color)
        self.screen.blit(surf, pos)

    def blit_text_center(self, font, text, y, color):
        surf = font.render(text, True, color)
        x    = (W - surf.get_width()) // 2
        self.screen.blit(surf, (x, y))

    # ─────────────────────────────────────────
    #  MAIN LOOP
    # ─────────────────────────────────────────
    def new_game(self):
        self._init_player()
        self.enemies     = []
        self.particles   = []
        self.killfeed    = []
        self.wave_msg    = ""
        self.wave_msg_t  = 0
        self.hit_flash   = 0
        self.muzzle_flash= 0
        self.total_kills = 0
        self.start_time  = time.time()
        self.spawn_wave(1)
        self.state = "play"
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)

    def exit_to_menu(self):
        self.state = "end"
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS_CAP)

            # ── EVENTS ──
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "play":
                            self.exit_to_menu()
                        else:
                            self.running = False

                    if self.state in ("start", "end") and event.key == pygame.K_SPACE:
                        self.new_game()

                    if self.state == "play":
                        if event.key == pygame.K_r:
                            self.start_reload()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "play" and event.button == 1:
                        self.shoot()

                elif event.type == pygame.MOUSEMOTION:
                    if self.state == "play":
                        self.angle += event.rel[0] * ROT_SPEED

                # custom timers
                elif event.type == pygame.USEREVENT + 1:
                    self.next_wave()
                elif event.type == pygame.USEREVENT + 2:
                    self.start_reload()

            # ── UPDATE ──
            if self.state == "play":
                keys = pygame.key.get_pressed()
                self.update_player(keys)
                self.update_enemies()
                self.update_particles()

                # reload timer
                if self.reloading and pygame.time.get_ticks() >= self.reload_timer:
                    self.ammo      = self.max_ammo
                    self.reloading = False

            # ── DRAW ──
            if self.state == "start":
                self.draw_start_screen()

            elif self.state == "play":
                self.render_scene()
                self.draw_weapon()
                self.draw_hud()

            elif self.state == "end":
                self.draw_end_screen()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ─────────────────────────────────────────────
def hp_fill_c(hp, max_hp):
    t = hp / max_hp
    return lerp_color(RED, NEON, t)

def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)

def map_at(x, y):
    xi, yi = int(x), int(y)
    if xi < 0 or xi >= MAP_W or yi < 0 or yi >= MAP_H:
        return 1
    return MAP[yi * MAP_W + xi]

def cast_ray(px, py, angle):
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    x, y  = px, py
    for _ in range(int(MAX_DEPTH / 0.05)):
        x += cos_a * 0.05
        y += sin_a * 0.05
        if map_at(x, y):
            return math.hypot(x - px, y - py)
    return MAX_DEPTH

# ─────────────────────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()
