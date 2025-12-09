"""
Ремесленные умения.

Содержит:
- Mining - добыча руды
- Lumberjacking - рубка леса
"""
from game.systems.skills.base import Skill, SkillCategory


class Mining(Skill):
    """Рудокоп - добыча руды"""

    def __init__(self):
        super().__init__(
            name="Рудокоп",
            description="Позволяет добывать руду в шахтах. Доступные руды зависят от ранга",
            category=SkillCategory.CRAFTING,
            stamina_cost=10,
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
        super().__init__(
            name="Лесоруб",
            description="Позволяет рубить деревья. Эффективность растет с рангом",
            category=SkillCategory.CRAFTING,
            stamina_cost=10,
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
        super().__init__(
            name="Изготовление",
            description="Умение создавать предметы из материалов. Ранг определяет сложность доступных рецептов",
            category=SkillCategory.CRAFTING,
            stamina_cost=0,
            mana_cost=0,
            cooldown=0
        )

    def get_quality_bonus(self):
        """Получить бонус к качеству изделий"""
        return 0.05 * (self.rank - 1)  # 0%, 5%, 10%, 15%, 20% для рангов 1-5

    def get_craft_speed_bonus(self):
        """Получить бонус к скорости крафта"""
        return 0.1 * (self.rank - 1)  # 0%, 10%, 20%, 30%, 40% для рангов 1-5

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
        super().__init__(
            name="Алхимия",
            description="Умение создавать зелья и эликсиры. Ранг определяет сложность доступных рецептов зелий",
            category=SkillCategory.CRAFTING,
            stamina_cost=0,
            mana_cost=0,
            cooldown=0
        )

    def get_quality_bonus(self):
        """Получить бонус к качеству зелий"""
        return 0.05 * (self.rank - 1)  # 0%, 5%, 10%, 15%, 20% для рангов 1-5

    def get_quantity_bonus(self):
        """Получить бонус к количеству зелий"""
        return 0.1 * (self.rank - 1)  # 0%, 10%, 20%, 30%, 40% для рангов 1-5

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
        super().__init__(
            name="Зачарование",
            description="Умение накладывать магические эффекты на предметы. Ранг определяет сложность доступных зачарований",
            category=SkillCategory.CRAFTING,
            stamina_cost=0,
            mana_cost=0,
            cooldown=0
        )

    def get_power_bonus(self):
        """Получить бонус к силе зачарований"""
        return 0.08 * (self.rank - 1)  # 0%, 8%, 16%, 24%, 32% для рангов 1-5

    def get_success_chance_bonus(self):
        """Получить бонус к шансу успеха зачарования"""
        return 0.05 * (self.rank - 1)  # 0%, 5%, 10%, 15%, 20% для рангов 1-5

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
        super().__init__(
            name="Травник",
            description="Позволяет собирать травы на равнинах и в лесах. Эффективность растет с рангом",
            category=SkillCategory.CRAFTING,
            stamina_cost=10,
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

