"""
Модуль UI компонентов для игры
Содержит все интерфейсные окна и элементы
"""
import pygame
from game.constants import COLORS, BASE_WIDTH, BASE_HEIGHT
from game.inventory import EquipmentSlot, EquipmentItem


class UIScaler:
    """Класс для масштабирования UI элементов под разные разрешения экрана"""

    def __init__(self, screen_width, screen_height):
        """
        Инициализация масштабировщика

        Args:
            screen_width: Фактическая ширина экрана
            screen_height: Фактическая высота экрана
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Вычисляем коэффициенты масштабирования
        self.scale_x = screen_width / BASE_WIDTH
        self.scale_y = screen_height / BASE_HEIGHT

        # Используем минимальный коэффициент для сохранения пропорций
        self.scale = min(self.scale_x, self.scale_y)

    def scale_value(self, value):
        """Масштабировать одиночное значение"""
        return int(value * self.scale)

    def scale_width(self, width):
        """Масштабировать ширину"""
        return int(width * self.scale_x)

    def scale_height(self, height):
        """Масштабировать высоту"""
        return int(height * self.scale_y)

    def scale_pos(self, x, y):
        """Масштабировать позицию (x, y)"""
        return int(x * self.scale_x), int(y * self.scale_y)

    def scale_rect(self, x, y, width, height):
        """Масштабировать прямоугольник"""
        return (
            int(x * self.scale_x),
            int(y * self.scale_y),
            int(width * self.scale_x),
            int(height * self.scale_y)
        )

    def scale_font_size(self, base_size):
        """Масштабировать размер шрифта"""
        return max(12, int(base_size * self.scale))

    def get_centered_x(self, width):
        """Получить X координату для центрирования элемента"""
        return (self.screen_width - width) // 2

    def get_centered_y(self, height):
        """Получить Y координату для центрирования элемента"""
        return (self.screen_height - height) // 2


class UIHelper:
    """Вспомогательные методы для UI"""

    @staticmethod
    def draw_panel(surface, x, y, width, height, color=(40, 40, 45), border_color=(100, 100, 120), border_width=2):
        """
        Отрисовка панели с рамкой

        Args:
            surface: Поверхность для рисования
            x, y: Координаты
            width, height: Размеры
            color: Цвет фона
            border_color: Цвет рамки
            border_width: Толщина рамки
        """
        # Фон панели
        pygame.draw.rect(surface, color, (x, y, width, height))
        # Рамка
        pygame.draw.rect(surface, border_color, (x, y, width, height), border_width)

    @staticmethod
    def draw_gradient_rect(surface, x, y, width, height, color1, color2, vertical=True):
        """
        Отрисовка прямоугольника с градиентом

        Args:
            surface: Поверхность для рисования
            x, y: Координаты
            width, height: Размеры
            color1, color2: Цвета градиента
            vertical: Вертикальный или горизонтальный градиент
        """
        if vertical:
            for i in range(height):
                ratio = i / height
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (x, y + i), (x + width, y + i))
        else:
            for i in range(width):
                ratio = i / width
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (x + i, y), (x + i, y + height))

    @staticmethod
    def draw_progress_bar(surface, x, y, width, height, current, maximum,
                          bg_color=(40, 40, 40), fill_color=(100, 200, 100),
                          border_color=(200, 200, 200), text=None, font=None):
        """
        Отрисовка полосы прогресса

        Args:
            surface: Поверхность для рисования
            x, y: Координаты
            width, height: Размеры
            current, maximum: Текущее и максимальное значение
            bg_color: Цвет фона
            fill_color: Цвет заполнения
            border_color: Цвет рамки
            text: Текст для отображения
            font: Шрифт для текста
        """
        # Фон
        pygame.draw.rect(surface, bg_color, (x, y, width, height))

        # Заполнение
        if maximum > 0:
            fill_width = int((current / maximum) * width)
            pygame.draw.rect(surface, fill_color, (x, y, fill_width, height))

        # Рамка
        pygame.draw.rect(surface, border_color, (x, y, width, height), 1)

        # Текст
        if text and font:
            text_surface = font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.center = (x + width // 2, y + height // 2)
            surface.blit(text_surface, text_rect)


class HelpWindow:
    """Окно помощи (F1)"""

    def __init__(self, screen, font, info_font, scaler=None):
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.scaler = scaler
        self.is_open = False

        self.help_data = [
            ("=== УПРАВЛЕНИЕ ===", None),
            ("Перемещение:", "W/A/S/D или Стрелки"),
            ("Отдых:", "R - восстановить здоровье и ману"),
            ("Работа:", "T - получить опыт и золото"),
            ("Взаимодействие:", "E - разговор с NPC"),
            ("Сбор ресурсов:", "F - собрать лут с локации"),
            ("Инвентарь:", "I - открыть/закрыть"),
            ("Характеристики:", "C - открыть окно персонажа"),
            ("Помощь:", "F1 - открыть/закрыть это окно"),
            ("Выход:", "ESC - выйти из игры"),
            ("", None),
            ("=== ИНВЕНТАРЬ ===", None),
            ("Навигация:", "W/S - выбор предмета"),
            ("Использовать:", "Enter/U - использовать предмет"),
            ("Экипировать:", "E - экипировать предмет"),
            ("Снять предмет:", "ПКМ - снять экипированный предмет"),
            ("Надеть предмет:", "ПКМ - экипировать из инвентаря"),
            ("Информация:", "Наведите мышь на предмет"),
            ("Закрыть:", "I/ESC - закрыть инвентарь"),
            ("", None),
            ("=== ВЗАИМОДЕЙСТВИЕ С NPC ===", None),
            ("Меню выбора:", "[1] Торговля, [2] Агрессия, [3] Уйти"),
            ("", None),
            ("=== ТОРГОВЛЯ ===", None),
            ("Режим покупки:", "Tab - переключить на продажу"),
            ("Режим продажи:", "Tab - переключить на покупку"),
            ("Навигация:", "W/S - выбор товара"),
            ("Подтвердить:", "Enter - купить/продать"),
            ("Закрыть:", "ESC - закрыть окно торговли"),
            ("", None),
            ("=== БОЙ ===", None),
            ("Атака:", "1 - обычная атака"),
            ("Побег:", "2 - попытка сбежать"),
        ]

    def toggle(self):
        """Переключить состояние окна"""
        self.is_open = not self.is_open

    def render(self):
        """Отрисовка окна помощи"""
        if not self.is_open:
            return

        # Получаем размеры экрана
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные)
        if self.scaler:
            window_width = self.scaler.scale_width(700)
            window_height = self.scaler.scale_height(600)
        else:
            window_width = min(700, int(screen_width * 0.7))
            window_height = min(600, int(screen_height * 0.7))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна с градиентом
        UIHelper.draw_gradient_rect(
            self.screen, window_x, window_y, window_width, window_height,
            (30, 30, 40), (50, 50, 65)
        )

        # Рамка
        pygame.draw.rect(
            self.screen,
            (150, 150, 200),
            (window_x, window_y, window_width, window_height),
            3
        )

        # Заголовок
        title_text = self.font.render("СПРАВКА", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + int(15 * (window_height / 600))
        self.screen.blit(title_text, title_rect)

        # Подзаголовок
        subtitle = self.info_font.render("Нажмите F1 для закрытия", True, (180, 180, 180))
        subtitle_rect = subtitle.get_rect()
        subtitle_rect.centerx = window_x + window_width // 2
        subtitle_rect.y = window_y + int(45 * (window_height / 600))
        self.screen.blit(subtitle, subtitle_rect)

        # Разделитель
        separator_y = int(70 * (window_height / 600))
        pygame.draw.line(
            self.screen,
            (100, 100, 150),
            (window_x + int(20 * (window_width / 700)), window_y + separator_y),
            (window_x + window_width - int(20 * (window_width / 700)), window_y + separator_y),
            2
        )

        # Содержимое в двух столбцах
        content_y_left = window_y + int(85 * (window_height / 600))
        content_y_right = content_y_left
        line_height = max(16, int(18 * (window_height / 600)))

        margin_left = int(20 * (window_width / 700))
        margin_left_text = int(35 * (window_width / 700))
        value_offset = int(180 * (window_width / 700))

        # Разделяем данные на два столбца
        column_width = (window_width - int(60 * (window_width / 700))) // 2
        right_column_x = window_x + column_width + int(40 * (window_width / 700))

        # Определяем точку разделения (половина данных в каждом столбце)
        split_index = len(self.help_data) // 2
        left_data = self.help_data[:split_index]
        right_data = self.help_data[split_index:]

        # Отрисовка левого столбца
        for label, value in left_data:
            if label.startswith("==="):
                section_text = self.font.render(label, True, (100, 200, 255))
                self.screen.blit(section_text, (window_x + margin_left, content_y_left))
                content_y_left += line_height + int(4 * (window_height / 600))
            elif label == "":
                content_y_left += int(8 * (window_height / 600))
            else:
                label_text = self.info_font.render(label, True, (200, 200, 200))
                self.screen.blit(label_text, (window_x + margin_left_text, content_y_left))
                if value:
                    value_text = self.info_font.render(value, True, (150, 255, 150))
                    self.screen.blit(value_text, (window_x + value_offset, content_y_left))
                content_y_left += line_height

        # Отрисовка правого столбца
        for label, value in right_data:
            if label.startswith("==="):
                section_text = self.font.render(label, True, (100, 200, 255))
                self.screen.blit(section_text, (right_column_x, content_y_right))
                content_y_right += line_height + int(4 * (window_height / 600))
            elif label == "":
                content_y_right += int(8 * (window_height / 600))
            else:
                label_text = self.info_font.render(label, True, (200, 200, 200))
                self.screen.blit(label_text, (right_column_x + int(15 * (window_width / 700)), content_y_right))
                if value:
                    value_text = self.info_font.render(value, True, (150, 255, 150))
                    # Уменьшаем смещение для правого столбца
                    self.screen.blit(value_text, (right_column_x + int(160 * (window_width / 700)), content_y_right))
                content_y_right += line_height


class InventoryWindow:
    """Улучшенное окно инвентаря с экипировкой"""

    def __init__(self, screen, font, info_font, scaler=None):
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.scaler = scaler
        self.selected_inventory_index = 0
        self.selected_equipment_slot = None
        self.mode = "inventory"  # "inventory" или "equipment"

    def render(self, player, mouse_pos=None):
        """
        Отрисовка окна инвентаря

        Args:
            player: Объект игрока
            mouse_pos: Позиция мыши (x, y) для tooltip
        """
        # Получаем размеры экрана
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные)
        if self.scaler:
            window_width = self.scaler.scale_width(900)
            window_height = self.scaler.scale_height(650)
        else:
            window_width = min(900, int(screen_width * 0.85))
            window_height = min(650, int(screen_height * 0.75))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна с градиентом
        UIHelper.draw_gradient_rect(
            self.screen, window_x, window_y, window_width, window_height,
            (35, 35, 45), (55, 55, 70)
        )

        # Рамка
        pygame.draw.rect(
            self.screen,
            (120, 120, 150),
            (window_x, window_y, window_width, window_height),
            3
        )

        # Заголовок
        title_text = self.font.render("ИНВЕНТАРЬ И ЭКИПИРОВКА", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + int(10 * (window_height / 650))
        self.screen.blit(title_text, title_rect)

        # Информация о золоте и весе
        gold_text = self.info_font.render(
            f"Золото: {player.inventory.gold}  |  Вес: {player.inventory.current_weight}/{player.inventory.max_weight} кг",
            True,
            (255, 215, 0)
        )
        gold_rect = gold_text.get_rect()
        gold_rect.centerx = window_x + window_width // 2
        gold_rect.y = window_y + int(40 * (window_height / 650))
        self.screen.blit(gold_text, gold_rect)

        # Разделитель
        separator_y = int(70 * (window_height / 650))
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (window_x + int(10 * (window_width / 900)), window_y + separator_y),
            (window_x + window_width - int(10 * (window_width / 900)), window_y + separator_y),
            2
        )

        # Левая панель - экипировка (адаптивные размеры)
        margin = int(20 * (window_width / 900))
        panel_y_offset = int(85 * (window_height / 650))
        equipment_panel_x = window_x + margin
        equipment_panel_y = window_y + panel_y_offset
        equipment_panel_width = int(400 * (window_width / 900))
        equipment_panel_height = int(500 * (window_height / 650))

        self._render_equipment_panel(
            player,
            equipment_panel_x,
            equipment_panel_y,
            equipment_panel_width,
            equipment_panel_height
        )

        # Правая панель - предметы (адаптивные размеры)
        inventory_panel_x = window_x + int(440 * (window_width / 900))
        inventory_panel_y = window_y + panel_y_offset
        inventory_panel_width = int(440 * (window_width / 900))
        inventory_panel_height = int(500 * (window_height / 650))

        self._render_inventory_panel(
            player,
            inventory_panel_x,
            inventory_panel_y,
            inventory_panel_width,
            inventory_panel_height
        )

        # Подсказки внизу
        hints_y = window_y + window_height - int(40 * (window_height / 650))
        hint_text = self.info_font.render(
            "W/S - выбор | E - экипировать | ПКМ - снять/надеть | U - использовать | I/ESC - закрыть",
            True,
            (180, 180, 180)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = hints_y
        self.screen.blit(hint_text, hint_rect)

        # Отрисовка tooltip при наведении мыши
        if mouse_pos:
            mouse_x, mouse_y = mouse_pos
            item = self.get_item_at_mouse(player, mouse_x, mouse_y)
            if item:
                self.render_item_tooltip(item, mouse_x, mouse_y)

    def _render_equipment_panel(self, player, x, y, width, height):
        """Отрисовка панели экипировки"""
        # Фон панели
        UIHelper.draw_panel(self.screen, x, y, width, height, (45, 45, 55), (100, 100, 120))

        # Заголовок (адаптивный отступ)
        title = self.font.render("Экипировка", True, (150, 200, 255))
        self.screen.blit(title, (x + int(10 * (width / 400)), y + int(5 * (height / 500))))

        # Слоты экипировки (адаптивные размеры)
        slot_y = y + int(40 * (height / 500))
        slot_height = max(18, int(22 * (height / 500)))

        # Группировка слотов
        slot_groups = [
            ("Оружие", [EquipmentSlot.WEAPON]),
            ("Доспехи", [EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET]),
            ("Кольца", [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]),
            ("Украшения", [EquipmentSlot.AMULET, EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]),
        ]

        slot_names = {
            EquipmentSlot.WEAPON: "Оружие",
            EquipmentSlot.HEAD: "Голова",
            EquipmentSlot.CHEST: "Торс",
            EquipmentSlot.HANDS: "Руки",
            EquipmentSlot.FEET: "Ноги",
            EquipmentSlot.RING_1: "Кольцо 1",
            EquipmentSlot.RING_2: "Кольцо 2",
            EquipmentSlot.RING_3: "Кольцо 3",
            EquipmentSlot.RING_4: "Кольцо 4",
            EquipmentSlot.AMULET: "Амулет",
            EquipmentSlot.BRACELET_1: "Браслет 1",
            EquipmentSlot.BRACELET_2: "Браслет 2",
        }

        # Адаптивные отступы
        margin_left = int(15 * (width / 400))
        margin_sides = int(30 * (width / 400))
        text_offset = int(130 * (width / 400))
        text_margin = int(20 * (width / 400))

        for group_name, slots in slot_groups:
            # Название группы
            group_text = self.info_font.render(f"[{group_name}]", True, (180, 180, 200))
            self.screen.blit(group_text, (x + margin_left, slot_y))
            slot_y += max(16, int(20 * (height / 500)))

            for slot in slots:
                item = player.inventory.get_equipped_item(slot)

                # Фон слота
                slot_color = (60, 60, 70) if item else (40, 40, 50)
                pygame.draw.rect(
                    self.screen,
                    slot_color,
                    (x + margin_left, slot_y, width - margin_sides, slot_height - 2)
                )

                # Рамка слота
                border_color = (100, 150, 200) if self.selected_equipment_slot == slot else (80, 80, 90)
                pygame.draw.rect(
                    self.screen,
                    border_color,
                    (x + margin_left, slot_y, width - margin_sides, slot_height - 2),
                    2 if self.selected_equipment_slot == slot else 1
                )

                # Название слота
                slot_name_text = self.info_font.render(
                    f"{slot_names[slot]}:",
                    True,
                    (150, 150, 150)
                )
                self.screen.blit(slot_name_text, (x + text_margin, slot_y + int(8 * (height / 500))))

                # Экипированный предмет
                if item:
                    item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
                    item_text = self.info_font.render(
                        item_name[:30],
                        True,
                        item.quality.color if hasattr(item, 'quality') else (200, 200, 200)
                    )
                    self.screen.blit(item_text, (x + text_offset, slot_y + int(8 * (height / 500))))
                else:
                    empty_text = self.info_font.render("---", True, (100, 100, 100))
                    self.screen.blit(empty_text, (x + text_offset, slot_y + int(8 * (height / 500))))

                slot_y += slot_height

            slot_y += max(6, int(8 * (height / 500)))

    def _render_inventory_panel(self, player, x, y, width, height):
        """Отрисовка панели предметов"""
        # Фон панели
        UIHelper.draw_panel(self.screen, x, y, width, height, (45, 45, 55), (100, 100, 120))

        # Заголовок (адаптивные отступы)
        title = self.font.render("Предметы", True, (150, 200, 255))
        self.screen.blit(title, (x + int(10 * (width / 440)), y + int(5 * (height / 500))))

        # Информация о слотах
        all_items = player.inventory.get_all_items()
        slots_text = self.info_font.render(
            f"Слотов: {len(all_items)}/{player.inventory.max_slots}",
            True,
            (180, 180, 180)
        )
        self.screen.blit(slots_text, (x + width - int(150 * (width / 440)), y + int(10 * (height / 500))))

        # Список предметов
        if not all_items:
            empty_text = self.info_font.render("Инвентарь пуст", True, (150, 150, 150))
            empty_rect = empty_text.get_rect()
            empty_rect.centerx = x + width // 2
            empty_rect.y = y + int(100 * (height / 500))
            self.screen.blit(empty_text, empty_rect)
        else:
            items_y = y + int(40 * (height / 500))
            item_height = max(24, int(30 * (height / 500)))
            max_visible_items = max(10, int(14 * (height / 500)))
            start_index = max(0, self.selected_inventory_index - max_visible_items + 1)
            end_index = min(len(all_items), start_index + max_visible_items)

            # Адаптивные отступы
            margin_h = int(10 * (width / 440))
            margin_sides = int(20 * (width / 440))
            text_margin = int(20 * (width / 440))
            weight_offset = int(120 * (width / 440))
            value_offset = int(60 * (width / 440))

            for i in range(start_index, end_index):
                item, quantity = all_items[i]
                display_index = i - start_index

                # Цвет фона для выбранного предмета
                if i == self.selected_inventory_index:
                    pygame.draw.rect(
                        self.screen,
                        (80, 80, 100),
                        (x + margin_h, items_y + display_index * item_height, width - margin_sides, item_height - 2)
                    )

                # Рамка предмета
                if i == self.selected_inventory_index:
                    pygame.draw.rect(
                        self.screen,
                        (120, 150, 200),
                        (x + margin_h, items_y + display_index * item_height, width - margin_sides, item_height - 2),
                        2
                    )

                # Название и количество
                item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
                item_color = item.quality.color if hasattr(item, 'quality') else (200, 200, 200)

                item_text = self.info_font.render(
                    f"{item_name} x{quantity}",
                    True,
                    item_color if i != self.selected_inventory_index else (255, 255, 255)
                )
                self.screen.blit(item_text, (x + text_margin, items_y + display_index * item_height + int(7 * (height / 500))))

                # Вес
                weight_text = self.info_font.render(
                    f"{item.weight * quantity:.1f}кг",
                    True,
                    (150, 150, 150)
                )
                self.screen.blit(weight_text, (x + width - weight_offset, items_y + display_index * item_height + int(7 * (height / 500))))

                # Стоимость
                value_text = self.info_font.render(
                    f"{item.value}з",
                    True,
                    (255, 215, 0)
                )
                self.screen.blit(value_text, (x + width - value_offset, items_y + display_index * item_height + int(7 * (height / 500))))

    def render_item_tooltip(self, item, mouse_x, mouse_y):
        """
        Отрисовка всплывающей подсказки для предмета

        Args:
            item: Предмет для отображения
            mouse_x: X координата мыши
            mouse_y: Y координата мыши
        """
        from game.inventory import EquipmentItem, WeaponItem, ArmorItem, JewelryItem, PotionItem

        # Размеры подсказки
        tooltip_width = 320
        tooltip_padding = 12
        line_height = 22

        # Собираем информацию о предмете
        lines = []

        # Название предмета
        item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
        item_color = item.quality.color if hasattr(item, 'quality') else (200, 200, 200)
        lines.append((item_name, item_color, True))  # True = жирный шрифт

        # Тип предмета
        if isinstance(item, WeaponItem):
            lines.append((f"Тип: {item.weapon_type}", (180, 180, 180), False))
        elif isinstance(item, ArmorItem):
            lines.append((f"Тип: {item.armor_type}", (180, 180, 180), False))
        elif isinstance(item, JewelryItem):
            lines.append((f"Тип: {item.jewelry_type}", (180, 180, 180), False))
        elif isinstance(item, PotionItem):
            lines.append(("Тип: Зелье", (180, 180, 180), False))

        # Характеристики экипировки
        if isinstance(item, EquipmentItem):
            lines.append(("", (0, 0, 0), False))  # Пустая строка

            if hasattr(item, 'attack') and item.attack > 0:
                lines.append((f"Атака: +{item.attack}", (255, 100, 100), False))
            if hasattr(item, 'defense') and item.defense > 0:
                lines.append((f"Защита: +{item.defense}", (100, 150, 255), False))

            # Бонусы к характеристикам
            if item.stats_bonus:
                for stat, bonus in item.stats_bonus.items():
                    stat_names = {
                        'strength': 'Сила',
                        'dexterity': 'Ловкость',
                        'intelligence': 'Интеллект',
                        'vitality': 'Телосложение',
                        'luck': 'Удача'
                    }
                    stat_name = stat_names.get(stat, stat)
                    lines.append((f"{stat_name}: +{bonus}", (150, 255, 150), False))

        # Эффекты зелья
        if isinstance(item, PotionItem):
            lines.append(("", (0, 0, 0), False))
            if hasattr(item, 'health_restore') and item.health_restore > 0:
                lines.append((f"Восстановление HP: +{item.health_restore}", (100, 255, 100), False))
            if hasattr(item, 'mana_restore') and item.mana_restore > 0:
                lines.append((f"Восстановление маны: +{item.mana_restore}", (100, 150, 255), False))
            if hasattr(item, 'stamina_restore') and item.stamina_restore > 0:
                lines.append((f"Восстановление выносливости: +{item.stamina_restore}", (255, 255, 100), False))

        # Вес и стоимость
        lines.append(("", (0, 0, 0), False))
        lines.append((f"Вес: {item.weight:.1f} кг", (200, 200, 200), False))
        lines.append((f"Стоимость: {item.value} золота", (255, 215, 0), False))

        # Описание
        if hasattr(item, 'description') and item.description:
            lines.append(("", (0, 0, 0), False))
            lines.append((item.description, (150, 150, 150), False))

        # Вычисляем высоту подсказки
        tooltip_height = tooltip_padding * 2 + len(lines) * line_height

        # Позиция подсказки (справа от курсора, но в пределах экрана)
        tooltip_x = mouse_x + 15
        tooltip_y = mouse_y + 15

        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = mouse_x - tooltip_width - 15
        if tooltip_y + tooltip_height > screen_height:
            tooltip_y = screen_height - tooltip_height - 5

        # Фон подсказки с градиентом
        UIHelper.draw_gradient_rect(
            self.screen, tooltip_x, tooltip_y, tooltip_width, tooltip_height,
            (40, 40, 50), (60, 60, 75)
        )

        # Рамка
        pygame.draw.rect(
            self.screen,
            (150, 150, 200),
            (tooltip_x, tooltip_y, tooltip_width, tooltip_height),
            2
        )

        # Отрисовка текста
        text_y = tooltip_y + tooltip_padding
        for line_text, line_color, is_bold in lines:
            if line_text == "":  # Пустая строка
                text_y += line_height // 2
                continue

            font_to_use = self.font if is_bold else self.info_font
            text_surface = font_to_use.render(line_text, True, line_color)
            self.screen.blit(text_surface, (tooltip_x + tooltip_padding, text_y))
            text_y += line_height

    def get_item_at_mouse(self, player, mouse_x, mouse_y):
        """
        Получить предмет под курсором мыши

        Args:
            player: Объект игрока
            mouse_x: X координата мыши
            mouse_y: Y координата мыши

        Returns:
            Item или None
        """
        # Получаем размеры экрана
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Размеры окна (адаптивные)
        if self.scaler:
            window_width = self.scaler.scale_width(900)
            window_height = self.scaler.scale_height(650)
        else:
            window_width = min(900, int(screen_width * 0.85))
            window_height = min(650, int(screen_height * 0.75))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Правая панель - предметы
        margin = int(20 * (window_width / 900))
        panel_y_offset = int(85 * (window_height / 650))
        inventory_panel_x = window_x + int(440 * (window_width / 900))
        inventory_panel_y = window_y + panel_y_offset
        inventory_panel_width = int(440 * (window_width / 900))
        inventory_panel_height = int(500 * (window_height / 650))

        # Проверяем, находится ли курсор в области предметов
        if not (inventory_panel_x <= mouse_x <= inventory_panel_x + inventory_panel_width and
                inventory_panel_y <= mouse_y <= inventory_panel_y + inventory_panel_height):
            return None

        # Вычисляем индекс предмета
        all_items = player.inventory.get_all_items()
        if not all_items:
            return None

        items_y = inventory_panel_y + int(40 * (inventory_panel_height / 500))
        item_height = max(24, int(30 * (inventory_panel_height / 500)))
        max_visible_items = max(10, int(14 * (inventory_panel_height / 500)))

        relative_y = mouse_y - items_y
        if relative_y < 0:
            return None

        item_index = int(relative_y / item_height)
        start_index = max(0, self.selected_inventory_index - max_visible_items + 1)
        actual_index = start_index + item_index

        if 0 <= actual_index < len(all_items):
            item, quantity = all_items[actual_index]
            return item

        return None


class TradeWindow:
    """Окно торговли с NPC"""

    def __init__(self, screen, font, info_font, scaler=None):
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.scaler = scaler
        self.selected_merchant_index = 0
        self.selected_player_index = 0
        self.mode = "buy"  # "buy" или "sell"

    def render(self, player, merchant):
        """
        Отрисовка окна торговли

        Args:
            player: Объект игрока
            merchant: Объект торговца
        """
        # Получаем размеры экрана
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные)
        if self.scaler:
            window_width = self.scaler.scale_width(900)
            window_height = self.scaler.scale_height(650)
        else:
            window_width = min(900, int(screen_width * 0.85))
            window_height = min(650, int(screen_height * 0.75))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна с градиентом
        UIHelper.draw_gradient_rect(
            self.screen, window_x, window_y, window_width, window_height,
            (35, 35, 45), (55, 55, 70)
        )

        # Рамка
        pygame.draw.rect(
            self.screen,
            (120, 120, 150),
            (window_x, window_y, window_width, window_height),
            3
        )

        # Коэффициенты масштабирования для адаптивности
        scale_w = window_width / 900
        scale_h = window_height / 650

        # Заголовок
        title_text = self.font.render(f"ТОРГОВЛЯ: {merchant.name}", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + int(10 * scale_h)
        self.screen.blit(title_text, title_rect)

        # Информация о золоте
        player_gold = self.info_font.render(
            f"Ваше золото: {player.inventory.gold}",
            True,
            (255, 215, 0)
        )
        self.screen.blit(player_gold, (window_x + int(50 * scale_w), window_y + int(45 * scale_h)))

        merchant_gold = self.info_font.render(
            f"Золото торговца: {merchant.inventory.gold if hasattr(merchant, 'inventory') else '???'}",
            True,
            (255, 215, 0)
        )
        self.screen.blit(merchant_gold, (window_x + window_width - int(300 * scale_w), window_y + int(45 * scale_h)))

        # Разделитель
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (window_x + int(10 * scale_w), window_y + int(75 * scale_h)),
            (window_x + window_width - int(10 * scale_w), window_y + int(75 * scale_h)),
            2
        )

        # Переключатель режима
        mode_y = window_y + int(90 * scale_h)
        buy_color = (100, 200, 100) if self.mode == "buy" else (100, 100, 100)
        sell_color = (200, 100, 100) if self.mode == "sell" else (100, 100, 100)

        buy_button = self.font.render("[TAB] ПОКУПКА", True, buy_color)
        sell_button = self.font.render("ПРОДАЖА", True, sell_color)

        self.screen.blit(buy_button, (window_x + int(50 * scale_w), mode_y))
        self.screen.blit(sell_button, (window_x + window_width - int(200 * scale_w), mode_y))

        # Панели товаров
        goods_y = window_y + int(130 * scale_h)
        goods_height = int(440 * scale_h)

        if self.mode == "buy":
            self._render_merchant_goods(merchant, window_x + int(30 * scale_w), goods_y, window_width - int(60 * scale_w), goods_height)
        else:
            self._render_player_goods(player, window_x + int(30 * scale_w), goods_y, window_width - int(60 * scale_w), goods_height)

        # Подсказки
        hints_y = window_y + window_height - int(35 * scale_h)
        if self.mode == "buy":
            hint = "W/S - выбор | Enter - купить | Tab - режим продажи | ESC - закрыть"
        else:
            hint = "W/S - выбор | Enter - продать | Tab - режим покупки | ESC - закрыть"

        hint_text = self.info_font.render(hint, True, (180, 180, 180))
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = hints_y
        self.screen.blit(hint_text, hint_rect)

    def _render_merchant_goods(self, merchant, x, y, width, height):
        """Отрисовка товаров торговца"""
        # Заголовок
        title = self.font.render("Товары торговца", True, (150, 200, 255))
        self.screen.blit(title, (x, y))

        # Проверяем наличие инвентаря у торговца
        if not hasattr(merchant, 'inventory'):
            no_goods = self.info_font.render("У торговца нет товаров", True, (150, 150, 150))
            self.screen.blit(no_goods, (x + width // 2 - 100, y + height // 2))
            return

        items = merchant.inventory.get_all_items()

        if not items:
            no_goods = self.info_font.render("Товары закончились", True, (150, 150, 150))
            self.screen.blit(no_goods, (x + width // 2 - 100, y + height // 2))
            return

        # Список товаров
        items_y = y + 35
        item_height = 28
        max_visible = 14

        start_index = max(0, self.selected_merchant_index - max_visible + 1)
        end_index = min(len(items), start_index + max_visible)

        for i in range(start_index, end_index):
            item, quantity = items[i]
            display_index = i - start_index

            # Фон выбранного предмета
            if i == self.selected_merchant_index:
                pygame.draw.rect(
                    self.screen,
                    (80, 100, 80),
                    (x, items_y + display_index * item_height, width, item_height - 2)
                )
                pygame.draw.rect(
                    self.screen,
                    (120, 200, 120),
                    (x, items_y + display_index * item_height, width, item_height - 2),
                    2
                )

            # Название предмета
            item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
            item_color = item.quality.color if hasattr(item, 'quality') else (200, 200, 200)

            name_text = self.info_font.render(
                f"{item_name} x{quantity}",
                True,
                item_color
            )
            self.screen.blit(name_text, (x + 10, items_y + display_index * item_height + 5))

            # Цена (наценка 50%)
            buy_price = int(item.value * 1.5)
            price_text = self.info_font.render(
                f"{buy_price}з",
                True,
                (255, 215, 0)
            )
            self.screen.blit(price_text, (x + width - 80, items_y + display_index * item_height + 5))

    def _render_player_goods(self, player, x, y, width, height):
        """Отрисовка товаров игрока для продажи"""
        # Заголовок
        title = self.font.render("Ваши товары", True, (200, 150, 150))
        self.screen.blit(title, (x, y))

        items = player.inventory.get_all_items()

        if not items:
            no_goods = self.info_font.render("У вас нет товаров для продажи", True, (150, 150, 150))
            self.screen.blit(no_goods, (x + width // 2 - 120, y + height // 2))
            return

        # Список товаров
        items_y = y + 35
        item_height = 28
        max_visible = 14

        start_index = max(0, self.selected_player_index - max_visible + 1)
        end_index = min(len(items), start_index + max_visible)

        for i in range(start_index, end_index):
            item, quantity = items[i]
            display_index = i - start_index

            # Фон выбранного предмета
            if i == self.selected_player_index:
                pygame.draw.rect(
                    self.screen,
                    (100, 80, 80),
                    (x, items_y + display_index * item_height, width, item_height - 2)
                )
                pygame.draw.rect(
                    self.screen,
                    (200, 120, 120),
                    (x, items_y + display_index * item_height, width, item_height - 2),
                    2
                )

            # Название предмета
            item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
            item_color = item.quality.color if hasattr(item, 'quality') else (200, 200, 200)

            name_text = self.info_font.render(
                f"{item_name} x{quantity}",
                True,
                item_color
            )
            self.screen.blit(name_text, (x + 10, items_y + display_index * item_height + 5))

            # Цена продажи (70% от стоимости)
            sell_price = int(item.value * 0.7)
            price_text = self.info_font.render(
                f"{sell_price}з",
                True,
                (255, 215, 0)
            )
            self.screen.blit(price_text, (x + width - 80, items_y + display_index * item_height + 5))


class CharacterWindow:
    """Окно характеристик персонажа"""

    def __init__(self, screen, font, info_font, scaler=None):
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.scaler = scaler
        self.selected_stat_index = 0

        # Список характеристик для навигации
        self.stats_list = [
            ('strength', 'Сила'),
            ('dexterity', 'Ловкость'),
            ('constitution', 'Телосложение'),
            ('spirit', 'Дух'),
            ('intelligence', 'Интеллект'),
            ('luck', 'Удача')
        ]

    def render(self, player):
        """
        Отрисовка окна характеристик

        Args:
            player: Объект игрока
        """
        # Получаем размеры экрана
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные)
        if self.scaler:
            window_width = self.scaler.scale_width(700)
            window_height = self.scaler.scale_height(600)
        else:
            window_width = min(700, int(screen_width * 0.7))
            window_height = min(600, int(screen_height * 0.7))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Коэффициенты масштабирования
        scale_w = window_width / 700
        scale_h = window_height / 600

        # Фон окна с градиентом
        UIHelper.draw_gradient_rect(
            self.screen, window_x, window_y, window_width, window_height,
            (35, 35, 45), (55, 55, 70)
        )

        # Рамка
        pygame.draw.rect(
            self.screen,
            (120, 120, 150),
            (window_x, window_y, window_width, window_height),
            3
        )

        # Заголовок
        title_text = self.font.render("ХАРАКТЕРИСТИКИ ПЕРСОНАЖА", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + int(10 * scale_h)
        self.screen.blit(title_text, title_rect)

        # Информация о персонаже
        info_y = window_y + int(50 * scale_h)
        player_rank = player.get_rank()

        info_lines = [
            f"Имя: {player.name}",
            f"Уровень: {player.level} ({player_rank})",
            f"Опыт: {player.experience}/{player.experience_to_next_level}",
            f"Золото: {player.inventory.gold}",
        ]

        for i, line in enumerate(info_lines):
            info_text = self.info_font.render(line, True, (200, 200, 200))
            self.screen.blit(info_text, (window_x + int(50 * scale_w), info_y + i * int(25 * scale_h)))

        # Разделитель
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (window_x + int(20 * scale_w), window_y + int(180 * scale_h)),
            (window_x + window_width - int(20 * scale_w), window_y + int(180 * scale_h)),
            2
        )

        # Характеристики
        stats_y = window_y + int(200 * scale_h)
        stats = player.get_stats()
        base_stats = player.get_base_stats()
        equip_bonuses = player.inventory.get_total_stats_bonus()

        # Свободные очки
        if player.stat_points > 0:
            points_text = self.font.render(
                f"Свободных очков: {player.stat_points}",
                True,
                (100, 255, 100)
            )
            points_rect = points_text.get_rect()
            points_rect.centerx = window_x + window_width // 2
            points_rect.y = stats_y - int(30 * scale_h)
            self.screen.blit(points_text, points_rect)

        # Отображение характеристик
        stat_line_height = max(28, int(32 * scale_h))
        for i, (stat_key, stat_name) in enumerate(self.stats_list):
            display_y = stats_y + i * stat_line_height

            # Подсветка выбранной характеристики
            if i == self.selected_stat_index:
                pygame.draw.rect(
                    self.screen,
                    (80, 80, 100),
                    (window_x + int(40 * scale_w), display_y - int(5 * scale_h), window_width - int(80 * scale_w), int(35 * scale_h))
                )
                pygame.draw.rect(
                    self.screen,
                    (120, 150, 200),
                    (window_x + int(40 * scale_w), display_y - int(5 * scale_h), window_width - int(80 * scale_w), int(35 * scale_h)),
                    2
                )

            # Название характеристики
            name_text = self.info_font.render(
                f"{stat_name}:",
                True,
                (220, 220, 220)
            )
            self.screen.blit(name_text, (window_x + int(60 * scale_w), display_y))

            # Значение
            base_value = base_stats[stat_key]
            bonus = equip_bonuses.get(stat_key, 0)
            total_value = stats[stat_key]

            if bonus > 0:
                value_str = f"{base_value} (+{bonus}) = {total_value}"
                value_color = (150, 255, 150)
            else:
                value_str = f"{total_value}"
                value_color = (200, 200, 200)

            value_text = self.info_font.render(value_str, True, value_color)
            self.screen.blit(value_text, (window_x + int(300 * scale_w), display_y))

            # Кнопка + для добавления очка
            if player.stat_points > 0 and i == self.selected_stat_index:
                plus_text = self.info_font.render("[+]", True, (100, 255, 100))
                self.screen.blit(plus_text, (window_x + window_width - int(120 * scale_w), display_y))

        # Дополнительная информация
        additional_y = stats_y + len(self.stats_list) * stat_line_height + int(10 * scale_h)

        additional_info = [
            f"Здоровье: {player.health}/{player.max_health}",
            f"Мана: {player.mana}/{player.max_mana}",
            f"Выносливость: {player.stamina}/{player.max_stamina}",
            f"Урон: {player.get_total_damage()}",
            f"Защита: {player.get_total_defense()}",
        ]

        for i, line in enumerate(additional_info):
            info_text = self.info_font.render(line, True, (180, 180, 200))
            self.screen.blit(info_text, (window_x + int(60 * scale_w), additional_y + i * int(25 * scale_h)))

        # Подсказки внизу
        hints_y = window_y + window_height - int(40 * scale_h)
        if player.stat_points > 0:
            hint_text = self.info_font.render(
                "W/S - выбор | Enter - добавить очко | C/ESC - закрыть",
                True,
                (180, 180, 180)
            )
        else:
            hint_text = self.info_font.render(
                "C/ESC - закрыть",
                True,
                (180, 180, 180)
            )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = hints_y
        self.screen.blit(hint_text, hint_rect)
