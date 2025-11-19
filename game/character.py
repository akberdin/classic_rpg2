"""
Классы персонажей (игрок и базовый класс Character)

NPC классы вынесены в отдельный пакет game.npc:
- from game.npc import NPC, Guard, Merchant, MagicMerchant, MagePatrol, Bandit, Miner, Undead
"""
import random
from game.inventory import Inventory
from game.constants import (
    MAX_LEVEL, RANKS,
    STAMINA_PER_STAT_POINT, STAMINA_COST_PER_MOVE, STAMINA_REST_MIN, STAMINA_REST_MAX,
    COMBAT_RANGE, DODGE_BASE_CHANCE, CRIT_BASE_CHANCE
)

__all__ = ['Character', 'Player']


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

        # Учитываем защиту цели с улучшенными diminishing returns
        target_defense = target.get_total_defense()

        # Улучшенные diminishing returns для баланса:
        # - Soft cap снижен до 30 для раннего ограничения
        # - После soft cap защита работает на 40%
        # - Это предотвращает ситуации когда броня полностью блокирует урон
        defense_soft_cap = 30
        if target_defense > defense_soft_cap:
            effective_defense = defense_soft_cap + (target_defense - defense_soft_cap) * 0.4
        else:
            effective_defense = target_defense

        # Защита снижает урон, но не может снизить его ниже 15% от базового урона
        min_damage = max(1, int(total_damage * 0.15))
        actual_damage = max(min_damage, total_damage - int(effective_defense))
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

        # Обновляем максимальную ману (пропорционально увеличиваем текущую)
        old_max_mana = getattr(self, 'max_mana', 0)
        self.max_mana = self.spirit * 10
        if old_max_mana > 0:
            mana_diff = self.max_mana - old_max_mana
            self.mana = min(self.max_mana, self.mana + mana_diff)
        else:
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

            # Обновляем максимальную ману если изменился дух (пропорционально)
            if stat_name == 'spirit':
                old_max_mana = self.max_mana
                self.max_mana = self.spirit * 10
                mana_diff = self.max_mana - old_max_mana
                self.mana = min(self.max_mana, self.mana + mana_diff)

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
