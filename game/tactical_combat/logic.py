"""
Логика тактического боя
"""
import math
import json
import os
import random
from heapq import heappush, heappop
from game.systems.skills.effects import BurnEffect


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
                 respawn_manager=None, sprite_manager=None, game=None, entourage=None):
        """
        Инициализация системы тактического боя

        Args:
            player: Игрок
            enemy: Основной враг
            screen: Pygame экран
            font: Шрифт для отображения текста
            scaler: UIScaler для адаптивного масштабирования (опционально)
            game_map: Карта игры (для размещения лута)
            respawn_manager: Менеджер респавна NPC
            sprite_manager: Менеджер спрайтов
            game: Объект игры
            entourage: Список членов свиты (опционально)
        """
        self.player = player
        self.enemy = enemy  # Основной враг (для обратной совместимости)
        self.screen = screen
        self.font = font
        self.scaler = scaler
        self.game_map = game_map
        self.respawn_manager = respawn_manager
        self.sprite_manager = sprite_manager
        self.game = game

        # Список всех врагов (основной + свита)
        self.enemies = [enemy]
        if entourage:
            self.enemies.extend(entourage)

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

        # Создаем юнитов врагов с размещением на поле боя
        self.enemy_units = []
        self._spawn_enemy_units(enemy_x, spawn_y)

        # Для обратной совместимости
        self.enemy_unit = self.enemy_units[0] if self.enemy_units else None

        # Состояние боя
        self.active = True
        self.current_turn = "player"  # player или enemy
        self.selected_unit = None
        self.selected_action = None  # move, skill, potion, pass
        self.selected_target = None  # Выбранная цель (для умений)
        self.last_selected_target = None  # Последняя выбранная цель (запоминается между ходами)
        self.hovered_cell = None
        self.combat_log = []
        self.max_log_entries = 10
        self.current_enemy_index = 0  # Индекс текущего врага для хода

        # Добавляем начальное сообщение
        self.add_to_log(f"=== ТАКТИЧЕСКИЙ БОЙ НАЧАЛСЯ ===")
        self.add_to_log(f"Противник: {enemy.name} (Уровень {enemy.level})")

        if len(self.enemies) > 1:
            self.add_to_log(f"Свита: {len(self.enemies) - 1} союзников")

    def _spawn_enemy_units(self, base_x, base_y):
        """
        Разместить врагов на поле боя по правой стороне карты,
        распределяя их равномерно чтобы избежать кучкования

        Args:
            base_x: Базовая координата X для размещения
            base_y: Базовая координата Y для размещения
        """
        total_enemies = len(self.enemies)

        if total_enemies == 1:
            # Один враг - размещаем в центре правой стороны
            main_enemy_unit = BattlefieldUnit(self.enemies[0], base_x, base_y)
            self.enemy_units.append(main_enemy_unit)
        else:
            # Распределяем врагов по правой стороне карты
            # Используем несколько колонок справа (X: base_x, base_x+1, base_x-1)
            # и равномерно распределяем по высоте

            # Определяем доступные колонки (от base_x влево и вправо в пределах карты)
            available_columns = []
            for offset in [0, 1, -1, 2, -2]:
                col_x = base_x + offset
                if 0 <= col_x < self.battlefield_width:
                    available_columns.append(col_x)

            # Вычисляем равномерное распределение по Y
            height = self.battlefield_height
            # Отступы сверху и снизу для лучшего распределения
            margin = 1
            usable_height = height - 2 * margin

            # Если врагов больше чем позиций в одной колонке, используем несколько колонок
            enemies_per_column = usable_height

            # Размещаем всех врагов
            for i, enemy in enumerate(self.enemies):
                # Определяем колонку для этого врага
                column_index = i // enemies_per_column
                position_in_column = i % enemies_per_column

                # Выбираем X координату колонки
                if column_index < len(available_columns):
                    spawn_x = available_columns[column_index]
                else:
                    # Если колонок не хватает, используем последнюю доступную
                    spawn_x = available_columns[-1]

                # Вычисляем Y координату с равномерным распределением
                enemies_in_this_column = min(
                    total_enemies - column_index * enemies_per_column,
                    enemies_per_column
                )
                if enemies_in_this_column > 1:
                    step = usable_height / (enemies_in_this_column - 1) if enemies_in_this_column > 1 else 0
                    spawn_y = margin + int(position_in_column * step)
                else:
                    spawn_y = height // 2  # Центр если один враг в колонке

                # Проверяем границы
                spawn_x = max(0, min(spawn_x, self.battlefield_width - 1))
                spawn_y = max(0, min(spawn_y, self.battlefield_height - 1))

                # Проверяем, не занята ли позиция
                occupied = True
                attempts = 0
                while occupied and attempts < 20:
                    occupied = False
                    for existing_unit in self.enemy_units:
                        if existing_unit.x == spawn_x and existing_unit.y == spawn_y:
                            occupied = True
                            # Ищем ближайшую свободную позицию
                            spawn_y = (spawn_y + 1) % self.battlefield_height
                            attempts += 1
                            break

                # Создаем юнит врага
                enemy_unit = BattlefieldUnit(enemy, spawn_x, spawn_y)
                self.enemy_units.append(enemy_unit)

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
        Использует чебышевское расстояние (максимум из разниц по осям)
        для поддержки 8 направлений движения в тактическом бою

        Args:
            x1, y1: Координаты первой точки
            x2, y2: Координаты второй точки

        Returns:
            int: Расстояние (в клетках)
        """
        return max(abs(x2 - x1), abs(y2 - y1))

    def get_euclidean_distance(self, x1, y1, x2, y2):
        """
        Вычислить евклидово расстояние между двумя точками
        Используется для радиальной области действия умений

        Args:
            x1, y1: Координаты первой точки
            x2, y2: Координаты второй точки

        Returns:
            float: Евклидово расстояние
        """
        dx = x2 - x1
        dy = y2 - y1
        return (dx * dx + dy * dy) ** 0.5

    def is_in_range(self, unit, target_x, target_y, range_distance):
        """
        Проверить, находится ли цель в радиусе действия умения
        Использует евклидово расстояние для радиальной области

        Args:
            unit: Юнит
            target_x, target_y: Координаты цели
            range_distance: Радиус действия

        Returns:
            bool: True если в радиусе
        """
        distance = self.get_euclidean_distance(unit.x, unit.y, target_x, target_y)
        return distance <= range_distance

    def can_move_to(self, unit, target_x, target_y):
        """
        Проверить, может ли юнит переместиться в указанную клетку
        Перемещение возможно только в соседние 8 клеток (радиус 1)

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

        # Проверяем, не занята ли клетка игроком
        if (target_x == self.player_unit.x and target_y == self.player_unit.y):
            return False

        # Проверяем, не занята ли клетка каким-либо живым врагом
        for enemy_unit in self.enemy_units:
            if enemy_unit.character.is_alive and (target_x == enemy_unit.x and target_y == enemy_unit.y):
                return False

        # Проверяем, что перемещение только в соседние 8 клеток (радиус 1)
        dx = abs(target_x - unit.x)
        dy = abs(target_y - unit.y)

        # Допускаем перемещение только на 1 клетку по любому направлению
        return dx <= 1 and dy <= 1 and (dx != 0 or dy != 0)

    def is_cell_blocked(self, x, y, ignore_unit=None):
        """
        Проверить, занята ли клетка препятствием или юнитом

        Args:
            x, y: Координаты клетки
            ignore_unit: Юнит, который нужно игнорировать (например, тот кто ищет путь)

        Returns:
            bool: True если клетка заблокирована
        """
        # Проверяем границы поля
        if x < 0 or x >= self.battlefield_width:
            return True
        if y < 0 or y >= self.battlefield_height:
            return True

        # Проверяем, не занята ли клетка игроком
        if self.player_unit != ignore_unit and (x == self.player_unit.x and y == self.player_unit.y):
            return True

        # Проверяем, не занята ли клетка каким-либо живым врагом
        for enemy_unit in self.enemy_units:
            if (enemy_unit != ignore_unit and
                enemy_unit.character.is_alive and
                x == enemy_unit.x and y == enemy_unit.y):
                return True

        return False

    def find_path(self, start_x, start_y, goal_x, goal_y, unit):
        """
        Найти путь от начальной позиции до цели используя A*
        Поддерживает движение по 8 направлениям

        Args:
            start_x, start_y: Начальная позиция
            goal_x, goal_y: Целевая позиция
            unit: Юнит, который ищет путь

        Returns:
            list: Список координат (x, y) пути от начала до цели, или None если путь не найден
        """
        # Если цель заблокирована, ищем ближайшую свободную клетку рядом с целью
        if self.is_cell_blocked(goal_x, goal_y, ignore_unit=unit):
            # Ищем ближайшую свободную клетку вокруг цели
            best_alternative = None
            best_distance = float('inf')

            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue

                    alt_x = goal_x + dx
                    alt_y = goal_y + dy

                    if not self.is_cell_blocked(alt_x, alt_y, ignore_unit=unit):
                        distance = self.get_distance(start_x, start_y, alt_x, alt_y)
                        if distance < best_distance:
                            best_distance = distance
                            best_alternative = (alt_x, alt_y)

            if best_alternative:
                goal_x, goal_y = best_alternative
            else:
                return None  # Нет доступных клеток рядом с целью

        # A* алгоритм
        def heuristic(x, y):
            # Используем чебышевское расстояние (максимум из разниц по осям)
            # Это подходит для движения по 8 направлениям
            return max(abs(x - goal_x), abs(y - goal_y))

        # Приоритетная очередь: (приоритет, координаты)
        open_set = []
        heappush(open_set, (0, (start_x, start_y)))

        # Словарь для хранения пути
        came_from = {}

        # Стоимость пути от начала до каждой клетки
        g_score = {(start_x, start_y): 0}

        # Оценочная стоимость от начала до цели через эту клетку
        f_score = {(start_x, start_y): heuristic(start_x, start_y)}

        while open_set:
            current_f, current = heappop(open_set)
            current_x, current_y = current

            # Достигли цели
            if current_x == goal_x and current_y == goal_y:
                # Восстанавливаем путь
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            # Проверяем всех соседей (8 направлений)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue

                    neighbor_x = current_x + dx
                    neighbor_y = current_y + dy
                    neighbor = (neighbor_x, neighbor_y)

                    # Пропускаем заблокированные клетки
                    if self.is_cell_blocked(neighbor_x, neighbor_y, ignore_unit=unit):
                        continue

                    # Стоимость диагонального движения немного выше
                    move_cost = 1.414 if (dx != 0 and dy != 0) else 1.0
                    tentative_g_score = g_score[current] + move_cost

                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + heuristic(neighbor_x, neighbor_y)
                        heappush(open_set, (f_score[neighbor], neighbor))

        # Путь не найден
        return None

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

            # Перемещение не логируется для улучшения читаемости лога боя
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
        targets = []

        # Определяем возможные цели в зависимости от типа умения
        from game.skills import SkillCategory

        # Получаем ID умения для определения типа
        skill_id = caster_unit.character.skill_manager.get_skill_id(skill)

        # Лечебные/поддерживающие умения - применяются на себя
        support_skills = ['heal', 'regeneration', 'stamina_recovery', 'mage_shield']
        if skill_id in support_skills:
            targets.append(caster_unit)
        else:
            # Боевые умения - применяются на врагов
            # Получаем радиус действия умения (используем метод get_tactical_range если доступен)
            if hasattr(skill, 'get_tactical_range'):
                skill_range = skill.get_tactical_range()
            else:
                skill_range = getattr(skill, 'tactical_range', 1)

            if caster_unit == self.player_unit:
                # Игрок может атаковать любого врага в радиусе действия
                for enemy_unit in self.enemy_units:
                    if enemy_unit.character.is_alive:
                        if self.is_in_range(caster_unit, enemy_unit.x, enemy_unit.y, skill_range):
                            targets.append(enemy_unit)
            else:
                # Враги атакуют только игрока
                if self.is_in_range(caster_unit, self.player_unit.x, self.player_unit.y, skill_range):
                    targets.append(self.player_unit)

        return targets

    def get_adjacent_units(self, target_unit, exclude_caster=None):
        """
        Получить всех живых юнитов в радиусе 1 клетки от цели (8 соседних клеток)

        Args:
            target_unit: Целевой юнит, вокруг которого ищем соседей
            exclude_caster: Юнит заклинателя, которого нужно исключить

        Returns:
            list: Список юнитов в соседних клетках
        """
        adjacent_units = []
        target_x, target_y = target_unit.x, target_unit.y

        # Проверяем все 8 соседних клеток
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Пропускаем саму цель

                check_x = target_x + dx
                check_y = target_y + dy

                # Проверяем игрока
                if (self.player_unit != exclude_caster and
                    self.player_unit != target_unit and
                    self.player_unit.x == check_x and
                    self.player_unit.y == check_y and
                    self.player.is_alive):
                    adjacent_units.append(self.player_unit)

                # Проверяем врагов
                for enemy_unit in self.enemy_units:
                    if (enemy_unit != exclude_caster and
                        enemy_unit != target_unit and
                        enemy_unit.x == check_x and
                        enemy_unit.y == check_y and
                        enemy_unit.character.is_alive):
                        adjacent_units.append(enemy_unit)

        return adjacent_units

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

            # === УНИВЕРСАЛЬНАЯ ОБРАБОТКА РАСПРОСТРАНЕНИЯ DoT ЭФФЕКТОВ НА СОСЕДЕЙ ===
            # Поддерживаем как новый универсальный формат 'effect_spread', так и старый 'burn_spread' для совместимости
            spread_config = result.get('effect_spread') or result.get('burn_spread')

            if spread_config:
                spread_chance = spread_config['chance']
                duration_min, duration_max = spread_config['duration_range']
                effect_type = spread_config.get('effect_type', 'burn')  # По умолчанию горение для совместимости

                # Получаем всех живых юнитов в соседних клетках
                adjacent_units = self.get_adjacent_units(target_unit, exclude_caster=caster_unit)

                # Проверяем шанс распространения для каждого соседа
                for adjacent_unit in adjacent_units:
                    if random.random() < spread_chance:
                        # Эффект перекинулся на соседа!
                        effect_duration = random.randint(duration_min, duration_max)

                        # Создаем соответствующий эффект в зависимости от типа
                        if effect_type == 'burn':
                            damage_per_turn = spread_config['damage_per_turn']
                            spread_effect = BurnEffect(duration=effect_duration, damage_per_turn=damage_per_turn)
                            spread_message = f"Огонь перекинулся на {adjacent_unit.character.name}! ({damage_per_turn} урона/ход на {effect_duration} ход(а))"
                        elif effect_type == 'poison':
                            from game.systems.skills.effects import PoisonEffect
                            damage_per_turn = spread_config['damage_per_turn']
                            spread_effect = PoisonEffect(duration=effect_duration, damage_per_turn=damage_per_turn)
                            spread_message = f"Яд перекинулся на {adjacent_unit.character.name}! ({damage_per_turn} урона/ход на {effect_duration} ход(а))"
                        else:
                            # Для других типов эффектов можно добавить обработку
                            continue

                        # Добавляем эффект
                        adjacent_char = adjacent_unit.character
                        if hasattr(adjacent_char, 'skill_manager') and adjacent_char.skill_manager:
                            adjacent_char.skill_manager.status_effects.append(spread_effect)
                        else:
                            if not hasattr(adjacent_char, 'status_effects'):
                                adjacent_char.status_effects = []
                            adjacent_char.status_effects.append(spread_effect)

                        self.add_to_log(spread_message)

            # Проверяем, не убит ли противник
            if 'killed' in result and result['killed']:
                # Проверяем, все ли враги мертвы
                if self._all_enemies_dead():
                    return {'status': 'victory', 'message': result['message']}

        return {'status': 'continue', 'message': result.get('message', '')}

    def _all_enemies_dead(self):
        """
        Проверить, все ли враги мертвы

        Returns:
            bool: True если все враги мертвы
        """
        for enemy_unit in self.enemy_units:
            if enemy_unit.character.is_alive:
                return False
        return True

    def execute_enemy_turn(self):
        """
        Выполнить ход врагов (AI) - все живые враги ходят по очереди

        Returns:
            str: Статус боя после хода
        """
        import random
        from game.skills import SkillCategory

        # Все живые враги ходят по очереди
        for enemy_unit in self.enemy_units:
            # Пропускаем мертвых врагов
            if not enemy_unit.character.is_alive:
                continue

            # Выполняем ход этого врага
            result = self._execute_single_enemy_turn(enemy_unit)

            if result == "defeat":
                return "defeat"

        # Сбрасываем cooldown умений игрока после хода всех врагов
        self.player.skill_manager.tick_cooldowns()

        return "continue"

    def _execute_single_enemy_turn(self, enemy_unit):
        """
        Выполнить ход одного врага

        Args:
            enemy_unit: Вражеский юнит

        Returns:
            str: Статус боя после хода
        """
        import random
        from game.skills import SkillCategory

        distance = self.get_distance(enemy_unit.x, enemy_unit.y,
                                     self.player_unit.x, self.player_unit.y)

        weapon_range = enemy_unit.get_weapon_range()

        # Пытаемся использовать умения, если они есть
        used_skill = False
        if hasattr(enemy_unit.character, 'skill_manager') and enemy_unit.character.skill_manager:
            # Получаем список боевых умений
            combat_categories = [SkillCategory.COMBAT, SkillCategory.MAGIC,
                               SkillCategory.SHADOW, SkillCategory.WARRIOR,
                               SkillCategory.HUNTER, SkillCategory.MAGE]

            usable_skills = []
            for skill in enemy_unit.character.skill_manager.learned_skills.values():
                # Проверяем, что умение боевое и готово к использованию
                if (skill.category in combat_categories and
                    enemy_unit.character.skill_manager.can_use_skill(skill)):

                    # Проверяем, что цель в радиусе действия
                    targets = self.get_skill_targets(skill, enemy_unit)
                    if self.player_unit in targets:
                        usable_skills.append(skill)

            # Если есть доступные умения - используем случайное
            if usable_skills:
                skill = random.choice(usable_skills)
                result = self.use_skill(skill, enemy_unit, self.player_unit)

                if result['status'] == 'continue':
                    used_skill = True

                    if not self.player.is_alive:
                        return "defeat"

        # Если умение не использовали - используем базовую атаку или двигаемся
        if not used_skill:
            # Если враг вне дистанции атаки - приближаемся (на 1 клетку за ход)
            if distance > weapon_range:
                # Используем pathfinding для поиска пути к игроку
                path = self.find_path(
                    enemy_unit.x, enemy_unit.y,
                    self.player_unit.x, self.player_unit.y,
                    enemy_unit
                )

                if path and len(path) > 0:
                    # Берем первый шаг из найденного пути
                    next_x, next_y = path[0]
                    self.move_unit(enemy_unit, next_x, next_y)
                else:
                    # Если путь не найден, пытаемся двигаться напрямую (старая логика)
                    dx = self.player_unit.x - enemy_unit.x
                    dy = self.player_unit.y - enemy_unit.y

                    # Нормализуем направление для движения по одной клетке
                    # Движение по диагонали, если оба dx и dy ненулевые
                    move_x = 1 if dx > 0 else -1 if dx < 0 else 0
                    move_y = 1 if dy > 0 else -1 if dy < 0 else 0

                    new_x = enemy_unit.x + move_x
                    new_y = enemy_unit.y + move_y

                    # Пытаемся двигаться
                    if not self.move_unit(enemy_unit, new_x, new_y):
                        # Если не получилось, пробуем двигаться только по одной оси
                        if abs(dx) > abs(dy):
                            new_x = enemy_unit.x + move_x
                            new_y = enemy_unit.y
                        else:
                            new_x = enemy_unit.x
                            new_y = enemy_unit.y + move_y
                        self.move_unit(enemy_unit, new_x, new_y)
            else:
                # В дистанции атаки - атакуем базовой атакой
                attack_result = enemy_unit.character.attack(self.player)

                if attack_result['dodged']:
                    self.add_to_log(f"Вы уклонились от атаки {enemy_unit.character.name}!")
                elif attack_result['hit']:
                    damage = attack_result['damage']
                    if attack_result['critical']:
                        self.add_to_log(f"КРИТИЧЕСКИЙ УДАР! {enemy_unit.character.name} наносит вам мощнейший удар! Урон: {damage}")
                    else:
                        self.add_to_log(f"{enemy_unit.character.name} атакует вас! Урон: {damage}")

                    if not self.player.is_alive:
                        return "defeat"

                enemy_unit.has_acted = True

        return "continue"

    def end_turn(self):
        """Завершить текущий ход"""
        if self.current_turn == "player":
            # Сбрасываем состояние игрока
            self.player_unit.reset_turn()

            # Переход к ходу врагов
            self.current_turn = "enemy"
            result = self.execute_enemy_turn()

            if result == "defeat":
                return "defeat"

            # После хода врагов - снова ход игрока
            self.current_turn = "player"

            # Сбрасываем состояние всех вражеских юнитов
            for enemy_unit in self.enemy_units:
                enemy_unit.reset_turn()

            # === ОБРАБОТКА СТАТУС-ЭФФЕКТОВ (DoT) ДЛЯ ВСЕХ ЮНИТОВ ===
            self._process_all_status_effects()

            # Проверяем победу после DoT урона
            if self._all_enemies_dead():
                return "victory"

            # Проверяем поражение после DoT урона
            if not self.player.is_alive:
                return "defeat"

            # Проверяем, жива ли последняя выбранная цель
            if self.last_selected_target and not self.last_selected_target.character.is_alive:
                self.last_selected_target = None

        return "continue"

    def _process_all_status_effects(self):
        """
        Обработать статус-эффекты (DoT, регенерация и т.д.) для всех юнитов.
        Вызывается в конце каждого раунда.
        """
        # Обрабатываем эффекты игрока
        if hasattr(self.player, 'skill_manager') and self.player.skill_manager:
            messages = self.player.skill_manager.tick_status_effects()
            for msg in messages:
                self.add_to_log(msg)

        # Обрабатываем эффекты всех врагов
        for enemy_unit in self.enemy_units:
            if not enemy_unit.character.is_alive:
                continue

            enemy = enemy_unit.character

            # Если у врага есть skill_manager - используем его
            if hasattr(enemy, 'skill_manager') and enemy.skill_manager:
                messages = enemy.skill_manager.tick_status_effects()
                for msg in messages:
                    self.add_to_log(msg)
            # Иначе обрабатываем status_effects напрямую
            elif hasattr(enemy, 'status_effects') and enemy.status_effects:
                for effect in enemy.status_effects[:]:
                    message = effect.tick(enemy)
                    if message:
                        self.add_to_log(message)

                    # Удаляем истекшие эффекты
                    if effect.is_expired():
                        remove_message = effect.remove(enemy)
                        if remove_message:
                            self.add_to_log(remove_message)
                        enemy.status_effects.remove(effect)

                # Проверяем, жив ли враг после DoT
                if not enemy.is_alive:
                    self.add_to_log(f"{enemy.name} повержен от горения!")
