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
            description="Позволяет добывать руду в шахтах. Эффективность растет с рангом",
            category=SkillCategory.CRAFTING,
            stamina_cost=10,
            cooldown=0
        )

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

        # Используем профессию для сбора ресурсов
        resources = mining_profession.gather(user)

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
    """Изготовление - улучшает качество создаваемых предметов"""

    def __init__(self):
        super().__init__(
            name="Изготовление",
            description="Умение создавать предметы из материалов. Качество зависит от ранга",
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
            "Ранг 1: Базовое качество изготовления",
            "Ранг 2: +5% к качеству изделий",
            "Ранг 3: +10% к качеству изделий",
            "Ранг 4: +15% к качеству изделий",
            "Ранг 5: +20% к качеству изделий"
        ]

    def use(self, user, target=None):
        """Пассивное умение, используется автоматически при крафте"""
        result = super().use(user, target)
        result['success'] = False
        result['message'] = "Изготовление - пассивное умение, влияет на качество крафта"
        return result


class Alchemy(Skill):
    """Алхимия - улучшает создание зелий и эликсиров"""

    def __init__(self):
        super().__init__(
            name="Алхимия",
            description="Умение создавать зелья и эликсиры. Качество и количество зависят от ранга",
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
            "Ранг 1: Базовое качество зелий",
            "Ранг 2: +5% к качеству, +10% к количеству",
            "Ранг 3: +10% к качеству, +20% к количеству",
            "Ранг 4: +15% к качеству, +30% к количеству",
            "Ранг 5: +20% к качеству, +40% к количеству"
        ]

    def use(self, user, target=None):
        """Пассивное умение, используется автоматически при создании зелий"""
        result = super().use(user, target)
        result['success'] = False
        result['message'] = "Алхимия - пассивное умение, влияет на создание зелий"
        return result


class Enchanting(Skill):
    """Зачарование - улучшает наложение магических эффектов на предметы"""

    def __init__(self):
        super().__init__(
            name="Зачарование",
            description="Умение накладывать магические эффекты на предметы. Сила эффектов зависит от ранга",
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
            "Ранг 1: Базовая сила зачарований",
            "Ранг 2: +8% к силе, +5% к шансу успеха",
            "Ранг 3: +16% к силе, +10% к шансу успеха",
            "Ранг 4: +24% к силе, +15% к шансу успеха",
            "Ранг 5: +32% к силе, +20% к шансу успеха"
        ]

    def use(self, user, target=None):
        """Пассивное умение, используется автоматически при зачаровании"""
        result = super().use(user, target)
        result['success'] = False
        result['message'] = "Зачарование - пассивное умение, влияет на магические эффекты предметов"
        return result


class Herbalism(Skill):
    """Травник - улучшает сбор и обработку трав"""

    def __init__(self):
        super().__init__(
            name="Травник",
            description="Умение собирать и обрабатывать травы. Количество и качество трав зависят от ранга",
            category=SkillCategory.CRAFTING,
            stamina_cost=0,
            mana_cost=0,
            cooldown=0
        )

    def get_gathering_bonus(self):
        """Получить бонус к количеству собранных трав"""
        return 0.15 * (self.rank - 1)  # 0%, 15%, 30%, 45%, 60% для рангов 1-5

    def get_rare_chance_bonus(self):
        """Получить бонус к шансу найти редкие травы"""
        return 0.05 * (self.rank - 1)  # 0%, 5%, 10%, 15%, 20% для рангов 1-5

    def get_rank_progression_info(self):
        """Информация о прогрессии по рангам"""
        return [
            "Ранг 1: Базовый сбор трав",
            "Ранг 2: +15% к количеству, +5% к редким травам",
            "Ранг 3: +30% к количеству, +10% к редким травам",
            "Ранг 4: +45% к количеству, +15% к редким травам",
            "Ранг 5: +60% к количеству, +20% к редким травам"
        ]

    def use(self, user, target=None):
        """Пассивное умение, используется автоматически при сборе трав"""
        result = super().use(user, target)
        result['success'] = False
        result['message'] = "Травник - пассивное умение, влияет на сбор трав"
        return result


# ==================== УМЕНИЯ ОРУЖИЯ ====================

