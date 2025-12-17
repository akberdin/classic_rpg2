"""
Система ловушек для подземелий
"""
import random
from enum import Enum
from typing import List, Tuple, Optional


class TrapType(Enum):
    """Типы ловушек"""
    SPIKE = "spike"            # Шипы - физический урон
    POISON_GAS = "poison_gas"  # Ядовитый газ - урон ядом со временем
    FIRE = "fire"              # Огненная ловушка - урон огнем
    ARROW = "arrow"            # Стрелы - физический урон
    PIT = "pit"                # Яма - падение, большой урон
    CURSE = "curse"            # Проклятие - дебафф


class TrapLevel(Enum):
    """Уровни ловушек"""
    PRIMITIVE = 1      # Примитивная
    COMMON = 2         # Обычная
    SKILLED = 3        # Искусная
    MASTERWORK = 4     # Мастерская
    LEGENDARY = 5      # Легендарная


# Параметры уровней ловушек
TRAP_LEVEL_DATA = {
    TrapLevel.PRIMITIVE: {
        "name": "Примитивная",
        "damage_multiplier": 0.7,    # 70% базового урона
        "dc_modifier": -2,            # -2 к DC обнаружения и обезвреживания
        "trigger_chance": 0.80,       # 80% шанс сработать
        "anti_disarm_damage": 0.0,    # Нет анти-обезвреживания
    },
    TrapLevel.COMMON: {
        "name": "Обычная",
        "damage_multiplier": 1.0,     # 100% базового урона
        "dc_modifier": 0,             # Базовый DC
        "trigger_chance": 0.85,
        "anti_disarm_damage": 0.0,
    },
    TrapLevel.SKILLED: {
        "name": "Искусная",
        "damage_multiplier": 1.4,     # 140% базового урона
        "dc_modifier": 4,             # +4 к DC
        "trigger_chance": 0.90,
        "anti_disarm_damage": 0.3,    # 30% урона при провале обезвреживания
        "secondary_effect": True,      # Дополнительный эффект
    },
    TrapLevel.MASTERWORK: {
        "name": "Мастерская",
        "damage_multiplier": 1.8,     # 180% базового урона
        "dc_modifier": 8,             # +8 к DC
        "trigger_chance": 0.95,
        "anti_disarm_damage": 0.5,    # 50% урона при провале
        "secondary_effect": True,
        "aoe_effect": True,           # Эффект на область
    },
    TrapLevel.LEGENDARY: {
        "name": "Легендарная",
        "damage_multiplier": 2.5,     # 250% базового урона
        "dc_modifier": 13,            # +13 к DC
        "trigger_chance": 1.0,        # Всегда срабатывает
        "anti_disarm_damage": 0.8,    # 80% урона при провале
        "secondary_effect": True,
        "aoe_effect": True,
        "triple_effect": True,        # Тройной эффект
    },
}

# Параметры ловушек
TRAP_DATA = {
    TrapType.SPIKE: {
        "name": "Шипы",
        "description": "Острые шипы выскакивают из пола",
        "base_damage": 15,
        "damage_type": "physical",
        "detection_dc": 10,  # Сложность обнаружения
        "disarm_dc": 12,     # Сложность обезвреживания
        "weight": 30,        # Вес для генерации (шанс появления)
    },
    TrapType.POISON_GAS: {
        "name": "Ядовитый газ",
        "description": "Облако ядовитого газа вырывается из щелей",
        "base_damage": 10,
        "damage_type": "poison",
        "poison_duration": 3,  # Ходов отравления
        "poison_damage": 5,    # Урон за ход
        "detection_dc": 14,
        "disarm_dc": 16,
        "weight": 15,
    },
    TrapType.FIRE: {
        "name": "Огненная ловушка",
        "description": "Струя пламени вырывается из стены",
        "base_damage": 25,
        "damage_type": "fire",
        "detection_dc": 12,
        "disarm_dc": 14,
        "weight": 20,
    },
    TrapType.ARROW: {
        "name": "Ловушка со стрелами",
        "description": "Отравленные стрелы вылетают из стены",
        "base_damage": 20,
        "damage_type": "physical",
        "detection_dc": 8,
        "disarm_dc": 10,
        "weight": 25,
    },
    TrapType.PIT: {
        "name": "Скрытая яма",
        "description": "Пол проваливается под ногами",
        "base_damage": 30,
        "damage_type": "physical",
        "detection_dc": 6,
        "disarm_dc": 8,
        "weight": 10,
    },
    TrapType.CURSE: {
        "name": "Проклятие",
        "description": "Древнее проклятие ослабляет вас",
        "base_damage": 0,
        "damage_type": "curse",
        "curse_effect": "weakness",  # Тип проклятия
        "curse_duration": 10,        # Длительность в ходах
        "detection_dc": 18,
        "disarm_dc": 20,
        "weight": 5,
    },
}


class Trap:
    """Класс ловушки"""

    def __init__(self, x: int, y: int, trap_type: TrapType, dungeon_level: int = 1,
                 trap_level: TrapLevel = TrapLevel.COMMON):
        """
        Создать ловушку

        Args:
            x: Координата X
            y: Координата Y
            trap_type: Тип ловушки
            dungeon_level: Уровень подземелья (влияет на урон)
            trap_level: Уровень ловушки (1-5)
        """
        self.x = x
        self.y = y
        self.trap_type = trap_type
        self.dungeon_level = dungeon_level
        self.trap_level = trap_level

        # Данные типа ловушки
        trap_data = TRAP_DATA.get(trap_type, TRAP_DATA[TrapType.SPIKE])
        self.name = trap_data["name"]
        self.description = trap_data["description"]
        self.damage_type = trap_data["damage_type"]

        # Данные уровня ловушки
        level_data = TRAP_LEVEL_DATA[trap_level]
        self.level_name = level_data["name"]
        self.trigger_chance = level_data["trigger_chance"]
        self.anti_disarm_damage = level_data["anti_disarm_damage"]

        # Расчет DC с учетом уровня ловушки
        base_detection_dc = trap_data["detection_dc"]
        base_disarm_dc = trap_data["disarm_dc"]
        dc_modifier = level_data["dc_modifier"]

        self.detection_dc = max(1, base_detection_dc + dc_modifier)
        self.disarm_dc = max(1, base_disarm_dc + dc_modifier)

        # Расчет урона с учетом уровня ловушки и подземелья
        base_damage = trap_data["base_damage"]
        damage_multiplier = level_data["damage_multiplier"]
        dungeon_scaling = 1 + 0.1 * (dungeon_level - 1)  # +10% за уровень подземелья

        self.damage = int(base_damage * damage_multiplier * dungeon_scaling)

        # Дополнительные эффекты
        self.poison_duration = trap_data.get("poison_duration", 0)
        self.poison_damage = trap_data.get("poison_damage", 0)
        self.curse_effect = trap_data.get("curse_effect", None)
        self.curse_duration = trap_data.get("curse_duration", 0)

        # Усиление эффектов для высокоуровневых ловушек
        if level_data.get("secondary_effect", False):
            self.poison_duration = int(self.poison_duration * 1.5)
            self.poison_damage = int(self.poison_damage * 1.5)
            self.curse_duration = int(self.curse_duration * 1.5)

        # Состояние
        self.is_triggered = False
        self.is_detected = False
        self.is_disarmed = False

    def trigger(self, target) -> dict:
        """
        Активировать ловушку

        Args:
            target: Объект игрока или NPC

        Returns:
            dict: Результат срабатывания ловушки
        """
        if self.is_triggered or self.is_disarmed:
            return {"success": False, "message": "Ловушка уже сработала или обезврежена"}

        # Проверка шанса срабатывания (для высокоуровневых ловушек)
        if random.random() > self.trigger_chance:
            # Ловушка не сработала (чудом)
            return {
                "success": False,
                "message": f"Ловушка '{self.name}' не сработала!"
            }

        self.is_triggered = True

        # Определяем, игрок это или NPC
        is_player = hasattr(target, 'inventory')  # У игрока есть инвентарь

        result = {
            "success": True,
            "trap_name": self.name,
            "trap_level": self.level_name,
            "damage": 0,
            "damage_type": self.damage_type,
            "effects": [],
            "message": "",
            "target_name": getattr(target, 'name', 'Цель')
        }

        # Шанс уклонения от ловушки (зависит от ловкости)
        target_dexterity = getattr(target, 'dexterity', 5)  # Защита от отсутствия атрибута
        dodge_chance = min(50, target_dexterity * 2)
        if random.randint(1, 100) <= dodge_chance:
            if is_player:
                result["message"] = f"Вы успели увернуться от ловушки '{self.name}' ({self.level_name})!"
            else:
                result["message"] = f"{target.name} увернулся от ловушки '{self.name}' ({self.level_name})!"
            result["damage"] = 0
            return result

        # Наносим урон с учетом защиты
        base_damage = self.damage

        # Получаем защиту цели (если есть метод get_total_defense)
        defense = 0
        if hasattr(target, 'get_total_defense'):
            defense = target.get_total_defense()

        # Применяем формулу урона (аналогично бою с врагами)
        # Защита снижает урон вдвое
        actual_damage = max(1, base_damage - defense // 2)

        target.health -= actual_damage
        if target.health < 0:
            target.health = 0
        result["damage"] = actual_damage

        # Формируем сообщение с информацией о защите
        if is_player:
            if defense > 0:
                blocked = base_damage - actual_damage
                result["message"] = f"Ловушка '{self.name}' нанесла вам {actual_damage} урона (заблокировано: {blocked})!"
            else:
                result["message"] = f"Ловушка '{self.name}' нанесла вам {actual_damage} урона!"
        else:
            if defense > 0:
                blocked = base_damage - actual_damage
                result["message"] = f"Ловушка '{self.name}' нанесла {target.name} {actual_damage} урона (заблокировано: {blocked})!"
            else:
                result["message"] = f"Ловушка '{self.name}' нанесла {target.name} {actual_damage} урона!"

        # Проверяем смерть
        if target.health <= 0:
            if is_player:
                result["player_dead"] = True
                result["message"] += " Вы погибли!"
            else:
                result["target_dead"] = True
                result["message"] += f" {target.name} погиб!"
                # Помечаем NPC как мертвого
                if hasattr(target, 'is_alive'):
                    target.is_alive = False

        # Дополнительные эффекты (только для игрока, у NPC могут не быть этих методов)
        if is_player:
            if self.poison_duration > 0:
                # Применяем отравление
                if hasattr(target, 'apply_poison'):
                    target.apply_poison(self.poison_damage, self.poison_duration)
                result["effects"].append(f"Отравление на {self.poison_duration} ходов")
                result["message"] += f" Вы отравлены на {self.poison_duration} ходов!"

            if self.curse_effect:
                # Применяем проклятие
                if hasattr(target, 'apply_curse'):
                    target.apply_curse(self.curse_effect, self.curse_duration)
                result["effects"].append(f"Проклятие '{self.curse_effect}' на {self.curse_duration} ходов")
                result["message"] += f" На вас наложено проклятие!"

        return result

    def try_detect(self, player) -> bool:
        """
        Попытка обнаружить ловушку

        Args:
            player: Объект игрока

        Returns:
            bool: True если ловушка обнаружена
        """
        if self.is_detected or self.is_triggered:
            return self.is_detected

        # Проверка на обнаружение (ловкость + удача против сложности)
        detection_roll = random.randint(1, 20) + player.dexterity // 3 + player.luck // 5

        if detection_roll >= self.detection_dc:
            self.is_detected = True
            return True
        return False

    def try_disarm(self, player) -> Tuple[bool, str]:
        """
        Попытка обезвредить ловушку

        Args:
            player: Объект игрока

        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        if not self.is_detected:
            return False, "Вы не видите здесь ловушки"

        if self.is_disarmed:
            return True, "Ловушка уже обезврежена"

        if self.is_triggered:
            return False, "Ловушка уже сработала"

        # Проверка на обезвреживание
        disarm_roll = random.randint(1, 20) + player.dexterity // 2 + player.luck // 4

        if disarm_roll >= self.disarm_dc:
            self.is_disarmed = True
            return True, f"Вы успешно обезвредили ловушку '{self.name}' ({self.level_name})!"
        else:
            # Провал - анти-обезвреживание или полное срабатывание
            if self.anti_disarm_damage > 0:
                # Частичное срабатывание (анти-обезвреживание)
                damage = int(self.damage * self.anti_disarm_damage)

                # Применяем защиту
                defense = 0
                if hasattr(player, 'get_total_defense'):
                    defense = player.get_total_defense()

                actual_damage = max(1, damage - defense // 2)
                player.health -= actual_damage
                if player.health < 0:
                    player.health = 0

                message = f"Неудача! Ловушка '{self.name}' частично сработала, нанеся {actual_damage} урона!"

                # Проверка смерти
                if player.health <= 0:
                    message += " Вы погибли!"
                    return False, message

                return False, message
            else:
                # Полное срабатывание ловушки (для низкоуровневых)
                result = self.trigger(player)
                return False, f"Неудача! {result['message']}"


class TrapManager:
    """Менеджер ловушек подземелья"""

    def __init__(self):
        """Инициализация менеджера"""
        self.traps: List[Trap] = []

    def add_trap(self, trap: Trap):
        """Добавить ловушку"""
        self.traps.append(trap)

    def get_trap_at(self, x: int, y: int) -> Optional[Trap]:
        """Получить ловушку по координатам"""
        for trap in self.traps:
            if trap.x == x and trap.y == y:
                return trap
        return None

    def check_player_position(self, player) -> Optional[dict]:
        """
        Проверить, наступил ли игрок на ловушку

        Args:
            player: Объект игрока

        Returns:
            dict или None: Результат срабатывания ловушки
        """
        trap = self.get_trap_at(player.x, player.y)
        if trap and not trap.is_triggered and not trap.is_disarmed:
            return trap.trigger(player)
        return None

    def try_detect_nearby(self, player, radius: int = 2) -> List[Trap]:
        """
        Попытка обнаружить ловушки поблизости

        Args:
            player: Объект игрока
            radius: Радиус обнаружения

        Returns:
            List[Trap]: Список обнаруженных ловушек
        """
        detected = []
        for trap in self.traps:
            if trap.is_detected or trap.is_triggered or trap.is_disarmed:
                continue

            distance = abs(trap.x - player.x) + abs(trap.y - player.y)
            if distance <= radius:
                if trap.try_detect(player):
                    detected.append(trap)

        return detected

    def generate_random_trap(self, x: int, y: int, dungeon_level: int = 1) -> Trap:
        """
        Сгенерировать случайную ловушку

        Args:
            x: Координата X
            y: Координата Y
            dungeon_level: Уровень подземелья

        Returns:
            Trap: Сгенерированная ловушка
        """
        # Выбираем тип ловушки с учетом веса
        trap_weights = []
        trap_types = []

        for trap_type, data in TRAP_DATA.items():
            trap_types.append(trap_type)
            trap_weights.append(data["weight"])

        chosen_type = random.choices(trap_types, weights=trap_weights, k=1)[0]

        # Определяем уровень ловушки на основе уровня подземелья
        trap_level = self._determine_trap_level(dungeon_level)

        return Trap(x, y, chosen_type, dungeon_level, trap_level)

    def _determine_trap_level(self, dungeon_level: int) -> TrapLevel:
        """
        Определить уровень ловушки на основе уровня подземелья

        Args:
            dungeon_level: Уровень подземелья

        Returns:
            TrapLevel: Уровень ловушки
        """
        # Распределение уровней ловушек по уровню подземелья
        if dungeon_level <= 3:
            # Уровень 1-3: в основном примитивные и обычные
            weights = [70, 25, 5, 0, 0]
        elif dungeon_level <= 6:
            # Уровень 4-6: обычные и искусные
            weights = [40, 35, 20, 5, 0]
        elif dungeon_level <= 10:
            # Уровень 7-10: искусные и мастерские
            weights = [20, 30, 30, 15, 5]
        elif dungeon_level <= 15:
            # Уровень 11-15: мастерские с редкими легендарными
            weights = [10, 20, 35, 25, 10]
        elif dungeon_level <= 20:
            # Уровень 16-20: мастерские и легендарные
            weights = [5, 15, 30, 35, 15]
        else:
            # Уровень 21+: в основном мастерские и легендарные
            weights = [0, 10, 25, 40, 25]

        levels = [TrapLevel.PRIMITIVE, TrapLevel.COMMON, TrapLevel.SKILLED,
                  TrapLevel.MASTERWORK, TrapLevel.LEGENDARY]

        return random.choices(levels, weights=weights, k=1)[0]

    def clear(self):
        """Очистить все ловушки"""
        self.traps.clear()

    def get_all_traps(self) -> List[Trap]:
        """Получить все ловушки"""
        return self.traps.copy()

    def get_detected_traps(self) -> List[Trap]:
        """Получить только обнаруженные ловушки"""
        return [t for t in self.traps if t.is_detected]
