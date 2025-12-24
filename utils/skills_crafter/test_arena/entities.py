"""
Минимальные классы сущностей для тестовой арены
Изолированы от основного кода игры
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class EntityType(Enum):
    """Тип сущности"""
    PLAYER = "player"
    NPC_ENEMY = "enemy"
    NPC_ALLY = "ally"
    NPC_NEUTRAL = "neutral"


@dataclass
class TestSkillSlot:
    """Слот для умения"""
    skill_id: str
    skill_data: Dict[str, Any]
    current_cooldown: int = 0


@dataclass
class StatusEffect:
    """Базовый статус-эффект"""
    effect_type: str
    name: str
    duration: int
    remaining_duration: int
    value: float  # урон/лечение/бонус за ход
    icon_id: str = ""

    def tick(self, character: "TestCharacter") -> Optional[str]:
        """Применить эффект за ход"""
        self.remaining_duration -= 1

        if self.effect_type == "burn":
            damage = int(self.value)
            character.health -= damage
            return f"{character.name} получает {damage} урона от огня"
        elif self.effect_type == "poison":
            damage = int(self.value)
            character.health -= damage
            return f"{character.name} получает {damage} урона от яда"
        elif self.effect_type == "bleed":
            damage = int(self.value)
            character.health -= damage
            return f"{character.name} получает {damage} урона от кровотечения"
        elif self.effect_type == "regeneration":
            healing = int(self.value)
            character.health = min(character.max_health, character.health + healing)
            return f"{character.name} восстанавливает {healing} здоровья"

        return None

    def is_expired(self) -> bool:
        return self.remaining_duration <= 0

    def remove(self, character: "TestCharacter") -> Optional[str]:
        """Вызывается при снятии эффекта"""
        return f"Эффект '{self.name}' закончился на {character.name}"


class TestCharacter:
    """
    Базовый класс персонажа для тестовой арены.
    Минимальная реализация без зависимостей от основного кода.
    """

    def __init__(
        self,
        name: str,
        level: int = 1,
        entity_type: EntityType = EntityType.NPC_NEUTRAL
    ):
        self.name = name
        self.level = level
        self.entity_type = entity_type

        # Базовые атрибуты
        self.strength = 10 + level * 2
        self.dexterity = 10 + level * 2
        self.constitution = 10 + level * 2
        self.intelligence = 10 + level * 2
        self.spirit = 10 + level * 2
        self.luck = 5 + level

        # Ресурсы
        self.max_health = 100 + self.constitution * 5 + level * 10
        self.health = self.max_health
        self.max_mana = 50 + self.intelligence * 3 + level * 5
        self.mana = self.max_mana
        self.max_stamina = 100 + self.constitution * 2 + level * 5
        self.stamina = self.max_stamina

        # Умения
        self.skill_slots: List[TestSkillSlot] = []
        self.status_effects: List[StatusEffect] = []

        # Состояние
        self.is_alive = True

        # Для рендеринга
        self.x = 0
        self.y = 0
        self.sprite_id: Optional[str] = None

    def get_effective_max_health(self) -> int:
        return self.max_health

    def get_effective_max_mana(self) -> int:
        return self.max_mana

    def get_effective_max_stamina(self) -> int:
        return self.max_stamina

    def get_total_damage(self) -> int:
        """Базовый урон"""
        return 5 + self.strength // 2 + self.level

    def get_total_defense(self) -> int:
        """Базовая защита"""
        return self.constitution // 3 + self.level // 2

    def get_magic_defense(self) -> int:
        """Магическая защита"""
        return self.spirit // 3 + self.intelligence // 4

    def take_damage(self, damage: int) -> int:
        """Получить урон"""
        actual_damage = max(1, damage - self.get_total_defense())
        self.health -= actual_damage
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
        return actual_damage

    def heal(self, amount: int) -> int:
        """Восстановить здоровье"""
        old_health = self.health
        self.health = min(self.max_health, self.health + amount)
        return self.health - old_health

    def spend_mana(self, amount: int) -> bool:
        """Потратить ману"""
        if self.mana >= amount:
            self.mana -= amount
            return True
        return False

    def spend_stamina(self, amount: int) -> bool:
        """Потратить выносливость"""
        if self.stamina >= amount:
            self.stamina -= amount
            return True
        return False

    def add_status_effect(self, effect: StatusEffect):
        """Добавить статус-эффект"""
        # Проверяем, есть ли уже такой эффект
        for existing in self.status_effects:
            if existing.effect_type == effect.effect_type:
                # Обновляем длительность
                existing.remaining_duration = max(
                    existing.remaining_duration,
                    effect.remaining_duration
                )
                return
        self.status_effects.append(effect)

    def tick_status_effects(self) -> List[str]:
        """Обработать статус-эффекты за ход"""
        messages = []
        for effect in self.status_effects[:]:
            msg = effect.tick(self)
            if msg:
                messages.append(msg)

            if effect.is_expired():
                remove_msg = effect.remove(self)
                if remove_msg:
                    messages.append(remove_msg)
                self.status_effects.remove(effect)

        # Проверяем смерть от DoT
        if self.health <= 0:
            self.is_alive = False

        return messages

    def reset(self):
        """Сбросить состояние персонажа"""
        self.health = self.max_health
        self.mana = self.max_mana
        self.stamina = self.max_stamina
        self.is_alive = True
        self.status_effects.clear()
        for slot in self.skill_slots:
            slot.current_cooldown = 0


class TestPlayer(TestCharacter):
    """Класс игрока для тестовой арены"""

    def __init__(self, name: str = "Тестовый Герой", level: int = 10):
        super().__init__(name, level, EntityType.PLAYER)
        self.sprite_id = "player"

        # Улучшенные характеристики игрока
        self.strength = 15 + level * 3
        self.dexterity = 15 + level * 3
        self.intelligence = 15 + level * 3

        # Пересчитываем ресурсы
        self.max_health = 150 + self.constitution * 5 + level * 15
        self.health = self.max_health
        self.max_mana = 80 + self.intelligence * 4 + level * 8
        self.mana = self.max_mana


class TestNPC(TestCharacter):
    """Класс NPC для тестовой арены"""

    # Пресеты NPC
    NPC_PRESETS = {
        "bandit": {
            "name": "Бандит",
            "sprite_id": "bandit",
            "strength_mult": 1.2,
            "dexterity_mult": 1.0,
            "constitution_mult": 1.0,
        },
        "guard": {
            "name": "Стражник",
            "sprite_id": "guard",
            "strength_mult": 1.0,
            "dexterity_mult": 0.8,
            "constitution_mult": 1.3,
        },
        "mage": {
            "name": "Маг",
            "sprite_id": "mage",
            "strength_mult": 0.6,
            "dexterity_mult": 0.8,
            "constitution_mult": 0.8,
            "intelligence_mult": 1.5,
        },
        "wolf": {
            "name": "Волк",
            "sprite_id": "wolf",
            "strength_mult": 1.1,
            "dexterity_mult": 1.3,
            "constitution_mult": 0.9,
        },
        "undead": {
            "name": "Нежить",
            "sprite_id": "undead",
            "strength_mult": 1.0,
            "dexterity_mult": 0.7,
            "constitution_mult": 1.2,
        },
        "dummy": {
            "name": "Манекен",
            "sprite_id": "dummy",
            "strength_mult": 0.0,
            "dexterity_mult": 0.0,
            "constitution_mult": 3.0,  # Много здоровья для тестов
        },
    }

    def __init__(
        self,
        npc_type: str = "bandit",
        level: int = 5,
        entity_type: EntityType = EntityType.NPC_ENEMY,
        custom_name: Optional[str] = None
    ):
        preset = self.NPC_PRESETS.get(npc_type, self.NPC_PRESETS["bandit"])
        name = custom_name or f"{preset['name']} (ур. {level})"

        super().__init__(name, level, entity_type)

        self.npc_type = npc_type
        self.sprite_id = preset.get("sprite_id", npc_type)

        # Применяем множители характеристик
        self.strength = int(self.strength * preset.get("strength_mult", 1.0))
        self.dexterity = int(self.dexterity * preset.get("dexterity_mult", 1.0))
        self.constitution = int(self.constitution * preset.get("constitution_mult", 1.0))
        self.intelligence = int(self.intelligence * preset.get("intelligence_mult", 1.0))

        # Пересчитываем ресурсы
        self.max_health = 80 + self.constitution * 4 + level * 8
        self.health = self.max_health
        self.max_mana = 30 + self.intelligence * 2 + level * 3
        self.mana = self.max_mana
        self.max_stamina = 80 + self.constitution * 2 + level * 4
        self.stamina = self.max_stamina


@dataclass
class NPCGroup:
    """Группа NPC"""
    npcs: List[TestNPC] = field(default_factory=list)
    group_name: str = "Группа"
    formation: str = "line"  # line, circle, square

    @classmethod
    def create_enemy_group(
        cls,
        npc_type: str,
        count: int,
        base_level: int = 5,
        group_name: Optional[str] = None
    ) -> "NPCGroup":
        """Создать группу враждебных NPC"""
        npcs = []
        for i in range(count):
            level = base_level + i  # Небольшой разброс уровней
            npc = TestNPC(npc_type, level, EntityType.NPC_ENEMY)
            npcs.append(npc)

        return cls(
            npcs=npcs,
            group_name=group_name or f"Группа {npc_type}",
        )

    @classmethod
    def create_mixed_group(
        cls,
        npc_configs: List[Dict[str, Any]],
        group_name: str = "Смешанная группа"
    ) -> "NPCGroup":
        """
        Создать смешанную группу NPC

        Args:
            npc_configs: Список конфигов [{type, level, entity_type}]
        """
        npcs = []
        for config in npc_configs:
            npc = TestNPC(
                npc_type=config.get("type", "bandit"),
                level=config.get("level", 5),
                entity_type=EntityType(config.get("entity_type", "enemy"))
            )
            npcs.append(npc)

        return cls(npcs=npcs, group_name=group_name)
