# =============================================
#DISPLAY
# =============================================
SCREEN_WIDTH = 800      #Screen width
SCREEN_HEIGHT = 650     #Screen height
FPS = 60                #FPS

# =============================================
#GRID PARAMETRS
# =============================================
CELL_SIZE = 30          #Cell size in pixels
GRID_COLS = 10          #Amount of columns
GRID_ROWS = 20          #A,ount of rows

# =============================================
#COLORING
# =============================================
COLORS = {
    #Tetramino colors
    'I': (0, 255, 255),     #Cyan
    'O': (255, 255, 0),     #Yellow
    'T': (128, 0, 128),     #Purple
    'L': (255, 165, 0),     #Orange
    'J': (0, 0, 255),       #Blue
    'S': (0, 255, 0),       #Green
    'Z': (255, 0, 0),       #Red
    
    #Additional colors
    'background': (25, 25, 25),    #Background
    'grid_line': (40, 40, 40),     #Grid lines
    'text': (255, 255, 255)        #Text
}

# =============================================
#GAMEPLAY PARAMETRS
# =============================================
BASE_FALL_SPEED = 1000          #Base fall speed (ms)
LEVEL_SPEED_REDUCTION = 100     #Level speed redction (ms)
LINES_PER_LEVEL = 10            #lines per level 

# =============================================
#SCORE SYSTEM
# =============================================
SCORE_DATA = {
    1: 100,     #1 line
    2: 300,     #2 lines
    3: 700,     #3 lines
    4: 1500     #Tetris
}

# =============================================
#ADDITIONAL SETTINGS
# =============================================
PREVIEW_SCALE = 0.6         #Preview scale
WALL_KICK_ENABLED = True    #Wall Kick enabler


# =============================================
#PATHS
# =============================================
PATHS = {
    "fonts": {
        "main": "assets/fonts/PressStart2P.ttf"
    },
    "sounds": {
        "rotate": "assets/sounds/rotate.wav",
        "drop": "assets/sounds/drop.wav",
        "hard_drop": "assets/sounds/hard_drop.wav",
        "line_clear": "assets/sounds/line_clear.wav",
        "game_over": "assets/sounds/game_over.wav"
        }
    }