import pygame, sys
from pygame.locals import *
import random

pygame.init()

FPS = 60
FramePerSec = pygame.time.Clock()

# Colors
BLUE  = (0, 0, 255)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Screen
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 700

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Need for Speed")

font = pygame.font.SysFont("Verdana", 40)
small_font = pygame.font.SysFont("Verdana", 20)

# ----------- GAME STATES -----------
START = 0
PLAYING = 1
GAME_OVER = 2

game_state = START


# ----------- CLASSES -----------
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("download.png")
        self.image = pygame.transform.scale(self.image, (110, 110))
        self.rect = self.image.get_rect()
        self.reset()

    def reset(self):
        self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)

    def move(self):
        self.rect.move_ip(0, 10)
        if self.rect.bottom > SCREEN_HEIGHT:
            self.reset()

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        original = pygame.image.load("download (1).png")
        self.image = pygame.transform.scale(original, (100, 120))
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)
        self.speed = 10

    def update(self):
        pressed_keys = pygame.key.get_pressed()

        if pressed_keys[K_UP] and self.rect.top > 0:
            self.rect.move_ip(0, -self.speed)

        if pressed_keys[K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.move_ip(0, self.speed)

        if pressed_keys[K_LEFT] and self.rect.left > 0:
            self.rect.move_ip(-self.speed, 0)

        if pressed_keys[K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.move_ip(self.speed, 0)

    def draw(self, surface):
        surface.blit(self.image, self.rect)


# ----------- OBJECTS -----------
P1 = Player()
E1 = Enemy()


# ----------- FUNCTIONS -----------
def draw_text(text, font, color, surface, x, y):
    obj = font.render(text, True, color)
    rect = obj.get_rect(center=(x, y))
    surface.blit(obj, rect)


# ----------- GAME LOOP -----------
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        if event.type == KEYDOWN:
            if game_state == START:
                game_state = PLAYING

            elif game_state == GAME_OVER:
                # restart game
                game_state = START
                P1.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)
                E1.reset()

    DISPLAYSURF.fill(WHITE)

    # -------- START SCREEN --------
    if game_state == START:
        draw_text("Need for Speed", font, BLACK, DISPLAYSURF, 250, 250)
        draw_text("Press any key to start", small_font, BLACK, DISPLAYSURF, 250, 350)

    # -------- PLAYING --------
    elif game_state == PLAYING:
        P1.update()
        E1.move()

        P1.draw(DISPLAYSURF)
        E1.draw(DISPLAYSURF)

        # COLLISION DETECTION
        if P1.rect.colliderect(E1.rect):
            game_state = GAME_OVER

    # -------- GAME OVER --------
    elif game_state == GAME_OVER:
        draw_text("GAME OVER", font, RED, DISPLAYSURF, 250, 250)
        draw_text("Press any key to restart", small_font, BLACK, DISPLAYSURF, 250, 350)

    pygame.display.update()
    FramePerSec.tick(FPS)