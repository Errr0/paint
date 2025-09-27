import pygame

pygame.init()

# rozmiar "logicznego" canvasu (np. 64x64 piksele)
GRID_SIZE = 64
PIXEL_SIZE = 12  # jak bardzo powiększamy jeden piksel

WIDTH, HEIGHT = GRID_SIZE * PIXEL_SIZE, GRID_SIZE * PIXEL_SIZE + 60
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pixel Paint")

# paleta kolorów (RGB)
PALETTE = [
    (0, 0, 0),       # czarny
    (255, 255, 255), # biały
    (255, 0, 0),     # czerwony
    (0, 255, 0),     # zielony
    (0, 0, 255),     # niebieski
    (255, 0, 255),   # różowy
    (0, 255, 255),   # cyjan
    (255, 255, 0),   # żółty
]

current_color = PALETTE[0]  # startowy kolor

# tablica canvasu
canvas = [[(255, 255, 255) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]


def draw_canvas():
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            rect = (x * PIXEL_SIZE, y * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE)
            pygame.draw.rect(WIN, canvas[y][x], rect)


def draw_palette():
    for i, color in enumerate(PALETTE):
        rect = (i * 50 + 10, HEIGHT - 50, 40, 40)
        pygame.draw.rect(WIN, color, rect)
        pygame.draw.rect(WIN, (0, 0, 0), rect, 2)  # obramowanie


def get_palette_click(pos):
    x, y = pos
    if y >= HEIGHT - 50:
        for i in range(len(PALETTE)):
            rect = pygame.Rect(i * 50 + 10, HEIGHT - 50, 40, 40)
            if rect.collidepoint(x, y):
                return PALETTE[i]
    return None


def main():
    global current_color
    run = True
    clock = pygame.time.Clock()

    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if pygame.mouse.get_pressed()[0]:  # lewy przycisk myszy
                mx, my = pygame.mouse.get_pos()
                if my < GRID_SIZE * PIXEL_SIZE:  # klik na canvasie
                    gx, gy = mx // PIXEL_SIZE, my // PIXEL_SIZE
                    if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                        canvas[gy][gx] = current_color
                else:  # klik na palecie
                    color = get_palette_click((mx, my))
                    if color:
                        current_color = color

        WIN.fill((200, 200, 200))
        draw_canvas()
        draw_palette()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
