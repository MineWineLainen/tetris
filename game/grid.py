import pygame
from config import THEMES, CELL_SIZE, FADE_DURATION

class Grid:
    def __init__(self):
        #Initialize game grid
        self.rows = 20
        self.cols = 10
        self.cell_size = CELL_SIZE
        self.cells = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.cleared_lines = []
        self.clear_start_time = 0
        self.grid_lines_surface = pygame.Surface((self.cols * self.cell_size, self.rows * self.cell_size), pygame.SRCALPHA)
        self.current_theme = "Classic"
        self.update_theme()

    def update_theme(self):
        #Update grid lines with current theme
        self.grid_lines_surface.fill((0, 0, 0, 0))
        self.draw_grid_lines_to_surface()

    def is_valid_position(self, tetromino, offset_x, offset_y):
        #Check if tetromino can be placed
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x = offset_x + x
                    grid_y = offset_y + y
                    if grid_x < 0 or grid_x >= self.cols or grid_y >= self.rows:
                        return False
                    if grid_y >= 0 and self.cells[grid_y][grid_x] != 0:
                        return False
        return True

    def clear_lines(self):
        #Clear completed lines
        lines_to_clear = [idx for idx, row in enumerate(self.cells) if all(cell != 0 for cell in row)]
        if lines_to_clear:
            self.cleared_lines = [(idx, self.cells[idx][:]) for idx in lines_to_clear]
            self.clear_start_time = pygame.time.get_ticks()
            for idx in reversed(lines_to_clear):
                del self.cells[idx]
            for _ in range(len(lines_to_clear)):
                self.cells.insert(0, [0] * self.cols)
        return len(lines_to_clear)

    def get_ghost_position(self, tetromino):
        #Calculate ghost tetromino position
        x, y = tetromino.x, tetromino.y
        while self.is_valid_position(tetromino, x, y + 1):
            y += 1
        return x, y

    def draw(self, screen, ghost_tetromino=None):
        #Draw grid
        rects = []
        screen.blit(self.grid_lines_surface, (0, 0))
        for y in range(self.rows):
            for x in range(self.cols):
                if self.cells[y][x] != 0:
                    rect = self.draw_cell(screen, x, y, self.cells[y][x], THEMES[self.current_theme]["cell_alpha"])
                    if isinstance(rect, pygame.Rect):
                        rects.append(rect)
        if ghost_tetromino:
            ghost_x, ghost_y = self.get_ghost_position(ghost_tetromino)
            rect = self.draw_ghost_tetromino(screen, ghost_tetromino, ghost_x, ghost_y)
            if isinstance(rect, pygame.Rect):
                rects.append(rect)
        if self.cleared_lines:
            rect = self.draw_fade_effect(screen)
            if isinstance(rect, pygame.Rect):
                rects.append(rect)
        return pygame.Rect.unionall(pygame.Rect(0, 0, 0, 0), rects) if rects else pygame.Rect(0, 0, 0, 0)

    def draw_grid_lines_to_surface(self):
        #Draw grid lines
        line_color = THEMES[self.current_theme]["grid_line"]
        for x in range(self.cols + 1):
            start_pos = (x * self.cell_size, 0)
            end_pos = (x * self.cell_size, self.rows * self.cell_size)
            pygame.draw.line(self.grid_lines_surface, line_color, start_pos, end_pos)
        for y in range(self.rows + 1):
            start_pos = (0, y * self.cell_size)
            end_pos = (self.cols * self.cell_size, y * self.cell_size)
            pygame.draw.line(self.grid_lines_surface, line_color, start_pos, end_pos)

    def draw_cell(self, screen, x, y, color, alpha=255):
        #Draw a cell
        cell_surface = pygame.Surface((self.cell_size - 1, self.cell_size - 1), pygame.SRCALPHA)
        cell_surface.set_alpha(alpha)
        cell_surface.fill((*color, alpha))

        border_color = tuple(min(255, c + 40) for c in color)
        pygame.draw.rect(cell_surface, (*border_color, alpha), (0, 0, self.cell_size - 1, self.cell_size - 1), 2)
        rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size - 1, self.cell_size - 1)
        screen.blit(cell_surface, rect)
        return rect

    def draw_ghost_tetromino(self, screen, tetromino, offset_x, offset_y):
        #Draw ghost tetromino
        rects = []
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    rect = self.draw_cell(screen, offset_x + x, offset_y + y, tetromino.color, THEMES[self.current_theme]["ghost_alpha"])
                    if isinstance(rect, pygame.Rect):
                        rects.append(rect)
        return pygame.Rect.unionall(pygame.Rect(0, 0, 0, 0), rects) if rects else pygame.Rect(0, 0, 0, 0)

    def draw_fade_effect(self, screen):
        #Draw fade effect for cleared lines
        current_time = pygame.time.get_ticks()
        fade_progress = (current_time - self.clear_start_time) / FADE_DURATION
        if fade_progress >= 1:
            self.cleared_lines = []
            return pygame.Rect(0, 0, 0, 0)
        alpha = int((1 - fade_progress) * 255)
        rects = []
        for y, colors in self.cleared_lines:
            for x, color in enumerate(colors):
                if color != 0:
                    rect = self.draw_cell(screen, x, y, color, alpha)
                    if isinstance(rect, pygame.Rect):
                        rects.append(rect)
        return pygame.Rect.unionall(pygame.Rect(0, 0, 0, 0), rects) if rects else pygame.Rect(0, 0, 0, 0)

    def reset(self):
        #Reset grid
        self.cells = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.cleared_lines = []