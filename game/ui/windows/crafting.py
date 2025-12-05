"""
Окно крафта предметов.
"""
import pygame
from game.ui.base import UIHelper
from game.crafting_system import ITEM_ID_TO_NAME


class CraftingWindow:
    """Окно крафта предметов"""

    def __init__(self, screen, font, info_font, scaler=None):
        """
        Инициализация окна крафта.

        Args:
            screen: Экран Pygame
            font: Основной шрифт
            info_font: Шрифт для информации
            scaler: Объект масштабирования (опционально)
        """
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.scaler = scaler

        # Текущая выбранная станция
        self.selected_station_index = 0
        # Текущий выбранный рецепт
        self.selected_recipe_index = 0

        # Хранение координат элементов для обработки мыши
        self.station_rects = []  # Список прямоугольников станций
        self.recipe_rects = []  # Список прямоугольников рецептов
        self.craft_button_rect = None  # Прямоугольник кнопки крафта

        # Фильтр по категориям
        self.current_category = "all"
        self.current_recipe_categories = ["all"]  # Список категорий рецептов для текущей вкладки
        self.category_rects = []

    def render(self, crafting_system, player, mouse_pos=None):
        """
        Отрисовка окна крафта.

        Args:
            crafting_system: Система крафта
            player: Объект игрока
            mouse_pos: Позиция мыши для tooltip
        """
        # Очищаем списки rect'ов
        self.station_rects = []
        self.recipe_rects = []
        self.category_rects = []

        # Получаем размеры экрана
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (увеличены для 4 столбцов и 8 строк рецептов)
        if self.scaler:
            window_width = self.scaler.scale_width(1600)
            window_height = self.scaler.scale_height(980)
        else:
            window_width = min(1600, int(screen_width * 0.95))
            window_height = min(980, int(screen_height * 0.95))

        window_x = (screen_width - window_width) // 2
        # Поднимаем окно выше для лучшего отображения всех рецептов
        window_y = max(10, (screen_height - window_height) // 2 - 30)

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

        # Коэффициенты масштабирования
        scale_w = window_width / 1000
        scale_h = window_height / 700

        # Заголовок
        title_text = self.font.render("КРАФТ", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + int(10 * scale_h)
        self.screen.blit(title_text, title_rect)

        # Разделитель
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (window_x + int(10 * scale_w), window_y + int(40 * scale_h)),
            (window_x + window_width - int(10 * scale_w), window_y + int(40 * scale_h)),
            2
        )

        # Получаем список станций
        stations = crafting_system.get_all_stations()

        if not stations:
            # Если нет станций
            no_stations_text = self.font.render(
                "Нет доступных станций крафта",
                True,
                (200, 200, 200)
            )
            text_rect = no_stations_text.get_rect()
            text_rect.center = (window_x + window_width // 2, window_y + window_height // 2)
            self.screen.blit(no_stations_text, text_rect)
        else:
            # Отрисовка станций (левая панель)
            self._render_stations(
                stations, player, window_x, window_y, window_width, window_height,
                scale_w, scale_h
            )

            # Получаем текущую станцию
            if 0 <= self.selected_station_index < len(stations):
                current_station = stations[self.selected_station_index]

                # Отрисовка вкладок категорий (вверху справа)
                self._render_categories(
                    crafting_system, window_x, window_y, window_width, window_height,
                    scale_w, scale_h
                )

                # Отрисовка рецептов (правая панель)
                self._render_recipes(
                    crafting_system, current_station, player,
                    window_x, window_y, window_width, window_height,
                    scale_w, scale_h, mouse_pos
                )

        # Подсказки внизу
        help_y = window_y + window_height - int(35 * scale_h)
        help_text = self.info_font.render(
            "[ЛКМ] Выбор  [ПКМ/ENTER] Создать  [ESC] Закрыть  [←/→] Сменить станцию",
            True,
            (180, 180, 180)
        )
        help_rect = help_text.get_rect()
        help_rect.centerx = window_x + window_width // 2
        help_rect.y = help_y
        self.screen.blit(help_text, help_rect)

    def _render_stations(self, stations, player, window_x, window_y, window_width, window_height, scale_w, scale_h):
        """Отрисовка списка станций."""
        stations_x = window_x + int(20 * scale_w)
        stations_y = window_y + int(170 * scale_h)  # Смещено вниз на 100 пикселей
        station_width = int(180 * scale_w)  # Уменьшено с 250 до 180
        station_height = int(40 * scale_h)  # Уменьшено с 60 до 40
        station_spacing = int(10 * scale_h)

        # Заголовок
        stations_title = self.info_font.render(
            "Станции крафта:",
            True,
            (200, 200, 200)
        )
        self.screen.blit(stations_title, (stations_x, stations_y - int(25 * scale_h)))

        # Маппинг станций на требуемые умения
        station_skill_requirements = {
            'workbench': 'craftsmanship',
            'forge': 'craftsmanship',
            'alchemy_table': 'alchemy',
            'enchanting_table': 'enchanting'
        }

        for i, station in enumerate(stations):
            rect_y = stations_y + i * (station_height + station_spacing)

            # Проверяем, не выходит ли за границы
            if rect_y + station_height > window_y + window_height - int(50 * scale_h):
                break

            # Проверяем, доступна ли станция для игрока
            is_locked = False
            required_skill_name = None
            if station.id in station_skill_requirements:
                required_skill_id = station_skill_requirements[station.id]
                if hasattr(player, 'skill_manager'):
                    skill = player.skill_manager.get_skill(required_skill_id)
                    if not skill:
                        is_locked = True
                        # Названия умений для отображения
                        skill_names = {
                            'craftsmanship': 'Изготовление',
                            'alchemy': 'Алхимия',
                            'enchanting': 'Зачарование'
                        }
                        required_skill_name = skill_names.get(required_skill_id, required_skill_id)

            # Цвет в зависимости от выбора и доступности
            if is_locked:
                bg_color = (40, 30, 30)
                border_color = (100, 60, 60)
            elif i == self.selected_station_index:
                bg_color = (80, 80, 120)
                border_color = (150, 150, 200)
            else:
                bg_color = (50, 50, 60)
                border_color = (80, 80, 100)

            # Фон станции
            station_rect = pygame.Rect(stations_x, rect_y, station_width, station_height)
            pygame.draw.rect(self.screen, bg_color, station_rect)
            pygame.draw.rect(self.screen, border_color, station_rect, 2)

            # Сохраняем rect для обработки мыши (вместе с флагом блокировки)
            self.station_rects.append(station_rect)

            # Название станции (центрированное по вертикали и горизонтали)
            name_color = (150, 100, 100) if is_locked else (255, 255, 255)
            name_text = self.info_font.render(station.name, True, name_color)
            name_rect = name_text.get_rect()
            name_rect.center = station_rect.center
            self.screen.blit(name_text, name_rect)

    def _render_categories(self, crafting_system, window_x, window_y, window_width, window_height, scale_w, scale_h):
        """Отрисовка вкладок категорий."""
        # Определяем категории (вкладка_id, отображаемое_имя, список_категорий_рецептов)
        categories = [
            ("all", "Все", ["all"]),
            ("materials", "Материалы", ["materials", "smelting", "tool"]),
            ("armor", "Броня", ["armor"]),
            ("weapon", "Оружие", ["weapon"]),
            ("jewelry", "Украшения", ["jewelry"]),
            ("artifacts", "Артефакты", ["artifacts"])
        ]

        # Начальная позиция для вкладок (справа от области станций)
        tabs_start_x = window_x + int(220 * scale_w)  # Уменьшено с 300 из-за уменьшения ширины кнопок станций
        tabs_y = window_y + int(60 * scale_h)
        tab_height = int(35 * scale_h)
        tab_spacing = int(5 * scale_w)

        # Вычисляем ширину вкладки
        available_width = window_width - int(320 * scale_w)
        tab_width = (available_width - (len(categories) - 1) * tab_spacing) // len(categories)

        # Отрисовываем вкладки
        for i, (category_id, category_name, recipe_categories) in enumerate(categories):
            tab_x = tabs_start_x + i * (tab_width + tab_spacing)

            # Определяем цвета в зависимости от выбранной категории
            if category_id == self.current_category:
                bg_color = (70, 70, 100)
                border_color = (120, 120, 180)
                text_color = (255, 255, 255)
            else:
                bg_color = (45, 45, 55)
                border_color = (70, 70, 90)
                text_color = (180, 180, 180)

            # Рисуем вкладку
            tab_rect = pygame.Rect(tab_x, tabs_y, tab_width, tab_height)
            pygame.draw.rect(self.screen, bg_color, tab_rect)
            pygame.draw.rect(self.screen, border_color, tab_rect, 2)

            # Сохраняем rect для обработки кликов (включая список категорий рецептов)
            self.category_rects.append((tab_rect, category_id, recipe_categories))

            # Текст категории
            category_text = self.info_font.render(category_name, True, text_color)
            text_rect = category_text.get_rect()
            text_rect.center = tab_rect.center
            self.screen.blit(category_text, text_rect)

    def _render_recipes(self, crafting_system, station, player, window_x, window_y,
                       window_width, window_height, scale_w, scale_h, mouse_pos):
        """Отрисовка списка рецептов в 4 столбца по 8 ячеек."""
        recipes_area_x = window_x + int(220 * scale_w)  # Уменьшено с 300 из-за уменьшения ширины кнопок станций
        recipes_area_y = window_y + int(110 * scale_h)  # Увеличено для вкладок категорий
        recipes_area_width = window_width - int(240 * scale_w)  # Уменьшено с 320

        # Получаем доступные рецепты
        all_recipes = station.get_available_recipes(player)

        # Фильтруем по категориям
        if "all" not in self.current_recipe_categories:
            recipes = [r for r in all_recipes if r.category in self.current_recipe_categories]
        else:
            recipes = all_recipes

        # Сортировка по качеству (required_skill_rank) по возрастанию
        recipes = sorted(recipes, key=lambda r: getattr(r, 'required_skill_rank', 1))

        if not recipes:
            # Если нет рецептов
            no_recipes_text = self.font.render(
                "Нет доступных рецептов" if not all_recipes else "Нет рецептов в этой категории",
                True,
                (150, 150, 150)
            )
            self.screen.blit(no_recipes_text, (recipes_area_x + int(200 * scale_w), recipes_area_y + int(100 * scale_h)))
            return

        # Корректируем выбранный индекс
        if self.selected_recipe_index >= len(recipes):
            self.selected_recipe_index = max(0, len(recipes) - 1)

        # Параметры сетки: 4 столбца по 16 рядов
        columns = 4
        rows_per_column = 16
        recipe_width = int((recipes_area_width - int(30 * scale_w)) / columns)
        recipe_height = int(30 * scale_h)  # Уменьшено для компактности (только название)
        recipe_spacing_x = int(10 * scale_w)
        recipe_spacing_y = int(5 * scale_h)

        # Отрисовка рецептов
        for i, recipe in enumerate(recipes):
            # Вычисляем позицию в сетке
            column = i // rows_per_column
            row = i % rows_per_column

            if column >= columns:
                break  # Максимум 40 рецептов (2x20)

            # Позиция рецепта
            rect_x = recipes_area_x + column * (recipe_width + recipe_spacing_x)
            rect_y = recipes_area_y + row * (recipe_height + recipe_spacing_y)

            # Проверяем возможность создания
            can_craft, error_msg = recipe.can_craft(player, player.inventory)

            # Цвет в зависимости от выбора и возможности создания
            if i == self.selected_recipe_index:
                bg_color = (80, 80, 120) if can_craft else (120, 60, 60)
                border_color = (150, 150, 200) if can_craft else (200, 100, 100)
            else:
                bg_color = (50, 50, 60) if can_craft else (70, 40, 40)
                border_color = (80, 80, 100) if can_craft else (100, 60, 60)

            # Фон рецепта
            recipe_rect = pygame.Rect(rect_x, rect_y, recipe_width, recipe_height)
            pygame.draw.rect(self.screen, bg_color, recipe_rect)
            pygame.draw.rect(self.screen, border_color, recipe_rect, 2)

            # Сохраняем rect для обработки мыши (важно для правильного индекса!)
            self.recipe_rects.append((recipe_rect, i, recipe))

            # Название рецепта (только название, центрированное по вертикали)
            name_color = (255, 255, 255) if can_craft else (200, 150, 150)
            name_text = self.info_font.render(recipe.name, True, name_color)

            # Обрезаем название если слишком длинное
            max_width = recipe_width - int(10 * scale_w)
            if name_text.get_width() > max_width:
                # Подбираем длину названия, чтобы оно поместилось
                short_name = recipe.name
                while len(short_name) > 0 and self.info_font.render(short_name + "...", True, name_color).get_width() > max_width:
                    short_name = short_name[:-1]
                name_text = self.info_font.render(short_name + "...", True, name_color)

            # Центрируем по вертикали
            name_rect = name_text.get_rect()
            name_rect.left = rect_x + int(5 * scale_w)
            name_rect.centery = recipe_rect.centery
            self.screen.blit(name_text, name_rect)

        # Проверяем наведение мыши и отрисовываем tooltip
        if mouse_pos:
            for rect, recipe_index, recipe in self.recipe_rects:
                if rect.collidepoint(mouse_pos):
                    self._render_recipe_tooltip(recipe, player, crafting_system, mouse_pos, rect, scale_w, scale_h)
                    break

    def _render_recipe_tooltip(self, recipe, player, crafting_system, mouse_pos, recipe_rect, scale_w, scale_h):
        """Отрисовка всплывающего окна с информацией о рецепте."""
        # Размеры tooltip
        tooltip_width = int(350 * scale_w)
        tooltip_padding = int(10 * scale_w)
        line_height = int(20 * scale_h)

        # Подготовка информации
        lines = []

        # Название (жирным)
        lines.append(("title", recipe.name))

        # Категория и ранг
        category_name = crafting_system.get_category_name(recipe.category)
        skill_rank = getattr(recipe, 'required_skill_rank', 1)
        lines.append(("info", f"Категория: {category_name}"))
        lines.append(("info", f"Требуемый ранг: {skill_rank}"))

        # Разделитель
        lines.append(("separator", None))

        # Ингредиенты
        lines.append(("header", "Ингредиенты:"))
        for ingredient in recipe.ingredients:
            item_id = ingredient['item']
            required = ingredient['quantity']
            item_name = ITEM_ID_TO_NAME.get(item_id, item_id)
            has = player.inventory.get_resource_count(item_name)

            has_enough = has >= required
            lines.append(("ingredient", f"  {item_name}: {has}/{required}", has_enough))

        # Результат
        lines.append(("separator", None))
        result_text = f"Результат: {recipe.name}"
        if recipe.result_quantity > 1:
            result_text += f" x{recipe.result_quantity}"
        lines.append(("result", result_text))

        # Проверка возможности создания
        can_craft, error_msg = recipe.can_craft(player, player.inventory)
        if not can_craft:
            lines.append(("separator", None))
            lines.append(("error", f"Невозможно: {error_msg}"))

        # Вычисляем высоту tooltip
        tooltip_height = len([l for l in lines if l[0] != "separator"]) * line_height + tooltip_padding * 2

        # Определяем позицию tooltip (справа или слева от рецепта)
        screen_width = self.screen.get_width()

        # Пытаемся разместить справа
        tooltip_x = recipe_rect.right + int(10 * scale_w)
        if tooltip_x + tooltip_width > screen_width - int(20 * scale_w):
            # Размещаем слева
            tooltip_x = recipe_rect.left - tooltip_width - int(10 * scale_w)

        tooltip_y = recipe_rect.top

        # Убеждаемся, что tooltip не выходит за границы экрана
        if tooltip_y + tooltip_height > self.screen.get_height():
            tooltip_y = self.screen.get_height() - tooltip_height - int(10 * scale_h)
        if tooltip_y < int(10 * scale_h):
            tooltip_y = int(10 * scale_h)

        # Фон tooltip
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(self.screen, (25, 25, 35), tooltip_rect)
        pygame.draw.rect(self.screen, (150, 150, 180), tooltip_rect, 2)

        # Отрисовка содержимого
        current_y = tooltip_y + tooltip_padding
        for line_type, *line_data in lines:
            if line_type == "separator":
                # Горизонтальная линия
                pygame.draw.line(
                    self.screen,
                    (100, 100, 120),
                    (tooltip_x + tooltip_padding, current_y + line_height // 2),
                    (tooltip_x + tooltip_width - tooltip_padding, current_y + line_height // 2),
                    1
                )
                current_y += line_height // 2
            elif line_type == "title":
                text = self.font.render(line_data[0], True, (255, 215, 0))
                self.screen.blit(text, (tooltip_x + tooltip_padding, current_y))
                current_y += line_height
            elif line_type == "info":
                text = self.info_font.render(line_data[0], True, (200, 200, 200))
                self.screen.blit(text, (tooltip_x + tooltip_padding, current_y))
                current_y += line_height
            elif line_type == "header":
                text = self.info_font.render(line_data[0], True, (180, 180, 220))
                self.screen.blit(text, (tooltip_x + tooltip_padding, current_y))
                current_y += line_height
            elif line_type == "ingredient":
                has_enough = line_data[1]
                color = (100, 200, 100) if has_enough else (200, 100, 100)
                text = self.info_font.render(line_data[0], True, color)
                self.screen.blit(text, (tooltip_x + tooltip_padding, current_y))
                current_y += line_height
            elif line_type == "result":
                text = self.info_font.render(line_data[0], True, (150, 255, 150))
                self.screen.blit(text, (tooltip_x + tooltip_padding, current_y))
                current_y += line_height
            elif line_type == "error":
                text = self.info_font.render(line_data[0], True, (255, 100, 100))
                self.screen.blit(text, (tooltip_x + tooltip_padding, current_y))
                current_y += line_height

    def _is_station_locked(self, station, player):
        """
        Проверка, заблокирована ли станция для игрока.

        Args:
            station: Станция крафта
            player: Объект игрока

        Returns:
            bool: True если станция заблокирована
        """
        station_skill_requirements = {
            'workbench': 'craftsmanship',
            'forge': 'craftsmanship',
            'alchemy_table': 'alchemy',
            'enchanting_table': 'enchanting'
        }

        if station.id in station_skill_requirements:
            required_skill_id = station_skill_requirements[station.id]
            if hasattr(player, 'skill_manager'):
                skill = player.skill_manager.get_skill(required_skill_id)
                if not skill:
                    return True
        return False

    def handle_input(self, event, crafting_system, player):
        """
        Обработка ввода пользователя.

        Args:
            event: Событие Pygame
            crafting_system: Система крафта
            player: Объект игрока

        Returns:
            tuple: (продолжить работу окна, сообщение о результате)
        """
        stations = crafting_system.get_all_stations()

        if not stations:
            return False, None

        current_station = stations[self.selected_station_index]

        # Проверяем, не заблокирована ли текущая станция
        if self._is_station_locked(current_station, player):
            # Если станция заблокирована, показываем только пустой список рецептов
            all_recipes = []
        else:
            all_recipes = current_station.get_available_recipes(player)

        # Фильтруем по категориям
        if "all" not in self.current_recipe_categories:
            recipes = [r for r in all_recipes if r.category in self.current_recipe_categories]
        else:
            recipes = all_recipes

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Закрыть окно
                return False, None

            elif event.key == pygame.K_UP:
                # Предыдущий рецепт
                if recipes:
                    self.selected_recipe_index = (self.selected_recipe_index - 1) % len(recipes)

            elif event.key == pygame.K_DOWN:
                # Следующий рецепт
                if recipes:
                    self.selected_recipe_index = (self.selected_recipe_index + 1) % len(recipes)

            elif event.key == pygame.K_LEFT:
                # Предыдущая станция (пропускаем заблокированные)
                new_index = (self.selected_station_index - 1) % len(stations)
                # Пропускаем заблокированные станции
                attempts = 0
                while self._is_station_locked(stations[new_index], player) and attempts < len(stations):
                    new_index = (new_index - 1) % len(stations)
                    attempts += 1
                self.selected_station_index = new_index
                self.selected_recipe_index = 0

            elif event.key == pygame.K_RIGHT:
                # Следующая станция (пропускаем заблокированные)
                new_index = (self.selected_station_index + 1) % len(stations)
                # Пропускаем заблокированные станции
                attempts = 0
                while self._is_station_locked(stations[new_index], player) and attempts < len(stations):
                    new_index = (new_index + 1) % len(stations)
                    attempts += 1
                self.selected_station_index = new_index
                self.selected_recipe_index = 0

            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # Создать предмет
                if recipes and 0 <= self.selected_recipe_index < len(recipes):
                    recipe = recipes[self.selected_recipe_index]
                    success, message = crafting_system.craft_item(recipe.id, player, player.inventory)
                    return True, message

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                mouse_pos = pygame.mouse.get_pos()

                # Проверяем клик по станциям
                for i, rect in enumerate(self.station_rects):
                    if rect.collidepoint(mouse_pos):
                        # Проверяем, не заблокирована ли станция
                        if not self._is_station_locked(stations[i], player):
                            self.selected_station_index = i
                            self.selected_recipe_index = 0
                        else:
                            # Показываем сообщение о блокировке
                            station_skill_requirements = {
                                'workbench': 'Изготовление',
                                'forge': 'Изготовление',
                                'alchemy_table': 'Алхимия',
                                'enchanting_table': 'Зачарование'
                            }
                            required_skill = station_skill_requirements.get(stations[i].id, 'умение')
                            return True, f"Станция заблокирована. Требуется умение: {required_skill}"
                        return True, None

                # Проверяем клик по рецептам
                for rect, recipe_index, recipe in self.recipe_rects:
                    if rect.collidepoint(mouse_pos):
                        # Двойной клик для крафта
                        if recipe_index == self.selected_recipe_index:
                            success, message = crafting_system.craft_item(recipe.id, player, player.inventory)
                            return True, message
                        else:
                            self.selected_recipe_index = recipe_index
                        return True, None

            elif event.button == 3:  # Правая кнопка мыши
                mouse_pos = pygame.mouse.get_pos()

                # Проверяем ПКМ по рецептам - сразу крафтим
                for rect, recipe_index, recipe in self.recipe_rects:
                    if rect.collidepoint(mouse_pos):
                        self.selected_recipe_index = recipe_index
                        success, message = crafting_system.craft_item(recipe.id, player, player.inventory)
                        return True, message

        # Обработка кликов по вкладкам категорий
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for rect, category_id, recipe_categories in self.category_rects:
                if rect.collidepoint(mouse_pos):
                    self.current_category = category_id
                    self.current_recipe_categories = recipe_categories
                    self.selected_recipe_index = 0  # Сбрасываем выбор рецепта
                    return True, None

        return True, None

    def reset_selection(self):
        """Сбросить выбор при открытии окна."""
        self.selected_station_index = 0
        self.selected_recipe_index = 0
        self.current_category = "all"
