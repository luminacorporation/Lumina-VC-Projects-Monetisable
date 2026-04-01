import pygame as pg
import math 
import numpy as np

WIDTH, HEIGHT = 1500, 900
bg_color = (255, 255, 255)
FPS = 120
g = 9.81
vi = float(input("Enter the initial velocity (m/s): "))
ang = float(input("Enter the angle of projection (degrees): "))
angle = float(math.radians(ang))

ball_radius = 10
ball_color = (255, 0, 0)
ball_x = 0
ball_y = HEIGHT // 2
ball_vx = vi * math.cos(angle)  # Horizontal velocity component
ball_vy = -vi * math.sin(angle)  # Vertical velocity component

screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Projectile Motion Simulation")
clock = pg.time.Clock()

time = 0  # Time in seconds
running = True
while running:
    clock.tick(FPS)
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    # Update position using physics equations
    time += 1 / FPS
    ball_x = ball_vx * time
    ball_y = HEIGHT // 2 + (ball_vy * time + 0.5 * g * time**2)

    screen.fill(bg_color)
    pg.draw.circle(screen, ball_color, (int(ball_x), int(ball_y)), ball_radius, vi, angle)
    pg.display.flip()

    # Stop if the ball goes out of screen
    if ball_y > HEIGHT or ball_x > WIDTH:
        running = False

pg.quit()
