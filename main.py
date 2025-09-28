import pygame
import sys

# Stałe ekranu
SCREEN_WIDTH = 540
SCREEN_HEIGHT = 960

# Inicjalizacja pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Podział ekranu - opcje sterowania")

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
RED = (255, 100, 100)
GREEN = (100, 255, 100)

# Pasek
BAR_WIDTH = 80
bar_on_left = True  # True = lewa strona, False = prawa

# Czerwona część
red_on_bottom = True  # True = dół, False = góra

# Proporcje 9:16
ASPECT_RATIO = 9 / 16

# Maksymalne FPS
MAX_FPS = 60
cap_fps = False

# Pętla główna
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_z:  # zmiana strony paska
                bar_on_left = not bar_on_left
            elif event.key == pygame.K_c:  # zmiana pozycji czerwonego
                red_on_bottom = not red_on_bottom

    # Tło
    screen.fill(WHITE)

    # --- NIEBIESKA CZĘŚĆ ---
    blue_width = SCREEN_WIDTH - BAR_WIDTH
    blue_height = int(blue_width / ASPECT_RATIO)

    # Pasek zielony
    if bar_on_left:
        bar_x = 0
        blue_x = BAR_WIDTH
    else:
        bar_x = SCREEN_WIDTH - BAR_WIDTH
        blue_x = 0

    pygame.draw.rect(screen, GREEN, (bar_x, 0, BAR_WIDTH, SCREEN_HEIGHT))
    pygame.draw.rect(screen, BLUE, (blue_x, 0, blue_width, blue_height))

    red_height = SCREEN_HEIGHT - blue_height
    if red_height > 0:
        if red_on_bottom:
            red_y = blue_height
        else:
            red_y = 0
            if bar_on_left:
                pygame.draw.rect(screen, BLUE, (BAR_WIDTH, red_height, blue_width, blue_height))
            else:
                pygame.draw.rect(screen, BLUE, (0, red_height, blue_width, blue_height))
        pygame.draw.rect(screen, RED, (0, red_y, SCREEN_WIDTH, red_height))

    # Aktualizacja ekranu
    pygame.display.flip()
    if cap_fps: clock.tick(MAX_FPS)

pygame.quit()
sys.exit()
