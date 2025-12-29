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

        # Временные бонусы от эффектов
        self.temp_strength_boost = 0

        # Состояния в бою
        self.stunned = False  # Флаг оглушения

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
        # Сохраняем текущие проценты от эффективных максимумов (для учета бонусов от экипировки)
        old_effective_max_stamina = self.get_effective_max_stamina() if hasattr(self, 'get_effective_max_stamina') else self.max_stamina
        old_effective_max_health = self.get_effective_max_health() if hasattr(self, 'get_effective_max_health') else self.max_health

        stamina_percent = self.stamina / old_effective_max_stamina if old_effective_max_stamina > 0 else 1.0
        health_percent = self.health / old_effective_max_health if old_effective_max_health > 0 else 1.0

        # Выносливость = (сила + телосложение) * 10
        old_max_stamina = self.max_stamina
        self.max_stamina = (self.strength + self.constitution) * STAMINA_PER_STAT_POINT

        # Восстанавливаем выносливость на основе сохраненного процента от нового эффективного максимума
        if old_max_stamina > 0:
            new_effective_max_stamina = self.get_effective_max_stamina() if hasattr(self, 'get_effective_max_stamina') else self.max_stamina
            self.stamina = min(int(new_effective_max_stamina * stamina_percent), new_effective_max_stamina)
        else:
            self.stamina = self.max_stamina

        # Устанавливаем порог отдыха (60-80% от максимальной выносливости)
        rest_percent = random.uniform(STAMINA_REST_MIN, STAMINA_REST_MAX)
        self.rest_threshold = int(self.max_stamina * rest_percent)

        # Здоровье = телосложение * 20
        old_max_health = self.max_health
        self.max_health = self.constitution * 20

        # Восстанавливаем здоровье на основе сохраненного процента от нового эффективного максимума
        if old_max_health > 0:
            new_effective_max_health = self.get_effective_max_health() if hasattr(self, 'get_effective_max_health') else self.max_health
            self.health = min(int(new_effective_max_health * health_percent), new_effective_max_health)
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

        # Добавляем процентный бонус от param_bonus (округляем до целого)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_total_param_bonus'):
            param_bonus = self.inventory.get_total_param_bonus()
            health_percent_bonus = param_bonus.get('health', 0)
            if health_percent_bonus > 0:
                base_max_health = int(base_max_health * (1 + health_percent_bonus / 100))

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

        base_max_stamina = (base_strength + base_constitution) * STAMINA_PER_STAT_POINT

        # Добавляем процентный бонус от param_bonus (округляем до целого)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_total_param_bonus'):
            param_bonus = self.inventory.get_total_param_bonus()
            stamina_percent_bonus = param_bonus.get('stamina', 0)
            if stamina_percent_bonus > 0:
                base_max_stamina = int(base_max_stamina * (1 + stamina_percent_bonus / 100))

        return base_max_stamina

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

        # Грузоподъемность = 30 + сила * 10
        return 30 + base_strength * 10

    def _get_effective_stat(self, stat_name):
        """
        Универсальный метод получения эффективного значения характеристики
        с учетом бонусов от экипировки

        Args:
            stat_name: Название характеристики (strength, dexterity, constitution, spirit, intelligence, luck)

        Returns:
            int: Эффективное значение характеристики
        """
        base_value = getattr(self, stat_name, 0)

        # Добавляем бонусы от экипировки
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_total_stats_bonus'):
            equipment_bonus = self.inventory.get_total_stats_bonus()
            base_value += equipment_bonus.get(stat_name, 0)

        return base_value

    def get_effective_strength(self):
        """Получить эффективную силу с учетом бонусов от экипировки"""
        return self._get_effective_stat('strength')

    def get_effective_intelligence(self):
        """Получить эффективный интеллект с учетом бонусов от экипировки"""
        return self._get_effective_stat('intelligence')

    def get_effective_spirit(self):
        """Получить эффективный дух с учетом бонусов от экипировки"""
        return self._get_effective_stat('spirit')

    def get_effective_dexterity(self):
        """Получить эффективную ловкость с учетом бонусов от экипировки"""
        return self._get_effective_stat('dexterity')

    def get_effective_constitution(self):
        """Получить эффективное телосложение с учетом бонусов от экипировки"""
        return self._get_effective_stat('constitution')

    def get_effective_luck(self):
        """Получить эффективную удачу с учетом бонусов от экипировки"""
        return self._get_effective_stat('luck')

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
        # Получаем эффективное значение с учетом экипировки
        effective_max_stamina = self.get_effective_max_stamina()

        if self.stamina < effective_max_stamina:
            # Получаем эффективную ловкость с учетом экипировки
            effective_dexterity = self.get_effective_dexterity()

            # При активном отдыхе восстанавливаем на основе ловкости
            if is_active_rest:
                # Каждая единица ловкости повышает скорость восстановления на 0.5% от максимума
                recovery = max(1, int(effective_max_stamina * effective_dexterity * 0.005))
            else:
                # При обычном движении восстановления нет (только отдых)
                recovery = 0

            self.stamina = min(effective_max_stamina, self.stamina + recovery)

            # Проверяем, достаточно ли восстановились для окончания отдыха
            if self.is_resting and self.stamina >= self.rest_threshold:
                self.is_resting = False

    def recover_health(self, is_active_rest=False):
        """
        Восстановить здоровье (вызывается каждый игровой час)

        Args:
            is_active_rest: True если это активный отдых (команда R)
        """
        # Получаем эффективное значение с учетом экипировки
        effective_max_health = self.get_effective_max_health()

        if self.health < effective_max_health:
            # Получаем эффективное телосложение с учетом экипировки
            effective_constitution = self.get_effective_constitution()

            # При активном отдыхе восстанавливаем на основе телосложения
            if is_active_rest:
                # Каждая единица телосложения повышает скорость восстановления на 0.5% от максимума
                recovery = max(1, int(effective_max_health * effective_constitution * 0.005))
            else:
                # При обычном движении восстановления нет (только отдых и зелья)
                recovery = 0

            self.health = min(effective_max_health, self.health + recovery)

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
        Использует расстояние Чебышёва для поддержки атаки в 8 направлениях

        Args:
            target: Целевой персонаж

        Returns:
            bool: True если может атаковать
        """
        if not self.is_alive or not target.is_alive:
            return False

        # Проверяем дистанцию (расстояние Чебышёва для атаки в 8 направлениях)
        # Это максимум из разностей по X и Y
        distance = max(abs(self.x - target.x), abs(self.y - target.y))
        return distance <= COMBAT_RANGE

    def _calculate_chance_with_diminishing_returns(self, stat_name, base_per_point, effect_bonus_attr):
        """
        Универсальный метод расчета шанса с diminishing returns

        Args:
            stat_name: Название характеристики (dexterity, luck)
            base_per_point: Базовый процент за единицу характеристики
            effect_bonus_attr: Название атрибута бонуса от эффектов (dodge_bonus, crit_bonus)

        Returns:
            float: Рассчитанный шанс (0-75)
        """
        # Получаем эффективное значение характеристики
        stat_value = self._get_effective_stat(stat_name)

        # Система diminishing returns:
        # Первые 10 единиц: 100% эффективности
        # 11-20 единиц: 50% эффективности
        # 21-30 единиц: 30% эффективности
        # 31+ единиц: 15% эффективности
        if stat_value <= 10:
            chance = stat_value * base_per_point
        elif stat_value <= 20:
            chance = 10 * base_per_point + (stat_value - 10) * base_per_point * 0.5
        elif stat_value <= 30:
            chance = (10 * base_per_point +
                      10 * base_per_point * 0.5 +
                      (stat_value - 20) * base_per_point * 0.3)
        else:
            chance = (10 * base_per_point +
                      10 * base_per_point * 0.5 +
                      10 * base_per_point * 0.3 +
                      (stat_value - 30) * base_per_point * 0.15)

        # Добавляем бонусы от активных эффектов
        effects_list = []
        if hasattr(self, 'skill_manager') and hasattr(self.skill_manager, 'status_effects'):
            effects_list.extend(self.skill_manager.status_effects)
        if hasattr(self, 'status_effects'):
            effects_list.extend(self.status_effects)

        for effect in effects_list:
            if hasattr(effect, effect_bonus_attr):
                chance += getattr(effect, effect_bonus_attr)

        return min(75.0, chance)  # Максимум 75%

    def calculate_dodge_chance(self):
        """
        Рассчитать шанс уворота на основе ловкости с учетом экипировки и эффектов

        Returns:
            float: Шанс уворота (0-75)
        """
        return self._calculate_chance_with_diminishing_returns(
            'dexterity', DODGE_BASE_CHANCE, 'dodge_bonus'
        )

    def calculate_crit_chance(self):
        """
        Рассчитать шанс критического удара на основе удачи с учетом экипировки и эффектов

        Returns:
            float: Шанс крита (0-75)
        """
        return self._calculate_chance_with_diminishing_returns(
            'luck', CRIT_BASE_CHANCE, 'crit_bonus'
        )

    def attack(self, target, skip_range_check=False):
        """
        Атаковать цель с учетом механики уворота и крита

        Args:
            target: Целевой персонаж
            skip_range_check: Пропустить проверку дистанции (для тактического боя)

        Returns:
            dict: Результат атаки с информацией об уроне, увороте и крите
        """
        if not skip_range_check and not self.can_attack(target):
            return {
                'damage': 0,
                'dodged': False,
                'critical': False,
                'hit': False,
                'stunned': False
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
                'hit': False,
                'stunned': False
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

        # МЕХАНИКА ИГНОРИРОВАНИЯ БРОНИ для нежити и магов
        armor_penetration = 0.0
        if hasattr(self, 'npc_type'):
            from game.constants import NPC_TYPE_UNDEAD, NPC_TYPE_MAGE
            if self.npc_type in [NPC_TYPE_UNDEAD, NPC_TYPE_MAGE]:
                # Определяем процент игнорирования брони по рангу
                attacker_level = getattr(self, 'level', 1)
                if 1 <= attacker_level <= 10:  # Новичок
                    armor_penetration = 0.10
                elif 11 <= attacker_level <= 20:  # Обычный
                    armor_penetration = 0.20
                elif 21 <= attacker_level <= 30:  # Опытный
                    armor_penetration = 0.30
                elif 31 <= attacker_level <= 40:  # Эксперт
                    armor_penetration = 0.40

        # Применяем игнорирование брони
        effective_target_defense = target_defense * (1.0 - armor_penetration)

        # Улучшенные diminishing returns для баланса:
        # - Soft cap снижен до 30 для раннего ограничения
        # - После soft cap защита работает на 40%
        # - Это предотвращает ситуации когда броня полностью блокирует урон
        defense_soft_cap = 30
        if effective_target_defense > defense_soft_cap:
            effective_defense = defense_soft_cap + (effective_target_defense - defense_soft_cap) * 0.4
        else:
            effective_defense = effective_target_defense

        # Защита снижает урон, но не может снизить его ниже 15% от базового урона
        min_damage = max(1, int(total_damage * 0.15))
        actual_damage = max(min_damage, total_damage - int(effective_defense))
        blocked_by_armor = max(0, total_damage - actual_damage)

        # МЕХАНИКА ОГЛУШЕНИЯ для бандитов
        stunned = False
        if hasattr(self, 'npc_type'):
            from game.constants import NPC_TYPE_BANDIT
            if self.npc_type == NPC_TYPE_BANDIT:
                # Определяем шанс оглушения по рангу
                attacker_level = getattr(self, 'level', 1)
                stun_chance = 0.0
                if 1 <= attacker_level <= 10:  # Новичок
                    stun_chance = 5.0
                elif 11 <= attacker_level <= 20:  # Обычный
                    stun_chance = 7.0
                elif 21 <= attacker_level <= 30:  # Опытный
                    stun_chance = 10.0
                elif 31 <= attacker_level <= 40:  # Эксперт
                    stun_chance = 15.0

                # Проверяем оглушение
                stun_roll = random.uniform(0, 100)
                if stun_roll < stun_chance:
                    stunned = True
                    # Применяем оглушение к цели (пропуск 1 хода)
                    if hasattr(target, 'stunned'):
                        target.stunned = True

        # Применяем урон
        damage_result = target.take_damage(actual_damage)

        return {
            'damage': damage_result['damage'],
            'blocked_by_armor': blocked_by_armor,
            'armor_penetration_percent': int(armor_penetration * 100) if armor_penetration > 0 else 0,
            'blocked_by_godmode': damage_result['blocked'] if damage_result['godmode'] else 0,
            'godmode': damage_result['godmode'],
            'dodged': False,
            'critical': is_critical,
            'hit': True,
            'stunned': stunned
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

        # Добавляем бонусы от активных эффектов (например, Щит мага)
        # Проверяем эффекты в skill_manager (для игрока) и в status_effects (для NPC)
        effects_list = []
        if hasattr(self, 'skill_manager') and hasattr(self.skill_manager, 'status_effects'):
            effects_list.extend(self.skill_manager.status_effects)
        if hasattr(self, 'status_effects'):
            effects_list.extend(self.status_effects)

        for effect in effects_list:
            if hasattr(effect, 'defense_bonus'):
                # defense_bonus в процентах, применяем к total_defense
                total_defense = int(total_defense * (1 + effect.defense_bonus / 100))
            # Учитываем также отрицательные эффекты (например, Сломленная броня)
            if hasattr(effect, 'defense_reduction'):
                total_defense = max(0, total_defense - effect.defense_reduction)

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

    def get_rank_number(self):
        """
        Получить числовой ранг персонажа на основе уровня

        Returns:
            int: Числовой ранг (1-4)
        """
        level = getattr(self, 'level', 1)
        if level <= 10:
            return 1
        elif level <= 20:
            return 2
        elif level <= 30:
            return 3
        else:
            return 4


# Player вынесен в отдельный модуль, импортируем для обратной совместимости
from game.entities.player import Player
