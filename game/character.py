"""
Классы персонажей (игрок и NPC)
"""
import random
from collections import deque
from game.inventory import Inventory
from game.constants import (
    MAX_LEVEL, RANKS, RELATIONSHIP_NEUTRAL, RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY,
    NPC_RELATIONSHIPS, NPC_TYPE_GUARD, NPC_TYPE_MERCHANT, NPC_TYPE_BANDIT,
    NPC_TYPE_MINER, NPC_TYPE_UNDEAD,
    STAMINA_PER_STAT_POINT, STAMINA_COST_PER_MOVE, STAMINA_REST_MIN, STAMINA_REST_MAX,
    COMBAT_RANGE, BANDIT_CAMP_RADIUS, DODGE_BASE_CHANCE, CRIT_BASE_CHANCE
)


class Character:
    """Базовый класс для всех персонажей (игрок и NPC)"""

    def __init__(self, name, x=0, y=0):
        """
        Инициализация персонажа

        Args:
            name: Имя персонажа
            x: Начальная позиция X
            y: Начальная позиция Y
        """
        self.name = name
        self.x = x
        self.y = y

        # Характеристики
        self.strength = 0      # Сила
        self.dexterity = 0     # Ловкость
        self.constitution = 0  # Телосложение
        self.spirit = 0        # Дух
        self.intelligence = 0  # Интеллект
        self.luck = 0          # Удача

        # Система выносливости
        self.max_stamina = 0
        self.stamina = 0
        self.is_resting = False
        self.rest_threshold = 0  # Порог для окончания отдыха (случайный от 60% до 80%)

        # Боевая система
        self.max_health = 0
        self.health = 0
        self.is_alive = True

    def generate_random_stats(self, min_val=5, max_val=15):
        """
        Генерация случайных характеристик

        Args:
            min_val: Минимальное значение характеристики
            max_val: Максимальное значение характеристики
        """
        self.strength = random.randint(min_val, max_val)
        self.dexterity = random.randint(min_val, max_val)
        self.constitution = random.randint(min_val, max_val)
        self.spirit = random.randint(min_val, max_val)
        self.intelligence = random.randint(min_val, max_val)
        self.luck = random.randint(min_val, max_val)

        # Обновляем выносливость и здоровье на основе характеристик
        self.update_derived_stats()

    def update_derived_stats(self):
        """Обновить производные характеристики (выносливость, здоровье)"""
        # Выносливость = (сила + телосложение) * 10
        self.max_stamina = (self.strength + self.constitution) * STAMINA_PER_STAT_POINT
        self.stamina = self.max_stamina

        # Устанавливаем порог отдыха (60-80% от максимальной выносливости)
        rest_percent = random.uniform(STAMINA_REST_MIN, STAMINA_REST_MAX)
        self.rest_threshold = int(self.max_stamina * rest_percent)

        # Здоровье = телосложение * 20
        old_max_health = self.max_health
        self.max_health = self.constitution * 20

        # Если здоровье увеличилось, добавляем разницу к текущему здоровью
        if old_max_health > 0:
            health_diff = self.max_health - old_max_health
            self.health = min(self.max_health, self.health + health_diff)
        else:
            self.health = self.max_health

    def consume_stamina(self, amount=STAMINA_COST_PER_MOVE):
        """
        Потратить выносливость

        Args:
            amount: Количество выносливости

        Returns:
            bool: True если удалось потратить
        """
        if self.stamina >= amount:
            self.stamina -= amount

            # Если выносливость закончилась, начинаем отдых
            if self.stamina <= 0:
                self.stamina = 0
                self.is_resting = True

            return True
        return False

    def recover_stamina(self, is_active_rest=False):
        """
        Восстановить выносливость (вызывается каждый игровой час)

        Args:
            is_active_rest: True если это активный отдых (команда R)
        """
        if self.stamina < self.max_stamina:
            # При активном отдыхе или принудительном отдыхе восстанавливаем больше
            if is_active_rest or self.is_resting:
                recovery = (self.strength + self.constitution) * 2
            else:
                # При обычном движении восстанавливаем только 25% от нормы
                recovery = max(1, (self.strength + self.constitution) // 4)

            self.stamina = min(self.max_stamina, self.stamina + recovery)

            # Проверяем, достаточно ли восстановились для окончания отдыха
            if self.is_resting and self.stamina >= self.rest_threshold:
                self.is_resting = False

    def take_damage(self, damage):
        """
        Получить урон

        Args:
            damage: Количество урона

        Returns:
            bool: True если персонаж жив
        """
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
        return self.is_alive

    def can_attack(self, target):
        """
        Проверить, может ли персонаж атаковать цель

        Args:
            target: Целевой персонаж

        Returns:
            bool: True если может атаковать
        """
        if not self.is_alive or not target.is_alive:
            return False

        # Проверяем дистанцию
        distance = abs(self.x - target.x) + abs(self.y - target.y)
        return distance <= COMBAT_RANGE

    def calculate_dodge_chance(self):
        """
        Рассчитать шанс уворота на основе ловкости

        Returns:
            float: Шанс уворота (0-100)
        """
        return self.dexterity * DODGE_BASE_CHANCE

    def calculate_crit_chance(self):
        """
        Рассчитать шанс критического удара на основе удачи

        Returns:
            float: Шанс крита (0-100)
        """
        return self.luck * CRIT_BASE_CHANCE

    def attack(self, target):
        """
        Атаковать цель с учетом механики уворота и крита

        Args:
            target: Целевой персонаж

        Returns:
            dict: Результат атаки с информацией об уроне, увороте и крите
        """
        if not self.can_attack(target):
            return {
                'damage': 0,
                'dodged': False,
                'critical': False,
                'hit': False
            }

        # Проверка уворота
        dodge_chance = target.calculate_dodge_chance()
        dodge_roll = random.uniform(0, 100)

        if dodge_roll < dodge_chance:
            # Цель увернулась
            return {
                'damage': 0,
                'dodged': True,
                'critical': False,
                'hit': False
            }

        # Проверка критического удара
        crit_chance = self.calculate_crit_chance()
        crit_roll = random.uniform(0, 100)
        is_critical = crit_roll < crit_chance

        # Расчет урона с учетом оружия
        base_damage = self.get_total_damage()
        bonus_damage = random.randint(0, self.dexterity // 2)
        total_damage = base_damage + bonus_damage

        # Удваиваем урон при крите
        if is_critical:
            total_damage *= 2

        # Учитываем защиту цели
        target_defense = target.get_total_defense()
        # Защита снижает урон, но не может снизить его до нуля (минимум 1)
        actual_damage = max(1, total_damage - target_defense)

        # Применяем урон
        target.take_damage(actual_damage)

        return {
            'damage': actual_damage,
            'dodged': False,
            'critical': is_critical,
            'hit': True
        }

    def get_base_stats(self):
        """Получить базовые характеристики без учета экипировки"""
        return {
            'strength': self.strength,
            'dexterity': self.dexterity,
            'constitution': self.constitution,
            'spirit': self.spirit,
            'intelligence': self.intelligence,
            'luck': self.luck
        }

    def get_stats(self):
        """Получить все характеристики с учетом экипировки (для Player)"""
        base_stats = self.get_base_stats()

        # Если есть инвентарь с экипировкой, добавляем бонусы
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_total_stats_bonus'):
            equipment_bonus = self.inventory.get_total_stats_bonus()

            for stat, bonus in equipment_bonus.items():
                if stat in base_stats:
                    base_stats[stat] += bonus

        return base_stats

    def get_total_damage(self):
        """Получить общий урон с учетом оружия и временных бонусов"""
        base_damage = self.strength

        # Добавляем временный бонус к силе
        if hasattr(self, 'temp_strength_boost'):
            base_damage += self.temp_strength_boost

        # Если есть экипированное оружие
        if hasattr(self, 'inventory'):
            from game.inventory import EquipmentSlot, WeaponItem
            weapon = self.inventory.get_equipped_item(EquipmentSlot.WEAPON)
            if weapon and isinstance(weapon, WeaponItem):
                return weapon.damage + base_damage

        return base_damage

    def get_total_defense(self):
        """Получить общую защиту с учетом доспехов"""
        total_defense = 0

        # Если есть экипированные доспехи
        if hasattr(self, 'inventory'):
            from game.inventory import ArmorItem
            for item in self.inventory.equipment.values():
                if item and isinstance(item, ArmorItem):
                    total_defense += item.defense

        return total_defense

    def move(self, dx, dy):
        """
        Переместить персонажа

        Args:
            dx: Смещение по X
            dy: Смещение по Y
        """
        self.x += dx
        self.y += dy

    def get_rank(self):
        """
        Получить ранг персонажа на основе уровня

        Returns:
            str: Название ранга
        """
        level = getattr(self, 'level', 1)
        for (min_level, max_level), rank_name in RANKS.items():
            if min_level <= level <= max_level:
                return rank_name
        return "Новичок"


class Player(Character):
    """Класс игрока"""

    def __init__(self, name="Hero", x=0, y=0):
        """
        Инициализация игрока

        Args:
            name: Имя игрока
            x: Начальная позиция X
            y: Начальная позиция Y
        """
        super().__init__(name, x, y)

        # Устанавливаем базовые характеристики игрока
        self.strength = 1
        self.dexterity = 1
        self.constitution = 1
        self.spirit = 1
        self.intelligence = 1
        self.luck = 1

        # Дополнительные параметры игрока
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100  # Опыт для следующего уровня
        self.stat_points = 0  # Нераспределенные очки характеристик

        # Параметр маг (по умолчанию - нет)
        self.is_mage = False

        # Мана зависит от духа (1 дух = 10 маны)
        self.max_mana = self.spirit * 10
        self.mana = self.max_mana

        # Обновляем производные характеристики (здоровье, выносливость)
        self.update_derived_stats()

        # Инвентарь
        self.inventory = Inventory(max_slots=20)
        # Обновляем грузоподъемность на основе силы
        self.inventory.update_max_weight(self.strength)

        # Менеджер навыков
        from game.skills import SkillManager
        self.skill_manager = SkillManager(self)

        # Менеджер профессий
        from game.professions import ProfessionManager
        self.profession_manager = ProfessionManager()

        # Атрибуты для достижений
        self.enemies_killed = 0
        self.visited_location_types = set()
        self.items_sold = 0
        self.resources_collected = 0

        # Флаг оглушения
        self.stunned = False

        # Временный бонус к силе (от навыков)
        self.temp_strength_boost = 0

        # Флаг атаки от NPC (для принудительного открытия окна боя)
        self.attacked_by_npc = None

    def can_move_to(self, x, y, game_map):
        """
        Проверить, может ли игрок переместиться на данную клетку

        Args:
            x: Целевая позиция X
            y: Целевая позиция Y
            game_map: Объект карты игры

        Returns:
            bool: True если можно переместиться
        """
        # Проверка границ карты
        if x < 0 or x >= game_map.width or y < 0 or y >= game_map.height:
            return False

        # Проверка проходимости тайла
        tile = game_map.get_tile(x, y)
        return tile.is_passable()

    def move_to(self, x, y, game_map):
        """
        Переместить игрока на указанную позицию с проверкой

        Args:
            x: Целевая позиция X
            y: Целевая позиция Y
            game_map: Объект карты игры

        Returns:
            bool: True если перемещение успешно
        """
        if self.can_move_to(x, y, game_map):
            self.x = x
            self.y = y
            return True
        return False

    def add_experience(self, amount):
        """
        Добавить опыт игроку

        Args:
            amount: Количество опыта

        Returns:
            bool: True если произошло повышение уровня
        """
        self.experience += amount
        leveled_up = False

        # Проверяем, достаточно ли опыта для повышения уровня
        while self.experience >= self.experience_to_next_level:
            leveled_up = True
            self.level_up()

        return leveled_up

    def level_up(self):
        """Повысить уровень игрока"""
        # Проверяем, не достигнут ли максимальный уровень
        if self.level >= MAX_LEVEL:
            print(f"Вы достигли максимального уровня {MAX_LEVEL}!")
            self.experience = 0
            return

        self.experience -= self.experience_to_next_level
        self.level += 1

        # Увеличиваем требуемый опыт для следующего уровня
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)

        # Даем игроку 3 очка характеристик для распределения
        self.stat_points += 3

        # Обновляем производные характеристики
        self.update_derived_stats()

        # Обновляем максимальную ману
        self.max_mana = self.spirit * 10
        self.mana = self.max_mana

        # Получаем ранг
        rank = self.get_rank()
        print(f"Поздравляем! Вы достигли {self.level} уровня! Ранг: {rank}")
        print(f"Вы получили 3 очка характеристик! Нажмите C для их распределения.")

    def add_stat_point(self, stat_name):
        """
        Распределить очко характеристики

        Args:
            stat_name: Название характеристики

        Returns:
            bool: True если удалось распределить
        """
        if self.stat_points <= 0:
            return False

        stat_map = {
            'strength': 'strength',
            'dexterity': 'dexterity',
            'constitution': 'constitution',
            'spirit': 'spirit',
            'intelligence': 'intelligence',
            'luck': 'luck'
        }

        if stat_name in stat_map:
            setattr(self, stat_map[stat_name], getattr(self, stat_map[stat_name]) + 1)
            self.stat_points -= 1

            # Обновляем производные характеристики
            self.update_derived_stats()

            # Обновляем максимальную ману если изменился дух
            if stat_name == 'spirit':
                self.max_mana = self.spirit * 10
                self.mana = self.max_mana

            # Обновляем грузоподъемность если изменилась сила
            if stat_name == 'strength':
                self.inventory.update_max_weight(self.strength)

            return True

        return False

    def rest(self):
        """
        Отдых - восстанавливает здоровье, ману и выносливость
        Занимает 1 час игрового времени
        """
        # Восстанавливаем 30% от максимального здоровья
        health_restored = int(self.max_health * 0.3)
        self.health = min(self.max_health, self.health + health_restored)

        # Восстанавливаем 50% от максимальной маны
        mana_restored = int(self.max_mana * 0.5)
        self.mana = min(self.max_mana, self.mana + mana_restored)

        # Восстанавливаем выносливость (используя активный отдых)
        old_stamina = self.stamina
        self.recover_stamina(is_active_rest=True)
        stamina_restored = self.stamina - old_stamina

        print(f"Здоровье восстановлено: +{health_restored} ({self.health}/{self.max_health})")
        print(f"Мана восстановлена: +{mana_restored} ({self.mana}/{self.max_mana})")
        print(f"Выносливость восстановлена: +{stamina_restored} ({self.stamina}/{self.max_stamina})")

    def work(self, game_map=None):
        """
        Работа - сбор ресурсов с использованием профессий или получение золота
        Занимает 1 час игрового времени

        Args:
            game_map: Карта игры (для определения биома и локации)
        """
        if not game_map:
            # Простая работа за золото
            gold_gained = 5 + self.level
            self.inventory.add_gold(gold_gained)
            print(f"Вы поработали и получили {gold_gained} золота")
            return

        # Получаем текущий тайл
        tile = game_map.get_tile(self.x, self.y)
        biome = tile.biome
        location = tile.location if tile.has_location() else None

        # Попытка использовать профессии
        resources_gathered = False

        # Проверяем рудокопство
        mining = self.profession_manager.get_profession('mining')
        can_mine, mine_msg = mining.can_use(self, location)
        if can_mine:
            resources = mining.gather(self)
            if resources:
                for item, quantity in resources:
                    if self.inventory.add_item(item, quantity):
                        print(f"Добыто: {item.name} x{quantity}")
                        self.resources_collected += 1
                    else:
                        print(f"Инвентарь полон! Не удалось добавить {item.name}")
                resources_gathered = True
            else:
                print("Вам не удалось ничего добыть в этот раз.")
                resources_gathered = True

        # Проверяем лесорубство
        lumberjacking = self.profession_manager.get_profession('lumberjacking')
        can_lumber, lumber_msg = lumberjacking.can_use(self, biome)
        if can_lumber and not resources_gathered:
            resources = lumberjacking.gather(self)
            if resources:
                for item, quantity in resources:
                    if self.inventory.add_item(item, quantity):
                        print(f"Срублено: {item.name} x{quantity}")
                        self.resources_collected += 1
                    else:
                        print(f"Инвентарь полон! Не удалось добавить {item.name}")
                resources_gathered = True
            else:
                print("Вам не удалось ничего добыть в этот раз.")
                resources_gathered = True

        # Если не удалось использовать профессии, работаем за золото
        if not resources_gathered:
            gold_gained = 5 + self.level
            self.inventory.add_gold(gold_gained)
            print(f"Вы поработали и получили {gold_gained} золота")

    def use_item(self, item_name):
        """
        Использовать предмет из инвентаря

        Args:
            item_name: Название предмета

        Returns:
            str: Сообщение о результате
        """
        item_data = self.inventory.get_item(item_name)
        if not item_data:
            return "Предмет не найден в инвентаре"

        item, quantity = item_data

        # Проверяем тип предмета
        if item.item_type == "potion":
            # Используем зелье
            result = item.use(self)
            self.inventory.remove_item(item_name, 1)
            return result
        else:
            return "Этот предмет нельзя использовать"


class NPC(Character):
    """Класс NPC (неигровых персонажей)"""

    def __init__(self, name, x=0, y=0, npc_type="neutral", level=1):
        """
        Инициализация NPC

        Args:
            name: Имя NPC
            x: Позиция X
            y: Позиция Y
            npc_type: Тип NPC (neutral, enemy, friendly)
            level: Уровень NPC
        """
        super().__init__(name, x, y)
        self.npc_type = npc_type
        self.level = level
        self.relationship = RELATIONSHIP_NEUTRAL  # Отношение к игроку по умолчанию
        self.generate_random_stats()

        # Инвентарь для NPC
        self.inventory = Inventory(max_slots=10, max_weight=50.0)

        # Генерируем и экипируем начальную экипировку
        self._generate_initial_equipment()

    def _generate_initial_equipment(self):
        """Генерация и автоматическая экипировка начального снаряжения"""
        from game.inventory import ItemGenerator

        equipment_items = ItemGenerator.generate_npc_equipment(self.npc_type, self.level)

        for item in equipment_items:
            # Добавляем в инвентарь
            if self.inventory.add_item(item, 1):
                # Пытаемся сразу экипировать
                self.inventory.equip_item(item.name)

    def _find_next_step(self, target_x, target_y, game_map, max_search_distance=50):
        """
        Найти следующий шаг к цели используя BFS (поиск в ширину)

        Args:
            target_x: Целевая X координата
            target_y: Целевая Y координата
            game_map: Объект карты игры
            max_search_distance: Максимальная дистанция поиска в клетках

        Returns:
            tuple: (dx, dy) - направление следующего шага, или (0, 0) если путь не найден
        """
        # Если уже на месте
        if self.x == target_x and self.y == target_y:
            return (0, 0)

        # BFS для поиска кратчайшего пути
        queue = deque([(self.x, self.y, None)])  # (x, y, first_step)
        visited = {(self.x, self.y)}

        # 8 направлений движения
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        while queue:
            x, y, first_step = queue.popleft()

            # Проверяем все 8 направлений
            for dx, dy in directions:
                nx, ny = x + dx, y + dy

                # Достигли цели
                if nx == target_x and ny == target_y:
                    # Возвращаем первый шаг из найденного пути
                    if first_step:
                        return first_step
                    else:
                        return (dx, dy)

                # Проверяем валидность и проходимость
                if (nx, ny) not in visited:
                    if game_map.is_valid_position(nx, ny):
                        tile = game_map.get_tile(nx, ny)
                        if tile.is_passable():
                            # Ограничиваем дистанцию поиска
                            distance = abs(nx - self.x) + abs(ny - self.y)
                            if distance <= max_search_distance:
                                visited.add((nx, ny))
                                # Сохраняем первый шаг (если это первый шаг из начальной позиции)
                                next_first_step = first_step if first_step else (dx, dy)
                                queue.append((nx, ny, next_first_step))

        # Путь не найден - возвращаем (0, 0)
        return (0, 0)

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли NPC двигаться на клетку (базовый метод)

        Args:
            x: Координата X
            y: Координата Y
            game_map: Объект карты

        Returns:
            bool: True если можно двигаться
        """
        if not game_map.is_valid_position(x, y):
            return False

        tile = game_map.get_tile(x, y)
        return tile.is_passable()


class Guard(NPC):
    """Класс Стражника с AI патрулирования и боевым поведением"""

    def __init__(self, name, x=0, y=0, level=5):
        """
        Инициализация Стражника

        Args:
            name: Имя стражника
            x: Позиция X
            y: Позиция Y
            level: Уровень стражника
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_GUARD, level=level)

        # AI параметры
        self.state = "patrol"  # patrol, rest, combat
        self.patrol_points = []  # Точки патрулирования
        self.current_patrol_index = 0
        self.rest_counter = 0
        self.rest_duration = 3  # Длительность отдыха в часах
        self.patrol_home_x = x  # Домашняя точка патруля
        self.patrol_home_y = y
        self.steps_per_hour = 1  # Количество шагов за 1 час игрового времени (только соседние клетки)
        self.target_enemy = None  # Текущий враг для атаки
        self.detection_range = 10  # Дальность обнаружения врагов

    def set_patrol_route(self, points):
        """
        Установить маршрут патрулирования

        Args:
            points: Список точек (x, y) для патрулирования
        """
        self.patrol_points = points
        self.current_patrol_index = 0

    def update_ai(self, game_map, all_npcs=None):
        """
        Обновление AI стражника за 1 час игрового времени
        Стражник делает несколько шагов за час

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для поиска врагов
        """
        if not self.is_alive:
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие врагов поблизости
        if all_npcs:
            self._check_for_enemies(all_npcs)

        if self.state == "combat":
            self._combat_step(game_map)
        elif self.state == "patrol":
            # Делаем несколько шагов за 1 час
            for _ in range(self.steps_per_hour):
                if not self.consume_stamina():
                    break
                self._patrol_step(game_map)
                if self.state == "rest":
                    break
        elif self.state == "rest":
            self._rest()

    def _check_for_enemies(self, all_npcs):
        """
        Проверить наличие врагов поблизости

        Args:
            all_npcs: Список всех NPC
        """
        # Ищем ближайшего живого врага
        closest_enemy = None
        closest_distance = float('inf')

        for npc in all_npcs:
            if not npc.is_alive:
                continue

            # Проверяем отношение к этому NPC
            relationship = NPC_RELATIONSHIPS.get((self.npc_type, npc.npc_type), RELATIONSHIP_NEUTRAL)

            if relationship == RELATIONSHIP_HOSTILE:
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                # Если враг в зоне обнаружения
                if distance <= self.detection_range and distance < closest_distance:
                    closest_enemy = npc
                    closest_distance = distance

        # Если нашли врага, переходим в боевой режим
        if closest_enemy:
            self.target_enemy = closest_enemy
            self.state = "combat"
        elif self.state == "combat":
            # Если враг исчез, возвращаемся к патрулю
            self.target_enemy = None
            self.state = "patrol"

    def _combat_step(self, game_map):
        """
        Один шаг боевого поведения

        Args:
            game_map: Объект карты игры
        """
        # Если нет цели или цель мертва, возвращаемся к патрулю
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.target_enemy = None
            self.state = "patrol"
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.target_enemy):
            attack_result = self.attack(self.target_enemy)

            if attack_result['dodged']:
                print(f"{self.target_enemy.name} увернулся от атаки {self.name}!")
            elif attack_result['hit']:
                crit_msg = " КРИТИЧЕСКИЙ УДАР!" if attack_result['critical'] else ""
                print(f"{self.name} атакует {self.target_enemy.name} и наносит {attack_result['damage']} урона!{crit_msg}")
                if not self.target_enemy.is_alive:
                    print(f"{self.target_enemy.name} повержен!")
                    self.target_enemy = None
                    self.state = "patrol"
        else:
            # Двигаемся к цели
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=30)
            if (dx != 0 or dy != 0) and self.consume_stamina():
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy

    def _patrol_step(self, game_map):
        """Один шаг патрулирования"""
        if not self.patrol_points:
            # Если нет маршрута, стоим на месте
            # Периодически переходим в режим отдыха
            if random.random() < 0.1:  # 10% шанс каждый шаг
                self.state = "rest"
                self.rest_counter = 0
            return

        # Получаем целевую точку
        target_x, target_y = self.patrol_points[self.current_patrol_index]

        # Используем алгоритм поиска пути для определения следующего шага
        dx, dy = self._find_next_step(target_x, target_y, game_map, max_search_distance=30)

        # Если нашли направление и можем двигаться
        if dx != 0 or dy != 0:
            if self._can_move(self.x + dx, self.y + dy, game_map):
                self.x += dx
                self.y += dy

        # Проверяем, достигли ли цели
        if self.x == target_x and self.y == target_y:
            # Переходим к следующей точке
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)

            # Случайный отдых в точке патруля
            if random.random() < 0.3:  # 30% шанс отдохнуть
                self.state = "rest"
                self.rest_counter = 0

    def _rest(self):
        """Отдых - обновляется каждый игровой час"""
        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            self.state = "patrol"
            self.rest_counter = 0

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли стражник двигаться на клетку

        Args:
            x: Координата X
            y: Координата Y
            game_map: Объект карты

        Returns:
            bool: True если можно двигаться
        """
        if not game_map.is_valid_position(x, y):
            return False

        tile = game_map.get_tile(x, y)
        return tile.is_passable()


class Merchant(NPC):
    """Класс Торговца с AI перемещения между городами и побега от опасности"""

    def __init__(self, name, x=0, y=0, level=3):
        """
        Инициализация Торговца

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_MERCHANT, level=level)

        # AI параметры
        self.state = "travel"  # travel, rest, flee
        self.target_location = None  # Целевая локация (город/деревня)
        self.rest_counter = 0
        self.rest_duration = random.randint(5, 8)  # Отдых 5-8 часов в городе
        self.steps_per_hour = 1  # Количество шагов за 1 час игрового времени (только соседние клетки)
        self.settlements = []  # Список всех населенных пунктов
        self.stuck_counter = 0  # Счетчик для определения застревания
        self.last_position = (x, y)
        self.threat = None  # Текущая угроза от которой убегаем
        self.detection_range = 8  # Дальность обнаружения угроз

        # Торговая система
        self._generate_merchant_goods()

    def _generate_merchant_goods(self):
        """Генерация начальных товаров торговца"""
        from game.inventory import ItemGenerator, PREDEFINED_ITEMS

        # Увеличиваем инвентарь торговца
        self.inventory.max_slots = 30
        self.inventory.max_weight = 200.0

        # Даем торговцу стартовое золото
        self.inventory.gold = random.randint(200, 500) + self.level * 50

        # Генерируем зелья (5-10 разных видов)
        potion_types = [
            "minor_health_potion", "health_potion", "greater_health_potion",
            "minor_mana_potion", "mana_potion",
            "minor_stamina_potion", "stamina_potion"
        ]
        for potion_type in random.sample(potion_types, random.randint(4, 6)):
            quantity = random.randint(2, 5)
            self.inventory.add_item(PREDEFINED_ITEMS[potion_type], quantity)

        # Генерируем оружие (2-4 штуки)
        for _ in range(random.randint(2, 4)):
            weapon = ItemGenerator.generate_weapon(self.level)
            self.inventory.add_item(weapon, 1)

        # Генерируем доспехи (3-6 штук)
        for _ in range(random.randint(3, 6)):
            armor = ItemGenerator.generate_armor(self.level)
            self.inventory.add_item(armor, 1)

        # Генерируем украшения (1-3 штуки)
        for _ in range(random.randint(1, 3)):
            jewelry = ItemGenerator.generate_jewelry(self.level)
            self.inventory.add_item(jewelry, 1)

        # Генерируем ресурсы (2-4 вида)
        resource_types = ["copper_ore", "iron_ore", "silver_ore", "ancient_coin", "artifact_fragment"]
        for resource_type in random.sample(resource_types, random.randint(2, 4)):
            quantity = random.randint(3, 10)
            self.inventory.add_item(PREDEFINED_ITEMS[resource_type], quantity)

    def restock_goods(self):
        """Пополнение товаров торговца (вызывается при отдыхе в городе)"""
        from game.inventory import ItemGenerator, PREDEFINED_ITEMS

        # Добавляем золото
        self.inventory.gold += random.randint(50, 150)

        # Добавляем случайные новые товары
        if random.random() < 0.7:  # 70% шанс добавить зелье
            potion_types = [
                "minor_health_potion", "health_potion",
                "minor_mana_potion", "mana_potion",
                "minor_stamina_potion"
            ]
            potion_type = random.choice(potion_types)
            quantity = random.randint(1, 3)
            self.inventory.add_item(PREDEFINED_ITEMS[potion_type], quantity)

        if random.random() < 0.5:  # 50% шанс добавить оружие
            weapon = ItemGenerator.generate_weapon(self.level)
            self.inventory.add_item(weapon, 1)

        if random.random() < 0.5:  # 50% шанс добавить доспех
            armor = ItemGenerator.generate_armor(self.level)
            self.inventory.add_item(armor, 1)

        if random.random() < 0.3:  # 30% шанс добавить украшение
            jewelry = ItemGenerator.generate_jewelry(self.level)
            self.inventory.add_item(jewelry, 1)

    def set_settlements(self, settlements):
        """
        Установить список населенных пунктов для посещения

        Args:
            settlements: Список локаций (Location объектов)
        """
        self.settlements = settlements
        if settlements and not self.target_location:
            self._choose_new_destination()

    def update_ai(self, game_map, all_npcs=None):
        """
        Обновление AI торговца за 1 час игрового времени

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для обнаружения угроз
        """
        if not self.is_alive:
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие угроз поблизости
        if all_npcs:
            self._check_for_threats(all_npcs)

        if self.state == "flee":
            self._flee_step(game_map)
        elif self.state == "travel":
            # Делаем несколько шагов за 1 час
            for _ in range(self.steps_per_hour):
                if not self.consume_stamina():
                    break
                if not self._travel_step(game_map):
                    break
        elif self.state == "rest":
            self._rest()

    def _check_for_threats(self, all_npcs):
        """
        Проверить наличие угроз поблизости

        Args:
            all_npcs: Список всех NPC
        """
        # Ищем ближайшую угрозу
        closest_threat = None
        closest_distance = float('inf')

        for npc in all_npcs:
            if not npc.is_alive:
                continue

            # Проверяем отношение к этому NPC
            relationship = NPC_RELATIONSHIPS.get((self.npc_type, npc.npc_type), RELATIONSHIP_NEUTRAL)

            if relationship in [RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY]:
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                # Если враг в зоне обнаружения
                if distance <= self.detection_range and distance < closest_distance:
                    closest_threat = npc
                    closest_distance = distance

        # Если есть угроза, убегаем
        if closest_threat:
            self.threat = closest_threat
            self.state = "flee"
        elif self.state == "flee":
            # Если угрозы больше нет, возвращаемся к путешествию
            self.threat = None
            self.state = "travel"

    def _flee_step(self, game_map):
        """
        Один шаг побега от угрозы

        Args:
            game_map: Объект карты игры
        """
        # Если угроза исчезла или мертва, возвращаемся к путешествию
        if not self.threat or not self.threat.is_alive:
            self.threat = None
            self.state = "travel"
            return

        # Убегаем в противоположную от угрозы сторону
        dx_away = self.x - self.threat.x
        dy_away = self.y - self.threat.y

        # Нормализуем направление
        if dx_away > 0:
            dx = 1
        elif dx_away < 0:
            dx = -1
        else:
            dx = 0

        if dy_away > 0:
            dy = 1
        elif dy_away < 0:
            dy = -1
        else:
            dy = 0

        # Если оба направления 0, выбираем случайное
        if dx == 0 and dy == 0:
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])

        # Пытаемся двигаться
        if self.consume_stamina():
            new_x = self.x + dx
            new_y = self.y + dy

            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y
            else:
                # Если не можем идти прямо, пробуем другие направления
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                random.shuffle(directions)
                for alt_dx, alt_dy in directions:
                    new_x = self.x + alt_dx
                    new_y = self.y + alt_dy
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        break

    def _choose_new_destination(self):
        """Выбрать новую цель для путешествия"""
        if not self.settlements:
            return

        # Исключаем текущую позицию из выбора
        available = [s for s in self.settlements
                    if abs(s.x - self.x) > 5 or abs(s.y - self.y) > 5]

        if available:
            self.target_location = random.choice(available)
        elif self.settlements:
            self.target_location = random.choice(self.settlements)

        self.stuck_counter = 0

    def _travel_step(self, game_map):
        """
        Один шаг путешествия к цели

        Returns:
            bool: True если торговец продолжает движение
        """
        if not self.target_location:
            self._choose_new_destination()
            return False

        target_x = self.target_location.x
        target_y = self.target_location.y

        # Проверяем, достигли ли цели (в пределах 2 клеток)
        distance = abs(self.x - target_x) + abs(self.y - target_y)
        if distance <= 2:
            # Достигли города, переходим в режим отдыха/торговли
            self.state = "rest"
            self.rest_counter = 0
            self.rest_duration = random.randint(5, 8)
            return False

        # Используем алгоритм поиска пути для определения следующего шага
        # Торговцы ищут путь на большие расстояния
        dx, dy = self._find_next_step(target_x, target_y, game_map, max_search_distance=100)

        # Сохраняем текущую позицию для проверки застревания
        old_x, old_y = self.x, self.y

        # Пытаемся двигаться
        moved = False
        if dx != 0 or dy != 0:
            if self._can_move(self.x + dx, self.y + dy, game_map):
                self.x += dx
                self.y += dy
                moved = True

        # Проверка застревания
        if not moved or (self.x == old_x and self.y == old_y):
            self.stuck_counter += 1
            if self.stuck_counter > 20:
                # Если застряли, выбираем новую цель
                self._choose_new_destination()
                self.stuck_counter = 0
                return False
        else:
            self.stuck_counter = 0

        return True

    def _rest(self):
        """Отдых/торговля в городе"""
        self.rest_counter += 1

        # Пополняем товары каждые 2 часа отдыха
        if self.rest_counter % 2 == 0:
            self.restock_goods()

        if self.rest_counter >= self.rest_duration:
            # Закончили отдых, выбираем новый город
            self.state = "travel"
            self._choose_new_destination()

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли торговец двигаться на клетку

        Args:
            x: Координата X
            y: Координата Y
            game_map: Объект карты

        Returns:
            bool: True если можно двигаться
        """
        if not game_map.is_valid_position(x, y):
            return False

        tile = game_map.get_tile(x, y)
        return tile.is_passable()


class Bandit(NPC):
    """Класс Бандита с AI патрулирования территории лагеря"""

    def __init__(self, name, x=0, y=0, level=4, camp_x=None, camp_y=None):
        """
        Инициализация Бандита

        Args:
            name: Имя бандита
            x: Позиция X
            y: Позиция Y
            level: Уровень бандита
            camp_x: Координата X лагеря
            camp_y: Координата Y лагеря
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_BANDIT, level=level)

        # AI параметры
        self.state = "patrol"  # patrol, rest, combat
        self.camp_x = camp_x if camp_x is not None else x  # Позиция лагеря
        self.camp_y = camp_y if camp_y is not None else y
        self.max_distance_from_camp = BANDIT_CAMP_RADIUS  # Максимальная дистанция от лагеря
        self.rest_counter = 0
        self.rest_duration = random.randint(2, 4)  # Отдых 2-4 часа
        self.steps_per_hour = 1  # Шагов за час
        self.target_enemy = None  # Текущий враг для атаки
        self.detection_range = 10  # Дальность обнаружения врагов
        self.wander_target = None  # Целевая точка для блуждания

    def update_ai(self, game_map, all_npcs=None, player=None):
        """
        Обновление AI бандита за 1 час игрового времени

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для поиска врагов
            player: Объект игрока (бандиты агрессивны к игроку)
        """
        if not self.is_alive:
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие врагов поблизости (включая игрока)
        if all_npcs or player:
            self._check_for_enemies(all_npcs, player)

        if self.state == "combat":
            self._combat_step(game_map)
        elif self.state == "patrol":
            # Делаем несколько шагов за 1 час
            for _ in range(self.steps_per_hour):
                if not self.consume_stamina():
                    break
                self._patrol_step(game_map)
                if self.state == "rest":
                    break
        elif self.state == "rest":
            self._rest()

    def _check_for_enemies(self, all_npcs, player=None):
        """
        Проверить наличие врагов поблизости (включая игрока)

        Args:
            all_npcs: Список всех NPC
            player: Объект игрока
        """
        # Ищем ближайшего живого врага
        closest_enemy = None
        closest_distance = float('inf')

        # Проверяем игрока (бандиты ВСЕГДА агрессивны к игроку)
        if player and player.is_alive:
            distance = abs(self.x - player.x) + abs(self.y - player.y)
            if distance <= self.detection_range:
                closest_enemy = player
                closest_distance = distance

        # Проверяем других NPC
        if all_npcs:
            for npc in all_npcs:
                if not npc.is_alive:
                    continue

                # Проверяем отношение к этому NPC
                relationship = NPC_RELATIONSHIPS.get((self.npc_type, npc.npc_type), RELATIONSHIP_NEUTRAL)

                if relationship == RELATIONSHIP_HOSTILE:
                    distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                    # Если враг в зоне обнаружения
                    if distance <= self.detection_range and distance < closest_distance:
                        closest_enemy = npc
                        closest_distance = distance

        # Если нашли врага, переходим в боевой режим
        if closest_enemy:
            self.target_enemy = closest_enemy
            self.state = "combat"
        elif self.state == "combat":
            # Если враг исчез, возвращаемся к патрулю
            self.target_enemy = None
            self.state = "patrol"

    def _combat_step(self, game_map):
        """
        Один шаг боевого поведения

        Args:
            game_map: Объект карты игры
        """
        # Если нет цели или цель мертва, возвращаемся к патрулю
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.target_enemy = None
            self.state = "patrol"
            return

        # Проверяем расстояние до лагеря
        distance_to_camp = abs(self.x - self.camp_x) + abs(self.y - self.camp_y)

        # Если слишком далеко от лагеря, возвращаемся
        if distance_to_camp > self.max_distance_from_camp:
            self.target_enemy = None
            self.state = "patrol"
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.target_enemy):
            # Устанавливаем флаг что атаковали игрока (для принудительного открытия окна боя)
            if hasattr(self.target_enemy, 'attacked_by_npc'):
                self.target_enemy.attacked_by_npc = self

            attack_result = self.attack(self.target_enemy)

            if attack_result['dodged']:
                print(f"{self.target_enemy.name} увернулся от атаки {self.name}!")
            elif attack_result['hit']:
                crit_msg = " КРИТИЧЕСКИЙ УДАР!" if attack_result['critical'] else ""
                print(f"{self.name} атакует {self.target_enemy.name} и наносит {attack_result['damage']} урона!{crit_msg}")
                if not self.target_enemy.is_alive:
                    print(f"{self.target_enemy.name} повержен!")
                    self.target_enemy = None
                    self.state = "patrol"
        else:
            # Двигаемся к цели
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=30)
            if (dx != 0 or dy != 0) and self.consume_stamina():
                new_x = self.x + dx
                new_y = self.y + dy

                # Проверяем, не выходим ли за пределы территории
                distance_to_camp_new = abs(new_x - self.camp_x) + abs(new_y - self.camp_y)
                if distance_to_camp_new <= self.max_distance_from_camp:
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                else:
                    # Слишком далеко, прекращаем преследование
                    self.target_enemy = None
                    self.state = "patrol"

    def _patrol_step(self, game_map):
        """Один шаг патрулирования территории"""
        # Проверяем расстояние до лагеря
        distance_to_camp = abs(self.x - self.camp_x) + abs(self.y - self.camp_y)

        # Если слишком далеко от лагеря, возвращаемся
        if distance_to_camp > self.max_distance_from_camp:
            # Идем в сторону лагеря
            dx, dy = self._find_next_step(self.camp_x, self.camp_y, game_map, max_search_distance=50)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy
            return

        # Если достигли цели блуждания или цели нет, выбираем новую
        if not self.wander_target or (self.x == self.wander_target[0] and self.y == self.wander_target[1]):
            self._choose_wander_target()

        # Идем к цели блуждания
        if self.wander_target:
            dx, dy = self._find_next_step(self.wander_target[0], self.wander_target[1], game_map, max_search_distance=30)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy

        # Случайный отдых
        if random.random() < 0.05:  # 5% шанс отдохнуть
            self.state = "rest"
            self.rest_counter = 0

    def _choose_wander_target(self):
        """Выбрать случайную точку для блуждания в пределах территории"""
        # Выбираем случайную точку в пределах радиуса от лагеря
        max_offset = min(self.max_distance_from_camp, 15)  # Ограничиваем для производительности

        target_x = self.camp_x + random.randint(-max_offset, max_offset)
        target_y = self.camp_y + random.randint(-max_offset, max_offset)

        self.wander_target = (target_x, target_y)

    def _rest(self):
        """Отдых - обновляется каждый игровой час"""
        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            self.state = "patrol"
            self.rest_counter = 0

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли бандит двигаться на клетку

        Args:
            x: Координата X
            y: Координата Y
            game_map: Объект карты

        Returns:
            bool: True если можно двигаться
        """
        if not game_map.is_valid_position(x, y):
            return False

        tile = game_map.get_tile(x, y)
        return tile.is_passable()


class Miner(NPC):
    """Класс Шахтера с AI работы и побега от опасности"""

    def __init__(self, name, x=0, y=0, level=3, mine_x=None, mine_y=None):
        """
        Инициализация Шахтера

        Args:
            name: Имя шахтера
            x: Позиция X
            y: Позиция Y
            level: Уровень шахтера
            mine_x: Координата X шахты (центр территории)
            mine_y: Координата Y шахты (центр территории)
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_MINER, level=level)

        # AI параметры
        self.state = "work"  # work, rest, flee
        self.mine_x = mine_x if mine_x is not None else x  # Центр шахты
        self.mine_y = mine_y if mine_y is not None else y
        self.max_distance_from_mine = 20  # Максимальная дистанция от шахты
        self.rest_counter = 0
        self.rest_duration = random.randint(3, 5)  # Отдых 3-5 часов
        self.steps_per_hour = 1  # Шагов за час
        self.threat = None  # Текущая угроза от которой убегаем
        self.detection_range = 8  # Дальность обнаружения угроз
        self.wander_target = None  # Целевая точка для блуждания

    def update_ai(self, game_map, all_npcs=None):
        """
        Обновление AI шахтера за 1 час игрового времени

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для обнаружения угроз
        """
        if not self.is_alive:
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие угроз поблизости
        if all_npcs:
            self._check_for_threats(all_npcs)

        if self.state == "flee":
            self._flee_step(game_map)
        elif self.state == "work":
            # Делаем несколько шагов за 1 час
            for _ in range(self.steps_per_hour):
                if not self.consume_stamina():
                    break
                self._work_step(game_map)
                if self.state == "rest":
                    break
        elif self.state == "rest":
            self._rest()

    def _check_for_threats(self, all_npcs):
        """
        Проверить наличие угроз поблизости

        Args:
            all_npcs: Список всех NPC
        """
        # Ищем ближайшую угрозу
        closest_threat = None
        closest_distance = float('inf')

        for npc in all_npcs:
            if not npc.is_alive:
                continue

            # Проверяем отношение к этому NPC
            relationship = NPC_RELATIONSHIPS.get((self.npc_type, npc.npc_type), RELATIONSHIP_NEUTRAL)

            if relationship in [RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY]:
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                # Если враг в зоне обнаружения
                if distance <= self.detection_range and distance < closest_distance:
                    closest_threat = npc
                    closest_distance = distance

        # Если есть угроза, убегаем
        if closest_threat:
            self.threat = closest_threat
            self.state = "flee"
        elif self.state == "flee":
            # Если угрозы больше нет, возвращаемся к работе
            self.threat = None
            self.state = "work"

    def _flee_step(self, game_map):
        """
        Один шаг побега от угрозы

        Args:
            game_map: Объект карты игры
        """
        # Если угроза исчезла или мертва, возвращаемся к работе
        if not self.threat or not self.threat.is_alive:
            self.threat = None
            self.state = "work"
            return

        # Убегаем в противоположную от угрозы сторону
        dx_away = self.x - self.threat.x
        dy_away = self.y - self.threat.y

        # Нормализуем направление
        if dx_away > 0:
            dx = 1
        elif dx_away < 0:
            dx = -1
        else:
            dx = 0

        if dy_away > 0:
            dy = 1
        elif dy_away < 0:
            dy = -1
        else:
            dy = 0

        # Если оба направления 0, выбираем случайное
        if dx == 0 and dy == 0:
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])

        # Пытаемся двигаться
        if self.consume_stamina():
            new_x = self.x + dx
            new_y = self.y + dy

            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y
            else:
                # Если не можем идти прямо, пробуем другие направления
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                random.shuffle(directions)
                for alt_dx, alt_dy in directions:
                    new_x = self.x + alt_dx
                    new_y = self.y + alt_dy
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        break

    def _work_step(self, game_map):
        """Один шаг работы - патрулирование территории шахты"""
        # Проверяем расстояние до шахты
        distance_to_mine = abs(self.x - self.mine_x) + abs(self.y - self.mine_y)

        # Если слишком далеко от шахты, возвращаемся
        if distance_to_mine > self.max_distance_from_mine:
            # Идем в сторону шахты
            dx, dy = self._find_next_step(self.mine_x, self.mine_y, game_map, max_search_distance=50)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy
            return

        # Если достигли цели блуждания или цели нет, выбираем новую
        if not self.wander_target or (self.x == self.wander_target[0] and self.y == self.wander_target[1]):
            self._choose_wander_target()

        # Идем к цели блуждания
        if self.wander_target:
            dx, dy = self._find_next_step(self.wander_target[0], self.wander_target[1], game_map, max_search_distance=30)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy

        # Случайный отдых
        if random.random() < 0.08:  # 8% шанс отдохнуть
            self.state = "rest"
            self.rest_counter = 0

    def _choose_wander_target(self):
        """Выбрать случайную точку для блуждания в пределах территории шахты"""
        # Выбираем случайную точку в пределах радиуса от шахты
        max_offset = min(self.max_distance_from_mine, 15)  # Ограничиваем для производительности

        target_x = self.mine_x + random.randint(-max_offset, max_offset)
        target_y = self.mine_y + random.randint(-max_offset, max_offset)

        self.wander_target = (target_x, target_y)

    def _rest(self):
        """Отдых - обновляется каждый игровой час"""
        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            self.state = "work"
            self.rest_counter = 0

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли шахтер двигаться на клетку

        Args:
            x: Координата X
            y: Координата Y
            game_map: Объект карты

        Returns:
            bool: True если можно двигаться
        """
        if not game_map.is_valid_position(x, y):
            return False

        tile = game_map.get_tile(x, y)
        return tile.is_passable()


class Undead(NPC):
    """Класс Нежити с агрессивным AI и привязкой к руинам"""

    def __init__(self, name, x=0, y=0, level=1, ruins_x=None, ruins_y=None):
        """
        Инициализация Нежити

        Args:
            name: Имя нежити
            x: Позиция X
            y: Позиция Y
            level: Уровень нежити (определяет ранг)
            ruins_x: Координата X руин
            ruins_y: Координата Y руин
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_UNDEAD, level=level)

        # AI параметры
        self.state = "patrol"  # patrol, rest, combat
        self.ruins_x = ruins_x if ruins_x is not None else x  # Центр руин
        self.ruins_y = ruins_y if ruins_y is not None else y
        self.max_distance_from_ruins = 7  # Максимальная дистанция от руин
        self.rest_counter = 0
        self.rest_duration = random.randint(2, 3)  # Отдых 2-3 часа
        self.steps_per_hour = 1  # Шагов за час
        self.target_enemy = None  # Текущая цель для атаки
        self.detection_range = 12  # Дальность обнаружения врагов
        self.wander_target = None  # Целевая точка для патруля

    def update_ai(self, game_map, all_npcs=None, player=None):
        """
        Обновление AI нежити за 1 час игрового времени
        Нежита агрессивна ко ВСЕМ!

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для обнаружения врагов
            player: Объект игрока (нежита также агрессивна к игроку)
        """
        if not self.is_alive:
            return

        # Восстанавливаем выносливость
        self.recover_stamina()

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие врагов поблизости (включая игрока)
        if all_npcs or player:
            self._check_for_enemies(all_npcs, player)

        if self.state == "combat":
            self._combat_step(game_map)
        elif self.state == "patrol":
            # Делаем несколько шагов за 1 час
            for _ in range(self.steps_per_hour):
                if not self.consume_stamina():
                    break
                self._patrol_step(game_map)
                if self.state == "rest":
                    break
        elif self.state == "rest":
            self._rest()

    def _check_for_enemies(self, all_npcs, player=None):
        """
        Проверить наличие врагов поблизости
        Нежита агрессивна ко ВСЕМ!

        Args:
            all_npcs: Список всех NPC
            player: Объект игрока
        """
        # Ищем ближайшего живого врага
        closest_enemy = None
        closest_distance = float('inf')

        # Проверяем игрока (нежита ВСЕГДА агрессивна к игроку)
        if player and player.is_alive:
            distance = abs(self.x - player.x) + abs(self.y - player.y)
            if distance <= self.detection_range:
                closest_enemy = player
                closest_distance = distance

        # Проверяем других NPC (нежита агрессивна ко ВСЕМ!)
        if all_npcs:
            for npc in all_npcs:
                if not npc.is_alive:
                    continue

                # Нежита враждебна ко всем живым существам
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)

                # Если враг в зоне обнаружения
                if distance <= self.detection_range and distance < closest_distance:
                    closest_enemy = npc
                    closest_distance = distance

        # Если нашли врага, переходим в боевой режим
        if closest_enemy:
            self.target_enemy = closest_enemy
            self.state = "combat"
        elif self.state == "combat":
            # Если враг исчез, возвращаемся к патрулю
            self.target_enemy = None
            self.state = "patrol"

    def _combat_step(self, game_map):
        """
        Один шаг боевого поведения

        Args:
            game_map: Объект карты игры
        """
        # Если нет цели или цель мертва, возвращаемся к патрулю
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.target_enemy = None
            self.state = "patrol"
            return

        # Проверяем расстояние до руин
        distance_to_ruins = abs(self.x - self.ruins_x) + abs(self.y - self.ruins_y)

        # Если слишком далеко от руин, возвращаемся
        if distance_to_ruins > self.max_distance_from_ruins:
            self.target_enemy = None
            self.state = "patrol"
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.target_enemy):
            # Устанавливаем флаг что атаковали игрока (для принудительного открытия окна боя)
            if hasattr(self.target_enemy, 'attacked_by_npc'):
                self.target_enemy.attacked_by_npc = self

            attack_result = self.attack(self.target_enemy)

            if attack_result['dodged']:
                print(f"{self.target_enemy.name} увернулся от атаки {self.name}!")
            elif attack_result['hit']:
                crit_msg = " КРИТИЧЕСКИЙ УДАР!" if attack_result['critical'] else ""
                print(f"{self.name} атакует {self.target_enemy.name} и наносит {attack_result['damage']} урона!{crit_msg}")
                if not self.target_enemy.is_alive:
                    print(f"{self.target_enemy.name} повержен!")
                    self.target_enemy = None
                    self.state = "patrol"
        else:
            # Двигаемся к цели
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=30)
            if (dx != 0 or dy != 0) and self.consume_stamina():
                new_x = self.x + dx
                new_y = self.y + dy

                # Проверяем, не выходим ли за пределы территории
                distance_to_ruins_new = abs(new_x - self.ruins_x) + abs(new_y - self.ruins_y)
                if distance_to_ruins_new <= self.max_distance_from_ruins:
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                else:
                    # Слишком далеко, прекращаем преследование
                    self.target_enemy = None
                    self.state = "patrol"

    def _patrol_step(self, game_map):
        """Один шаг патрулирования территории руин"""
        # Проверяем расстояние до руин
        distance_to_ruins = abs(self.x - self.ruins_x) + abs(self.y - self.ruins_y)

        # Если слишком далеко от руин, возвращаемся
        if distance_to_ruins > self.max_distance_from_ruins:
            # Идем в сторону руин
            dx, dy = self._find_next_step(self.ruins_x, self.ruins_y, game_map, max_search_distance=20)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy
            return

        # Если достигли цели патруля или цели нет, выбираем новую
        if not self.wander_target or (self.x == self.wander_target[0] and self.y == self.wander_target[1]):
            self._choose_patrol_target()

        # Идем к цели патруля
        if self.wander_target:
            dx, dy = self._find_next_step(self.wander_target[0], self.wander_target[1], game_map, max_search_distance=20)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy

        # Случайный отдых
        if random.random() < 0.1:  # 10% шанс отдохнуть
            self.state = "rest"
            self.rest_counter = 0

    def _choose_patrol_target(self):
        """Выбрать случайную точку для патруля в пределах территории руин"""
        # Выбираем случайную точку в пределах радиуса от руин
        max_offset = min(self.max_distance_from_ruins, 7)

        target_x = self.ruins_x + random.randint(-max_offset, max_offset)
        target_y = self.ruins_y + random.randint(-max_offset, max_offset)

        self.wander_target = (target_x, target_y)

    def _rest(self):
        """Отдых - обновляется каждый игровой час"""
        self.rest_counter += 1
        if self.rest_counter >= self.rest_duration:
            self.state = "patrol"
            self.rest_counter = 0

    def _can_move(self, x, y, game_map):
        """
        Проверить, может ли нежить двигаться на клетку

        Args:
            x: Координата X
            y: Координата Y
            game_map: Объект карты

        Returns:
            bool: True если можно двигаться
        """
        if not game_map.is_valid_position(x, y):
            return False

        tile = game_map.get_tile(x, y)
        return tile.is_passable()
