import pygame
import logging
import os
import json
import time
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, SCORE_DATA, LINES_PER_LEVEL, LEVEL_SPEED_REDUCTION, COLORS, GRID_COLS, GRID_ROWS, CELL_SIZE, PATHS, THEMES, GAME_MODES, DEFAULT_KEY_BINDINGS, LOCK_DELAY, FADE_DURATION
from .tetromino import Tetromino, TetrominoBag
from .grid import Grid
from .settings import Settings
from .save_game import SaveGame
from enum import Enum

#Logging
logging.basicConfig(filename="tetris.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

#GameState class
class GameState(Enum):
    MENU = 1
    SETTINGS = 2
    PAUSED = 3
    PLAYING = 4
    GAME_OVER = 5

class Game:
    def __init__(self):
        #Initialize Tetris with Pygame, game state, and resources
        try:
            pygame.init()
            pygame.font.init()
            pygame.mixer.init()
        except Exception as e:
            logging.error(f"Failed to initialize Pygame: {e}")
            raise

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.game_surface = pygame.Surface((GRID_COLS * CELL_SIZE, GRID_ROWS * CELL_SIZE), pygame.SRCALPHA)
        pygame.display.set_caption("Tetris")

        #Game state
        self.state = GameState.MENU
        self.final_score = 0
        self.high_score = self.load_high_score()
        self.start_time = 0
        self.game_mode = "Marathon"
        self.settings = Settings()
        self.current_theme = self.settings.get_theme()
        self.key_bindings = self.settings.get_key_bindings()

        #Time management
        self.clock = pygame.time.Clock()
        self.fall_time = 0
        self.fall_speed = GAME_MODES[self.game_mode]["fall_speed"]
        self.line_clear_delay = 0
        self.lock_delay = 0
        self.locked = False

        #Game components
        self.grid = Grid()
        self.grid.current_theme = self.current_theme
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
        self.modes = list(GAME_MODES.keys())
        self.selected_mode = "Marathon"
        self.themes = list(THEMES.keys())
        self.selected_theme = self.current_theme

        #Statistics
        self.stats = {
            "tetrominos": {'I': 0, 'O': 0, 'T': 0, 'L': 0, 'J': 0, 'S': 0, 'Z': 0},
            "lines": {1: 0, 2: 0, 3: 0, 4: 0},
            "time": 0
        }

        #Settings state
        self.key_to_rebind = None
        self.waiting_for_key = False

    def run(self):
        #Run the main game loop
        while True:
            self.clock.tick(FPS)
            if self.state == GameState.MENU:
                self.handle_menu_events()
                self.draw_menu()
            elif self.state == GameState.SETTINGS:
                self.handle_settings_events()
                self.draw_settings()
            elif self.state == GameState.PAUSED:
                self.handle_pause_events()
                self.draw_pause()
            elif self.state == GameState.PLAYING:
                self.handle_events()
                self.update()
                self.draw()
            elif self.state == GameState.GAME_OVER:
                self.handle_game_over_events()
                self.draw_game_over()
            pygame.display.flip()

    def handle_menu_events(self):
        #Handle main menu events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    current_idx = self.modes.index(self.selected_mode)
                    self.selected_mode = self.modes[(current_idx - 1) % len(self.modes)]
                if event.key == pygame.K_DOWN:
                    current_idx = self.modes.index(self.selected_mode)
                    self.selected_mode = self.modes[(current_idx + 1) % len(self.modes)]
                if event.key == pygame.K_RETURN:
                    self.start_game()
                if event.key == pygame.K_s:
                    self.state = GameState.SETTINGS
                if event.key == pygame.K_l:
                    self.load_game()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

    def handle_settings_events(self):
        #Handle settings menu events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if self.waiting_for_key:
                    self.key_bindings[self.key_to_rebind] = pygame.key.name(event.key)
                    self.settings.save_key_bindings(self.key_bindings)
                    self.waiting_for_key = False
                    self.key_to_rebind = None
                else:
                    if event.key == pygame.K_UP:
                        current_idx = self.themes.index(self.selected_theme)
                        self.selected_theme = self.themes[(current_idx - 1) % len(self.themes)]
                    if event.key == pygame.K_DOWN:
                        current_idx = self.themes.index(self.selected_theme)
                        self.selected_theme = self.themes[(current_idx + 1) % len(self.themes)]
                    if event.key == pygame.K_s:
                        self.settings.save_theme(self.selected_theme)
                        self.current_theme = self.selected_theme
                        self.grid.current_theme = self.current_theme
                        self.grid.update_theme()
                        self.screen.fill(THEMES[self.current_theme]["background"])
                        pygame.display.flip()
                    if event.key == pygame.K_1:
                        self.key_to_rebind = "left"
                        self.waiting_for_key = True
                    if event.key == pygame.K_2:
                        self.key_to_rebind = "right"
                        self.waiting_for_key = True
                    if event.key == pygame.K_3:
                        self.key_to_rebind = "down"
                        self.waiting_for_key = True
                    if event.key == pygame.K_4:
                        self.key_to_rebind = "hard_drop"
                        self.waiting_for_key = True
                    if event.key == pygame.K_5:
                        self.key_to_rebind = "rotate_cw"
                        self.waiting_for_key = True
                    if event.key == pygame.K_6:
                        self.key_to_rebind = "rotate_ccw"
                        self.waiting_for_key = True
                    if event.key == pygame.K_7:
                        self.key_to_rebind = "hold"
                        self.waiting_for_key = True
                    if event.key == pygame.K_8:
                        self.key_to_rebind = "pause"
                        self.waiting_for_key = True
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU

    def handle_pause_events(self):
        #Handle pause menu events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.state = GameState.PLAYING
                if event.key == pygame.K_s:
                    self.save_game()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

    def handle_game_over_events(self):
        #Handle gameplay events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.reset()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

    def handle_events(self):
        #Update game state
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                key_name = pygame.key.name(event.key)
                actions = {
                    self.key_bindings["rotate_cw"]: lambda: self.rotate_tetromino(clockwise=True),
                    self.key_bindings["rotate_ccw"]: lambda: self.rotate_tetromino(clockwise=False),
                    self.key_bindings["hard_drop"]: lambda: self.hard_drop(),
                    self.key_bindings["hold"]: lambda: self.hold_tetromino(),
                    self.key_bindings["pause"]: lambda: setattr(self, 'state', GameState.PAUSED)
                }
                if key_name in actions:
                    actions[key_name]()

        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        move_actions = {
            self.key_bindings["left"]: lambda: self.move_horizontal(-1),
            self.key_bindings["right"]: lambda: self.move_horizontal(1),
            self.key_bindings["down"]: lambda: self.soft_drop()
        }
        for key, action in move_actions.items():
            if keys[pygame.key.key_code(key)] and current_time - self.last_move_time > self.move_delay:
                action()
                self.last_move_time = current_time

    def update(self):
        #Update game state
        if self.state != GameState.PLAYING:
            return

        current_time = pygame.time.get_ticks()
        self.stats["time"] = (current_time - self.start_time) // 1000

        #Handle line clear delay
        if self.line_clear_delay > 0:
            if current_time - self.line_clear_delay >= FADE_DURATION:
                self.line_clear_delay = 0
            return

        #Handle lock delay
        if self.locked:
            if current_time - self.lock_delay >= LOCK_DELAY:
                self.fix_tetromino()
                self.locked = False
            return

        #Automatic falling
        if current_time - self.fall_time > self.fall_speed:
            if not self.move_vertical():
                self.locked = True
                self.lock_delay = current_time
            else:
                self.fall_time = current_time

        #Check game mode conditions
        if self.game_mode == "Sprint" and self.lines_cleared >= GAME_MODES["Sprint"]["goal"]:
            self.game_over()
        elif self.game_mode == "Ultra" and current_time - self.start_time >= GAME_MODES["Ultra"]["time_limit"]:
            self.game_over()

    def draw(self):
        #Clear screen before rendering
        self.screen.fill(THEMES[self.current_theme]["background"])
        self.game_surface.fill(THEMES[self.current_theme]["background"])

        #Render grid and current tetromino if it exists
        if self.state == GameState.PLAYING:
            self.grid.draw(self.game_surface, self.current_tetromino if self.current_tetromino else None)
            if self.current_tetromino:
                self.draw_current_tetromino()
            self.screen.blit(self.game_surface, (20, 20))
            self.draw_ui()

    def draw_menu(self):
        #Main menu render
        self.screen.fill(THEMES[self.current_theme]["background"])
        self.draw_text("Tetris", (SCREEN_WIDTH // 2, 100), 24, center=True)
        self.draw_text("Select Mode:", (SCREEN_WIDTH // 2, 200), center=True)
        for i, mode in enumerate(self.modes):
            color = (255, 255, 0) if mode == self.selected_mode else THEMES[self.current_theme]["text"]
            self.draw_text(mode, (SCREEN_WIDTH // 2, 250 + i * 40), center=True, color=color)
        self.draw_text("Press ENTER to start, S for settings, L to load, ESC to quit", (SCREEN_WIDTH // 2, 400), center=True)

    def draw_settings(self):
        #Settings menu render
        self.screen.fill(THEMES[self.current_theme]["background"])
        self.draw_text("Settings", (SCREEN_WIDTH // 2, 100), 24, center=True)
        self.draw_text("Select Theme:", (SCREEN_WIDTH // 2, 200), center=True)
        for i, theme in enumerate(self.themes):
            color = (255, 255, 0) if theme == self.selected_theme else THEMES[self.current_theme]["text"]
            self.draw_text(theme, (SCREEN_WIDTH // 2, 250 + i * 40), center=True, color=color)
        self.draw_text("Press 1-8 to rebind keys, S to save theme, ESC to return", (SCREEN_WIDTH // 2, 400), center=True)
        self.draw_text("1:Left, 2:Right, 3:Down, 4:Hard Drop, 5:Rotate CW, 6:Rotate CCW, 7:Hold, 8:Pause", (SCREEN_WIDTH // 2, 430), center=True)
        if self.waiting_for_key:
            self.draw_text(f"Press key for {self.key_to_rebind}", (SCREEN_WIDTH // 2, 460), center=True)

    def draw_pause(self):
        #Pause menu render
        self.screen.fill(THEMES[self.current_theme]["background"])
        self.draw_text("Paused", (SCREEN_WIDTH // 2, 200), 24, center=True)
        self.draw_text("Press P to resume, S to save, ESC to quit", (SCREEN_WIDTH // 2, 300), center=True)

    def draw_game_over(self):
        #Game over screen render
        self.screen.fill(THEMES[self.current_theme]["background"])
        self.draw_text("GAME OVER", (SCREEN_WIDTH // 2, 200), 24, center=True)
        self.draw_text(f"Final Score: {self.final_score}", (SCREEN_WIDTH // 2, 250), center=True)
        self.draw_text(f"High Score: {self.high_score}", (SCREEN_WIDTH // 2, 280), center=True)
        self.draw_text(f"Time: {self.stats['time']}s", (SCREEN_WIDTH // 2, 310), center=True)
        self.draw_text("Tetrominos:", (SCREEN_WIDTH // 2, 340), center=True)
        for i, (shape, count) in enumerate(self.stats["tetrominos"].items()):
            self.draw_text(f"{shape}: {count}", (SCREEN_WIDTH // 2, 360 + i * 20), center=True)
        self.draw_text("Lines Cleared:", (SCREEN_WIDTH // 2, 520), center=True)
        for i, (lines, count) in enumerate(self.stats["lines"].items()):
            self.draw_text(f"{lines} Lines: {count}", (SCREEN_WIDTH // 2, 540 + i * 20), center=True)
        self.draw_text("Press SPACE to restart or ESC to quit", (SCREEN_WIDTH // 2, 620), center=True)

    def draw_ui(self):
        #UI render
        self.draw_text(f"Score: {self.score}", (320, 50))
        self.draw_text(f"High Score: {self.high_score}", (320, 80))
        self.draw_text(f"Level: {self.level}", (320, 110))
        self.draw_text(f"Mode: {self.game_mode}", (320, 140))
        self.draw_text("Next:", (320, 170))
        self.draw_tetromino_preview(self.next_tetromino, 320, 200)
        self.draw_text("Hold:", (320, 320))
        self.draw_tetromino_preview(self.held_tetromino, 320, 350)

    def draw_tetromino_preview(self, tetromino, x, y):
        #Render tetromino preview
        if not tetromino:
            return
        for dy, row in enumerate(tetromino.shape):
            for dx, cell in enumerate(row):
                if cell:
                    cell_surface = pygame.Surface((18, 18), pygame.SRCALPHA)
                    cell_surface.set_alpha(THEMES[self.current_theme]["cell_alpha"])
                    cell_surface.fill((*tetromino.color, THEMES[self.current_theme]["cell_alpha"]))
                    border_color = tuple(min(255, c + 40) for c in tetromino.color)
                    pygame.draw.rect(cell_surface, (*border_color, THEMES[self.current_theme]["cell_alpha"]), (0, 0, 18, 18), 1)
                    self.screen.blit(cell_surface, (x + dx * 20, y + dy * 20))

    def draw_current_tetromino(self):
        #Render current tetromino
        if not self.current_tetromino:
            return
        for y, row in enumerate(self.current_tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    screen_x = (self.current_tetromino.x + x) * CELL_SIZE
                    screen_y = (self.current_tetromino.y + y) * CELL_SIZE
                    cell_surface = pygame.Surface((CELL_SIZE - 2, CELL_SIZE - 2), pygame.SRCALPHA)
                    cell_surface.set_alpha(THEMES[self.current_theme]["cell_alpha"])
                    cell_surface.fill((*self.current_tetromino.color, THEMES[self.current_theme]["cell_alpha"]))
                    border_color = tuple(min(255, c + 40) for c in self.current_tetromino.color)
                    pygame.draw.rect(cell_surface, (*border_color, THEMES[self.current_theme]["cell_alpha"]), (0, 0, CELL_SIZE - 2, CELL_SIZE - 2), 2)
                    self.game_surface.blit(cell_surface, (screen_x, screen_y))

    def draw_text(self, text, position, size=18, color=None, center=False):
        #Render in-game text
        if color is None:
            color = THEMES[self.current_theme]["text"]
        font = self.menu_font if size > 18 else self.font
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=position) if center else text_surface.get_rect(topleft=position)
        self.screen.blit(text_surface, text_rect)

    def start_game(self):
        #Launch game
        self.state = GameState.PLAYING
        self.game_mode = self.selected_mode
        self.fall_speed = GAME_MODES[self.game_mode]["fall_speed"]
        self.current_tetromino = self.bag.get_next()
        self.next_tetromino = self.bag.get_next()
        self.held_tetromino = None
        self.can_hold = True
        self.start_time = pygame.time.get_ticks()
        self.stats = {
            "tetrominos": {'I': 0, 'O': 0, 'T': 0, 'L': 0, 'J': 0, 'S': 0, 'Z': 0},
            "lines": {1: 0, 2: 0, 3: 0, 4: 0},
            "time": 0
        }
        self.screen.fill(THEMES[self.current_theme]["background"])
        pygame.display.flip()

    def move_horizontal(self, direction):
        #Move tetromino horizontaly
        new_x = self.current_tetromino.x + direction
        if self.grid.is_valid_position(self.current_tetromino, new_x, self.current_tetromino.y):
            self.current_tetromino.x = new_x
            self.locked = False

    def rotate_tetromino(self, clockwise=True):
        #Tetromino rotation
        self.sounds["rotate"].play()
        success = (self.current_tetromino.rotate_clockwise(self.grid) if clockwise
                   else self.current_tetromino.rotate_counterclockwise(self.grid))
        if success and self.locked:
            self.locked = False
        if not success:
            self.sounds["rotate"].stop()

    def soft_drop(self):
        #Preform soft drop
        if self.move_vertical():
            self.score += 1 * self.level
            self.fall_time = pygame.time.get_ticks()
            self.sounds["drop"].play()
            self.locked = False

    def hard_drop(self):
        #Perform hard drop
        self.sounds["hard_drop"].play()
        drop_distance = 0
        while self.move_vertical():
            drop_distance += 1
        self.score += 2 * drop_distance * self.level
        self.fix_tetromino()

    def hold_tetromino(self):
        #Hold tetromino in place
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
        self.locked = False

    def move_vertical(self):
        #Move tetromino down
        new_y = self.current_tetromino.y + 1
        if self.grid.is_valid_position(self.current_tetromino, self.current_tetromino.x, new_y):
            self.current_tetromino.y = new_y
            return True
        return False

    def fix_tetromino(self):
        #Lock tetromino and handle line clears
        self.sounds["drop"].play()
        self.stats["tetrominos"][self.current_tetromino.shape_type] += 1
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
            self.stats["lines"][lines_cleared] += 1

        self.current_tetromino = self.next_tetromino
        self.next_tetromino = self.bag.get_next()
        self.can_hold = True
        self.locked = False

        if not self.grid.is_valid_position(self.current_tetromino, self.current_tetromino.x, self.current_tetromino.y):
            self.game_over()

    def update_score(self, lines):
        #Update score and level
        self.score += SCORE_DATA.get(lines, 0) * self.level
        self.lines_cleared += lines
        new_level = 1 + self.lines_cleared // LINES_PER_LEVEL
        if new_level > self.level:
            self.level = new_level
            self.fall_speed = max(50, 1000 - (self.level * LEVEL_SPEED_REDUCTION))
        if lines > 0:
            self.sounds["line_clear"].play()
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def game_over(self):
        #Trigger game over
        self.sounds["game_over"].play()
        self.state = GameState.GAME_OVER
        self.final_score = self.score
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def reset(self):
        #Reset game state
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = GAME_MODES[self.game_mode]["fall_speed"]
        self.grid.reset()
        self.bag = TetrominoBag()
        self.current_tetromino = self.bag.get_next()
        self.next_tetromino = self.bag.get_next()
        self.held_tetromino = None
        self.can_hold = True
        self.line_clear_delay = 0
        self.locked = False
        self.start_time = pygame.time.get_ticks()
        self.stats = {
            "tetrominos": {'I': 0, 'O': 0, 'T': 0, 'L': 0, 'J': 0, 'S': 0, 'Z': 0},
            "lines": {1: 0, 2: 0, 3: 0, 4: 0},
            "time": 0
        }

    def load_high_score(self):
        #Load high score
        if os.path.exists("high_score.txt"):
            try:
                with open("high_score.txt", "r") as f:
                    return int(f.read().strip())
            except (ValueError, IOError):
                return 0
        return 0

    def save_high_score(self):
        #Save high score
        try:
            with open("high_score.txt", "w") as f:
                f.write(str(self.high_score))
        except Exception as e:
            logging.error(f"Failed to save high score: {e}")

    def save_game(self):
        #Save game state
        try:
            save_data = SaveGame.save(self)
            with open("save_game.json", "w") as f:
                json.dump(save_data, f)
        except Exception as e:
            logging.error(f"Failed to save game: {e}")

    def load_game(self):
        #Load save file
        if os.path.exists("save_game.json"):
            try:
                with open("save_game.json", "r") as f:
                    save_data = json.load(f)
                SaveGame.load(self, save_data)
                self.state = GameState.PLAYING
                self.start_time = pygame.time.get_ticks() - (self.stats["time"] * 1000)
            except Exception as e:
                logging.error(f"Failed to load game: {e}")
                print("Failed to load game. Starting a new one.")
                self.start_game()
        else:
            print("There is no save files! Starting a new game.")
            self.start_game()