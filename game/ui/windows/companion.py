"""
Окно управления спутниками
"""
import pygame
from game.ui.windows.base import BaseWindow


class CompanionWindow(BaseWindow):
    """Окно управления спутниками"""

    BASE_WIDTH = 800
    BASE_HEIGHT = 700

    def __init__(self, screen, font, info_font, scaler=None):
        super().__init__(screen, font, info_font, scaler)
        self.selected_companion_index = 0
        self.show_dismiss_confirmation = False
        self.companion_to_dismiss = None

    def render(self, companion_manager):
        """
        Отрисовка окна спутников

        Args:
            companion_manager: Менеджер спутников
        """
        companions = companion_manager.get_all_companions()

        # Используем базовый класс для отрисовки окна
        win = self.begin_render(
            self.BASE_WIDTH, self.BASE_HEIGHT,
            title="СПУТНИКИ"
        )

        window_x = win['x']
        window_y = win['y']
        window_width = win['width']
        window_height = win['height']
        scale_w = win['scale_w']
        scale_h = win['scale_h']

        # Если нет спутников
        if not companions:
            no_companions_text = self.font.render(
                "У вас пока нет спутников",
                True,
                (150, 150, 150)
            )
            text_rect = no_companions_text.get_rect()
            text_rect.centerx = window_x + window_width // 2
            text_rect.centery = window_y + window_height // 2
            self.screen.blit(no_companions_text, text_rect)

            hint_text = self.info_font.render(
                "Спутники присоединяются к вам в процессе приключений",
                True,
                (120, 120, 120)
            )
            hint_rect = hint_text.get_rect()
            hint_rect.centerx = window_x + window_width // 2
            hint_rect.centery = text_rect.centery + int(40 * scale_h)
            self.screen.blit(hint_text, hint_rect)
            return

        # Ограничиваем выбранный индекс
        if self.selected_companion_index >= len(companions):
            self.selected_companion_index = len(companions) - 1

        # Список спутников (левая часть)
        list_x = window_x + int(30 * scale_w)
        list_y = window_y + int(60 * scale_h)
        list_width = int(280 * scale_w)

        list_title = self.font.render("Ваши спутники:", True, (200, 200, 200))
        self.screen.blit(list_title, (list_x, list_y))

        list_y += int(35 * scale_h)

        for i, companion in enumerate(companions):
            item_y = list_y + i * int(60 * scale_h)

            # Подсветка выбранного спутника
            if i == self.selected_companion_index:
                pygame.draw.rect(
                    self.screen,
                    (80, 80, 100),
                    (list_x - int(10 * scale_w), item_y - int(5 * scale_h),
                     list_width + int(20 * scale_w), int(55 * scale_h))
                )
                pygame.draw.rect(
                    self.screen,
                    (120, 150, 200),
                    (list_x - int(10 * scale_w), item_y - int(5 * scale_h),
                     list_width + int(20 * scale_w), int(55 * scale_h)),
                    2
                )

            # Имя и ранг
            name_text = self.info_font.render(companion.name, True, (220, 220, 220))
            self.screen.blit(name_text, (list_x, item_y))

            # Уровень
            level_text = self.info_font.render(
                f"Уровень {companion.level}",
                True,
                (180, 180, 180)
            )
            self.screen.blit(level_text, (list_x, item_y + int(20 * scale_h)))

        # Разделитель
        separator_x = window_x + int(340 * scale_w)
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (separator_x, window_y + int(50 * scale_h)),
            (separator_x, window_y + window_height - int(50 * scale_h)),
            2
        )

        # Детальная информация (правая часть)
        if companions:
            selected_companion = companions[self.selected_companion_index]
            self._render_companion_details(
                selected_companion,
                separator_x + int(30 * scale_w),
                window_y + int(60 * scale_h),
                window_width - int(390 * scale_w),
                scale_w,
                scale_h
            )

            # Кнопка "Прогнать"
            if not self.show_dismiss_confirmation:
                dismiss_text = self.info_font.render(
                    "[D] Прогнать спутника",
                    True,
                    (255, 100, 100)
                )
                dismiss_rect = dismiss_text.get_rect()
                dismiss_rect.centerx = window_x + window_width // 2
                dismiss_rect.bottom = window_y + window_height - int(30 * scale_h)
                self.screen.blit(dismiss_text, dismiss_rect)
            else:
                # Подтверждение прогнания
                self._render_dismiss_confirmation(
                    window_x + window_width // 2,
                    window_y + window_height - int(80 * scale_h),
                    scale_w,
                    scale_h
                )

    def _render_companion_details(self, companion, x, y, width, scale_w, scale_h):
        """
        Отрисовка детальной информации о спутнике

        Args:
            companion: Спутник для отображения
            x, y: Координаты области
            width: Ширина области
            scale_w, scale_h: Масштабы
        """
        # Имя и ранг
        name_text = self.font.render(companion.name, True, (220, 220, 220))
        self.screen.blit(name_text, (x, y))

        y += int(35 * scale_h)

        # Ранг информация
        rank_info = companion.get_rank_info()
        rank_text = self.info_font.render(
            f"Ранг: {rank_info['name']}",
            True,
            (150, 200, 255)
        )
        self.screen.blit(rank_text, (x, y))

        y += int(25 * scale_h)

        # Описание ранга
        rank_desc = self.info_font.render(
            rank_info['description'],
            True,
            (140, 140, 140)
        )
        self.screen.blit(rank_desc, (x, y))

        y += int(35 * scale_h)

        # Разделитель
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (x, y),
            (x + width - int(20 * scale_w), y),
            1
        )

        y += int(15 * scale_h)

        # Уровень и опыт
        level_text = self.info_font.render(
            f"Уровень: {companion.level}/{companion.max_level}",
            True,
            (200, 200, 200)
        )
        self.screen.blit(level_text, (x, y))

        y += int(25 * scale_h)

        # Прогресс опыта
        exp_text = self.info_font.render(
            f"Опыт: {companion.experience}/{companion.get_experience_for_next_level()}",
            True,
            (180, 180, 180)
        )
        self.screen.blit(exp_text, (x, y))

        # Прогресс-бар опыта
        if companion.level < companion.max_level:
            y += int(25 * scale_h)
            progress_width = int(300 * scale_w)
            progress_height = int(15 * scale_h)

            pygame.draw.rect(
                self.screen,
                (50, 50, 50),
                (x, y, progress_width, progress_height)
            )

            exp_percent = companion.experience / companion.get_experience_for_next_level()
            fill_width = int(progress_width * exp_percent)

            pygame.draw.rect(
                self.screen,
                (100, 200, 100),
                (x, y, fill_width, progress_height)
            )

            pygame.draw.rect(
                self.screen,
                (100, 100, 100),
                (x, y, progress_width, progress_height),
                1
            )

        y += int(30 * scale_h)

        # Здоровье и выносливость
        health_text = self.info_font.render(
            f"Здоровье: {companion.health}/{companion.max_health}",
            True,
            (255, 100, 100)
        )
        self.screen.blit(health_text, (x, y))

        y += int(25 * scale_h)

        stamina_text = self.info_font.render(
            f"Выносливость: {companion.stamina}/{companion.max_stamina}",
            True,
            (100, 255, 100)
        )
        self.screen.blit(stamina_text, (x, y))

        y += int(35 * scale_h)

        # Разделитель
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (x, y),
            (x + width - int(20 * scale_w), y),
            1
        )

        y += int(15 * scale_h)

        # Характеристики
        stats_title = self.info_font.render("Характеристики:", True, (200, 200, 200))
        self.screen.blit(stats_title, (x, y))

        y += int(25 * scale_h)

        stats_list = [
            ('Сила', companion.strength),
            ('Ловкость', companion.dexterity),
            ('Телосложение', companion.constitution),
            ('Дух', companion.spirit),
            ('Интеллект', companion.intelligence),
            ('Удача', companion.luck)
        ]

        for stat_name, stat_value in stats_list:
            stat_text = self.info_font.render(
                f"{stat_name}: {stat_value}",
                True,
                (180, 180, 180)
            )
            self.screen.blit(stat_text, (x, y))
            y += int(22 * scale_h)

    def _render_dismiss_confirmation(self, center_x, center_y, scale_w, scale_h):
        """
        Отрисовка подтверждения прогнания спутника

        Args:
            center_x, center_y: Центр области подтверждения
            scale_w, scale_h: Масштабы
        """
        # Фон подтверждения
        confirm_width = int(400 * scale_w)
        confirm_height = int(60 * scale_h)

        pygame.draw.rect(
            self.screen,
            (60, 40, 40),
            (center_x - confirm_width // 2, center_y - confirm_height // 2,
             confirm_width, confirm_height)
        )
        pygame.draw.rect(
            self.screen,
            (200, 80, 80),
            (center_x - confirm_width // 2, center_y - confirm_height // 2,
             confirm_width, confirm_height),
            2
        )

        # Текст подтверждения
        confirm_text = self.info_font.render(
            "Вы уверены? [Y] Да  [N] Нет",
            True,
            (255, 200, 200)
        )
        text_rect = confirm_text.get_rect()
        text_rect.center = (center_x, center_y)
        self.screen.blit(confirm_text, text_rect)

    def move_selection_up(self, companion_manager):
        """Переместить выбор вверх"""
        companions = companion_manager.get_all_companions()
        if companions:
            self.selected_companion_index = (self.selected_companion_index - 1) % len(companions)
            self.show_dismiss_confirmation = False

    def move_selection_down(self, companion_manager):
        """Переместить выбор вниз"""
        companions = companion_manager.get_all_companions()
        if companions:
            self.selected_companion_index = (self.selected_companion_index + 1) % len(companions)
            self.show_dismiss_confirmation = False

    def request_dismiss(self, companion_manager):
        """Запросить прогнание текущего спутника"""
        companions = companion_manager.get_all_companions()
        if companions and not self.show_dismiss_confirmation:
            self.companion_to_dismiss = companions[self.selected_companion_index].companion_id
            self.show_dismiss_confirmation = True

    def confirm_dismiss(self, companion_manager):
        """Подтвердить прогнание спутника"""
        if self.show_dismiss_confirmation and self.companion_to_dismiss:
            companion_manager.remove_companion(self.companion_to_dismiss)
            self.show_dismiss_confirmation = False
            self.companion_to_dismiss = None

            # Корректируем выбор если нужно
            companions = companion_manager.get_all_companions()
            if companions and self.selected_companion_index >= len(companions):
                self.selected_companion_index = len(companions) - 1
            return True
        return False

    def cancel_dismiss(self):
        """Отменить прогнание спутника"""
        self.show_dismiss_confirmation = False
        self.companion_to_dismiss = None
