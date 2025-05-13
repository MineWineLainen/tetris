import json
from .tetromino import Tetromino, TetrominoBag

class SaveGame:
    @staticmethod
    def save(game):
        return {
            "score": game.score,
            "level": game.level,
            "lines_cleared": game.lines_cleared,
            "fall_speed": game.fall_speed,
            "game_mode": game.game_mode,
            "grid": [[cell if cell != 0 else 0 for cell in row] for row in game.grid.cells],
            "current_tetromino": game.current_tetromino.to_dict() if game.current_tetromino else None,
            "next_tetromino": game.next_tetromino.to_dict() if game.next_tetromino else None,
            "held_tetromino": game.held_tetromino.to_dict() if game.held_tetromino else None,
            "can_hold": game.can_hold,
            "stats": game.stats,
            "bag": game.bag.to_dict()
        }

    @staticmethod
    def load(game, data):
        game.score = data["score"]
        game.level = data["level"]
        game.lines_cleared = data["lines_cleared"]
        game.fall_speed = data["fall_speed"]
        game.game_mode = data["game_mode"]
        game.grid.cells = data["grid"]
        game.current_tetromino = Tetromino.from_dict(data["current_tetromino"]) if data["current_tetromino"] else None
        game.next_tetromino = Tetromino.from_dict(data["next_tetromino"]) if data["next_tetromino"] else None
        game.held_tetromino = Tetromino.from_dict(data["held_tetromino"]) if data["held_tetromino"] else None
        game.can_hold = data["can_hold"]
        game.stats = data["stats"]
        game.bag = TetrominoBag.from_dict(data["bag"])