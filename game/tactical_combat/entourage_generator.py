"""
Генератор свиты для NPC в тактическом бою
"""
import json
import os
import random
from typing import List, Optional

from game.utils.rank_utils import get_numeric_rank, get_random_level_for_rank
from game.constants import (
    NPC_TYPE_GUARD, NPC_TYPE_MERCHANT, NPC_TYPE_BANDIT,
    NPC_TYPE_MINER, NPC_TYPE_UNDEAD, NPC_TYPE_MAGE,
    NPC_TYPE_ALCHEMIST, NPC_TYPE_HUNTER, NPC_TYPE_NECROMANCER,
    NPC_TYPE_WOLF, NPC_TYPE_BEAR, NPC_TYPE_DEER
)


class EntourageGenerator:
    """Генератор свиты для NPC"""

    # Типы NPC, которые не могут иметь свиту (животные)
    EXCLUDED_TYPES = {
        NPC_TYPE_WOLF,
        NPC_TYPE_BEAR,
        NPC_TYPE_DEER,
        'animal'
    }

    def __init__(self):
        """Инициализация генератора свиты"""
        self.config = self._load_config()

    def _load_config(self):
        """Загрузить конфигурацию свиты"""
        config_path = os.path.join('game', 'config', 'entourage_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Если конфигурация не найдена, используем значения по умолчанию
            return {
                'entourage_rules': {},
                'excluded_npc_types': list(self.EXCLUDED_TYPES)
            }

    def can_have_entourage(self, npc) -> bool:
        """
        Проверить, может ли NPC иметь свиту

        Args:
            npc: Экземпляр NPC

        Returns:
            bool: True если NPC может иметь свиту
        """
        # Проверяем, что это не животное
        npc_type = getattr(npc, 'npc_type', None)
        if npc_type in self.EXCLUDED_TYPES:
            return False

        # Проверяем ранг (свита доступна с ранга 1 и выше)
        level = getattr(npc, 'level', 1)
        rank = get_numeric_rank(level)

        if rank < 1:
            return False

        # Проверяем, включена ли свита для данного ранга
        rank_config = self.config['entourage_rules'].get(str(rank), {})
        return rank_config.get('enabled', False)

    def generate_entourage(self, npc) -> List:
        """
        Генерировать свиту для NPC

        Args:
            npc: Экземпляр NPC (основной противник)

        Returns:
            List: Список членов свиты (NPC)
        """
        if not self.can_have_entourage(npc):
            return []

        level = getattr(npc, 'level', 1)
        rank = get_numeric_rank(level)
        rank_config = self.config['entourage_rules'].get(str(rank), {})

        # Проверяем, должна ли свита появиться (по шансу)
        spawn_chance = rank_config.get('spawn_chance', 0.0)
        if random.random() > spawn_chance:
            return []

        # Определяем количество членов свиты
        min_count = rank_config.get('min_count', 0)
        max_count = rank_config.get('max_count', 0)

        if max_count == 0:
            return []

        entourage_count = random.randint(min_count, max_count)
        if entourage_count == 0:
            return []

        # Генерируем членов свиты
        entourage = []
        allowed_ranks = rank_config.get('allowed_ranks', [])
        rank_weights = rank_config.get('rank_weights', {})

        for i in range(entourage_count):
            # Выбираем ранг члена свиты на основе весов
            member_rank = self._choose_rank(allowed_ranks, rank_weights)

            # Создаем члена свиты
            member = self._create_entourage_member(npc, member_rank, i)
            if member:
                entourage.append(member)

        return entourage

    def _choose_rank(self, allowed_ranks: List[int], rank_weights: dict) -> int:
        """
        Выбрать ранг для члена свиты на основе весов

        Args:
            allowed_ranks: Список разрешенных рангов
            rank_weights: Словарь весов для каждого ранга

        Returns:
            int: Выбранный ранг
        """
        if not allowed_ranks:
            return 0

        # Если весов нет, используем равномерное распределение
        if not rank_weights:
            return random.choice(allowed_ranks)

        # Выбираем на основе весов
        ranks = []
        weights = []

        for rank in allowed_ranks:
            weight = rank_weights.get(str(rank), 1.0)
            ranks.append(rank)
            weights.append(weight)

        return random.choices(ranks, weights=weights)[0]

    def _create_entourage_member(self, leader_npc, rank: int, index: int):
        """
        Создать члена свиты

        Args:
            leader_npc: Основной NPC (лидер)
            rank: Ранг члена свиты
            index: Индекс члена свиты (для уникального имени)

        Returns:
            NPC: Созданный член свиты или None
        """
        # Импортируем классы NPC
        from game.npc.guard import Guard
        from game.npc.merchant import Merchant
        from game.npc.hostile import Bandit, Undead
        from game.npc.worker import Miner, Alchemist, Hunter
        from game.npc.unique import Necromancer

        # Определяем тип лидера
        leader_type = getattr(leader_npc, 'npc_type', None)
        leader_name = getattr(leader_npc, 'name', 'Неизвестный')
        leader_x = getattr(leader_npc, 'x', 0)
        leader_y = getattr(leader_npc, 'y', 0)

        # Генерируем уровень для члена свиты
        level = get_random_level_for_rank(rank)

        # Создаем члена свиты того же типа что и лидер
        member = None
        member_name = f"{leader_name} (Свита {index + 1})"

        try:
            if leader_type == NPC_TYPE_GUARD:
                member = Guard(member_name, leader_x, leader_y, level)
            elif leader_type == NPC_TYPE_BANDIT:
                # Бандиты используют те же координаты лагеря что и лидер
                camp_x = getattr(leader_npc, 'camp_x', leader_x)
                camp_y = getattr(leader_npc, 'camp_y', leader_y)
                member = Bandit(member_name, leader_x, leader_y, level, camp_x, camp_y)
            elif leader_type == NPC_TYPE_UNDEAD:
                member = Undead(member_name, leader_x, leader_y, level)
            elif leader_type == NPC_TYPE_MERCHANT:
                member = Merchant(member_name, leader_x, leader_y, level)
            elif leader_type == NPC_TYPE_MINER:
                mine_x = getattr(leader_npc, 'mine_x', leader_x)
                mine_y = getattr(leader_npc, 'mine_y', leader_y)
                member = Miner(member_name, leader_x, leader_y, level, mine_x, mine_y)
            elif leader_type == NPC_TYPE_ALCHEMIST:
                member = Alchemist(member_name, leader_x, leader_y, level)
            elif leader_type == NPC_TYPE_HUNTER:
                member = Hunter(member_name, leader_x, leader_y, level)
            elif leader_type == NPC_TYPE_NECROMANCER:
                member = Necromancer(member_name, leader_x, leader_y, level)
            else:
                # Для неизвестных типов создаем стража по умолчанию
                member = Guard(member_name, leader_x, leader_y, level)

        except Exception as e:
            print(f"Ошибка при создании члена свиты: {e}")
            return None

        return member
