"""
Ремесленные умения.

Содержит:
- Mining - добыча руды
- Lumberjacking - рубка леса
"""
from game.systems.skills.base import Skill, SkillCategory
from game.config.config_loader import get_skills_config


class Mining(Skill):
    """Рудокоп - добыча руды"""

    def __init__(self):
        # Загружаем параметры из конфига
        config = get_skills_config()
        name = config.get_crafting_skill('mining', 'name', default='Рудокоп')
        description = config.get_crafting_skill('mining', 'description', default='Позволяет добывать руду в шахтах. Доступные руды зависят от ранга')
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
            "Ранг 1: Добыча меди",
            "Ранг 2: Добыча меди и железа",
            "Ранг 3: Добыча меди, железа и серебра",
            "Ранг 4: Добыча меди, железа, серебра и золота",
            "Ранг 5: Добыча меди, железа, серебра, золота и мифрила"
        ]

    def use(self, user, target=None):
        """Использовать умение рудокопа"""
        # Получаем профессию рудокопа
        if not hasattr(user, 'profession_manager'):
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"У {user.name} нет менеджера профессий"
            return result

        mining_profession = user.profession_manager.get_profession('mining')
        if not mining_profession:
            result = super().use(user, target)
            result['success'] = False
            result['message'] = f"Профессия Рудокоп не найдена"
            return result

        # Проверяем, можно ли использовать профессию
        # Получаем текущую локацию
        location = None
        if hasattr(user, 'x') and hasattr(user, 'y'):
            # Пытаемся получить локацию из текущей позиции игрока
            # Это требует доступа к карте, который мы получим из контекста
            pass

        # Вызываем базовый метод для списания ресурсов
        result = super().use(user, target)

        # Используем профессию для сбора ресурсов, передаем ранг УМЕНИЯ
        resources = mining_profession.gather(user, skill_rank=self.rank)

        if resources:
            result['success'] = True
            result['resources'] = resources
            messages = []
            for item, quantity in resources:
                if user.inventory.add_item(item, quantity):
                    messages.append(f"Добыто: {item.name} x{quantity}")
                    if hasattr(user, 'resources_collected'):
                        user.resources_collected += 1
                else:
                    messages.append(f"Инвентарь полон! Не удалось добавить {item.name}")
            result['message'] = "\n".join(messages) if messages else f"{user.name} добыл ресурсы!"
        else:
            result['success'] = False
            result['message'] = f"{user.name} не смог ничего добыть в этот раз"

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
                if user.inventory.add_item(item, quantity):
                    messages.append(f"Срублено: {item.name} x{quantity}")
                    if hasattr(user, 'resources_collected'):
                        user.resources_collected += 1
                else:
                    messages.append(f"Инвентарь полон! Не удалось добавить {item.name}")
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
                if user.inventory.add_item(item, quantity):
                    messages.append(f"Собрано: {item.name} x{quantity}")
                    if hasattr(user, 'resources_collected'):
                        user.resources_collected += 1
                else:
                    messages.append(f"Инвентарь полон! Не удалось добавить {item.name}")
            result['message'] = "\n".join(messages) if messages else f"{user.name} собрал травы!"
        else:
            result['success'] = False
            result['message'] = f"{user.name} не смог ничего собрать в этот раз"

        return result


# ==================== УМЕНИЯ ОРУЖИЯ ====================

