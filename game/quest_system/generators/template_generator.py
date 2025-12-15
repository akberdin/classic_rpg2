"""
Универсальный шаблонный генератор квестов.

Использует конфигурацию для логичной генерации квестов:
- Привязка к NPC-квестодателям
- Учет типа локации
- Соответствие сложности рангу игрока
- Исключение дублирования ресурсов/врагов
"""
import random
import json
from pathlib import Path

from ..models import Quest, QuestObjective, QuestType, QuestDifficulty
from ..quest_data import ITEM_KEY_TO_NAME
from .rewards import calculate_gather_quest_rewards, calculate_kill_quest_rewards
from .utils import get_player_rank


# Загрузка конфигурации
def _load_quest_config():
    """Загрузить конфигурацию квестов"""
    config_path = Path(__file__).parent.parent.parent / 'config' / 'quest_config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


_QUEST_CONFIG = None


def get_quest_config():
    """Получить кешированную конфигурацию"""
    global _QUEST_CONFIG
    if _QUEST_CONFIG is None:
        _QUEST_CONFIG = _load_quest_config()
    return _QUEST_CONFIG


# Шаблоны названий квестов по темам
QUEST_NAME_TEMPLATES = {
    'trade': {
        'gather': [
            'Торговый заказ: {item}',
            'Поставка для гильдии: {item}',
            'Срочный заказ: {item}',
            'Партия товара: {item}'
        ]
    },
    'protection': {
        'kill': [
            'Защита поселения от {enemy}',
            'Угроза безопасности: {enemy}',
            'Патрульный рейд: {enemy}',
            'Истребление {enemy}'
        ]
    },
    'mining': {
        'gather': [
            'Добыча руды: {item}',
            'Шахтерский заказ: {item}',
            'Глубинная добыча: {item}',
            'Рудная экспедиция: {item}'
        ]
    },
    'hunting': {
        'kill': [
            'Охотничий контракт: {enemy}',
            'Контроль популяции: {enemy}',
            'Опасная дичь: {enemy}',
            'Охота на {enemy}'
        ],
        'gather': [
            'Охотничья добыча: {item}',
            'Трофеи охотника: {item}',
            'Заказ мастера: {item}',
            'Ценные материалы: {item}'
        ]
    },
    'alchemy': {
        'gather': [
            'Алхимические компоненты: {item}',
            'Редкие ингредиенты: {item}',
            'Сбор для зелий: {item}',
            'Магические материалы: {item}'
        ]
    },
    'arcane': {
        'kill': [
            'Магическая угроза: {enemy}',
            'Очищение от {enemy}',
            'Защита от темных сил: {enemy}',
            'Изгнание {enemy}'
        ],
        'gather': [
            'Артефакты древних: {item}',
            'Магические реликвии: {item}',
            'Исследование руин: {item}',
            'Поиск знаний: {item}'
        ]
    },
    'dark_magic': {
        'gather': [
            'Темные артефакты: {item}',
            'Древние реликвии: {item}',
            'Запретные знания: {item}'
        ]
    }
}

# Описания квестов по темам
QUEST_DESCRIPTION_TEMPLATES = {
    'trade': {
        'gather': [
            'Торговая гильдия нуждается в поставке {item}.',
            'Местный торговец готов хорошо заплатить за {item}.',
            'Городские ремесленники ищут {item} для своих изделий.'
        ]
    },
    'protection': {
        'kill': [
            '{enemy} угрожают мирным жителям. Необходимо их остановить.',
            'Стража просит помощи в борьбе с {enemy}.',
            '{enemy} нападают на караваны. Требуется вмешательство.'
        ]
    },
    'mining': {
        'gather': [
            'Шахтеры не справляются с заказом на {item}.',
            'Нужна помощь в добыче {item} для кузнечной гильдии.',
            'Горнодобытчики ищут помощника для добычи {item}.'
        ]
    },
    'hunting': {
        'kill': [
            '{enemy} расплодились в округе и угрожают стадам.',
            'Охотничья гильдия объявила награду за {enemy}.',
            '{enemy} нападают на путников. Требуется проредить популяцию.'
        ],
        'gather': [
            'Охотники ищут опытного добытчика {item}.',
            'Скорняк заплатит за качественные {item}.',
            'Местная таверна скупает {item} по хорошей цене.'
        ]
    },
    'alchemy': {
        'gather': [
            'Алхимику срочно нужны {item} для зелий.',
            'Магическая академия заказала партию {item}.',
            'Местный целитель ищет {item} для снадобий.'
        ]
    },
    'arcane': {
        'kill': [
            '{enemy} осквернили древнее святилище. Требуется очищение.',
            'Магический совет обеспокоен активностью {enemy}.',
            '{enemy} угрожают балансу магических сил в регионе.'
        ],
        'gather': [
            'Маги исследуют древние руины и ищут {item}.',
            'Академия магии заинтересована в {item}.',
            'Древние {item} содержат ценные знания.'
        ]
    },
    'dark_magic': {
        'gather': [
            'Некромант ищет {item} для своих исследований.',
            'Темные артефакты вроде {item} имеют особую ценность.',
            'Древние {item} хранят запретные секреты.'
        ]
    }
}

# Имена врагов для описаний
ENEMY_DISPLAY_NAMES = {
    'bandit': 'бандитов',
    'undead': 'нежити',
    'necromancer': 'некромантов',
    'wolf': 'волков',
    'bear': 'медведей',
    'deer': 'оленей'
}


class TemplateQuestGenerator:
    """Шаблонный генератор квестов на основе конфигурации"""

    def __init__(self):
        self.config = get_quest_config()
        self._used_resources = set()
        self._used_enemies = set()

    def reset_used(self):
        """Сбросить использованные ресурсы/врагов для новой генерации"""
        self._used_resources.clear()
        self._used_enemies.clear()

    def generate_quests_for_location(self, location_name, location_id, player_level,
                                      location_type, count=3):
        """
        Генерировать квесты для локации на основе конфигурации.

        Args:
            location_name: Название локации
            location_id: ID локации
            player_level: Уровень игрока
            location_type: Тип локации (city, village, mine, ruins, magic_school)
            count: Количество квестов

        Returns:
            list: Список квестов
        """
        self.reset_used()

        location_rules = self.config.get('location_quest_rules', {}).get(location_type, {})
        if not location_rules:
            return []

        player_rank = get_player_rank(player_level)
        quests = []

        # Определяем распределение типов квестов
        distribution = location_rules.get('quest_distribution', {'gather': 0.5, 'kill': 0.5})

        # Определяем доступную сложность
        allowed_difficulties = self._get_allowed_difficulties(player_rank)

        # Генерируем квесты
        for _ in range(count):
            quest_type = self._choose_quest_type(distribution)

            if quest_type == 'gather':
                quest = self._generate_gather_quest(
                    location_name, location_id, player_level, player_rank,
                    location_rules, allowed_difficulties
                )
            elif quest_type == 'kill':
                quest = self._generate_kill_quest(
                    location_name, location_id, player_level, player_rank,
                    location_rules, allowed_difficulties
                )
            else:
                continue

            if quest:
                quests.append(quest)

        return quests

    def _get_allowed_difficulties(self, player_rank):
        """Получить допустимые сложности для ранга игрока"""
        difficulty_map = self.config.get('difficulty_by_rank', {})
        difficulties = difficulty_map.get(str(player_rank), ['easy', 'medium'])
        return [self._str_to_difficulty(d) for d in difficulties]

    def _str_to_difficulty(self, s):
        """Преобразовать строку в QuestDifficulty"""
        mapping = {
            'easy': QuestDifficulty.EASY,
            'medium': QuestDifficulty.MEDIUM,
            'hard': QuestDifficulty.HARD,
            'very_hard': QuestDifficulty.VERY_HARD
        }
        return mapping.get(s, QuestDifficulty.EASY)

    def _choose_quest_type(self, distribution):
        """Выбрать тип квеста на основе распределения"""
        roll = random.random()
        cumulative = 0
        for quest_type, prob in distribution.items():
            cumulative += prob
            if roll < cumulative:
                return quest_type
        return 'gather'

    def _get_quest_giver(self, location_rules):
        """Выбрать квестодателя для локации"""
        primary = location_rules.get('primary_givers', [])
        secondary = location_rules.get('secondary_givers', [])

        # 70% шанс на primary, 30% на secondary
        if primary and (not secondary or random.random() < 0.7):
            return random.choice(primary)
        elif secondary:
            return random.choice(secondary)
        return None

    def _get_theme_for_giver(self, giver_type):
        """Получить тему квестов для типа квестодателя"""
        npc_config = self.config.get('npc_quest_givers', {}).get(giver_type, {})
        return npc_config.get('quest_theme', 'trade')

    def _generate_gather_quest(self, location_name, location_id, player_level,
                                player_rank, location_rules, allowed_difficulties):
        """Генерировать квест на сбор ресурсов"""
        # Выбираем квестодателя
        giver = self._get_quest_giver(location_rules)
        theme = self._get_theme_for_giver(giver) if giver else 'trade'

        # Получаем доступные ресурсы для локации и ранга
        resource_focus = location_rules.get('resource_focus', [])
        resource_by_difficulty = self.config.get('resource_by_difficulty', {})

        # Собираем ресурсы, соответствующие сложности
        available_resources = []
        for difficulty in allowed_difficulties:
            diff_name = difficulty.name.lower()
            resources = resource_by_difficulty.get(diff_name, [])
            # Фильтруем по фокусу локации если есть
            if resource_focus:
                resources = [r for r in resources if r in resource_focus]
            for r in resources:
                if r not in self._used_resources:
                    available_resources.append((r, difficulty))

        if not available_resources:
            return None

        # Выбираем ресурс
        resource, difficulty = random.choice(available_resources)
        self._used_resources.add(resource)

        # Определяем количество
        amounts_config = self.config.get('quest_amounts', {}).get('gather', {})
        diff_key = difficulty.name.lower()
        amount_range = amounts_config.get(diff_key, [3, 5])
        amount = random.randint(amount_range[0], amount_range[1])

        # Получаем название ресурса
        item_name = ITEM_KEY_TO_NAME.get(resource, resource)

        # Генерируем название и описание
        name_templates = QUEST_NAME_TEMPLATES.get(theme, {}).get('gather', ['Сбор: {item}'])
        desc_templates = QUEST_DESCRIPTION_TEMPLATES.get(theme, {}).get('gather', ['Соберите {item}.'])

        quest_name = random.choice(name_templates).format(item=item_name)
        description = random.choice(desc_templates).format(item=item_name)

        # Рассчитываем награды
        rewards = calculate_gather_quest_rewards(player_level, difficulty, amount)

        # Создаем квест
        quest_id = f"gather_{resource}_{location_id}_{random.randint(1000, 9999)}"
        objective = QuestObjective(f"Собрать {item_name}", required_count=amount)

        quest = Quest(
            quest_id=quest_id,
            name=quest_name,
            description=description,
            objectives=[objective],
            rewards=rewards,
            quest_type=QuestType.GATHER_RESOURCE,
            difficulty=difficulty,
            location_id=location_id,
            giver_location=location_name,
            min_rank=max(1, player_rank - 1)  # Доступен для ранга на 1 ниже текущего
        )
        quest.target_item = resource

        return quest

    def _generate_kill_quest(self, location_name, location_id, player_level,
                              player_rank, location_rules, allowed_difficulties):
        """Генерировать квест на убийство"""
        # Выбираем квестодателя
        giver = self._get_quest_giver(location_rules)
        theme = self._get_theme_for_giver(giver) if giver else 'protection'

        # Получаем доступных врагов
        enemy_focus = location_rules.get('enemy_focus', [])
        enemy_by_difficulty = self.config.get('enemy_by_difficulty', {})

        # Собираем врагов, соответствующих сложности
        available_enemies = []
        for difficulty in allowed_difficulties:
            diff_name = difficulty.name.lower()
            enemies = enemy_by_difficulty.get(diff_name, [])
            # Фильтруем по фокусу локации
            if enemy_focus:
                enemies = [e for e in enemies if e in enemy_focus]
            for e in enemies:
                if e not in self._used_enemies:
                    available_enemies.append((e, difficulty))

        if not available_enemies:
            return None

        # Выбираем врага
        enemy, difficulty = random.choice(available_enemies)
        self._used_enemies.add(enemy)

        # Определяем количество
        amounts_config = self.config.get('quest_amounts', {}).get('kill', {})
        diff_key = difficulty.name.lower()
        amount_range = amounts_config.get(diff_key, [2, 4])
        amount = random.randint(amount_range[0], amount_range[1])

        # Получаем название врага
        enemy_name = ENEMY_DISPLAY_NAMES.get(enemy, enemy)

        # Генерируем название и описание
        name_templates = QUEST_NAME_TEMPLATES.get(theme, {}).get('kill', ['Уничтожение: {enemy}'])
        desc_templates = QUEST_DESCRIPTION_TEMPLATES.get(theme, {}).get('kill', ['Уничтожьте {enemy}.'])

        quest_name = random.choice(name_templates).format(enemy=enemy_name)
        description = random.choice(desc_templates).format(enemy=enemy_name)

        # Рассчитываем награды
        rewards = calculate_kill_quest_rewards(player_level, difficulty, amount)

        # Определяем тип квеста (убийство врагов или животных)
        is_animal = enemy in ['wolf', 'bear', 'deer']
        quest_type = QuestType.KILL_ANIMALS if is_animal else QuestType.KILL_ENEMIES

        # Создаем квест
        quest_id = f"kill_{enemy}_{location_id}_{random.randint(1000, 9999)}"
        objective = QuestObjective(f"Уничтожить {enemy_name}", required_count=amount)

        quest = Quest(
            quest_id=quest_id,
            name=quest_name,
            description=description,
            objectives=[objective],
            rewards=rewards,
            quest_type=quest_type,
            difficulty=difficulty,
            location_id=location_id,
            giver_location=location_name,
            min_rank=max(1, player_rank - 1)
        )

        if is_animal:
            quest.target_animal = enemy
        else:
            quest.target_enemy = enemy

        return quest


# Глобальный экземпляр генератора
_generator = None


def get_template_generator():
    """Получить экземпляр шаблонного генератора"""
    global _generator
    if _generator is None:
        _generator = TemplateQuestGenerator()
    return _generator


def generate_quests_from_template(location_name, location_id, player_level,
                                   location_type, count=3):
    """
    Удобная функция для генерации квестов из шаблона.

    Args:
        location_name: Название локации
        location_id: ID локации
        player_level: Уровень игрока
        location_type: Тип локации
        count: Количество квестов

    Returns:
        list: Список квестов
    """
    generator = get_template_generator()
    return generator.generate_quests_for_location(
        location_name, location_id, player_level, location_type, count
    )
