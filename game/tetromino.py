import random
from collections import deque
from config import COLORS

#Standard SRS wall kick data for I tetromino
WALL_KICK_I = [
    [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)]
]

WALL_KICK_I_CCW = [
    [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)]
]

#Standard SRS wall kick data for non-I tetrominos 
WALL_KICK_OTHER = [
    [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],  #0->1
    [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],    #1->2
    [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],     #2->3
    [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)]  #3->0
]

WALL_KICK_OTHER_CCW = [
    [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],    #0->3
    [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],     #3->2
    [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)], #2->1
    [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)]   #1->0
]

class Tetromino:
    def __init__(self, shape_type, x=0, y=0):
        #Initialize a tetromino with a specific shape, position, and color
        self.shape_type = shape_type
        self.color = COLORS[shape_type]
        self.shape = self._get_shape_matrix(shape_type)
        self.rotation = 0

        #Center tetrominos: x=3 for I, T, L, J, S, Z; x=4 for O
        self.x = 3 if shape_type != 'O' else 4
        self.y = y  

    @staticmethod
    def _get_shape_matrix(shape_type):
        #Return the 4x4 matrix representing the tetromino's shape
        shapes = {
            'I': [
                [0, 0, 0, 0],
                [1, 1, 1, 1],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            'O': [
                [0, 0, 0, 0],
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0]
            ],
            'T': [
                [0, 0, 0, 0],
                [0, 1, 0, 0],
                [1, 1, 1, 0],
                [0, 0, 0, 0]
            ],
            'L': [
                [0, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 1, 0]
            ],
            'J': [
                [0, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 0],
                [0, 1, 1, 0]
            ],
            'S': [
                [0, 0, 0, 0],
                [0, 1, 1, 0],
                [1, 1, 0, 0],
                [0, 0, 0, 0]
            ],
            'Z': [
                [0, 0, 0, 0],
                [1, 1, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0]
            ]
        }
        return shapes[shape_type]


    def rotate_clockwise(self, grid):
        #Rotate the tetromino clockwise, applying SRS wall kicks if needed
        original_rotation = self.rotation
        original_x, original_y = self.x, self.y
        original_shape = [row[:] for row in self.shape]

        self.rotation = (self.rotation + 1) % 4
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

        #Apply wall kicks
        kick_table = WALL_KICK_I if self.shape_type == 'I' else WALL_KICK_OTHER
        for dx, dy in kick_table[original_rotation]:
            temp_x, temp_y = self.x + dx, self.y + dy
            if grid.is_valid_position(self, temp_x, temp_y):
                self.x, self.y = temp_x, temp_y
                return True

        #Revert if no valid position found
        self.rotation = original_rotation
        self.x, self.y = original_x, original_y
        self.shape = original_shape
        return False

    def rotate_counterclockwise(self, grid):
        #Rotate the tetromino counterclockwise, applying SRS wall kicks if needed
        original_rotation = self.rotation
        original_x, original_y = self.x, self.y
        original_shape = [row[:] for row in self.shape]

        self.rotation = (self.rotation - 1) % 4
        self.shape = [list(row)[::-1] for row in zip(*self.shape[::-1])]

        #Apply wall kicks
        kick_table = WALL_KICK_I_CCW if self.shape_type == 'I' else WALL_KICK_OTHER_CCW
        for dx, dy in kick_table[original_rotation]:
            temp_x, temp_y = self.x + dx, self.y + dy
            if grid.is_valid_position(self, temp_x, temp_y):
                self.x, self.y = temp_x, temp_y
                return True

        #Revert if no valid position found
        self.rotation = original_rotation
        self.x, self.y = original_x, original_y
        self.shape = original_shape
        return False

class TetrominoBag:
    def __init__(self):
        #Initialize a tetromino bag with a shuffled queue of tetromino shapes
        self.bag = deque()
        self._refill_bag()

    def _refill_bag(self):
        #Refill the bag with a shuffled set of all tetromino shapes
        shapes = ['I', 'O', 'T', 'L', 'J', 'S', 'Z']
        random.shuffle(shapes)
        self.bag.extend(shapes)

    def get_next(self, x=0, y=0):
        #Get the next tetromino from the bag, refilling if necessary
        if not self.bag:
            self._refill_bag()
        return Tetromino(self.bag.popleft(), x, y)
