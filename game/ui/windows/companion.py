"""
Окно управления спутниками
"""
import pygame
import os
from game.ui.windows.base import BaseWindow


class CompanionWindow(BaseWindow):
    """Окно управления спутниками"""

    BASE_WIDTH = 850
    BASE_HEIGHT = 800

    def __init__(self, screen, font, info_font, scaler=None):
        super().__init__(screen, font, info_font, scaler)
        self.selected_companion_index = 0
        self.show_dismiss_confirmation = False
        self.companion_to_dismiss = None
        self.sprite_cache = {}  # Кэш загруженных спрайтов
        self._player_ref = None  # Ссылка на игрока для проверки инвентаря

    def render(self, companion_manager, player=None):
        """
        Отрисовка окна спутников

        Args:
            companion_manager: Менеджер спутников
            player: Игрок (для проверки инвентаря)
        """
        # Сохраняем ссылку на игрока
        if player:
            self._player_ref = player

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

    def _load_companion_sprite(self, sprite_path):
        """
        Загрузить спрайт спутника с кэшированием

        Args:
            sprite_path: Путь к файлу спрайта

        Returns:
            pygame.Surface: Загруженный спрайт или None
        """
        if sprite_path in self.sprite_cache:
            return self.sprite_cache[sprite_path]

        try:
            if os.path.exists(sprite_path):
                sprite = pygame.image.load(sprite_path).convert_alpha()
                self.sprite_cache[sprite_path] = sprite
                return sprite
        except:
            pass

        return None

    def _render_companion_details(self, companion, x, y, width, scale_w, scale_h):
        """
        Отрисовка детальной информации о спутнике

        Args:
            companion: Спутник для отображения
            x, y: Координаты области
            width: Ширина области
            scale_w, scale_h: Масштабы
        """
        # Имя и ранг (слева)
        name_text = self.font.render(companion.name, True, (220, 220, 220))
        self.screen.blit(name_text, (x, y))

        # Загружаем и отображаем спрайт спутника (справа)
        sprite_path = companion.get_sprite_path()
        sprite = self._load_companion_sprite(sprite_path)

        if sprite:
            sprite_size = int(64 * min(scale_w, scale_h))
            scaled_sprite = pygame.transform.scale(sprite, (sprite_size, sprite_size))
            # Размещаем спрайт в правой части блока
            sprite_x = x + width - sprite_size - int(10 * scale_w)
            self.screen.blit(scaled_sprite, (sprite_x, y))

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

        y += int(20 * scale_h)

        # Разделитель
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (x, y),
            (x + width - int(20 * scale_w), y),
            1
        )

        y += int(15 * scale_h)

        # Переключатель участия в боях
        combat_status = "АКТИВЕН" if companion.participate_in_combat else "НЕАКТИВЕН"
        combat_color = (100, 255, 100) if companion.participate_in_combat else (255, 100, 100)

        combat_label = self.info_font.render("Участие в боях:", True, (200, 200, 200))
        self.screen.blit(combat_label, (x, y))

        y += int(25 * scale_h)

        combat_status_text = self.info_font.render(
            f"Статус: {combat_status}",
            True,
            combat_color
        )
        self.screen.blit(combat_status_text, (x, y))

        y += int(25 * scale_h)

        # Кнопка переключения статуса
        button_width = int(200 * scale_w)
        button_height = int(25 * scale_h)
        button_rect = pygame.Rect(x, y, button_width, button_height)

        # Сохраняем rect кнопки для обработки кликов
        if not hasattr(self, 'combat_toggle_button'):
            self.combat_toggle_button = None
        self.combat_toggle_button = button_rect

        # Цвет кнопки
        button_color = (60, 80, 100)
        button_border = (150, 200, 255)

        pygame.draw.rect(self.screen, button_color, button_rect)
        pygame.draw.rect(self.screen, button_border, button_rect, 2)

        toggle_text = self.info_font.render(
            "Переключить участие в боях",
            True,
            (200, 200, 200)
        )
        text_rect = toggle_text.get_rect()
        text_rect.center = button_rect.center
        self.screen.blit(toggle_text, text_rect)

        # Блок взаимодействия (для волка)
        if companion.companion_type == 'wolf':
            y += int(45 * scale_h)

            # Разделитель
            pygame.draw.line(
                self.screen,
                (100, 100, 120),
                (x, y),
                (x + width - int(20 * scale_w), y),
                1
            )

            y += int(15 * scale_h)

            # Заголовок секции
            interaction_title = self.info_font.render("Взаимодействие:", True, (200, 200, 200))
            self.screen.blit(interaction_title, (x, y))

            y += int(30 * scale_h)

            # Кнопка "Накормить"
            feed_button_width = int(200 * scale_w)
            feed_button_height = int(25 * scale_h)
            feed_button_rect = pygame.Rect(x, y, feed_button_width, feed_button_height)

            # Сохраняем rect кнопки для обработки кликов
            if not hasattr(self, 'feed_button'):
                self.feed_button = None
            self.feed_button = feed_button_rect

            # Проверяем наличие мяса (оленина или медвежатина)
            has_meat = False
            meat_name = None
            if hasattr(self, '_player_ref'):
                player = self._player_ref
                if player and hasattr(player, 'inventory'):
                    # Проверяем оленину
                    deer_meat = player.inventory.get_item('venison')
                    if deer_meat and deer_meat[1] > 0:
                        has_meat = True
                        meat_name = 'venison'
                    else:
                        # Проверяем медвежатину
                        bear_meat = player.inventory.get_item('bear_meat')
                        if bear_meat and bear_meat[1] > 0:
                            has_meat = True
                            meat_name = 'bear_meat'

            # Цвет кнопки (серая если нет мяса)
            if has_meat:
                button_color = (60, 100, 60)
                button_border = (100, 200, 100)
                text_color = (200, 255, 200)
            else:
                button_color = (60, 60, 60)
                button_border = (100, 100, 100)
                text_color = (150, 150, 150)

            pygame.draw.rect(self.screen, button_color, feed_button_rect)
            pygame.draw.rect(self.screen, button_border, feed_button_rect, 2)

            feed_text = self.info_font.render(
                "[F] Накормить (мясо)",
                True,
                text_color
            )
            feed_text_rect = feed_text.get_rect()
            feed_text_rect.center = feed_button_rect.center
            self.screen.blit(feed_text, feed_text_rect)

            # Подсказка о доступности
            if not has_meat:
                y += int(30 * scale_h)
                hint_text = self.info_font.render(
                    "Требуется мясо (оленина или медвежатина)",
                    True,
                    (120, 120, 120)
                )
                self.screen.blit(hint_text, (x, y))

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

    def toggle_combat_participation(self, companion_manager):
        """Переключить участие текущего спутника в боях"""
        companions = companion_manager.get_all_companions()
        if companions and self.selected_companion_index < len(companions):
            companion = companions[self.selected_companion_index]
            companion.participate_in_combat = not companion.participate_in_combat
            return True
        return False

    def set_player_reference(self, player):
        """Установить ссылку на игрока для проверки инвентаря"""
        self._player_ref = player

    def feed_companion(self, companion_manager, player):
        """
        Накормить выбранного спутника (волка)

        Args:
            companion_manager: Менеджер спутников
            player: Игрок

        Returns:
            tuple: (success: bool, message: str)
        """
        companions = companion_manager.get_all_companions()
        if not companions or self.selected_companion_index >= len(companions):
            return False, "Спутник не выбран"

        companion = companions[self.selected_companion_index]

        # Проверяем, что это волк
        if companion.companion_type != 'wolf':
            return False, "Этот спутник не ест мясо"

        # Проверяем наличие мяса
        meat_item = None
        meat_name_display = None

        # Сначала пробуем оленину
        venison = player.inventory.get_item('venison')
        if venison and venison[1] > 0:
            meat_item = venison[0]
            meat_name_display = "оленину"
        else:
            # Затем медвежатину
            bear_meat = player.inventory.get_item('bear_meat')
            if bear_meat and bear_meat[1] > 0:
                meat_item = bear_meat[0]
                meat_name_display = "медвежатину"

        if not meat_item:
            return False, "У вас нет мяса (оленина или медвежатина)"

        # Убираем 1 единицу мяса из инвентаря
        if not player.inventory.remove_item(meat_item, 1):
            return False, "Не удалось использовать мясо"

        # Восстанавливаем 30% здоровья и выносливости
        old_health = companion.health
        old_stamina = companion.stamina

        health_restore = int(companion.max_health * 0.3)
        stamina_restore = int(companion.max_stamina * 0.3)

        companion.health = min(companion.max_health, companion.health + health_restore)
        companion.stamina = min(companion.max_stamina, companion.stamina + stamina_restore)

        actual_health = companion.health - old_health
        actual_stamina = companion.stamina - old_stamina

        return True, f"Вы накормили {companion.name} ({meat_name_display}). Восстановлено: {actual_health} здоровья, {actual_stamina} выносливости."
