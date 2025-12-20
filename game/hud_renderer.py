"""
Модуль для отрисовки HUD (интерфейса игрока).

Извлечено из engine.py для уменьшения сложности.
"""
import pygame
from game.ui import UIHelper
from game.constants import COLORS
from game.core.game_context import GameContext


class HUDRenderer:
    """Класс для отрисовки HUD игрока"""

    # Определение кнопок меню
    MENU_BUTTONS = [
        {'key': 'C', 'name': 'Характеристики', 'action': 'character'},
        {'key': 'I', 'name': 'Инвентарь', 'action': 'inventory'},
        {'key': 'K', 'name': 'Умения', 'action': 'skills'},
        {'key': 'V', 'name': 'Крафт', 'action': 'crafting'},
        {'key': 'Q', 'name': 'Квесты', 'action': 'quests'},
        {'key': 'P', 'name': 'Спутники', 'action': 'companions'},
        {'key': 'F1', 'name': 'Справка', 'action': 'help'},
        {'key': 'F2', 'name': 'Читы', 'action': 'cheats'},
    ]

    def __init__(self, game):
        """
        Инициализация рендерера HUD.

        Args:
            game: Ссылка на основной объект игры
        """
        self.game = game
        self.ctx = GameContext(game)

        # Координаты для обнаружения наведения мыши
        self.status_bar_rects = {}  # {name: pygame.Rect}
        self.menu_button_rects = {}  # {action: pygame.Rect}
        self.hovered_status_bar = None
        self.hovered_menu_button = None

    @property
    def screen(self):
        return self.ctx.screen

    @property
    def font(self):
        return self.game.font

    @property
    def info_font(self):
        return self.game.info_font

    @property
    def ui_scaler(self):
        return self.game.ui_scaler

    @property
    def player(self):
        return self.ctx.player

    @property
    def sprite_manager(self):
        return self.game.sprite_manager

    def render(self):
        """Отрисовка пользовательского интерфейса"""
        # Панель внизу экрана (масштабируется под разрешение)
        ui_height = self.ui_scaler.scale_height(70)  # Уменьшена высота
        ui_y = self.ctx.window_height - ui_height

        # Фон панели
        pygame.draw.rect(
            self.screen,
            (32, 32, 32),
            (0, ui_y, self.ctx.window_width, ui_height)
        )

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            COLORS['text'],
            (0, ui_y),
            (self.ctx.window_width, ui_y),
            2
        )

        # Прогресс-бар опыта (2 пикселя во всю ширину, над панелью)
        self._render_experience_bar(ui_y)

        # Компактные полосы статусов слева
        bars_end_x = self._render_compact_status_bars(ui_y)

        # Панель умений (справа от полос статуса)
        skills_end_x = self._render_skill_panel(bars_end_x, ui_y)

        # Панель зелий (справа от панели умений)
        self._render_potion_panel(skills_end_x, ui_y)

        # Кнопки меню (справа)
        self._render_menu_buttons(ui_y)

        # Игровое время, погода и золото (справа вверху панели)
        self._render_time_weather_gold(ui_y)

        # Серия убийств (если активна)
        self._render_killstreak(ui_y)

        # Отрисовка всплывающих подсказок (в конце, чтобы они были поверх всего)
        self._render_tooltips()

    def _render_experience_bar(self, ui_y):
        """Отрисовка тонкой полосы опыта во всю ширину экрана."""
        bar_height = 3
        bar_y = ui_y - bar_height

        # Фон полосы
        pygame.draw.rect(
            self.screen,
            (20, 20, 40),
            (0, bar_y, self.ctx.window_width, bar_height)
        )

        # Заполнение опыта
        if self.player.experience_to_next_level > 0:
            exp_ratio = min(1.0, self.player.experience / self.player.experience_to_next_level)
            exp_width = int(exp_ratio * self.ctx.window_width)
            if exp_width > 0:
                pygame.draw.rect(
                    self.screen,
                    (100, 180, 255),
                    (0, bar_y, exp_width, bar_height)
                )

    def _render_compact_status_bars(self, ui_y):
        """
        Отрисовка компактных полос здоровья, маны и выносливости.
        Полосы расположены вертикально друг под другом без надписей.

        Returns:
            int: X координата конца полос для размещения следующих элементов
        """
        bar_x = self.ui_scaler.scale_width(15)
        bar_width = self.ui_scaler.scale_width(150)  # Ширина уменьшена в 2 раза
        bar_height = self.ui_scaler.scale_height(12)  # Толщина уменьшена в 1.5 раза
        bar_spacing = self.ui_scaler.scale_height(4)  # Вертикальный отступ

        # Начальная Y позиция для центрирования полос
        total_bars_height = 3 * bar_height + 2 * bar_spacing
        ui_height = self.ui_scaler.scale_height(70)
        start_y = ui_y + (ui_height - total_bars_height) // 2

        # Получаем эффективные максимумы с учетом экипировки
        effective_max_health = self.player.get_effective_max_health()
        effective_max_mana = self.player.get_effective_max_mana()
        effective_max_stamina = self.player.get_effective_max_stamina()

        # Очищаем старые rect'ы
        self.status_bar_rects.clear()

        # Полоса здоровья (красная)
        hp_y = start_y
        UIHelper.draw_rounded_progress_bar(
            self.screen,
            bar_x, hp_y, bar_width, bar_height,
            self.player.health, effective_max_health,
            bg_color=(60, 20, 20),
            fill_color=(200, 50, 50)
        )
        self.status_bar_rects['hp'] = pygame.Rect(bar_x, hp_y, bar_width, bar_height)

        # Полоса маны (синяя)
        mp_y = hp_y + bar_height + bar_spacing
        UIHelper.draw_rounded_progress_bar(
            self.screen,
            bar_x, mp_y, bar_width, bar_height,
            self.player.mana, effective_max_mana,
            bg_color=(20, 20, 60),
            fill_color=(50, 100, 200)
        )
        self.status_bar_rects['mp'] = pygame.Rect(bar_x, mp_y, bar_width, bar_height)

        # Полоса выносливости (оранжевая)
        stamina_y = mp_y + bar_height + bar_spacing
        stamina_color = (200, 120, 50) if not self.player.is_resting else (150, 70, 30)
        UIHelper.draw_rounded_progress_bar(
            self.screen,
            bar_x, stamina_y, bar_width, bar_height,
            self.player.stamina, effective_max_stamina,
            bg_color=(60, 40, 20),
            fill_color=stamina_color
        )
        self.status_bar_rects['stamina'] = pygame.Rect(bar_x, stamina_y, bar_width, bar_height)

        # Возвращаем X координату конца полос
        return bar_x + bar_width + self.ui_scaler.scale_width(15)

    def _render_time_weather_gold(self, ui_y):
        """Отрисовка времени, погоды и золота."""
        weather_str = ""
        if self.ctx.weather_system:
            weather_str = f" | {self.ctx.weather_system.current_weather.display_name}"

        time_gold_text = self.info_font.render(
            f"{self.ctx.game_time.get_time_string()}{weather_str} | Золото: {self.player.inventory.gold}",
            True,
            (255, 215, 0)
        )
        time_gold_x = self.ctx.window_width - self.ui_scaler.scale_width(350)
        self.screen.blit(time_gold_text, (time_gold_x, ui_y + 8))

    def _render_killstreak(self, ui_y):
        """Отрисовка серии убийств."""
        if self.ctx.killstreak_system and self.ctx.killstreak_system.current_streak >= 3:
            streak_text = self.info_font.render(
                f"Серия: x{self.ctx.killstreak_system.current_streak}",
                True,
                (255, 100, 100)
            )
            time_gold_x = self.ctx.window_width - self.ui_scaler.scale_width(350)
            self.screen.blit(streak_text, (time_gold_x, ui_y + 25))

    def _render_skill_panel(self, start_x, ui_y):
        """
        Отрисовка панели умений.

        Args:
            start_x: X координата начала панели
            ui_y: Y координата верха UI панели

        Returns:
            int: X координата конца панели
        """
        slot_size = self.ui_scaler.scale_value(40)  # Чуть меньше для компактности
        slot_spacing = self.ui_scaler.scale_value(4)

        ui_height = self.ui_scaler.scale_height(70)
        # Центрируем по вертикали
        panel_y = ui_y + (ui_height - slot_size - 5) // 2

        for i in range(8):
            slot_x = start_x + i * (slot_size + slot_spacing)
            skill = self.player.skill_manager.get_slot_skill(i)

            # Проверяем, доступно ли умение для использования
            is_usable = False
            if skill:
                can_use, _ = skill.can_use(self.player)
                is_usable = can_use

            # Фон и рамка слота
            bg_color, border_color = self._get_slot_colors(skill, is_usable)

            pygame.draw.rect(self.screen, bg_color, (slot_x, panel_y, slot_size, slot_size), border_radius=4)
            pygame.draw.rect(self.screen, border_color, (slot_x, panel_y, slot_size, slot_size), 2, border_radius=4)

            # Номер слота (клавиша) - маленький в углу
            small_font = pygame.font.Font(None, self.ui_scaler.scale_value(16))
            key_text = small_font.render(str(i + 1), True, (150, 150, 150))
            self.screen.blit(key_text, (slot_x + 3, panel_y + 2))

            # Если есть умение, показываем его информацию
            if skill:
                skill_id = self.player.skill_manager.get_slot_skill_id(i)
                self._render_skill_slot(skill, skill_id, slot_x, panel_y, slot_size)

            # Шкала прогресса использований для повышения ранга (под слотом)
            progress_bar_height = 2
            progress_bar_y = panel_y + slot_size + 1

            # Темный фон шкалы
            pygame.draw.rect(
                self.screen,
                (30, 30, 30),
                (slot_x, progress_bar_y, slot_size, progress_bar_height),
                border_radius=1
            )

            # Заполнение шкалы если есть умение
            if skill and skill.rank < skill.max_rank:
                required_uses = skill.get_required_uses_for_rank()
                current_uses = skill.use_count

                if required_uses > 0:
                    progress = min(1.0, current_uses / required_uses)
                    filled_width = int(slot_size * progress)

                    if filled_width > 0:
                        if progress >= 1.0:
                            bar_color = (100, 255, 100)
                        elif progress >= 0.5:
                            bar_color = (255, 215, 0)
                        else:
                            bar_color = (200, 150, 50)

                        pygame.draw.rect(
                            self.screen,
                            bar_color,
                            (slot_x, progress_bar_y, filled_width, progress_bar_height),
                            border_radius=1
                        )
            elif skill and skill.rank >= skill.max_rank:
                pygame.draw.rect(
                    self.screen,
                    (100, 150, 255),
                    (slot_x, progress_bar_y, slot_size, progress_bar_height),
                    border_radius=1
                )

        # Возвращаем X координату конца панели
        return start_x + 8 * (slot_size + slot_spacing) + self.ui_scaler.scale_width(15)

    def _get_slot_colors(self, skill, is_usable):
        """
        Получить цвета для слота умения.

        Returns:
            tuple: (bg_color, border_color)
        """
        if not skill:
            return (30, 30, 30), (100, 100, 100)

        color_map = {
            'combat': ((80, 50, 50), (40, 25, 25)),
            'magic': ((50, 50, 80), (25, 25, 40)),
            'crafting': ((70, 70, 50), (35, 35, 25)),
        }

        category = skill.category.value
        bright, dark = color_map.get(category, ((60, 60, 60), (30, 30, 30)))

        bg_color = bright if is_usable else dark
        border_color = (200, 200, 100) if is_usable else (80, 80, 80)

        return bg_color, border_color

    def _render_skill_slot(self, skill, skill_id, slot_x, panel_y, slot_size):
        """Отрисовка содержимого слота умения."""
        icon_size = slot_size - 8
        icon_x = slot_x + 4
        icon_y = panel_y + 4

        if skill_id and self.sprite_manager:
            self.sprite_manager.render_skill_icon(
                self.screen,
                skill_id,
                icon_x,
                icon_y,
                icon_size,
                fallback_text=skill.name[0]
            )
        else:
            icon_font = pygame.font.Font(None, self.ui_scaler.scale_value(24))
            icon_text = icon_font.render(skill.name[0], True, (255, 255, 255))
            icon_rect = icon_text.get_rect()
            icon_rect.center = (slot_x + slot_size // 2, panel_y + slot_size // 2 + 2)
            self.screen.blit(icon_text, icon_rect)

        # Ранг умения (маленький, в правом нижнем углу)
        small_font = pygame.font.Font(None, self.ui_scaler.scale_value(14))
        rank_text = small_font.render(f"R{skill.rank}", True, (255, 215, 0))
        self.screen.blit(rank_text, (slot_x + slot_size - 18, panel_y + slot_size - 14))

        # Перезарядка
        if skill.current_cooldown > 0:
            # Затемнение слота
            overlay = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (slot_x, panel_y))

            cooldown_font = pygame.font.Font(None, self.ui_scaler.scale_value(20))
            cooldown_text = cooldown_font.render(str(skill.current_cooldown), True, (255, 100, 100))
            cooldown_rect = cooldown_text.get_rect()
            cooldown_rect.center = (slot_x + slot_size // 2, panel_y + slot_size // 2)
            self.screen.blit(cooldown_text, cooldown_rect)

    def _render_potion_panel(self, start_x, ui_y):
        """
        Отрисовка панели быстрых зелий справа от панели умений.

        Args:
            start_x: X координата начала панели
            ui_y: Y координата верха UI панели
        """
        from game.inventory import EquipmentSlot

        belt = self.player.inventory.get_equipped_item(EquipmentSlot.BELT)
        if not belt or not hasattr(belt, 'potion_slots') or belt.potion_slots == 0:
            return

        slot_size = self.ui_scaler.scale_value(40)
        slot_spacing = self.ui_scaler.scale_value(4)

        ui_height = self.ui_scaler.scale_height(70)
        panel_y = ui_y + (ui_height - slot_size - 5) // 2

        potion_slots = [
            EquipmentSlot.BELT_POTION_1,
            EquipmentSlot.BELT_POTION_2,
            EquipmentSlot.BELT_POTION_3,
            EquipmentSlot.BELT_POTION_4
        ][:belt.potion_slots]

        if not hasattr(self, 'potion_slot_rects'):
            self.potion_slot_rects = {}

        self.potion_slot_rects.clear()

        for i, slot in enumerate(potion_slots):
            slot_x = start_x + i * (slot_size + slot_spacing)
            potion = self.player.inventory.get_equipped_item(slot)

            bg_color = (60, 40, 60) if potion else (30, 30, 30)
            border_color = (150, 100, 150) if potion else (100, 100, 100)

            pygame.draw.rect(self.screen, bg_color, (slot_x, panel_y, slot_size, slot_size), border_radius=4)
            pygame.draw.rect(self.screen, border_color, (slot_x, panel_y, slot_size, slot_size), 2, border_radius=4)

            self.potion_slot_rects[i] = (pygame.Rect(slot_x, panel_y, slot_size, slot_size), slot, potion)

            if potion:
                icon_size = slot_size - 8
                icon_x = slot_x + 4
                icon_y = panel_y + 4

                potion_name = potion.get_full_name() if hasattr(potion, 'get_full_name') else potion.name
                potion_id = potion.item_id if hasattr(potion, 'item_id') else None

                if potion_id and self.sprite_manager:
                    self.sprite_manager.render_potion_icon(
                        self.screen,
                        potion_id,
                        icon_x,
                        icon_y,
                        icon_size,
                        fallback_text=potion_name[0]
                    )
                else:
                    icon_font = pygame.font.Font(None, self.ui_scaler.scale_value(24))
                    icon_text = icon_font.render(potion_name[0], True, (200, 100, 200))
                    icon_rect = icon_text.get_rect()
                    icon_rect.center = (slot_x + slot_size // 2, panel_y + slot_size // 2 + 2)
                    self.screen.blit(icon_text, icon_rect)

                # Количество зелий
                potion_count = self.player.inventory.get_item_count(potion)
                if potion_count > 1:
                    small_font = pygame.font.Font(None, self.ui_scaler.scale_value(14))
                    count_text = small_font.render(f"x{potion_count}", True, (255, 215, 0))
                    self.screen.blit(count_text, (slot_x + slot_size - 20, panel_y + slot_size - 14))

    def _render_menu_buttons(self, ui_y):
        """Отрисовка кнопок меню с подсветкой при наведении."""
        button_width = self.ui_scaler.scale_width(30)
        button_height = self.ui_scaler.scale_height(30)
        button_spacing = self.ui_scaler.scale_width(4)

        # Начинаем справа
        start_x = self.ctx.window_width - len(self.MENU_BUTTONS) * (button_width + button_spacing) - self.ui_scaler.scale_width(15)
        ui_height = self.ui_scaler.scale_height(70)
        button_y = ui_y + ui_height - button_height - self.ui_scaler.scale_height(8)

        self.menu_button_rects.clear()

        mouse_pos = pygame.mouse.get_pos()

        for i, button in enumerate(self.MENU_BUTTONS):
            button_x = start_x + i * (button_width + button_spacing)
            rect = pygame.Rect(button_x, button_y, button_width, button_height)
            self.menu_button_rects[button['action']] = rect

            # Проверка наведения
            is_hovered = rect.collidepoint(mouse_pos)

            # Специальная обработка кнопки характеристик при наличии свободных очков
            has_stat_points = button['action'] == 'character' and self.player.stat_points > 0

            # Цвета в зависимости от наведения и наличия очков
            if has_stat_points:
                bg_color = (40, 80, 40) if not is_hovered else (60, 120, 60)
                border_color = (100, 200, 100)
            elif is_hovered:
                bg_color = (70, 70, 80)
                border_color = (150, 150, 180)
                self.hovered_menu_button = button
            else:
                bg_color = (45, 45, 55)
                border_color = (80, 80, 100)

            if is_hovered:
                self.hovered_menu_button = button

            # Фон кнопки
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=4)
            pygame.draw.rect(self.screen, border_color, rect, 1, border_radius=4)

            # Текст клавиши (или "+" для характеристик при наличии очков)
            small_font = pygame.font.Font(None, self.ui_scaler.scale_value(16))
            if has_stat_points:
                key_text = small_font.render("+", True, (100, 255, 100))
            else:
                key_text = small_font.render(button['key'], True, (200, 200, 200) if is_hovered else (150, 150, 150))
            key_rect = key_text.get_rect(center=rect.center)
            self.screen.blit(key_text, key_rect)

        # Сбрасываем hovered если ни одна кнопка не под курсором
        if not any(rect.collidepoint(mouse_pos) for rect in self.menu_button_rects.values()):
            self.hovered_menu_button = None

    def _render_tooltips(self):
        """Отрисовка всплывающих подсказок."""
        mouse_pos = pygame.mouse.get_pos()

        # Проверяем наведение на полосы статусов
        for name, rect in self.status_bar_rects.items():
            if rect.collidepoint(mouse_pos):
                tooltip_text = self._get_status_tooltip(name)
                if tooltip_text:
                    UIHelper.draw_tooltip(
                        self.screen,
                        tooltip_text,
                        mouse_pos[0] + 15,
                        mouse_pos[1] - 30,
                        self.info_font,
                        bg_color=(30, 30, 35),
                        text_color=(255, 255, 255)
                    )
                return

        # Проверяем наведение на кнопки меню
        if self.hovered_menu_button:
            button = self.hovered_menu_button
            rect = self.menu_button_rects.get(button['action'])
            if rect:
                tooltip_text = f"{button['name']} [{button['key']}]"
                UIHelper.draw_tooltip(
                    self.screen,
                    tooltip_text,
                    rect.centerx,
                    rect.top - 25,
                    self.info_font,
                    bg_color=(30, 30, 35),
                    text_color=(255, 255, 255)
                )

    def _get_status_tooltip(self, status_name):
        """Получить текст подсказки для полосы статуса."""
        if status_name == 'hp':
            effective_max = self.player.get_effective_max_health()
            percent = int((self.player.health / effective_max * 100) if effective_max > 0 else 0)
            return f"Здоровье: {self.player.health}/{effective_max} ({percent}%)"
        elif status_name == 'mp':
            effective_max = self.player.get_effective_max_mana()
            percent = int((self.player.mana / effective_max * 100) if effective_max > 0 else 0)
            return f"Мана: {self.player.mana}/{effective_max} ({percent}%)"
        elif status_name == 'stamina':
            effective_max = self.player.get_effective_max_stamina()
            percent = int((self.player.stamina / effective_max * 100) if effective_max > 0 else 0)
            status = " [ОТДЫХ]" if self.player.is_resting else ""
            return f"Выносливость: {self.player.stamina}/{effective_max} ({percent}%){status}"
        return None

    def handle_menu_button_click(self, mouse_pos):
        """
        Обработка клика по кнопке меню.

        Args:
            mouse_pos: Позиция мыши (x, y)

        Returns:
            str or None: Название действия кнопки или None если клик не по кнопке
        """
        for action, rect in self.menu_button_rects.items():
            if rect.collidepoint(mouse_pos):
                return action
        return None

    def handle_potion_click(self, mouse_pos, button):
        """
        Обработка клика по слоту зелья.

        Args:
            mouse_pos: Позиция мыши (x, y)
            button: Кнопка мыши (1 = левая, 3 = правая)

        Returns:
            tuple or None: (slot, potion) или None если клик не по слоту
        """
        if not hasattr(self, 'potion_slot_rects'):
            return None

        for i, (rect, slot, potion) in self.potion_slot_rects.items():
            if rect.collidepoint(mouse_pos):
                return (slot, potion)
        return None
