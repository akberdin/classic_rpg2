"""
Окно сбора лута.
"""
import pygame
from game.ui.base import UIHelper


class DungeonLootWindow:
    """Окно лута для подземелий (останки)"""

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
        self.loot_items = []  # Список кортежей (item_name, quantity)
        self.loot_gold = 0
        self.source_name = ""
        self.loot_type = "remains"

    def set_loot_from_remains(self, result: dict, enemy_name: str):
        """
        Установить лут из останков врага

        Args:
            result: Результат loot_remains
            enemy_name: Имя врага
        """
        self.loot_type = "remains"
        self.source_name = enemy_name
        self.loot_gold = result.get('gold', 0)

        # Преобразуем items - может быть [(item, qty), ...]
        self.loot_items = []
        for item_data in result.get('items', []):
            if len(item_data) == 2:
                # Формат (item, quantity) - из loot_remains
                item, quantity = item_data
                if hasattr(item, 'name'):
                    self.loot_items.append((item.name, quantity))
                else:
                    self.loot_items.append((str(item), quantity))

    def render(self):
        """Отрисовать окно лута"""
        # Затемняем фон
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные)
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        if self.ui_scaler:
            window_width = self.ui_scaler.scale_width(500)
            window_height = self.ui_scaler.scale_height(400)
        else:
            window_width = min(500, int(screen_width * 0.6))
            window_height = min(400, int(screen_height * 0.5))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна
        pygame.draw.rect(
            self.screen,
            (40, 40, 45),
            (window_x, window_y, window_width, window_height)
        )

        # Рамка окна (коричневатая для останков)
        border_color = (180, 120, 100)

        pygame.draw.rect(
            self.screen,
            border_color,
            (window_x, window_y, window_width, window_height),
            3
        )

        # Заголовок
        title = "ОБЫСК"
        title_color = (200, 180, 150)

        title_text = self.font.render(title, True, title_color)
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + 15
        self.screen.blit(title_text, title_rect)

        # Источник лута
        source_text = self.info_font.render(
            f"{self.source_name}",
            True,
            (200, 200, 200)
        )
        source_rect = source_text.get_rect()
        source_rect.centerx = window_x + window_width // 2
        source_rect.y = window_y + 50
        self.screen.blit(source_text, source_rect)

        # Линия разделения
        pygame.draw.line(
            self.screen,
            (100, 100, 100),
            (window_x + 20, window_y + 80),
            (window_x + window_width - 20, window_y + 80),
            2
        )

        # Золото
        if self.loot_gold > 0:
            gold_text = self.font.render(
                f"+{self.loot_gold} золота",
                True,
                (255, 215, 0)
            )
            gold_rect = gold_text.get_rect()
            gold_rect.centerx = window_x + window_width // 2
            gold_rect.y = window_y + 95
            self.screen.blit(gold_text, gold_rect)
            items_y = window_y + 140
        else:
            items_y = window_y + 100

        # Список предметов
        if self.loot_items:
            for idx, (item_name, quantity) in enumerate(self.loot_items):
                if idx >= 6:  # Максимум 6 предметов в окне
                    more_text = self.info_font.render(
                        f"...и еще {len(self.loot_items) - 6} предмет(ов)",
                        True,
                        (150, 150, 150)
                    )
                    self.screen.blit(more_text, (window_x + 40, items_y + idx * 35))
                    break

                item_y = items_y + idx * 35

                # Фон предмета
                pygame.draw.rect(
                    self.screen,
                    (50, 50, 55),
                    (window_x + 25, item_y, window_width - 50, 30)
                )

                # Рамка предмета
                pygame.draw.rect(
                    self.screen,
                    (80, 80, 80),
                    (window_x + 25, item_y, window_width - 50, 30),
                    1
                )

                # Название предмета и количество
                display_name = f"{item_name} x{quantity}" if quantity > 1 else item_name
                item_text = self.info_font.render(
                    display_name,
                    True,
                    (200, 200, 200)
                )
                self.screen.blit(item_text, (window_x + 35, item_y + 6))
        else:
            if self.loot_gold <= 0:
                no_items_text = self.info_font.render(
                    "Ничего не найдено",
                    True,
                    (150, 150, 150)
                )
                no_items_rect = no_items_text.get_rect()
                no_items_rect.centerx = window_x + window_width // 2
                no_items_rect.y = items_y + 20
                self.screen.blit(no_items_text, no_items_rect)

        # Подсказка внизу
        hint_text = self.info_font.render(
            "Нажмите любую клавишу...",
            True,
            (150, 150, 150)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = window_y + window_height - 35
        self.screen.blit(hint_text, hint_rect)


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


