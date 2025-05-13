import pygame
from game.game import Game

def main():
    try:
        game = Game()
        game.run()

    except Exception as e:
        print(f"Произошла критическая ошибка: {str(e)}")
        pygame.quit

    finally:
        pygame.quit()

if __name__ == "__main__":
    main()