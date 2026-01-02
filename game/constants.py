"""
Константы и идентификаторы игры

Этот файл содержит только статические константы и идентификаторы.
Настраиваемые параметры находятся в профильных конфигах game/config/*.json
"""

from game.config.config_loader import get_config, get_ui_config, get_world_config

# =============================================================================
# ИДЕНТИФИКАТОРЫ ТИПОВ
# =============================================================================

# Типы биомов
BIOME_WATER = 'water'
BIOME_SAND = 'sand'
BIOME_PLAINS = 'plains'
BIOME_HILLS = 'hills'
BIOME_FOREST = 'forest'
BIOME_MOUNTAIN = 'mountain'  # Горы (высокие, труднопроходимые)
BIOME_SWAMP = 'swamp'        # Болото (влажные низины)

# Типы локаций
LOCATION_CITY = 'city'
LOCATION_VILLAGE = 'village'
LOCATION_MINE = 'mine'
LOCATION_BANDIT_CAMP = 'bandit_camp'
LOCATION_RUINS = 'ruins'
LOCATION_MAGIC_SCHOOL = 'magic_school'
LOCATION_WARRIOR_ACADEMY = 'warrior_academy'
LOCATION_SECRET_CAMP = 'secret_camp'

# Типы этажей подземелий (руины)
DUNGEON_FLOOR_BASEMENT = 'basement'              # Подвал
DUNGEON_FLOOR_DARK_BASEMENT = 'dark_basement'    # Темный подвал
DUNGEON_FLOOR_GLOOMY_BASEMENT = 'gloomy_basement'  # Мрачный подвал
DUNGEON_FLOOR_ABYSS = 'abyss'                    # Преисподня

# Типы этажей шахт
MINE_FLOOR_MINE = 'mine'              # Шахта
MINE_FLOOR_DARK_MINE = 'dark_mine'    # Темная шахта
MINE_FLOOR_GLOOMY_MINE = 'gloomy_mine'  # Мрачная шахта
MINE_FLOOR_ABYSS = 'abyss'            # Преисподня

# Проходимые биомы (горы и болото проходимы, но с высокой стоимостью)
PASSABLE_BIOMES = [BIOME_SAND, BIOME_PLAINS, BIOME_HILLS, BIOME_FOREST, BIOME_MOUNTAIN, BIOME_SWAMP]

# Типы NPC
NPC_TYPE_GUARD = "guard"
NPC_TYPE_MERCHANT = "merchant"
NPC_TYPE_BANDIT = "bandit"
NPC_TYPE_NEUTRAL = "neutral"
NPC_TYPE_MINER = "miner"
NPC_TYPE_UNDEAD = "undead"
NPC_TYPE_MAGE = "mage"
NPC_TYPE_ALCHEMIST = "alchemist"
NPC_TYPE_HUNTER = "hunter"
NPC_TYPE_NECROMANCER = "necromancer"
NPC_TYPE_SHADOW_ADEPT = "shadow_adept"

# Типы животных NPC
NPC_TYPE_WOLF = "wolf"
NPC_TYPE_BEAR = "bear"
NPC_TYPE_DEER = "deer"
NPC_TYPE_RAT = "rat"  # Крыса (враждебное подземельное существо)

# Система отношений
RELATIONSHIP_HOSTILE = "hostile"
RELATIONSHIP_UNFRIENDLY = "unfriendly"
RELATIONSHIP_NEUTRAL = "neutral"
RELATIONSHIP_FRIENDLY = "friendly"
RELATIONSHIP_ALLIED = "allied"

# Действия игрока при взаимодействии с NPC
INTERACTION_TRADE = "trade"
INTERACTION_ATTACK = "attack"
INTERACTION_LEAVE = "leave"

# =============================================================================
# СИСТЕМА РАНГОВ
# =============================================================================

MAX_LEVEL = 40
RANKS = {
    (1, 10): "Новичок",
    (11, 20): "Обычный",
    (21, 30): "Опытный",
    (31, 40): "Эксперт"
}

# =============================================================================
# МАТРИЦА ОТНОШЕНИЙ NPC (статическая структура)
# =============================================================================

NPC_RELATIONSHIPS = {
    # Бандиты
    (NPC_TYPE_BANDIT, NPC_TYPE_GUARD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_MERCHANT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_NEUTRAL): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_BANDIT): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_BANDIT, NPC_TYPE_MINER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_UNDEAD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_MAGE): RELATIONSHIP_HOSTILE,

    # Стражники
    (NPC_TYPE_GUARD, NPC_TYPE_BANDIT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_GUARD, NPC_TYPE_GUARD): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_GUARD, NPC_TYPE_MERCHANT): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_GUARD, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_GUARD, NPC_TYPE_MINER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_GUARD, NPC_TYPE_UNDEAD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_GUARD, NPC_TYPE_MAGE): RELATIONSHIP_FRIENDLY,

    # Торговцы
    (NPC_TYPE_MERCHANT, NPC_TYPE_BANDIT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_GUARD): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_MERCHANT): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MERCHANT, NPC_TYPE_MINER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_UNDEAD): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_MAGE): RELATIONSHIP_FRIENDLY,

    # Нейтральные
    (NPC_TYPE_NEUTRAL, NPC_TYPE_BANDIT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_GUARD): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_MERCHANT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_MINER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_UNDEAD): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_MAGE): RELATIONSHIP_NEUTRAL,

    # Шахтеры
    (NPC_TYPE_MINER, NPC_TYPE_BANDIT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_GUARD): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_MERCHANT): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MINER, NPC_TYPE_MINER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_UNDEAD): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_MAGE): RELATIONSHIP_FRIENDLY,

    # Нежить
    (NPC_TYPE_UNDEAD, NPC_TYPE_BANDIT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_GUARD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_MERCHANT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_NEUTRAL): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_MINER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_UNDEAD): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_UNDEAD, NPC_TYPE_MAGE): RELATIONSHIP_HOSTILE,

    # Маги
    (NPC_TYPE_MAGE, NPC_TYPE_GUARD): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MAGE, NPC_TYPE_MERCHANT): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MAGE, NPC_TYPE_MINER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MAGE, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MAGE, NPC_TYPE_MAGE): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MAGE, NPC_TYPE_BANDIT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_MAGE, NPC_TYPE_UNDEAD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_MAGE, NPC_TYPE_ALCHEMIST): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MAGE, NPC_TYPE_HUNTER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MAGE, NPC_TYPE_NECROMANCER): RELATIONSHIP_HOSTILE,

    # Алхимики (дружелюбны ко всем, кроме враждебных)
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_GUARD): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_MERCHANT): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_MINER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_NEUTRAL): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_MAGE): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_BANDIT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_UNDEAD): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_ALCHEMIST): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_HUNTER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_NECROMANCER): RELATIONSHIP_HOSTILE,

    # Охотники (враждебны к бандитам и нежити)
    (NPC_TYPE_HUNTER, NPC_TYPE_GUARD): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_HUNTER, NPC_TYPE_MERCHANT): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_HUNTER, NPC_TYPE_MINER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_HUNTER, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_HUNTER, NPC_TYPE_MAGE): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_HUNTER, NPC_TYPE_BANDIT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_HUNTER, NPC_TYPE_UNDEAD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_HUNTER, NPC_TYPE_ALCHEMIST): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_HUNTER, NPC_TYPE_HUNTER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_HUNTER, NPC_TYPE_NECROMANCER): RELATIONSHIP_HOSTILE,

    # Некроманты (враждебны ко всем, кроме нежити)
    (NPC_TYPE_NECROMANCER, NPC_TYPE_GUARD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_MERCHANT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_MINER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_NEUTRAL): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_MAGE): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_BANDIT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_UNDEAD): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_ALCHEMIST): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_HUNTER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_NECROMANCER): RELATIONSHIP_FRIENDLY,

    # Дополнительные отношения для существующих NPC к новым типам
    (NPC_TYPE_BANDIT, NPC_TYPE_ALCHEMIST): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_HUNTER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_NECROMANCER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_GUARD, NPC_TYPE_ALCHEMIST): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_GUARD, NPC_TYPE_HUNTER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_GUARD, NPC_TYPE_NECROMANCER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_MERCHANT, NPC_TYPE_ALCHEMIST): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_HUNTER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_NECROMANCER): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_ALCHEMIST): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_HUNTER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_NECROMANCER): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_ALCHEMIST): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_HUNTER): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_NECROMANCER): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_UNDEAD, NPC_TYPE_ALCHEMIST): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_HUNTER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_NECROMANCER): RELATIONSHIP_FRIENDLY,

    # Животные (нейтральны ко всем, кроме охотников)
    # Волки
    (NPC_TYPE_WOLF, NPC_TYPE_GUARD): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_WOLF, NPC_TYPE_MERCHANT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_WOLF, NPC_TYPE_BANDIT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_WOLF, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_WOLF, NPC_TYPE_MINER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_WOLF, NPC_TYPE_UNDEAD): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_WOLF, NPC_TYPE_MAGE): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_WOLF, NPC_TYPE_ALCHEMIST): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_WOLF, NPC_TYPE_HUNTER): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_WOLF, NPC_TYPE_NECROMANCER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_WOLF, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_WOLF, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_WOLF, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,

    # Медведи
    (NPC_TYPE_BEAR, NPC_TYPE_GUARD): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_MERCHANT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_BANDIT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_MINER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_UNDEAD): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_MAGE): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_ALCHEMIST): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_HUNTER): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_BEAR, NPC_TYPE_NECROMANCER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,

    # Олени
    (NPC_TYPE_DEER, NPC_TYPE_GUARD): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_MERCHANT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_BANDIT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_MINER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_UNDEAD): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_MAGE): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_ALCHEMIST): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_HUNTER): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_DEER, NPC_TYPE_NECROMANCER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,

    # Отношения других NPC к животным
    (NPC_TYPE_GUARD, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_GUARD, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_GUARD, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MERCHANT, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MERCHANT, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MERCHANT, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BANDIT, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BANDIT, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BANDIT, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MINER, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MINER, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MINER, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_UNDEAD, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_UNDEAD, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_UNDEAD, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MAGE, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MAGE, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MAGE, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,

    # Охотники агрессивны ко всем животным
    (NPC_TYPE_HUNTER, NPC_TYPE_WOLF): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_HUNTER, NPC_TYPE_BEAR): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_HUNTER, NPC_TYPE_DEER): RELATIONSHIP_HOSTILE,

    # Адепты тени (агрессивны к магам, нежити, бандитам, некромантам)
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_GUARD): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_MERCHANT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_MINER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_NEUTRAL): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_ALCHEMIST): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_HUNTER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_MAGE): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_BANDIT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_UNDEAD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_NECROMANCER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_FRIENDLY,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,

    # Отношения других NPC к Адептам тени
    (NPC_TYPE_GUARD, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_MERCHANT, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_MINER, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_HUNTER, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_UNFRIENDLY,
    (NPC_TYPE_MAGE, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_WOLF, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_BEAR, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_DEER, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_NEUTRAL,

    # Крысы (враждебные подземельные существа)
    (NPC_TYPE_RAT, NPC_TYPE_GUARD): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_RAT, NPC_TYPE_MERCHANT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_RAT, NPC_TYPE_BANDIT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_RAT, NPC_TYPE_NEUTRAL): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_RAT, NPC_TYPE_MINER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_RAT, NPC_TYPE_UNDEAD): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_RAT, NPC_TYPE_MAGE): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_RAT, NPC_TYPE_ALCHEMIST): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_RAT, NPC_TYPE_HUNTER): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_RAT, NPC_TYPE_NECROMANCER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_RAT, NPC_TYPE_SHADOW_ADEPT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_RAT, NPC_TYPE_WOLF): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_RAT, NPC_TYPE_BEAR): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_RAT, NPC_TYPE_DEER): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_RAT, NPC_TYPE_RAT): RELATIONSHIP_FRIENDLY,

    # Отношение других типов к крысам
    (NPC_TYPE_GUARD, NPC_TYPE_RAT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_MERCHANT, NPC_TYPE_RAT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BANDIT, NPC_TYPE_RAT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_NEUTRAL, NPC_TYPE_RAT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_MINER, NPC_TYPE_RAT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_UNDEAD, NPC_TYPE_RAT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_MAGE, NPC_TYPE_RAT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_ALCHEMIST, NPC_TYPE_RAT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_HUNTER, NPC_TYPE_RAT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_NECROMANCER, NPC_TYPE_RAT): RELATIONSHIP_NEUTRAL,
    (NPC_TYPE_SHADOW_ADEPT, NPC_TYPE_RAT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_WOLF, NPC_TYPE_RAT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_BEAR, NPC_TYPE_RAT): RELATIONSHIP_HOSTILE,
    (NPC_TYPE_DEER, NPC_TYPE_RAT): RELATIONSHIP_NEUTRAL,
}

# =============================================================================
# ИМЕНА ЛОКАЦИЙ
# =============================================================================
# УДАЛЕНО: Списки имен локаций больше не нужны в основном коде
# Генерация карт перенесена в map_editor, который имеет свои собственные списки имен
# Готовые карты (map1.json и т.д.) уже содержат все имена локаций

# =============================================================================
# ДИНАМИЧЕСКИЕ КОНСТАНТЫ (загружаются из конфигов)
# Для обратной совместимости со старым кодом
# =============================================================================

def _init_dynamic_constants():
    """Инициализация динамических констант из конфигов"""
    global BASE_WIDTH, BASE_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT, FPS
    global TILE_SIZE, MAP_WIDTH, MAP_HEIGHT, VISION_RADIUS, DUNGEON_VISION_RADIUS
    global COLORS, ITEM_QUALITY_COLORS
    global STAMINA_PER_STAT_POINT, STAMINA_COST_PER_MOVE
    global STAMINA_REST_MIN, STAMINA_REST_MAX
    global COMBAT_RANGE, BANDIT_CAMP_RADIUS
    global DODGE_BASE_CHANCE, CRIT_BASE_CHANCE
    global GUARD_DETECTION_RANGE, GUARD_REST_DURATION_MIN, GUARD_REST_DURATION_MAX
    global MERCHANT_DETECTION_RANGE, MERCHANT_REST_DURATION_MIN, MERCHANT_REST_DURATION_MAX
    global BANDIT_DETECTION_RANGE, BANDIT_REST_DURATION_MIN, BANDIT_REST_DURATION_MAX
    global MINER_DETECTION_RANGE, MINER_REST_DURATION_MIN, MINER_REST_DURATION_MAX
    global MINER_MAX_DISTANCE_FROM_MINE
    global UNDEAD_DETECTION_RANGE, UNDEAD_REST_DURATION_MIN, UNDEAD_REST_DURATION_MAX
    global UNDEAD_MAX_DISTANCE_FROM_RUINS
    global MAGE_DETECTION_RANGE, MAGE_REST_DURATION_MIN, MAGE_REST_DURATION_MAX
    global MAGE_MAX_DISTANCE_FROM_SCHOOL
    global GAME_START_HOUR, HOURS_PER_DAY
    global UI_OVERLAY_ALPHA, UI_PANEL_BORDER_WIDTH
    global UI_MIN_FONT_SIZE, UI_DEFAULT_FONT_SIZE, UI_INFO_FONT_SIZE
    global HEALTH_LOW_THRESHOLD, HEALTH_MEDIUM_THRESHOLD
    global LOCATION_MIN_DISTANCE
    global GUARDS_PER_CITY, GUARDS_PER_VILLAGE
    global MERCHANTS_PER_CITY, MERCHANTS_PER_VILLAGE
    global BANDITS_PER_CAMP_MIN, BANDITS_PER_CAMP_MAX
    global MINERS_PER_MINE_MIN, MINERS_PER_MINE_MAX
    global UNDEAD_PER_RUINS_MIN, UNDEAD_PER_RUINS_MAX
    global MAGES_PER_SCHOOL
    global SHOP_BUY_MULTIPLIER, SHOP_SELL_MULTIPLIER

    config = get_config()
    ui_config = get_ui_config()
    world_config = get_world_config()

    # Display параметры
    BASE_WIDTH = ui_config.get_display_param('base_width', 1920)
    BASE_HEIGHT = ui_config.get_display_param('base_height', 1200)
    WINDOW_WIDTH = ui_config.get_display_param('window_width', 1920)
    WINDOW_HEIGHT = ui_config.get_display_param('window_height', 1200)
    FPS = ui_config.get_display_param('fps', 60)
    TILE_SIZE = ui_config.get_display_param('tile_size', 32)

    # Map параметры
    MAP_WIDTH = world_config.get_map_param('width', 200)
    MAP_HEIGHT = world_config.get_map_param('height', 200)
    VISION_RADIUS = world_config.get_map_param('vision_radius', 5)
    DUNGEON_VISION_RADIUS = world_config.get_map_param('dungeon_vision_radius', 10)  # В 2 раза больше
    LOCATION_MIN_DISTANCE = world_config.get_map_param('location_min_distance', 8)

    # Цвета из конфига
    COLORS = {
        # Биомы
        'water': tuple(ui_config.get_color('biomes', 'water', [65, 105, 225])),
        'sand': tuple(ui_config.get_color('biomes', 'sand', [194, 178, 128])),
        'plains': tuple(ui_config.get_color('biomes', 'plains', [107, 142, 35])),
        'hills': tuple(ui_config.get_color('biomes', 'hills', [160, 140, 100])),
        'forest': tuple(ui_config.get_color('biomes', 'forest', [34, 100, 34])),

        # Локации
        'city': tuple(ui_config.get_color('locations', 'city', [169, 169, 169])),
        'village': tuple(ui_config.get_color('locations', 'village', [139, 115, 85])),
        'mine': tuple(ui_config.get_color('locations', 'mine', [96, 96, 96])),
        'bandit_camp': tuple(ui_config.get_color('locations', 'bandit_camp', [178, 34, 34])),
        'ruins': tuple(ui_config.get_color('locations', 'ruins', [128, 128, 128])),
        'magic_school': tuple(ui_config.get_color('locations', 'magic_school', [138, 43, 226])),
        'warrior_academy': tuple(ui_config.get_color('locations', 'warrior_academy', [178, 34, 34])),
        'secret_camp': tuple(ui_config.get_color('locations', 'secret_camp', [64, 64, 64])),

        # Общие
        'player': tuple(ui_config.get_color('general', 'player', [255, 215, 0])),
        'fog': tuple(ui_config.get_color('general', 'fog', [40, 40, 45])),
        'background': tuple(ui_config.get_color('general', 'background', [20, 20, 25])),
        'text': tuple(ui_config.get_color('general', 'text', [255, 255, 255])),

        # Панели
        'panel_bg': tuple(ui_config.get_color('panel', 'bg', [40, 40, 45])),
        'panel_border': tuple(ui_config.get_color('panel', 'border', [100, 100, 120])),
        'panel_header': tuple(ui_config.get_color('panel', 'header', [35, 35, 45])),
        'panel_header_end': tuple(ui_config.get_color('panel', 'header_end', [55, 55, 70])),
        'panel_content': tuple(ui_config.get_color('panel', 'content', [25, 25, 35])),

        # Бой
        'combat_title': tuple(ui_config.get_color('combat', 'title', [255, 215, 0])),
        'combat_log_title': tuple(ui_config.get_color('combat', 'log_title', [150, 200, 255])),
        'combat_success': tuple(ui_config.get_color('combat', 'success', [150, 255, 150])),
        'combat_damage': tuple(ui_config.get_color('combat', 'damage', [255, 150, 150])),
        'combat_crit': tuple(ui_config.get_color('combat', 'crit', [255, 215, 0])),
        'combat_dodge': tuple(ui_config.get_color('combat', 'dodge', [150, 200, 255])),
        'combat_default': tuple(ui_config.get_color('combat', 'default', [200, 200, 200])),
        'combat_player_turn': tuple(ui_config.get_color('combat', 'player_turn', [100, 255, 100])),
        'combat_enemy_turn': tuple(ui_config.get_color('combat', 'enemy_turn', [255, 150, 150])),
        'combat_player_border': tuple(ui_config.get_color('combat', 'player_border', [100, 200, 100])),
        'combat_enemy_border': tuple(ui_config.get_color('combat', 'enemy_border', [200, 100, 100])),

        # Здоровье
        'health_low': tuple(ui_config.get_color('health', 'low', [255, 100, 100])),
        'health_medium': tuple(ui_config.get_color('health', 'medium', [255, 165, 0])),
        'health_high': tuple(ui_config.get_color('health', 'high', [100, 255, 100])),

        # Кнопки
        'button_available': tuple(ui_config.get_color('buttons', 'available', [200, 200, 100])),
        'button_unavailable': tuple(ui_config.get_color('buttons', 'unavailable', [80, 80, 80])),
        'button_default': tuple(ui_config.get_color('buttons', 'default', [100, 100, 100])),
        'cooldown_text': tuple(ui_config.get_color('buttons', 'cooldown_text', [255, 100, 100])),
    }

    # Цвета качества предметов
    items_config = config.items
    ITEM_QUALITY_COLORS = {}
    for quality in ['poor', 'common', 'uncommon', 'rare', 'epic', 'legendary', 'artifact']:
        color = items_config.get_quality(quality, 'color', [255, 255, 255])
        ITEM_QUALITY_COLORS[quality] = tuple(color)

    # Параметры игрока
    player_config = config.player
    STAMINA_PER_STAT_POINT = player_config.get_base_stat('stamina_per_stat_point', 10)
    STAMINA_COST_PER_MOVE = player_config.get_regen_param('stamina_cost_per_move', 2)
    STAMINA_REST_MIN = player_config.get_regen_param('rest_threshold_min', 0.6)
    STAMINA_REST_MAX = player_config.get_regen_param('rest_threshold_max', 0.8)

    # Параметры боя
    combat_config = config.combat
    COMBAT_RANGE = combat_config.get('damage', 'combat_range', default=1)
    DODGE_BASE_CHANCE = combat_config.get_dodge_param('base_chance_per_dex', 3)
    CRIT_BASE_CHANCE = combat_config.get_crit_param('base_chance_per_luck', 3)

    # Параметры NPC
    npc_config = config.npc

    # Guard
    guard_ai = npc_config.get_ai_behavior('guard', default={})
    GUARD_DETECTION_RANGE = guard_ai.get('detection_range', 10) if isinstance(guard_ai, dict) else 10
    GUARD_REST_DURATION_MIN = guard_ai.get('rest_duration_min', 3) if isinstance(guard_ai, dict) else 3
    GUARD_REST_DURATION_MAX = guard_ai.get('rest_duration_max', 3) if isinstance(guard_ai, dict) else 3

    # Merchant
    merchant_ai = npc_config.get_ai_behavior('merchant', default={})
    MERCHANT_DETECTION_RANGE = merchant_ai.get('detection_range', 8) if isinstance(merchant_ai, dict) else 8
    MERCHANT_REST_DURATION_MIN = merchant_ai.get('rest_duration_min', 5) if isinstance(merchant_ai, dict) else 5
    MERCHANT_REST_DURATION_MAX = merchant_ai.get('rest_duration_max', 8) if isinstance(merchant_ai, dict) else 8

    # Bandit
    bandit_ai = npc_config.get_ai_behavior('bandit', default={})
    BANDIT_DETECTION_RANGE = bandit_ai.get('detection_range', 10) if isinstance(bandit_ai, dict) else 10
    BANDIT_REST_DURATION_MIN = bandit_ai.get('rest_duration_min', 2) if isinstance(bandit_ai, dict) else 2
    BANDIT_REST_DURATION_MAX = bandit_ai.get('rest_duration_max', 4) if isinstance(bandit_ai, dict) else 4
    BANDIT_CAMP_RADIUS = bandit_ai.get('camp_radius', 40) if isinstance(bandit_ai, dict) else 40

    # Miner
    miner_ai = npc_config.get_ai_behavior('miner', default={})
    MINER_DETECTION_RANGE = miner_ai.get('detection_range', 8) if isinstance(miner_ai, dict) else 8
    MINER_REST_DURATION_MIN = miner_ai.get('rest_duration_min', 3) if isinstance(miner_ai, dict) else 3
    MINER_REST_DURATION_MAX = miner_ai.get('rest_duration_max', 5) if isinstance(miner_ai, dict) else 5
    MINER_MAX_DISTANCE_FROM_MINE = miner_ai.get('max_distance_from_mine', 20) if isinstance(miner_ai, dict) else 20

    # Undead
    undead_ai = npc_config.get_ai_behavior('undead', default={})
    UNDEAD_DETECTION_RANGE = undead_ai.get('detection_range', 15) if isinstance(undead_ai, dict) else 15
    UNDEAD_REST_DURATION_MIN = undead_ai.get('rest_duration_min', 2) if isinstance(undead_ai, dict) else 2
    UNDEAD_REST_DURATION_MAX = undead_ai.get('rest_duration_max', 3) if isinstance(undead_ai, dict) else 3
    UNDEAD_MAX_DISTANCE_FROM_RUINS = undead_ai.get('max_distance_from_ruins', 15) if isinstance(undead_ai, dict) else 15

    # Mage
    mage_ai = npc_config.get_ai_behavior('mage', default={})
    MAGE_DETECTION_RANGE = mage_ai.get('detection_range', 12) if isinstance(mage_ai, dict) else 12
    MAGE_REST_DURATION_MIN = mage_ai.get('rest_duration_min', 3) if isinstance(mage_ai, dict) else 3
    MAGE_REST_DURATION_MAX = mage_ai.get('rest_duration_max', 5) if isinstance(mage_ai, dict) else 5
    MAGE_MAX_DISTANCE_FROM_SCHOOL = mage_ai.get('max_distance_from_school', 25) if isinstance(mage_ai, dict) else 25

    # Игровое время
    GAME_START_HOUR = world_config.get('time', 'game_start_hour', default=6)
    HOURS_PER_DAY = world_config.get('time', 'hours_per_day', default=24)

    # UI параметры
    UI_OVERLAY_ALPHA = ui_config.get_panel_param('overlay_alpha', 180)
    UI_PANEL_BORDER_WIDTH = ui_config.get_panel_param('border_width', 2)
    UI_MIN_FONT_SIZE = ui_config.get_font_param('min_size', 12)
    UI_DEFAULT_FONT_SIZE = ui_config.get_font_param('default_size', 24)
    UI_INFO_FONT_SIZE = ui_config.get_font_param('info_size', 20)

    # Пороги здоровья
    HEALTH_LOW_THRESHOLD = config.player.get('health_thresholds', 'low', default=30)
    HEALTH_MEDIUM_THRESHOLD = config.player.get('health_thresholds', 'medium', default=60)

    # УДАЛЕНО: Параметры количества локаций больше не нужны
    # Генерация карт перенесена в map_editor

    # Спавн NPC
    # УДАЛЕНО: GUARDS_PER_CITY и GUARDS_PER_VILLAGE - используется система guards из конфигурации map
    MERCHANTS_PER_CITY = npc_config.get_spawn_param('merchants_per_city', 3)
    MERCHANTS_PER_VILLAGE = npc_config.get_spawn_param('merchants_per_village', 2)

    bandits = npc_config.get_spawn_param('bandits_per_camp', {'min': 3, 'max': 6})
    BANDITS_PER_CAMP_MIN = bandits.get('min', 3) if isinstance(bandits, dict) else 3
    BANDITS_PER_CAMP_MAX = bandits.get('max', 6) if isinstance(bandits, dict) else 6

    miners = npc_config.get_spawn_param('miners_per_mine', {'min': 2, 'max': 4})
    MINERS_PER_MINE_MIN = miners.get('min', 2) if isinstance(miners, dict) else 2
    MINERS_PER_MINE_MAX = miners.get('max', 4) if isinstance(miners, dict) else 4

    undead_spawn = npc_config.get_spawn_param('undead_per_ruins', {'min': 3, 'max': 6})
    UNDEAD_PER_RUINS_MIN = undead_spawn.get('min', 3) if isinstance(undead_spawn, dict) else 3
    UNDEAD_PER_RUINS_MAX = undead_spawn.get('max', 6) if isinstance(undead_spawn, dict) else 6

    MAGES_PER_SCHOOL = npc_config.get_spawn_param('mages_per_school', 4)

    # Торговля
    SHOP_BUY_MULTIPLIER = config.economy.get_trade_param('buy_multiplier', 1.5)
    SHOP_SELL_MULTIPLIER = config.economy.get_trade_param('sell_multiplier', 0.5)


# Значения по умолчанию (до инициализации конфигов)
BASE_WIDTH = 1920
BASE_HEIGHT = 1200
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1200
FPS = 60
TILE_SIZE = 64
MAP_WIDTH = 200
MAP_HEIGHT = 200
VISION_RADIUS = 5
DUNGEON_VISION_RADIUS = 10  # Радиус обзора в подземельях (в 2 раза больше)

# Цвета по умолчанию (должны совпадать с ui_config.json)
COLORS = {
    'water': (35, 55, 95),
    'sand': (125, 115, 85),
    'plains': (65, 80, 25),
    'hills': (95, 85, 60),
    'forest': (20, 55, 20),
    'mountain': (110, 100, 95),   # Горы - серо-коричневый
    'swamp': (45, 65, 35),        # Болото - темно-зеленый с коричневым
    'city': (169, 169, 169),
    'village': (139, 115, 85),
    'mine': (96, 96, 96),
    'bandit_camp': (178, 34, 34),
    'ruins': (128, 128, 128),
    'magic_school': (138, 43, 226),
    'warrior_academy': (178, 34, 34),
    'secret_camp': (64, 64, 64),
    'player': (255, 215, 0),
    'fog': (40, 40, 45),
    'background': (20, 20, 25),
    'text': (255, 255, 255),
    'panel_bg': (40, 40, 45),
    'panel_border': (100, 100, 120),
    'panel_header': (35, 35, 45),
    'panel_header_end': (55, 55, 70),
    'panel_content': (25, 25, 35),
    'combat_title': (255, 215, 0),
    'combat_log_title': (150, 200, 255),
    'combat_success': (150, 255, 150),
    'combat_damage': (255, 150, 150),
    'combat_crit': (255, 215, 0),
    'combat_dodge': (150, 200, 255),
    'combat_default': (200, 200, 200),
    'combat_player_turn': (100, 255, 100),
    'combat_enemy_turn': (255, 150, 150),
    'combat_player_border': (100, 200, 100),
    'combat_enemy_border': (200, 100, 100),
    'health_low': (255, 100, 100),
    'health_medium': (255, 165, 0),
    'health_high': (100, 255, 100),
    'button_available': (200, 200, 100),
    'button_unavailable': (80, 80, 80),
    'button_default': (100, 100, 100),
    'cooldown_text': (255, 100, 100),
}

ITEM_QUALITY_COLORS = {
    'poor': (128, 128, 128),
    'common': (255, 255, 255),
    'uncommon': (30, 255, 0),
    'rare': (0, 112, 255),
    'epic': (163, 53, 238),
    'legendary': (255, 128, 0),
    'artifact': (230, 204, 128),
}

# Остальные значения по умолчанию
STAMINA_PER_STAT_POINT = 10
STAMINA_COST_PER_MOVE = 2
STAMINA_REST_MIN = 0.6
STAMINA_REST_MAX = 0.8
COMBAT_RANGE = 1
BANDIT_CAMP_RADIUS = 40
# Новые сбалансированные значения с diminishing returns (ver 1.1)
DODGE_BASE_CHANCE = 2  # Было 3, теперь 2% за первые 10 единиц dex
CRIT_BASE_CHANCE = 2   # Было 3, теперь 2% за первые 10 единиц luck

GUARD_DETECTION_RANGE = 10
GUARD_REST_DURATION_MIN = 3
GUARD_REST_DURATION_MAX = 3
MERCHANT_DETECTION_RANGE = 8
MERCHANT_REST_DURATION_MIN = 5
MERCHANT_REST_DURATION_MAX = 8
BANDIT_DETECTION_RANGE = 10
BANDIT_REST_DURATION_MIN = 2
BANDIT_REST_DURATION_MAX = 4
MINER_DETECTION_RANGE = 8
MINER_REST_DURATION_MIN = 3
MINER_REST_DURATION_MAX = 5
MINER_MAX_DISTANCE_FROM_MINE = 20
UNDEAD_DETECTION_RANGE = 15
UNDEAD_REST_DURATION_MIN = 2
UNDEAD_REST_DURATION_MAX = 3
UNDEAD_MAX_DISTANCE_FROM_RUINS = 15
MAGE_DETECTION_RANGE = 12
MAGE_REST_DURATION_MIN = 3
MAGE_REST_DURATION_MAX = 5
MAGE_MAX_DISTANCE_FROM_SCHOOL = 25

GAME_START_HOUR = 6
HOURS_PER_DAY = 24
UI_OVERLAY_ALPHA = 180
UI_PANEL_BORDER_WIDTH = 2
UI_MIN_FONT_SIZE = 12
UI_DEFAULT_FONT_SIZE = 24
UI_INFO_FONT_SIZE = 20
HEALTH_LOW_THRESHOLD = 30
HEALTH_MEDIUM_THRESHOLD = 60

LOCATION_MIN_DISTANCE = 8
# УДАЛЕНО: Константы количества локаций больше не нужны (генерация в map_editor)
# УДАЛЕНО: GUARDS_PER_CITY и GUARDS_PER_VILLAGE - используется система guards из конфигурации map

MERCHANTS_PER_CITY = 3
MERCHANTS_PER_VILLAGE = 2
BANDITS_PER_CAMP_MIN = 3
BANDITS_PER_CAMP_MAX = 6
MINERS_PER_MINE_MIN = 2
MINERS_PER_MINE_MAX = 4
UNDEAD_PER_RUINS_MIN = 3
UNDEAD_PER_RUINS_MAX = 6
MAGES_PER_SCHOOL = 4

SHOP_BUY_MULTIPLIER = 1.5
SHOP_SELL_MULTIPLIER = 0.5


def init_constants():
    """Инициализировать константы из конфигов (вызывать после загрузки конфигов)"""
    try:
        _init_dynamic_constants()
    except Exception as e:
        print(f"Warning: Failed to load dynamic constants: {e}")
        print("Using default values")
