"""
Окно крафта через производственные объекты инфраструктуры.
Позволяет создавать предметы на станциях в городах с оплатой аренды.
"""
import pygame
from game.ui.windows.base import BaseWindow
from game.item_registry import get_item_name


# Маппинг ID станций из инфраструктуры на ID станций в crafting_config
INFRASTRUCTURE_TO_STATION = {
    "forge": "forge",
    "workshop": "workshop",
    "jewelry_workshop": "jewelry_workshop",
    "alchemy_lab": "alchemy_lab",
    "enchanting_workshop": "enchanting_workshop",
    "sawmill": "sawmill",
    "charcoal_burners": "charcoal_kiln",
    "tannery": "tannery",
    "smeltery": "forge",  # Плавильня использует рецепты кузницы (smelting)
}

# Базовая стоимость аренды за единицу произведённого предмета
BASE_RENTAL_COST = 5

# Коэффициенты ранга инфраструктуры
RANK_MULTIPLIERS = {
    1: 1.0,
    2: 0.9,
    3: 0.8,
    4: 0.7,
    5: 0.6,
}


class ProductionCraftingWindow(BaseWindow):
    """Окно крафта через производственный объект"""

    BASE_WIDTH = 900
    BASE_HEIGHT = 650

    # Цвета
    BUTTON_COLOR = (50, 50, 60)
    BUTTON_HOVER_COLOR = (70, 70, 85)
    BUTTON_DISABLED_COLOR = (40, 35, 35)
    BUTTON_BORDER_COLOR = (100, 100, 120)
    BUTTON_TEXT_COLOR = (220, 220, 220)
    CRAFT_BUTTON_COLOR = (50, 80, 50)
    CRAFT_BUTTON_HOVER_COLOR = (60, 100, 60)
    CRAFT_BUTTON_DISABLED_COLOR = (50, 40, 40)
    BACK_BUTTON_COLOR = (80, 50, 50)
    BACK_BUTTON_HOVER_COLOR = (100, 60, 60)
    GOLD_COLOR = (255, 215, 0)
    SUCCESS_COLOR = (100, 200, 100)
    ERROR_COLOR = (200, 100, 100)

    def __init__(self, screen, font, info_font, ui_scaler, crafting_system):
        """
        Инициализация окна производственного крафта.

        Args:
            screen: Pygame экран
            font: Основной шрифт
            info_font: Информационный шрифт
            ui_scaler: Объект для масштабирования UI
            crafting_system: Система крафта
        """
        super().__init__(screen, font, info_font, ui_scaler)
        self.crafting_system = crafting_system

        # Текущая станция и локация
        self.station_id = None
        self.station_name = None
        self.station_rank = 1
        self.location = None

        # Списки рецептов
        self.recipes = []
        self.filtered_recipes = []

        # Состояние UI
        self.selected_recipe_index = 0
        self.scroll_offset = 0
        self.current_category = "all"

        # Области для кликов
        self.recipe_rects = []
        self.category_rects = []
        self.craft_button_rect = None
        self.back_button_rect = None

        # Сообщение о результате
        self.result_message = None
        self.result_message_timer = 0
        self.result_is_success = True

    def set_station(self, infrastructure_id, station_name, rank, location):
        """
        Установить станцию для крафта.

        Args:
            infrastructure_id: ID инфраструктуры (forge, workshop и т.д.)
            station_name: Отображаемое имя станции
            rank: Ранг станции
            location: Локация (город/деревня)
        """
        self.station_id = INFRASTRUCTURE_TO_STATION.get(infrastructure_id, infrastructure_id)
        self.station_name = station_name
        self.station_rank = rank
        self.location = location

        # Загружаем рецепты для станции
        self._load_recipes()

        # Сбрасываем состояние
        self.selected_recipe_index = 0
        self.scroll_offset = 0
        self.current_category = "all"
        self.result_message = None

    def _load_recipes(self):
        """Загрузить рецепты для текущей станции."""
        self.recipes = []

        station = self.crafting_system.get_station(self.station_id)
        if station:
            # Получаем все рецепты станции без ограничений
            self.recipes = list(station.recipes)

        self._apply_category_filter()

    def _apply_category_filter(self):
        """Применить фильтр по категории."""
        if self.current_category == "all":
            self.filtered_recipes = list(self.recipes)
        else:
            self.filtered_recipes = [r for r in self.recipes if r.category == self.current_category]

        # Сортировка по имени
        self.filtered_recipes.sort(key=lambda r: r.name)

        # Корректируем выбранный индекс
        if self.selected_recipe_index >= len(self.filtered_recipes):
            self.selected_recipe_index = max(0, len(self.filtered_recipes) - 1)

    def get_rental_cost(self, recipe):
        """
        Рассчитать стоимость аренды для рецепта.

        Args:
            recipe: Рецепт крафта

        Returns:
            int: Стоимость аренды
        """
        # Базовая стоимость зависит от цены рецепта
        base_cost = max(BASE_RENTAL_COST, recipe.base_price // 10)

        # Применяем коэффициент ранга (чем выше ранг, тем дешевле)
        rank_mult = RANK_MULTIPLIERS.get(self.station_rank, 1.0)

        return max(1, int(base_cost * rank_mult))

    def can_afford_rental(self, recipe, player):
        """
        Проверить, может ли игрок оплатить аренду.

        Args:
            recipe: Рецепт крафта
            player: Игрок

        Returns:
            bool: True если может оплатить
        """
        rental_cost = self.get_rental_cost(recipe)
        return player.inventory.gold >= rental_cost

    def can_craft_recipe(self, recipe, player):
        """
        Проверить возможность крафта рецепта (без ограничений по навыкам).

        Args:
            recipe: Рецепт крафта
            player: Игрок

        Returns:
            tuple: (можно ли крафтить, причина отказа)
        """
        # Проверяем наличие ресурсов
        for ingredient in recipe.ingredients:
            item_id = ingredient['item']
            required_quantity = ingredient['quantity']
            item_name = get_item_name(item_id) or item_id
            has_quantity = player.inventory.get_resource_count(item_name)

            if has_quantity < required_quantity:
                return False, f"Недостаточно: {item_name} ({has_quantity}/{required_quantity})"

        # Проверяем деньги на аренду
        rental_cost = self.get_rental_cost(recipe)
        if player.inventory.gold < rental_cost:
            return False, f"Недостаточно золота на аренду ({rental_cost})"

        return True, None

    def craft_item(self, recipe, player):
        """
        Выполнить крафт предмета.

        Args:
            recipe: Рецепт крафта
            player: Игрок

        Returns:
            tuple: (успех, сообщение)
        """
        can_craft, error = self.can_craft_recipe(recipe, player)
        if not can_craft:
            return False, error

        # Списываем аренду
        rental_cost = self.get_rental_cost(recipe)
        player.inventory.remove_gold(rental_cost)

        # Выполняем крафт через систему крафта (без проверки навыков)
        # Удаляем ресурсы
        for ingredient in recipe.ingredients:
            item_id = ingredient['item']
            quantity = ingredient['quantity']
            item_name = get_item_name(item_id) or item_id
            player.inventory.remove_resource(item_name, quantity)

        # Добавляем результат
        from game.item_registry import get_item
        result_item = get_item(recipe.result_item)

        if result_item:
            player.inventory.add_item(result_item, recipe.result_quantity)
            qty_text = f" x{recipe.result_quantity}" if recipe.result_quantity > 1 else ""
            return True, f"Создано: {recipe.name}{qty_text} (аренда: {rental_cost} зол.)"
        else:
            # Возвращаем ресурсы и деньги
            player.inventory.add_gold(rental_cost)
            for ingredient in recipe.ingredients:
                item_id = ingredient['item']
                quantity = ingredient['quantity']
                item_name = get_item_name(item_id) or item_id
                player.inventory.add_resource(item_name, quantity)
            return False, f"Ошибка: предмет '{recipe.result_item}' не найден"

    def render(self, player):
        """
        Отрисовка окна.

        Args:
            player: Игрок
        """
        # Обновляем таймер сообщения
        if self.result_message and self.result_message_timer > 0:
            self.result_message_timer -= 1
            if self.result_message_timer <= 0:
                self.result_message = None

        # Очищаем области кликов
        self.recipe_rects = []
        self.category_rects = []

        win = self.begin_render(
            self.BASE_WIDTH, self.BASE_HEIGHT,
            title=f"{self.station_name} (ур. {self.station_rank})"
        )

        window_x = win['x']
        window_y = win['y']
        window_width = win['width']
        window_height = win['height']
        scale_w = win['scale_w']
        scale_h = win['scale_h']
        content_y = win['content_y']

        # Информация о золоте игрока
        gold_text = self.info_font.render(f"Золото: {player.inventory.gold}", True, self.GOLD_COLOR)
        gold_rect = gold_text.get_rect()
        gold_rect.right = window_x + window_width - int(20 * scale_w)
        gold_rect.y = window_y + int(15 * scale_h)
        self.screen.blit(gold_text, gold_rect)

        # Разделительная линия
        line_y = content_y + int(10 * scale_h)
        pygame.draw.line(
            self.screen, self.FRAME_COLOR,
            (window_x + int(20 * scale_w), line_y),
            (window_x + window_width - int(20 * scale_w), line_y),
            2
        )

        # Категории (вкладки)
        self._render_categories(window_x, line_y + int(10 * scale_h), window_width, scale_w, scale_h)

        # Список рецептов (левая часть)
        recipes_y = line_y + int(50 * scale_h)
        recipes_width = int(350 * scale_w)
        self._render_recipes(
            player, window_x + int(20 * scale_w), recipes_y,
            recipes_width, window_height - (recipes_y - window_y) - int(70 * scale_h),
            scale_w, scale_h
        )

        # Детали выбранного рецепта (правая часть)
        details_x = window_x + int(390 * scale_w)
        details_width = window_width - int(410 * scale_w)
        self._render_recipe_details(
            player, details_x, recipes_y,
            details_width, window_height - (recipes_y - window_y) - int(70 * scale_h),
            scale_w, scale_h
        )

        # Нижняя панель с кнопками
        self._render_bottom_panel(
            player, window_x, window_y, window_width, window_height, scale_w, scale_h
        )

        # Сообщение о результате
        if self.result_message:
            self._render_result_message(window_x, window_y, window_width, window_height, scale_w, scale_h)

    def _render_categories(self, window_x, y, window_width, scale_w, scale_h):
        """Отрисовка вкладок категорий."""
        categories = [
            ("all", "Все"),
            ("smelting", "Переплавка"),
            ("tool", "Заготовки"),
            ("weapon", "Оружие"),
            ("armor", "Броня"),
            ("jewelry", "Украшения"),
            ("alchemy", "Алхимия"),
        ]

        # Фильтруем категории, которые есть в рецептах станции
        available_categories = {"all"}
        for recipe in self.recipes:
            available_categories.add(recipe.category)

        categories = [(cat_id, cat_name) for cat_id, cat_name in categories
                      if cat_id in available_categories]

        tab_width = int(100 * scale_w)
        tab_height = int(28 * scale_h)
        tab_spacing = int(5 * scale_w)
        start_x = window_x + int(20 * scale_w)

        for i, (category_id, category_name) in enumerate(categories):
            tab_x = start_x + i * (tab_width + tab_spacing)

            is_selected = category_id == self.current_category
            bg_color = self.BUTTON_HOVER_COLOR if is_selected else self.BUTTON_COLOR

            tab_rect = pygame.Rect(tab_x, y, tab_width, tab_height)
            pygame.draw.rect(self.screen, bg_color, tab_rect, border_radius=3)
            pygame.draw.rect(self.screen, self.BUTTON_BORDER_COLOR, tab_rect, 1, border_radius=3)

            text = self.info_font.render(category_name, True, self.BUTTON_TEXT_COLOR)
            text_rect = text.get_rect(center=tab_rect.center)
            self.screen.blit(text, text_rect)

            self.category_rects.append((tab_rect, category_id))

    def _render_recipes(self, player, x, y, width, height, scale_w, scale_h):
        """Отрисовка списка рецептов."""
        if not self.filtered_recipes:
            text = self.info_font.render("Нет рецептов", True, (150, 150, 150))
            self.screen.blit(text, (x + int(10 * scale_w), y + int(10 * scale_h)))
            return

        recipe_height = int(30 * scale_h)
        recipe_spacing = int(5 * scale_h)
        visible_count = int(height // (recipe_height + recipe_spacing))

        for i in range(visible_count):
            recipe_idx = i + self.scroll_offset
            if recipe_idx >= len(self.filtered_recipes):
                break

            recipe = self.filtered_recipes[recipe_idx]
            can_craft, _ = self.can_craft_recipe(recipe, player)
            is_selected = recipe_idx == self.selected_recipe_index

            rect_y = y + i * (recipe_height + recipe_spacing)
            rect = pygame.Rect(x, rect_y, width, recipe_height)

            # Цвет фона
            if is_selected:
                bg_color = self.BUTTON_HOVER_COLOR if can_craft else (80, 50, 50)
            else:
                bg_color = self.BUTTON_COLOR if can_craft else self.BUTTON_DISABLED_COLOR

            pygame.draw.rect(self.screen, bg_color, rect, border_radius=3)
            pygame.draw.rect(self.screen, self.BUTTON_BORDER_COLOR, rect, 1, border_radius=3)

            # Название рецепта
            text_color = self.BUTTON_TEXT_COLOR if can_craft else (120, 100, 100)
            text = self.info_font.render(recipe.name, True, text_color)

            # Обрезаем если слишком длинное
            max_text_width = width - int(60 * scale_w)
            if text.get_width() > max_text_width:
                name = recipe.name
                while len(name) > 0 and self.info_font.render(name + "...", True, text_color).get_width() > max_text_width:
                    name = name[:-1]
                text = self.info_font.render(name + "...", True, text_color)

            self.screen.blit(text, (rect.x + int(8 * scale_w), rect.centery - text.get_height() // 2))

            # Стоимость аренды справа
            rental = self.get_rental_cost(recipe)
            rental_text = self.info_font.render(f"{rental}з", True, self.GOLD_COLOR)
            self.screen.blit(rental_text, (rect.right - rental_text.get_width() - int(8 * scale_w),
                                           rect.centery - rental_text.get_height() // 2))

            self.recipe_rects.append((rect, recipe_idx))

    def _render_recipe_details(self, player, x, y, width, height, scale_w, scale_h):
        """Отрисовка деталей выбранного рецепта."""
        if not self.filtered_recipes or self.selected_recipe_index >= len(self.filtered_recipes):
            return

        recipe = self.filtered_recipes[self.selected_recipe_index]

        # Фон панели деталей
        details_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (40, 40, 50), details_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.BUTTON_BORDER_COLOR, details_rect, 1, border_radius=5)

        padding = int(15 * scale_w)
        line_height = int(24 * scale_h)
        current_y = y + padding

        # Название рецепта
        name_text = self.font.render(recipe.name, True, self.GOLD_COLOR)
        self.screen.blit(name_text, (x + padding, current_y))
        current_y += line_height + int(10 * scale_h)

        # Результат
        result_qty = f" x{recipe.result_quantity}" if recipe.result_quantity > 1 else ""
        result_text = self.info_font.render(f"Результат: {recipe.name}{result_qty}", True, self.SUCCESS_COLOR)
        self.screen.blit(result_text, (x + padding, current_y))
        current_y += line_height + int(10 * scale_h)

        # Разделитель
        pygame.draw.line(self.screen, self.FRAME_COLOR,
                         (x + padding, current_y), (x + width - padding, current_y), 1)
        current_y += int(10 * scale_h)

        # Заголовок ингредиентов
        ing_title = self.info_font.render("Ингредиенты:", True, (180, 180, 200))
        self.screen.blit(ing_title, (x + padding, current_y))
        current_y += line_height

        # Список ингредиентов
        for ingredient in recipe.ingredients:
            item_id = ingredient['item']
            required = ingredient['quantity']
            item_name = get_item_name(item_id) or item_id
            has = player.inventory.get_resource_count(item_name)

            has_enough = has >= required
            color = self.SUCCESS_COLOR if has_enough else self.ERROR_COLOR

            ing_text = self.info_font.render(f"  • {item_name}: {has}/{required}", True, color)
            self.screen.blit(ing_text, (x + padding, current_y))
            current_y += line_height

        current_y += int(10 * scale_h)

        # Разделитель
        pygame.draw.line(self.screen, self.FRAME_COLOR,
                         (x + padding, current_y), (x + width - padding, current_y), 1)
        current_y += int(10 * scale_h)

        # Стоимость аренды
        rental_cost = self.get_rental_cost(recipe)
        can_afford = player.inventory.gold >= rental_cost
        rental_color = self.GOLD_COLOR if can_afford else self.ERROR_COLOR

        rental_text = self.info_font.render(f"Стоимость аренды: {rental_cost} золота", True, rental_color)
        self.screen.blit(rental_text, (x + padding, current_y))
        current_y += line_height

        # Информация о ранге
        rank_info = f"Ранг станции: {self.station_rank} (скидка: {int((1 - RANK_MULTIPLIERS.get(self.station_rank, 1.0)) * 100)}%)"
        rank_text = self.info_font.render(rank_info, True, (150, 150, 170))
        self.screen.blit(rank_text, (x + padding, current_y))

    def _render_bottom_panel(self, player, window_x, window_y, window_width, window_height, scale_w, scale_h):
        """Отрисовка нижней панели с кнопками."""
        panel_y = window_y + window_height - int(55 * scale_h)

        # Кнопка "Создать"
        craft_btn_width = int(150 * scale_w)
        craft_btn_height = int(40 * scale_h)
        craft_btn_x = window_x + window_width // 2 - craft_btn_width - int(10 * scale_w)

        can_craft = False
        if self.filtered_recipes and self.selected_recipe_index < len(self.filtered_recipes):
            recipe = self.filtered_recipes[self.selected_recipe_index]
            can_craft, _ = self.can_craft_recipe(recipe, player)

        mouse_pos = pygame.mouse.get_pos()
        craft_rect = pygame.Rect(craft_btn_x, panel_y, craft_btn_width, craft_btn_height)
        craft_hovered = craft_rect.collidepoint(mouse_pos)

        if can_craft:
            craft_bg = self.CRAFT_BUTTON_HOVER_COLOR if craft_hovered else self.CRAFT_BUTTON_COLOR
        else:
            craft_bg = self.CRAFT_BUTTON_DISABLED_COLOR

        pygame.draw.rect(self.screen, craft_bg, craft_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.BUTTON_BORDER_COLOR, craft_rect, 2, border_radius=5)

        craft_text = self.font.render("Создать", True, self.BUTTON_TEXT_COLOR)
        craft_text_rect = craft_text.get_rect(center=craft_rect.center)
        self.screen.blit(craft_text, craft_text_rect)

        self.craft_button_rect = craft_rect

        # Кнопка "Назад"
        back_btn_width = int(120 * scale_w)
        back_btn_height = int(40 * scale_h)
        back_btn_x = window_x + window_width // 2 + int(10 * scale_w)

        back_rect = pygame.Rect(back_btn_x, panel_y, back_btn_width, back_btn_height)
        back_hovered = back_rect.collidepoint(mouse_pos)

        back_bg = self.BACK_BUTTON_HOVER_COLOR if back_hovered else self.BACK_BUTTON_COLOR
        pygame.draw.rect(self.screen, back_bg, back_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.BUTTON_BORDER_COLOR, back_rect, 2, border_radius=5)

        back_text = self.font.render("Назад", True, self.BUTTON_TEXT_COLOR)
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.screen.blit(back_text, back_text_rect)

        self.back_button_rect = back_rect

    def _render_result_message(self, window_x, window_y, window_width, window_height, scale_w, scale_h):
        """Отрисовка сообщения о результате крафта."""
        msg_rect = pygame.Rect(
            window_x + int(100 * scale_w),
            window_y + window_height // 2 - int(30 * scale_h),
            window_width - int(200 * scale_w),
            int(60 * scale_h)
        )

        bg_color = (30, 60, 30) if self.result_is_success else (60, 30, 30)
        pygame.draw.rect(self.screen, bg_color, msg_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.FRAME_COLOR, msg_rect, 2, border_radius=8)

        text_color = self.SUCCESS_COLOR if self.result_is_success else self.ERROR_COLOR
        text = self.font.render(self.result_message, True, text_color)
        text_rect = text.get_rect(center=msg_rect.center)
        self.screen.blit(text, text_rect)

    def handle_click(self, mouse_pos, player):
        """
        Обработка клика мыши.

        Args:
            mouse_pos: Позиция мыши (x, y)
            player: Игрок

        Returns:
            str or None: "back" для возврата, None для продолжения
        """
        x, y = mouse_pos

        # Клик по кнопке "Назад"
        if self.back_button_rect and self.back_button_rect.collidepoint(x, y):
            return "back"

        # Клик по кнопке "Создать"
        if self.craft_button_rect and self.craft_button_rect.collidepoint(x, y):
            if self.filtered_recipes and self.selected_recipe_index < len(self.filtered_recipes):
                recipe = self.filtered_recipes[self.selected_recipe_index]
                success, message = self.craft_item(recipe, player)
                self.result_message = message
                self.result_is_success = success
                self.result_message_timer = 90  # ~1.5 секунды при 60 FPS

        # Клик по категориям
        for rect, category_id in self.category_rects:
            if rect.collidepoint(x, y):
                self.current_category = category_id
                self._apply_category_filter()
                return None

        # Клик по рецептам
        for rect, recipe_idx in self.recipe_rects:
            if rect.collidepoint(x, y):
                if recipe_idx == self.selected_recipe_index:
                    # Двойной клик - крафтим
                    recipe = self.filtered_recipes[recipe_idx]
                    success, message = self.craft_item(recipe, player)
                    self.result_message = message
                    self.result_is_success = success
                    self.result_message_timer = 90
                else:
                    self.selected_recipe_index = recipe_idx
                return None

        return None

    def handle_key(self, key, player):
        """
        Обработка нажатия клавиши.

        Args:
            key: Код клавиши
            player: Игрок

        Returns:
            str or None: "back" для возврата, None для продолжения
        """
        if key == pygame.K_ESCAPE:
            return "back"

        if key == pygame.K_UP:
            if self.selected_recipe_index > 0:
                self.selected_recipe_index -= 1
                # Прокрутка вверх если нужно
                if self.selected_recipe_index < self.scroll_offset:
                    self.scroll_offset = self.selected_recipe_index

        elif key == pygame.K_DOWN:
            if self.selected_recipe_index < len(self.filtered_recipes) - 1:
                self.selected_recipe_index += 1
                # Прокрутка вниз если нужно
                # (примерно 15 видимых рецептов)
                if self.selected_recipe_index >= self.scroll_offset + 15:
                    self.scroll_offset = self.selected_recipe_index - 14

        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if self.filtered_recipes and self.selected_recipe_index < len(self.filtered_recipes):
                recipe = self.filtered_recipes[self.selected_recipe_index]
                success, message = self.craft_item(recipe, player)
                self.result_message = message
                self.result_is_success = success
                self.result_message_timer = 90

        return None

    def handle_scroll(self, scroll_up):
        """
        Обработка прокрутки колёсиком мыши.

        Args:
            scroll_up: True если прокрутка вверх
        """
        if scroll_up:
            if self.scroll_offset > 0:
                self.scroll_offset -= 1
        else:
            max_offset = max(0, len(self.filtered_recipes) - 15)
            if self.scroll_offset < max_offset:
                self.scroll_offset += 1
