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
            # Вычисляем заполнение с ограничением (clamp)
            fill_ratio = min(1.0, max(0.0, current / maximum))
            fill_width = int(fill_ratio * width)
            pygame.draw.rect(surface, fill_color, (x, y, fill_width, height))

        # Рамка
        pygame.draw.rect(surface, border_color, (x, y, width, height), 1)

        # Текст
        if text and font:
            text_surface = font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.center = (x + width // 2, y + height // 2)
            surface.blit(text_surface, text_rect)

    @staticmethod
    def wrap_text(text, font, max_width):
        """
        Разбивает текст на строки с переносом по словам

        Args:
            text: Текст для разбивки
            font: Шрифт для измерения ширины
            max_width: Максимальная ширина строки в пикселях

        Returns:
            list: Список строк
        """
        if not text:
            return [""]

        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            # Пробуем добавить слово к текущей строке
            test_line = current_line + (" " if current_line else "") + word
            test_surface = font.render(test_line, True, (255, 255, 255))

            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                # Если текущая строка не пуста, сохраняем её
                if current_line:
                    lines.append(current_line)
                # Проверяем, помещается ли слово само по себе
                word_surface = font.render(word, True, (255, 255, 255))
                if word_surface.get_width() > max_width:
                    # Слово слишком длинное, разбиваем по символам
                    current_word = ""
                    for char in word:
                        test_word = current_word + char
                        char_surface = font.render(test_word, True, (255, 255, 255))
                        if char_surface.get_width() <= max_width:
                            current_word = test_word
                        else:
                            if current_word:
                                lines.append(current_word)
                            current_word = char
                    current_line = current_word
                else:
                    current_line = word

        # Добавляем последнюю строку
        if current_line:
            lines.append(current_line)

        return lines if lines else [""]


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
        self.equipment_slot_rects = {}  # Словарь {slot: (rect, item)} для tooltip экипировки

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
            # Проверяем, наведён ли курсор на экипированный предмет
            is_equipped_item = False
            for slot, (rect, eq_item) in self.equipment_slot_rects.items():
                if rect.collidepoint(mouse_x, mouse_y) and eq_item:
                    is_equipped_item = True
                    break

            item = self.get_item_at_mouse(player, mouse_x, mouse_y)
            if item:
                # Не показываем сравнение для экипированных предметов
                self.render_item_tooltip(item, mouse_x, mouse_y, player, show_comparison=not is_equipped_item)

    def _render_equipment_panel(self, player, x, y, width, height):
        """Отрисовка панели экипировки"""
        # Очищаем словарь координат слотов
        self.equipment_slot_rects.clear()

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

                # Создаём прямоугольник слота и сохраняем для tooltip
                slot_rect = pygame.Rect(x + margin_left, slot_y, width - margin_sides, slot_height - 2)
                self.equipment_slot_rects[slot] = (slot_rect, item)

                # Фон слота
                slot_color = (60, 60, 70) if item else (40, 40, 50)
                pygame.draw.rect(
                    self.screen,
                    slot_color,
                    slot_rect
                )

                # Рамка слота
                border_color = (100, 150, 200) if self.selected_equipment_slot == slot else (80, 80, 90)
                pygame.draw.rect(
                    self.screen,
                    border_color,
                    slot_rect,
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

                # Показываем количество только для стакающихся предметов или если quantity > 1
                is_stackable = item.is_stackable if hasattr(item, 'is_stackable') else True
                display_name = f"{item_name} x{quantity}" if (is_stackable and quantity > 1) or (not is_stackable and quantity > 1) else item_name
                if quantity > 1:
                    display_name = f"{item_name} x{quantity}"
                else:
                    display_name = item_name

                item_text = self.info_font.render(
                    display_name,
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

    def render_item_tooltip(self, item, mouse_x, mouse_y, player=None, show_comparison=True):
        """
        Отрисовка всплывающей подсказки для предмета с возможным сравнением

        Args:
            item: Предмет для отображения
            mouse_x: X координата мыши
            mouse_y: Y координата мыши
            player: Игрок для сравнения с экипировкой
            show_comparison: Показывать ли окна сравнения (False для экипированных предметов)
        """
        from game.inventory import EquipmentItem, WeaponItem, ArmorItem, JewelryItem, PotionItem, EquipmentSlot

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
            # Определяем тип украшения по слоту
            from game.inventory import EquipmentSlot
            jewelry_types = {
                EquipmentSlot.RING_1: "Кольцо",
                EquipmentSlot.RING_2: "Кольцо",
                EquipmentSlot.RING_3: "Кольцо",
                EquipmentSlot.RING_4: "Кольцо",
                EquipmentSlot.AMULET: "Амулет",
                EquipmentSlot.BRACELET_1: "Браслет",
                EquipmentSlot.BRACELET_2: "Браслет",
            }
            jewelry_type = jewelry_types.get(item.slot, "Украшение")
            lines.append((f"Тип: {jewelry_type}", (180, 180, 180), False))
        elif isinstance(item, PotionItem):
            lines.append(("Тип: Зелье", (180, 180, 180), False))

        # УРОН И БРОНЯ СВЕРХУ (сразу после типа)
        if isinstance(item, EquipmentItem):
            if hasattr(item, 'attack') and item.attack > 0:
                lines.append((f"Урон: +{item.attack}", (255, 100, 100), False))
            if hasattr(item, 'defense') and item.defense > 0:
                lines.append((f"Броня: +{item.defense}", (100, 150, 255), False))

            lines.append(("", (0, 0, 0), False))  # Пустая строка

            # Бонусы к характеристикам
            if item.stats_bonus:
                for stat, bonus in item.stats_bonus.items():
                    if stat in ['damage', 'defense']:  # Пропускаем урон и защиту, они уже отображены
                        continue
                    stat_names = {
                        'strength': 'Сила',
                        'dexterity': 'Ловкость',
                        'constitution': 'Телосложение',
                        'spirit': 'Дух',
                        'intelligence': 'Интеллект',
                        'luck': 'Удача'
                    }
                    stat_name = stat_names.get(stat, stat)
                    actual_bonus = item.get_stat_bonus(stat)
                    lines.append((f"{stat_name}: +{actual_bonus}", (150, 255, 150), False))

            # Процентные бонусы к параметрам
            if hasattr(item, 'param_bonus') and item.param_bonus:
                for param, bonus in item.param_bonus.items():
                    param_names = {
                        'health': 'Здоровье',
                        'mana': 'Мана',
                        'stamina': 'Выносливость'
                    }
                    param_name = param_names.get(param, param)
                    lines.append((f"{param_name}: +{bonus}%", (100, 200, 255), False))

            # Бонусы к навыкам
            if hasattr(item, 'skill_bonus') and item.skill_bonus:
                # Словарь названий умений по ID с указанием типа оружия
                skill_names = {
                    'basic_attack': 'Базовая атака',
                    'power_strike': 'Мощный удар',
                    'poison_strike': 'Отравляющий удар',
                    'stun_strike': 'Оглушающий удар',
                    'battle_cry': 'Боевой клич',
                    'precise_shot': 'Точный выстрел (Лук)',
                    'rapid_fire': 'Скорострельность (Лук)',
                    'piercing_arrow': 'Пронзающая стрела (Лук)',
                    'backstab': 'Удар в спину (Нож)',
                    'bleeding_cut': 'Кровоточащий порез (Нож)',
                    'shadow_step': 'Шаг сквозь тень (Нож)',
                    'whirlwind_strike': 'Вихревой удар (Меч)',
                    'shield_breaker': 'Сокрушение щита (Меч)',
                    'blade_dance': 'Танец клинков (Меч)',
                    'heal': 'Исцеление',
                    'regeneration': 'Регенерация',
                    'stamina_recovery': 'Восстановление сил',
                    'mage_shield': 'Магический щит',
                    'fireball': 'Огненный шар',
                    'ice_bolt': 'Ледяная стрела',
                    'lightning': 'Молния',
                    'magic_missile': 'Магическая стрела',
                    'mining': 'Рудокопство',
                    'lumberjacking': 'Лесорубство'
                }
                for skill_id, bonus in item.skill_bonus.items():
                    skill_name = skill_names.get(skill_id, skill_id)
                    lines.append((f"Умение: {skill_name} [Ранг {bonus}]", (255, 200, 100), False))

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

        # Максимальная ширина текста
        max_text_width = tooltip_width - tooltip_padding * 2

        # Обрабатываем перенос строк для длинных текстов
        wrapped_lines = []
        for line_text, line_color, is_bold in lines:
            if line_text == "":
                wrapped_lines.append((line_text, line_color, is_bold))
            else:
                font_to_use = self.font if is_bold else self.info_font
                # Проверяем, помещается ли текст
                test_surface = font_to_use.render(line_text, True, line_color)
                if test_surface.get_width() <= max_text_width:
                    wrapped_lines.append((line_text, line_color, is_bold))
                else:
                    # Переносим по словам
                    wrapped = UIHelper.wrap_text(line_text, font_to_use, max_text_width)
                    for wrapped_line in wrapped:
                        wrapped_lines.append((wrapped_line, line_color, is_bold))

        # Вычисляем высоту подсказки с учетом переносов
        actual_line_count = 0
        empty_line_count = 0
        for line_text, _, _ in wrapped_lines:
            if line_text == "":
                empty_line_count += 1
            else:
                actual_line_count += 1
        tooltip_height = tooltip_padding * 2 + actual_line_count * line_height + empty_line_count * (line_height // 2)

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
        for line_text, line_color, is_bold in wrapped_lines:
            if line_text == "":  # Пустая строка
                text_y += line_height // 2
                continue

            font_to_use = self.font if is_bold else self.info_font
            text_surface = font_to_use.render(line_text, True, line_color)
            self.screen.blit(text_surface, (tooltip_x + tooltip_padding, text_y))
            text_y += line_height

        # Отрисовка окон сравнения для экипируемых предметов (только если не наводим на экипировку)
        if player and isinstance(item, EquipmentItem) and show_comparison:
            self._render_comparison_tooltips(item, tooltip_x, tooltip_y, tooltip_width, tooltip_height, player)

    def _render_comparison_tooltips(self, item, main_tooltip_x, main_tooltip_y, main_width, main_height, player):
        """
        Отрисовка окон сравнения для экипируемых предметов

        Args:
            item: Предмет для сравнения
            main_tooltip_x, main_tooltip_y: Позиция основного tooltip
            main_width, main_height: Размеры основного tooltip
            player: Игрок
        """
        from game.inventory import EquipmentSlot, WeaponItem, ArmorItem, JewelryItem

        # Определяем слоты для сравнения
        comparison_slots = []
        if hasattr(item, 'slot'):
            slot = item.slot
            # Для колец и браслетов показываем все занятые слоты
            if slot in [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]:
                comparison_slots = [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]
            elif slot in [EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]:
                comparison_slots = [EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]
            else:
                comparison_slots = [slot]

        # Собираем экипированные предметы для сравнения (только непустые слоты)
        equipped_items = []
        for comp_slot in comparison_slots:
            equipped = player.inventory.get_equipped_item(comp_slot)
            if equipped:
                equipped_items.append((comp_slot, equipped))

        if not equipped_items:
            return

        # Отрисовываем окна сравнения
        comp_width = 250
        comp_padding = 10
        line_height = 20
        screen_width = self.screen.get_width()

        # Позиция окон сравнения - слева от основного или справа
        comp_x = main_tooltip_x - comp_width - 10
        if comp_x < 5:
            comp_x = main_tooltip_x + main_width + 10
        if comp_x + comp_width > screen_width - 5:
            return  # Нет места для сравнения

        comp_y = main_tooltip_y

        for slot, equipped in equipped_items:
            lines = []

            # Заголовок
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
            lines.append((f"[{slot_names.get(slot, 'Слот')}]", (200, 200, 100), True))

            # Название экипированного предмета
            equipped_name = equipped.get_full_name() if hasattr(equipped, 'get_full_name') else equipped.name
            equipped_color = equipped.quality.color if hasattr(equipped, 'quality') else (200, 200, 200)
            lines.append((equipped_name[:25], equipped_color, False))
            lines.append(("", (0, 0, 0), False))

            # Сравнение характеристик
            # Урон
            item_attack = getattr(item, 'attack', 0)
            equip_attack = getattr(equipped, 'attack', 0)
            if item_attack or equip_attack:
                diff = item_attack - equip_attack
                diff_color = (100, 255, 100) if diff > 0 else ((255, 100, 100) if diff < 0 else (180, 180, 180))
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                lines.append((f"Урон: {diff_str}", diff_color, False))

            # Броня
            item_defense = getattr(item, 'defense', 0)
            equip_defense = getattr(equipped, 'defense', 0)
            if item_defense or equip_defense:
                diff = item_defense - equip_defense
                diff_color = (100, 255, 100) if diff > 0 else ((255, 100, 100) if diff < 0 else (180, 180, 180))
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                lines.append((f"Броня: {diff_str}", diff_color, False))

            # Бонусы к характеристикам
            stat_names = {
                'strength': 'Сила', 'dexterity': 'Ловкость', 'constitution': 'Телосл.',
                'spirit': 'Дух', 'intelligence': 'Интеллект', 'luck': 'Удача'
            }
            all_stats = set()
            if item.stats_bonus:
                all_stats.update(item.stats_bonus.keys())
            if equipped.stats_bonus:
                all_stats.update(equipped.stats_bonus.keys())

            for stat in all_stats:
                if stat in ['damage', 'defense']:
                    continue
                item_bonus = item.get_stat_bonus(stat) if hasattr(item, 'get_stat_bonus') else 0
                equip_bonus = equipped.get_stat_bonus(stat) if hasattr(equipped, 'get_stat_bonus') else 0
                diff = item_bonus - equip_bonus
                if diff != 0:
                    diff_color = (100, 255, 100) if diff > 0 else (255, 100, 100)
                    diff_str = f"+{diff}" if diff > 0 else str(diff)
                    lines.append((f"{stat_names.get(stat, stat)}: {diff_str}", diff_color, False))

            # Процентные бонусы к параметрам (важно для бижутерии)
            param_names = {
                'health': 'Здоровье', 'mana': 'Мана', 'stamina': 'Выносливость'
            }
            item_param_bonus = getattr(item, 'param_bonus', {}) or {}
            equip_param_bonus = getattr(equipped, 'param_bonus', {}) or {}
            all_params = set(item_param_bonus.keys()) | set(equip_param_bonus.keys())

            for param in all_params:
                item_pb = item_param_bonus.get(param, 0)
                equip_pb = equip_param_bonus.get(param, 0)
                diff = item_pb - equip_pb
                if diff != 0:
                    diff_color = (100, 255, 100) if diff > 0 else (255, 100, 100)
                    diff_str = f"+{diff}%" if diff > 0 else f"{diff}%"
                    lines.append((f"{param_names.get(param, param)}: {diff_str}", diff_color, False))

            # Вычисляем высоту
            comp_height = comp_padding * 2 + len(lines) * line_height

            # Фон сравнения
            UIHelper.draw_gradient_rect(
                self.screen, comp_x, comp_y, comp_width, comp_height,
                (50, 40, 40), (70, 55, 55)
            )
            pygame.draw.rect(self.screen, (150, 120, 120), (comp_x, comp_y, comp_width, comp_height), 2)

            # Текст
            text_y = comp_y + comp_padding
            for line_text, line_color, is_bold in lines:
                if line_text == "":
                    text_y += line_height // 2
                    continue
                font_to_use = self.font if is_bold else self.info_font
                text_surface = font_to_use.render(line_text, True, line_color)
                self.screen.blit(text_surface, (comp_x + comp_padding, text_y))
                text_y += line_height

            comp_y += comp_height + 5

    def get_item_at_mouse(self, player, mouse_x, mouse_y, check_equipment=False):
        """
        Получить предмет под курсором мыши

        Args:
            player: Объект игрока
            mouse_x: X координата мыши
            mouse_y: Y координата мыши
            check_equipment: Если True, проверяет только инвентарь (не экипировку)

        Returns:
            Item или None
        """
        # Проверяем слоты экипировки только если не отключено
        if not check_equipment:
            for slot, (rect, item) in self.equipment_slot_rects.items():
                if rect.collidepoint(mouse_x, mouse_y) and item:
                    return item

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

    def get_equipment_slot_at_mouse(self, mouse_x, mouse_y):
        """
        Получить слот экипировки под курсором мыши

        Args:
            mouse_x: X координата мыши
            mouse_y: Y координата мыши

        Returns:
            tuple: (EquipmentSlot, Item) или (None, None)
        """
        for slot, (rect, item) in self.equipment_slot_rects.items():
            if rect.collidepoint(mouse_x, mouse_y):
                return (slot, item)
        return (None, None)


class TradeWindow:
    """Окно торговли с NPC"""

    # Типы фильтров
    FILTER_TYPES = ["all", "weapon", "armor", "jewelry", "potion", "resource", "book"]
    FILTER_NAMES = {
        "all": "Все",
        "weapon": "Оружие",
        "armor": "Броня",
        "jewelry": "Украш.",
        "potion": "Зелья",
        "resource": "Ресурсы",
        "book": "Книги"
    }

    # Типы сортировки
    SORT_TYPES = ["default", "price_asc", "price_desc", "quality"]
    SORT_NAMES = {
        "default": "По умолч.",
        "price_asc": "Цена ↑",
        "price_desc": "Цена ↓",
        "quality": "Качество"
    }

    def __init__(self, screen, font, info_font, scaler=None):
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.scaler = scaler
        self.selected_merchant_index = 0
        self.selected_player_index = 0
        self.mode = "buy"  # "buy" или "sell"

        # Фильтры и сортировка
        self.current_filter = "all"
        self.current_sort = "default"
        self.filter_rects = []  # Прямоугольники кнопок фильтров
        self.sort_rects = []  # Прямоугольники кнопок сортировки

        # Хранение координат элементов для обработки мыши
        self.item_rects = []  # Список прямоугольников предметов
        self.goods_area = None  # Область списка товаров

        # Хранение отфильтрованных списков для консистентности между рендером и вводом
        self.current_merchant_items = []  # Текущий отфильтрованный список товаров торговца
        self.current_player_items = []  # Текущий отфильтрованный список товаров игрока

    def render(self, player, merchant, mouse_pos=None):
        """
        Отрисовка окна торговли

        Args:
            player: Объект игрока
            merchant: Объект торговца
            mouse_pos: Позиция мыши для tooltip
        """
        # Очищаем список rect'ов
        self.item_rects = []
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
        mode_y = window_y + int(85 * scale_h)
        buy_color = (100, 200, 100) if self.mode == "buy" else (100, 100, 100)
        sell_color = (200, 100, 100) if self.mode == "sell" else (100, 100, 100)

        buy_button = self.font.render("[TAB] ПОКУПКА", True, buy_color)
        sell_button = self.font.render("ПРОДАЖА", True, sell_color)

        self.screen.blit(buy_button, (window_x + int(50 * scale_w), mode_y))
        self.screen.blit(sell_button, (window_x + window_width - int(200 * scale_w), mode_y))

        # Отрисовка фильтров и сортировки
        self.filter_rects = []
        self.sort_rects = []
        filter_y = window_y + int(115 * scale_h)
        filter_x = window_x + int(30 * scale_w)
        btn_width = int(70 * scale_w)
        btn_height = int(22 * scale_h)
        btn_spacing = int(5 * scale_w)

        # Фильтры по типу
        filter_label = self.info_font.render("Тип:", True, (180, 180, 180))
        self.screen.blit(filter_label, (filter_x, filter_y + 3))
        filter_x += int(40 * scale_w)

        for filter_type in self.FILTER_TYPES:
            is_active = self.current_filter == filter_type
            btn_color = (80, 120, 80) if is_active else (50, 50, 60)
            border_color = (120, 200, 120) if is_active else (80, 80, 90)
            text_color = (200, 255, 200) if is_active else (150, 150, 150)

            btn_rect = pygame.Rect(filter_x, filter_y, btn_width, btn_height)
            pygame.draw.rect(self.screen, btn_color, btn_rect)
            pygame.draw.rect(self.screen, border_color, btn_rect, 1)

            btn_text = self.info_font.render(self.FILTER_NAMES[filter_type], True, text_color)
            text_rect = btn_text.get_rect(center=btn_rect.center)
            self.screen.blit(btn_text, text_rect)

            self.filter_rects.append((btn_rect, filter_type))
            filter_x += btn_width + btn_spacing

        # Сортировка
        sort_y = filter_y
        sort_x = window_x + window_width - int(350 * scale_w)

        sort_label = self.info_font.render("Сорт.:", True, (180, 180, 180))
        self.screen.blit(sort_label, (sort_x, sort_y + 3))
        sort_x += int(50 * scale_w)

        for sort_type in self.SORT_TYPES:
            is_active = self.current_sort == sort_type
            btn_color = (80, 80, 120) if is_active else (50, 50, 60)
            border_color = (120, 120, 200) if is_active else (80, 80, 90)
            text_color = (200, 200, 255) if is_active else (150, 150, 150)

            btn_rect = pygame.Rect(sort_x, sort_y, btn_width, btn_height)
            pygame.draw.rect(self.screen, btn_color, btn_rect)
            pygame.draw.rect(self.screen, border_color, btn_rect, 1)

            btn_text = self.info_font.render(self.SORT_NAMES[sort_type], True, text_color)
            text_rect = btn_text.get_rect(center=btn_rect.center)
            self.screen.blit(btn_text, text_rect)

            self.sort_rects.append((btn_rect, sort_type))
            sort_x += btn_width + btn_spacing

        # Панели товаров
        goods_y = window_y + int(145 * scale_h)
        goods_height = int(425 * scale_h)

        if self.mode == "buy":
            self._render_merchant_goods(merchant, window_x + int(30 * scale_w), goods_y, window_width - int(60 * scale_w), goods_height)
        else:
            self._render_player_goods(player, window_x + int(30 * scale_w), goods_y, window_width - int(60 * scale_w), goods_height)

        # Подсказки
        hints_y = window_y + window_height - int(35 * scale_h)
        if self.mode == "buy":
            hint = "W/S - выбор | Enter/ПКМ - купить | Tab - режим продажи | ESC - закрыть"
        else:
            hint = "W/S - выбор | Enter/ПКМ - продать | Tab - режим покупки | ESC - закрыть"

        hint_text = self.info_font.render(hint, True, (180, 180, 180))
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = hints_y
        self.screen.blit(hint_text, hint_rect)

        # Отрисовка tooltip при наведении мыши
        if mouse_pos:
            mouse_x, mouse_y = mouse_pos
            item = self.get_item_at_mouse(player, merchant, mouse_x, mouse_y)
            if item:
                self.render_item_tooltip(item, mouse_x, mouse_y, player)

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
        # Применяем фильтрацию и сортировку
        items = self.filter_and_sort_items(items)
        # Сохраняем для использования в input handler
        self.current_merchant_items = items

        if not items:
            msg = "Нет товаров этого типа" if self.current_filter != "all" else "Товары закончились"
            no_goods = self.info_font.render(msg, True, (150, 150, 150))
            self.screen.blit(no_goods, (x + width // 2 - 100, y + height // 2))
            return

        # Список товаров с прокруткой
        items_y = y + 35
        item_height = 28
        max_visible = int(height / item_height) - 1  # Вычисляем максимум видимых элементов

        # Умная прокрутка: держим выбранный элемент в видимой области
        if len(items) <= max_visible:
            start_index = 0
            end_index = len(items)
        else:
            # Центрируем выбранный элемент, если возможно
            half_visible = max_visible // 2
            start_index = max(0, min(self.selected_merchant_index - half_visible, len(items) - max_visible))
            end_index = min(len(items), start_index + max_visible)

        for i in range(start_index, end_index):
            item, quantity = items[i]
            display_index = i - start_index

            # Сохраняем прямоугольник предмета для обработки мыши
            item_rect = pygame.Rect(x, items_y + display_index * item_height, width, item_height - 2)
            self.item_rects.append((item_rect, item, i))

            # Фон выбранного предмета
            if i == self.selected_merchant_index:
                pygame.draw.rect(
                    self.screen,
                    (80, 100, 80),
                    item_rect
                )
                pygame.draw.rect(
                    self.screen,
                    (120, 200, 120),
                    item_rect,
                    2
                )

            # Название предмета
            item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
            item_color = item.quality.color if hasattr(item, 'quality') else (200, 200, 200)

            # Показываем количество только если > 1
            display_name = f"{item_name} x{quantity}" if quantity > 1 else item_name

            name_text = self.info_font.render(
                display_name,
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

        # Индикаторы прокрутки
        if start_index > 0:
            scroll_up = self.info_font.render("[^] Еще товары выше", True, (150, 200, 255))
            self.screen.blit(scroll_up, (x + width // 2 - 70, y + 10))
        if end_index < len(items):
            scroll_down = self.info_font.render("[v] Еще товары ниже", True, (150, 200, 255))
            self.screen.blit(scroll_down, (x + width // 2 - 70, y + height - 25))

    def _render_player_goods(self, player, x, y, width, height):
        """Отрисовка товаров игрока для продажи"""
        # Заголовок
        title = self.font.render("Ваши товары", True, (200, 150, 150))
        self.screen.blit(title, (x, y))

        items = player.inventory.get_all_items()
        # Применяем фильтрацию и сортировку
        items = self.filter_and_sort_items(items)
        # Сохраняем для использования в input handler
        self.current_player_items = items

        if not items:
            msg = "Нет товаров этого типа" if self.current_filter != "all" else "У вас нет товаров для продажи"
            no_goods = self.info_font.render(msg, True, (150, 150, 150))
            self.screen.blit(no_goods, (x + width // 2 - 120, y + height // 2))
            return

        # Список товаров с прокруткой
        items_y = y + 35
        item_height = 28
        max_visible = int(height / item_height) - 1  # Вычисляем максимум видимых элементов

        # Умная прокрутка: держим выбранный элемент в видимой области
        if len(items) <= max_visible:
            start_index = 0
            end_index = len(items)
        else:
            # Центрируем выбранный элемент, если возможно
            half_visible = max_visible // 2
            start_index = max(0, min(self.selected_player_index - half_visible, len(items) - max_visible))
            end_index = min(len(items), start_index + max_visible)

        for i in range(start_index, end_index):
            item, quantity = items[i]
            display_index = i - start_index

            # Сохраняем прямоугольник предмета для обработки мыши
            item_rect = pygame.Rect(x, items_y + display_index * item_height, width, item_height - 2)
            self.item_rects.append((item_rect, item, i))

            # Фон выбранного предмета
            if i == self.selected_player_index:
                pygame.draw.rect(
                    self.screen,
                    (100, 80, 80),
                    item_rect
                )
                pygame.draw.rect(
                    self.screen,
                    (200, 120, 120),
                    item_rect,
                    2
                )

            # Название предмета
            item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
            item_color = item.quality.color if hasattr(item, 'quality') else (200, 200, 200)

            # Показываем количество только если > 1
            display_name = f"{item_name} x{quantity}" if quantity > 1 else item_name

            name_text = self.info_font.render(
                display_name,
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

        # Индикаторы прокрутки
        if start_index > 0:
            scroll_up = self.info_font.render("[^] Еще товары выше", True, (200, 150, 150))
            self.screen.blit(scroll_up, (x + width // 2 - 70, y + 10))
        if end_index < len(items):
            scroll_down = self.info_font.render("[v] Еще товары ниже", True, (200, 150, 150))
            self.screen.blit(scroll_down, (x + width // 2 - 70, y + height - 25))

    def get_item_at_mouse(self, player, merchant, mouse_x, mouse_y):
        """
        Получить предмет под курсором мыши

        Args:
            player: Объект игрока
            merchant: Объект торговца
            mouse_x: X координата мыши
            mouse_y: Y координата мыши

        Returns:
            Item или None
        """
        for rect, item, index in self.item_rects:
            if rect.collidepoint(mouse_x, mouse_y):
                return item
        return None

    def get_item_index_at_mouse(self, mouse_x, mouse_y):
        """
        Получить индекс предмета под курсором мыши

        Args:
            mouse_x: X координата мыши
            mouse_y: Y координата мыши

        Returns:
            int или None: Индекс предмета в списке
        """
        for rect, item, index in self.item_rects:
            if rect.collidepoint(mouse_x, mouse_y):
                return index
        return None

    def get_item_at_mouse_trade(self, mouse_x, mouse_y):
        """
        Получить сам предмет под курсором мыши (не индекс)

        Args:
            mouse_x: X координата мыши
            mouse_y: Y координата мыши

        Returns:
            Item или None: Предмет под курсором
        """
        for rect, item, index in self.item_rects:
            if rect.collidepoint(mouse_x, mouse_y):
                return item
        return None

    def _get_item_type(self, item):
        """Определить тип предмета для фильтрации"""
        from game.inventory import WeaponItem, ArmorItem, JewelryItem, PotionItem, ResourceItem, SkillBookItem
        if isinstance(item, WeaponItem):
            return "weapon"
        elif isinstance(item, ArmorItem):
            return "armor"
        elif isinstance(item, JewelryItem):
            return "jewelry"
        elif isinstance(item, PotionItem):
            return "potion"
        elif isinstance(item, ResourceItem):
            return "resource"
        elif isinstance(item, SkillBookItem):
            return "book"
        return "other"

    def _get_quality_value(self, item):
        """Получить числовое значение качества для сортировки"""
        if hasattr(item, 'quality'):
            quality_order = {
                'POOR': 0, 'COMMON': 1, 'UNCOMMON': 2,
                'RARE': 3, 'EPIC': 4, 'LEGENDARY': 5, 'ARTIFACT': 6
            }
            return quality_order.get(item.quality.name, 0)
        return 0

    def filter_and_sort_items(self, items):
        """
        Фильтрация и сортировка списка предметов

        Args:
            items: Список кортежей (item, quantity)

        Returns:
            list: Отфильтрованный и отсортированный список
        """
        # Фильтрация
        if self.current_filter != "all":
            items = [(item, qty) for item, qty in items if self._get_item_type(item) == self.current_filter]

        # Сортировка
        if self.current_sort == "price_asc":
            items = sorted(items, key=lambda x: x[0].value)
        elif self.current_sort == "price_desc":
            items = sorted(items, key=lambda x: x[0].value, reverse=True)
        elif self.current_sort == "quality":
            items = sorted(items, key=lambda x: self._get_quality_value(x[0]), reverse=True)

        return items

    def handle_filter_click(self, mouse_x, mouse_y):
        """Обработка клика по кнопкам фильтров"""
        for rect, filter_type in self.filter_rects:
            if rect.collidepoint(mouse_x, mouse_y):
                self.current_filter = filter_type
                self.selected_merchant_index = 0
                self.selected_player_index = 0
                return True
        return False

    def handle_sort_click(self, mouse_x, mouse_y):
        """Обработка клика по кнопкам сортировки"""
        for rect, sort_type in self.sort_rects:
            if rect.collidepoint(mouse_x, mouse_y):
                self.current_sort = sort_type
                self.selected_merchant_index = 0
                self.selected_player_index = 0
                return True
        return False

    def render_item_tooltip(self, item, mouse_x, mouse_y, player=None):
        """
        Отрисовка всплывающей подсказки для предмета в торговом окне

        Args:
            item: Предмет для отображения
            mouse_x: X координата мыши
            mouse_y: Y координата мыши
            player: Игрок для сравнения с экипировкой
        """
        from game.inventory import EquipmentItem, WeaponItem, ArmorItem, JewelryItem, PotionItem, EquipmentSlot

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
            lines.append((f"Тип: {item.weapon_type.rus_name}", (180, 180, 180), False))
        elif isinstance(item, ArmorItem):
            lines.append((f"Тип: {item.armor_type.rus_name}", (180, 180, 180), False))
        elif isinstance(item, JewelryItem):
            from game.inventory import EquipmentSlot
            jewelry_types = {
                EquipmentSlot.RING_1: "Кольцо", EquipmentSlot.RING_2: "Кольцо",
                EquipmentSlot.RING_3: "Кольцо", EquipmentSlot.RING_4: "Кольцо",
                EquipmentSlot.AMULET: "Амулет",
                EquipmentSlot.BRACELET_1: "Браслет", EquipmentSlot.BRACELET_2: "Браслет",
            }
            jewelry_type = jewelry_types.get(item.slot, "Украшение")
            lines.append((f"Тип: {jewelry_type}", (180, 180, 180), False))
        elif isinstance(item, PotionItem):
            lines.append(("Тип: Зелье", (180, 180, 180), False))

        # УРОН И БРОНЯ СВЕРХУ (сразу после типа)
        if isinstance(item, EquipmentItem):
            # Урон (проверяем и damage, и attack)
            item_damage = getattr(item, 'damage', 0) or getattr(item, 'attack', 0)
            if item_damage > 0:
                lines.append((f"Урон: +{item_damage}", (255, 100, 100), False))
            if hasattr(item, 'defense') and item.defense > 0:
                lines.append((f"Броня: +{item.defense}", (100, 150, 255), False))

            lines.append(("", (0, 0, 0), False))  # Пустая строка

            # Бонусы к характеристикам
            if item.stats_bonus:
                stat_names = {
                    'strength': 'Сила', 'dexterity': 'Ловкость',
                    'constitution': 'Телосложение', 'spirit': 'Дух',
                    'intelligence': 'Интеллект', 'luck': 'Удача',
                    'damage': 'Урон', 'defense': 'Защита'
                }
                for stat, bonus in item.stats_bonus.items():
                    actual_bonus = item.get_stat_bonus(stat)
                    stat_name = stat_names.get(stat, stat)
                    if stat not in ['damage', 'defense']:  # Урон и защита уже показаны выше
                        lines.append((f"{stat_name}: +{actual_bonus}", (150, 255, 150), False))

            # Процентные бонусы к параметрам
            if hasattr(item, 'param_bonus') and item.param_bonus:
                for param, bonus in item.param_bonus.items():
                    param_names = {
                        'health': 'Здоровье',
                        'mana': 'Мана',
                        'stamina': 'Выносливость'
                    }
                    param_name = param_names.get(param, param)
                    lines.append((f"{param_name}: +{bonus}%", (100, 200, 255), False))

            # Бонусы к навыкам
            if hasattr(item, 'skill_bonus') and item.skill_bonus:
                # Словарь названий умений по ID с указанием типа оружия
                skill_names = {
                    'basic_attack': 'Базовая атака',
                    'power_strike': 'Мощный удар',
                    'poison_strike': 'Отравляющий удар',
                    'stun_strike': 'Оглушающий удар',
                    'battle_cry': 'Боевой клич',
                    'precise_shot': 'Точный выстрел (Лук)',
                    'rapid_fire': 'Скорострельность (Лук)',
                    'piercing_arrow': 'Пронзающая стрела (Лук)',
                    'backstab': 'Удар в спину (Нож)',
                    'bleeding_cut': 'Кровоточащий порез (Нож)',
                    'shadow_step': 'Шаг сквозь тень (Нож)',
                    'whirlwind_strike': 'Вихревой удар (Меч)',
                    'shield_breaker': 'Сокрушение щита (Меч)',
                    'blade_dance': 'Танец клинков (Меч)',
                    'heal': 'Исцеление',
                    'regeneration': 'Регенерация',
                    'stamina_recovery': 'Восстановление сил',
                    'mage_shield': 'Магический щит',
                    'fireball': 'Огненный шар',
                    'ice_bolt': 'Ледяная стрела',
                    'lightning': 'Молния',
                    'magic_missile': 'Магическая стрела',
                    'mining': 'Рудокопство',
                    'lumberjacking': 'Лесорубство'
                }
                for skill_id, bonus in item.skill_bonus.items():
                    skill_name = skill_names.get(skill_id, skill_id)
                    lines.append((f"Умение: {skill_name} [Ранг {bonus}]", (255, 200, 100), False))

        # Эффекты зелья
        if isinstance(item, PotionItem):
            lines.append(("", (0, 0, 0), False))
            effect_names = {'health': 'Здоровье', 'mana': 'Мана', 'stamina': 'Выносливость'}
            effect_name = effect_names.get(item.effect_type, item.effect_type)
            lines.append((f"Восстановление: +{item.effect_value} {effect_name}", (100, 255, 100), False))

        # Вес и стоимость
        lines.append(("", (0, 0, 0), False))
        lines.append((f"Вес: {item.weight:.1f} кг", (200, 200, 200), False))

        # Показываем цену покупки/продажи
        if self.mode == "buy":
            buy_price = int(item.value * 1.5)
            lines.append((f"Цена покупки: {buy_price} золота", (255, 215, 0), False))
        else:
            sell_price = int(item.value * 0.7)
            lines.append((f"Цена продажи: {sell_price} золота", (255, 215, 0), False))

        # Максимальная ширина текста
        max_text_width = tooltip_width - tooltip_padding * 2

        # Обрабатываем перенос строк для длинных текстов
        wrapped_lines = []
        for line_text, line_color, is_bold in lines:
            if line_text == "":
                wrapped_lines.append((line_text, line_color, is_bold))
            else:
                font_to_use = self.font if is_bold else self.info_font
                # Проверяем, помещается ли текст
                test_surface = font_to_use.render(line_text, True, line_color)
                if test_surface.get_width() <= max_text_width:
                    wrapped_lines.append((line_text, line_color, is_bold))
                else:
                    # Переносим по словам
                    wrapped = UIHelper.wrap_text(line_text, font_to_use, max_text_width)
                    for wrapped_line in wrapped:
                        wrapped_lines.append((wrapped_line, line_color, is_bold))

        # Вычисляем высоту подсказки с учетом переносов
        actual_line_count = 0
        empty_line_count = 0
        for line_text, _, _ in wrapped_lines:
            if line_text == "":
                empty_line_count += 1
            else:
                actual_line_count += 1
        tooltip_height = tooltip_padding * 2 + actual_line_count * line_height + empty_line_count * (line_height // 2)

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
        for line_text, line_color, is_bold in wrapped_lines:
            if line_text == "":  # Пустая строка
                text_y += line_height // 2
                continue

            font_to_use = self.font if is_bold else self.info_font
            text_surface = font_to_use.render(line_text, True, line_color)
            self.screen.blit(text_surface, (tooltip_x + tooltip_padding, text_y))
            text_y += line_height

        # Отрисовка окон сравнения для экипируемых предметов (если передан player)
        if player and isinstance(item, EquipmentItem):
            self._render_comparison_tooltips(item, tooltip_x, tooltip_y, tooltip_width, tooltip_height, player)

    def _render_comparison_tooltips(self, item, main_tooltip_x, main_tooltip_y, main_width, main_height, player):
        """Отрисовка окон сравнения для экипируемых предметов (торговое окно)"""
        from game.inventory import EquipmentSlot

        comparison_slots = []
        if hasattr(item, 'slot'):
            slot = item.slot
            if slot in [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]:
                comparison_slots = [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]
            elif slot in [EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]:
                comparison_slots = [EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]
            else:
                comparison_slots = [slot]

        equipped_items = []
        for comp_slot in comparison_slots:
            equipped = player.inventory.get_equipped_item(comp_slot)
            if equipped:
                equipped_items.append((comp_slot, equipped))

        if not equipped_items:
            return

        comp_width = 250
        comp_padding = 10
        line_height = 20
        screen_width = self.screen.get_width()

        comp_x = main_tooltip_x - comp_width - 10
        if comp_x < 5:
            comp_x = main_tooltip_x + main_width + 10
        if comp_x + comp_width > screen_width - 5:
            return

        comp_y = main_tooltip_y

        slot_names = {
            EquipmentSlot.WEAPON: "Оружие", EquipmentSlot.HEAD: "Голова", EquipmentSlot.CHEST: "Торс",
            EquipmentSlot.HANDS: "Руки", EquipmentSlot.FEET: "Ноги",
            EquipmentSlot.RING_1: "Кольцо 1", EquipmentSlot.RING_2: "Кольцо 2",
            EquipmentSlot.RING_3: "Кольцо 3", EquipmentSlot.RING_4: "Кольцо 4",
            EquipmentSlot.AMULET: "Амулет", EquipmentSlot.BRACELET_1: "Браслет 1", EquipmentSlot.BRACELET_2: "Браслет 2",
        }

        stat_names = {'strength': 'Сила', 'dexterity': 'Ловкость', 'constitution': 'Телосл.',
                     'spirit': 'Дух', 'intelligence': 'Интеллект', 'luck': 'Удача'}

        for slot, equipped in equipped_items:
            lines = []
            lines.append((f"[{slot_names.get(slot, 'Слот')}]", (200, 200, 100), True))
            equipped_name = equipped.get_full_name() if hasattr(equipped, 'get_full_name') else equipped.name
            equipped_color = equipped.quality.color if hasattr(equipped, 'quality') else (200, 200, 200)
            lines.append((equipped_name[:25], equipped_color, False))
            lines.append(("", (0, 0, 0), False))

            item_attack = getattr(item, 'attack', 0) or getattr(item, 'damage', 0)
            equip_attack = getattr(equipped, 'attack', 0) or getattr(equipped, 'damage', 0)
            if item_attack or equip_attack:
                diff = item_attack - equip_attack
                diff_color = (100, 255, 100) if diff > 0 else ((255, 100, 100) if diff < 0 else (180, 180, 180))
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                lines.append((f"Урон: {diff_str}", diff_color, False))

            item_defense = getattr(item, 'defense', 0)
            equip_defense = getattr(equipped, 'defense', 0)
            if item_defense or equip_defense:
                diff = item_defense - equip_defense
                diff_color = (100, 255, 100) if diff > 0 else ((255, 100, 100) if diff < 0 else (180, 180, 180))
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                lines.append((f"Броня: {diff_str}", diff_color, False))

            all_stats = set()
            if item.stats_bonus:
                all_stats.update(item.stats_bonus.keys())
            if equipped.stats_bonus:
                all_stats.update(equipped.stats_bonus.keys())

            for stat in all_stats:
                if stat in ['damage', 'defense']:
                    continue
                item_bonus = item.get_stat_bonus(stat) if hasattr(item, 'get_stat_bonus') else 0
                equip_bonus = equipped.get_stat_bonus(stat) if hasattr(equipped, 'get_stat_bonus') else 0
                diff = item_bonus - equip_bonus
                if diff != 0:
                    diff_color = (100, 255, 100) if diff > 0 else (255, 100, 100)
                    diff_str = f"+{diff}" if diff > 0 else str(diff)
                    lines.append((f"{stat_names.get(stat, stat)}: {diff_str}", diff_color, False))

            # Процентные бонусы к параметрам (важно для бижутерии)
            param_names = {'health': 'Здоровье', 'mana': 'Мана', 'stamina': 'Выносливость'}
            item_param_bonus = getattr(item, 'param_bonus', {}) or {}
            equip_param_bonus = getattr(equipped, 'param_bonus', {}) or {}
            all_params = set(item_param_bonus.keys()) | set(equip_param_bonus.keys())

            for param in all_params:
                item_pb = item_param_bonus.get(param, 0)
                equip_pb = equip_param_bonus.get(param, 0)
                diff = item_pb - equip_pb
                if diff != 0:
                    diff_color = (100, 255, 100) if diff > 0 else (255, 100, 100)
                    diff_str = f"+{diff}%" if diff > 0 else f"{diff}%"
                    lines.append((f"{param_names.get(param, param)}: {diff_str}", diff_color, False))

            comp_height = comp_padding * 2 + len(lines) * line_height
            UIHelper.draw_gradient_rect(self.screen, comp_x, comp_y, comp_width, comp_height, (50, 40, 40), (70, 55, 55))
            pygame.draw.rect(self.screen, (150, 120, 120), (comp_x, comp_y, comp_width, comp_height), 2)

            text_y = comp_y + comp_padding
            for line_text, line_color, is_bold in lines:
                if line_text == "":
                    text_y += line_height // 2
                    continue
                font_to_use = self.font if is_bold else self.info_font
                text_surface = font_to_use.render(line_text, True, line_color)
                self.screen.blit(text_surface, (comp_x + comp_padding, text_y))
                text_y += line_height

            comp_y += comp_height + 5


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
                # Компактный формат для больших значений
                if total_value > 999:
                    value_str = f"{base_value}+{bonus}={total_value}"
                else:
                    value_str = f"{base_value} (+{bonus}) = {total_value}"
                value_color = (150, 255, 150)
            else:
                value_str = f"{total_value}"
                value_color = (200, 200, 200)

            value_text = self.info_font.render(value_str, True, value_color)
            # Ограничиваем ширину текста
            max_text_width = int(180 * scale_w)
            if value_text.get_width() > max_text_width:
                # Используем самый компактный формат
                value_str = f"{total_value}"
                if bonus > 0:
                    value_str += f"(+{bonus})"
                value_text = self.info_font.render(value_str, True, value_color)
            self.screen.blit(value_text, (window_x + int(300 * scale_w), display_y))

            # Кнопка + для добавления очка
            if player.stat_points > 0 and i == self.selected_stat_index:
                plus_text = self.info_font.render("[+]", True, (100, 255, 100))
                self.screen.blit(plus_text, (window_x + window_width - int(120 * scale_w), display_y))

        # Дополнительная информация
        additional_y = stats_y + len(self.stats_list) * stat_line_height + int(10 * scale_h)

        # Используем эффективные значения с учетом бонусов от экипировки
        effective_max_health = player.get_effective_max_health()
        effective_max_mana = player.get_effective_max_mana()
        effective_max_stamina = player.get_effective_max_stamina()

        additional_info = [
            f"Здоровье: {player.health}/{effective_max_health}",
            f"Мана: {player.mana}/{effective_max_mana}",
            f"Выносливость: {player.stamina}/{effective_max_stamina}",
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


class SkillBookWindow:
    """Окно книги умений для управления изученными умениями и их назначением в слоты"""

    def __init__(self, screen, font, info_font, ui_scaler=None):
        """
        Инициализация окна книги умений

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

        # Индексы для навигации
        self.selected_skill_index = 0
        self.selected_slot_index = 0
        self.selected_tab = 0  # 0 - Боевые, 1 - Магические, 2 - Ремесленные

        # Для хранения координат элементов при рендеринге
        self.skill_rects = []  # Список прямоугольников умений
        self.slot_rects = []   # Список прямоугольников слотов
        self.tab_rects = []    # Список прямоугольников вкладок
        self.rank_up_rect = None  # Прямоугольник кнопки повышения ранга

    def handle_mouse_event(self, event, player):
        """
        Обработка событий мыши в окне книги умений

        Args:
            event: Событие pygame
            player: Объект игрока

        Returns:
            bool: True если событие обработано
        """
        import pygame
        from game.skills import SkillCategory

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Проверяем клик по вкладкам
            for i, rect in enumerate(self.tab_rects):
                if rect.collidepoint(mouse_pos):
                    if event.button == 1:  # Левая кнопка
                        self.selected_tab = i
                        self.selected_skill_index = 0
                    return True

            # Проверяем клик по кнопке повышения ранга
            if self.rank_up_rect and self.rank_up_rect.collidepoint(mouse_pos):
                if event.button == 1:  # Левая кнопка
                    categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
                    current_category = categories[self.selected_tab]
                    skills_dict = player.skill_manager.get_all_skills()
                    skills = [skill for skill in skills_dict.values() if skill.category == current_category]

                    if self.selected_skill_index < len(skills):
                        selected_skill = skills[self.selected_skill_index]
                        # Найдем ID умения
                        skill_id = None
                        for sid, skill in skills_dict.items():
                            if skill == selected_skill:
                                skill_id = sid
                                break

                        if skill_id:
                            success, message = player.skill_manager.try_rank_up_skill(skill_id, player)
                            print(message)
                return True

            # Проверяем клик по умениям
            for i, rect in enumerate(self.skill_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_skill_index = i

                    # Левая кнопка мыши - назначить умение в выбранный слот
                    if event.button == 1:
                        categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
                        current_category = categories[self.selected_tab]
                        skills_dict = player.skill_manager.get_all_skills()
                        skills = [skill for skill in skills_dict.values() if skill.category == current_category]

                        if i < len(skills):
                            selected_skill = skills[i]
                            # Найдем ID умения
                            skill_id = None
                            for sid, skill in skills_dict.items():
                                if skill == selected_skill:
                                    skill_id = sid
                                    break

                            if skill_id:
                                player.skill_manager.assign_to_slot(skill_id, self.selected_slot_index)

                    # Правая кнопка мыши - попытка повышения ранга
                    elif event.button == 3:
                        categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
                        current_category = categories[self.selected_tab]
                        skills_dict = player.skill_manager.get_all_skills()
                        skills = [skill for skill in skills_dict.values() if skill.category == current_category]

                        if i < len(skills):
                            selected_skill = skills[i]
                            # Найдем ID умения
                            skill_id = None
                            for sid, skill in skills_dict.items():
                                if skill == selected_skill:
                                    skill_id = sid
                                    break

                            if skill_id:
                                success, message = player.skill_manager.try_rank_up_skill(skill_id, player)
                                print(message)
                    return True

            # Проверяем клик по слотам
            for i, rect in enumerate(self.slot_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_slot_index = i

                    # Левая кнопка мыши - назначить выбранное умение в слот
                    if event.button == 1:
                        categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
                        current_category = categories[self.selected_tab]
                        skills_dict = player.skill_manager.get_all_skills()
                        skills = [skill for skill in skills_dict.values() if skill.category == current_category]

                        if self.selected_skill_index < len(skills):
                            selected_skill = skills[self.selected_skill_index]
                            # Найдем ID умения
                            skill_id = None
                            for sid, skill in skills_dict.items():
                                if skill == selected_skill:
                                    skill_id = sid
                                    break

                            if skill_id:
                                player.skill_manager.assign_to_slot(skill_id, i)

                    # Правая кнопка мыши - убрать умение из слота
                    elif event.button == 3:
                        player.skill_manager.unassign_from_slot(i)
                    return True

        # Обработка колёсика мыши для прокрутки умений
        elif event.type == pygame.MOUSEWHEEL:
            from game.skills import SkillCategory
            categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
            current_category = categories[self.selected_tab]
            skills_dict = player.skill_manager.get_all_skills()
            skills = [skill for skill in skills_dict.values() if skill.category == current_category]

            if event.y > 0:  # Прокрутка вверх
                self.selected_skill_index = max(0, self.selected_skill_index - 1)
            elif event.y < 0:  # Прокрутка вниз
                self.selected_skill_index = min(len(skills) - 1, self.selected_skill_index + 1)
            return True

        return False

    def render(self, player):
        """
        Отрисовать окно книги умений

        Args:
            player: Объект игрока
        """
        import pygame
        from game.skills import SkillCategory

        # Затемняем фон
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные)
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        if self.ui_scaler:
            window_width = self.ui_scaler.scale_width(1000)
            window_height = self.ui_scaler.scale_height(700)
        else:
            window_width = min(1000, int(screen_width * 0.85))
            window_height = min(700, int(screen_height * 0.8))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна
        pygame.draw.rect(
            self.screen,
            (40, 40, 45),
            (window_x, window_y, window_width, window_height)
        )

        # Рамка окна
        pygame.draw.rect(
            self.screen,
            (200, 200, 200),
            (window_x, window_y, window_width, window_height),
            3
        )

        # Заголовок
        title_text = self.font.render(
            "КНИГА УМЕНИЙ",
            True,
            (255, 215, 0)
        )
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + 15
        self.screen.blit(title_text, title_rect)

        # Вкладки категорий
        tabs = ["БОЕВЫЕ", "МАГИЧЕСКИЕ", "РЕМЕСЛЕННЫЕ"]
        tab_width = window_width // 3
        tab_height = 40
        tab_y = window_y + 60

        # Очищаем список прямоугольников вкладок
        self.tab_rects.clear()

        for i, tab_name in enumerate(tabs):
            tab_x = window_x + i * tab_width

            # Сохраняем прямоугольник вкладки для обработки мыши
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
            self.tab_rects.append(tab_rect)

            # Цвет вкладки
            if i == self.selected_tab:
                tab_color = (60, 60, 80)
                text_color = (255, 255, 100)
            else:
                tab_color = (30, 30, 35)
                text_color = (180, 180, 180)

            # Фон вкладки
            pygame.draw.rect(
                self.screen,
                tab_color,
                tab_rect
            )

            # Рамка вкладки
            pygame.draw.rect(
                self.screen,
                (100, 100, 100),
                tab_rect,
                2
            )

            # Текст вкладки
            tab_text = self.font.render(tab_name, True, text_color)
            tab_text_rect = tab_text.get_rect()
            tab_text_rect.center = (tab_x + tab_width // 2, tab_y + tab_height // 2)
            self.screen.blit(tab_text, tab_text_rect)

        # Получаем умения текущей категории
        categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
        current_category = categories[self.selected_tab]
        skills_dict = player.skill_manager.get_all_skills()
        skills = [skill for skill in skills_dict.values() if skill.category == current_category]

        # Область списка умений
        skills_list_y = tab_y + tab_height + 20
        skills_list_height = window_height - 250

        # Очищаем списки rect'ов
        self.skill_rects.clear()

        # Отрисовка списка умений
        if skills:
            for idx, skill in enumerate(skills):
                if idx >= 5:  # Ограничиваем количество отображаемых умений
                    break

                skill_y = skills_list_y + idx * 90
                skill_x = window_x + 20

                # Сохраняем прямоугольник умения для обработки мыши
                skill_rect = pygame.Rect(skill_x, skill_y, window_width - 40, 85)
                self.skill_rects.append(skill_rect)

                # Фон умения
                if idx == self.selected_skill_index:
                    bg_color = (60, 60, 80)
                else:
                    bg_color = (45, 45, 50)

                pygame.draw.rect(
                    self.screen,
                    bg_color,
                    skill_rect
                )

                # Рамка умения
                pygame.draw.rect(
                    self.screen,
                    (100, 100, 100),
                    skill_rect,
                    2
                )

                # Название умения и ранг
                skill_name_text = self.font.render(
                    f"{skill.name} [Ранг {skill.rank}/{skill.max_rank}]",
                    True,
                    (255, 255, 255)
                )
                self.screen.blit(skill_name_text, (skill_x + 10, skill_y + 5))

                # Текущий эффект ранга (вместо базового описания)
                current_rank_desc = skill.get_current_rank_description() if hasattr(skill, 'get_current_rank_description') else skill.base_description[:80]
                skill_desc_text = self.info_font.render(
                    current_rank_desc[:85],
                    True,
                    (150, 255, 150)  # Зелёный цвет для текущего эффекта
                )
                self.screen.blit(skill_desc_text, (skill_x + 10, skill_y + 28))

                # Прогресс до следующего ранга
                if skill.rank < skill.max_rank:
                    # Первая строка условий: опыт и использования
                    exp_color = (100, 255, 100) if skill.experience >= skill.experience_to_next_rank else (200, 200, 100)
                    use_color = (100, 255, 100) if skill.use_count >= skill.get_required_uses_for_rank() else (200, 200, 100)

                    cond_text1 = self.info_font.render(
                        f"Опыт: {skill.experience}/{skill.experience_to_next_rank}  |  Использований: {skill.use_count}/{skill.get_required_uses_for_rank()}",
                        True,
                        (180, 180, 180)
                    )
                    self.screen.blit(cond_text1, (skill_x + 10, skill_y + 48))

                    # Вторая строка условий: уровень и золото
                    cond_text2 = self.info_font.render(
                        f"Треб. уровень: {skill.get_required_player_level_for_rank()}  |  Золото: {skill.get_gold_cost_for_rank()}",
                        True,
                        (255, 200, 100)
                    )
                    self.screen.blit(cond_text2, (skill_x + 10, skill_y + 66))
                else:
                    max_rank_text = self.info_font.render(
                        "МАКСИМАЛЬНЫЙ РАНГ",
                        True,
                        (255, 215, 0)
                    )
                    self.screen.blit(max_rank_text, (skill_x + 10, skill_y + 48))

                # Стоимость и перезарядка
                cost_parts = []
                if skill.mana_cost > 0:
                    cost_parts.append(f"MP:{skill.mana_cost}")
                if skill.stamina_cost > 0:
                    cost_parts.append(f"ST:{skill.stamina_cost}")
                if skill.cooldown > 0:
                    cost_parts.append(f"CD:{skill.cooldown}")

                if cost_parts:
                    cost_text = " ".join(cost_parts)
                    cost_render = self.info_font.render(cost_text, True, (150, 150, 200))
                    self.screen.blit(cost_render, (skill_x + window_width - 250, skill_y + 66))
        else:
            # Нет умений в этой категории
            no_skills_text = self.font.render(
                "Нет изученных умений в этой категории",
                True,
                (150, 150, 150)
            )
            no_skills_rect = no_skills_text.get_rect()
            no_skills_rect.center = (window_x + window_width // 2, skills_list_y + 100)
            self.screen.blit(no_skills_text, no_skills_rect)

        # Панель слотов быстрого доступа внизу
        slots_panel_y = window_y + window_height - 100
        slot_size = 60
        slot_spacing = 10
        slots_start_x = window_x + (window_width - (slot_size + slot_spacing) * 8) // 2

        # Заголовок слотов
        slots_title = self.font.render("СЛОТЫ БЫСТРОГО ДОСТУПА (1-8)", True, (200, 200, 200))
        slots_title_rect = slots_title.get_rect()
        slots_title_rect.centerx = window_x + window_width // 2
        slots_title_rect.y = slots_panel_y - 30
        self.screen.blit(slots_title, slots_title_rect)

        # Очищаем список rect'ов слотов
        self.slot_rects.clear()

        # Отрисовка слотов
        for i in range(8):
            slot_x = slots_start_x + i * (slot_size + slot_spacing)
            slot_skill = player.skill_manager.get_slot_skill(i)

            # Сохраняем прямоугольник слота для обработки мыши
            slot_rect = pygame.Rect(slot_x, slots_panel_y, slot_size, slot_size)
            self.slot_rects.append(slot_rect)

            # Фон слота
            if i == self.selected_slot_index:
                bg_color = (80, 80, 100)
            elif slot_skill:
                if slot_skill.category == SkillCategory.COMBAT:
                    bg_color = (60, 40, 40)
                elif slot_skill.category == SkillCategory.MAGIC:
                    bg_color = (40, 40, 60)
                elif slot_skill.category == SkillCategory.CRAFTING:
                    bg_color = (50, 50, 40)
                else:
                    bg_color = (40, 40, 40)
            else:
                bg_color = (30, 30, 30)

            pygame.draw.rect(
                self.screen,
                bg_color,
                slot_rect
            )

            # Рамка слота
            pygame.draw.rect(
                self.screen,
                (150, 150, 150) if i == self.selected_slot_index else (100, 100, 100),
                slot_rect,
                3 if i == self.selected_slot_index else 2
            )

            # Номер слота
            slot_num_text = self.font.render(str(i + 1), True, (200, 200, 200))
            self.screen.blit(slot_num_text, (slot_x + 5, slots_panel_y + 5))

            # Если в слоте есть умение
            if slot_skill:
                icon_font = pygame.font.Font(None, 36)
                icon_text = icon_font.render(slot_skill.name[0], True, (255, 255, 255))
                icon_rect = icon_text.get_rect()
                icon_rect.center = (slot_x + slot_size // 2, slots_panel_y + slot_size // 2)
                self.screen.blit(icon_text, icon_rect)

        # Подсказки
        hints_y = window_y + window_height - 30
        hint_text = self.info_font.render(
            "ЛКМ - назначить/выбрать | ПКМ - повысить ранг/убрать | Колёсико - листать | K/ESC - закрыть",
            True,
            (180, 180, 180)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = hints_y
        self.screen.blit(hint_text, hint_rect)

        # Всплывающая подсказка при наведении на умение
        mouse_pos = pygame.mouse.get_pos()
        for i, rect in enumerate(self.skill_rects):
            if rect.collidepoint(mouse_pos) and i < len(skills):
                self._render_skill_tooltip(skills[i], mouse_pos)
                break

    def _render_skill_tooltip(self, skill, mouse_pos):
        """
        Отрисовать всплывающую подсказку с развитием умения по рангам

        Args:
            skill: Объект умения
            mouse_pos: Позиция мыши
        """
        import pygame

        # Получаем информацию о развитии по рангам
        progression_info = skill.get_rank_progression_info() if hasattr(skill, 'get_rank_progression_info') else []

        if not progression_info:
            return

        # Параметры подсказки
        tooltip_padding = 10
        line_height = 20
        tooltip_width = 350

        # Формируем строки подсказки
        lines = []
        lines.append((f"Развитие умения: {skill.name}", (255, 215, 0), True))
        lines.append(("", (0, 0, 0), False))  # Пустая строка
        lines.append((f"Описание: {skill.base_description}", (180, 180, 180), False))
        lines.append(("", (0, 0, 0), False))  # Пустая строка
        lines.append(("Прогрессия по рангам:", (200, 200, 255), True))

        for i, rank_info in enumerate(progression_info):
            # Подсветка текущего ранга
            if i + 1 == skill.rank:
                lines.append((f"► {rank_info}", (100, 255, 100), False))
            else:
                lines.append((f"  {rank_info}", (180, 180, 180), False))

        # Добавляем информацию о стоимости
        lines.append(("", (0, 0, 0), False))
        lines.append((f"Мана: {skill.mana_cost} | Выносливость: {skill.stamina_cost} | CD: {skill.cooldown}", (100, 200, 255), False))

        # Вычисляем размер подсказки
        tooltip_height = tooltip_padding * 2 + len(lines) * line_height

        # Позиция подсказки (справа от курсора)
        tooltip_x = mouse_pos[0] + 15
        tooltip_y = mouse_pos[1] + 15

        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = mouse_pos[0] - tooltip_width - 15
        if tooltip_y + tooltip_height > screen_height:
            tooltip_y = screen_height - tooltip_height - 5

        # Фон подсказки
        pygame.draw.rect(
            self.screen,
            (30, 30, 40),
            (tooltip_x, tooltip_y, tooltip_width, tooltip_height)
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
            if line_text:
                font_to_use = self.font if is_bold else self.info_font
                text_surface = font_to_use.render(line_text[:60], True, line_color)
                self.screen.blit(text_surface, (tooltip_x + tooltip_padding, text_y))
            text_y += line_height


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


class QuestWindow:
    """Окно квестов города"""

    def __init__(self, screen, font, info_font, ui_scaler=None):
        """
        Инициализация окна квестов

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

        # Состояние окна
        self.mode = "available"  # available, active, turn_in
        self.selected_index = 0
        self.scroll_offset = 0

        # Данные
        self.location_name = ""
        self.location_id = None
        self.available_quests = []
        self.active_quests = []
        self.turn_in_quests = []

        # Для хранения координат элементов при рендеринге
        self.tab_rects = []      # Прямоугольники вкладок
        self.quest_rects = []    # Прямоугольники квестов
        self.window_rect = None  # Прямоугольник окна

    def set_data(self, location_name, location_id, available_quests, active_quests, turn_in_quests):
        """
        Установить данные для отображения

        Args:
            location_name: Название локации
            location_id: ID локации
            available_quests: Доступные квесты в локации
            active_quests: Активные квесты игрока
            turn_in_quests: Квесты готовые к сдаче
        """
        self.location_name = location_name
        self.location_id = location_id
        self.available_quests = available_quests
        self.active_quests = active_quests
        self.turn_in_quests = turn_in_quests
        self.selected_index = 0
        self.scroll_offset = 0

        # Если есть квесты для сдачи, открываем на этой вкладке
        if turn_in_quests:
            self.mode = "turn_in"
        elif available_quests:
            self.mode = "available"
        else:
            self.mode = "active"

    def get_current_list(self):
        """Получить текущий список квестов"""
        if self.mode == "available":
            return self.available_quests
        elif self.mode == "active":
            return self.active_quests
        else:
            return self.turn_in_quests

    def get_selected_quest(self):
        """Получить выбранный квест"""
        quests = self.get_current_list()
        if quests and 0 <= self.selected_index < len(quests):
            return quests[self.selected_index]
        return None

    def handle_mouse_event(self, event, game):
        """
        Обработка событий мыши в окне квестов

        Args:
            event: Событие pygame
            game: Объект игры

        Returns:
            str: Действие для выполнения ('accept', 'turn_in', 'abandon') или None
        """
        import pygame

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Проверяем клик по вкладкам
            for i, rect in enumerate(self.tab_rects):
                if rect.collidepoint(mouse_pos):
                    modes = ["available", "active", "turn_in"]
                    self.mode = modes[i]
                    self.selected_index = 0
                    self.scroll_offset = 0
                    return None

            # Проверяем клик по квестам
            for i, rect in enumerate(self.quest_rects):
                if rect.collidepoint(mouse_pos):
                    quest_idx = i + self.scroll_offset
                    quests = self.get_current_list()
                    if quest_idx < len(quests):
                        self.selected_index = quest_idx

                        # Левая кнопка - выбор, двойной клик - действие
                        if event.button == 1:
                            # Проверяем двойной клик
                            if hasattr(self, '_last_click_time'):
                                import time
                                if time.time() - self._last_click_time < 0.3:
                                    # Двойной клик - выполняем действие
                                    if self.mode == "available":
                                        return 'accept'
                                    elif self.mode == "turn_in":
                                        return 'turn_in'
                            import time
                            self._last_click_time = time.time()

                        # Правая кнопка - действие
                        elif event.button == 3:
                            if self.mode == "available":
                                return 'accept'
                            elif self.mode == "active":
                                return 'abandon'
                            elif self.mode == "turn_in":
                                return 'turn_in'
                    return None

            # Прокрутка колёсиком мыши
            if event.button == 4:  # Колёсико вверх
                if self.scroll_offset > 0:
                    self.scroll_offset -= 1
                return None
            elif event.button == 5:  # Колёсико вниз
                quests = self.get_current_list()
                # Определяем количество видимых квестов
                if self.window_rect:
                    quest_height = 95
                    list_height = self.window_rect.height - 200
                    visible_quests = list_height // quest_height
                    max_scroll = max(0, len(quests) - visible_quests)
                    if self.scroll_offset < max_scroll:
                        self.scroll_offset += 1
                return None

        return None

    def render(self, player):
        """Отрисовать окно квестов"""
        import pygame
        from game.quests import QuestStatus

        # Затемняем фон
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные)
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        if self.ui_scaler:
            window_width = self.ui_scaler.scale_width(900)
            window_height = self.ui_scaler.scale_height(650)
        else:
            window_width = min(900, int(screen_width * 0.85))
            window_height = min(650, int(screen_height * 0.75))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Сохраняем прямоугольник окна
        self.window_rect = pygame.Rect(window_x, window_y, window_width, window_height)

        # Очищаем списки прямоугольников
        self.tab_rects = []
        self.quest_rects = []

        # Фон окна
        pygame.draw.rect(
            self.screen,
            (40, 40, 45),
            (window_x, window_y, window_width, window_height)
        )

        # Рамка окна
        pygame.draw.rect(
            self.screen,
            (200, 180, 100),
            (window_x, window_y, window_width, window_height),
            3
        )

        # Заголовок
        title_text = self.font.render(
            f"КВЕСТЫ - {self.location_name}",
            True,
            (255, 215, 0)
        )
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + 15
        self.screen.blit(title_text, title_rect)

        # Информация о лимите квестов
        from game.quests import QuestManager
        limit_text = self.info_font.render(
            f"Активных квестов: {len(self.active_quests)}/{QuestManager.MAX_ACTIVE_QUESTS}",
            True,
            (150, 150, 150)
        )
        self.screen.blit(limit_text, (window_x + 20, window_y + 50))

        # Вкладки
        tab_y = window_y + 75
        tab_width = (window_width - 60) // 3
        tabs = [
            ("Доступные", "available", len(self.available_quests)),
            ("Активные", "active", len(self.active_quests)),
            ("Готовые к сдаче", "turn_in", len(self.turn_in_quests))
        ]

        for i, (tab_name, tab_mode, count) in enumerate(tabs):
            tab_x = window_x + 20 + i * (tab_width + 10)
            is_selected = self.mode == tab_mode

            # Сохраняем прямоугольник вкладки
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, 30)
            self.tab_rects.append(tab_rect)

            # Фон вкладки
            tab_color = (80, 80, 90) if is_selected else (50, 50, 55)
            pygame.draw.rect(
                self.screen,
                tab_color,
                (tab_x, tab_y, tab_width, 30)
            )

            # Рамка вкладки
            border_color = (255, 215, 0) if is_selected else (100, 100, 100)
            pygame.draw.rect(
                self.screen,
                border_color,
                (tab_x, tab_y, tab_width, 30),
                2
            )

            # Текст вкладки
            text_color = (255, 215, 0) if is_selected else (180, 180, 180)
            tab_text = self.info_font.render(
                f"{tab_name} ({count})",
                True,
                text_color
            )
            tab_text_rect = tab_text.get_rect()
            tab_text_rect.centerx = tab_x + tab_width // 2
            tab_text_rect.centery = tab_y + 15
            self.screen.blit(tab_text, tab_text_rect)

        # Область списка квестов
        list_y = tab_y + 45
        list_height = window_height - 200
        list_width = window_width - 40

        # Фон списка
        pygame.draw.rect(
            self.screen,
            (30, 30, 35),
            (window_x + 20, list_y, list_width, list_height)
        )

        # Текущий список квестов
        quests = self.get_current_list()

        if not quests:
            no_quests_text = self.info_font.render(
                "Нет доступных квестов" if self.mode == "available"
                else "Нет активных квестов" if self.mode == "active"
                else "Нет квестов для сдачи",
                True,
                (150, 150, 150)
            )
            no_quests_rect = no_quests_text.get_rect()
            no_quests_rect.centerx = window_x + window_width // 2
            no_quests_rect.centery = list_y + list_height // 2
            self.screen.blit(no_quests_text, no_quests_rect)
        else:
            # Отображаем список квестов
            quest_height = 95
            visible_quests = list_height // quest_height

            for i in range(min(visible_quests, len(quests))):
                quest_idx = i + self.scroll_offset
                if quest_idx >= len(quests):
                    break

                quest = quests[quest_idx]
                quest_y = list_y + i * quest_height

                # Сохраняем прямоугольник квеста
                quest_rect = pygame.Rect(window_x + 25, quest_y + 5, list_width - 10, quest_height - 10)
                self.quest_rects.append(quest_rect)

                # Фон элемента
                is_selected = quest_idx == self.selected_index
                is_unique = getattr(quest, 'is_unique', False)
                is_starter = getattr(quest, 'is_starter', False)

                # Цвет фона: уникальные - темно-красный, стартовые - темно-зеленый, обычные - серый
                if is_unique:
                    bg_color = (70, 40, 40) if is_selected else (50, 30, 30)
                elif is_starter:
                    bg_color = (40, 60, 40) if is_selected else (30, 45, 30)
                else:
                    bg_color = (60, 60, 70) if is_selected else (40, 40, 45)

                pygame.draw.rect(
                    self.screen,
                    bg_color,
                    (window_x + 25, quest_y + 5, list_width - 10, quest_height - 10)
                )

                # Рамка: уникальные - красная, стартовые - зеленая, выбранные - золотая
                if is_unique:
                    # Красная рамка для уникальных квестов (всегда)
                    border_color = (255, 100, 100) if is_selected else (200, 50, 50)
                    pygame.draw.rect(
                        self.screen,
                        border_color,
                        (window_x + 25, quest_y + 5, list_width - 10, quest_height - 10),
                        3 if is_selected else 2
                    )
                elif is_starter:
                    # Зеленая рамка для стартовых квестов (всегда)
                    border_color = (100, 255, 100) if is_selected else (50, 200, 50)
                    pygame.draw.rect(
                        self.screen,
                        border_color,
                        (window_x + 25, quest_y + 5, list_width - 10, quest_height - 10),
                        3 if is_selected else 2
                    )
                elif is_selected:
                    # Золотая рамка только для выбранных обычных квестов
                    pygame.draw.rect(
                        self.screen,
                        (255, 215, 0),
                        (window_x + 25, quest_y + 5, list_width - 10, quest_height - 10),
                        2
                    )

                # Название квеста с цветом по типу
                difficulty_str = f" [{quest.difficulty.display_name}]" if hasattr(quest.difficulty, 'display_name') else ""
                if is_unique:
                    name_color = (255, 150, 150)  # Красноватый для уникальных
                elif is_starter:
                    name_color = (150, 255, 150)  # Зеленоватый для стартовых
                else:
                    name_color = (255, 255, 255)  # Белый для обычных

                name_text = self.font.render(
                    f"{quest.name}{difficulty_str}",
                    True,
                    name_color
                )
                self.screen.blit(name_text, (window_x + 35, quest_y + 10))

                # Место выдачи квеста (если есть)
                if quest.giver_location:
                    giver_text = self.info_font.render(
                        f"Место: {quest.giver_location}",
                        True,
                        (150, 200, 255)
                    )
                    self.screen.blit(giver_text, (window_x + 35, quest_y + 32))
                    desc_y_offset = 50
                else:
                    desc_y_offset = 32

                # Описание
                desc_text = self.info_font.render(
                    quest.description[:60] + "..." if len(quest.description) > 60 else quest.description,
                    True,
                    (180, 180, 180)
                )
                self.screen.blit(desc_text, (window_x + 35, quest_y + desc_y_offset))

                # Цели и награды
                if quest.objectives:
                    obj = quest.objectives[0]
                    progress = f"{obj.current_count}/{obj.required_count}"
                    obj_text = self.info_font.render(
                        f"Цель: {obj.description[:30]}... ({progress})" if len(obj.description) > 30
                        else f"Цель: {obj.description} ({progress})",
                        True,
                        (100, 255, 100) if obj.is_completed() else (200, 200, 100)
                    )
                    obj_y_offset = desc_y_offset + 22
                    self.screen.blit(obj_text, (window_x + 35, quest_y + obj_y_offset))

                # Награды (справа)
                rewards_parts = []
                if 'exp' in quest.rewards:
                    rewards_parts.append(f"{quest.rewards['exp']} XP")
                if 'gold' in quest.rewards:
                    rewards_parts.append(f"{quest.rewards['gold']}g")
                rewards_str = " | ".join(rewards_parts)

                rewards_text = self.info_font.render(
                    rewards_str,
                    True,
                    (255, 215, 0)
                )
                rewards_rect = rewards_text.get_rect()
                rewards_rect.right = window_x + window_width - 35
                rewards_rect.y = quest_y + 32
                self.screen.blit(rewards_text, rewards_rect)

        # Подсказки управления
        controls_y = window_y + window_height - 50

        if self.mode == "available":
            action_text = "Enter/ПКМ - Принять"
        elif self.mode == "active":
            action_text = "Delete/ПКМ - Отменить"
        else:
            action_text = "Enter/ПКМ - Сдать"

        controls_text = self.info_font.render(
            f"Tab/Клик - Вкладки | W/S/Колёсико - Выбор | {action_text} | Esc - Закрыть",
            True,
            (150, 150, 150)
        )
        controls_rect = controls_text.get_rect()
        controls_rect.centerx = window_x + window_width // 2
        controls_rect.y = controls_y
        self.screen.blit(controls_text, controls_rect)


class RandomEventWindow:
    """Окно отображения случайных событий"""

    def __init__(self, screen, font, info_font, ui_scaler=None):
        """
        Инициализация окна событий

        Args:
            screen: Экран pygame
            font: Основной шрифт
            info_font: Информационный шрифт
            ui_scaler: Объект масштабирования UI
        """
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.ui_scaler = ui_scaler

        # Кнопка закрытия
        self.close_button_rect = None

    def handle_input(self, event):
        """
        Обработать ввод

        Args:
            event: Событие pygame

        Returns:
            bool: True если окно нужно закрыть
        """
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE]:
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                mouse_pos = event.pos
                # Проверяем клик по кнопке закрытия
                if self.close_button_rect and self.close_button_rect.collidepoint(mouse_pos):
                    return True

        return False

    def render(self, event_result):
        """
        Отрисовать окно события

        Args:
            event_result: Объект EventResult с информацией о событии
        """
        if not event_result or not event_result.event:
            return

        screen_width, screen_height = self.screen.get_size()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна
        if self.ui_scaler:
            window_width = self.ui_scaler.scale_width(500)
            window_height = self.ui_scaler.scale_height(350)
        else:
            window_width = 500
            window_height = 350

        # Центрирование
        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Цвета в зависимости от типа события
        event = event_result.event
        from game.events import EventType

        if event.event_type == EventType.POSITIVE:
            border_color = (100, 200, 100)  # Зелёный
            title_color = (150, 255, 150)
            icon_color = (100, 255, 100)
        elif event.event_type == EventType.NEGATIVE:
            border_color = (200, 100, 100)  # Красный
            title_color = (255, 150, 150)
            icon_color = (255, 100, 100)
        else:
            border_color = (200, 180, 100)  # Жёлтый/нейтральный
            title_color = (255, 215, 0)
            icon_color = (255, 215, 0)

        # Фон окна
        pygame.draw.rect(self.screen, (40, 40, 45),
                        (window_x, window_y, window_width, window_height))

        # Рамка
        pygame.draw.rect(self.screen, border_color,
                        (window_x, window_y, window_width, window_height), 3)

        # Заголовок с иконкой
        header_height = 50
        pygame.draw.rect(self.screen, (35, 35, 45),
                        (window_x + 3, window_y + 3, window_width - 6, header_height))

        # Иконка события
        icon_text = self.font.render(f"[{event.icon}]", True, icon_color)
        icon_rect = icon_text.get_rect()
        icon_rect.x = window_x + 15
        icon_rect.centery = window_y + header_height // 2
        self.screen.blit(icon_text, icon_rect)

        # Название события
        title_text = self.font.render(event.name, True, title_color)
        title_rect = title_text.get_rect()
        title_rect.x = window_x + 60
        title_rect.centery = window_y + header_height // 2
        self.screen.blit(title_text, title_rect)

        # Ранг игрока
        rank_text = self.info_font.render(
            f"Ранг: {event_result.player_rank}",
            True, (150, 150, 150)
        )
        rank_rect = rank_text.get_rect()
        rank_rect.right = window_x + window_width - 15
        rank_rect.centery = window_y + header_height // 2
        self.screen.blit(rank_text, rank_rect)

        # Описание события
        content_y = window_y + header_height + 20

        # Разбиваем описание на строки
        description = event.description
        words = description.split(' ')
        lines = []
        current_line = ""
        max_width = window_width - 40

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surface = self.info_font.render(test_line, True, (255, 255, 255))
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Отрисовка описания
        for line in lines:
            desc_text = self.info_font.render(line, True, (220, 220, 220))
            self.screen.blit(desc_text, (window_x + 20, content_y))
            content_y += 25

        # Разделитель
        content_y += 10
        pygame.draw.line(self.screen, (80, 80, 90),
                        (window_x + 20, content_y),
                        (window_x + window_width - 20, content_y), 1)
        content_y += 15

        # Эффекты события
        effects_title = self.info_font.render("Эффекты:", True, (200, 200, 100))
        self.screen.blit(effects_title, (window_x + 20, content_y))
        content_y += 30

        for effect in event_result.effects:
            # Цвет эффекта в зависимости от содержимого
            if "Получено" in effect or "Восстановлено" in effect:
                effect_color = (100, 255, 100)
            elif "Потеряно" in effect or "урона" in effect:
                effect_color = (255, 100, 100)
            else:
                effect_color = (200, 200, 200)

            effect_text = self.info_font.render(effect, True, effect_color)
            self.screen.blit(effect_text, (window_x + 20, content_y))
            content_y += 22

        # Кнопка закрытия
        button_width = 120
        button_height = 35
        button_x = window_x + (window_width - button_width) // 2
        button_y = window_y + window_height - button_height - 15

        self.close_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # Фон кнопки
        pygame.draw.rect(self.screen, (60, 60, 70), self.close_button_rect)
        pygame.draw.rect(self.screen, border_color, self.close_button_rect, 2)

        # Текст кнопки
        button_text = self.info_font.render("OK", True, (255, 255, 255))
        button_text_rect = button_text.get_rect(center=self.close_button_rect.center)
        self.screen.blit(button_text, button_text_rect)

        # Подсказка
        hint_text = self.info_font.render(
            "Нажмите Enter/Esc или кликните OK для закрытия",
            True, (100, 100, 100)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = window_y + window_height - 55
        self.screen.blit(hint_text, hint_rect)


class CheatMenuWindow:
    """Окно чит-меню с возможностью включать/отключать отдельные читы"""

    def __init__(self, screen, font, info_font, scaler=None):
        """
        Инициализация окна чит-меню

        Args:
            screen: Pygame экран
            font: Основной шрифт
            info_font: Информационный шрифт
            scaler: UIScaler для адаптивного масштабирования (опционально)
        """
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.scaler = scaler

        # Состояние читов
        self.cheats = {
            'godmode': {'name': 'Режим бессмертия', 'enabled': False},
            'reveal_map': {'name': 'Открыть карту', 'enabled': False},
            'give_gold': {'name': 'Дать 5000 золота', 'enabled': False, 'one_time': True},
            'give_books': {'name': 'Дать все книги умений', 'enabled': False, 'one_time': True},
            'teleport_academy': {'name': 'Телепорт к академии магов', 'enabled': False, 'one_time': True},
            'level_up': {'name': 'Повысить уровень на 1', 'enabled': False, 'one_time': True},
            'give_artifact': {'name': 'Дать случайный артефакт', 'enabled': False, 'one_time': True},
        }

        self.selected_index = 0
        self.button_rects = []  # Прямоугольники кнопок для обработки мыши

    def handle_input(self, event, game):
        """
        Обработка ввода в чит-меню

        Args:
            event: Pygame событие
            game: Ссылка на основной объект игры

        Returns:
            bool: True если меню нужно закрыть
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_F2:
                return True

            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_index = max(0, self.selected_index - 1)

            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_index = min(len(self.cheats) - 1, self.selected_index + 1)

            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # Активировать выбранный чит
                self._activate_cheat(list(self.cheats.keys())[self.selected_index], game)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                mouse_pos = event.pos
                for i, rect in enumerate(self.button_rects):
                    if rect.collidepoint(mouse_pos):
                        self._activate_cheat(list(self.cheats.keys())[i], game)
                        break

        return False

    def _activate_cheat(self, cheat_id, game):
        """
        Активировать чит

        Args:
            cheat_id: ID чита
            game: Ссылка на основной объект игры
        """
        cheat = self.cheats[cheat_id]

        # Для одноразовых читов просто выполняем действие
        if cheat.get('one_time'):
            if cheat_id == 'give_gold':
                game.player.inventory.add_gold(5000)
                print("Получено 5000 золота!")

            elif cheat_id == 'give_books':
                from game.inventory import PREDEFINED_ITEMS
                skill_books = [
                    # Магические поддерживающие
                    "book_heal", "book_regeneration", "book_stamina_recovery",
                    "book_mage_shield",
                    # Боевые общие
                    "book_power_strike", "book_poison_strike",
                    "book_stun_strike", "book_battle_cry",
                    # Магические атакующие
                    "book_magic_missile", "book_fireball",
                    "book_ice_bolt", "book_lightning",
                    # Оружейные - лук
                    "book_precise_shot", "book_rapid_fire", "book_piercing_arrow",
                    # Оружейные - кинжал
                    "book_backstab", "book_bleeding_cut", "book_shadow_step",
                    # Оружейные - меч
                    "book_whirlwind_strike", "book_shield_breaker", "book_blade_dance"
                ]
                for book_id in skill_books:
                    if book_id in PREDEFINED_ITEMS:
                        game.player.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)
                print("Получены все книги умений!")

            elif cheat_id == 'teleport_academy':
                # Ищем академию магов на карте
                academy_found = False
                for location in game.game_map.locations:
                    if location.location_type == 'magic_school':
                        # Ищем свободную клетку в радиусе 10 от академии
                        import random
                        for _ in range(100):  # 100 попыток
                            dx = random.randint(-10, 10)
                            dy = random.randint(-10, 10)
                            new_x = location.x + dx
                            new_y = location.y + dy

                            if game.game_map.is_valid_position(new_x, new_y):
                                tile = game.game_map.get_tile(new_x, new_y)
                                if tile.is_passable():
                                    # Телепортируемся без проверки на NPC - сущности могут находиться на одной клетке
                                    game.player.x = new_x
                                    game.player.y = new_y
                                    game.fog_of_war.update_vision(game.player.x, game.player.y)
                                    game.camera.update()
                                    academy_found = True
                                    print(f"Телепортация к {location.name}!")
                                    break

                        if academy_found:
                            break

                if not academy_found:
                    print("Не удалось найти свободное место возле академии!")

            elif cheat_id == 'level_up':
                if game.player.level < 40:
                    game.player.level += 1
                    game.player.stat_points += 5
                    game.player.update_derived_stats()
                    print(f"Уровень повышен до {game.player.level}! Получено 5 очков характеристик.")
                else:
                    print("Достигнут максимальный уровень (40)!")

            elif cheat_id == 'give_artifact':
                from game.inventory import ItemGenerator, ItemQuality, EquipmentSlot, ArmorType
                import random
                # Генерируем случайный артефакт
                item_type = random.choice(['weapon', 'armor'])
                try:
                    if item_type == 'weapon':
                        # Правильные параметры: level, quality, max_quality
                        artifact = ItemGenerator.generate_weapon(
                            level=game.player.level,
                            quality=ItemQuality.ARTIFACT,
                            max_quality=ItemQuality.ARTIFACT
                        )
                    else:
                        # Правильные параметры: level, slot, armor_type, quality
                        slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST,
                                            EquipmentSlot.HANDS, EquipmentSlot.FEET])
                        armor_type = random.choice(list(ArmorType))
                        artifact = ItemGenerator.generate_armor(
                            level=game.player.level,
                            slot=slot,
                            armor_type=armor_type,
                            quality=ItemQuality.ARTIFACT
                        )

                    if game.player.inventory.add_item(artifact, 1):
                        print(f"Получен артефакт: {artifact.name}!")
                    else:
                        print("Не удалось добавить артефакт - инвентарь переполнен!")
                except Exception as e:
                    print(f"Ошибка при создании артефакта: {e}")
                    import traceback
                    traceback.print_exc()

        else:
            # Для постоянных читов переключаем состояние
            cheat['enabled'] = not cheat['enabled']

            if cheat_id == 'godmode':
                game.player.godmode = cheat['enabled']
                if cheat['enabled']:
                    print("Режим бессмертия ВКЛЮЧЕН")
                else:
                    print("Режим бессмертия ВЫКЛЮЧЕН")

            elif cheat_id == 'reveal_map':
                if cheat['enabled']:
                    # Открываем всю карту
                    for x in range(game.game_map.width):
                        for y in range(game.game_map.height):
                            tile = game.game_map.get_tile(x, y)
                            if tile:
                                tile.explored = True
                    print("Карта ОТКРЫТА")
                else:
                    # Закрываем карту (кроме видимой области)
                    game.fog_of_war.update_vision(game.player.x, game.player.y)
                    print("Карта ЗАКРЫТА")

    def render(self):
        """Отрисовка окна чит-меню"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна
        if self.scaler:
            window_width = self.scaler.scale_width(700)
            window_height = self.scaler.scale_height(550)
        else:
            window_width = min(700, int(screen_width * 0.7))
            window_height = min(550, int(screen_height * 0.7))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна с градиентом
        UIHelper.draw_gradient_rect(
            self.screen, window_x, window_y, window_width, window_height,
            (40, 40, 50), (60, 60, 75)
        )

        # Рамка окна
        pygame.draw.rect(
            self.screen,
            (150, 150, 200),
            (window_x, window_y, window_width, window_height),
            4
        )

        # Заголовок
        title_text = self.font.render("⚙ ЧИТ-МЕНЮ ⚙", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + 15
        self.screen.blit(title_text, title_rect)

        # Подзаголовок
        subtitle_text = self.info_font.render(
            "Нажмите на кнопку или используйте клавиши W/S и Enter",
            True, (150, 150, 150)
        )
        subtitle_rect = subtitle_text.get_rect()
        subtitle_rect.centerx = window_x + window_width // 2
        subtitle_rect.y = window_y + 50
        self.screen.blit(subtitle_text, subtitle_rect)

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            (100, 100, 150),
            (window_x + 10, window_y + 80),
            (window_x + window_width - 10, window_y + 80),
            2
        )

        # Кнопки читов
        self.button_rects = []
        button_y = window_y + 100
        button_height = 50
        button_margin = 10
        button_width = window_width - 60

        for i, (cheat_id, cheat) in enumerate(self.cheats.items()):
            button_x = window_x + 30
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            self.button_rects.append(button_rect)

            # Фон кнопки
            if i == self.selected_index:
                # Выделенная кнопка
                bg_color = (70, 70, 90)
                border_color = (200, 200, 100)
                border_width = 3
            else:
                bg_color = (50, 50, 65)
                border_color = (100, 100, 120)
                border_width = 2

            pygame.draw.rect(self.screen, bg_color, button_rect)
            pygame.draw.rect(self.screen, border_color, button_rect, border_width)

            # Текст кнопки
            button_text = self.info_font.render(cheat['name'], True, (255, 255, 255))
            text_rect = button_text.get_rect()
            text_rect.left = button_x + 15
            text_rect.centery = button_y + button_height // 2
            self.screen.blit(button_text, text_rect)

            # Статус для постоянных читов
            if not cheat.get('one_time'):
                status_text = "ВКЛ" if cheat['enabled'] else "ВЫКЛ"
                status_color = (100, 255, 100) if cheat['enabled'] else (150, 150, 150)
                status_surface = self.info_font.render(status_text, True, status_color)
                status_rect = status_surface.get_rect()
                status_rect.right = button_x + button_width - 15
                status_rect.centery = button_y + button_height // 2
                self.screen.blit(status_surface, status_rect)

            button_y += button_height + button_margin

        # Подсказка внизу
        hint_text = self.info_font.render(
            "F2 или ESC - закрыть меню",
            True, (100, 100, 120)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = window_y + window_height - 35
        self.screen.blit(hint_text, hint_rect)
