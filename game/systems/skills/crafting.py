"""
Ремесленные умения.

Содержит:
- Mining - добыча руды
- Lumberjacking - рубка леса
"""
import random
from game.systems.skills.base import Skill, SkillCategory
from game.config.config_loader import get_skills_config
from game.item_registry import get_item
from game.inventory import WeaponType, EquipmentSlot


class Mining(Skill):
    """Рудокоп - добыча руды из объектов в шахтах"""

    # Маппинг типа руды на ID предмета в item_registry
    ORE_ITEM_MAPPING = {
        "copper": "copper_ore",
        "iron": "iron_ore",
        "silver": "silver_ore",
        "gold": "gold_ore",
        "mithril": "mithril_ore"
    }

    # Минимальный ранг умения для добычи каждого типа руды
    ORE_RANK_REQUIREMENTS = {
        "copper": 1,
        "iron": 2,
        "silver": 3,
        "gold": 4,
        "mithril": 5
    }

    # Названия руды для отображения
    ORE_NAMES = {
        "copper": "медная руда",
        "iron": "железная руда",
        "silver": "серебряная руда",
        "gold": "золотая руда",
        "mithril": "мифриловая руда"
    }

    # Драгоценные камни: шанс и веса качества
    GEM_TYPES = {
        "amethyst": {"base_chance": 5, "weights": [50, 35, 12, 3]},
        "ruby": {"base_chance": 4, "weights": [50, 35, 12, 3]},
        "sapphire": {"base_chance": 4, "weights": [50, 35, 12, 3]},
        "emerald": {"base_chance": 3, "weights": [45, 35, 15, 5]},
        "topaz": {"base_chance": 4.5, "weights": [50, 35, 12, 3]},
        "diamond": {"base_chance": 1, "weights": [60, 30, 8, 2]}
    }
    GEM_QUALITIES = ["shard", "raw", "cut", "perfect"]

    def __init__(self):
        # Загружаем параметры из конфига
        config = get_skills_config()
        name = config.get_crafting_skill('mining', 'name', default='Рудокоп')
        description = config.get_crafting_skill('mining', 'description',
            default='Позволяет добывать руду из объектов в шахтах. Выберите объект руды и используйте умение.')
        stamina_cost = config.get_crafting_skill('mining', 'stamina_cost', default=10)

        super().__init__(
            name=name,
            description=description,
            category=SkillCategory.CRAFTING,
            stamina_cost=stamina_cost,
            cooldown=0
        )

    def get_rank_progression_info(self):
        """Информация о прогрессии по рангам"""
        return [
            "Ранг 1: Добыча медной руды",
            "Ранг 2: Добыча железной руды",
            "Ранг 3: Добыча серебряной руды",
            "Ранг 4: Добыча золотой руды",
            "Ранг 5: Добыча мифриловой руды"
        ]

    def can_mine_ore_type(self, ore_type: str) -> bool:
        """
        Проверить, может ли игрок добывать руду данного типа

        Args:
            ore_type: Тип руды (copper, iron, silver, gold, mithril)

        Returns:
            bool: True если ранг достаточен для добычи
        """
        required_rank = self.ORE_RANK_REQUIREMENTS.get(ore_type, 99)
        return self.rank >= required_rank

    def use(self, user, target=None, dungeon_manager=None):
        """
        Использовать умение рудокопа для добычи руды из выбранного объекта

        Args:
            user: Игрок
            target: Не используется для новой механики
            dungeon_manager: Менеджер подземелий для доступа к выбранному объекту руды

        Returns:
            dict: Результат использования умения
        """
        result = {
            'success': False,
            'message': '',
            'resources': [],
            'skill_name': self.name
        }

        # Проверяем, что есть dungeon_manager
        if not dungeon_manager:
            result['message'] = "Добыча руды возможна только в шахтах!"
            return result

        # Проверяем, что игрок в подземелье
        if not dungeon_manager.is_in_dungeon:
            result['message'] = "Вы должны находиться в шахте!"
            return result

        # Проверяем, что есть выбранный объект руды
        if not dungeon_manager.selected_ore:
            result['message'] = "Выберите объект руды для добычи (ЛКМ)!"
            return result

        ore_tile = dungeon_manager.selected_ore
        ore_data = ore_tile.ore_data

        if not ore_data:
            result['message'] = "Выбранный объект не содержит руды!"
            dungeon_manager.deselect_ore()
            return result

        ore_type = ore_data.get('resource_type')
        if not ore_type:
            result['message'] = "Неизвестный тип руды!"
            dungeon_manager.deselect_ore()
            return result

        # Проверяем расстояние до объекта руды (должен быть в радиусе 1 клетки)
        distance = abs(user.x - ore_tile.x) + abs(user.y - ore_tile.y)
        if distance > 1:
            result['message'] = f"Вы слишком далеко от руды! Подойдите ближе."
            return result

        # Проверяем экипировку - нужна кирка
        weapon = user.inventory.get_equipped_item(EquipmentSlot.WEAPON)
        if not weapon or weapon.weapon_type != WeaponType.PICKAXE:
            result['message'] = "Для добычи руды нужна экипированная кирка!"
            return result

        # Проверяем ранг умения для данного типа руды
        if not self.can_mine_ore_type(ore_type):
            required_rank = self.ORE_RANK_REQUIREMENTS.get(ore_type, 99)
            ore_name = self.ORE_NAMES.get(ore_type, ore_type)
            result['message'] = f"Для добычи {ore_name} нужен ранг {required_rank} умения!"
            return result

        # Проверяем выносливость
        if user.stamina < self.stamina_cost:
            result['message'] = f"Недостаточно выносливости! Нужно: {self.stamina_cost}"
            return result

        # Списываем выносливость
        user.stamina -= self.stamina_cost

        # Добываем руду!
        resources = []
        messages = []

        # Основная руда - гарантированный дроп
        ore_item_id = self.ORE_ITEM_MAPPING.get(ore_type)
        if ore_item_id:
            ore_item = get_item(ore_item_id)
            if ore_item:
                # Количество зависит от ранга умения (1-3 на низких рангах, до 5 на высоких)
                quantity = random.randint(1, min(5, 1 + self.rank))
                resources.append((ore_item, quantity))
                user.inventory.add_item(ore_item, quantity)
                messages.append(f"Добыто: {ore_item.name} x{quantity}")

                if hasattr(user, 'resources_collected'):
                    user.resources_collected += quantity

        # Шанс найти драгоценный камень
        player_luck = getattr(user, 'luck', 1)
        if hasattr(user, 'get_effective_stat'):
            player_luck = user.get_effective_stat('luck')
        elif hasattr(user, 'inventory'):
            player_luck = user.inventory.get_total_stats_bonus().get('luck', 0) + getattr(user, 'luck', 1)

        for gem_name, gem_data in self.GEM_TYPES.items():
            gem_chance = gem_data["base_chance"] + (player_luck * 0.5)
            gem_chance = min(gem_chance, 25)

            if random.random() * 100 < gem_chance:
                weights = gem_data["weights"].copy()
                luck_bonus = min(player_luck * 0.5, 15)
                if luck_bonus > 0:
                    weights[0] = max(20, weights[0] - luck_bonus * 0.5)
                    weights[1] = max(15, weights[1] - luck_bonus * 0.3)
                    weights[2] += luck_bonus * 0.5
                    weights[3] += luck_bonus * 0.3

                quality_idx = random.choices(range(4), weights=weights)[0]
                quality = self.GEM_QUALITIES[quality_idx]
                gem_id = f"{quality}_{gem_name}"

                gem_item = get_item(gem_id)
                if gem_item:
                    resources.append((gem_item, 1))
                    user.inventory.add_item(gem_item, 1)
                    messages.append(f"Найден драгоценный камень: {gem_item.name}!")

        # Добавляем опыт умению
        exp_gain = 15 + len(resources) * 5
        self.add_experience(exp_gain)

        # Добавляем опыт персонажу
        if hasattr(user, 'add_experience'):
            user.add_experience(1)

        # Увеличиваем счётчик использований
        self.use_count += 1

        # Уменьшаем количество руды в объекте
        ore_depleted = dungeon_manager.deplete_ore(ore_tile)

        # Сообщаем только если руда полностью исчерпана
        if ore_depleted:
            messages.append("Жила руды исчерпана!")

        result['success'] = True
        result['resources'] = resources
        result['message'] = "\n".join(messages) if messages else "Добыча завершена!"

        return result


class Lumberjacking(Skill):
    """Лесоруб - рубка деревьев"""

    def __init__(self):
        # Загружаем параметры из конфига
        config = get_skills_config()
        name = config.get_crafting_skill('lumberjacking', 'name', default='Лесоруб')
        description = config.get_crafting_skill('lumberjacking', 'description', default='Позволяет рубить деревья. Эффективность растет с рангом')
        stamina_cost = config.get_crafting_skill('lumberjacking', 'stamina_cost', default=10)

        super().__init__(
            name=name,
            description=description,
            category=SkillCategory.CRAFTING,
            stamina_cost=stamina_cost,
            cooldown=0
        )

    def use(self, user, target=None):
        """Использовать умение лесоруба"""
        # Получаем профессию лесоруба
        if not hasattr(user, 'profession_manager'):
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"У {user.name} нет менеджера профессий"
            return result

        lumberjacking_profession = user.profession_manager.get_profession('lumberjacking')
        if not lumberjacking_profession:
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"Профессия Лесоруб не найдена"
            return result

        # Вызываем базовый метод для списания ресурсов
        result = super().use(user, target)

        # Используем профессию для сбора ресурсов
        resources = lumberjacking_profession.gather(user)

        if resources:
            result['success'] = True
            result['resources'] = resources
            messages = []
            for item, quantity in resources:
                user.inventory.add_item(item, quantity)
                messages.append(f"Срублено: {item.name} x{quantity}")
                if hasattr(user, 'resources_collected'):
                    user.resources_collected += 1
            result['message'] = "\n".join(messages) if messages else f"{user.name} срубил деревья!"
        else:
            result['success'] = False
            result['message'] = f"{user.name} не смог ничего добыть в этот раз"

        return result


class Craftsmanship(Skill):
    """Изготовление - открывает доступ к более сложным рецептам"""

    def __init__(self):
        # Загружаем параметры из конфига
        config = get_skills_config()
        name = config.get_crafting_skill('craftsmanship', 'name', default='Изготовление')
        description = config.get_crafting_skill('craftsmanship', 'description', default='Умение создавать предметы из материалов. Ранг определяет сложность доступных рецептов')
        stamina_cost = config.get_crafting_skill('craftsmanship', 'stamina_cost', default=0)
        mana_cost = config.get_crafting_skill('craftsmanship', 'mana_cost', default=0)

        super().__init__(
            name=name,
            description=description,
            category=SkillCategory.CRAFTING,
            stamina_cost=stamina_cost,
            mana_cost=mana_cost,
            cooldown=0
        )

    def get_quality_bonus(self):
        """Получить бонус к качеству изделий"""
        config = get_skills_config()
        quality_bonus_per_rank = config.get_crafting_skill('craftsmanship', 'quality_bonus_per_rank', default=0.05)
        return quality_bonus_per_rank * (self.rank - 1)

    def get_craft_speed_bonus(self):
        """Получить бонус к скорости крафта"""
        config = get_skills_config()
        craft_speed_bonus_per_rank = config.get_crafting_skill('craftsmanship', 'craft_speed_bonus_per_rank', default=0.1)
        return craft_speed_bonus_per_rank * (self.rank - 1)

    def get_rank_progression_info(self):
        """Информация о прогрессии по рангам"""
        return [
            "Ранг 1: Доступ к простым рецептам",
            "Ранг 2: Доступ к обычным рецептам",
            "Ранг 3: Доступ к качественным рецептам",
            "Ранг 4: Доступ к превосходным рецептам",
            "Ранг 5: Доступ к легендарным рецептам"
        ]

    def use(self, user, target=None):
        """Пассивное умение, используется автоматически при крафте"""
        result = super().use(user, target)
        result['success'] = False
        result['message'] = "Изготовление - пассивное умение, влияет на качество крафта"
        return result

    def is_assignable_to_quickbar(self):
        """Изготовление - пассивное умение, нельзя назначить на панель быстрого доступа"""
        return False


class Alchemy(Skill):
    """Алхимия - открывает доступ к более сложным зельям"""

    def __init__(self):
        # Загружаем параметры из конфига
        config = get_skills_config()
        name = config.get_crafting_skill('alchemy', 'name', default='Алхимия')
        description = config.get_crafting_skill('alchemy', 'description', default='Умение создавать зелья и эликсиры. Ранг определяет сложность доступных рецептов зелий')
        stamina_cost = config.get_crafting_skill('alchemy', 'stamina_cost', default=0)
        mana_cost = config.get_crafting_skill('alchemy', 'mana_cost', default=0)

        super().__init__(
            name=name,
            description=description,
            category=SkillCategory.CRAFTING,
            stamina_cost=stamina_cost,
            mana_cost=mana_cost,
            cooldown=0
        )

    def get_quality_bonus(self):
        """Получить бонус к качеству зелий"""
        config = get_skills_config()
        quality_bonus_per_rank = config.get_crafting_skill('alchemy', 'quality_bonus_per_rank', default=0.05)
        return quality_bonus_per_rank * (self.rank - 1)

    def get_quantity_bonus(self):
        """Получить бонус к количеству зелий"""
        config = get_skills_config()
        quantity_bonus_per_rank = config.get_crafting_skill('alchemy', 'quantity_bonus_per_rank', default=0.1)
        return quantity_bonus_per_rank * (self.rank - 1)

    def get_rank_progression_info(self):
        """Информация о прогрессии по рангам"""
        return [
            "Ранг 1: Доступ к простым зельям",
            "Ранг 2: Доступ к обычным зельям",
            "Ранг 3: Доступ к качественным зельям",
            "Ранг 4: Доступ к превосходным зельям",
            "Ранг 5: Доступ к легендарным зельям"
        ]

    def use(self, user, target=None):
        """Пассивное умение, используется автоматически при создании зелий"""
        result = super().use(user, target)
        result['success'] = False
        result['message'] = "Алхимия - пассивное умение, влияет на создание зелий"
        return result

    def is_assignable_to_quickbar(self):
        """Алхимия - пассивное умение, нельзя назначить на панель быстрого доступа"""
        return False


class Enchanting(Skill):
    """Зачарование - открывает доступ к более сложным зачарованиям"""

    def __init__(self):
        # Загружаем параметры из конфига
        config = get_skills_config()
        name = config.get_crafting_skill('enchanting', 'name', default='Зачарование')
        description = config.get_crafting_skill('enchanting', 'description', default='Умение накладывать магические эффекты на предметы. Ранг определяет сложность доступных зачарований')
        stamina_cost = config.get_crafting_skill('enchanting', 'stamina_cost', default=0)
        mana_cost = config.get_crafting_skill('enchanting', 'mana_cost', default=0)

        super().__init__(
            name=name,
            description=description,
            category=SkillCategory.CRAFTING,
            stamina_cost=stamina_cost,
            mana_cost=mana_cost,
            cooldown=0
        )

    def get_power_bonus(self):
        """Получить бонус к силе зачарований"""
        config = get_skills_config()
        power_bonus_per_rank = config.get_crafting_skill('enchanting', 'power_bonus_per_rank', default=0.08)
        return power_bonus_per_rank * (self.rank - 1)

    def get_success_chance_bonus(self):
        """Получить бонус к шансу успеха зачарования"""
        config = get_skills_config()
        success_chance_bonus_per_rank = config.get_crafting_skill('enchanting', 'success_chance_bonus_per_rank', default=0.05)
        return success_chance_bonus_per_rank * (self.rank - 1)

    def get_rank_progression_info(self):
        """Информация о прогрессии по рангам"""
        return [
            "Ранг 1: Доступ к простым зачарованиям",
            "Ранг 2: Доступ к обычным зачарованиям",
            "Ранг 3: Доступ к качественным зачарованиям",
            "Ранг 4: Доступ к превосходным зачарованиям",
            "Ранг 5: Доступ к легендарным зачарованиям"
        ]

    def use(self, user, target=None):
        """Пассивное умение, используется автоматически при зачаровании"""
        result = super().use(user, target)
        result['success'] = False
        result['message'] = "Зачарование - пассивное умение, влияет на магические эффекты предметов"
        return result

    def is_assignable_to_quickbar(self):
        """Зачарование - пассивное умение, нельзя назначить на панель быстрого доступа"""
        return False


class Herbalism(Skill):
    """Травник - сбор трав"""

    def __init__(self):
        # Загружаем параметры из конфига
        config = get_skills_config()
        name = config.get_crafting_skill('herbalism', 'name', default='Травник')
        description = config.get_crafting_skill('herbalism', 'description', default='Позволяет собирать травы на равнинах и в лесах. Эффективность растет с рангом')
        stamina_cost = config.get_crafting_skill('herbalism', 'stamina_cost', default=10)

        super().__init__(
            name=name,
            description=description,
            category=SkillCategory.CRAFTING,
            stamina_cost=stamina_cost,
            cooldown=0
        )

    def use(self, user, target=None):
        """Использовать умение травника"""
        # Получаем профессию травника
        if not hasattr(user, 'profession_manager'):
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"У {user.name} нет менеджера профессий"
            return result

        herbalism_profession = user.profession_manager.get_profession('herbalism')
        if not herbalism_profession:
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"Профессия Травник не найдена"
            return result

        # Вызываем базовый метод для списания ресурсов
        result = super().use(user, target)

        # Используем профессию для сбора ресурсов
        resources = herbalism_profession.gather(user)

        if resources:
            result['success'] = True
            result['resources'] = resources
            messages = []
            for item, quantity in resources:
                user.inventory.add_item(item, quantity)
                messages.append(f"Собрано: {item.name} x{quantity}")
                if hasattr(user, 'resources_collected'):
                    user.resources_collected += 1
            result['message'] = "\n".join(messages) if messages else f"{user.name} собрал травы!"
        else:
            result['success'] = False
            result['message'] = f"{user.name} не смог ничего собрать в этот раз"

        return result


# ==================== УМЕНИЯ ОРУЖИЯ ====================

