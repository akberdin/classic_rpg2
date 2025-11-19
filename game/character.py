"""
Классы персонажей (игрок и NPC)
"""
import random
from collections import deque
from game.inventory import Inventory
from game.constants import (
    MAX_LEVEL, RANKS, RELATIONSHIP_NEUTRAL, RELATIONSHIP_HOSTILE, RELATIONSHIP_UNFRIENDLY,
    NPC_RELATIONSHIPS, NPC_TYPE_GUARD, NPC_TYPE_MERCHANT, NPC_TYPE_BANDIT,
    NPC_TYPE_MINER, NPC_TYPE_UNDEAD, NPC_TYPE_MAGE,
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

    def generate_random_stats(self, level=1):
        """
        Генерация сбалансированных характеристик на основе уровня

        Args:
            level: Уровень персонажа (влияет на силу характеристик)
        """
        # Сбалансированная формула с плавным ростом для всех уровней
        if level <= 5:
            # Низкие уровни (1-5): начальные характеристики
            base_stat = 2 + level * 0.8  # Уровень 1: 2.8, Уровень 5: 6
        elif level <= 15:
            # Средние уровни (6-15): улучшенный рост (исправлено)
            base_stat = 6 + level * 0.7  # Уровень 6: 10.2, Уровень 15: 16.5
        elif level <= 30:
            # Высокие уровни (16-30): сильные характеристики
            base_stat = 10 + level * 0.7  # Уровень 16: 21.2, Уровень 30: 31
        else:
            # Очень высокие уровни (31-40): элитные характеристики
            base_stat = 14 + level * 0.75  # Уровень 31: 37.25, Уровень 40: 44

        # Вариация ±15% для разнообразия
        variation = max(1, int(base_stat * 0.15))

        # Генерируем характеристики с округлением
        self.strength = max(1, int(random.uniform(base_stat - variation, base_stat + variation)))
        self.dexterity = max(1, int(random.uniform(base_stat - variation, base_stat + variation)))
        self.constitution = max(1, int(random.uniform(base_stat - variation, base_stat + variation)))
        self.spirit = max(1, int(random.uniform(base_stat - variation, base_stat + variation)))
        self.intelligence = max(1, int(random.uniform(base_stat - variation, base_stat + variation)))
        self.luck = max(1, int(random.uniform(base_stat - variation, base_stat + variation)))

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

    def get_effective_max_health(self):
        """
        Получить эффективное максимальное здоровье с учетом бонусов от экипировки

        Returns:
            int: Эффективное максимальное здоровье
        """
        base_max_health = self.constitution * 20

        # Добавляем бонусы от экипировки
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_total_stats_bonus'):
            equipment_bonus = self.inventory.get_total_stats_bonus()
            # Бонус к телосложению увеличивает здоровье
            constitution_bonus = equipment_bonus.get('constitution', 0)
            base_max_health += constitution_bonus * 20

        return base_max_health

    def get_effective_max_stamina(self):
        """
        Получить эффективную максимальную выносливость с учетом бонусов от экипировки

        Returns:
            int: Эффективная максимальная выносливость
        """
        base_strength = self.strength
        base_constitution = self.constitution

        # Добавляем бонусы от экипировки
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_total_stats_bonus'):
            equipment_bonus = self.inventory.get_total_stats_bonus()
            base_strength += equipment_bonus.get('strength', 0)
            base_constitution += equipment_bonus.get('constitution', 0)

        return (base_strength + base_constitution) * STAMINA_PER_STAT_POINT

    def get_effective_max_weight(self):
        """
        Получить эффективную максимальную грузоподъемность с учетом бонусов от экипировки

        Returns:
            int: Эффективная максимальная грузоподъемность
        """
        base_strength = self.strength

        # Добавляем бонусы от экипировки
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_total_stats_bonus'):
            equipment_bonus = self.inventory.get_total_stats_bonus()
            base_strength += equipment_bonus.get('strength', 0)

        # Грузоподъемность = 50 + сила * 5
        return 50 + base_strength * 5

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
            dict: Информация о полученном уроне
                - damage: Итоговый урон
                - blocked: Урон, заблокированный броней
                - godmode: True если сработал режим бессмертия
        """
        # Проверяем режим бессмертия (только для игрока)
        if hasattr(self, 'godmode') and self.godmode:
            # В режиме бессмертия урон не наносится
            return {
                'damage': 0,
                'blocked': damage,
                'godmode': True,
                'alive': True
            }

        # Применяем урон
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.is_alive = False

        return {
            'damage': damage,
            'blocked': 0,
            'godmode': False,
            'alive': self.is_alive
        }

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
        Максимум 85%

        Returns:
            float: Шанс уворота (0-85)
        """
        dodge_chance = self.dexterity * DODGE_BASE_CHANCE
        return min(85.0, dodge_chance)  # Максимум 85%

    def calculate_crit_chance(self):
        """
        Рассчитать шанс критического удара на основе удачи
        Максимум 85%

        Returns:
            float: Шанс крита (0-85)
        """
        crit_chance = self.luck * CRIT_BASE_CHANCE
        return min(85.0, crit_chance)  # Максимум 85%

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

        # Учитываем защиту цели с diminishing returns
        target_defense = target.get_total_defense()

        # Diminishing returns: после soft cap (50) защита работает на 50%
        defense_soft_cap = 50
        if target_defense > defense_soft_cap:
            effective_defense = defense_soft_cap + (target_defense - defense_soft_cap) * 0.5
        else:
            effective_defense = target_defense

        # Защита снижает урон, но не может снизить его до нуля (минимум 1)
        actual_damage = max(1, total_damage - effective_defense)
        blocked_by_armor = max(0, total_damage - actual_damage)

        # Применяем урон
        damage_result = target.take_damage(actual_damage)

        return {
            'damage': damage_result['damage'],
            'blocked_by_armor': blocked_by_armor,
            'blocked_by_godmode': damage_result['blocked'] if damage_result['godmode'] else 0,
            'godmode': damage_result['godmode'],
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
        """Получить общий урон с учетом оружия, экипировки и временных бонусов"""
        base_damage = self.strength

        # Добавляем бонусы к силе от экипировки (украшения и т.д.)
        if hasattr(self, 'inventory') and self.inventory and hasattr(self.inventory, 'get_total_stats_bonus'):
            equipment_bonus = self.inventory.get_total_stats_bonus()
            base_damage += equipment_bonus.get('strength', 0)

        # Добавляем временный бонус к силе
        if hasattr(self, 'temp_strength_boost'):
            base_damage += self.temp_strength_boost

        # Если есть экипированное оружие
        if hasattr(self, 'inventory') and self.inventory:
            from game.inventory import EquipmentSlot, WeaponItem
            weapon = self.inventory.get_equipped_item(EquipmentSlot.WEAPON)
            if weapon and isinstance(weapon, WeaponItem):
                return weapon.damage + base_damage

        return base_damage

    def get_total_defense(self):
        """Получить общую защиту с учетом доспехов и бонусов от экипировки"""
        total_defense = 0

        # Добавляем бонусы к защите от телосложения (constitution) от экипировки
        if hasattr(self, 'inventory') and self.inventory and hasattr(self.inventory, 'get_total_stats_bonus'):
            equipment_bonus = self.inventory.get_total_stats_bonus()
            # Constitution даёт бонус к защите
            total_defense += equipment_bonus.get('constitution', 0)

        # Если есть экипированные доспехи
        if hasattr(self, 'inventory') and self.inventory:
            from game.inventory import ArmorItem
            for item in self.inventory.equipment.values():
                if item and isinstance(item, ArmorItem):
                    total_defense += item.defense

        return total_defense

    def get_magic_defense(self):
        """
        Получить магическую защиту на основе характеристики Дух

        Магическая защита снижает урон от магических атак.
        Формула: Дух * 0.8 + бонусы от экипировки (сниженный множитель для баланса)

        Returns:
            int: Значение магической защиты
        """
        # Базовая магическая защита от характеристики Дух (снижено с 1.5 до 0.8)
        base_magic_defense = int(self.spirit * 0.8)

        # Бонусы от экипировки (spirit дает бонус к магической защите)
        equipment_bonus = 0
        if hasattr(self, 'inventory') and self.inventory and hasattr(self.inventory, 'get_total_stats_bonus'):
            stats_bonus = self.inventory.get_total_stats_bonus()
            # Spirit от экипировки также увеличивает магическую защиту (сниженный множитель)
            equipment_bonus = int(stats_bonus.get('spirit', 0) * 0.8)

        return base_magic_defense + equipment_bonus

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

        # Чит-мод (бессмертие)
        self.godmode = False

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

    def get_effective_max_mana(self):
        """
        Получить эффективную максимальную ману с учетом бонусов от экипировки

        Returns:
            int: Эффективная максимальная мана
        """
        base_spirit = self.spirit

        # Добавляем бонусы от экипировки
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_total_stats_bonus'):
            equipment_bonus = self.inventory.get_total_stats_bonus()
            base_spirit += equipment_bonus.get('spirit', 0)

        return base_spirit * 10

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

        # Увеличиваем требуемый опыт для следующего уровня (менее агрессивный рост)
        self.experience_to_next_level = int(self.experience_to_next_level * 1.35)

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
        # Используем эффективные значения с учетом бонусов от экипировки
        effective_max_health = self.get_effective_max_health()
        effective_max_mana = self.get_effective_max_mana()
        effective_max_stamina = self.get_effective_max_stamina()

        # Восстанавливаем 30% от эффективного максимального здоровья
        health_restored = int(effective_max_health * 0.3)
        self.health = min(effective_max_health, self.health + health_restored)

        # Восстанавливаем 50% от эффективной максимальной маны
        mana_restored = int(effective_max_mana * 0.5)
        self.mana = min(effective_max_mana, self.mana + mana_restored)

        # Восстанавливаем выносливость (используя активный отдых)
        old_stamina = self.stamina
        # Временно устанавливаем max_stamina на эффективное значение
        original_max_stamina = self.max_stamina
        self.max_stamina = effective_max_stamina
        self.recover_stamina(is_active_rest=True)
        self.max_stamina = original_max_stamina
        stamina_restored = self.stamina - old_stamina

        print(f"Здоровье восстановлено: +{health_restored} ({self.health}/{effective_max_health})")
        print(f"Мана восстановлена: +{mana_restored} ({self.mana}/{effective_max_mana})")
        print(f"Выносливость восстановлена: +{stamina_restored} ({self.stamina}/{effective_max_stamina})")

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
        elif item.item_type == "skill_book":
            # Используем книгу умения
            result = item.use(self)
            # Удаляем книгу только если умение было успешно изучено
            if "Изучено умение" in result:
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

        # Генерируем характеристики на основе уровня
        self.generate_random_stats(level=self.level)

        # Инвентарь для NPC
        self.inventory = Inventory(max_slots=10, max_weight=50.0)

        # Генерируем и экипируем начальную экипировку
        self._generate_initial_equipment()

    def _generate_initial_equipment(self):
        """Генерация и автоматическая экипировка начального снаряжения"""
        from game.inventory import ItemGenerator

        # Используем rank-based генерацию для лучшего масштабирования
        equipment_items = ItemGenerator.generate_npc_equipment_by_rank(self.npc_type, self.level)

        for item in equipment_items:
            # Добавляем в инвентарь
            if self.inventory.add_item(item, 1):
                # Пытаемся сразу экипировать
                self.inventory.equip_item(item.name)

        # Обновляем характеристики после экипировки
        self.update_derived_stats()

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

        # Модификация статов для стражника: высокие сила и телосложение, низкий дух
        self._adjust_guard_stats()

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
        self.pursuit_counter = 0  # Счетчик ходов преследования
        self.max_pursuit_steps = 8  # Максимальное количество ходов преследования

    def _adjust_guard_stats(self):
        """Модификация статов для стражника - воин, не маг"""
        # Увеличиваем боевые характеристики
        self.strength = int(self.strength * 1.3)
        self.constitution = int(self.constitution * 1.2)
        self.dexterity = int(self.dexterity * 1.1)

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.4))
        self.intelligence = max(1, int(self.intelligence * 0.6))

        # Обновляем производные статы
        self.update_derived_stats()

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
            self.pursuit_counter = 0  # Сбрасываем счетчик преследования
        elif self.state == "combat":
            # Если враг исчез, возвращаемся к патрулю
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0

    def _combat_step(self, game_map):
        """
        Один шаг боевого поведения с ограничением преследования

        Args:
            game_map: Объект карты игры
        """
        # Если нет цели или цель мертва, возвращаемся к патрулю
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем лимит преследования (8 ходов)
        if self.pursuit_counter >= self.max_pursuit_steps:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
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
                    self.pursuit_counter = 0
        else:
            # Двигаемся к цели и увеличиваем счетчик преследования
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=30)
            if (dx != 0 or dy != 0) and self.consume_stamina():
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy
                    self.pursuit_counter += 1  # Увеличиваем счетчик преследования

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

        # Модификация статов для торговца: средние характеристики, низкий дух
        self._adjust_merchant_stats()

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

    def _adjust_merchant_stats(self):
        """Модификация статов для торговца - не боец, не маг"""
        # Немного повышаем удачу (торговая жилка)
        self.luck = int(self.luck * 1.3)

        # Снижаем боевые характеристики
        self.strength = max(1, int(self.strength * 0.7))
        self.dexterity = max(1, int(self.dexterity * 0.8))

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.4))
        self.intelligence = max(1, int(self.intelligence * 0.8))

        # Обновляем производные статы
        self.update_derived_stats()

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

        # Всегда добавляем инструменты (кирки и топоры)
        self.inventory.add_item(PREDEFINED_ITEMS["basic_pickaxe"], random.randint(1, 3))
        self.inventory.add_item(PREDEFINED_ITEMS["basic_axe"], random.randint(1, 3))

        # Генерируем оружие (2-4 штуки) с ограничением качества для магазина
        for _ in range(random.randint(2, 4)):
            quality = ItemGenerator.generate_quality_for_shop()
            weapon = ItemGenerator.generate_weapon(self.level, quality=quality)
            self.inventory.add_item(weapon, 1)

        # Генерируем доспехи (3-6 штук) с ограничением качества для магазина
        for _ in range(random.randint(3, 6)):
            quality = ItemGenerator.generate_quality_for_shop()
            armor = ItemGenerator.generate_armor(self.level, quality=quality)
            self.inventory.add_item(armor, 1)

        # Генерируем украшения (1-3 штуки) с ограничением качества для магазина
        for _ in range(random.randint(1, 3)):
            quality = ItemGenerator.generate_quality_for_shop()
            jewelry = ItemGenerator.generate_jewelry(self.level, quality=quality)
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

        # Пополняем инструменты если их мало (кирки и топоры)
        if random.random() < 0.6:  # 60% шанс пополнить инструменты
            self.inventory.add_item(PREDEFINED_ITEMS["basic_pickaxe"], 1)
            self.inventory.add_item(PREDEFINED_ITEMS["basic_axe"], 1)

        if random.random() < 0.5:  # 50% шанс добавить оружие
            quality = ItemGenerator.generate_quality_for_shop()
            weapon = ItemGenerator.generate_weapon(self.level, quality=quality)
            self.inventory.add_item(weapon, 1)

        if random.random() < 0.5:  # 50% шанс добавить доспех
            quality = ItemGenerator.generate_quality_for_shop()
            armor = ItemGenerator.generate_armor(self.level, quality=quality)
            self.inventory.add_item(armor, 1)

        if random.random() < 0.3:  # 30% шанс добавить украшение
            quality = ItemGenerator.generate_quality_for_shop()
            jewelry = ItemGenerator.generate_jewelry(self.level, quality=quality)
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


class MagicMerchant(Merchant):
    """Класс Торговца магическими книгами для академии магии"""

    def __init__(self, name, x=0, y=0, level=5):
        """
        Инициализация Торговца книгами магии

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
        """
        super().__init__(name, x, y, level)
        # Торговец магией не путешествует
        self.state = "rest"
        self.settlements = []
        # Перегенерируем товары для магического торговца
        self._generate_magic_goods()

    def _generate_magic_goods(self):
        """Генерация товаров магического торговца (только книги и магические предметы)"""
        from game.inventory import PREDEFINED_ITEMS, ItemGenerator

        # Очищаем стандартные товары
        self.inventory.items.clear()

        # Увеличенное золото для скупки (больше для дорогих книг)
        self.inventory.gold = random.randint(2000, 5000) + self.level * 200

        # Книги магических умений (всегда в наличии)
        magic_books = ["book_heal", "book_regeneration"]
        for book_id in magic_books:
            if book_id in PREDEFINED_ITEMS:
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # Книги боевых умений (1-2 случайных)
        combat_books = ["book_power_strike", "book_poison_strike", "book_stun_strike", "book_battle_cry"]
        for book_id in random.sample(combat_books, random.randint(1, 2)):
            if book_id in PREDEFINED_ITEMS:
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # Книги атакующей магии (очень дорогие, всегда в наличии)
        attack_magic_books = ["book_magic_missile", "book_ice_bolt", "book_fireball", "book_lightning"]
        for book_id in attack_magic_books:
            if book_id in PREDEFINED_ITEMS:
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # Зелья маны (много)
        self.inventory.add_item(PREDEFINED_ITEMS["minor_mana_potion"], random.randint(5, 10))
        self.inventory.add_item(PREDEFINED_ITEMS["mana_potion"], random.randint(3, 6))

        # Магические кристаллы
        self.inventory.add_item(PREDEFINED_ITEMS["magic_crystal"], random.randint(2, 5))

        # Магические украшения (1-3 штуки) с ограничением качества для магазина
        for _ in range(random.randint(1, 3)):
            quality = ItemGenerator.generate_quality_for_shop()
            jewelry = ItemGenerator.generate_jewelry(self.level + 2, quality=quality)
            self.inventory.add_item(jewelry, 1)

    def restock_goods(self):
        """Пополнение товаров магического торговца"""
        from game.inventory import PREDEFINED_ITEMS, ItemGenerator

        # Добавляем золото (больше для скупки дорогих предметов)
        self.inventory.gold += random.randint(500, 1000)

        # 50% шанс добавить книгу обычного умения
        if random.random() < 0.5:
            all_books = ["book_heal", "book_regeneration", "book_power_strike",
                        "book_poison_strike", "book_stun_strike", "book_battle_cry"]
            book_id = random.choice(all_books)
            if book_id in PREDEFINED_ITEMS:
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # 30% шанс добавить книгу атакующей магии (дорогую)
        if random.random() < 0.3:
            attack_books = ["book_magic_missile", "book_ice_bolt", "book_fireball", "book_lightning"]
            book_id = random.choice(attack_books)
            if book_id in PREDEFINED_ITEMS:
                self.inventory.add_item(PREDEFINED_ITEMS[book_id], 1)

        # Всегда добавляем зелья маны
        self.inventory.add_item(PREDEFINED_ITEMS["minor_mana_potion"], random.randint(2, 4))

        # 40% шанс добавить украшение с ограничением качества для магазина
        if random.random() < 0.4:
            quality = ItemGenerator.generate_quality_for_shop()
            jewelry = ItemGenerator.generate_jewelry(self.level + 2, quality=quality)
            self.inventory.add_item(jewelry, 1)

    def update_ai(self, game_map, all_npcs=None):
        """Магический торговец не перемещается"""
        # Восстанавливаем энергию стоя на месте
        if self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + 2)


class MagePatrol(NPC):
    """Класс Мага-патрульного с AI патрулирования территории академии"""

    def __init__(self, name, x=0, y=0, level=8, academy_x=None, academy_y=None):
        """
        Инициализация Мага-патрульного

        Args:
            name: Имя мага
            x: Позиция X
            y: Позиция Y
            level: Уровень мага
            academy_x: Координата X академии
            academy_y: Координата Y академии
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_MAGE, level=level)

        # Модификация статов для мага: высокие интеллект и дух, низкие сила и ловкость
        self._adjust_mage_stats()

        # Генерация магических товаров для торговли
        self._generate_magical_goods()

        # AI параметры
        self.state = "patrol"  # patrol, rest, combat
        self.academy_x = academy_x if academy_x is not None else x  # Позиция академии
        self.academy_y = academy_y if academy_y is not None else y
        self.max_distance_from_academy = 20  # Радиус патрулирования от академии
        self.rest_counter = 0
        self.rest_duration = random.randint(2, 4)  # Отдых 2-4 часа
        self.steps_per_hour = 1  # Шагов за час
        self.patrol_point_index = 0
        self.patrol_points = self._generate_patrol_points()
        self.target_enemy = None  # Текущий враг для атаки
        self.detection_range = 12  # Дальность обнаружения врагов
        self.pursuit_counter = 0  # Счетчик ходов преследования
        self.max_pursuit_steps = 6  # Маги не любят долго преследовать

    def _adjust_mage_stats(self):
        """Модификация статов для мага - заклинатель, не воин"""
        # Значительно повышаем магические характеристики
        self.intelligence = int(self.intelligence * 1.8)
        self.spirit = int(self.spirit * 1.6)

        # Значительно снижаем боевые характеристики
        self.strength = max(1, int(self.strength * 0.4))
        self.dexterity = max(1, int(self.dexterity * 0.5))

        # Телосложение немного снижаем
        self.constitution = max(1, int(self.constitution * 0.7))

        # Обновляем производные статы
        self.update_derived_stats()

        # Обновляем ману на основе духа
        self.max_mana = self.spirit * 10
        self.mana = self.max_mana

    def _generate_magical_goods(self):
        """Генерация магических товаров для продажи"""
        from game.inventory import PREDEFINED_ITEMS, ItemGenerator

        # Стартовое золото
        self.inventory.add_gold(500 + self.level * 50)

        # Книги лечебной магии
        self.inventory.add_item(PREDEFINED_ITEMS["book_heal"], 1)

        if self.level >= 5:
            self.inventory.add_item(PREDEFINED_ITEMS["book_regeneration"], 1)

        # Книги атакующей магии (зависят от уровня мага)
        if self.level >= 8:
            self.inventory.add_item(PREDEFINED_ITEMS["book_magic_missile"], 1)

        if self.level >= 12:
            if random.random() < 0.5:
                self.inventory.add_item(PREDEFINED_ITEMS["book_ice_bolt"], 1)

        if self.level >= 15:
            if random.random() < 0.3:
                self.inventory.add_item(PREDEFINED_ITEMS["book_fireball"], 1)

        if self.level >= 20:
            if random.random() < 0.1:
                self.inventory.add_item(PREDEFINED_ITEMS["book_lightning"], 1)

        # Зелья маны
        self.inventory.add_item(PREDEFINED_ITEMS["minor_mana_potion"], random.randint(2, 4))
        if self.level >= 10:
            self.inventory.add_item(PREDEFINED_ITEMS["mana_potion"], random.randint(1, 2))

        # Магические украшения
        if random.random() < 0.5:
            jewelry = ItemGenerator.generate_jewelry(self.level)
            self.inventory.add_item(jewelry, 1)

    def _generate_patrol_points(self):
        """Генерация точек патрулирования вокруг академии"""
        points = []
        # Создаем квадратный маршрут вокруг академии
        offsets = [
            (-8, -8), (0, -8), (8, -8),
            (8, 0), (8, 8),
            (0, 8), (-8, 8),
            (-8, 0)
        ]
        for dx, dy in offsets:
            points.append((self.academy_x + dx, self.academy_y + dy))
        return points

    def update_ai(self, game_map, all_npcs=None, player=None):
        """
        Обновление AI мага за 1 час игрового времени

        Args:
            game_map: Объект карты игры
            all_npcs: Список всех NPC для поиска врагов
            player: Объект игрока
        """
        if not self.is_alive:
            return

        # Восстанавливаем выносливость и ману
        self.recover_stamina()
        if self.mana < self.max_mana:
            self.mana = min(self.max_mana, self.mana + 3)  # Медленное восстановление маны

        # Если отдыхаем из-за выносливости, ничего не делаем
        if self.is_resting:
            return

        # Проверяем наличие врагов поблизости
        if all_npcs or player:
            self._check_for_enemies(all_npcs, player)

        if self.state == "combat":
            self._combat_step(game_map)
        elif self.state == "patrol":
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
        Маги враждебны к бандитам и нежити

        Args:
            all_npcs: Список всех NPC
            player: Объект игрока
        """
        # Ищем ближайшего врага
        closest_enemy = None
        closest_distance = float('inf')

        if all_npcs:
            for npc in all_npcs:
                if not npc.is_alive:
                    continue

                # Маги враждебны к бандитам и нежити
                if npc.npc_type in [NPC_TYPE_BANDIT, NPC_TYPE_UNDEAD]:
                    distance = abs(self.x - npc.x) + abs(self.y - npc.y)
                    if distance <= self.detection_range and distance < closest_distance:
                        closest_enemy = npc
                        closest_distance = distance

        # Если нашли врага, переходим в боевой режим
        if closest_enemy:
            self.target_enemy = closest_enemy
            self.state = "combat"
            self.pursuit_counter = 0
        elif self.state == "combat":
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0

    def _combat_step(self, game_map):
        """
        Один шаг боевого поведения

        Args:
            game_map: Объект карты игры
        """
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем лимит преследования
        if self.pursuit_counter >= self.max_pursuit_steps:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем расстояние до академии
        distance_to_academy = abs(self.x - self.academy_x) + abs(self.y - self.academy_y)
        if distance_to_academy > self.max_distance_from_academy:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.target_enemy):
            # Атакуем
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
                    self.pursuit_counter = 0
        else:
            # Двигаемся к цели
            dx, dy = self._find_next_step(self.target_enemy.x, self.target_enemy.y, game_map, max_search_distance=20)
            if (dx != 0 or dy != 0) and self.consume_stamina():
                new_x = self.x + dx
                new_y = self.y + dy

                distance_to_academy_new = abs(new_x - self.academy_x) + abs(new_y - self.academy_y)
                if distance_to_academy_new <= self.max_distance_from_academy:
                    if self._can_move(new_x, new_y, game_map):
                        self.x = new_x
                        self.y = new_y
                        self.pursuit_counter += 1
                else:
                    self.target_enemy = None
                    self.state = "patrol"
                    self.pursuit_counter = 0

    def _patrol_step(self, game_map):
        """Один шаг патрулирования территории академии"""
        # Проверяем расстояние до академии
        distance_to_academy = abs(self.x - self.academy_x) + abs(self.y - self.academy_y)

        # Если слишком далеко от академии, возвращаемся
        if distance_to_academy > self.max_distance_from_academy:
            dx, dy = self._find_next_step(self.academy_x, self.academy_y, game_map, max_search_distance=20)
            if dx != 0 or dy != 0:
                if self._can_move(self.x + dx, self.y + dy, game_map):
                    self.x += dx
                    self.y += dy
            return

        # Получаем текущую точку патрулирования
        if not self.patrol_points:
            return

        target_x, target_y = self.patrol_points[self.patrol_point_index]

        # Если достигли точки, переходим к следующей
        if self.x == target_x and self.y == target_y:
            self.patrol_point_index = (self.patrol_point_index + 1) % len(self.patrol_points)
            # Небольшой шанс отдохнуть
            if random.random() < 0.1:
                self.state = "rest"
                self.rest_counter = 0
            return

        # Двигаемся к точке патрулирования
        dx, dy = self._find_next_step(target_x, target_y, game_map, max_search_distance=15)
        if dx != 0 or dy != 0:
            new_x = self.x + dx
            new_y = self.y + dy
            if self._can_move(new_x, new_y, game_map):
                self.x = new_x
                self.y = new_y
        else:
            # Если не можем достичь точки, переходим к следующей
            self.patrol_point_index = (self.patrol_point_index + 1) % len(self.patrol_points)

    def _rest(self):
        """Отдых мага"""
        self.rest_counter += 1
        # Усиленное восстановление маны во время отдыха
        if self.mana < self.max_mana:
            self.mana = min(self.max_mana, self.mana + 5)

        if self.rest_counter >= self.rest_duration:
            self.state = "patrol"
            self.rest_counter = 0
            self.rest_duration = random.randint(2, 4)

    def _can_move(self, x, y, game_map):
        """Проверить, можно ли переместиться в указанную позицию"""
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

        # Модификация статов для бандита: боец с низким духом
        self._adjust_bandit_stats()

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
        self.pursuit_counter = 0  # Счетчик ходов преследования
        self.max_pursuit_steps = 8  # Максимальное количество ходов преследования

    def _adjust_bandit_stats(self):
        """Модификация статов для бандита - агрессивный боец"""
        # Повышаем боевые характеристики
        self.strength = int(self.strength * 1.2)
        self.dexterity = int(self.dexterity * 1.15)

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.35))
        self.intelligence = max(1, int(self.intelligence * 0.5))

        # Обновляем производные статы
        self.update_derived_stats()

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

                # Пропускаем самого себя
                if npc is self:
                    continue

                # Бандиты не атакуют других бандитов
                if npc.npc_type == NPC_TYPE_BANDIT:
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
            self.pursuit_counter = 0  # Сбрасываем счетчик преследования
        elif self.state == "combat":
            # Если враг исчез, возвращаемся к патрулю
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0

    def _combat_step(self, game_map):
        """
        Один шаг боевого поведения с ограничением преследования

        Args:
            game_map: Объект карты игры
        """
        # Если нет цели или цель мертва, возвращаемся к патрулю
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем лимит преследования (8 ходов)
        if self.pursuit_counter >= self.max_pursuit_steps:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем расстояние до лагеря
        distance_to_camp = abs(self.x - self.camp_x) + abs(self.y - self.camp_y)

        # Если слишком далеко от лагеря, возвращаемся
        if distance_to_camp > self.max_distance_from_camp:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.target_enemy):
            # Если цель - игрок, устанавливаем флаг для открытия интерфейса боя вместо прямой атаки
            if hasattr(self.target_enemy, 'attacked_by_npc'):
                self.target_enemy.attacked_by_npc = self
                # Не атакуем игрока напрямую, ждем открытия интерфейса боя
                return

            # Атакуем только NPC
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
                    self.pursuit_counter = 0
        else:
            # Двигаемся к цели и увеличиваем счетчик преследования
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
                        self.pursuit_counter += 1  # Увеличиваем счетчик преследования
                else:
                    # Слишком далеко, прекращаем преследование
                    self.target_enemy = None
                    self.state = "patrol"
                    self.pursuit_counter = 0

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

        # Модификация статов для шахтера: физический труд, низкий дух
        self._adjust_miner_stats()

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

    def _adjust_miner_stats(self):
        """Модификация статов для шахтера - физический труженик"""
        # Повышаем физические характеристики
        self.strength = int(self.strength * 1.2)
        self.constitution = int(self.constitution * 1.3)

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.35))
        self.intelligence = max(1, int(self.intelligence * 0.6))

        # Немного снижаем ловкость
        self.dexterity = max(1, int(self.dexterity * 0.9))

        # Обновляем производные статы
        self.update_derived_stats()

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
        self.max_distance_from_ruins = 15  # Увеличено с 7 до 15 - больше радиус патруля
        self.rest_counter = 0
        self.rest_duration = random.randint(2, 3)  # Отдых 2-3 часа
        self.steps_per_hour = 2  # Увеличено с 1 до 2 - нежить быстрее передвигается
        self.target_enemy = None  # Текущая цель для атаки
        self.detection_range = 15  # Увеличено с 12 до 15 - лучше видят врагов
        self.wander_target = None  # Целевая точка для патруля
        self.pursuit_counter = 0  # Счетчик ходов преследования
        self.max_pursuit_steps = 10  # Увеличено с 8 до 10 - дольше преследуют

    def update_ai(self, game_map, all_npcs=None, player=None):
        """
        Обновление AI нежити за 1 час игрового времени
        АКТИВИРОВАНА система патруля и агрессии

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

        # Проверяем других NPC (нежита агрессивна ко всем, кроме другой нежити!)
        if all_npcs:
            for npc in all_npcs:
                if not npc.is_alive:
                    continue

                # Нежита не атакует другую нежить
                if npc.npc_type == NPC_TYPE_UNDEAD:
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
            self.pursuit_counter = 0  # Сбрасываем счетчик преследования
        elif self.state == "combat":
            # Если враг исчез, возвращаемся к патрулю
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0

    def _combat_step(self, game_map):
        """
        Один шаг боевого поведения с ограничением преследования

        Args:
            game_map: Объект карты игры
        """
        # Если нет цели или цель мертва, возвращаемся к патрулю
        if not self.target_enemy or not self.target_enemy.is_alive:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем лимит преследования (8 ходов)
        if self.pursuit_counter >= self.max_pursuit_steps:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем расстояние до руин
        distance_to_ruins = abs(self.x - self.ruins_x) + abs(self.y - self.ruins_y)

        # Если слишком далеко от руин, возвращаемся
        if distance_to_ruins > self.max_distance_from_ruins:
            self.target_enemy = None
            self.state = "patrol"
            self.pursuit_counter = 0
            return

        # Проверяем, можем ли атаковать
        if self.can_attack(self.target_enemy):
            # Если цель - игрок, устанавливаем флаг для открытия интерфейса боя вместо прямой атаки
            if hasattr(self.target_enemy, 'attacked_by_npc'):
                self.target_enemy.attacked_by_npc = self
                # Не атакуем игрока напрямую, ждем открытия интерфейса боя
                return

            # Атакуем только NPC
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
                    self.pursuit_counter = 0
        else:
            # Двигаемся к цели и увеличиваем счетчик преследования
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
                        self.pursuit_counter += 1  # Увеличиваем счетчик преследования
                else:
                    # Слишком далеко, прекращаем преследование
                    self.target_enemy = None
                    self.state = "patrol"
                    self.pursuit_counter = 0

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
