"""
Окно торговли.
"""
import pygame
from game.ui.base import UIHelper
from game.inventory import EquipmentSlot


class TradeWindow:
    """Окно торговли с NPC"""

    # Типы фильтров
    FILTER_TYPES = ["all", "weapon", "armor", "jewelry", "potion", "resource", "book", "recipe"]
    FILTER_NAMES = {
        "all": "Все",
        "weapon": "Оружие",
        "armor": "Броня",
        "jewelry": "Украш.",
        "potion": "Зелья",
        "resource": "Ресурсы",
        "book": "Книги",
        "recipe": "Рецепты"
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
            window_width = self.scaler.scale_width(1080)
            window_height = self.scaler.scale_height(750)
        else:
            window_width = min(1080, int(screen_width * 0.85))
            window_height = min(750, int(screen_height * 0.80))

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
        scale_w = window_width / 1080
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

            # Цена (наценка 350%)
            buy_price = int(item.value * 4.5)
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
        from game.inventory import WeaponItem, ArmorItem, JewelryItem, PotionItem, ResourceItem, SkillBookItem, RecipeItem, BeltItem, BackpackItem, EquipmentSlot
        if isinstance(item, WeaponItem):
            return "weapon"
        elif isinstance(item, (ArmorItem, BeltItem, BackpackItem)):
            # Броня включает обычную броню, пояса и рюкзаки
            return "armor"
        elif hasattr(item, 'slot') and item.slot in [EquipmentSlot.BELT, EquipmentSlot.BACKPACK]:
            # Дополнительная проверка на случай, если пояса/рюкзаки имеют только слот
            return "armor"
        elif isinstance(item, JewelryItem):
            return "jewelry"
        elif isinstance(item, PotionItem):
            return "potion"
        elif isinstance(item, ResourceItem):
            return "resource"
        elif isinstance(item, SkillBookItem):
            return "book"
        elif isinstance(item, RecipeItem):
            return "recipe"
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

        # Описание книг умений
        from game.inventory import SkillBookItem
        if isinstance(item, SkillBookItem):
            lines.append(("", (0, 0, 0), False))
            if hasattr(item, 'description') and item.description:
                lines.append((item.description, (200, 200, 150), False))

        # Вес и стоимость
        lines.append(("", (0, 0, 0), False))
        lines.append((f"Вес: {item.weight:.1f} кг", (200, 200, 200), False))

        # Показываем цену покупки/продажи
        if self.mode == "buy":
            buy_price = int(item.value * 4.5)
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


