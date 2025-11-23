"""
Окно чит-меню.
"""
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
