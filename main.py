"""
Пошаговая RPG игра на Pygame
Главный файл запуска игры
"""
import pygame
import sys
from game.engine import Game


def main():
    """Главная функция запуска игры"""
    pygame.init()

    game = Game()
    game.run()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
