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

    def __init__(self, x: int, y: int, trap_type: TrapType, dungeon_level: int = 1):
        """
        Создать ловушку

        Args:
            x: Координата X
            y: Координата Y
            trap_type: Тип ловушки
            dungeon_level: Уровень подземелья (влияет на урон)
        """
        self.x = x
        self.y = y
        self.trap_type = trap_type
        self.dungeon_level = dungeon_level

        # Данные ловушки
        data = TRAP_DATA.get(trap_type, TRAP_DATA[TrapType.SPIKE])
        self.name = data["name"]
        self.description = data["description"]
        self.damage_type = data["damage_type"]
        self.detection_dc = data["detection_dc"]
        self.disarm_dc = data["disarm_dc"]

        # Расчет урона с учетом уровня подземелья
        base_damage = data["base_damage"]
        self.damage = int(base_damage * (1 + 0.15 * (dungeon_level - 1)))

        # Дополнительные эффекты
        self.poison_duration = data.get("poison_duration", 0)
        self.poison_damage = data.get("poison_damage", 0)
        self.curse_effect = data.get("curse_effect", None)
        self.curse_duration = data.get("curse_duration", 0)

        # Состояние
        self.is_triggered = False
        self.is_detected = False
        self.is_disarmed = False

    def trigger(self, player) -> dict:
        """
        Активировать ловушку

        Args:
            player: Объект игрока

        Returns:
            dict: Результат срабатывания ловушки
        """
        if self.is_triggered or self.is_disarmed:
            return {"success": False, "message": "Ловушка уже сработала или обезврежена"}

        self.is_triggered = True

        result = {
            "success": True,
            "trap_name": self.name,
            "damage": 0,
            "damage_type": self.damage_type,
            "effects": [],
            "message": ""
        }

        # Шанс уклонения от ловушки (зависит от ловкости)
        dodge_chance = min(50, player.dexterity * 2)
        if random.randint(1, 100) <= dodge_chance:
            result["message"] = f"Вы успели увернуться от ловушки '{self.name}'!"
            result["damage"] = 0
            return result

        # Наносим урон
        actual_damage = self.damage
        player.health -= actual_damage
        result["damage"] = actual_damage
        result["message"] = f"Ловушка '{self.name}' нанесла вам {actual_damage} урона!"

        # Дополнительные эффекты
        if self.poison_duration > 0:
            # Применяем отравление
            if hasattr(player, 'apply_poison'):
                player.apply_poison(self.poison_damage, self.poison_duration)
            result["effects"].append(f"Отравление на {self.poison_duration} ходов")
            result["message"] += f" Вы отравлены на {self.poison_duration} ходов!"

        if self.curse_effect:
            # Применяем проклятие
            if hasattr(player, 'apply_curse'):
                player.apply_curse(self.curse_effect, self.curse_duration)
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
            return True, f"Вы успешно обезвредили ловушку '{self.name}'!"
        else:
            # Провал - ловушка срабатывает
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
        return Trap(x, y, chosen_type, dungeon_level)

    def clear(self):
        """Очистить все ловушки"""
        self.traps.clear()

    def get_all_traps(self) -> List[Trap]:
        """Получить все ловушки"""
        return self.traps.copy()

    def get_detected_traps(self) -> List[Trap]:
        """Получить только обнаруженные ловушки"""
        return [t for t in self.traps if t.is_detected]
