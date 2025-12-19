"""
Система расписаний для NPC
Управляет временем активности, отдыха и посещением локаций
"""
import random
from game.constants import (
    NPC_TYPE_MINER, NPC_TYPE_GUARD, NPC_TYPE_MERCHANT,
    NPC_TYPE_MAGE, NPC_TYPE_BANDIT, NPC_TYPE_UNDEAD,
    LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MINE
)


class NPCSchedule:
    """Базовый класс расписания NPC"""

    def __init__(self, npc):
        """
        Инициализация расписания

        Args:
            npc: Объект NPC
        """
        self.npc = npc
        # Время активности (часы в сутках от 0 до 23)
        self.active_hours = (6, 22)  # По умолчанию активны с 6 до 22
        self.rest_hours = (22, 6)     # Отдыхают с 22 до 6

        # Флаг скрытия NPC (когда он в локации)
        self.is_hidden = False
        self.hidden_location = None  # Локация, где скрыт NPC
        self.hidden_duration = 0      # Длительность скрытия в часах

        # Текущая активность
        self.current_activity = "active"  # active, resting, visiting_location

        # Случайный сдвиг для асинхронности (в часах)
        self.time_offset = random.uniform(-2, 2)

    def should_be_active(self, current_hour):
        """
        Проверить, должен ли NPC быть активным в данный час

        Args:
            current_hour: Текущий час суток (0-23)

        Returns:
            bool: True если должен быть активным
        """
        # Применяем случайный сдвиг
        adjusted_hour = (current_hour + self.time_offset) % 24

        start, end = self.active_hours
        if start < end:
            return start <= adjusted_hour < end
        else:  # Период через полночь
            return adjusted_hour >= start or adjusted_hour < end

    def should_rest(self, current_hour):
        """
        Проверить, должен ли NPC отдыхать в данный час

        Args:
            current_hour: Текущий час суток (0-23)

        Returns:
            bool: True если должен отдыхать
        """
        return not self.should_be_active(current_hour)

    def update(self, current_hour, game_map):
        """
        Обновить расписание NPC

        Args:
            current_hour: Текущий час суток
            game_map: Карта игры
        """
        # Если скрыт, уменьшаем длительность
        if self.is_hidden:
            self.hidden_duration -= 1
            if self.hidden_duration <= 0:
                self.unhide()
                return

        # Проверяем, должен ли NPC отдыхать
        if self.should_rest(current_hour) and not self.is_hidden:
            if self.npc.state != "rest":
                self.npc.state = "rest"
                self.npc.rest_counter = 0
        elif self.should_be_active(current_hour) and not self.is_hidden:
            if self.npc.state == "rest":
                self.npc.state = self._get_default_state()

    def _get_default_state(self):
        """Получить состояние по умолчанию для NPC"""
        if hasattr(self.npc, 'default_state'):
            return self.npc.default_state
        return "patrol"  # По умолчанию патруль

    def hide_in_location(self, location, duration):
        """
        Скрыть NPC в локации

        Args:
            location: Локация для скрытия
            duration: Длительность скрытия в часах
        """
        self.is_hidden = True
        self.hidden_location = location
        self.hidden_duration = duration
        self.current_activity = "visiting_location"

    def unhide(self):
        """Вернуть NPC на карту"""
        self.is_hidden = False
        self.hidden_location = None
        self.hidden_duration = 0
        self.current_activity = "active"
        self.npc.state = self._get_default_state()


class GuardSchedule(NPCSchedule):
    """Расписание для стражников"""

    def __init__(self, npc):
        super().__init__(npc)
        # Стражники работают круглосуточно в смены
        # Каждый стражник работает 12 часов
        shift = random.choice([0, 12])  # Две смены
        self.active_hours = (shift, (shift + 12) % 24)
        self.rest_hours = ((shift + 12) % 24, shift)


class BanditSchedule(NPCSchedule):
    """Расписание для бандитов"""

    def __init__(self, npc):
        super().__init__(npc)
        # Бандиты активны в ночное время и вечером
        self.active_hours = (18, 6)  # С 18 вечера до 6 утра
        self.rest_hours = (6, 18)


class UndeadSchedule(NPCSchedule):
    """Расписание для нежити"""

    def __init__(self, npc):
        super().__init__(npc)
        # Нежить активна только ночью
        self.active_hours = (20, 6)  # С 20 вечера до 6 утра
        self.rest_hours = (6, 20)


class MageSchedule(NPCSchedule):
    """Расписание для магов"""

    def __init__(self, npc):
        super().__init__(npc)
        # Маги работают днем
        self.active_hours = (8, 22)  # С 8 утра до 22 вечера
        self.rest_hours = (22, 8)


class MerchantSchedule(NPCSchedule):
    """Расписание для торговцев"""

    def __init__(self, npc):
        super().__init__(npc)
        # Торговцы работают днем
        self.active_hours = (7, 21)  # С 7 утра до 21 вечера
        self.rest_hours = (21, 7)


def create_schedule_for_npc(npc):
    """
    Создать расписание для NPC на основе его типа

    Args:
        npc: Объект NPC

    Returns:
        NPCSchedule: Объект расписания
    """
    # Шахтеры теперь используют новую логику на основе ходов, им не нужно расписание по времени суток
    if npc.npc_type == NPC_TYPE_MINER:
        return NPCSchedule(npc)  # Базовое расписание (не используется)
    elif npc.npc_type == NPC_TYPE_GUARD:
        return GuardSchedule(npc)
    elif npc.npc_type == NPC_TYPE_BANDIT:
        return BanditSchedule(npc)
    elif npc.npc_type == NPC_TYPE_UNDEAD:
        return UndeadSchedule(npc)
    elif npc.npc_type == NPC_TYPE_MAGE:
        return MageSchedule(npc)
    elif npc.npc_type == NPC_TYPE_MERCHANT:
        return MerchantSchedule(npc)
    else:
        return NPCSchedule(npc)  # Базовое расписание по умолчанию
