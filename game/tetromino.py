import logging
import random
from config import COLORS, WALL_KICK_I, WALL_KICK_OTHER, WALL_KICK_I_CCW, WALL_KICK_OTHER_CCW

#Configure logging
logging.basicConfig(
    filename="tetris.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class Tetromino:
    def __init__(self, shape_type):
        self.shape_type = shape_type
        self.color = COLORS[shape_type]
        self.shape = self._get_shape_matrix(shape_type)
        self.x = 3
        self.y = 0
        self.rotation = 0

    def to_dict(self):
        return {
            "shape_type": self.shape_type,
            "color": self.color,
            "shape": self.shape,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation
        }
    
    @staticmethod
    def from_dict(data):
        if data is None:
            return None
        tetromino = Tetromino(data["shape_type"])
        tetromino.color = data["color"]
        tetromino.shape = data["shape"]
        tetromino.x = data["x"]
        tetromino.y = data["y"]
        tetromino.rotation = data["rotation"]
        return tetromino

    def _get_shape_matrix(self, shape_type):
        #Define shape matrices for each tetromino type
        SHAPES = {
            'I': [[1, 1, 1, 1]],
            'O': [[1, 1], [1, 1]],
            'T': [[0, 1, 0], [1, 1, 1]],
            'S': [[0, 1, 1], [1, 1, 0]],
            'Z': [[1, 1, 0], [0, 1, 1]],
            'J': [[1, 0, 0], [1, 1, 1]],
            'L': [[0, 0, 1], [1, 1, 1]]
        }
        return [row[:] for row in SHAPES[shape_type]]

    def rotate_clockwise(self, grid):
        #Rotate clockwise with wall kicks
        original_rotation = self.rotation
        original_x, original_y = self.x, self.y
        original_shape = [row[:] for row in self.shape]
        self.rotation = (self.rotation + 1) % 4
        self.shape = [list(row) for row in zip(*self.shape[::-1])]
        kick_table = WALL_KICK_I if self.shape_type == 'I' else WALL_KICK_OTHER
        logging.debug(f"Rotating {self.shape_type} clockwise from rotation {original_rotation} to {self.rotation}")
        for dx, dy in kick_table[original_rotation]:
            logging.debug(f"Trying wall kick: dx={dx}, dy={dy}")
            temp_x, temp_y = self.x + dx, self.y + dy
            if grid.is_valid_position(self, temp_x, temp_y):
                self.x, self.y = temp_x, temp_y
                logging.debug(f"Wall kick successful, new position: x={self.x}, y={self.y}")
                return True

        self.rotation = original_rotation
        self.x, self.y = original_x, original_y
        self.shape = original_shape
        logging.debug("Rotation failed, state restored")
        return False

    def rotate_counterclockwise(self, grid):
        #Rotate counterclockwise with wall kicks
        original_rotation = self.rotation
        original_x, original_y = self.x, self.y
        original_shape = [row[:] for row in self.shape]
        self.rotation = (self.rotation - 1) % 4
        self.shape = [list(row)[::-1] for row in zip(*self.shape[::-1])]
        kick_table = WALL_KICK_I_CCW if self.shape_type == 'I' else WALL_KICK_OTHER_CCW
        logging.debug(f"Rotating {self.shape_type} counterclockwise from rotation {original_rotation} to {self.rotation}")
        for dx, dy in kick_table[original_rotation]:
            logging.debug(f"Trying wall kick: dx={dx}, dy={dy}")
            temp_x, temp_y = self.x + dx, self.y + dy
            if grid.is_valid_position(self, temp_x, temp_y):
                self.x, self.y = temp_x, temp_y
                logging.debug(f"Wall kick successful, new position: x={self.x}, y={self.y}")
                return True

        self.rotation = original_rotation
        self.x, self.y = original_x, original_y
        self.shape = original_shape
        logging.debug("Rotation failed, state restored")
        return False

    def get_bounding_box(self):
        #Get the bounding box of the tetromino
        min_x = min(x for y, row in enumerate(self.shape) for x, cell in enumerate(row) if cell)
        max_x = max(x for y, row in enumerate(self.shape) for x, cell in enumerate(row) if cell)
        min_y = min(y for y, row in enumerate(self.shape) for x, cell in enumerate(row) if cell)
        max_y = max(y for y, row in enumerate(self.shape) for x, cell in enumerate(row) if cell)
        return min_x, max_x, min_y, max_y

class TetrominoBag:
    def __init__(self):
        self.shapes = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']
        self.bag = []
        self.fill_bag()

    def to_dict(self):
        return {"bag": self.bag}

    @staticmethod
    def from_dict(data):
        bag = TetrominoBag()
        bag.bag = data["bag"]
        return bag

    def fill_bag(self):
        self.bag.extend(self.shapes)
        random.shuffle(self.bag)
        logging.debug(f"Bag filled and shuffled: {self.bag}")

    def get_next(self):
        if not self.bag:
            self.fill_bag()
        shape_type = self.bag.pop(0)
        logging.debug(f"Got tetromino {shape_type}, remaining in bag: {self.bag}")
        return Tetromino(shape_type)