"""
Окно сбора лута.
"""
import pygame
from game.ui.base import UIHelper


class LootWindow:
    """Окно лута после победы над врагом"""

    def __init__(self, screen, font, info_font, ui_scaler=None):
        """
        Инициализация окна лута

        Args:
            screen: Поверхность pygame для отрисовки
            font: Основной шрифт
            info_font: Шрифт для информации
            ui_scaler: Масштабировщик UI (опционально)
        """
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.ui_scaler = ui_scaler
        
        # Данные лута
        self.loot_items = []  # Список (item, quantity)
        self.loot_gold = 0
        self.enemy_name = ""

    def set_loot(self, items, gold, enemy_name):
        """
        Установить лут для отображения

        Args:
            items: Список кортежей (item, quantity)
            gold: Количество золота
            enemy_name: Имя поверженного врага
        """
        self.loot_items = items
        self.loot_gold = gold
        self.enemy_name = enemy_name

    def render(self):
        """Отрисовать окно лута"""
        import pygame

        # Затемняем фон
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные)
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        if self.ui_scaler:
            window_width = self.ui_scaler.scale_width(600)
            window_height = self.ui_scaler.scale_height(500)
        else:
            window_width = min(600, int(screen_width * 0.7))
            window_height = min(500, int(screen_height * 0.6))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна
        pygame.draw.rect(
            self.screen,
            (40, 40, 45),
            (window_x, window_y, window_width, window_height)
        )

        # Рамка окна (золотая - победа!)
        pygame.draw.rect(
            self.screen,
            (255, 215, 0),
            (window_x, window_y, window_width, window_height),
            4
        )

        # Заголовок
        title_text = self.font.render(
            "ПОБЕДА!",
            True,
            (255, 215, 0)
        )
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + 15
        self.screen.blit(title_text, title_rect)

        # Имя врага
        enemy_text = self.info_font.render(
            f"Вы победили: {self.enemy_name}",
            True,
            (200, 200, 200)
        )
        enemy_rect = enemy_text.get_rect()
        enemy_rect.centerx = window_x + window_width // 2
        enemy_rect.y = window_y + 55
        self.screen.blit(enemy_text, enemy_rect)

        # Линия разделения
        pygame.draw.line(
            self.screen,
            (100, 100, 100),
            (window_x + 20, window_y + 90),
            (window_x + window_width - 20, window_y + 90),
            2
        )

        # Заголовок лута
        loot_title_text = self.font.render(
            "ПОЛУЧЕННЫЙ ЛУТ:",
            True,
            (255, 255, 255)
        )
        loot_title_rect = loot_title_text.get_rect()
        loot_title_rect.centerx = window_x + window_width // 2
        loot_title_rect.y = window_y + 105
        self.screen.blit(loot_title_text, loot_title_rect)

        # Золото
        gold_text = self.font.render(
            f"Золото: {self.loot_gold}",
            True,
            (255, 215, 0)
        )
        gold_rect = gold_text.get_rect()
        gold_rect.centerx = window_x + window_width // 2
        gold_rect.y = window_y + 145
        self.screen.blit(gold_text, gold_rect)

        # Список предметов
        items_y = window_y + 190
        if self.loot_items:
            for idx, (item, quantity) in enumerate(self.loot_items):
                item_y = items_y + idx * 40

                # Фон предмета
                pygame.draw.rect(
                    self.screen,
                    (50, 50, 55),
                    (window_x + 30, item_y, window_width - 60, 35)
                )

                # Рамка предмета
                pygame.draw.rect(
                    self.screen,
                    (100, 100, 100),
                    (window_x + 30, item_y, window_width - 60, 35),
                    1
                )

                # Название предмета и количество (показываем количество только если > 1)
                display_name = f"{item.name} x{quantity}" if quantity > 1 else item.name
                item_text = self.info_font.render(
                    display_name,
                    True,
                    (200, 200, 200)
                )
                self.screen.blit(item_text, (window_x + 40, item_y + 8))

                # Стоимость предмета (справа)
                value_text = self.info_font.render(
                    f"{item.value}g",
                    True,
                    (255, 215, 0)
                )
                self.screen.blit(value_text, (window_x + window_width - 100, item_y + 8))
        else:
            no_items_text = self.info_font.render(
                "Предметов не найдено",
                True,
                (150, 150, 150)
            )
            no_items_rect = no_items_text.get_rect()
            no_items_rect.centerx = window_x + window_width // 2
            no_items_rect.y = items_y + 20
            self.screen.blit(no_items_text, no_items_rect)

        # Подсказка внизу
        hint_text = self.info_font.render(
            "Нажмите любую клавишу для продолжения...",
            True,
            (180, 180, 180)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = window_y + window_height - 40
        self.screen.blit(hint_text, hint_rect)


