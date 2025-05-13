import pygame
from config import COLORS, CELL_SIZE

class Grid:
    def __init__(self):
        #Initialize the Tetris game grid with dimensions, cells, and animation parameters
        #Main grid parameters
        self.rows = 20
        self.cols = 10
        self.cell_size = CELL_SIZE
        
        #Game window matrix
        self.cells = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        
        #Parameters for animation
        self.flashing_lines = []
        self.flash_start_time = 0
        self.flash_duration = 500
        
        #Cached grid lines surface
        self.grid_lines_surface = pygame.Surface((self.cols * self.cell_size, self.rows * self.cell_size))
        self.grid_lines_surface.fill(COLORS["background"])
        self.draw_grid_lines_to_surface()

    def is_valid_position(self, tetromino, offset_x, offset_y):
        #Check if a tetromino can be placed at the specified position
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x = offset_x + x
                    grid_y = offset_y + y
                    #Check boundaries and collisions
                    if grid_x < 0 or grid_x >= self.cols or grid_y >= self.rows:
                        return False
                    if grid_y >= 0 and self.cells[grid_y][grid_x] != 0:
                        return False
        return True

    def clear_lines(self):
        #Clear completed lines, initiate flashing animation, and return the number of lines cleared
        lines_to_clear = [idx for idx, row in enumerate(self.cells) if all(cell != 0 for cell in row)]
        
        if lines_to_clear:
            #Set up flashing animation
            self.flashing_lines = lines_to_clear
            self.flash_start_time = pygame.time.get_ticks()
            
            #Delete from bottom to top
            for idx in reversed(lines_to_clear):
                del self.cells[idx]
            
            #Add empty lines above
            for _ in range(len(lines_to_clear)):
                self.cells.insert(0, [0] * self.cols)
        
        return len(lines_to_clear)

    def get_ghost_position(self, tetromino):
        #Calculate the position where the tetromino would land if hard-dropped
        x, y = tetromino.x, tetromino.y
        while self.is_valid_position(tetromino, x, y + 1):
            y += 1
        return x, y

    def draw(self, screen, ghost_tetromino=None):
        #Draw the grid, cells, flashing animations, and optional ghost tetromino
        #Draw cached grid lines
        screen.blit(self.grid_lines_surface, (0, 0))
        
        #Draw cells
        for y in range(self.rows):
            for x in range(self.cols):
                if self.cells[y][x] != 0:
                    self.draw_cell(screen, x, y, self.cells[y][x])
        
        #Draw ghost tetromino if provided
        if ghost_tetromino:
            ghost_x, ghost_y = self.get_ghost_position(ghost_tetromino)
            self.draw_ghost_tetromino(screen, ghost_tetromino, ghost_x, ghost_y)
        
        #Draw flashing animation
        if self.flashing_lines:
            self.draw_flashing_effect(screen)

    def draw_grid_lines_to_surface(self):
        #Draw grid lines onto the cached grid_lines_surface
        line_color = COLORS["grid_line"]
        
        #Vertical lines
        for x in range(self.cols + 1):
            start_pos = (x * self.cell_size, 0)
            end_pos = (x * self.cell_size, self.rows * self.cell_size)
            pygame.draw.line(self.grid_lines_surface, line_color, start_pos, end_pos)
        
        #Horizontal lines
        for y in range(self.rows + 1):
            start_pos = (0, y * self.cell_size)
            end_pos = (self.cols * self.cell_size, y * self.cell_size)
            pygame.draw.line(self.grid_lines_surface, line_color, start_pos, end_pos)

    def draw_cell(self, screen, x, y, color):
        #Draw a single cell with the specified color and border effects
        rect = pygame.Rect(
            x * self.cell_size,
            y * self.cell_size,
            self.cell_size - 1,
            self.cell_size - 1
        )
        
        #Main color
        pygame.draw.rect(screen, color, rect)
        
        #Border effects for volume
        border_color = tuple(min(255, c + 40) for c in color)
        pygame.draw.rect(screen, border_color, rect, 2)

    def draw_ghost_tetromino(self, screen, tetromino, offset_x, offset_y):
        #Draw a semi-transparent ghost tetromino at the specified position
        ghost_color = tuple(c // 2 for c in tetromino.color)  #Darker, semi-transparent effect
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_cell(screen, offset_x + x, offset_y + y, ghost_color)

    def draw_flashing_effect(self, screen):
        #Draw the flashing effect for cleared lines and clear animation when complete
        current_time = pygame.time.get_ticks()
        flash_progress = (current_time - self.flash_start_time) / self.flash_duration
        
        if flash_progress >= 1:
            self.flashing_lines = []
            return
        
        #Transparency of the flash
        alpha = int((1 - abs(flash_progress - 0.5) * 2) * 255)
        overlay = pygame.Surface((self.cols * self.cell_size, self.rows * self.cell_size))
        overlay.set_alpha(alpha)
        
        for y in self.flashing_lines:
            for x in range(self.cols):
                rect = pygame.Rect(
                    x * self.cell_size,
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                pygame.draw.rect(overlay, (255, 255, 255), rect)
        
        screen.blit(overlay, (0, 0))

    def reset(self):
        #Reset the grid to its initial state, clearing all cells and animations
        self.cells = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.flashing_lines = []
