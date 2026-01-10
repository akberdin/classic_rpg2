"""
Окно чит-меню.
"""
import json
import os
import pygame
from game.ui.base import UIHelper


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
            'learn_all_skills': {'name': 'Выучить все умения', 'enabled': False, 'one_time': True},
            'learn_all_recipes': {'name': 'Изучить все рецепты', 'enabled': False, 'one_time': True},
            'teleport_academy': {'name': 'Телепорт к академии магов', 'enabled': False, 'one_time': True},
            'teleport_warrior_academy': {'name': 'Телепорт к военной академии', 'enabled': False, 'one_time': True},
            'teleport_secret_camp': {'name': 'Телепорт к Тайному лагерю', 'enabled': False, 'one_time': True},
            'level_up': {'name': 'Повысить уровень на 1', 'enabled': False, 'one_time': True},
            'give_artifact': {'name': 'Дать случайный артефакт', 'enabled': False, 'one_time': True},
            'add_companion': {'name': 'Добавить спутника', 'enabled': False, 'one_time': True, 'submenu': True},
        }

        self.selected_index = 0
        self.button_rects = []  # Прямоугольники кнопок для обработки мыши

        # Состояние подменю добавления спутника
        self.companion_submenu_active = False
        self.companion_submenu_stage = 'select_type'  # 'select_type' или 'select_level'
        self.companion_types = []  # Список доступных типов спутников
        self.companion_type_index = 0  # Выбранный тип
        self.companion_level = 1  # Выбранный уровень
        self.selected_companion_type = None  # Выбранный тип для добавления
        self.companion_config = None  # Конфигурация спутников
        self._load_companion_config()

    def _load_companion_config(self):
        """Загрузить конфигурацию спутников из файла"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'companion_config.json')
            config_path = os.path.normpath(config_path)
            with open(config_path, 'r', encoding='utf-8') as f:
                self.companion_config = json.load(f)
            # Получаем список типов спутников
            self.companion_types = list(self.companion_config.get('companions', {}).keys())
        except Exception as e:
            print(f"Ошибка загрузки конфигурации спутников: {e}")
            self.companion_config = {'companions': {}}
            self.companion_types = []

    def _get_companion_display_name(self, companion_type: str) -> str:
        """Получить отображаемое имя типа спутника"""
        if self.companion_config and 'companions' in self.companion_config:
            companion_info = self.companion_config['companions'].get(companion_type, {})
            return companion_info.get('display_name', companion_type.capitalize())
        return companion_type.capitalize()

    def _get_companion_description(self, companion_type: str) -> str:
        """Получить описание типа спутника"""
        if self.companion_config and 'companions' in self.companion_config:
            companion_info = self.companion_config['companions'].get(companion_type, {})
            return companion_info.get('description', '')
        return ''

    def _get_companion_max_level(self, companion_type: str) -> int:
        """Получить максимальный уровень спутника"""
        if self.companion_config and 'companions' in self.companion_config:
            companion_info = self.companion_config['companions'].get(companion_type, {})
            return companion_info.get('max_level', 20)
        return 20

    def handle_input(self, event, game):
        """
        Обработка ввода в чит-меню

        Args:
            event: Pygame событие
            game: Ссылка на основной объект игры

        Returns:
            bool: True если меню нужно закрыть
        """
        # Обработка подменю добавления спутника
        if self.companion_submenu_active:
            return self._handle_companion_submenu_input(event, game)

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

    def _handle_companion_submenu_input(self, event, game):
        """
        Обработка ввода в подменю добавления спутника

        Args:
            event: Pygame событие
            game: Ссылка на основной объект игры

        Returns:
            bool: True если меню нужно закрыть
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Закрыть подменю
                if self.companion_submenu_stage == 'select_level':
                    # Вернуться к выбору типа
                    self.companion_submenu_stage = 'select_type'
                    self.companion_level = 1
                else:
                    # Закрыть подменю полностью
                    self.companion_submenu_active = False
                    self.companion_submenu_stage = 'select_type'
                    self.companion_type_index = 0
                    self.companion_level = 1
                return False

            if self.companion_submenu_stage == 'select_type':
                # Выбор типа спутника
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.companion_type_index = max(0, self.companion_type_index - 1)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.companion_type_index = min(len(self.companion_types) - 1, self.companion_type_index + 1)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.companion_types:
                        self.selected_companion_type = self.companion_types[self.companion_type_index]
                        self.companion_submenu_stage = 'select_level'
                        self.companion_level = 1

            elif self.companion_submenu_stage == 'select_level':
                # Выбор уровня спутника
                max_level = self._get_companion_max_level(self.selected_companion_type)
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.companion_level = min(max_level, self.companion_level + 1)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.companion_level = max(1, self.companion_level - 1)
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.companion_level = max(1, self.companion_level - 5)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.companion_level = min(max_level, self.companion_level + 5)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Добавить спутника
                    self._add_companion(game, self.selected_companion_type, self.companion_level)
                    # Закрыть подменю
                    self.companion_submenu_active = False
                    self.companion_submenu_stage = 'select_type'
                    self.companion_type_index = 0
                    self.companion_level = 1

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                mouse_pos = event.pos
                for i, rect in enumerate(self.button_rects):
                    if rect.collidepoint(mouse_pos):
                        if self.companion_submenu_stage == 'select_type':
                            if i < len(self.companion_types):
                                self.selected_companion_type = self.companion_types[i]
                                self.companion_submenu_stage = 'select_level'
                                self.companion_level = 1
                        break

        return False

    def _add_companion(self, game, companion_type: str, level: int):
        """
        Добавить спутника игроку

        Args:
            game: Ссылка на основной объект игры
            companion_type: Тип спутника
            level: Уровень спутника
        """
        if hasattr(game, 'player') and hasattr(game.player, 'companion_manager'):
            companion = game.player.companion_manager.add_companion(companion_type, level)
            display_name = self._get_companion_display_name(companion_type)
            print(f"Добавлен спутник: {display_name} (Уровень {level})")
        else:
            print("Ошибка: система спутников недоступна!")

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

            elif cheat_id == 'learn_all_skills':
                from game.systems.skills import AVAILABLE_SKILLS
                learned_count = 0
                for skill_id in AVAILABLE_SKILLS.keys():
                    if game.player.skill_manager.learn_skill(skill_id):
                        learned_count += 1
                print(f"Выучено умений: {learned_count}")

            elif cheat_id == 'learn_all_recipes':
                # Изучаем все рецепты из системы крафта
                if hasattr(game, 'crafting_system') and game.crafting_system:
                    learned_count = 0
                    for recipe_id in game.crafting_system.recipes.keys():
                        if recipe_id not in game.player.known_recipes:
                            game.player.known_recipes.add(recipe_id)
                            learned_count += 1
                    print(f"Изучено рецептов: {learned_count}")
                else:
                    print("Система крафта не найдена!")

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

            elif cheat_id == 'teleport_warrior_academy':
                # Ищем военную академию на карте
                academy_found = False
                for location in game.game_map.locations:
                    if location.location_type == 'warrior_academy':
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
                    print("Не удалось найти свободное место возле военной академии!")

            elif cheat_id == 'teleport_secret_camp':
                # Ищем Тайный лагерь на карте
                camp_found = False
                for location in game.game_map.locations:
                    if location.location_type == 'secret_camp':
                        # Ищем свободную клетку в радиусе 10 от лагеря
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
                                    camp_found = True
                                    print(f"Телепортация к {location.name}!")
                                    break

                        if camp_found:
                            break

                if not camp_found:
                    print("Не удалось найти Тайный лагерь!")

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
                # Генерируем случайный артефакт (оружие, броня, украшение, пояс, рюкзак или талисман)
                item_type = random.choice(['weapon', 'armor', 'jewelry', 'belt', 'backpack', 'talisman'])
                try:
                    if item_type == 'weapon':
                        # Правильные параметры: level, quality, max_quality
                        artifact = ItemGenerator.generate_weapon(
                            level=game.player.level,
                            quality=ItemQuality.ARTIFACT,
                            max_quality=ItemQuality.ARTIFACT
                        )
                    elif item_type == 'armor':
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
                    elif item_type == 'jewelry':
                        # Генерируем артефактное украшение (кольцо, амулет или браслет)
                        jewelry_slots = [
                            EquipmentSlot.RING_1, EquipmentSlot.RING_2,
                            EquipmentSlot.RING_3, EquipmentSlot.RING_4,
                            EquipmentSlot.AMULET,
                            EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2
                        ]
                        slot = random.choice(jewelry_slots)
                        artifact = ItemGenerator.generate_jewelry(
                            level=game.player.level,
                            slot=slot,
                            quality=ItemQuality.ARTIFACT
                        )
                    elif item_type == 'belt':
                        artifact = ItemGenerator.generate_belt(
                            level=game.player.level,
                            quality=ItemQuality.ARTIFACT
                        )
                    elif item_type == 'backpack':
                        artifact = ItemGenerator.generate_backpack(
                            level=game.player.level,
                            quality=ItemQuality.ARTIFACT
                        )
                    elif item_type == 'talisman':
                        artifact = ItemGenerator.generate_talisman(
                            level=game.player.level,
                            quality=ItemQuality.ARTIFACT
                        )

                    game.player.inventory.add_item(artifact, 1)
                    print(f"Получен артефакт: {artifact.name}!")
                except Exception as e:
                    print(f"Ошибка при создании артефакта: {e}")
                    import traceback
                    traceback.print_exc()

            elif cheat_id == 'add_companion':
                # Открываем подменю выбора спутника
                if self.companion_types:
                    self.companion_submenu_active = True
                    self.companion_submenu_stage = 'select_type'
                    self.companion_type_index = 0
                    self.companion_level = 1
                else:
                    print("Нет доступных типов спутников!")

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
                    # Инвалидируем кэш миникарты для перерисовки
                    game.fog_of_war.mark_minimap_dirty()
                    print("Карта ОТКРЫТА")
                else:
                    # Закрываем карту (кроме видимой области)
                    game.fog_of_war.update_vision(game.player.x, game.player.y)
                    # Инвалидируем кэш миникарты
                    game.fog_of_war.mark_minimap_dirty()
                    print("Карта ЗАКРЫТА")

    def render(self):
        """Отрисовка окна чит-меню"""
        # Если активно подменю выбора спутника, рисуем его
        if self.companion_submenu_active:
            self._render_companion_submenu()
            return

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
            window_height = self.scaler.scale_height(700)
        else:
            window_width = min(700, int(screen_width * 0.7))
            window_height = min(700, int(screen_height * 0.8))

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

    def _render_companion_submenu(self):
        """Отрисовка подменю выбора спутника"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна
        if self.scaler:
            window_width = self.scaler.scale_width(600)
            window_height = self.scaler.scale_height(500)
        else:
            window_width = min(600, int(screen_width * 0.6))
            window_height = min(500, int(screen_height * 0.6))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна с градиентом
        UIHelper.draw_gradient_rect(
            self.screen, window_x, window_y, window_width, window_height,
            (40, 50, 40), (60, 75, 60)
        )

        # Рамка окна
        pygame.draw.rect(
            self.screen,
            (100, 200, 100),
            (window_x, window_y, window_width, window_height),
            4
        )

        if self.companion_submenu_stage == 'select_type':
            self._render_companion_type_selection(window_x, window_y, window_width, window_height)
        elif self.companion_submenu_stage == 'select_level':
            self._render_companion_level_selection(window_x, window_y, window_width, window_height)

    def _render_companion_type_selection(self, window_x, window_y, window_width, window_height):
        """Отрисовка выбора типа спутника"""
        # Заголовок
        title_text = self.font.render("Выберите спутника", True, (100, 255, 100))
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + 20
        self.screen.blit(title_text, title_rect)

        # Подзаголовок
        subtitle_text = self.info_font.render(
            "W/S - выбор, Enter - подтвердить, ESC - назад",
            True, (150, 150, 150)
        )
        subtitle_rect = subtitle_text.get_rect()
        subtitle_rect.centerx = window_x + window_width // 2
        subtitle_rect.y = window_y + 55
        self.screen.blit(subtitle_text, subtitle_rect)

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            (100, 150, 100),
            (window_x + 10, window_y + 85),
            (window_x + window_width - 10, window_y + 85),
            2
        )

        # Список типов спутников
        self.button_rects = []
        button_y = window_y + 100
        button_height = 70
        button_margin = 10
        button_width = window_width - 60

        for i, companion_type in enumerate(self.companion_types):
            button_x = window_x + 30
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            self.button_rects.append(button_rect)

            # Фон кнопки
            if i == self.companion_type_index:
                bg_color = (60, 90, 60)
                border_color = (100, 200, 100)
                border_width = 3
            else:
                bg_color = (50, 65, 50)
                border_color = (80, 120, 80)
                border_width = 2

            pygame.draw.rect(self.screen, bg_color, button_rect)
            pygame.draw.rect(self.screen, border_color, button_rect, border_width)

            # Имя спутника
            display_name = self._get_companion_display_name(companion_type)
            name_text = self.font.render(display_name, True, (255, 255, 255))
            name_rect = name_text.get_rect()
            name_rect.left = button_x + 15
            name_rect.y = button_y + 10
            self.screen.blit(name_text, name_rect)

            # Описание спутника
            description = self._get_companion_description(companion_type)
            if description:
                desc_text = self.info_font.render(description, True, (180, 180, 180))
                desc_rect = desc_text.get_rect()
                desc_rect.left = button_x + 15
                desc_rect.y = button_y + 40
                self.screen.blit(desc_text, desc_rect)

            button_y += button_height + button_margin

        # Если нет спутников
        if not self.companion_types:
            no_companions_text = self.font.render("Нет доступных спутников", True, (200, 100, 100))
            no_companions_rect = no_companions_text.get_rect()
            no_companions_rect.centerx = window_x + window_width // 2
            no_companions_rect.centery = window_y + window_height // 2
            self.screen.blit(no_companions_text, no_companions_rect)

    def _render_companion_level_selection(self, window_x, window_y, window_width, window_height):
        """Отрисовка выбора уровня спутника"""
        display_name = self._get_companion_display_name(self.selected_companion_type)
        max_level = self._get_companion_max_level(self.selected_companion_type)

        # Заголовок
        title_text = self.font.render(f"Уровень: {display_name}", True, (100, 255, 100))
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + 20
        self.screen.blit(title_text, title_rect)

        # Подзаголовок
        subtitle_text = self.info_font.render(
            "W/S - ±1, A/D - ±5, Enter - добавить, ESC - назад",
            True, (150, 150, 150)
        )
        subtitle_rect = subtitle_text.get_rect()
        subtitle_rect.centerx = window_x + window_width // 2
        subtitle_rect.y = window_y + 55
        self.screen.blit(subtitle_text, subtitle_rect)

        # Разделительная линия
        pygame.draw.line(
            self.screen,
            (100, 150, 100),
            (window_x + 10, window_y + 85),
            (window_x + window_width - 10, window_y + 85),
            2
        )

        # Большое отображение уровня по центру
        level_y = window_y + 150

        # Фон для уровня
        level_box_width = 200
        level_box_height = 100
        level_box_x = window_x + (window_width - level_box_width) // 2
        level_box_rect = pygame.Rect(level_box_x, level_y, level_box_width, level_box_height)

        pygame.draw.rect(self.screen, (50, 70, 50), level_box_rect)
        pygame.draw.rect(self.screen, (100, 200, 100), level_box_rect, 3)

        # Текст уровня
        level_text = self.font.render(f"Уровень {self.companion_level}", True, (255, 255, 100))
        level_text_rect = level_text.get_rect()
        level_text_rect.centerx = level_box_x + level_box_width // 2
        level_text_rect.centery = level_y + level_box_height // 2 - 10
        self.screen.blit(level_text, level_text_rect)

        # Диапазон
        range_text = self.info_font.render(f"(1 - {max_level})", True, (150, 150, 150))
        range_rect = range_text.get_rect()
        range_rect.centerx = level_box_x + level_box_width // 2
        range_rect.centery = level_y + level_box_height // 2 + 20
        self.screen.blit(range_text, range_rect)

        # Получаем информацию о ранге для выбранного уровня
        rank_info = self._get_rank_for_level(self.selected_companion_type, self.companion_level)
        if rank_info:
            rank_y = level_y + level_box_height + 30
            rank_text = self.info_font.render(f"Ранг: {rank_info['name']}", True, (200, 200, 100))
            rank_rect = rank_text.get_rect()
            rank_rect.centerx = window_x + window_width // 2
            rank_rect.y = rank_y
            self.screen.blit(rank_text, rank_rect)

            if rank_info.get('description'):
                rank_desc_text = self.info_font.render(rank_info['description'], True, (150, 150, 150))
                rank_desc_rect = rank_desc_text.get_rect()
                rank_desc_rect.centerx = window_x + window_width // 2
                rank_desc_rect.y = rank_y + 25
                self.screen.blit(rank_desc_text, rank_desc_rect)

        # Кнопка подтверждения
        confirm_y = window_y + window_height - 80
        confirm_width = 200
        confirm_height = 50
        confirm_x = window_x + (window_width - confirm_width) // 2
        confirm_rect = pygame.Rect(confirm_x, confirm_y, confirm_width, confirm_height)

        pygame.draw.rect(self.screen, (60, 100, 60), confirm_rect)
        pygame.draw.rect(self.screen, (100, 200, 100), confirm_rect, 3)

        confirm_text = self.font.render("Добавить", True, (255, 255, 255))
        confirm_text_rect = confirm_text.get_rect()
        confirm_text_rect.centerx = confirm_x + confirm_width // 2
        confirm_text_rect.centery = confirm_y + confirm_height // 2
        self.screen.blit(confirm_text, confirm_text_rect)

    def _get_rank_for_level(self, companion_type: str, level: int) -> dict:
        """Получить информацию о ранге для заданного уровня"""
        if not self.companion_config or 'companions' not in self.companion_config:
            return None

        companion_info = self.companion_config['companions'].get(companion_type, {})
        ranks = companion_info.get('ranks', {})

        for rank_id, rank_data in ranks.items():
            level_range = rank_data.get('level_range', [1, 20])
            if level_range[0] <= level <= level_range[1]:
                return rank_data

        return None
