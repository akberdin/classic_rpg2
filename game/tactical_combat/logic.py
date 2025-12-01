"""
Логика тактического боя
"""
import math
import json
import os


class BattlefieldUnit:
    """Представление юнита на поле боя"""

    def __init__(self, character, x, y):
        """
        Инициализация юнита

        Args:
            character: Персонаж (игрок или NPC)
            x: Координата X на поле
            y: Координата Y на поле
        """
        self.character = character
        self.x = x
        self.y = y
        self.has_acted = False  # Ходил ли юнит в этот ход

    def get_weapon_range(self):
        """
        Получить радиус действия оружия юнита

        Returns:
            int: Радиус действия в клетках
        """
        weapon = self.character.inventory.get_equipped_item('weapon')
        if weapon and hasattr(weapon, 'get_tactical_range'):
            return weapon.get_tactical_range()
        return 1  # По умолчанию рукопашный бой

    def reset_turn(self):
        """Сбросить состояние хода"""
        self.has_acted = False


class TacticalCombatSystem:
    """Система тактического боя"""

    def __init__(self, player, enemy, screen, font, scaler=None, game_map=None,
                 respawn_manager=None, sprite_manager=None, game=None):
        """
        Инициализация системы тактического боя

        Args:
            player: Игрок
            enemy: Враг
            screen: Pygame экран
            font: Шрифт для отображения текста
            scaler: UIScaler для адаптивного масштабирования (опционально)
            game_map: Карта игры (для размещения лута)
            respawn_manager: Менеджер респавна NPC
            sprite_manager: Менеджер спрайтов
            game: Объект игры
        """
        self.player = player
        self.enemy = enemy
        self.screen = screen
        self.font = font
        self.scaler = scaler
        self.game_map = game_map
        self.respawn_manager = respawn_manager
        self.sprite_manager = sprite_manager
        self.game = game

        # Загружаем конфиг
        self.config = self._load_config()

        # Параметры поля боя
        self.battlefield_width = self.config['battlefield']['width']
        self.battlefield_height = self.config['battlefield']['height']
        self.cell_size = self.config['battlefield']['cell_size']

        # Создаем юнитов
        player_x = self.config['battlefield']['player_spawn_x']
        enemy_x = self.config['battlefield']['enemy_spawn_x']
        spawn_y = self.battlefield_height // 2

        self.player_unit = BattlefieldUnit(player, player_x, spawn_y)
        self.enemy_unit = BattlefieldUnit(enemy, enemy_x, spawn_y)

        # Состояние боя
        self.active = True
        self.current_turn = "player"  # player или enemy
        self.selected_unit = None
        self.selected_action = None  # move, skill, potion, pass
        self.hovered_cell = None
        self.combat_log = []
        self.max_log_entries = 10

        # Добавляем начальное сообщение
        self.add_to_log(f"=== ТАКТИЧЕСКИЙ БОЙ НАЧАЛСЯ ===")
        self.add_to_log(f"Противник: {enemy.name} (Уровень {enemy.level})")

    def _load_config(self):
        """Загрузить конфигурацию тактического боя"""
        config_path = os.path.join('game', 'config', 'tactical_combat_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Используем дефолтные настройки
            return {
                'battlefield': {
                    'width': 20,
                    'height': 10,
                    'cell_size': 64,
                    'player_spawn_x': 2,
                    'enemy_spawn_x': 17
                },
                'movement': {
                    'base_movement_range': 3,
                    'diagonal_allowed': True
                },
                'ui': {
                    'grid_color': [100, 100, 120],
                    'cell_hover_color': [150, 150, 200, 128],
                    'player_unit_color': [100, 200, 100],
                    'enemy_unit_color': [200, 100, 100]
                }
            }

    def add_to_log(self, message):
        """Добавить сообщение в лог"""
        self.combat_log.append(message)
        if len(self.combat_log) > self.max_log_entries:
            self.combat_log.pop(0)

    def get_distance(self, x1, y1, x2, y2):
        """
        Вычислить расстояние между двумя точками

        Args:
            x1, y1: Координаты первой точки
            x2, y2: Координаты второй точки

        Returns:
            float: Расстояние
        """
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def is_in_range(self, unit, target_x, target_y, range_distance):
        """
        Проверить, находится ли цель в радиусе действия

        Args:
            unit: Юнит
            target_x, target_y: Координаты цели
            range_distance: Радиус действия

        Returns:
            bool: True если в радиусе
        """
        distance = self.get_distance(unit.x, unit.y, target_x, target_y)
        return distance <= range_distance

    def can_move_to(self, unit, target_x, target_y):
        """
        Проверить, может ли юнит переместиться в указанную клетку

        Args:
            unit: Юнит
            target_x, target_y: Целевые координаты

        Returns:
            bool: True если может переместиться
        """
        # Проверяем границы поля
        if target_x < 0 or target_x >= self.battlefield_width:
            return False
        if target_y < 0 or target_y >= self.battlefield_height:
            return False

        # Проверяем, не занята ли клетка
        if (target_x == self.player_unit.x and target_y == self.player_unit.y):
            return False
        if (target_x == self.enemy_unit.x and target_y == self.enemy_unit.y):
            return False

        # Проверяем дистанцию перемещения
        move_range = self.config['movement']['base_movement_range']
        distance = self.get_distance(unit.x, unit.y, target_x, target_y)

        return distance <= move_range

    def move_unit(self, unit, target_x, target_y):
        """
        Переместить юнита

        Args:
            unit: Юнит для перемещения
            target_x, target_y: Целевые координаты

        Returns:
            bool: True если перемещение успешно
        """
        if self.can_move_to(unit, target_x, target_y):
            old_x, old_y = unit.x, unit.y
            unit.x = target_x
            unit.y = target_y
            unit.has_acted = True

            name = "Вы" if unit == self.player_unit else unit.character.name
            self.add_to_log(f"{name} переместился с ({old_x}, {old_y}) на ({target_x}, {target_y})")
            return True
        return False

    def get_skill_targets(self, skill, caster_unit):
        """
        Получить возможные цели для умения

        Args:
            skill: Умение
            caster_unit: Юнит, использующий умение

        Returns:
            list: Список возможных целей
        """
        # Получаем радиус действия умения из конфига
        skill_range = skill.config.get('tactical_range', 1)

        targets = []

        # Определяем возможные цели в зависимости от типа умения
        from game.skills import SkillCategory

        if skill.category == SkillCategory.MAGIC and skill.skill_id in ['heal', 'regeneration', 'stamina_recovery', 'mage_shield']:
            # Лечебные умения - применяются на себя
            if skill_range == 0:
                targets.append(caster_unit)
        else:
            # Боевые умения - применяются на врага
            target_unit = self.enemy_unit if caster_unit == self.player_unit else self.player_unit

            if self.is_in_range(caster_unit, target_unit.x, target_unit.y, skill_range):
                targets.append(target_unit)

        return targets

    def use_skill(self, skill, caster_unit, target_unit):
        """
        Использовать умение

        Args:
            skill: Умение
            caster_unit: Юнит, использующий умение
            target_unit: Цель умения

        Returns:
            dict: Результат использования умения
        """
        # Используем умение через менеджер умений персонажа
        result = caster_unit.character.skill_manager.use_skill(skill, target_unit.character)

        if result['success']:
            self.add_to_log(result['message'])
            caster_unit.has_acted = True

            # Проверяем, не убит ли противник
            if 'killed' in result and result['killed']:
                return {'status': 'victory', 'message': result['message']}

        return {'status': 'continue', 'message': result.get('message', '')}

    def execute_enemy_turn(self):
        """
        Выполнить ход врага (AI)

        Returns:
            str: Статус боя после хода
        """
        # Простой AI: двигаемся к игроку и атакуем
        distance = self.get_distance(self.enemy_unit.x, self.enemy_unit.y,
                                     self.player_unit.x, self.player_unit.y)

        weapon_range = self.enemy_unit.get_weapon_range()

        # Если враг вне дистанции атаки - приближаемся
        if distance > weapon_range:
            # Двигаемся к игроку
            dx = self.player_unit.x - self.enemy_unit.x
            dy = self.player_unit.y - self.enemy_unit.y

            # Нормализуем направление
            distance_norm = math.sqrt(dx*dx + dy*dy)
            if distance_norm > 0:
                dx = dx / distance_norm
                dy = dy / distance_norm

            # Вычисляем новую позицию
            move_range = self.config['movement']['base_movement_range']
            new_x = int(self.enemy_unit.x + dx * min(move_range, distance - weapon_range))
            new_y = int(self.enemy_unit.y + dy * min(move_range, distance - weapon_range))

            # Двигаемся
            self.move_unit(self.enemy_unit, new_x, new_y)
        else:
            # В дистанции атаки - атакуем
            attack_result = self.enemy.attack(self.player)

            if attack_result['dodged']:
                self.add_to_log(f"Вы уклонились от атаки {self.enemy.name}!")
            elif attack_result['hit']:
                damage = attack_result['damage']
                self.add_to_log(f"{self.enemy.name} атакует вас! Урон: {damage}")

                if not self.player.is_alive:
                    return "defeat"

            self.enemy_unit.has_acted = True

        # Сбрасываем cooldown умений игрока
        self.player.skill_manager.tick_cooldowns()

        return "continue"

    def end_turn(self):
        """Завершить текущий ход"""
        if self.current_turn == "player":
            # Сбрасываем состояние игрока
            self.player_unit.reset_turn()

            # Переход к ходу врага
            self.current_turn = "enemy"
            result = self.execute_enemy_turn()

            if result == "defeat":
                return "defeat"

            # После хода врага - снова ход игрока
            self.current_turn = "player"
            self.enemy_unit.reset_turn()

        return "continue"
