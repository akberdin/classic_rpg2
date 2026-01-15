"""Map generator for procedural terrain creation."""

import random
import uuid
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field

from ..utils.helpers import (
    PerlinNoise, normalize_map, get_neighbors, distance
)


# Biome constants
BIOME_WATER = "water"
BIOME_SAND = "sand"
BIOME_PLAINS = "plains"
BIOME_FOREST = "forest"
BIOME_HILLS = "hills"
BIOME_MOUNTAIN = "mountain"
BIOME_SWAMP = "swamp"

# Location constants
LOCATION_CITY = "city"
LOCATION_CAPITAL = "capital"
LOCATION_VILLAGE = "village"
LOCATION_MINE = "mine"
LOCATION_BANDIT_CAMP = "bandit_camp"
LOCATION_RUINS = "ruins"
LOCATION_MAGIC_SCHOOL = "magic_school"
LOCATION_WARRIOR_ACADEMY = "warrior_academy"
LOCATION_SECRET_CAMP = "secret_camp"

# Beast spawn point constants
LOCATION_SPAWN_WOLF = "spawn_wolf"
LOCATION_SPAWN_BEAR = "spawn_bear"
LOCATION_SPAWN_DEER = "spawn_deer"

PASSABLE_BIOMES = [BIOME_SAND, BIOME_PLAINS, BIOME_HILLS, BIOME_FOREST, BIOME_MOUNTAIN, BIOME_SWAMP]


def get_default_player_attitude(location_type: str) -> int:
    """Get default player attitude for a location type."""
    attitude_map = {
        LOCATION_MINE: 0,
        LOCATION_VILLAGE: 0,
        LOCATION_CITY: -1,
        LOCATION_CAPITAL: -3,
        LOCATION_MAGIC_SCHOOL: -2,
        LOCATION_WARRIOR_ACADEMY: -2,
        LOCATION_SECRET_CAMP: -2,
        LOCATION_BANDIT_CAMP: -10,
        LOCATION_RUINS: -10,
    }
    return attitude_map.get(location_type, 0)


@dataclass
class GeneratorParams:
    """Parameters for map generation."""
    width: int = 200
    height: int = 200
    seed: Optional[int] = None

    # Noise parameters
    elevation_scale: float = 150.0
    elevation_octaves: int = 3
    moisture_scale: float = 120.0
    moisture_octaves: int = 2

    # Biome thresholds
    water_level: float = 0.30
    beach_level: float = 0.35
    plains_level: float = 0.50
    hills_level: float = 0.60
    mountain_level: float = 0.75
    forest_moisture: float = 0.55
    swamp_moisture: float = 0.70

    # Options
    temperature_gradient: bool = True
    smooth_iterations: int = 2
    generate_beaches: bool = True
    generate_rivers: bool = True
    river_count: int = 5

    # Location counts
    city_count: int = 5
    village_count: int = 15
    mine_count: int = 8
    bandit_camp_count: int = 10
    ruins_count: int = 10

    # Placement options
    ignore_min_distance: bool = False  # Disable minimum distance restriction

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'width': self.width,
            'height': self.height,
            'seed': self.seed,
            'elevation_scale': self.elevation_scale,
            'elevation_octaves': self.elevation_octaves,
            'moisture_scale': self.moisture_scale,
            'moisture_octaves': self.moisture_octaves,
            'water_level': self.water_level,
            'beach_level': self.beach_level,
            'plains_level': self.plains_level,
            'hills_level': self.hills_level,
            'mountain_level': self.mountain_level,
            'forest_moisture': self.forest_moisture,
            'swamp_moisture': self.swamp_moisture,
            'temperature_gradient': self.temperature_gradient,
            'smooth_iterations': self.smooth_iterations,
            'generate_beaches': self.generate_beaches,
            'generate_rivers': self.generate_rivers,
            'river_count': self.river_count,
            'city_count': self.city_count,
            'village_count': self.village_count,
            'mine_count': self.mine_count,
            'bandit_camp_count': self.bandit_camp_count,
            'ruins_count': self.ruins_count,
            'ignore_min_distance': self.ignore_min_distance
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeneratorParams':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# Guard type constants
GUARD_WARRIOR = "warrior"
GUARD_MAGE = "mage"
GUARD_SHADOW_ADEPT = "shadow_adept"
GUARD_HUNTER = "hunter"
GUARD_NONE = ""  # Empty slot

GUARD_TYPES = {
    GUARD_WARRIOR: "Воин",
    GUARD_MAGE: "Маг",
    GUARD_SHADOW_ADEPT: "Адепты тени",
    GUARD_HUNTER: "Охотник",
    GUARD_NONE: "Нет"
}

# Resource type constants for mines
RESOURCE_COPPER = "copper"
RESOURCE_IRON = "iron"
RESOURCE_SILVER = "silver"
RESOURCE_GOLD = "gold"
RESOURCE_MITHRIL = "mithril"

RESOURCE_TYPES = {
    RESOURCE_COPPER: "Медь",
    RESOURCE_IRON: "Железо",
    RESOURCE_SILVER: "Серебро",
    RESOURCE_GOLD: "Золото",
    RESOURCE_MITHRIL: "Мифрил"
}

# Quest type constants
QUEST_GATHER_RESOURCE = "gather_resource"
QUEST_HUNT_ANIMALS = "hunt_animals"
QUEST_DELIVER_MESSAGE = "deliver_message"
QUEST_CLEAR_LOCATION = "clear_location"
QUEST_COLLECT_ITEMS = "collect_items"

QUEST_TYPES = {
    QUEST_GATHER_RESOURCE: "Добыть ресурс",
    QUEST_HUNT_ANIMALS: "Охота на животных",
    QUEST_DELIVER_MESSAGE: "Доставить послание",
    QUEST_CLEAR_LOCATION: "Зачистка локации",
    QUEST_COLLECT_ITEMS: "Собрать предметы"
}

# Quest target constants - resources
QUEST_TARGET_WOOD = "wood"
QUEST_TARGET_COPPER = "copper"
QUEST_TARGET_IRON = "iron"
QUEST_TARGET_SILVER = "silver"
QUEST_TARGET_GOLD = "gold"
QUEST_TARGET_MITHRIL = "mithril"

QUEST_RESOURCE_TARGETS = {
    QUEST_TARGET_WOOD: "Древесина",
    QUEST_TARGET_COPPER: "Медная руда",
    QUEST_TARGET_IRON: "Железная руда",
    QUEST_TARGET_SILVER: "Серебряная руда",
    QUEST_TARGET_GOLD: "Золотая руда",
    QUEST_TARGET_MITHRIL: "Мифриловая руда"
}

# Quest target constants - animals
QUEST_TARGET_WOLF = "wolf"
QUEST_TARGET_BEAR = "bear"
QUEST_TARGET_DEER = "deer"

QUEST_ANIMAL_TARGETS = {
    QUEST_TARGET_WOLF: "Волк",
    QUEST_TARGET_BEAR: "Медведь",
    QUEST_TARGET_DEER: "Олень"
}

# Combined quest targets dictionary
QUEST_TARGETS = {
    **QUEST_RESOURCE_TARGETS,
    **QUEST_ANIMAL_TARGETS
}

# Difficulty levels
QUEST_DIFFICULTIES = {
    1: "Легкий",
    2: "Обычный",
    3: "Сложный",
    4: "Очень сложный",
    5: "Героический"
}

# Locations that can give quests
QUEST_GIVER_LOCATIONS = [
    LOCATION_CAPITAL,
    LOCATION_CITY,
    LOCATION_VILLAGE,
    LOCATION_MAGIC_SCHOOL,
    LOCATION_WARRIOR_ACADEMY,
    LOCATION_SECRET_CAMP
]

# Locations that can be cleared (have floors)
QUEST_CLEARABLE_LOCATIONS = [
    LOCATION_MINE,
    LOCATION_RUINS
]

# Floor type constants for mines and ruins
FLOOR_MINE = "mine"
FLOOR_DARK_MINE = "dark_mine"
FLOOR_GLOOMY_MINE = "gloomy_mine"
FLOOR_BASEMENT = "basement"
FLOOR_DARK_BASEMENT = "dark_basement"
FLOOR_GLOOMY_BASEMENT = "gloomy_basement"
FLOOR_ABYSS = "abyss"
FLOOR_NONE = ""  # Empty floor slot

FLOOR_TYPES = {
    FLOOR_NONE: "Нет",
    FLOOR_MINE: "Шахта",
    FLOOR_DARK_MINE: "Темная шахта",
    FLOOR_GLOOMY_MINE: "Мрачная шахта",
    FLOOR_BASEMENT: "Подвал",
    FLOOR_DARK_BASEMENT: "Темный подвал",
    FLOOR_GLOOMY_BASEMENT: "Мрачный подвал",
    FLOOR_ABYSS: "Преисподня"
}

# Floor NPC type constants
FLOOR_NPC_MINER = "miner"
FLOOR_NPC_WARRIOR = "warrior"
FLOOR_NPC_MAGE = "mage"
FLOOR_NPC_HUNTER = "hunter"
FLOOR_NPC_BANDIT = "bandit"
FLOOR_NPC_UNDEAD = "undead"
FLOOR_NPC_NECROMANCER = "necromancer"
FLOOR_NPC_SHADOW_ADEPT = "shadow_adept"
FLOOR_NPC_RAT = "rat"
FLOOR_NPC_ZOMBIE = "zombie"
FLOOR_NPC_SKELETON = "skeleton"
FLOOR_NPC_GHOST = "ghost"
FLOOR_NPC_SPIDER = "spider"
FLOOR_NPC_GOLEM = "golem"
FLOOR_NPC_DEMON = "demon"
FLOOR_NPC_NONE = ""

FLOOR_NPC_TYPES = {
    FLOOR_NPC_NONE: "Нет",
    FLOOR_NPC_MINER: "Шахтер",
    FLOOR_NPC_WARRIOR: "Воин",
    FLOOR_NPC_MAGE: "Маг",
    FLOOR_NPC_HUNTER: "Охотник",
    FLOOR_NPC_BANDIT: "Бандит",
    FLOOR_NPC_UNDEAD: "Нежить",
    FLOOR_NPC_NECROMANCER: "Некромант",
    FLOOR_NPC_SHADOW_ADEPT: "Адепт тени",
    FLOOR_NPC_RAT: "Крыса",
    FLOOR_NPC_ZOMBIE: "Зомби",
    FLOOR_NPC_SKELETON: "Скелет",
    FLOOR_NPC_GHOST: "Призрак",
    FLOOR_NPC_SPIDER: "Паук",
    FLOOR_NPC_GOLEM: "Голем",
    FLOOR_NPC_DEMON: "Демон"
}

# NPC rank constants (1-4)
FLOOR_NPC_RANKS = {
    1: "Ранг 1 (Новичок)",
    2: "Ранг 2 (Обычный)",
    3: "Ранг 3 (Опытный)",
    4: "Ранг 4 (Эксперт)"
}


@dataclass
class Quest:
    """Represents a regular quest configuration for a location."""
    id: str = ""  # Unique identifier
    quest_type: str = QUEST_GATHER_RESOURCE  # Type of quest
    name: str = ""  # Quest name
    description: str = ""  # Quest description
    target_type: str = QUEST_TARGET_WOOD  # Target type (resource or animal)
    target_item_id: str = ""  # Target item ID (for collect_items quest type)
    target_amount: int = 10  # Amount to gather/hunt/collect
    time_limit: int = 0  # Time limit in turns (0 = no limit)
    difficulty: int = 1  # Difficulty level (1-5)
    # Target location (for deliver_message and clear_location)
    target_location_id: str = ""  # Target location ID
    target_location_name: str = ""  # Target location name (for display)
    target_floor: int = 0  # Target floor (0 = all floors, 1-10 = specific floor)
    # Rewards
    reward_gold: int = 100  # Gold reward
    reward_item_id: str = ""  # Item ID reward (alternative to gold)
    reward_item_amount: int = 1  # Amount of reward items
    reward_exp: int = 50  # Experience reward
    reward_reputation: int = 5  # Reputation reward
    # Availability
    is_repeatable: bool = True  # Whether quest can be repeated
    cooldown: int = 100  # Cooldown in turns before quest can be taken again
    # Requirements
    min_player_attitude: int = 0  # Minimum player_attitude required to get this quest (-10 to 10)
    min_player_rank: int = 0  # Minimum player rank required (0 = no requirement, 1-4 = specific rank)
    min_player_level: int = 0  # Minimum player level required (0 = no requirement, 1-100 = specific level)
    # Penalties
    fail_attitude_penalty: int = 0  # Penalty to player_attitude when quest is failed (0-20)
    # Events
    completion_event_id: str = ""  # Event ID to trigger on quest completion (in addition to rewards)
    # Scaling
    scaling_factor: float = 1.1  # Coefficient for scaling rewards/targets by player level

    def __post_init__(self):
        """Generate ID if not provided."""
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        data = {
            'id': self.id,
            'quest_type': self.quest_type,
            'name': self.name,
            'description': self.description,
            'time_limit': self.time_limit,
            'difficulty': self.difficulty,
            'reward_gold': self.reward_gold,
            'reward_item_id': self.reward_item_id,
            'reward_item_amount': self.reward_item_amount,
            'reward_exp': self.reward_exp,
            'reward_reputation': self.reward_reputation,
            'is_repeatable': self.is_repeatable,
            'cooldown': self.cooldown,
            'min_player_attitude': self.min_player_attitude,
            'min_player_rank': self.min_player_rank,
            'min_player_level': self.min_player_level,
            'fail_attitude_penalty': self.fail_attitude_penalty,
            'completion_event_id': self.completion_event_id,
            'scaling_factor': self.scaling_factor
        }
        # Only include target_type and target_amount for quests that use them
        if self.quest_type in (QUEST_GATHER_RESOURCE, QUEST_HUNT_ANIMALS):
            data['target_type'] = self.target_type
            data['target_amount'] = self.target_amount
        elif self.quest_type == QUEST_COLLECT_ITEMS:
            data['target_item_id'] = self.target_item_id
            data['target_amount'] = self.target_amount
        # Only include location fields for quests that use them
        if self.quest_type in (QUEST_DELIVER_MESSAGE, QUEST_CLEAR_LOCATION):
            data['target_location_id'] = self.target_location_id
            data['target_location_name'] = self.target_location_name
            if self.quest_type == QUEST_CLEAR_LOCATION:
                data['target_floor'] = self.target_floor
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Quest':
        """Create from dictionary."""
        # Backward compatibility: support old field names
        target_loc_id = data.get('target_location_id', data.get('destination_id', ''))
        target_loc_name = data.get('target_location_name', data.get('destination_name', ''))
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            quest_type=data.get('quest_type', QUEST_GATHER_RESOURCE),
            name=data.get('name', ''),
            description=data.get('description', ''),
            target_type=data.get('target_type', QUEST_TARGET_WOOD),
            target_item_id=data.get('target_item_id', ''),
            target_amount=data.get('target_amount', 10),
            time_limit=data.get('time_limit', 0),
            difficulty=data.get('difficulty', 1),
            target_location_id=target_loc_id,
            target_location_name=target_loc_name,
            target_floor=data.get('target_floor', 0),
            reward_gold=data.get('reward_gold', 100),
            reward_item_id=data.get('reward_item_id', ''),
            reward_item_amount=data.get('reward_item_amount', 1),
            reward_exp=data.get('reward_exp', 50),
            reward_reputation=data.get('reward_reputation', 5),
            is_repeatable=data.get('is_repeatable', True),
            cooldown=data.get('cooldown', 100),
            min_player_attitude=data.get('min_player_attitude', 0),
            min_player_rank=data.get('min_player_rank', 0),
            min_player_level=data.get('min_player_level', 0),
            fail_attitude_penalty=data.get('fail_attitude_penalty', 0),
            completion_event_id=data.get('completion_event_id', ''),
            scaling_factor=data.get('scaling_factor', 1.1)
        )

    def is_empty(self) -> bool:
        """Check if quest is empty/unconfigured."""
        return not self.name

    def get_type_display(self) -> str:
        """Get display name for quest type."""
        return QUEST_TYPES.get(self.quest_type, self.quest_type)

    def get_target_display(self) -> str:
        """Get display name for quest target."""
        return QUEST_TARGETS.get(self.target_type, self.target_type)

    def get_difficulty_display(self) -> str:
        """Get display name for difficulty level."""
        return QUEST_DIFFICULTIES.get(self.difficulty, f"Уровень {self.difficulty}")

    def get_short_description(self) -> str:
        """Get a short description of the quest."""
        if self.quest_type == QUEST_GATHER_RESOURCE:
            return f"Добыть {self.target_amount}x {self.get_target_display()}"
        elif self.quest_type == QUEST_HUNT_ANIMALS:
            return f"Убить {self.target_amount}x {self.get_target_display()}"
        elif self.quest_type == QUEST_DELIVER_MESSAGE:
            dest = self.target_location_name or "???"
            return f"Доставить послание в {dest}"
        elif self.quest_type == QUEST_CLEAR_LOCATION:
            loc = self.target_location_name or "???"
            if self.target_floor > 0:
                return f"Зачистить этаж {self.target_floor} в {loc}"
            return f"Зачистить {loc}"
        elif self.quest_type == QUEST_COLLECT_ITEMS:
            item = self.target_item_id or "???"
            return f"Собрать {self.target_amount}x [{item}]"
        return self.name or "Неизвестный квест"


def _create_empty_quests() -> List['Quest']:
    """Create empty quest list for location."""
    return []


@dataclass
class FloorNPC:
    """Represents an NPC configuration on a floor."""
    npc_type: str = FLOOR_NPC_NONE  # Type of NPC
    rank: int = 1  # NPC rank (1-4)
    count: int = 0  # Number of NPCs of this type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        return {
            'type': self.npc_type,
            'rank': self.rank,
            'count': self.count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FloorNPC':
        """Create from dictionary."""
        return cls(
            npc_type=data.get('type', FLOOR_NPC_NONE),
            rank=data.get('rank', 1),
            count=data.get('count', 0)
        )

    def is_empty(self) -> bool:
        """Check if NPC slot is empty."""
        return self.npc_type == FLOOR_NPC_NONE or self.count == 0

    def get_display_name(self) -> str:
        """Get display name for this NPC configuration."""
        if self.is_empty():
            return ""
        npc_name = FLOOR_NPC_TYPES.get(self.npc_type, self.npc_type)
        return f"{self.count}x {npc_name} (Р{self.rank})"


def _create_empty_floor_npcs() -> List['FloorNPC']:
    """Create empty NPC list for floor."""
    return []


@dataclass
class Floor:
    """Represents a floor in a mine or ruins."""
    floor_number: int = 1  # Floor number (1-10)
    floor_type: str = FLOOR_NONE  # Type of floor (mine, dark_mine, etc.)
    size: int = 1  # Size of floor (1-10)
    npcs: List[FloorNPC] = field(default_factory=_create_empty_floor_npcs)  # List of NPC configurations

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        data = {
            'floor_number': self.floor_number,
            'floor_type': self.floor_type,
            'size': self.size
        }
        # Only save non-empty NPCs
        npcs_data = [npc.to_dict() for npc in self.npcs if not npc.is_empty()]
        if npcs_data:
            data['npcs'] = npcs_data
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Floor':
        """Create from dictionary."""
        # Load NPCs list
        npcs = []
        if 'npcs' in data:
            npcs = [FloorNPC.from_dict(npc_data) for npc_data in data['npcs']]
        # Backward compatibility: handle old 'npc' string field
        elif 'npc' in data and data['npc']:
            # Old format stored NPC as string, skip it
            pass

        return cls(
            floor_number=data.get('floor_number', 1),
            floor_type=data.get('floor_type', FLOOR_NONE),
            size=data.get('size', 1),
            npcs=npcs
        )

    def is_empty(self) -> bool:
        """Check if floor slot is empty."""
        return self.floor_type == FLOOR_NONE

    def get_total_npc_count(self) -> int:
        """Get total count of all NPCs on this floor."""
        return sum(npc.count for npc in self.npcs if not npc.is_empty())

    def get_npc_summary(self) -> str:
        """Get a short summary of NPCs on this floor."""
        active_npcs = [npc for npc in self.npcs if not npc.is_empty()]
        if not active_npcs:
            return "-"
        total = sum(npc.count for npc in active_npcs)
        return f"{total} NPC ({len(active_npcs)} тип.)"

    def add_npc(self, npc_type: str, rank: int, count: int) -> None:
        """Add or update NPC configuration."""
        # Check if this type+rank already exists
        for existing in self.npcs:
            if existing.npc_type == npc_type and existing.rank == rank:
                existing.count += count
                return
        # Add new NPC
        self.npcs.append(FloorNPC(npc_type=npc_type, rank=rank, count=count))

    def remove_npc(self, index: int) -> bool:
        """Remove NPC at index. Returns True if removed."""
        if 0 <= index < len(self.npcs):
            self.npcs.pop(index)
            return True
        return False

    def clear_npcs(self) -> None:
        """Remove all NPCs from this floor."""
        self.npcs = []


def _create_empty_floors() -> List['Floor']:
    """Create 10 empty floor slots."""
    return [Floor(floor_number=i+1) for i in range(10)]


@dataclass
class Guard:
    """Represents a guard slot for a location."""
    guard_type: str = GUARD_NONE  # Type of guard (warrior, mage, shadow_adept, hunter)
    rank: int = 1  # Guard rank (1-4)
    count: int = 0  # Number of guards (0-20)
    patrol_radius: int = 5  # Patrol radius (3-20)
    respawn_time: int = 0  # Respawn time in turns (0-999)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        return {
            'type': self.guard_type,
            'rank': self.rank,
            'count': self.count,
            'patrol_radius': self.patrol_radius,
            'respawn_time': self.respawn_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Guard':
        """Create from dictionary."""
        return cls(
            guard_type=data.get('type', GUARD_NONE),
            rank=data.get('rank', 1),
            count=data.get('count', 0),
            patrol_radius=data.get('patrol_radius', 5),
            respawn_time=data.get('respawn_time', 0)
        )

    def is_empty(self) -> bool:
        """Check if guard slot is empty."""
        return self.guard_type == GUARD_NONE or self.count == 0


def _create_empty_guards() -> List[Guard]:
    """Create 5 empty guard slots."""
    return [Guard() for _ in range(5)]


# Merchant rank constants
MERCHANT_RANK_1 = 1  # Бродячий торговец
MERCHANT_RANK_2 = 2  # Странствующий купец
MERCHANT_RANK_3 = 3  # Караванщик
MERCHANT_RANK_4 = 4  # Гильдейский торговец

MERCHANT_RANKS = {
    MERCHANT_RANK_1: "Бродячий торговец",
    MERCHANT_RANK_2: "Странствующий купец",
    MERCHANT_RANK_3: "Караванщик",
    MERCHANT_RANK_4: "Гильдейский торговец"
}

# Merchant specialization constants
SPEC_JEWELRY = "jewelry"        # Украшения
SPEC_RESOURCES = "resources"    # Ресурсы и материалы
SPEC_ARMOR = "armor"            # Броня
SPEC_WEAPONS = "weapons"        # Оружие
SPEC_POTIONS = "potions"        # Зелья

MERCHANT_SPECIALIZATIONS = {
    SPEC_JEWELRY: "Украшения",
    SPEC_RESOURCES: "Ресурсы и материалы",
    SPEC_ARMOR: "Броня",
    SPEC_WEAPONS: "Оружие",
    SPEC_POTIONS: "Зелья"
}


@dataclass
class MerchantWaypoint:
    """Represents a waypoint (stop point) in a merchant's route."""
    x: int
    y: int
    duration: int = 10  # Duration of stay at this waypoint (in game turns)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        return {
            'x': self.x,
            'y': self.y,
            'duration': self.duration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MerchantWaypoint':
        """Create from dictionary."""
        return cls(
            x=data['x'],
            y=data['y'],
            duration=data.get('duration', 10)
        )


@dataclass
class Merchant:
    """Represents a merchant with a route on the map."""
    id: str = ""  # Unique identifier
    name: str = ""  # Merchant name
    rank: int = 1  # Merchant rank (1-4)
    waypoints: List[MerchantWaypoint] = field(default_factory=list)  # Route waypoints
    current_waypoint_index: int = 0  # Current position in route (for game state)
    color: Tuple[int, int, int] = (255, 165, 0)  # Display color (orange by default)
    is_loop: bool = True  # Whether route loops back to start
    specializations: Dict[str, int] = field(default_factory=dict)  # Category -> rank (1-4), 0 = disabled
    respawn_time: int = 200  # Respawn time in game turns
    assortment_update: int = 100  # Turns until assortment update (10-1000)
    wealth: int = 3000  # Merchant's wealth/state (1000-50000)

    def __post_init__(self):
        """Generate ID if not provided."""
        if not self.id:
            self.id = str(uuid.uuid4())
        # Initialize empty specializations if not provided
        if not self.specializations:
            self.specializations = {key: 0 for key in MERCHANT_SPECIALIZATIONS.keys()}

    def add_waypoint(self, x: int, y: int, duration: int = 10) -> None:
        """Add a waypoint to the route."""
        self.waypoints.append(MerchantWaypoint(x=x, y=y, duration=duration))

    def remove_waypoint(self, index: int) -> bool:
        """Remove waypoint at index. Returns True if removed."""
        if 0 <= index < len(self.waypoints):
            self.waypoints.pop(index)
            return True
        return False

    def update_waypoint(self, index: int, x: int = None, y: int = None, duration: int = None) -> bool:
        """Update waypoint at index. Returns True if updated."""
        if 0 <= index < len(self.waypoints):
            wp = self.waypoints[index]
            if x is not None:
                wp.x = x
            if y is not None:
                wp.y = y
            if duration is not None:
                wp.duration = duration
            return True
        return False

    def get_route_length(self) -> int:
        """Get the number of waypoints in the route."""
        return len(self.waypoints)

    def is_route_closed(self) -> bool:
        """Check if route is closed (first and last waypoint are the same)."""
        if len(self.waypoints) < 2:
            return False
        first = self.waypoints[0]
        last = self.waypoints[-1]
        return first.x == last.x and first.y == last.y

    def set_specialization(self, spec_key: str, rank: int) -> None:
        """Set specialization rank (0 = disabled, 1-4 = enabled with rank)."""
        if spec_key in MERCHANT_SPECIALIZATIONS:
            self.specializations[spec_key] = max(0, min(4, rank))

    def get_specialization(self, spec_key: str) -> int:
        """Get specialization rank (0 if disabled)."""
        return self.specializations.get(spec_key, 0)

    def get_active_specializations(self) -> Dict[str, int]:
        """Get only active specializations (rank > 0)."""
        return {k: v for k, v in self.specializations.items() if v > 0}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        return {
            'id': self.id,
            'name': self.name,
            'rank': self.rank,
            'waypoints': [wp.to_dict() for wp in self.waypoints],
            'color': list(self.color),
            'is_loop': self.is_loop,
            'specializations': self.specializations,
            'respawn_time': self.respawn_time,
            'assortment_update': self.assortment_update,
            'wealth': self.wealth
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Merchant':
        """Create from dictionary."""
        waypoints = [MerchantWaypoint.from_dict(wp) for wp in data.get('waypoints', [])]
        color = tuple(data.get('color', [255, 165, 0]))
        # Load specializations with defaults
        specs = data.get('specializations', {})
        full_specs = {key: specs.get(key, 0) for key in MERCHANT_SPECIALIZATIONS.keys()}
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            rank=data.get('rank', 1),
            waypoints=waypoints,
            color=color,
            is_loop=data.get('is_loop', True),
            specializations=full_specs,
            respawn_time=data.get('respawn_time', 200),
            assortment_update=data.get('assortment_update', 100),
            wealth=data.get('wealth', 3000)
        )


@dataclass
class MapLocation:
    """Represents a location on the map."""
    x: int
    y: int
    location_type: str
    name: str = ""
    id: str = ""  # Unique identifier for the location
    rank: int = 1  # Rank for mines, ruins (1-4)
    shop_rank: int = 1  # Shop rank for cities, villages (1-4)
    miners_count: int = 0  # Number of miners for mines (0-10)
    respawn_time: int = 0  # Respawn time for mines and animal spawns (0-999)
    resource_type: str = "copper"  # Resource type for mines: copper, iron, silver, gold, mithril
    player_attitude: int = 0  # Attitude towards player (-10 to 10)
    spawn_radius: int = 5  # Spawn radius for NPCs and animals related to this location (3-10 for animals, 1-20 for others)
    animal_count: int = 1  # Number of animals for spawn points (1-10)
    guards: List[Guard] = field(default_factory=_create_empty_guards)  # Guard slots (max 5)
    connections: List[Tuple[int, int]] = field(default_factory=list)  # Connections: [(target_x, target_y), ...]
    floors: List[Floor] = field(default_factory=_create_empty_floors)  # Floor slots for mines/ruins (max 10)
    quests: List[Quest] = field(default_factory=_create_empty_quests)  # Regular quests for quest-giving locations

    def get_id(self) -> str:
        """Get unique identifier for this location (based on coordinates)."""
        return f"{self.x},{self.y}"

    def add_connection(self, target_x: int, target_y: int) -> bool:
        """Add connection to another location. Returns True if added, False if already exists."""
        conn = (target_x, target_y)
        if conn not in self.connections:
            self.connections.append(conn)
            return True
        return False

    def remove_connection(self, target_x: int, target_y: int) -> bool:
        """Remove connection to another location. Returns True if removed, False if not found."""
        conn = (target_x, target_y)
        if conn in self.connections:
            self.connections.remove(conn)
            return True
        return False

    def has_connection_to(self, target_x: int, target_y: int) -> bool:
        """Check if this location has connection to target."""
        return (target_x, target_y) in self.connections

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        data = {
            'x': self.x,
            'y': self.y,
            'type': self.location_type,
            'name': self.name,
            'id': self.id,  # Always save ID
            'player_attitude': self.player_attitude,
            'spawn_radius': self.spawn_radius,  # Save spawn radius for all locations
            'rank': self.rank  # Save rank for all locations (1-4)
        }
        # Only save shop_rank for settlements
        if self.location_type in [LOCATION_CITY, LOCATION_CAPITAL, LOCATION_VILLAGE]:
            data['shop_rank'] = self.shop_rank
        # Only save miners_count, respawn_time and resource_type for mines
        if self.location_type == LOCATION_MINE:
            data['miners_count'] = self.miners_count
            data['respawn_time'] = self.respawn_time
            data['resource_type'] = self.resource_type
        # Save animal_count, respawn_time and spawn_radius for animal spawn points
        if self.location_type in [LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER]:
            data['animal_count'] = self.animal_count
            data['respawn_time'] = self.respawn_time
            data['spawn_radius'] = self.spawn_radius
        # Save guards for locations that have them
        if self.location_type in [LOCATION_VILLAGE, LOCATION_CITY, LOCATION_CAPITAL,
                                  LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY, 'secret_camp']:
            # Only save non-empty guards
            guards_data = [guard.to_dict() for guard in self.guards if not guard.is_empty()]
            if guards_data:
                data['guards'] = guards_data
        # Save connections if any
        if self.connections:
            data['connections'] = [[x, y] for x, y in self.connections]
        # Save floors for mines and ruins
        if self.location_type in [LOCATION_MINE, LOCATION_RUINS]:
            floors_data = [floor.to_dict() for floor in self.floors if not floor.is_empty()]
            if floors_data:
                data['floors'] = floors_data
        # Save quests for quest-giving locations
        if self.location_type in QUEST_GIVER_LOCATIONS:
            quests_data = [quest.to_dict() for quest in self.quests if not quest.is_empty()]
            if quests_data:
                data['quests'] = quests_data
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MapLocation':
        """Create from dictionary."""
        connections = []
        if 'connections' in data:
            connections = [tuple(conn) for conn in data['connections']]

        # Generate new ID if not present (for backward compatibility)
        location_id = data.get('id', '')
        if not location_id:
            location_id = str(uuid.uuid4())

        # Load guards data (for backward compatibility, create empty guards if not present)
        guards = []
        if 'guards' in data:
            guards = [Guard.from_dict(guard_data) for guard_data in data['guards']]
        # Fill remaining slots with empty guards to maintain 5 total slots
        while len(guards) < 5:
            guards.append(Guard())

        # Load floors data (for mines and ruins)
        floors = []
        if 'floors' in data:
            floors = [Floor.from_dict(floor_data) for floor_data in data['floors']]
        # Fill remaining slots with empty floors to maintain 10 total slots
        existing_floor_nums = {f.floor_number for f in floors}
        for i in range(1, 11):
            if i not in existing_floor_nums:
                floors.append(Floor(floor_number=i))
        # Sort floors by floor number
        floors.sort(key=lambda f: f.floor_number)

        # Load quests data (for quest-giving locations)
        quests = []
        if 'quests' in data:
            quests = [Quest.from_dict(quest_data) for quest_data in data['quests']]

        return cls(
            x=data['x'],
            y=data['y'],
            location_type=data['type'],
            name=data.get('name', ''),
            id=location_id,
            rank=data.get('rank', 1),
            shop_rank=data.get('shop_rank', 1),
            miners_count=data.get('miners_count', 0),
            respawn_time=data.get('respawn_time', 0),
            resource_type=data.get('resource_type', 'copper'),
            player_attitude=data.get('player_attitude', 0),
            spawn_radius=data.get('spawn_radius', 5),
            animal_count=data.get('animal_count', 1),
            guards=guards,
            connections=connections,
            floors=floors,
            quests=quests
        )


@dataclass
class MapConfig:
    """Configuration for map locations and their properties."""
    locations: List[MapLocation] = field(default_factory=list)
    starting_village: Optional[Tuple[int, int]] = None  # (x, y) coordinates
    merchants: List[Merchant] = field(default_factory=list)  # List of merchants with routes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        data = {
            'version': '1.0',
            'locations': [loc.to_dict() for loc in self.locations]
        }
        if self.starting_village:
            data['starting_village'] = {
                'x': self.starting_village[0],
                'y': self.starting_village[1]
            }
        # Save merchants
        if self.merchants:
            data['merchants'] = [merchant.to_dict() for merchant in self.merchants]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], locations: List[MapLocation] = None) -> 'MapConfig':
        """Create from dictionary."""
        config_locations = [MapLocation.from_dict(loc) for loc in data.get('locations', [])]

        # If locations provided (from main map), merge configs
        if locations:
            # Update locations with config data
            for loc in locations:
                for config_loc in config_locations:
                    if loc.x == config_loc.x and loc.y == config_loc.y:
                        loc.miners_count = config_loc.miners_count
                        loc.respawn_time = config_loc.respawn_time
                        loc.player_attitude = config_loc.player_attitude
                        loc.connections = config_loc.connections
                        break

        starting_village = None
        if 'starting_village' in data:
            sv_data = data['starting_village']
            starting_village = (sv_data['x'], sv_data['y'])

        # Load merchants
        merchants = [Merchant.from_dict(m) for m in data.get('merchants', [])]

        return cls(
            locations=config_locations if not locations else locations,
            starting_village=starting_village,
            merchants=merchants
        )


@dataclass
class GeneratedMap:
    """Container for generated map data."""
    width: int
    height: int
    seed: int
    biomes: List[List[str]]
    elevation: List[List[float]]
    moisture: List[List[float]]
    locations: List[MapLocation] = field(default_factory=list)
    starting_village: Optional[MapLocation] = None
    merchants: List[Merchant] = field(default_factory=list)  # List of merchants with routes

    def get_biome(self, x: int, y: int) -> str:
        """Get biome at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.biomes[y][x]
        return BIOME_WATER

    def set_biome(self, x: int, y: int, biome: str) -> None:
        """Set biome at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.biomes[y][x] = biome

    def is_passable(self, x: int, y: int) -> bool:
        """Check if tile is passable."""
        return self.get_biome(x, y) in PASSABLE_BIOMES

    def get_location_at(self, x: int, y: int) -> Optional[MapLocation]:
        """Get location at coordinates if any."""
        for loc in self.locations:
            if loc.x == x and loc.y == y:
                return loc
        return None

    def add_location(self, location: MapLocation) -> None:
        """Add a location to the map."""
        self.locations.append(location)

    def remove_location(self, x: int, y: int) -> bool:
        """Remove location at coordinates."""
        for i, loc in enumerate(self.locations):
            if loc.x == x and loc.y == y:
                if self.starting_village and loc == self.starting_village:
                    self.starting_village = None
                self.locations.pop(i)
                return True
        return False

    def validate_connections(self) -> int:
        """
        Validate all connections and remove invalid ones.
        Returns the number of invalid connections removed.
        """
        removed_count = 0

        for location in self.locations:
            valid_connections = []
            for target_x, target_y in location.connections:
                # Check if target location exists
                target_location = self.get_location_at(target_x, target_y)
                if target_location:
                    valid_connections.append((target_x, target_y))
                else:
                    removed_count += 1

            location.connections = valid_connections

        return removed_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving (terrain only)."""
        data = {
            'version': '1.0',
            'width': self.width,
            'height': self.height,
            'seed': self.seed,
            'biomes': self.biomes
        }
        return data

    def to_config_dict(self) -> Dict[str, Any]:
        """Convert location config to dictionary for saving."""
        config = MapConfig(locations=self.locations, merchants=self.merchants)
        if self.starting_village:
            config.starting_village = (self.starting_village.x, self.starting_village.y)
        return config.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any], config_data: Dict[str, Any] = None) -> 'GeneratedMap':
        """Create from dictionary."""
        width = data['width']
        height = data['height']
        seed = data.get('seed', 0)
        biomes = data['biomes']

        # Create empty elevation/moisture maps
        elevation = [[0.5 for _ in range(width)] for _ in range(height)]
        moisture = [[0.5 for _ in range(width)] for _ in range(height)]

        # Load locations from config if provided, otherwise from main data (backward compatibility)
        locations = []
        starting_village = None
        merchants = []

        if config_data:
            # New format: locations in separate config file
            config = MapConfig.from_dict(config_data)
            locations = config.locations
            merchants = config.merchants

            # Find starting village
            if config.starting_village:
                sv_x, sv_y = config.starting_village
                for loc in locations:
                    if loc.x == sv_x and loc.y == sv_y:
                        starting_village = loc
                        break
        else:
            # Old format: locations in main map file (backward compatibility)
            locations = [MapLocation.from_dict(loc) for loc in data.get('locations', [])]

            # Find starting village in locations list (by coordinates)
            if 'starting_village' in data:
                sv_data = data['starting_village']
                sv_x, sv_y = sv_data['x'], sv_data['y']
                sv_name = sv_data.get('name', 'Тихая')

                # Find matching location in list
                for loc in locations:
                    if loc.x == sv_x and loc.y == sv_y:
                        starting_village = loc
                        if not loc.name:
                            loc.name = sv_name
                        break

                # If not found in locations, create new and add
                if starting_village is None:
                    starting_village = MapLocation(
                        x=sv_x,
                        y=sv_y,
                        location_type=LOCATION_VILLAGE,
                        name=sv_name,
                        id=str(uuid.uuid4())
                    )
                    locations.append(starting_village)

        # Create map instance
        map_instance = cls(
            width=width,
            height=height,
            seed=seed,
            biomes=biomes,
            elevation=elevation,
            moisture=moisture,
            locations=locations,
            starting_village=starting_village,
            merchants=merchants
        )

        # Validate connections (remove invalid ones)
        removed = map_instance.validate_connections()
        if removed > 0:
            print(f"Внимание: удалено {removed} недействительных связей")

        return map_instance

    def add_merchant(self, merchant: Merchant) -> None:
        """Add a merchant to the map."""
        self.merchants.append(merchant)

    def remove_merchant(self, merchant_id: str) -> bool:
        """Remove merchant by ID. Returns True if removed."""
        for i, merchant in enumerate(self.merchants):
            if merchant.id == merchant_id:
                self.merchants.pop(i)
                return True
        return False

    def get_merchant_by_id(self, merchant_id: str) -> Optional[Merchant]:
        """Get merchant by ID."""
        for merchant in self.merchants:
            if merchant.id == merchant_id:
                return merchant
        return None

    def get_merchant_at(self, x: int, y: int) -> Optional[Merchant]:
        """Get merchant that has a waypoint at the given coordinates."""
        for merchant in self.merchants:
            for wp in merchant.waypoints:
                if wp.x == x and wp.y == y:
                    return merchant
        return None

    def get_merchants_count(self) -> int:
        """Get the number of merchants on the map."""
        return len(self.merchants)


class MapGenerator:
    """Procedural map generator using Perlin noise."""

    # Location names
    CITY_NAMES = [
        "Кристальград", "Златоград", "Серебряный Пик", "Королевская Гавань",
        "Драконий Утёс", "Орлиное Гнездо", "Железный Форт", "Солнечный Берег",
        "Лунная Крепость", "Звёздная Твердыня", "Каменный Страж", "Древний Оплот"
    ]

    VILLAGE_NAMES = [
        "Тихая", "Дубравка", "Речная", "Лесная", "Полянка", "Холмовка",
        "Берёзовка", "Ивовка", "Сосновка", "Ельники", "Озёрная", "Луговая",
        "Пригорье", "Заречье", "Подгорная", "Светлая", "Росная", "Туманная",
        "Привольная", "Раздольная", "Ключевая", "Родниковая", "Медовая",
        "Яблоневка", "Вишнёвка", "Грибная", "Охотничья", "Рыбацкая"
    ]

    MINE_NAMES = [
        "Железная жила", "Медный рудник", "Серебряная шахта", "Золотые копи",
        "Угольный разрез", "Изумрудная штольня", "Рубиновая пещера",
        "Сапфировый грот", "Алмазные недра", "Мифриловая жила",
        "Адамантитовая шахта", "Обсидиановая пещера", "Кварцевые залежи",
        "Аметистовый грот", "Малахитовая шахта", "Ониксовые копи",
        "Топазовая жила", "Опаловый рудник"
    ]

    BANDIT_CAMP_NAMES = [
        "Волчье логово", "Разбойничий схрон", "Воровская нора",
        "Лагерь Кровавого Клыка", "Притон Чёрных Масок", "Убежище Теней",
        "Стоянка Головорезов", "Лежбище Мародёров", "Приют Изгоев",
        "Гнездо Ворон", "Логово Гадюк", "Берлога Медведей"
    ]

    RUINS_NAMES = [
        "Забытый храм", "Древние развалины", "Руины замка", "Проклятые катакомбы",
        "Заброшенный монастырь", "Разрушенная башня", "Павший бастион",
        "Мёртвый город", "Потерянное святилище", "Гробница древних",
        "Склеп королей", "Подземелье ужаса", "Лабиринт теней",
        "Обитель проклятых", "Чертоги забвения", "Пещера страха",
        "Колодец душ", "Врата бездны", "Алтарь тьмы", "Престол скорби",
        "Цитадель падших", "Оплот нежити", "Некрополь", "Усыпальница"
    ]

    MAGIC_SCHOOL_NAMES = ["Академия Магии", "Башня Волшебников", "Школа Чародейства"]
    WARRIOR_ACADEMY_NAMES = ["Академия Воинов", "Школа Боевых Искусств", "Арена Героев"]
    SECRET_CAMP_NAMES = ["Тайное убежище", "Скрытый лагерь", "Логово отшельника",
                        "Затерянный приют", "Укрытие мудреца", "Тайная поляна"]

    CAPITAL_NAMES = ["Королевская столица", "Имперский престол", "Великий Трон",
                    "Столица Империи", "Сердце Королевства", "Царский Град"]

    # Spawn point names by beast type
    SPAWN_NAMES = {
        LOCATION_SPAWN_WOLF: "Волчье логово",
        LOCATION_SPAWN_BEAR: "Медвежья берлога",
        LOCATION_SPAWN_DEER: "Оленья поляна"
    }

    def __init__(self, params: GeneratorParams = None):
        self.params = params or GeneratorParams()
        self._used_names: Dict[str, set] = {
            LOCATION_CITY: set(),
            LOCATION_CAPITAL: set(),
            LOCATION_VILLAGE: set(),
            LOCATION_MINE: set(),
            LOCATION_BANDIT_CAMP: set(),
            LOCATION_RUINS: set(),
            LOCATION_MAGIC_SCHOOL: set(),
            LOCATION_WARRIOR_ACADEMY: set(),
            LOCATION_SECRET_CAMP: set(),
            LOCATION_SPAWN_WOLF: set(),
            LOCATION_SPAWN_BEAR: set(),
            LOCATION_SPAWN_DEER: set()
        }

    def generate(self, params: GeneratorParams = None) -> GeneratedMap:
        """Generate a new map with given parameters."""
        if params:
            self.params = params

        # Initialize seed
        if self.params.seed is None:
            self.params.seed = random.randint(0, 2**31)

        random.seed(self.params.seed)

        # Reset used names
        for key in self._used_names:
            self._used_names[key].clear()

        # Generate noise maps with different seeds for variation
        elevation = self._generate_noise(
            self.params.elevation_scale,
            self.params.elevation_octaves,
            seed_offset=0
        )
        moisture = self._generate_noise(
            self.params.moisture_scale,
            self.params.moisture_octaves,
            seed_offset=10000  # Different seed for moisture map
        )

        # Normalize maps
        elevation = normalize_map(elevation)
        moisture = normalize_map(moisture)

        # Generate biomes
        biomes = self._generate_biomes(elevation, moisture)

        # Smooth biomes
        for _ in range(self.params.smooth_iterations):
            biomes = self._smooth_biomes(biomes)

        # Generate beaches
        if self.params.generate_beaches:
            biomes = self._generate_beaches(biomes)

        # Generate rivers
        if self.params.generate_rivers:
            biomes = self._generate_rivers(biomes, elevation)

        # Create map object
        generated_map = GeneratedMap(
            width=self.params.width,
            height=self.params.height,
            seed=self.params.seed,
            biomes=biomes,
            elevation=elevation,
            moisture=moisture
        )

        # Place locations
        self._place_locations(generated_map)

        return generated_map

    def _generate_noise(self, scale: float, octaves: int, seed_offset: int = 0) -> List[List[float]]:
        """Generate Perlin noise map with optional seed offset for variation."""
        noise_seed = self.params.seed + seed_offset if self.params.seed else seed_offset
        noise_gen = PerlinNoise(noise_seed)
        noise_map = []

        for y in range(self.params.height):
            row = []
            for x in range(self.params.width):
                nx = x / scale
                ny = y / scale
                value = noise_gen.octave_noise(nx, ny, octaves)
                row.append(value)
            noise_map.append(row)

        return noise_map

    def _generate_biomes(self, elevation: List[List[float]],
                         moisture: List[List[float]]) -> List[List[str]]:
        """Generate biome map from elevation and moisture."""
        biomes = []

        for y in range(self.params.height):
            row = []
            for x in range(self.params.width):
                e = elevation[y][x]
                m = moisture[y][x]

                # Apply temperature gradient
                if self.params.temperature_gradient:
                    temp_factor = y / self.params.height
                    e = e * (0.8 + 0.4 * temp_factor)
                    e = min(1.0, max(0.0, e))

                biome = self._determine_biome(e, m)
                row.append(biome)
            biomes.append(row)

        return biomes

    def _determine_biome(self, elevation: float, moisture: float) -> str:
        """Determine biome based on elevation and moisture."""
        if elevation < self.params.water_level:
            return BIOME_WATER
        elif elevation < self.params.beach_level:
            return BIOME_SAND
        elif elevation > self.params.mountain_level:
            return BIOME_MOUNTAIN
        elif elevation > self.params.hills_level:
            return BIOME_HILLS
        elif moisture > self.params.swamp_moisture and elevation < self.params.plains_level:
            return BIOME_SWAMP
        elif moisture > self.params.forest_moisture:
            return BIOME_FOREST
        else:
            return BIOME_PLAINS

    def _smooth_biomes(self, biomes: List[List[str]]) -> List[List[str]]:
        """Smooth biomes using neighbor voting."""
        smoothed = [[biomes[y][x] for x in range(self.params.width)]
                   for y in range(self.params.height)]

        for y in range(self.params.height):
            for x in range(self.params.width):
                neighbors = get_neighbors(x, y, self.params.width, self.params.height)
                biome_counts: Dict[str, int] = {}

                for nx, ny in neighbors:
                    b = biomes[ny][nx]
                    biome_counts[b] = biome_counts.get(b, 0) + 1

                current = biomes[y][x]
                biome_counts[current] = biome_counts.get(current, 0) + 2

                most_common = max(biome_counts.keys(), key=lambda k: biome_counts[k])
                smoothed[y][x] = most_common

        return smoothed

    def _generate_beaches(self, biomes: List[List[str]]) -> List[List[str]]:
        """Generate sand beaches around water."""
        result = [[biomes[y][x] for x in range(self.params.width)]
                 for y in range(self.params.height)]

        for y in range(self.params.height):
            for x in range(self.params.width):
                if biomes[y][x] != BIOME_WATER:
                    neighbors = get_neighbors(x, y, self.params.width, self.params.height)
                    has_water = any(biomes[ny][nx] == BIOME_WATER for nx, ny in neighbors)
                    if has_water and biomes[y][x] != BIOME_MOUNTAIN:
                        result[y][x] = BIOME_SAND

        return result

    def _generate_rivers(self, biomes: List[List[str]],
                        elevation: List[List[float]]) -> List[List[str]]:
        """Generate natural meandering rivers flowing from high to low elevation."""
        result = [[biomes[y][x] for x in range(self.params.width)]
                 for y in range(self.params.height)]

        # Find high points for river sources
        high_points = []
        for y in range(self.params.height):
            for x in range(self.params.width):
                if elevation[y][x] > self.params.hills_level and biomes[y][x] != BIOME_WATER:
                    high_points.append((x, y, elevation[y][x]))

        if not high_points:
            return result

        high_points.sort(key=lambda p: p[2], reverse=True)
        river_sources = high_points[:min(self.params.river_count * 3, len(high_points))]
        random.shuffle(river_sources)

        rivers_created = 0
        for sx, sy, _ in river_sources:
            if rivers_created >= self.params.river_count:
                break

            # Trace river path with natural meandering
            x, y = sx, sy
            path = [(x, y)]
            max_steps = self.params.width + self.params.height
            meander_direction = random.choice([-1, 1])  # Initial meander direction
            meander_strength = random.uniform(0.3, 0.6)  # How much it meanders

            for step in range(max_steps):
                if biomes[y][x] == BIOME_WATER:
                    break

                neighbors = get_neighbors(x, y, self.params.width, self.params.height, False)
                if not neighbors:
                    break

                # Sort neighbors by elevation
                sorted_neighbors = sorted(neighbors, key=lambda n: elevation[n[1]][n[0]])

                # Find candidates (neighbors lower than current)
                candidates = [n for n in sorted_neighbors if elevation[n[1]][n[0]] < elevation[y][x]]

                if not candidates:
                    break

                # Add meandering: occasionally prefer side neighbors over lowest
                if len(candidates) > 1 and random.random() < meander_strength:
                    # Prefer candidates that maintain meander direction
                    dx_preferred = meander_direction
                    side_candidates = [
                        n for n in candidates
                        if (n[0] - x) * dx_preferred > 0  # Moving in meander direction
                    ]
                    if side_candidates:
                        # Choose from side candidates, weighted by elevation
                        weights = [1.0 / (elevation[n[1]][n[0]] + 0.1) for n in side_candidates]
                        total = sum(weights)
                        r = random.random() * total
                        cumsum = 0
                        next_pos = side_candidates[0]
                        for i, w in enumerate(weights):
                            cumsum += w
                            if r <= cumsum:
                                next_pos = side_candidates[i]
                                break
                    else:
                        next_pos = candidates[0]  # Lowest neighbor

                    # Occasionally reverse meander direction
                    if random.random() < 0.15:
                        meander_direction *= -1
                else:
                    # Follow steepest descent
                    next_pos = candidates[0]

                x, y = next_pos

                if (x, y) in path:
                    break
                path.append((x, y))

            # Only create river if it reaches water or is long enough
            if len(path) > 10:
                # Draw river with variable width
                for i, (rx, ry) in enumerate(path):
                    # River gets wider as it flows
                    progress = i / len(path)
                    width = 1 if progress < 0.5 else (2 if progress < 0.8 else 3)

                    # Draw main river point
                    if result[ry][rx] not in [BIOME_WATER, BIOME_MOUNTAIN]:
                        result[ry][rx] = BIOME_WATER

                    # Widen river in later sections
                    if width > 1:
                        for dx in range(-width // 2, width // 2 + 1):
                            for dy in range(-width // 2, width // 2 + 1):
                                nx, ny = rx + dx, ry + dy
                                if (0 <= nx < self.params.width and
                                        0 <= ny < self.params.height and
                                        result[ny][nx] not in [BIOME_WATER, BIOME_MOUNTAIN]):
                                    # Don't widen too much, use probability
                                    if abs(dx) + abs(dy) <= width // 2 or random.random() < 0.3:
                                        result[ny][nx] = BIOME_WATER

                rivers_created += 1

        return result

    def _place_locations(self, game_map: GeneratedMap) -> None:
        """Place locations on the map."""
        # Place cities
        self._place_location_type(
            game_map, LOCATION_CITY, self.params.city_count,
            valid_biomes=[BIOME_PLAINS, BIOME_SAND],
            min_distance=20
        )

        # Place villages
        self._place_location_type(
            game_map, LOCATION_VILLAGE, self.params.village_count,
            valid_biomes=[BIOME_PLAINS, BIOME_FOREST],
            min_distance=8
        )

        # Set starting village
        for loc in game_map.locations:
            if loc.location_type == LOCATION_VILLAGE and loc.name == "Тихая":
                game_map.starting_village = loc
                break

        if not game_map.starting_village and game_map.locations:
            villages = [l for l in game_map.locations if l.location_type == LOCATION_VILLAGE]
            if villages:
                game_map.starting_village = villages[0]
                game_map.starting_village.name = "Тихая"

        # Place mines
        self._place_location_type(
            game_map, LOCATION_MINE, self.params.mine_count,
            valid_biomes=[BIOME_MOUNTAIN, BIOME_HILLS],
            min_distance=10
        )

        # Place bandit camps
        self._place_location_type(
            game_map, LOCATION_BANDIT_CAMP, self.params.bandit_camp_count,
            valid_biomes=[BIOME_FOREST],
            min_distance=15,
            min_distance_from_settlements=15
        )

        # Place ruins
        self._place_location_type(
            game_map, LOCATION_RUINS, self.params.ruins_count,
            valid_biomes=PASSABLE_BIOMES,
            min_distance=12,
            min_distance_from_settlements=15
        )

        # Place special locations
        self._place_location_type(
            game_map, LOCATION_MAGIC_SCHOOL, 1,
            valid_biomes=PASSABLE_BIOMES,
            min_distance=20
        )

        self._place_location_type(
            game_map, LOCATION_WARRIOR_ACADEMY, 1,
            valid_biomes=PASSABLE_BIOMES,
            min_distance=20
        )

        self._place_location_type(
            game_map, LOCATION_SECRET_CAMP, 1,
            valid_biomes=[BIOME_FOREST],
            min_distance=25
        )

    def _place_location_type(self, game_map: GeneratedMap, location_type: str,
                            count: int, valid_biomes: List[str],
                            min_distance: int = 8,
                            min_distance_from_settlements: int = 0) -> None:
        """Place locations of a specific type."""
        placed = 0
        attempts = 0
        max_attempts = count * 100

        while placed < count and attempts < max_attempts:
            attempts += 1

            x = random.randint(5, game_map.width - 6)
            y = random.randint(5, game_map.height - 6)

            if game_map.get_biome(x, y) not in valid_biomes:
                continue

            if game_map.get_location_at(x, y):
                continue

            # Check distance from other locations (unless disabled)
            if not self.params.ignore_min_distance:
                too_close = False
                for loc in game_map.locations:
                    d = distance(x, y, loc.x, loc.y)
                    if d < min_distance:
                        too_close = True
                        break
                    if min_distance_from_settlements > 0:
                        if loc.location_type in [LOCATION_CITY, LOCATION_VILLAGE]:
                            if d < min_distance_from_settlements:
                                too_close = True
                                break

                if too_close:
                    continue

            # Generate name
            name = self._get_location_name(location_type)
            attitude = get_default_player_attitude(location_type)

            # Set default values for mines
            if location_type == LOCATION_MINE:
                location = MapLocation(
                    x, y, location_type, name,
                    id=str(uuid.uuid4()),
                    rank=1,
                    spawn_radius=3,
                    miners_count=3,
                    respawn_time=100,
                    player_attitude=attitude
                )
            else:
                location = MapLocation(
                    x, y, location_type, name,
                    id=str(uuid.uuid4()),
                    player_attitude=attitude
                )
            game_map.add_location(location)
            placed += 1

    def _get_location_name(self, location_type: str) -> str:
        """Get a unique name for a location type."""
        # Handle spawn points - they have fixed names with numbers
        if location_type in self.SPAWN_NAMES:
            base_name = self.SPAWN_NAMES[location_type]
            used = self._used_names.get(location_type, set())
            i = 1
            while f"{base_name} {i}" in used:
                i += 1
            name = f"{base_name} {i}"
            self._used_names[location_type].add(name)
            return name

        name_lists = {
            LOCATION_CITY: self.CITY_NAMES,
            LOCATION_CAPITAL: self.CAPITAL_NAMES,
            LOCATION_VILLAGE: self.VILLAGE_NAMES,
            LOCATION_MINE: self.MINE_NAMES,
            LOCATION_BANDIT_CAMP: self.BANDIT_CAMP_NAMES,
            LOCATION_RUINS: self.RUINS_NAMES,
            LOCATION_MAGIC_SCHOOL: self.MAGIC_SCHOOL_NAMES,
            LOCATION_WARRIOR_ACADEMY: self.WARRIOR_ACADEMY_NAMES,
            LOCATION_SECRET_CAMP: self.SECRET_CAMP_NAMES
        }

        names = name_lists.get(location_type, ["Неизвестное место"])
        used = self._used_names.get(location_type, set())

        available = [n for n in names if n not in used]
        if not available:
            # Generate numbered name
            base = names[0] if names else "Место"
            i = 1
            while f"{base} {i}" in used:
                i += 1
            name = f"{base} {i}"
        else:
            name = random.choice(available)

        self._used_names[location_type].add(name)
        return name

    def regenerate_terrain_only(self, game_map: GeneratedMap,
                                params: GeneratorParams = None) -> GeneratedMap:
        """Regenerate only terrain, keeping locations."""
        if params:
            self.params = params

        if self.params.seed is None:
            self.params.seed = random.randint(0, 2**31)

        random.seed(self.params.seed)

        # Generate new terrain with different seeds for variation
        elevation = self._generate_noise(
            self.params.elevation_scale,
            self.params.elevation_octaves,
            seed_offset=0
        )
        moisture = self._generate_noise(
            self.params.moisture_scale,
            self.params.moisture_octaves,
            seed_offset=10000
        )

        elevation = normalize_map(elevation)
        moisture = normalize_map(moisture)

        biomes = self._generate_biomes(elevation, moisture)

        for _ in range(self.params.smooth_iterations):
            biomes = self._smooth_biomes(biomes)

        if self.params.generate_beaches:
            biomes = self._generate_beaches(biomes)

        if self.params.generate_rivers:
            biomes = self._generate_rivers(biomes, elevation)

        # Update map with new terrain
        game_map.biomes = biomes
        game_map.elevation = elevation
        game_map.moisture = moisture
        game_map.seed = self.params.seed

        return game_map
