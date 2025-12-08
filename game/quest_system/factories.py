"""
Фабрики для создания специальных квестов (стартовые, уникальные и т.д.)
"""
import random
from game.config.config_loader import get_quest_config
from .models import Quest, QuestObjective, QuestType, QuestDifficulty


def create_starter_quests():
    """
    Создать стартовые квесты (автоматически назначаются при старте игры)

    Returns:
        list: Список стартовых квестов
    """
    quests = []

    # Квест 1: Первые шаги - автоматически назначается
    objectives = [
        QuestObjective("Убейте 5 врагов", required_count=5),
    ]
    rewards = {'exp': 150, 'gold': 75}
    quest1 = Quest(
        quest_id="first_steps",
        name="Первые шаги",
        description="Изучите основы боя. Уничтожьте врагов в окрестностях.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.KILL_ENEMIES,
        difficulty=QuestDifficulty.EASY,
        is_starter=True,
        giver_location="Любая локация"
    )
    quest1.target_enemy = "any_enemy"  # Засчитываются любые враги (bandit, undead, necromancer)
    quests.append(quest1)

    # Квест 2: Первая охота - автоматически назначается
    objectives = [
        QuestObjective("Убейте 3 волков", required_count=3),
    ]
    rewards = {'exp': 120, 'gold': 60}
    quest2 = Quest(
        quest_id="first_hunt",
        name="Первая охота",
        description="Охотьтесь на волков в лесах.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.KILL_ANIMALS,
        difficulty=QuestDifficulty.EASY,
        is_starter=True,
        giver_location="Любая локация"
    )
    quest2.target_animal = "wolf"
    quests.append(quest2)

    # Квест 3: Сборщик ресурсов - автоматически назначается
    objectives = [
        QuestObjective("Добыть Медная руда x5", required_count=5),
    ]
    rewards = {'exp': 100, 'skills': ['craftsmanship']}
    quest3 = Quest(
        quest_id="resource_gatherer",
        name="Сборщик ресурсов",
        description="Соберите медную руду в шахтах.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=QuestDifficulty.EASY,
        is_starter=True,
        giver_location="Любая локация"
    )
    quest3.target_item = "copper_ore"
    quests.append(quest3)

    # Квест 4: Лесоруб - автоматически назначается
    objectives = [
        QuestObjective("Добыть Древесина x30", required_count=30),
    ]
    rewards = {
        'exp': 120,
        'items': [(PREDEFINED_ITEMS["poor_pickaxe"], 1)]
    }
    quest4 = Quest(
        quest_id="lumberjack_start",
        name="Лесоруб",
        description="Добудьте древесину для строительства.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.GATHER_RESOURCE,
        difficulty=QuestDifficulty.EASY,
        is_starter=True,
        giver_location="Любая локация"
    )
    quest4.target_item = "wood"
    quests.append(quest4)

    # Квест 5: Исследователь - автоматически назначается
    objectives = [
        QuestObjective("Посетите 3 разных локации", required_count=3),
    ]
    rewards = {'exp': 200, 'gold': 100}
    quest5 = Quest(
        quest_id="explorer_start",
        name="Исследователь",
        description="Исследуйте мир и посетите различные локации.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.STORY,
        difficulty=QuestDifficulty.EASY,
        is_starter=True,
        giver_location="Любая локация"
    )
    quests.append(quest5)

    return quests


def auto_assign_starter_quests(quest_manager):
    """
    Автоматически назначить стартовые квесты игроку
    Вызывается при создании нового персонажа

    Args:
        quest_manager: Менеджер квестов

    Returns:
        list: Список назначенных квестов
    """
    starter_quests = create_starter_quests()
    assigned = []

    for quest in starter_quests:
        if quest.is_starter:
            quest.start()  # Автоматически активируем
            quest_manager.active_quests.append(quest)
            assigned.append(quest)

    return assigned


def create_unique_quests():
    """
    Создать уникальные квесты с особыми наградами (красная рамка в UI)

    Returns:
        list: Список уникальных квестов
    """
    from game.inventory import PREDEFINED_ITEMS

    quests = []

    # ===== КВЕСТЫ АЛХИМИКА (УНИКАЛЬНЫЕ) =====

    # Квест 1: Сбор редких ингредиентов
    objectives = [
        QuestObjective("Собрать магические кристаллы", required_count=5),
        QuestObjective("Собрать фрагменты артефактов", required_count=3),
    ]
    rewards = {
        'exp': 500,
        'gold': 300,
        'items': [
            (PREDEFINED_ITEMS["elixir_of_life"], 2),
            (PREDEFINED_ITEMS["elixir_of_power"], 3),
        ]
    }
    quest = Quest(
        quest_id="alchemist_rare_ingredients",
        name="[УНИК] Редкие ингредиенты",
        description="Алхимик ищет редкие компоненты для создания мощных эликсиров.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.HARD,
        giver_location="Алхимик",
        is_unique=True
    )
    quest.target_item = "magic_crystal"
    quests.append(quest)

    # Квест 2: Философский камень (ЛЕГЕНДАРНЫЙ)
    objectives = [
        QuestObjective("Найти осколки Философского Камня в руинах", required_count=1),
        QuestObjective("Собрать золотую руду", required_count=10),
        QuestObjective("Собрать серебряную руду", required_count=15),
    ]
    rewards = {
        'exp': 1500,
        'gold': 1200,
        'items': [
            (PREDEFINED_ITEMS["alchemists_staff"], 1),
            (PREDEFINED_ITEMS["book_heal"], 1),
        ]
    }
    quest = Quest(
        quest_id="alchemist_philosophers_stone",
        name="[ЛЕГЕНД] Тайна Философского Камня",
        description="Помогите алхимику в поисках легендарного артефакта.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Алхимик",
        is_unique=True
    )
    quests.append(quest)

    # ===== КВЕСТЫ ОХОТНИКА (УНИКАЛЬНЫЕ) =====

    # Квест 3: Великая охота на волков
    objectives = [
        QuestObjective("Убить волков", required_count=15),
        QuestObjective("Добыть Шкура волка x8", required_count=8),
    ]
    rewards = {
        'exp': 600,
        'gold': 400,
        'items': [
            (PREDEFINED_ITEMS["hunters_bow"], 1),
        ]
    }
    quest = Quest(
        quest_id="hunter_wolf_master",
        name="[УНИК] Великая охота на волков",
        description="Охотник предлагает масштабную охоту на волков.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.HARD,
        giver_location="Охотник",
        is_unique=True
    )
    quest.target_animal = "wolf"
    quests.append(quest)

    # Квест 4: Медвежий охотник
    objectives = [
        QuestObjective("Убить медведей", required_count=10),
        QuestObjective("Добыть Шкура медведя x5", required_count=5),
    ]
    rewards = {
        'exp': 800,
        'gold': 600,
        'items': [
            (PREDEFINED_ITEMS["shadow_blade"], 1),
            (PREDEFINED_ITEMS["greater_health_potion"], 5),
        ]
    }
    quest = Quest(
        quest_id="hunter_bear_master",
        name="[УНИК] Медвежий охотник",
        description="Докажите мастерство в охоте на медведей.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Охотник",
        is_unique=True
    )
    quest.target_animal = "bear"
    quests.append(quest)

    # Квест 5: Мастер охоты (ЛЕГЕНДАРНЫЙ)
    objectives = [
        QuestObjective("Уничтожить бандитов", required_count=20),
        QuestObjective("Уничтожить нежить", required_count=20),
        QuestObjective("Убить волков", required_count=15),
        QuestObjective("Убить медведей", required_count=10),
    ]
    rewards = {
        'exp': 2500,
        'gold': 1500,
        'items': [
            (PREDEFINED_ITEMS["book_power_strike"], 1),
            (PREDEFINED_ITEMS["book_battle_cry"], 1),
        ]
    }
    quest = Quest(
        quest_id="hunter_master_hunt",
        name="[ЛЕГЕНД] Мастер Охоты",
        description="Докажите, что вы достойны звания Мастера Охоты.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Охотник",
        is_unique=True
    )
    quests.append(quest)

    # ===== КВЕСТЫ НЕКРОМАНТА (УНИКАЛЬНЫЕ) =====

    # Квест 6: Остановить некроманта (ЛЕГЕНДАРНЫЙ)
    objectives = [
        QuestObjective("Победить некроманта", required_count=1),
    ]
    rewards = {
        'exp': 3000,
        'gold': 2000,
        'items': [
            (PREDEFINED_ITEMS["book_fireball"], 1),
            (PREDEFINED_ITEMS["book_lightning"], 1),
        ]
    }
    quest = Quest(
        quest_id="stop_necromancer",
        name="[ЛЕГЕНД] Угроза из руин",
        description="Некромант угрожает живым. Остановите его!",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Магическая Академия",
        is_unique=True
    )
    quest.target_enemy = "necromancer"
    quests.append(quest)

    # ===== КВЕСТЫ НА СБОР (УНИКАЛЬНЫЕ) =====

    # Квест 7: Богатство земли
    objectives = [
        QuestObjective("Собрать медную руду", required_count=20),
        QuestObjective("Собрать железную руду", required_count=15),
        QuestObjective("Собрать серебряную руду", required_count=10),
        QuestObjective("Собрать золотую руду", required_count=5),
    ]
    rewards = {
        'exp': 1000,
        'gold': 1200,
        'items': [
            (PREDEFINED_ITEMS["book_regeneration"], 1),
        ]
    }
    quest = Quest(
        quest_id="mining_master",
        name="[УНИК] Богатство земли",
        description="Соберите руды всех типов для кузнецов города.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.HARD,
        giver_location="Город",
        is_unique=True
    )
    quests.append(quest)

    # Квест 8: Древние знания (УНИКАЛЬНЫЙ)
    objectives = [
        QuestObjective("Собрать древние монеты", required_count=10),
        QuestObjective("Собрать фрагменты артефактов", required_count=5),
        QuestObjective("Собрать старые свитки", required_count=8),
    ]
    rewards = {
        'exp': 1500,
        'gold': 1000,
        'items': [
            (PREDEFINED_ITEMS["book_magic_missile"], 1),
            (PREDEFINED_ITEMS["book_ice_bolt"], 1),
        ]
    }
    quest = Quest(
        quest_id="ancient_knowledge",
        name="[УНИК] Древние знания",
        description="Соберите артефакты из руин для исследований.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.VERY_HARD,
        giver_location="Магическая Академия",
        is_unique=True
    )
    quests.append(quest)

    # Квест 9: Охотник на оленей (УНИКАЛЬНЫЙ)
    objectives = [
        QuestObjective("Убить оленей", required_count=12),
        QuestObjective("Добыть Оленина x10", required_count=10),
        QuestObjective("Добыть Шкура оленя x6", required_count=6),
    ]
    rewards = {
        'exp': 700,
        'gold': 500,
        'items': [
            (PREDEFINED_ITEMS["stamina_potion"], 5),
        ]
    }
    quest = Quest(
        quest_id="deer_hunter_master",
        name="[УНИК] Охотник на оленей",
        description="Масштабная охота на оленей для торговой гильдии.",
        objectives=objectives,
        rewards=rewards,
        quest_type=QuestType.UNIQUE,
        difficulty=QuestDifficulty.MEDIUM,
        giver_location="Охотник",
        is_unique=True
    )
    quest.target_animal = "deer"
    quests.append(quest)

    return quests


def get_unique_quest_for_location(location_type, location_name):
    """
    Получить уникальный квест для типа локации с вероятностью

    Args:
        location_type: Тип локации (city, village, magic_school)
        location_name: Название локации для установки giver_location

    Returns:
        Quest или None: Уникальный квест или None если не повезло
    """
    from game.inventory import PREDEFINED_ITEMS
    from game.constants import LOCATION_CITY, LOCATION_VILLAGE, LOCATION_MAGIC_SCHOOL

    config = get_quest_config()

    # Вероятность появления уникального квеста из конфига
    probability = config.get_unique_quest_probability(location_type, default=0)
    if random.random() > probability:
        return None

    # Пулы уникальных квестов для разных типов локаций
    city_quests = [
        # Квест кузнеца
        {
            'quest_id': f'blacksmith_order_{random.randint(1000, 9999)}',
            'name': 'Заказ кузнеца',
            'description': 'Кузнец ищет материалы для особого заказа.',
            'objectives': [
                QuestObjective("Собрать железную руду", required_count=10),
                QuestObjective("Собрать медную руду", required_count=8),
            ],
            'rewards': {
                'exp': 400,
                'gold': 350,
                'items': [(PREDEFINED_ITEMS["steel_sword"], 1)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.MEDIUM,
            'target_item': 'iron_ore'
        },
        # Квест главы города
        {
            'quest_id': f'mayor_protection_{random.randint(1000, 9999)}',
            'name': 'Защита торговых путей',
            'description': 'Глава города просит очистить окрестности от бандитов.',
            'objectives': [
                QuestObjective("Уничтожить бандитов", required_count=12),
            ],
            'rewards': {
                'exp': 600,
                'gold': 500,
                'items': [(PREDEFINED_ITEMS["greater_health_potion"], 3)]
            },
            'quest_type': QuestType.KILL_ENEMIES,
            'difficulty': QuestDifficulty.HARD,
            'target_enemy': 'bandit'
        },
        # Квест торговца
        {
            'quest_id': f'merchant_collection_{random.randint(1000, 9999)}',
            'name': 'Ценные находки',
            'description': 'Торговец готов заплатить за редкие артефакты.',
            'objectives': [
                QuestObjective("Собрать древние монеты", required_count=8),
                QuestObjective("Собрать фрагменты артефактов", required_count=4),
            ],
            'rewards': {
                'exp': 500,
                'gold': 600,
                'items': [(PREDEFINED_ITEMS["elixir_of_power"], 2)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.HARD,
            'target_item': 'ancient_coin'
        },
    ]

    village_quests = [
        # Квест старосты
        {
            'quest_id': f'elder_herbs_{random.randint(1000, 9999)}',
            'name': 'Лечебные травы',
            'description': 'Староста деревни просит помочь собрать лекарства.',
            'objectives': [
                QuestObjective("Собрать магические кристаллы", required_count=3),
            ],
            'rewards': {
                'exp': 250,
                'gold': 150,
                'items': [(PREDEFINED_ITEMS["health_potion"], 5)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.EASY,
            'target_item': 'magic_crystal'
        },
        # Квест охотника деревни
        {
            'quest_id': f'village_hunter_{random.randint(1000, 9999)}',
            'name': 'Помощь охотнику',
            'description': 'Местный охотник просит помочь с бандитами.',
            'objectives': [
                QuestObjective("Уничтожить бандитов", required_count=6),
            ],
            'rewards': {
                'exp': 300,
                'gold': 200,
                'items': [(PREDEFINED_ITEMS["hunters_bow"], 1)]
            },
            'quest_type': QuestType.KILL_ENEMIES,
            'difficulty': QuestDifficulty.MEDIUM,
            'target_enemy': 'bandit'
        },
        # Квест шахтёра
        {
            'quest_id': f'village_miner_{random.randint(1000, 9999)}',
            'name': 'Руда для кузни',
            'description': 'Кузнец деревни нуждается в руде.',
            'objectives': [
                QuestObjective("Собрать медную руду", required_count=12),
            ],
            'rewards': {
                'exp': 200,
                'gold': 180,
                'items': [(PREDEFINED_ITEMS["mana_potion"], 3)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.EASY,
            'target_item': 'copper_ore'
        },
    ]

    magic_school_quests = [
        # Квест архимага
        {
            'quest_id': f'archmage_research_{random.randint(1000, 9999)}',
            'name': 'Исследование древних',
            'description': 'Архимаг изучает древние артефакты и нуждается в материалах.',
            'objectives': [
                QuestObjective("Собрать старые свитки", required_count=10),
                QuestObjective("Собрать фрагменты артефактов", required_count=6),
            ],
            'rewards': {
                'exp': 800,
                'gold': 600,
                'items': [(PREDEFINED_ITEMS["book_magic_missile"], 1)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.HARD,
            'target_item': 'old_scroll'
        },
        # Квест мастера боевой магии
        {
            'quest_id': f'battle_mage_training_{random.randint(1000, 9999)}',
            'name': 'Боевая практика',
            'description': 'Мастер боевой магии предлагает испытание против нежити.',
            'objectives': [
                QuestObjective("Уничтожить нежить", required_count=15),
            ],
            'rewards': {
                'exp': 700,
                'gold': 400,
                'items': [(PREDEFINED_ITEMS["book_fireball"], 1)]
            },
            'quest_type': QuestType.KILL_ENEMIES,
            'difficulty': QuestDifficulty.HARD,
            'target_enemy': 'undead'
        },
        # Квест хранителя знаний
        {
            'quest_id': f'lorekeeper_crystals_{random.randint(1000, 9999)}',
            'name': 'Магические кристаллы',
            'description': 'Хранитель знаний ищет кристаллы для магических исследований.',
            'objectives': [
                QuestObjective("Собрать магические кристаллы", required_count=8),
            ],
            'rewards': {
                'exp': 600,
                'gold': 500,
                'items': [(PREDEFINED_ITEMS["book_ice_bolt"], 1)]
            },
            'quest_type': QuestType.GATHER_RESOURCE,
            'difficulty': QuestDifficulty.HARD,
            'target_item': 'magic_crystal'
        },
        # Квест на некроманта
        {
            'quest_id': f'necromancer_hunt_{random.randint(1000, 9999)}',
            'name': 'Угроза некромантии',
            'description': 'Академия просит остановить некроманта, угрожающего региону.',
            'objectives': [
                QuestObjective("Победить некроманта", required_count=1),
            ],
            'rewards': {
                'exp': 1500,
                'gold': 1000,
                'items': [
                    (PREDEFINED_ITEMS["book_lightning"], 1),
                    (PREDEFINED_ITEMS["elixir_of_life"], 2)
                ]
            },
            'quest_type': QuestType.KILL_ENEMIES,
            'difficulty': QuestDifficulty.VERY_HARD,
            'target_enemy': 'necromancer'
        },
    ]

    # Выбираем пул квестов по типу локации
    quest_pools = {
        LOCATION_CITY: city_quests,
        LOCATION_VILLAGE: village_quests,
        LOCATION_MAGIC_SCHOOL: magic_school_quests
    }

    quest_pool = quest_pools.get(location_type, [])
    if not quest_pool:
        return None

    # Выбираем случайный квест из пула
    quest_data = random.choice(quest_pool)

    # Создаём объект квеста
    quest = Quest(
        quest_id=quest_data['quest_id'],
        name=quest_data['name'],
        description=quest_data['description'],
        objectives=quest_data['objectives'],
        rewards=quest_data['rewards'],
        quest_type=quest_data['quest_type'],
        difficulty=quest_data['difficulty'],
        giver_location=location_name
    )

    # Устанавливаем target_item или target_enemy
    if 'target_item' in quest_data:
        quest.target_item = quest_data['target_item']
    if 'target_enemy' in quest_data:
        quest.target_enemy = quest_data['target_enemy']

    return quest
