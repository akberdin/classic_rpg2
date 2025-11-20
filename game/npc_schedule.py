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


class MinerSchedule(NPCSchedule):
    """Расписание для шахтеров"""

    def __init__(self, npc):
        super().__init__(npc)
        # Шахтеры работают с 6 до 20
        self.active_hours = (6, 20)
        self.rest_hours = (20, 6)

        # Параметры посещения локаций
        self.visit_mine_chance = 0.15      # 15% шанс посетить шахту каждый час
        self.visit_town_chance = 0.05      # 5% шанс посетить город/деревню
        self.mine_visit_duration = (2, 4)  # 2-4 часа в шахте
        self.town_visit_duration = (1, 3)  # 1-3 часа в городе

        # Последнее посещение (для избежания частых визитов)
        self.last_mine_visit = -10
        self.last_town_visit = -10

    def update(self, current_hour, game_map):
        """Обновить расписание шахтера"""
        super().update(current_hour, game_map)

        # Если уже скрыт или не активен, ничего не делаем
        if self.is_hidden or not self.should_be_active(current_hour):
            return

        # Проверяем посещение шахты
        if (current_hour - self.last_mine_visit > 5 and
            random.random() < self.visit_mine_chance):
            self._visit_mine(game_map)
        # Проверяем посещение города
        elif (current_hour - self.last_town_visit > 8 and
              random.random() < self.visit_town_chance):
            self._visit_town(game_map)

    def _visit_mine(self, game_map):
        """Посетить шахту"""
        if hasattr(self.npc, 'mine_x') and self.npc.mine_x is not None:
            # Проверяем, рядом ли мы с шахтой
            distance = abs(self.npc.x - self.npc.mine_x) + abs(self.npc.y - self.npc.mine_y)
            if distance <= 3:  # Если в пределах 3 клеток от шахты
                duration = random.randint(*self.mine_visit_duration)
                self.hide_in_location(LOCATION_MINE, duration)
                self.last_mine_visit = 0  # Сброс счетчика

    def _visit_town(self, game_map):
        """Посетить ближайший город или деревню"""
        # Ищем ближайший город или деревню
        nearest_location = None
        nearest_distance = float('inf')

        for location in game_map.locations:
            if location.location_type in [LOCATION_CITY, LOCATION_VILLAGE]:
                distance = abs(self.npc.x - location.x) + abs(self.npc.y - location.y)
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_location = location

        # Если рядом с локацией (в пределах 5 клеток), посещаем
        if nearest_location and nearest_distance <= 5:
            duration = random.randint(*self.town_visit_duration)
            self.hide_in_location(nearest_location.location_type, duration)
            self.last_town_visit = 0  # Сброс счетчика


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
    if npc.npc_type == NPC_TYPE_MINER:
        return MinerSchedule(npc)
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
