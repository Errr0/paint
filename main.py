"""
pixel_painter.py
Prosty pixelowy edytor z Pygame.

Sterowanie:
- LPM (kliknięcie/drag) -> maluj wybranym kolorem
- PPM (kliknięcie/drag) -> kasuj (ustawia przezroczystą/ tło)
- F -> przełącz tryb kubełka (następne LPM wypełnia obszar)
- S -> zapisz do PNG (plik: pixel_art_TIMESTAMP.png)
- C -> wyczyść kanwę
- Z -> undo (cofnij ostatnią zmianę)
- Numery 1-6 -> wybór koloru z palety
- Kliknij na paletę (po prawej) by wybrać kolor
- ESC -> wyjście
"""

import pygame
import sys
import time
from collections import deque

pygame.init()
FONT = pygame.font.SysFont("Arial", 16)

# ---- Konfiguracja ----
PIXELS_X = 32  # liczba "pikseli" w poziomie
PIXELS_Y = 32  # liczba "pikseli" w pionie
PIXEL_SIZE = 20  # rozmiar pojedynczego piksela (w pikselach ekranu)
MARGIN = 10  # margines wokół kanwy
PALETTE_WIDTH = 160  # szerokość panelu z prawej
UNDO_LIMIT = 20

# kolory (RGBA) — ostatni kanał jako alfa (255 = pełny)
PALETTE = [
    (0, 0, 0, 255),       # black
    (255, 255, 255, 255), # white
    (255, 0, 0, 255),     # red
    (0, 255, 0, 255),     # green
    (0, 0, 255, 255),     # blue
    (255, 200, 0, 255),   # yellow/orange
    (180, 0, 180, 255),   # purple
    (255, 150, 200, 255), # pink
    (100, 100, 100, 255), # gray
]

BG_COLOR = (220, 220, 220)
GRID_COLOR = (180, 180, 180)
WINDOW_WIDTH = PIXELS_X * PIXEL_SIZE + MARGIN * 2 + PALETTE_WIDTH
WINDOW_HEIGHT = PIXELS_Y * PIXEL_SIZE + MARGIN * 2

# ---- Inicjalizacja okna ----
WIN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Pixel Painter")

# ---- Pomocnicze funkcje ----
def make_empty_canvas(cols, rows, default=(255,255,255,0)):
    """Zwraca tablicę kolorów RGBA (kol, row). 0 alfa = przezroczyste."""
    return [[default for _ in range(cols)] for _ in range(rows)]

def rgba_to_surface_color(rgba):
    """Konwertuje (r,g,b,a) -> (r,g,b) dla rysowania na surface; alpha traktujemy oddzielnie."""
    return (rgba[0], rgba[1], rgba[2])

# ---- Klasy ----
class Canvas:
    def __init__(self, cols, rows, pixel_size, pos=(MARGIN, MARGIN)):
        self.cols = cols
        self.rows = rows
        self.pixel_size = pixel_size
        self.x, self.y = pos
        self.grid = make_empty_canvas(cols, rows)
        self.surface = pygame.Surface((cols * pixel_size, rows * pixel_size), pygame.SRCALPHA)
        self.needs_redraw = True

    def in_bounds(self, mx, my):
        """Sprawdza czy podane współrzędne ekranu są wewnątrz kanwy."""
        gx = (mx - self.x) // self.pixel_size
        gy = (my - self.y) // self.pixel_size
        return 0 <= gx < self.cols and 0 <= gy < self.rows

    def mouse_to_cell(self, mx, my):
        gx = (mx - self.x) // self.pixel_size
        gy = (my - self.y) // self.pixel_size
        return int(gx), int(gy)

    def set_pixel(self, col, row, color):
        if 0 <= col < self.cols and 0 <= row < self.rows:
            self.grid[row][col] = color
            self.needs_redraw = True

    def get_pixel(self, col, row):
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return self.grid[row][col]
        return None

    def clear(self):
        self.grid = make_empty_canvas(self.cols, self.rows)
        self.needs_redraw = True

    def flood_fill(self, start_col, start_row, new_color):
        """Iteratywne wypełnianie (4-neighbors). Kolory są porównywane dokładnie."""
        if not (0 <= start_col < self.cols and 0 <= start_row < self.rows):
            return
        target = self.get_pixel(start_col, start_row)
        if target == new_color:
            return

        q = deque()
        q.append((start_col, start_row))
        while q:
            c, r = q.popleft()
            if not (0 <= c < self.cols and 0 <= r < self.rows):
                continue
            if self.get_pixel(c, r) != target:
                continue
            self.set_pixel(c, r, new_color)
            q.append((c+1, r))
            q.append((c-1, r))
            q.append((c, r+1))
            q.append((c, r-1))

    def draw(self, surface):
        """Rysuje kanwę i siatkę na podanym surface."""
        if self.needs_redraw:
            # przerysuj surface
            self.surface.fill((0,0,0,0))  # przezroczyste tło
            for r in range(self.rows):
                for c in range(self.cols):
                    col = self.grid[r][c]
                    # jeśli alpha == 0 to rysujemy przezroczystość (puste)
                    if col[3] != 0:
                        rect = pygame.Rect(c*self.pixel_size, r*self.pixel_size, self.pixel_size, self.pixel_size)
                        pygame.draw.rect(self.surface, rgba_to_surface_color(col), rect)
            # narysuj kratkę (opcjonalnie)
            for i in range(self.cols+1):
                x = i * self.pixel_size
                pygame.draw.line(self.surface, GRID_COLOR, (x,0), (x, self.rows*self.pixel_size))
            for j in range(self.rows+1):
                y = j * self.pixel_size
                pygame.draw.line(self.surface, GRID_COLOR, (0,y), (self.cols*self.pixel_size, y))
            self.needs_redraw = False

        # wklej surface na ekran
        surface.blit(self.surface, (self.x, self.y))

class Palette:
    def __init__(self, palette_colors, rect_x):
        self.colors = palette_colors
        self.rect_x = rect_x
        self.slot_size = 32
        self.padding = 8
        # prepare clickable rects
        self.slots = []
        self._compute_slots()

    def _compute_slots(self):
        self.slots.clear()
        x = self.rect_x + self.padding
        y = MARGIN + self.padding
        per_col = 2
        c = 0
        for color in self.colors:
            rx = x + (c % per_col) * (self.slot_size + self.padding)
            ry = y + (c // per_col) * (self.slot_size + self.padding)
            self.slots.append((pygame.Rect(rx, ry, self.slot_size, self.slot_size), color))
            c += 1

    def draw(self, surface, selected_color):
        # panel background
        panel_rect = pygame.Rect(self.rect_x, 0, PALETTE_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(surface, (240,240,240), panel_rect)
        # title
        txt = FONT.render("Paleta", True, (20,20,20))
        surface.blit(txt, (self.rect_x + 10, 6))

        for rect, color in self.slots:
            pygame.draw.rect(surface, rgba_to_surface_color(color), rect)
            # border if selected
            if color == selected_color:
                pygame.draw.rect(surface, (255,0,0), rect, 3)
            else:
                pygame.draw.rect(surface, (100,100,100), rect, 1)

    def pick(self, mx, my):
        for rect, color in self.slots:
            if rect.collidepoint(mx, my):
                return color
        return None

# ---- Główna pętla / logika ----
def main():
    clock = pygame.time.Clock()
    canvas = Canvas(PIXELS_X, PIXELS_Y, PIXEL_SIZE)
    palette = Palette(PALETTE, WINDOW_WIDTH - PALETTE_WIDTH)
    selected_color = PALETTE[2]  # domyślnie czerwony
    bucket_mode = False
    running = True
    painting = False
    erasing = False
    last_cell = None

    # undo stack: przechowujemy kopię gridy (waga: dla małych canvases ok)
    undo_stack = []

    def push_undo():
        # kopiuj aktualny stan
        if len(undo_stack) >= UNDO_LIMIT:
            undo_stack.pop(0)
        copy_grid = [row.copy() for row in canvas.grid]
        undo_stack.append(copy_grid)

    def do_undo():
        if not undo_stack:
            return
        last = undo_stack.pop()
        canvas.grid = [row.copy() for row in last]
        canvas.needs_redraw = True

    push_undo()  # initial state

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_s:  # save
                    filename = f"pixel_art_{int(time.time())}.png"
                    # render canvas to image surface then save
                    export = pygame.Surface((canvas.cols, canvas.rows), pygame.SRCALPHA)
                    for r in range(canvas.rows):
                        for c in range(canvas.cols):
                            col = canvas.get_pixel(c,r)
                            if col[3] != 0:
                                export.set_at((c,r), (col[0], col[1], col[2], col[3]))
                            else:
                                export.set_at((c,r), (0,0,0,0))
                    # scale up to original pixel size for nicer PNG (optional)
                    scaled = pygame.transform.scale(export, (canvas.cols * canvas.pixel_size, canvas.rows * canvas.pixel_size))
                    pygame.image.save(scaled, filename)
                    print("Saved:", filename)
                elif event.key == pygame.K_c:  # clear
                    push_undo()
                    canvas.clear()
                elif event.key == pygame.K_z:  # undo
                    do_undo()
                elif event.key == pygame.K_f:  # toggle bucket mode
                    bucket_mode = not bucket_mode
                    print("Bucket mode:", bucket_mode)
                elif event.unicode in "123456":
                    idx = int(event.unicode) - 1
                    if idx < len(PALETTE):
                        selected_color = PALETTE[idx]

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # klik na paletę?
                picked = palette.pick(mx, my)
                if picked:
                    selected_color = picked
                    bucket_mode = False
                    continue

                if canvas.in_bounds(mx, my):
                    col, row = canvas.mouse_to_cell(mx, my)
                    if event.button == 1:  # left
                        if bucket_mode:
                            push_undo()
                            canvas.flood_fill(col, row, selected_color)
                        else:
                            push_undo()
                            painting = True
                            last_cell = (col, row)
                            canvas.set_pixel(col, row, selected_color)
                    elif event.button == 3:  # right
                        push_undo()
                        erasing = True
                        last_cell = (col,row)
                        # set transparent (alpha=0)
                        canvas.set_pixel(col, row, (0,0,0,0))

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    painting = False
                    last_cell = None
                elif event.button == 3:
                    erasing = False
                    last_cell = None

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if painting and canvas.in_bounds(mx, my):
                    col, row = canvas.mouse_to_cell(mx, my)
                    if last_cell != (col, row):
                        canvas.set_pixel(col, row, selected_color)
                        last_cell = (col, row)
                if erasing and canvas.in_bounds(mx, my):
                    col, row = canvas.mouse_to_cell(mx, my)
                    if last_cell != (col, row):
                        canvas.set_pixel(col, row, (0,0,0,0))
                        last_cell = (col, row)

        # rysowanie UI
        WIN.fill(BG_COLOR)
        canvas.draw(WIN)
        palette.draw(WIN, selected_color)

        # Info / instrukcje
        info_lines = [
            f"Tool: {'Bucket' if bucket_mode else 'Pencil'}    Selected: #{PALETTE.index(selected_color)+1 if selected_color in PALETTE else '?'}",
            "LPM: draw    PPM: erase    F: bucket    S: save",
            "C: clear    Z: undo    1-6: quick palette"
        ]
        for i, line in enumerate(info_lines):
            txt = FONT.render(line, True, (20,20,20))
            WIN.blit(txt, (MARGIN, WINDOW_HEIGHT - 20 * (len(info_lines)-i) - 8))

        # podświetlenie komórki pod myszką
        mx, my = pygame.mouse.get_pos()
        if canvas.in_bounds(mx, my):
            c, r = canvas.mouse_to_cell(mx, my)
            rect = pygame.Rect(canvas.x + c*canvas.pixel_size, canvas.y + r*canvas.pixel_size,
                               canvas.pixel_size, canvas.pixel_size)
            pygame.draw.rect(WIN, (255,0,0), rect, 2)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
