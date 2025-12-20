"""
Загрузчик конфигурации игры
Обеспечивает централизованный доступ к профильным конфигурациям
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigLoader:
    """Базовый загрузчик конфигурации из JSON файла"""

    def __init__(self, config_name: str):
        self._config_name = config_name
        self._config = self._load_config()

    def _load_config(self) -> Dict:
        """Загрузить конфигурацию из JSON файла"""
        config_path = Path(__file__).parent / f"{self._config_name}.json"

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {config_path}: {e}")
            return {}

    def get(self, *keys, default=None) -> Any:
        """
        Получить значение из конфигурации по ключам

        Args:
            *keys: Путь к значению (например, 'combat', 'max_dodge_chance')
            default: Значение по умолчанию, если ключ не найден

        Returns:
            Значение из конфигурации или default
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def reload(self):
        """Перезагрузить конфигурацию"""
        self._config = self._load_config()


class PlayerConfig(ConfigLoader):
    """Конфигурация игрока - статы, инвентарь, регенерация"""

    def __init__(self):
        super().__init__('player_config')

    def get_base_stat(self, stat_name: str, default=None):
        """Получить базовую характеристику"""
        return self.get('base_stats', stat_name, default=default)

    def get_regen_param(self, param_name: str, default=None):
        """Получить параметр регенерации"""
        return self.get('regeneration', param_name, default=default)

    def get_inventory_param(self, param_name: str, default=None):
        """Получить параметр инвентаря"""
        return self.get('inventory', param_name, default=default)


class CombatConfig(ConfigLoader):
    """Конфигурация боевой системы - уворот, крит, защита"""

    def __init__(self):
        super().__init__('combat_config')

    def get_dodge_param(self, param_name: str, default=None):
        """Получить параметр уворота"""
        return self.get('dodge', param_name, default=default)

    def get_crit_param(self, param_name: str, default=None):
        """Получить параметр крита"""
        return self.get('critical', param_name, default=default)

    def get_defense_param(self, param_name: str, default=None):
        """Получить параметр защиты"""
        return self.get('defense', param_name, default=default)


class ProgressionConfig(ConfigLoader):
    """Конфигурация прогрессии - опыт, уровни, ранги"""

    def __init__(self):
        super().__init__('progression_config')

    def get_exp_param(self, param_name: str, default=None):
        """Получить параметр опыта"""
        return self.get('experience', param_name, default=default)

    def get_rank_info(self, rank_id: str, default=None):
        """Получить информацию о ранге"""
        return self.get('ranks', rank_id, default=default)

    def get_profession_param(self, param_name: str, default=None):
        """Получить параметр профессии"""
        return self.get('professions', param_name, default=default)


class EconomyConfig(ConfigLoader):
    """Конфигурация экономики - золото, торговля"""

    def __init__(self):
        super().__init__('economy_config')

    def get_loot_param(self, param_name: str, default=None):
        """Получить параметр лута"""
        return self.get('loot', param_name, default=default)

    def get_trade_param(self, param_name: str, default=None):
        """Получить параметр торговли"""
        return self.get('trade', param_name, default=default)


class SkillsConfig(ConfigLoader):
    """Конфигурация навыков и способностей"""

    def __init__(self):
        super().__init__('skills_config')

    # ==================== СИСТЕМНЫЕ ПАРАМЕТРЫ ====================

    def get_system_param(self, param_name: str, default=None):
        """Получить системный параметр умений"""
        return self.get('system', param_name, default=default)

    def get_max_rank(self, default=5):
        """Получить максимальный ранг умения"""
        return self.get_system_param('max_rank', default=default)

    def get_base_experience_to_rank_2(self, default=100):
        """Получить базовый опыт для ранга 2"""
        return self.get_system_param('base_experience_to_rank_2', default=default)

    def get_experience_multiplier(self, default=1.5):
        """Получить множитель роста опыта"""
        return self.get_system_param('experience_multiplier', default=default)

    def get_experience_per_use(self, default=10):
        """Получить опыт за использование умения"""
        return self.get_system_param('experience_per_use', default=default)

    def get_skill_slots_count(self, default=8):
        """Получить количество слотов для умений"""
        return self.get_system_param('skill_slots_count', default=default)

    def get_rank_requirement(self, param_name: str, default=None):
        """Получить параметр требований для ранга"""
        return self.get('system', 'rank_requirements', param_name, default=default)

    # ==================== БОЕВЫЕ УМЕНИЯ ====================

    def get_combat_skill(self, skill_name: str, param_name: str = None, default=None):
        """Получить параметр боевого умения"""
        if param_name:
            return self.get('combat_skills', skill_name, param_name, default=default)
        return self.get('combat_skills', skill_name, default=default)

    # ==================== МАГИЧЕСКИЕ УМЕНИЯ ====================

    def get_magic_skill(self, skill_name: str, param_name: str = None, default=None):
        """Получить параметр магического умения"""
        if param_name:
            return self.get('magic_skills', skill_name, param_name, default=default)
        return self.get('magic_skills', skill_name, default=default)

    # ==================== ЛЕЧЕБНЫЕ УМЕНИЯ ====================

    def get_healing_skill(self, skill_name: str, param_name: str = None, default=None):
        """Получить параметр лечебного навыка"""
        if param_name:
            return self.get('healing_skills', skill_name, param_name, default=default)
        return self.get('healing_skills', skill_name, default=default)

    # ==================== ОРУЖЕЙНЫЕ УМЕНИЯ ====================

    def get_weapon_skill(self, weapon_type: str, skill_name: str, param_name: str = None, default=None):
        """
        Получить параметр оружейного умения

        Args:
            weapon_type: Тип оружия (bow_skills, knife_skills, sword_skills)
            skill_name: Название умения
            param_name: Название параметра (опционально)
            default: Значение по умолчанию
        """
        if param_name:
            return self.get('weapon_skills', weapon_type, skill_name, param_name, default=default)
        return self.get('weapon_skills', weapon_type, skill_name, default=default)

    def get_bow_skill(self, skill_name: str, param_name: str = None, default=None):
        """Получить параметр умения лука"""
        return self.get_weapon_skill('bow_skills', skill_name, param_name, default=default)

    def get_knife_skill(self, skill_name: str, param_name: str = None, default=None):
        """Получить параметр умения кинжала"""
        return self.get_weapon_skill('knife_skills', skill_name, param_name, default=default)

    def get_sword_skill(self, skill_name: str, param_name: str = None, default=None):
        """Получить параметр умения меча"""
        return self.get_weapon_skill('sword_skills', skill_name, param_name, default=default)

    # ==================== СТАТУС-ЭФФЕКТЫ ====================

    def get_status_effect(self, effect_name: str, param_name: str = None, default=None):
        """Получить параметр статус-эффекта"""
        if param_name:
            return self.get('status_effects', effect_name, param_name, default=default)
        return self.get('status_effects', effect_name, default=default)

    # ==================== РЕМЕСЛЕННЫЕ УМЕНИЯ ====================

    def get_crafting_skill(self, skill_name: str, param_name: str = None, default=None):
        """Получить параметр ремесленного умения"""
        if param_name:
            return self.get('crafting_skills', skill_name, param_name, default=default)
        return self.get('crafting_skills', skill_name, default=default)

    # ==================== LEGACY МЕТОДЫ ====================

    def get_melee_skill(self, skill_name: str, param_name: str = None, default=None):
        """Получить параметр ближнего навыка (устаревший - используйте get_combat_skill)"""
        return self.get_combat_skill(skill_name, param_name, default=default)


class NPCConfig(ConfigLoader):
    """Конфигурация NPC - типы, AI, отношения, спавн"""

    def __init__(self):
        super().__init__('npc_config')

    def get_ai_behavior(self, npc_type: str, param_name: str = None, default=None):
        """Получить параметр AI поведения"""
        if param_name:
            return self.get('ai_behavior', npc_type, param_name, default=default)
        return self.get('ai_behavior', npc_type, default=default)

    def get_stat_generation(self, level_range: str, param_name: str = None, default=None):
        """Получить параметр генерации статов"""
        if param_name:
            return self.get('stat_generation', level_range, param_name, default=default)
        return self.get('stat_generation', level_range, default=default)

    def get_relationship(self, npc_type1: str, npc_type2: str, default='neutral'):
        """Получить отношение между типами NPC"""
        return self.get('relationships', 'matrix', npc_type1, npc_type2, default=default)

    def get_spawn_param(self, param_name: str, default=None):
        """Получить параметр спавна"""
        return self.get('spawning', param_name, default=default)


class ItemsConfig(ConfigLoader):
    """Конфигурация предметов - качество, дроп"""

    def __init__(self):
        super().__init__('items_config')

    def get_quality(self, quality_name: str, param_name: str = None, default=None):
        """Получить параметр качества"""
        if param_name:
            return self.get('quality_levels', quality_name, param_name, default=default)
        return self.get('quality_levels', quality_name, default=default)

    def get_weapon_param(self, param_name: str, default=None):
        """Получить параметр оружия"""
        return self.get('weapons', param_name, default=default)

    def get_armor_param(self, param_name: str, default=None):
        """Получить параметр брони"""
        return self.get('armor', param_name, default=default)


class WorldConfig(ConfigLoader):
    """Конфигурация мира - карта, локации, биомы"""

    def __init__(self):
        super().__init__('world_config')

    def get_map_param(self, param_name: str, default=None):
        """Получить параметр карты"""
        return self.get('map', param_name, default=default)

    def get_biome(self, biome_name: str, param_name: str = None, default=None):
        """Получить параметр биома"""
        if param_name:
            return self.get('biomes', biome_name, param_name, default=default)
        return self.get('biomes', biome_name, default=default)

    def get_location_names(self, location_type: str, default=None):
        """Получить имена локаций"""
        return self.get('location_names', location_type, default=default or [])

    def get_location_count(self, location_type: str, default=None):
        """Получить количество локаций"""
        return self.get('location_counts', location_type, default=default)


class UIConfig(ConfigLoader):
    """Конфигурация интерфейса - цвета, шрифты, панели"""

    def __init__(self):
        super().__init__('ui_config')

    def get_display_param(self, param_name: str, default=None):
        """Получить параметр отображения"""
        return self.get('display', param_name, default=default)

    def get_font_param(self, param_name: str, default=None):
        """Получить параметр шрифта"""
        return self.get('fonts', param_name, default=default)

    def get_color(self, category: str, color_name: str, default=None):
        """Получить цвет"""
        color = self.get('colors', category, color_name, default=default)
        if isinstance(color, list):
            return tuple(color)
        return color

    def get_panel_param(self, param_name: str, default=None):
        """Получить параметр панели"""
        return self.get('panels', param_name, default=default)


class AssetsConfig(ConfigLoader):
    """Конфигурация ассетов - спрайты NPC, локаций, биомов, навыков, зелий"""

    def __init__(self):
        super().__init__('assets_config')

    def get_npc_sprite(self, npc_type: str, rank: str = 'default', default=None):
        """Получить путь к спрайту NPC"""
        return self.get('npcs', npc_type, rank, default=default)

    def get_location_sprite(self, location_type: str, default=None):
        """Получить путь к спрайту локации"""
        return self.get('locations', location_type, default=default)

    def get_biome_sprite(self, biome_name: str, default=None):
        """Получить путь к спрайту биома"""
        return self.get('biomes', biome_name, default=default)

    def get_skill_sprite(self, skill_name: str, default=None):
        """Получить путь к спрайту навыка"""
        return self.get('skills', skill_name, default=default)

    def get_potion_sprite(self, potion_id: str, default=None):
        """Получить путь к спрайту зелья"""
        return self.get('potions', potion_id, default=default)

    def get_sprite_size(self, default=64):
        """Получить размер спрайта"""
        return self.get('sprite_size', default=default)


class GameConfig:
    """
    Главный класс конфигурации игры - агрегатор всех профильных конфигов
    Синглтон для централизованного доступа
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_configs()
        return cls._instance

    def _init_configs(self):
        """Инициализировать все профильные конфигурации"""
        self.player = PlayerConfig()
        self.combat = CombatConfig()
        self.progression = ProgressionConfig()
        self.economy = EconomyConfig()
        self.skills = SkillsConfig()
        self.npc = NPCConfig()
        self.items = ItemsConfig()
        self.world = WorldConfig()
        self.ui = UIConfig()
        self.assets = AssetsConfig()
        # Система квестов на переработке - QuestConfig удален

        # Для обратной совместимости загружаем старый balance_config если он есть
        self._legacy_config = self._load_legacy_config()

    def _load_legacy_config(self) -> Dict:
        """Загрузить старый balance_config для обратной совместимости"""
        config_path = Path(__file__).parent / "balance_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def get(self, *keys, default=None) -> Any:
        """
        Получить значение из legacy конфигурации (для обратной совместимости)

        Args:
            *keys: Путь к значению
            default: Значение по умолчанию

        Returns:
            Значение из конфигурации или default
        """
        value = self._legacy_config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    # Методы для обратной совместимости со старым API
    def get_player_stat(self, stat_name, default=None):
        """Получить параметр игрока (legacy)"""
        return self.player.get_base_stat(stat_name, default=default)

    def get_combat_param(self, param_name, default=None):
        """Получить параметр боя (legacy)"""
        # Маппинг старых ключей на новые
        mapping = {
            'base_dodge_chance_per_dex': ('dodge', 'base_chance_per_dex'),
            'base_crit_chance_per_luck': ('critical', 'base_chance_per_luck'),
            'max_dodge_chance': ('dodge', 'max_chance'),
            'max_crit_chance': ('critical', 'max_chance'),
            'crit_damage_multiplier': ('critical', 'damage_multiplier'),
            'min_damage': ('damage', 'min_damage'),
            'combat_range': ('damage', 'combat_range'),
            'magic_defense_per_spirit': ('defense', 'magic_defense_per_spirit'),
            'defense_soft_cap': ('defense', 'soft_cap'),
            'defense_reduction_after_cap': ('defense', 'reduction_after_cap'),
        }

        if param_name in mapping:
            return self.combat.get(*mapping[param_name], default=default)
        return self.combat.get(param_name, default=default)

    def get_skill_param(self, skill_name, param_name, default=None):
        """Получить параметр навыка (legacy)"""
        # Попробовать найти в разных категориях
        result = self.skills.get_melee_skill(skill_name, param_name)
        if result is not None:
            return result
        result = self.skills.get_magic_skill(skill_name, param_name)
        if result is not None:
            return result
        result = self.skills.get_healing_skill(skill_name, param_name)
        if result is not None:
            return result
        return default

    def get_npc_param(self, category, *keys, default=None):
        """Получить параметр NPC (legacy)"""
        if category == 'stat_generation':
            return self.npc.get('stat_generation', *keys, default=default)
        elif category == 'detection_ranges':
            npc_type = keys[0] if keys else None
            return self.npc.get_ai_behavior(npc_type, 'detection_range', default=default)
        elif category == 'rest_durations':
            npc_type = keys[0] if keys else None
            return self.npc.get_ai_behavior(npc_type, default=default)
        elif category == 'movement_limits':
            return self.npc.get('ai_behavior', *keys, default=default)
        return self.npc.get(category, *keys, default=default)

    def get_item_param(self, *keys, default=None):
        """Получить параметр предмета (legacy)"""
        return self.items.get(*keys, default=default)

    def get_economy_param(self, param_name, default=None):
        """Получить экономический параметр (legacy)"""
        mapping = {
            'gold_per_enemy_level_min': ('loot', 'gold_per_enemy_level_min'),
            'gold_per_enemy_level_max': ('loot', 'gold_per_enemy_level_max'),
            'work_base_gold': ('work', 'base_gold'),
            'work_gold_per_level': ('work', 'gold_per_level'),
            'shop_buy_multiplier': ('trade', 'buy_multiplier'),
            'shop_sell_multiplier': ('trade', 'sell_multiplier'),
        }

        if param_name in mapping:
            return self.economy.get(*mapping[param_name], default=default)
        return self.economy.get(param_name, default=default)

    def get_regen_param(self, param_name, default=None):
        """Получить параметр регенерации (legacy)"""
        return self.player.get_regen_param(param_name, default=default)

    def get_exp_param(self, param_name, default=None):
        """Получить параметр опыта (legacy)"""
        return self.progression.get_exp_param(param_name, default=default)

    def get_ui_param(self, param_name, default=None):
        """Получить параметр UI (legacy)"""
        # Проверяем в разных секциях
        result = self.ui.get_display_param(param_name)
        if result is not None:
            return result
        result = self.ui.get_font_param(param_name)
        if result is not None:
            return result
        result = self.ui.get_panel_param(param_name)
        if result is not None:
            return result
        return self.ui.get('text_limits', param_name, default=default)

    def reload(self):
        """Перезагрузить все конфигурации"""
        self._init_configs()


# Глобальный экземпляр конфигурации
_config = None

def get_config() -> GameConfig:
    """Получить экземпляр конфигурации"""
    global _config
    if _config is None:
        _config = GameConfig()
    return _config


# Удобные функции-обертки для частого использования
def get_balance(section, *keys, default=None):
    """Получить значение из конфигурации баланса (legacy)"""
    return get_config().get(section, *keys, default=default)


# Новые удобные функции для профильных конфигов
def get_player_config() -> PlayerConfig:
    """Получить конфигурацию игрока"""
    return get_config().player

def get_combat_config() -> CombatConfig:
    """Получить конфигурацию боя"""
    return get_config().combat

def get_progression_config() -> ProgressionConfig:
    """Получить конфигурацию прогрессии"""
    return get_config().progression

def get_economy_config() -> EconomyConfig:
    """Получить конфигурацию экономики"""
    return get_config().economy

def get_skills_config() -> SkillsConfig:
    """Получить конфигурацию навыков"""
    return get_config().skills

def get_npc_config() -> NPCConfig:
    """Получить конфигурацию NPC"""
    return get_config().npc

def get_items_config() -> ItemsConfig:
    """Получить конфигурацию предметов"""
    return get_config().items

def get_world_config() -> WorldConfig:
    """Получить конфигурацию мира"""
    return get_config().world

def get_ui_config() -> UIConfig:
    """Получить конфигурацию UI"""
    return get_config().ui

def get_assets_config() -> AssetsConfig:
    """Получить конфигурацию ассетов"""
    return get_config().assets


# Система квестов на переработке - get_quest_config удален
