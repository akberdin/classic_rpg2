"""
Менеджер для управления спутниками игрока
"""
from typing import List, Optional, Dict
from game.companion import Companion


class CompanionManager:
    """Управление спутниками игрока"""

    def __init__(self):
        """Инициализация менеджера спутников"""
        self.companions: Dict[str, Companion] = {}  # Словарь: companion_id -> Companion

    def add_companion(self, companion_type: str, level: int = 1) -> Companion:
        """
        Добавить нового спутника

        Args:
            companion_type: Тип спутника (например, 'wolf')
            level: Начальный уровень

        Returns:
            Companion: Созданный спутник
        """
        companion = Companion(companion_type, level)
        self.companions[companion.companion_id] = companion
        return companion

    def remove_companion(self, companion_id: str) -> bool:
        """
        Удалить спутника (прогнать)

        Args:
            companion_id: ID спутника для удаления

        Returns:
            bool: True если спутник успешно удален
        """
        if companion_id in self.companions:
            del self.companions[companion_id]
            return True
        return False

    def get_companion(self, companion_id: str) -> Optional[Companion]:
        """
        Получить спутника по ID

        Args:
            companion_id: ID спутника

        Returns:
            Companion: Спутник или None если не найден
        """
        return self.companions.get(companion_id)

    def get_all_companions(self) -> List[Companion]:
        """
        Получить список всех спутников

        Returns:
            List[Companion]: Список всех спутников
        """
        return list(self.companions.values())

    def get_companions_by_type(self, companion_type: str) -> List[Companion]:
        """
        Получить всех спутников определенного типа

        Args:
            companion_type: Тип спутника

        Returns:
            List[Companion]: Список спутников данного типа
        """
        return [c for c in self.companions.values() if c.companion_type == companion_type]

    def add_experience_to_all(self, exp: int) -> List[tuple]:
        """
        Добавить опыт всем спутникам

        Args:
            exp: Количество опыта

        Returns:
            List[tuple]: Список кортежей (companion_id, leveled_up)
        """
        results = []
        for companion_id, companion in self.companions.items():
            leveled_up = companion.add_experience(exp)
            results.append((companion_id, leveled_up))
        return results

    def heal_all_companions(self):
        """Восстановить здоровье и выносливость всех спутников"""
        for companion in self.companions.values():
            companion.health = companion.max_health
            companion.stamina = companion.max_stamina

    def get_total_companion_count(self) -> int:
        """
        Получить общее количество спутников

        Returns:
            int: Количество спутников
        """
        return len(self.companions)

    def has_companion_type(self, companion_type: str) -> bool:
        """
        Проверить, есть ли спутник определенного типа

        Args:
            companion_type: Тип спутника

        Returns:
            bool: True если есть хотя бы один спутник данного типа
        """
        return any(c.companion_type == companion_type for c in self.companions.values())

    def get_companions_summary(self) -> List[Dict]:
        """
        Получить сводку по всем спутникам

        Returns:
            List[Dict]: Список словарей с информацией о спутниках
        """
        return [companion.get_stats_summary() for companion in self.companions.values()]

    def serialize(self) -> Dict:
        """
        Сериализовать всех спутников для сохранения

        Returns:
            Dict: Словарь с сериализованными данными
        """
        return {
            'companions': {
                companion_id: companion.serialize()
                for companion_id, companion in self.companions.items()
            }
        }

    def deserialize(self, data: Dict):
        """
        Десериализовать спутников из сохранения

        Args:
            data: Словарь с сохраненными данными
        """
        self.companions.clear()

        companions_data = data.get('companions', {})
        for companion_id, companion_data in companions_data.items():
            companion = Companion.deserialize(companion_data)
            self.companions[companion_id] = companion
