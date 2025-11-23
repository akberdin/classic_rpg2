"""
NPCManager - централизованное управление всеми NPC в игре.

Этот класс заменяет множество отдельных списков NPC в Game классе,
предоставляя единый интерфейс для работы с NPC.
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Iterator, Callable, Any
from enum import Enum

if TYPE_CHECKING:
    from game.npc.base import NPC
    from game.core.ai_context import AIContext


class NPCType(Enum):
    """Типы NPC в игре."""
    GUARD = 'guards'
    MERCHANT = 'merchants'
    MAGE = 'mages'
    BANDIT = 'bandits'
    MINER = 'miners'
    UNDEAD = 'undead'
    ALCHEMIST = 'alchemists'
    HUNTER = 'hunters'
    NECROMANCER = 'necromancers'
    ANIMAL = 'animals'


class NPCManager:
    """
    Централизованное управление всеми NPC.

    Предоставляет:
    - Единый интерфейс для добавления/удаления NPC
    - Методы для получения NPC по типу или всех сразу
    - Обновление AI всех NPC
    - Поиск ближайших NPC
    """

    def __init__(self):
        """Инициализация менеджера NPC."""
        self._npcs: Dict[str, List['NPC']] = {
            npc_type.value: [] for npc_type in NPCType
        }
        self._all_npcs_cache: Optional[List['NPC']] = None
        self._cache_valid = False

    def _invalidate_cache(self):
        """Сбросить кеш списка всех NPC."""
        self._cache_valid = False
        self._all_npcs_cache = None

    # === Добавление и удаление ===

    def add_npc(self, npc: 'NPC', npc_type: NPCType) -> None:
        """
        Добавить NPC.

        Args:
            npc: Экземпляр NPC
            npc_type: Тип NPC
        """
        self._npcs[npc_type.value].append(npc)
        self._invalidate_cache()

    def add_npcs(self, npcs: List['NPC'], npc_type: NPCType) -> None:
        """
        Добавить несколько NPC одного типа.

        Args:
            npcs: Список NPC
            npc_type: Тип NPC
        """
        self._npcs[npc_type.value].extend(npcs)
        self._invalidate_cache()

    def remove_npc(self, npc: 'NPC', npc_type: NPCType) -> bool:
        """
        Удалить NPC.

        Args:
            npc: Экземпляр NPC для удаления
            npc_type: Тип NPC

        Returns:
            True если NPC был удалён
        """
        npc_list = self._npcs[npc_type.value]
        if npc in npc_list:
            npc_list.remove(npc)
            self._invalidate_cache()
            return True
        return False

    def clear_all(self) -> None:
        """Удалить всех NPC."""
        for npc_type in NPCType:
            self._npcs[npc_type.value].clear()
        self._invalidate_cache()

    def clear_type(self, npc_type: NPCType) -> None:
        """
        Удалить всех NPC определённого типа.

        Args:
            npc_type: Тип NPC для очистки
        """
        self._npcs[npc_type.value].clear()
        self._invalidate_cache()

    # === Получение NPC ===

    def get_all_npcs(self) -> List['NPC']:
        """
        Получить список всех NPC.

        Returns:
            Список всех NPC в игре
        """
        if not self._cache_valid:
            self._all_npcs_cache = []
            for npc_list in self._npcs.values():
                self._all_npcs_cache.extend(npc_list)
            self._cache_valid = True
        return self._all_npcs_cache

    def get_npcs_by_type(self, npc_type: NPCType) -> List['NPC']:
        """
        Получить NPC определённого типа.

        Args:
            npc_type: Тип NPC

        Returns:
            Список NPC данного типа
        """
        return self._npcs[npc_type.value]

    def get_npcs_by_type_name(self, type_name: str) -> List['NPC']:
        """
        Получить NPC по имени типа (строка).

        Args:
            type_name: Имя типа (guards, merchants и т.д.)

        Returns:
            Список NPC данного типа
        """
        return self._npcs.get(type_name, [])

    # === Свойства для быстрого доступа ===

    @property
    def guards(self) -> List['NPC']:
        """Список стражников."""
        return self._npcs[NPCType.GUARD.value]

    @property
    def merchants(self) -> List['NPC']:
        """Список торговцев."""
        return self._npcs[NPCType.MERCHANT.value]

    @property
    def mages(self) -> List['NPC']:
        """Список магов."""
        return self._npcs[NPCType.MAGE.value]

    @property
    def bandits(self) -> List['NPC']:
        """Список бандитов."""
        return self._npcs[NPCType.BANDIT.value]

    @property
    def miners(self) -> List['NPC']:
        """Список шахтёров."""
        return self._npcs[NPCType.MINER.value]

    @property
    def undead(self) -> List['NPC']:
        """Список нежити."""
        return self._npcs[NPCType.UNDEAD.value]

    @property
    def alchemists(self) -> List['NPC']:
        """Список алхимиков."""
        return self._npcs[NPCType.ALCHEMIST.value]

    @property
    def hunters(self) -> List['NPC']:
        """Список охотников."""
        return self._npcs[NPCType.HUNTER.value]

    @property
    def necromancers(self) -> List['NPC']:
        """Список некромантов."""
        return self._npcs[NPCType.NECROMANCER.value]

    @property
    def animals(self) -> List['NPC']:
        """Список животных."""
        return self._npcs[NPCType.ANIMAL.value]

    # === Итерация ===

    def __iter__(self) -> Iterator['NPC']:
        """Итерация по всем NPC."""
        return iter(self.get_all_npcs())

    def __len__(self) -> int:
        """Общее количество NPC."""
        return len(self.get_all_npcs())

    def iter_by_type(self, npc_type: NPCType) -> Iterator['NPC']:
        """
        Итерация по NPC определённого типа.

        Args:
            npc_type: Тип NPC

        Yields:
            NPC данного типа
        """
        return iter(self._npcs[npc_type.value])

    # === Обновление AI ===

    def update_all_ai(self, context: 'AIContext') -> None:
        """
        Обновить AI всех NPC.

        Args:
            context: Контекст AI с необходимыми данными
        """
        for npc in self.get_all_npcs():
            if context.should_update(npc):
                self._update_npc_ai(npc, context)

    def update_ai_by_type(self, npc_type: NPCType, context: 'AIContext') -> None:
        """
        Обновить AI NPC определённого типа.

        Args:
            npc_type: Тип NPC
            context: Контекст AI
        """
        for npc in self._npcs[npc_type.value]:
            if context.should_update(npc):
                self._update_npc_ai(npc, context)

    def _update_npc_ai(self, npc: 'NPC', context: 'AIContext') -> None:
        """
        Обновить AI одного NPC.

        Args:
            npc: NPC для обновления
            context: Контекст AI
        """
        # Определяем тип NPC и вызываем соответствующий метод
        npc_class_name = npc.__class__.__name__

        # NPC, которые не принимают player (наследники Merchant и рабочие)
        no_player_npcs = ('Merchant', 'MagicMerchant', 'Alchemist', 'Miner')

        if npc_class_name in no_player_npcs:
            npc.update_ai(context.game_map, context.all_npcs, context.current_hour)
        else:
            npc.update_ai(
                context.game_map,
                context.all_npcs,
                context.player,
                context.current_hour
            )

    # === Поиск ===

    def find_nearby(self, x: int, y: int, radius: int) -> List['NPC']:
        """
        Найти NPC в радиусе от точки.

        Args:
            x: X координата
            y: Y координата
            radius: Радиус поиска

        Returns:
            Список NPC в радиусе
        """
        return [
            npc for npc in self.get_all_npcs()
            if npc.x is not None and npc.y is not None
            and abs(npc.x - x) + abs(npc.y - y) <= radius
        ]

    def find_closest(self, x: int, y: int, npc_type: Optional[NPCType] = None) -> Optional['NPC']:
        """
        Найти ближайшего NPC.

        Args:
            x: X координата
            y: Y координата
            npc_type: Опционально - тип NPC

        Returns:
            Ближайший NPC или None
        """
        npcs = self._npcs[npc_type.value] if npc_type else self.get_all_npcs()

        closest = None
        min_distance = float('inf')

        for npc in npcs:
            if npc.x is None or npc.y is None:
                continue
            distance = abs(npc.x - x) + abs(npc.y - y)
            if distance < min_distance:
                min_distance = distance
                closest = npc

        return closest

    def find_by_condition(self, condition: Callable[['NPC'], bool]) -> List['NPC']:
        """
        Найти NPC по условию.

        Args:
            condition: Функция-предикат (NPC -> bool)

        Returns:
            Список NPC, удовлетворяющих условию
        """
        return [npc for npc in self.get_all_npcs() if condition(npc)]

    def find_hostile(self) -> List['NPC']:
        """
        Получить всех враждебных NPC.

        Returns:
            Список враждебных NPC
        """
        from game.constants import RELATIONSHIP_HOSTILE
        return self.find_by_condition(
            lambda npc: getattr(npc, 'relationship', 0) <= RELATIONSHIP_HOSTILE
        )

    def find_friendly(self) -> List['NPC']:
        """
        Получить всех дружественных NPC.

        Returns:
            Список дружественных NPC
        """
        from game.constants import RELATIONSHIP_NEUTRAL
        return self.find_by_condition(
            lambda npc: getattr(npc, 'relationship', 0) >= RELATIONSHIP_NEUTRAL
        )

    # === Загрузка из spawner ===

    def load_from_dict(self, npcs_dict: Dict[str, List['NPC']]) -> None:
        """
        Загрузить NPC из словаря (от NPCSpawner).

        Args:
            npcs_dict: Словарь с NPC по типам
        """
        for type_name, npc_list in npcs_dict.items():
            if type_name in self._npcs:
                self._npcs[type_name] = npc_list
        self._invalidate_cache()

    # === Статистика ===

    def get_counts(self) -> Dict[str, int]:
        """
        Получить количество NPC по типам.

        Returns:
            Словарь {тип: количество}
        """
        return {
            npc_type: len(npc_list)
            for npc_type, npc_list in self._npcs.items()
        }

    def get_total_count(self) -> int:
        """
        Получить общее количество NPC.

        Returns:
            Общее количество
        """
        return sum(len(npc_list) for npc_list in self._npcs.values())
