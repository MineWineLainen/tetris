import pygame
import logging
import os
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, SCORE_DATA, LINES_PER_LEVEL, LEVEL_SPEED_REDUCTION, COLORS, GRID_COLS, GRID_ROWS, CELL_SIZE, PATHS
from .tetromino import Tetromino, TetrominoBag
from .grid import Grid

#Configure logging
logging.basicConfig(
    filename="tetris.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class Game:
    def __init__(self):
        #Initialize Tetris with Pygame, game state, and resources
        #Pygame initialization
        try:
            pygame.init()
            pygame.font.init()
            pygame.mixer.init()
        except Exception as e:
            logging.error(f"Failed to initialize Pygame: {e}")
            raise

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.game_surface = pygame.Surface((GRID_COLS * CELL_SIZE, GRID_ROWS * CELL_SIZE))
        pygame.display.set_caption("Tetris")

        #Game state
        self.running = True
        self.game_over_flag = False
        self.in_menu = True
        self.final_score = 0
        self.high_score = self.load_high_score()

        #Time management
        self.clock = pygame.time.Clock()
        self.fall_time = 0
        self.fall_speed = 1000
        self.line_clear_delay = 0
        self.line_clear_delay_duration = 600

        #Game components
        self.grid = Grid()
        self.bag = TetrominoBag()

        #Level and score management
        self.score = 0
        self.level = 1
        self.lines_cleared = 0

        #Tetromino management
        self.current_tetromino = None
        self.next_tetromino = None
        self.held_tetromino = None
        self.can_hold = True

        #Input delay
        self.move_delay = 150
        self.last_move_time = 0

        #Sounds
        self.sounds = {}
        try:
            self.sounds = {
                "rotate": pygame.mixer.Sound(PATHS["sounds"]["rotate"]),
                "drop": pygame.mixer.Sound(PATHS["sounds"]["drop"]),
                "hard_drop": pygame.mixer.Sound(PATHS["sounds"]["hard_drop"]),
                "line_clear": pygame.mixer.Sound(PATHS["sounds"]["line_clear"]),
                "game_over": pygame.mixer.Sound(PATHS["sounds"]["game_over"])
            }
        except Exception as e:
            logging.error(f"Failed to load sounds: {e}")

        #Font
        try:
            self.font = pygame.font.Font(PATHS["fonts"]["main"], 18)
            self.menu_font = pygame.font.Font(PATHS["fonts"]["main"], 24)
        except Exception as e:
            logging.error(f"Failed to load font: {e}")
            self.font = pygame.font.SysFont("arial", 18)
            self.menu_font = pygame.font.SysFont("arial", 24)

        #Menu options
        self.difficulties = {
            "Easy": 1000,
            "Normal": 800,
            "Hard": 600
        }
        self.selected_difficulty = "Normal"

    def run(self):
        #Run the main game loop, handling menu, gameplay, and rendering
        while self.running:
            self.clock.tick(FPS)
            if self.in_menu:
                self.handle_menu_events()
                self.draw_menu()
            else:
                self.handle_events()
                if not self.game_over_flag and not self.in_menu:
                    self.update()
                self.draw()
        pygame.quit()

    def handle_menu_events(self):
        #Handle user inputs in the start menu
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    current_idx = list(self.difficulties.keys()).index(self.selected_difficulty)
                    self.selected_difficulty = list(self.difficulties.keys())[(current_idx - 1) % len(self.difficulties)]
                if event.key == pygame.K_DOWN:
                    current_idx = list(self.difficulties.keys()).index(self.selected_difficulty)
                    self.selected_difficulty = list(self.difficulties.keys())[(current_idx + 1) % len(self.difficulties)]
                if event.key == pygame.K_RETURN:
                    self.start_game()
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def handle_events(self):
        #Handle user inputs and game events during gameplay
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if self.game_over_flag:
                    if event.key == pygame.K_SPACE:
                        self.reset()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                else:
                    if event.key == pygame.K_UP:
                        self.rotate_tetromino(clockwise=True)
                    elif event.key == pygame.K_z:
                        self.rotate_tetromino(clockwise=False)
                    elif event.key == pygame.K_SPACE:
                        self.hard_drop()
                    elif event.key == pygame.K_c:
                        self.hold_tetromino()

        if not self.game_over_flag:
            current_time = pygame.time.get_ticks()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and current_time - self.last_move_time > self.move_delay:
                self.move_horizontal(-1)
                self.last_move_time = current_time
            if keys[pygame.K_RIGHT] and current_time - self.last_move_time > self.move_delay:
                self.move_horizontal(1)
                self.last_move_time = current_time
            if keys[pygame.K_DOWN] and current_time - self.last_move_time > 50:
                self.soft_drop()
                self.last_move_time = current_time

    def update(self):
        #Update game state, including tetromino falling and line clear delays
        current_time = pygame.time.get_ticks()

        #Handle line clear delay
        if self.line_clear_delay > 0:
            if current_time - self.line_clear_delay >= self.line_clear_delay_duration:
                self.line_clear_delay = 0
            return

        #Automatic falling
        if current_time - self.fall_time > self.fall_speed:
            if not self.move_vertical():
                self.fix_tetromino()
            self.fall_time = current_time

    def draw(self):
        #Render all game elements to the game surface and then to the screen
        self.game_surface.fill(COLORS["background"])
        if not self.game_over_flag:
            self.grid.draw(self.game_surface, self.current_tetromino)  #Draw grid with ghost piece
            self.draw_current_tetromino()
        self.screen.fill(COLORS["background"])
        self.screen.blit(self.game_surface, (20, 20))  #Offset game surface
        if not self.game_over_flag:
            self.draw_ui()
        else:
            self.draw_game_over()
        pygame.display.flip()

    def draw_menu(self):
        #Render the start menu with difficulty selection
        self.screen.fill(COLORS["background"])
        self.draw_text("Tetris", (SCREEN_WIDTH // 2, 100), 24, center=True)
        self.draw_text("Select Difficulty:", (SCREEN_WIDTH // 2, 200), center=True)
        for i, difficulty in enumerate(self.difficulties.keys()):
            color = (255, 255, 0) if difficulty == self.selected_difficulty else (255, 255, 255)
            self.draw_text(difficulty, (SCREEN_WIDTH // 2, 250 + i * 40), center=True, color=color)
        self.draw_text("Press ENTER to start, ESC to quit", (SCREEN_WIDTH // 2, 400), center=True)
        pygame.display.flip()

    def draw_ui(self):
        #Draw UI elements including score, level, next, and held tetrominos
        self.draw_text(f"Score: {self.score}", (320, 50))
        self.draw_text(f"High Score: {self.high_score}", (320, 80))
        self.draw_text(f"Level: {self.level}", (320, 110))
        self.draw_text("Next:", (320, 150))
        self.draw_next_tetromino(320, 180)
        self.draw_text("Hold:", (320, 300))
        if self.held_tetromino:
            self.draw_held_tetromino(320, 330)

    def draw_current_tetromino(self):
        #Draw the currently falling tetromino on the game surface
        for y, row in enumerate(self.current_tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    screen_x = (self.current_tetromino.x + x) * CELL_SIZE
                    screen_y = (self.current_tetromino.y + y) * CELL_SIZE
                    pygame.draw.rect(self.game_surface, self.current_tetromino.color,
                                     (screen_x, screen_y, CELL_SIZE - 2, CELL_SIZE - 2))

    def draw_next_tetromino(self, x, y):
        #Draw the next tetromino preview on the screen
        for dy, row in enumerate(self.next_tetromino.shape):
            for dx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, self.next_tetromino.color,
                                     (x + dx * 20, y + dy * 20, 18, 18))

    def draw_held_tetromino(self, x, y):
        #Draw the held tetromino preview on the screen
        for dy, row in enumerate(self.held_tetromino.shape):
            for dx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, self.held_tetromino.color,
                                     (x + dx * 20, y + dy * 20, 18, 18))

    def draw_game_over(self):
        #Display the game over screen with final score and high score
        self.draw_text("GAME OVER", (SCREEN_WIDTH // 2, 200), 24, center=True)
        self.draw_text(f"Final Score: {self.final_score}", (SCREEN_WIDTH // 2, 300), center=True)
        self.draw_text(f"High Score: {self.high_score}", (SCREEN_WIDTH // 2, 350), center=True)
        self.draw_text("Press SPACE to restart", (SCREEN_WIDTH // 2, 400), center=True)
        self.draw_text("or ESC to quit", (SCREEN_WIDTH // 2, 450), center=True)

    def draw_text(self, text, position, size=18, color=(255, 255, 255), center=False):
        #Render text on the screen at the specified position
        font = self.menu_font if size > 24 else self.font
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=position) if center else text_surface.get_rect(topleft=position)
        self.screen.blit(text_surface, text_rect)

    def start_game(self):
        #Start the game with the selected difficulty
        self.in_menu = False
        self.fall_speed = self.difficulties[self.selected_difficulty]
        self.current_tetromino = self.bag.get_next()
        self.next_tetromino = self.bag.get_next()
        self.held_tetromino = None
        self.can_hold = True

    def move_horizontal(self, direction):
        #Move the tetromino horizontally with collision check.
        new_x = self.current_tetromino.x + direction
        if self.grid.is_valid_position(self.current_tetromino, new_x, self.current_tetromino.y):
            self.current_tetromino.x = new_x

    def rotate_tetromino(self, clockwise=True):
        #Rotate the tetromino, applying wall kicks if needed.
        self.sounds["rotate"].play()
        success = (self.current_tetromino.rotate_clockwise(self.grid) if clockwise
                   else self.current_tetromino.rotate_counterclockwise(self.grid))
        if not success:
            self.sounds["rotate"].stop()  # Optional: stop sound if rotation fails

    def soft_drop(self):
        #Perform a soft drop, moving the tetromino down one cell
        if self.move_vertical():
            self.score += 1 * self.level
            self.fall_time = pygame.time.get_ticks()
            self.sounds["drop"].play()

    def hard_drop(self):
        #Perform a hard drop, instantly dropping the tetromino to the bottom
        self.sounds["hard_drop"].play()
        drop_distance = 0
        while self.move_vertical():
            drop_distance += 1
        self.score += 2 * drop_distance * self.level
        self.fix_tetromino()

    def hold_tetromino(self):
        #Swap the current tetromino with the held tetromino or hold it if none is held
        if not self.can_hold:
            return
        self.sounds["rotate"].play()
        if self.held_tetromino is None:
            self.held_tetromino = self.current_tetromino
            self.current_tetromino = self.bag.get_next()
        else:
            self.held_tetromino, self.current_tetromino = self.current_tetromino, self.held_tetromino
            self.current_tetromino.x = 3
            self.current_tetromino.y = 0
            self.current_tetromino.rotation = 0
            self.current_tetromino.shape = self.current_tetromino._get_shape_matrix(self.current_tetromino.shape_type)
        self.can_hold = False

    def move_vertical(self):
        #Move the tetromino down one cell
        new_y = self.current_tetromino.y + 1
        if self.grid.is_valid_position(self.current_tetromino, self.current_tetromino.x, new_y):
            self.current_tetromino.y = new_y
            return True
        return False

    def fix_tetromino(self):
        #Lock the tetromino in place and handle line clears and game over
        self.sounds["drop"].play()
        for y, row in enumerate(self.current_tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_y = self.current_tetromino.y + y
                    grid_x = self.current_tetromino.x + x
                    if grid_y < 0:
                        self.game_over()
                        return
                    self.grid.cells[grid_y][grid_x] = self.current_tetromino.color

        lines_cleared = self.grid.clear_lines()
        if lines_cleared > 0:
            self.update_score(lines_cleared)
            self.line_clear_delay = pygame.time.get_ticks()

        self.current_tetromino = self.next_tetromino
        self.next_tetromino = self.bag.get_next()
        self.can_hold = True

        if not self.grid.is_valid_position(self.current_tetromino, self.current_tetromino.x, self.current_tetromino.y):
            self.game_over()

    def update_score(self, lines):
        #Update score and level based on cleared lines
        self.score += SCORE_DATA.get(lines, 0) * self.level
        self.lines_cleared += lines
        new_level = 1 + self.lines_cleared // LINES_PER_LEVEL
        if new_level > self.level:
            self.level = new_level
            self.fall_speed = max(50, 1000 - (self.level * LEVEL_SPEED_REDUCTION))
        if lines > 0:
            self.sounds["line_clear"].play()
        if self.score > self.high_score:
            self.hige_score = self.score
            self.save_high_score()

    def game_over(self):
        #Trigger game over state and save high score
        self.sounds["game_over"].play()
        self.game_over_flag = True
        self.final_score = self.score
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def reset(self):
        #Reset the game state to start a new game
        self.game_over_flag = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = self.difficulties[self.selected_difficulty]
        self.grid.reset()
        self.bag = TetrominoBag()
        self.current_tetromino = self.bag.get_next()
        self.next_tetromino = self.bag.get_next()
        self.held_tetromino = None
        self.can_hold = True
        self.line_clear_delay = 0

    def load_high_score(self):
        #Load the high score from a file.
        try:
            with open("high_score.txt", "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError) as e:
            logging.error(f"Failed to load high score: {e}")
            return 0

    def save_high_score(self):
        #Save the high score to a file
        try:
            with open("high_score.txt", "w") as f:
                f.write(str(self.high_score))
        except Exception as e:
            logging.error(f"Failed to save high score: {e}")
