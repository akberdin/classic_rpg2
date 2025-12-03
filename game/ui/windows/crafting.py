"""
Окно крафта предметов.
"""
import pygame
from game.ui.base import UIHelper


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

        # Размеры окна (адаптивные)
        if self.scaler:
            window_width = self.scaler.scale_width(1000)
            window_height = self.scaler.scale_height(700)
        else:
            window_width = min(1000, int(screen_width * 0.9))
            window_height = min(700, int(screen_height * 0.8))

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
            (window_x + int(10 * scale_w), window_y + int(50 * scale_h)),
            (window_x + window_width - int(10 * scale_w), window_y + int(50 * scale_h)),
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
                stations, window_x, window_y, window_width, window_height,
                scale_w, scale_h
            )

            # Получаем текущую станцию
            if 0 <= self.selected_station_index < len(stations):
                current_station = stations[self.selected_station_index]

                # Отрисовка рецептов (правая панель)
                self._render_recipes(
                    crafting_system, current_station, player,
                    window_x, window_y, window_width, window_height,
                    scale_w, scale_h, mouse_pos
                )

        # Подсказки внизу
        help_y = window_y + window_height - int(35 * scale_h)
        help_text = self.info_font.render(
            "[W/S] Выбор  [ENTER] Создать  [ESC] Закрыть  [A/D] Сменить станцию",
            True,
            (180, 180, 180)
        )
        help_rect = help_text.get_rect()
        help_rect.centerx = window_x + window_width // 2
        help_rect.y = help_y
        self.screen.blit(help_text, help_rect)

    def _render_stations(self, stations, window_x, window_y, window_width, window_height, scale_w, scale_h):
        """Отрисовка списка станций."""
        stations_x = window_x + int(20 * scale_w)
        stations_y = window_y + int(70 * scale_h)
        station_width = int(250 * scale_w)
        station_height = int(60 * scale_h)
        station_spacing = int(10 * scale_h)

        # Заголовок
        stations_title = self.info_font.render(
            "Станции крафта:",
            True,
            (200, 200, 200)
        )
        self.screen.blit(stations_title, (stations_x, stations_y - int(25 * scale_h)))

        for i, station in enumerate(stations):
            rect_y = stations_y + i * (station_height + station_spacing)

            # Проверяем, не выходит ли за границы
            if rect_y + station_height > window_y + window_height - int(50 * scale_h):
                break

            # Цвет в зависимости от выбора
            if i == self.selected_station_index:
                bg_color = (80, 80, 120)
                border_color = (150, 150, 200)
            else:
                bg_color = (50, 50, 60)
                border_color = (80, 80, 100)

            # Фон станции
            station_rect = pygame.Rect(stations_x, rect_y, station_width, station_height)
            pygame.draw.rect(self.screen, bg_color, station_rect)
            pygame.draw.rect(self.screen, border_color, station_rect, 2)

            # Сохраняем rect для обработки мыши
            self.station_rects.append(station_rect)

            # Название станции
            name_text = self.font.render(station.name, True, (255, 255, 255))
            name_rect = name_text.get_rect()
            name_rect.centerx = station_rect.centerx
            name_rect.y = rect_y + int(10 * scale_h)
            self.screen.blit(name_text, name_rect)

            # Описание станции (мелким шрифтом)
            desc_text = self.info_font.render(
                station.description[:35] + ("..." if len(station.description) > 35 else ""),
                True,
                (180, 180, 180)
            )
            self.screen.blit(desc_text, (stations_x + int(10 * scale_w), rect_y + int(35 * scale_h)))

    def _render_recipes(self, crafting_system, station, player, window_x, window_y,
                       window_width, window_height, scale_w, scale_h, mouse_pos):
        """Отрисовка списка рецептов."""
        recipes_x = window_x + int(300 * scale_w)
        recipes_y = window_y + int(70 * scale_h)
        recipes_width = window_width - int(340 * scale_w)
        recipe_height = int(80 * scale_h)
        recipe_spacing = int(10 * scale_h)

        # Заголовок
        recipes_title = self.info_font.render(
            f"Рецепты ({station.name}):",
            True,
            (200, 200, 200)
        )
        self.screen.blit(recipes_title, (recipes_x, recipes_y - int(25 * scale_h)))

        # Получаем доступные рецепты
        all_recipes = station.get_available_recipes(player)

        # Фильтруем по категории
        if self.current_category != "all":
            recipes = [r for r in all_recipes if r.category == self.current_category]
        else:
            recipes = all_recipes

        if not recipes:
            # Если нет рецептов
            no_recipes_text = self.font.render(
                "Нет доступных рецептов" if not all_recipes else "Нет рецептов в этой категории",
                True,
                (150, 150, 150)
            )
            self.screen.blit(no_recipes_text, (recipes_x + int(100 * scale_w), recipes_y + int(100 * scale_h)))
            return

        # Корректируем выбранный индекс
        if self.selected_recipe_index >= len(recipes):
            self.selected_recipe_index = max(0, len(recipes) - 1)

        # Отрисовка рецептов
        max_visible = int((window_height - 150 * scale_h) / (recipe_height + recipe_spacing))
        start_index = max(0, self.selected_recipe_index - max_visible + 1)

        for i in range(start_index, min(start_index + max_visible, len(recipes))):
            recipe = recipes[i]
            rect_y = recipes_y + (i - start_index) * (recipe_height + recipe_spacing)

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
            recipe_rect = pygame.Rect(recipes_x, rect_y, recipes_width, recipe_height)
            pygame.draw.rect(self.screen, bg_color, recipe_rect)
            pygame.draw.rect(self.screen, border_color, recipe_rect, 2)

            # Сохраняем rect для обработки мыши
            self.recipe_rects.append((recipe_rect, recipe))

            # Название рецепта
            name_color = (255, 255, 255) if can_craft else (200, 150, 150)
            name_text = self.font.render(recipe.name, True, name_color)
            self.screen.blit(name_text, (recipes_x + int(10 * scale_w), rect_y + int(5 * scale_h)))

            # Категория и уровень
            category_name = crafting_system.get_category_name(recipe.category)
            info_text = self.info_font.render(
                f"[{category_name}] Ур. {recipe.required_level}",
                True,
                (150, 150, 200)
            )
            self.screen.blit(info_text, (recipes_x + int(10 * scale_w), rect_y + int(30 * scale_h)))

            # Ингредиенты
            ingredients_y = rect_y + int(50 * scale_h)
            ingredients_text = "Требуется: "
            for j, ingredient in enumerate(recipe.ingredients):
                item_name = ingredient['item']
                required = ingredient['quantity']
                has = player.inventory.get_resource_count(item_name)

                if j > 0:
                    ingredients_text += ", "
                ingredients_text += f"{item_name} ({has}/{required})"

            ingr_color = (100, 200, 100) if can_craft else (200, 100, 100)
            ingr_surface = self.info_font.render(ingredients_text[:80], True, ingr_color)
            self.screen.blit(ingr_surface, (recipes_x + int(10 * scale_w), ingredients_y))

            # Результат
            result_text = self.info_font.render(
                f"Результат: {recipe.name} x{recipe.result_quantity}",
                True,
                (255, 215, 0)
            )
            self.screen.blit(
                result_text,
                (recipes_x + recipes_width - int(250 * scale_w), rect_y + int(30 * scale_h))
            )

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
        all_recipes = current_station.get_available_recipes(player)

        # Фильтруем по категории
        if self.current_category != "all":
            recipes = [r for r in all_recipes if r.category == self.current_category]
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
                # Предыдущая станция
                self.selected_station_index = (self.selected_station_index - 1) % len(stations)
                self.selected_recipe_index = 0

            elif event.key == pygame.K_RIGHT:
                # Следующая станция
                self.selected_station_index = (self.selected_station_index + 1) % len(stations)
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
                        self.selected_station_index = i
                        self.selected_recipe_index = 0
                        return True, None

                # Проверяем клик по рецептам
                for i, (rect, recipe) in enumerate(self.recipe_rects):
                    if rect.collidepoint(mouse_pos):
                        # Двойной клик для крафта
                        if i == self.selected_recipe_index:
                            success, message = crafting_system.craft_item(recipe.id, player, player.inventory)
                            return True, message
                        else:
                            self.selected_recipe_index = i
                        return True, None

        return True, None

    def reset_selection(self):
        """Сбросить выбор при открытии окна."""
        self.selected_station_index = 0
        self.selected_recipe_index = 0
        self.current_category = "all"
