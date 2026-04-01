import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 400
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GROUND = HEIGHT - 60
PLAYER_SIZE = 40
GRAVITY = 1
JUMP_VELOCITY = -15
OBSTACLE_WIDTH = 30
OBSTACLE_HEIGHT = 50
FPS = 60

# Setup display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Geometry Dash Clone")
clock = pygame.time.Clock()

# Player class
class Player:
    def __init__(self):
        self.rect = pygame.Rect(100, GROUND - PLAYER_SIZE, PLAYER_SIZE, PLAYER_SIZE)
        self.velocity_y = 0
        self.on_ground = True

    def jump(self):
        if self.on_ground:
            self.velocity_y = JUMP_VELOCITY
            self.on_ground = False

    def update(self):
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y
        if self.rect.bottom >= GROUND:
            self.rect.bottom = GROUND
            self.velocity_y = 0
            self.on_ground = True

    def draw(self):
        pygame.draw.rect(screen, (0, 200, 255), self.rect)

# Obstacle class
class Obstacle:
    def __init__(self, x):
        self.rect = pygame.Rect(x, GROUND - OBSTACLE_HEIGHT, OBSTACLE_WIDTH, OBSTACLE_HEIGHT)

    def update(self):
        self.rect.x -= 6

    def draw(self):
        pygame.draw.rect(screen, (255, 0, 0), self.rect)

# Main function
def main():
    player = Player()
    obstacles = []
    spawn_timer = 0
    score = 0
    font = pygame.font.SysFont(None, 36)

    while True:
        screen.fill(WHITE)
        pygame.draw.line(screen, BLACK, (0, GROUND), (WIDTH, GROUND), 3)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.jump()

        # Update player
        player.update()

        # Obstacle spawning
        spawn_timer += 1
        if spawn_timer > 90:
            spawn_timer = 0
            obstacles.append(Obstacle(WIDTH + random.randint(0, 100)))

        # Update obstacles
        for obs in list(obstacles):
            obs.update()
            if obs.rect.right < 0:
                obstacles.remove(obs)
                score += 1
            if player.rect.colliderect(obs.rect):
                print("Game Over!")
                pygame.quit()
                sys.exit()

        # Draw everything
        player.draw()
        for obs in obstacles:
            obs.draw()

        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

# Run the game
if __name__ == "__main__":
    main()
