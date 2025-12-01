"""
Окно сбора ресурсов из локаций (руины, лагеря бандитов, шахты).
"""
import pygame
from game.ui.base import UIHelper


class ResourceCollectionWindow:
    """Окно отображения собранных ресурсов с локации"""

    def __init__(self, screen, font, info_font, ui_scaler=None):
        """
        Инициализация окна сбора ресурсов

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

        # Данные собранных ресурсов
        self.collected_items = []  # Список (item, quantity)
        self.collected_gold = 0
        self.location_name = ""
        self.location_type_display = ""
        self.event_message = None  # Сообщение о событии (ловушка, бонусный лут и т.д.)

    def set_resources(self, items, gold, location_name, location_type_display, event_message=None):
        """
        Установить собранные ресурсы для отображения

        Args:
            items: Список кортежей (item, quantity)
            gold: Количество золота
            location_name: Название локации
            location_type_display: Отображаемый тип локации (Руины, Лагерь бандитов и т.д.)
            event_message: Сообщение о событии (опционально)
        """
        self.collected_items = items
        self.collected_gold = gold
        self.location_name = location_name
        self.location_type_display = location_type_display
        self.event_message = event_message

    def render(self):
        """Отрисовать окно собранных ресурсов"""
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
            window_height = self.ui_scaler.scale_height(550)
        else:
            window_width = min(600, int(screen_width * 0.7))
            window_height = min(550, int(screen_height * 0.65))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна с градиентом
        UIHelper.draw_gradient_rect(
            self.screen, window_x, window_y, window_width, window_height,
            (35, 45, 35), (50, 65, 50)
        )

        # Рамка окна (зеленая - сбор ресурсов)
        pygame.draw.rect(
            self.screen,
            (100, 200, 100),
            (window_x, window_y, window_width, window_height),
            4
        )

        # Заголовок
        title_text = self.font.render(
            "РЕСУРСЫ СОБРАНЫ!",
            True,
            (150, 255, 150)
        )
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + 15
        self.screen.blit(title_text, title_rect)

        # Название локации и тип
        location_text = self.info_font.render(
            f"{self.location_type_display}: {self.location_name}",
            True,
            (200, 200, 200)
        )
        location_rect = location_text.get_rect()
        location_rect.centerx = window_x + window_width // 2
        location_rect.y = window_y + 55
        self.screen.blit(location_text, location_rect)

        # Событие (если есть)
        current_y = window_y + 85
        if self.event_message:
            # Цвет в зависимости от типа события
            if "Удача" in self.event_message or "дополнительный" in self.event_message:
                event_color = (150, 255, 150)
            elif "ловушку" in self.event_message or "урон" in self.event_message:
                event_color = (255, 150, 150)
            else:
                event_color = (255, 215, 0)

            event_text = self.info_font.render(
                self.event_message,
                True,
                event_color
            )
            event_rect = event_text.get_rect()
            event_rect.centerx = window_x + window_width // 2
            event_rect.y = current_y
            self.screen.blit(event_text, event_rect)
            current_y += 30

        # Линия разделения
        pygame.draw.line(
            self.screen,
            (100, 150, 100),
            (window_x + 20, current_y),
            (window_x + window_width - 20, current_y),
            2
        )
        current_y += 15

        # Заголовок лута
        loot_title_text = self.font.render(
            "НАЙДЕННЫЕ РЕСУРСЫ:",
            True,
            (255, 255, 255)
        )
        loot_title_rect = loot_title_text.get_rect()
        loot_title_rect.centerx = window_x + window_width // 2
        loot_title_rect.y = current_y
        self.screen.blit(loot_title_text, loot_title_rect)
        current_y += 40

        # Золото (если есть)
        if self.collected_gold > 0:
            gold_text = self.font.render(
                f"💰 Золото: {self.collected_gold}",
                True,
                (255, 215, 0)
            )
            gold_rect = gold_text.get_rect()
            gold_rect.centerx = window_x + window_width // 2
            gold_rect.y = current_y
            self.screen.blit(gold_text, gold_rect)
            current_y += 40

        # Список предметов
        if self.collected_items:
            items_y = current_y
            max_visible_items = 6  # Максимум видимых предметов
            visible_items = self.collected_items[:max_visible_items]

            for idx, (item, quantity) in enumerate(visible_items):
                item_y = items_y + idx * 40

                # Фон предмета
                pygame.draw.rect(
                    self.screen,
                    (45, 55, 45),
                    (window_x + 30, item_y, window_width - 60, 35)
                )

                # Рамка предмета
                pygame.draw.rect(
                    self.screen,
                    (100, 150, 100),
                    (window_x + 30, item_y, window_width - 60, 35),
                    2
                )

                # Название предмета и количество
                display_name = f"{item.name} x{quantity}" if quantity > 1 else item.name
                item_text = self.info_font.render(
                    display_name,
                    True,
                    (220, 220, 220)
                )
                self.screen.blit(item_text, (window_x + 40, item_y + 8))

                # Стоимость предмета (справа)
                total_value = item.value * quantity
                value_text = self.info_font.render(
                    f"{total_value}g",
                    True,
                    (255, 215, 0)
                )
                self.screen.blit(value_text, (window_x + window_width - 100, item_y + 8))

            # Если предметов больше, показываем +N еще
            if len(self.collected_items) > max_visible_items:
                more_text = self.info_font.render(
                    f"... и еще {len(self.collected_items) - max_visible_items} предметов",
                    True,
                    (180, 180, 180)
                )
                more_rect = more_text.get_rect()
                more_rect.centerx = window_x + window_width // 2
                more_rect.y = items_y + max_visible_items * 40 + 10
                self.screen.blit(more_text, more_rect)
        elif self.collected_gold == 0:
            # Если вообще ничего не найдено
            no_items_text = self.info_font.render(
                "Ничего не найдено...",
                True,
                (150, 150, 150)
            )
            no_items_rect = no_items_text.get_rect()
            no_items_rect.centerx = window_x + window_width // 2
            no_items_rect.y = current_y + 20
            self.screen.blit(no_items_text, no_items_rect)

        # Подсказка внизу
        hint_text = self.info_font.render(
            "Нажмите любую клавишу для продолжения...",
            True,
            (180, 200, 180)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = window_y + window_height - 40
        self.screen.blit(hint_text, hint_rect)
