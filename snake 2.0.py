import pygame
import time
import random

# Initialize pygame
pygame.init()

# Screen size
width = 600
height = 400
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Snake Game')

# Colors
black = (0, 0, 0)
green = (0, 255, 0)
red = (213, 50, 80)
blue = (50, 153, 213)
white = (255, 255, 255)

# Clock and snake block size
clock = pygame.time.Clock()
snake_block = 10
snake_speed = 15

# Font
font = pygame.font.SysFont(None, 35)

def show_score(score):
    value = font.render(f"Score: {score}", True, white)
    screen.blit(value, [0, 0])

def draw_snake(snake_block, snake_list):
    for x in snake_list:
        pygame.draw.rect(screen, green, [x[0], x[1], snake_block, snake_block])

def game_loop():
    game_over = False
    game_close = False

    # Snake starting position
    x = width / 2
    y = height / 2
    dx = 0
    dy = 0

    snake_list = []
    length = 1

    # Food position
    foodx = round(random.randrange(0, width - snake_block) / 10.0) * 10.0
    foody = round(random.randrange(0, height - snake_block) / 10.0) * 10.0

    while not game_over:

        while game_close:
            screen.fill(black)
            msg = font.render("Game Over! Press Q-Quit or C-Play Again", True, red)
            screen.blit(msg, [width / 6, height / 3])
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        game_loop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    dx = -snake_block
                    dy = 0
                elif event.key == pygame.K_RIGHT:
                    dx = snake_block
                    dy = 0
                elif event.key == pygame.K_UP:
                    dy = -snake_block
                    dx = 0
                elif event.key == pygame.K_DOWN:
                    dy = snake_block
                    dx = 0

        # Move
        x += dx
        y += dy

        # Hit wall
        if x >= width or x < 0 or y >= height or y < 0:
            game_close = True

        screen.fill(blue)
        pygame.draw.rect(screen, red, [foodx, foody, snake_block, snake_block])

        head = []
        head.append(x)
        head.append(y)
        snake_list.append(head)

        if len(snake_list) > length:
            del snake_list[0]

        # Hit itself
        for segment in snake_list[:-1]:
            if segment == head:
                game_close = True

        draw_snake(snake_block, snake_list)
        show_score(length - 1)

        pygame.display.update()

        # Eat food
        if x == foodx and y == foody:
            foodx = round(random.randrange(0, width - snake_block) / 10.0) * 10.0
            foody = round(random.randrange(0, height - snake_block) / 10.0) * 10.0
            length += 1

        clock.tick(snake_speed)

    pygame.quit()
    quit()

game_loop()
