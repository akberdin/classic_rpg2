"""
Модели и логика для системы спутников

Спутники - это существа, которые присоединяются к игроку
и путешествуют вместе с ним, помогая в боях.
"""
import json
import os
import uuid
from game.character import Character


class Companion(Character):
    """Спутник игрока"""

    def __init__(self, companion_type, level=1, companion_id=None):
        """
        Инициализация спутника

        Args:
            companion_type: Тип спутника (например, 'wolf')
            level: Начальный уровень спутника
            companion_id: Уникальный ID (генерируется автоматически если не указан)
        """
        self.companion_type = companion_type
        self.companion_id = companion_id or str(uuid.uuid4())
        self.level = level
        self.experience = 0
        self.rank = 0

        # Загружаем конфигурацию
        self.config = self._load_config()
        self.companion_config = self.config['companions'].get(companion_type, {})

        # Получаем имя с учетом ранга
        display_name = self._get_display_name()

        # Инициализируем базовый Character
        super().__init__(display_name, x=0, y=0)

        # Устанавливаем максимальные значения
        self.max_level = self.companion_config.get('max_level', 20)
        self.max_rank = self.companion_config.get('max_rank', 3)

        # Генерируем характеристики на основе уровня и ранга
        self._calculate_stats()

    def _load_config(self):
        """Загрузить конфигурацию спутников"""
        config_path = os.path.join('game', 'config', 'companion_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'companions': {}, 'experience': {}}

    def _get_display_name(self):
        """
        Получить отображаемое имя с учетом ранга

        Returns:
            str: Имя спутника
        """
        ranks = self.companion_config.get('ranks', {})
        rank_info = ranks.get(str(self.rank), {})
        return rank_info.get('name', self.companion_config.get('display_name', 'Спутник'))

    def _calculate_rank_from_level(self):
        """
        Вычислить ранг на основе текущего уровня

        Returns:
            int: Новый ранг
        """
        ranks = self.companion_config.get('ranks', {})

        for rank_str, rank_data in ranks.items():
            rank_num = int(rank_str)
            level_range = rank_data.get('level_range', [1, 1])
            min_level, max_level = level_range

            if min_level <= self.level <= max_level:
                return rank_num

        return 0

    def _calculate_stats(self):
        """Вычислить характеристики спутника на основе уровня и ранга"""
        # Обновляем ранг на основе уровня
        new_rank = self._calculate_rank_from_level()
        if new_rank != self.rank:
            self.rank = new_rank
            # Обновляем имя при смене ранга
            self.name = self._get_display_name()

        # Базовые характеристики
        base_stats = self.companion_config.get('base_stats', {})
        stats_per_level = self.companion_config.get('stats_per_level', {})
        rank_multipliers = self.companion_config.get('rank_stat_multipliers', {})

        # Множитель для текущего ранга
        rank_multiplier = rank_multipliers.get(str(self.rank), 1.0)

        # Вычисляем характеристики
        self.strength = int((base_stats.get('strength', 5) +
                            (self.level - 1) * stats_per_level.get('strength', 1)) * rank_multiplier)
        self.dexterity = int((base_stats.get('dexterity', 5) +
                             (self.level - 1) * stats_per_level.get('dexterity', 1)) * rank_multiplier)
        self.constitution = int((base_stats.get('constitution', 5) +
                                (self.level - 1) * stats_per_level.get('constitution', 1)) * rank_multiplier)
        self.spirit = int((base_stats.get('spirit', 5) +
                          (self.level - 1) * stats_per_level.get('spirit', 1)) * rank_multiplier)
        self.intelligence = int((base_stats.get('intelligence', 5) +
                                (self.level - 1) * stats_per_level.get('intelligence', 1)) * rank_multiplier)
        self.luck = int((base_stats.get('luck', 5) +
                        (self.level - 1) * stats_per_level.get('luck', 1)) * rank_multiplier)

        # Обновляем производные характеристики
        self.update_derived_stats()

    def add_experience(self, exp):
        """
        Добавить опыт спутнику

        Args:
            exp: Количество опыта

        Returns:
            bool: True если произошло повышение уровня
        """
        if self.level >= self.max_level:
            return False

        self.experience += exp
        exp_needed = self.get_experience_for_next_level()

        if self.experience >= exp_needed:
            return self.level_up()

        return False

    def level_up(self):
        """
        Повысить уровень спутника

        Returns:
            bool: True если повышение успешно
        """
        if self.level >= self.max_level:
            return False

        self.level += 1
        self.experience = 0  # Сбрасываем опыт после повышения уровня

        # Пересчитываем характеристики
        self._calculate_stats()

        return True

    def get_experience_for_next_level(self):
        """
        Получить количество опыта для следующего уровня

        Returns:
            int: Требуемое количество опыта
        """
        exp_config = self.config.get('experience', {})
        base_exp = exp_config.get('base_exp_per_level', 100)
        multiplier = exp_config.get('exp_multiplier_per_level', 1.15)

        return int(base_exp * (multiplier ** (self.level - 1)))

    def get_rank_info(self):
        """
        Получить информацию о текущем ранге

        Returns:
            dict: Словарь с информацией о ранге
        """
        ranks = self.companion_config.get('ranks', {})
        rank_info = ranks.get(str(self.rank), {})

        return {
            'rank': self.rank,
            'name': rank_info.get('name', 'Неизвестный'),
            'description': rank_info.get('description', ''),
            'level_range': rank_info.get('level_range', [1, 1])
        }

    def get_stats_summary(self):
        """
        Получить сводку характеристик

        Returns:
            dict: Словарь с характеристиками
        """
        return {
            'name': self.name,
            'type': self.companion_type,
            'level': self.level,
            'experience': self.experience,
            'exp_needed': self.get_experience_for_next_level(),
            'rank': self.get_rank_info(),
            'health': f"{self.health}/{self.max_health}",
            'stamina': f"{self.stamina}/{self.max_stamina}",
            'stats': {
                'strength': self.strength,
                'dexterity': self.dexterity,
                'constitution': self.constitution,
                'spirit': self.spirit,
                'intelligence': self.intelligence,
                'luck': self.luck
            }
        }

    def serialize(self):
        """
        Сериализовать спутника для сохранения

        Returns:
            dict: Сериализованные данные
        """
        return {
            'companion_id': self.companion_id,
            'companion_type': self.companion_type,
            'level': self.level,
            'experience': self.experience,
            'rank': self.rank,
            'health': self.health,
            'max_health': self.max_health,
            'stamina': self.stamina,
            'max_stamina': self.max_stamina,
            'x': self.x,
            'y': self.y
        }

    @staticmethod
    def deserialize(data):
        """
        Десериализовать спутника из сохранения

        Args:
            data: Словарь с сохраненными данными

        Returns:
            Companion: Восстановленный спутник
        """
        companion = Companion(
            companion_type=data['companion_type'],
            level=data['level'],
            companion_id=data['companion_id']
        )

        companion.experience = data.get('experience', 0)
        companion.rank = data.get('rank', 0)
        companion.health = data.get('health', companion.max_health)
        companion.stamina = data.get('stamina', companion.max_stamina)
        companion.x = data.get('x', 0)
        companion.y = data.get('y', 0)

        return companion
