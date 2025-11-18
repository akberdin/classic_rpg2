"""
Модуль UI компонентов для игры
Содержит все интерфейсные окна и элементы
"""
import pygame
from game.constants import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT
from game.inventory import EquipmentSlot, EquipmentItem


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

    def __init__(self, screen, font, info_font):
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.is_open = False

        self.help_data = [
            ("=== УПРАВЛЕНИЕ ===", None),
            ("Перемещение:", "W/A/S/D или Стрелки"),
            ("Отдых:", "R - восстановить здоровье и ману"),
            ("Работа:", "T - получить опыт и золото"),
            ("Взаимодействие:", "E - разговор с NPC"),
            ("Сбор ресурсов:", "F - собрать лут с локации"),
            ("Инвентарь:", "I - открыть/закрыть"),
            ("Помощь:", "F1 - открыть/закрыть это окно"),
            ("Выход:", "ESC - выйти из игры"),
            ("", None),
            ("=== ИНВЕНТАРЬ ===", None),
            ("Навигация:", "W/S - выбор предмета"),
            ("Использовать:", "Enter/U - использовать предмет"),
            ("Экипировать:", "E - экипировать предмет"),
            ("Снять:", "Q - снять выбранный предмет"),
            ("Закрыть:", "I/ESC - закрыть инвентарь"),
            ("", None),
            ("=== БОЙ ===", None),
            ("Атака:", "1 - обычная атака"),
            ("Сильная атака:", "2 - мощная атака (-10 выносл.)"),
            ("Защита:", "3 - защититься на ход"),
            ("Магия:", "4 - магическая атака (-20 маны)"),
            ("Побег:", "5 - попытка сбежать"),
        ]

    def toggle(self):
        """Переключить состояние окна"""
        self.is_open = not self.is_open

    def render(self):
        """Отрисовка окна помощи"""
        if not self.is_open:
            return

        # Затемнение фона
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна
        window_width = 700
        window_height = 600
        window_x = (WINDOW_WIDTH - window_width) // 2
        window_y = (WINDOW_HEIGHT - window_height) // 2

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
        title_rect.y = window_y + 15
        self.screen.blit(title_text, title_rect)

        # Подзаголовок
        subtitle = self.info_font.render("Нажмите F1 для закрытия", True, (180, 180, 180))
        subtitle_rect = subtitle.get_rect()
        subtitle_rect.centerx = window_x + window_width // 2
        subtitle_rect.y = window_y + 45
        self.screen.blit(subtitle, subtitle_rect)

        # Разделитель
        pygame.draw.line(
            self.screen,
            (100, 100, 150),
            (window_x + 20, window_y + 70),
            (window_x + window_width - 20, window_y + 70),
            2
        )

        # Содержимое
        content_y = window_y + 85
        line_height = 22

        for label, value in self.help_data:
            if label.startswith("==="):
                # Заголовок раздела
                section_text = self.font.render(label, True, (100, 200, 255))
                section_rect = section_text.get_rect()
                section_rect.x = window_x + 30
                section_rect.y = content_y
                self.screen.blit(section_text, section_rect)
                content_y += line_height + 5
            elif label == "":
                # Пустая строка
                content_y += 10
            else:
                # Обычная строка
                label_text = self.info_font.render(label, True, (200, 200, 200))
                self.screen.blit(label_text, (window_x + 50, content_y))

                if value:
                    value_text = self.info_font.render(value, True, (150, 255, 150))
                    self.screen.blit(value_text, (window_x + 250, content_y))

                content_y += line_height


class InventoryWindow:
    """Улучшенное окно инвентаря с экипировкой"""

    def __init__(self, screen, font, info_font):
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.selected_inventory_index = 0
        self.selected_equipment_slot = None
        self.mode = "inventory"  # "inventory" или "equipment"

    def render(self, player):
        """
        Отрисовка окна инвентаря

        Args:
            player: Объект игрока
        """
        # Затемнение фона
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна
        window_width = 900
        window_height = 650
        window_x = (WINDOW_WIDTH - window_width) // 2
        window_y = (WINDOW_HEIGHT - window_height) // 2

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
        title_rect.y = window_y + 10
        self.screen.blit(title_text, title_rect)

        # Информация о золоте и весе
        gold_text = self.info_font.render(
            f"Золото: {player.inventory.gold}  |  Вес: {player.inventory.current_weight}/{player.inventory.max_weight} кг",
            True,
            (255, 215, 0)
        )
        gold_rect = gold_text.get_rect()
        gold_rect.centerx = window_x + window_width // 2
        gold_rect.y = window_y + 40
        self.screen.blit(gold_text, gold_rect)

        # Разделитель
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (window_x + 10, window_y + 70),
            (window_x + window_width - 10, window_y + 70),
            2
        )

        # Левая панель - экипировка
        equipment_panel_x = window_x + 20
        equipment_panel_y = window_y + 85
        equipment_panel_width = 400
        equipment_panel_height = 500

        self._render_equipment_panel(
            player,
            equipment_panel_x,
            equipment_panel_y,
            equipment_panel_width,
            equipment_panel_height
        )

        # Правая панель - предметы
        inventory_panel_x = window_x + 440
        inventory_panel_y = window_y + 85
        inventory_panel_width = 440
        inventory_panel_height = 500

        self._render_inventory_panel(
            player,
            inventory_panel_x,
            inventory_panel_y,
            inventory_panel_width,
            inventory_panel_height
        )

        # Подсказки внизу
        hints_y = window_y + window_height - 40
        hint_text = self.info_font.render(
            "W/S - выбор | E - экипировать | Q - снять | U - использовать | I/ESC - закрыть",
            True,
            (180, 180, 180)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = hints_y
        self.screen.blit(hint_text, hint_rect)

    def _render_equipment_panel(self, player, x, y, width, height):
        """Отрисовка панели экипировки"""
        # Фон панели
        UIHelper.draw_panel(self.screen, x, y, width, height, (45, 45, 55), (100, 100, 120))

        # Заголовок
        title = self.font.render("Экипировка", True, (150, 200, 255))
        self.screen.blit(title, (x + 10, y + 5))

        # Слоты экипировки
        slot_y = y + 40
        slot_height = 35

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

        for group_name, slots in slot_groups:
            # Название группы
            group_text = self.info_font.render(f"[{group_name}]", True, (180, 180, 200))
            self.screen.blit(group_text, (x + 15, slot_y))
            slot_y += 25

            for slot in slots:
                item = player.inventory.get_equipped_item(slot)

                # Фон слота
                slot_color = (60, 60, 70) if item else (40, 40, 50)
                pygame.draw.rect(
                    self.screen,
                    slot_color,
                    (x + 15, slot_y, width - 30, slot_height - 2)
                )

                # Рамка слота
                border_color = (100, 150, 200) if self.selected_equipment_slot == slot else (80, 80, 90)
                pygame.draw.rect(
                    self.screen,
                    border_color,
                    (x + 15, slot_y, width - 30, slot_height - 2),
                    2 if self.selected_equipment_slot == slot else 1
                )

                # Название слота
                slot_name_text = self.info_font.render(
                    f"{slot_names[slot]}:",
                    True,
                    (150, 150, 150)
                )
                self.screen.blit(slot_name_text, (x + 20, slot_y + 8))

                # Экипированный предмет
                if item:
                    item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
                    item_text = self.info_font.render(
                        item_name[:30],
                        True,
                        item.quality.color if hasattr(item, 'quality') else (200, 200, 200)
                    )
                    self.screen.blit(item_text, (x + 130, slot_y + 8))
                else:
                    empty_text = self.info_font.render("---", True, (100, 100, 100))
                    self.screen.blit(empty_text, (x + 130, slot_y + 8))

                slot_y += slot_height

            slot_y += 10

    def _render_inventory_panel(self, player, x, y, width, height):
        """Отрисовка панели предметов"""
        # Фон панели
        UIHelper.draw_panel(self.screen, x, y, width, height, (45, 45, 55), (100, 100, 120))

        # Заголовок
        title = self.font.render("Предметы", True, (150, 200, 255))
        self.screen.blit(title, (x + 10, y + 5))

        # Информация о слотах
        all_items = player.inventory.get_all_items()
        slots_text = self.info_font.render(
            f"Слотов: {len(all_items)}/{player.inventory.max_slots}",
            True,
            (180, 180, 180)
        )
        self.screen.blit(slots_text, (x + width - 150, y + 10))

        # Список предметов
        if not all_items:
            empty_text = self.info_font.render("Инвентарь пуст", True, (150, 150, 150))
            empty_rect = empty_text.get_rect()
            empty_rect.centerx = x + width // 2
            empty_rect.y = y + 100
            self.screen.blit(empty_text, empty_rect)
        else:
            items_y = y + 40
            item_height = 30
            max_visible_items = 14
            start_index = max(0, self.selected_inventory_index - max_visible_items + 1)
            end_index = min(len(all_items), start_index + max_visible_items)

            for i in range(start_index, end_index):
                item, quantity = all_items[i]
                display_index = i - start_index

                # Цвет фона для выбранного предмета
                if i == self.selected_inventory_index:
                    pygame.draw.rect(
                        self.screen,
                        (80, 80, 100),
                        (x + 10, items_y + display_index * item_height, width - 20, item_height - 2)
                    )

                # Рамка предмета
                if i == self.selected_inventory_index:
                    pygame.draw.rect(
                        self.screen,
                        (120, 150, 200),
                        (x + 10, items_y + display_index * item_height, width - 20, item_height - 2),
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
                self.screen.blit(item_text, (x + 20, items_y + display_index * item_height + 7))

                # Вес
                weight_text = self.info_font.render(
                    f"{item.weight * quantity:.1f}кг",
                    True,
                    (150, 150, 150)
                )
                self.screen.blit(weight_text, (x + width - 120, items_y + display_index * item_height + 7))

                # Стоимость
                value_text = self.info_font.render(
                    f"{item.value}з",
                    True,
                    (255, 215, 0)
                )
                self.screen.blit(value_text, (x + width - 60, items_y + display_index * item_height + 7))


class TradeWindow:
    """Окно торговли с NPC"""

    def __init__(self, screen, font, info_font):
        self.screen = screen
        self.font = font
        self.info_font = info_font
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
        # Затемнение фона
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна
        window_width = 900
        window_height = 650
        window_x = (WINDOW_WIDTH - window_width) // 2
        window_y = (WINDOW_HEIGHT - window_height) // 2

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
        title_text = self.font.render(f"ТОРГОВЛЯ: {merchant.name}", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + 10
        self.screen.blit(title_text, title_rect)

        # Информация о золоте
        player_gold = self.info_font.render(
            f"Ваше золото: {player.inventory.gold}",
            True,
            (255, 215, 0)
        )
        self.screen.blit(player_gold, (window_x + 50, window_y + 45))

        merchant_gold = self.info_font.render(
            f"Золото торговца: {merchant.inventory.gold if hasattr(merchant, 'inventory') else '???'}",
            True,
            (255, 215, 0)
        )
        self.screen.blit(merchant_gold, (window_x + window_width - 300, window_y + 45))

        # Разделитель
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (window_x + 10, window_y + 75),
            (window_x + window_width - 10, window_y + 75),
            2
        )

        # Переключатель режима
        mode_y = window_y + 90
        buy_color = (100, 200, 100) if self.mode == "buy" else (100, 100, 100)
        sell_color = (200, 100, 100) if self.mode == "sell" else (100, 100, 100)

        buy_button = self.font.render("[TAB] ПОКУПКА", True, buy_color)
        sell_button = self.font.render("ПРОДАЖА", True, sell_color)

        self.screen.blit(buy_button, (window_x + 50, mode_y))
        self.screen.blit(sell_button, (window_x + window_width - 200, mode_y))

        # Панели товаров
        goods_y = window_y + 130
        goods_height = 440

        if self.mode == "buy":
            self._render_merchant_goods(merchant, window_x + 30, goods_y, window_width - 60, goods_height)
        else:
            self._render_player_goods(player, window_x + 30, goods_y, window_width - 60, goods_height)

        # Подсказки
        hints_y = window_y + window_height - 35
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

    def __init__(self, screen, font, info_font):
        self.screen = screen
        self.font = font
        self.info_font = info_font
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
        # Затемнение фона
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна
        window_width = 700
        window_height = 600
        window_x = (WINDOW_WIDTH - window_width) // 2
        window_y = (WINDOW_HEIGHT - window_height) // 2

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
        title_rect.y = window_y + 10
        self.screen.blit(title_text, title_rect)

        # Информация о персонаже
        info_y = window_y + 50
        player_rank = player.get_rank()

        info_lines = [
            f"Имя: {player.name}",
            f"Уровень: {player.level} ({player_rank})",
            f"Опыт: {player.experience}/{player.experience_to_next_level}",
            f"Золото: {player.inventory.gold}",
        ]

        for i, line in enumerate(info_lines):
            info_text = self.info_font.render(line, True, (200, 200, 200))
            self.screen.blit(info_text, (window_x + 50, info_y + i * 25))

        # Разделитель
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (window_x + 20, window_y + 180),
            (window_x + window_width - 20, window_y + 180),
            2
        )

        # Характеристики
        stats_y = window_y + 200
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
            points_rect.y = stats_y - 30
            self.screen.blit(points_text, points_rect)

        # Отображение характеристик
        for i, (stat_key, stat_name) in enumerate(self.stats_list):
            display_y = stats_y + i * 40

            # Подсветка выбранной характеристики
            if i == self.selected_stat_index:
                pygame.draw.rect(
                    self.screen,
                    (80, 80, 100),
                    (window_x + 40, display_y - 5, window_width - 80, 35)
                )
                pygame.draw.rect(
                    self.screen,
                    (120, 150, 200),
                    (window_x + 40, display_y - 5, window_width - 80, 35),
                    2
                )

            # Название характеристики
            name_text = self.info_font.render(
                f"{stat_name}:",
                True,
                (220, 220, 220)
            )
            self.screen.blit(name_text, (window_x + 60, display_y))

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
            self.screen.blit(value_text, (window_x + 300, display_y))

            # Кнопка + для добавления очка
            if player.stat_points > 0 and i == self.selected_stat_index:
                plus_text = self.info_font.render("[+]", True, (100, 255, 100))
                self.screen.blit(plus_text, (window_x + window_width - 120, display_y))

        # Дополнительная информация
        additional_y = stats_y + len(self.stats_list) * 40 + 20

        additional_info = [
            f"Здоровье: {player.health}/{player.max_health}",
            f"Мана: {player.mana}/{player.max_mana}",
            f"Выносливость: {player.stamina}/{player.max_stamina}",
            f"Урон: {player.get_total_damage()}",
            f"Защита: {player.get_total_defense()}",
        ]

        for i, line in enumerate(additional_info):
            info_text = self.info_font.render(line, True, (180, 180, 200))
            self.screen.blit(info_text, (window_x + 60, additional_y + i * 25))

        # Подсказки внизу
        hints_y = window_y + window_height - 40
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
