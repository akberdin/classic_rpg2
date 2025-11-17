"""
Система инвентаря и предметов
"""
import random


class Item:
    """Базовый класс для предмета"""

    def __init__(self, name, item_type, value=0, description=""):
        """
        Инициализация предмета

        Args:
            name: Название предмета
            item_type: Тип предмета (resource, potion, equipment, etc.)
            value: Стоимость предмета в золоте
            description: Описание предмета
        """
        self.name = name
        self.item_type = item_type
        self.value = value
        self.description = description


class ResourceItem(Item):
    """Класс для ресурсов (руда, древесина, травы и т.д.)"""

    def __init__(self, name, value=10):
        super().__init__(name, "resource", value, f"Ресурс: {name}")


class PotionItem(Item):
    """Класс для зелий"""

    def __init__(self, name, effect_type, effect_value, value=50):
        """
        Инициализация зелья

        Args:
            name: Название зелья
            effect_type: Тип эффекта (health, mana, stamina)
            effect_value: Значение эффекта
            value: Стоимость зелья
        """
        super().__init__(name, "potion", value, f"Зелье: {name}")
        self.effect_type = effect_type
        self.effect_value = effect_value

    def use(self, character):
        """
        Использовать зелье на персонаже

        Args:
            character: Персонаж для применения эффекта

        Returns:
            str: Сообщение о результате
        """
        if self.effect_type == "health":
            old_health = character.health
            character.health = min(character.max_health, character.health + self.effect_value)
            restored = character.health - old_health
            return f"Восстановлено {restored} здоровья"
        elif self.effect_type == "mana":
            if hasattr(character, 'mana'):
                old_mana = character.mana
                character.mana = min(character.max_mana, character.mana + self.effect_value)
                restored = character.mana - old_mana
                return f"Восстановлено {restored} маны"
            return "Не применимо к этому персонажу"
        elif self.effect_type == "stamina":
            old_stamina = character.stamina
            character.stamina = min(character.max_stamina, character.stamina + self.effect_value)
            character.is_resting = False  # Снимаем состояние отдыха
            restored = character.stamina - old_stamina
            return f"Восстановлено {restored} выносливости"
        return "Эффект не применен"


class Inventory:
    """Класс инвентаря для хранения предметов"""

    def __init__(self, max_slots=20):
        """
        Инициализация инвентаря

        Args:
            max_slots: Максимальное количество слотов
        """
        self.items = {}  # {item_name: (item, quantity)}
        self.max_slots = max_slots
        self.gold = 0

    def add_item(self, item, quantity=1):
        """
        Добавить предмет в инвентарь

        Args:
            item: Объект предмета
            quantity: Количество

        Returns:
            bool: True если успешно добавлен
        """
        if len(self.items) >= self.max_slots and item.name not in self.items:
            return False  # Инвентарь полон

        if item.name in self.items:
            # Увеличиваем количество существующего предмета
            self.items[item.name] = (item, self.items[item.name][1] + quantity)
        else:
            # Добавляем новый предмет
            self.items[item.name] = (item, quantity)

        return True

    def remove_item(self, item_name, quantity=1):
        """
        Удалить предмет из инвентаря

        Args:
            item_name: Название предмета
            quantity: Количество для удаления

        Returns:
            bool: True если успешно удален
        """
        if item_name not in self.items:
            return False

        item, current_quantity = self.items[item_name]

        if current_quantity < quantity:
            return False

        if current_quantity == quantity:
            # Удаляем предмет полностью
            del self.items[item_name]
        else:
            # Уменьшаем количество
            self.items[item_name] = (item, current_quantity - quantity)

        return True

    def get_item(self, item_name):
        """
        Получить предмет по названию

        Args:
            item_name: Название предмета

        Returns:
            tuple: (item, quantity) или None
        """
        return self.items.get(item_name)

    def has_item(self, item_name, quantity=1):
        """
        Проверить наличие предмета

        Args:
            item_name: Название предмета
            quantity: Требуемое количество

        Returns:
            bool: True если предмет есть в нужном количестве
        """
        if item_name not in self.items:
            return False

        _, current_quantity = self.items[item_name]
        return current_quantity >= quantity

    def add_gold(self, amount):
        """Добавить золото"""
        self.gold += amount

    def remove_gold(self, amount):
        """
        Убрать золото

        Returns:
            bool: True если успешно
        """
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def get_items_by_type(self, item_type):
        """
        Получить все предметы определенного типа

        Args:
            item_type: Тип предмета

        Returns:
            list: Список (item, quantity)
        """
        return [(item, quantity) for item, quantity in self.items.values() if item.item_type == item_type]

    def get_all_items(self):
        """Получить все предметы"""
        return list(self.items.values())


# Предопределенные предметы
PREDEFINED_ITEMS = {
    # Ресурсы из шахт
    "copper_ore": ResourceItem("Медная руда", 10),
    "iron_ore": ResourceItem("Железная руда", 20),
    "silver_ore": ResourceItem("Серебряная руда", 50),
    "gold_ore": ResourceItem("Золотая руда", 100),
    "mithril_ore": ResourceItem("Мифриловая руда", 200),

    # Ресурсы из руин
    "ancient_coin": ResourceItem("Древняя монета", 30),
    "artifact_fragment": ResourceItem("Фрагмент артефакта", 80),
    "magic_crystal": ResourceItem("Магический кристалл", 150),
    "old_scroll": ResourceItem("Старый свиток", 40),

    # Зелья
    "minor_health_potion": PotionItem("Малое зелье здоровья", "health", 50, 30),
    "health_potion": PotionItem("Зелье здоровья", "health", 100, 60),
    "greater_health_potion": PotionItem("Большое зелье здоровья", "health", 200, 120),

    "minor_mana_potion": PotionItem("Малое зелье маны", "mana", 30, 25),
    "mana_potion": PotionItem("Зелье маны", "mana", 60, 50),

    "minor_stamina_potion": PotionItem("Малое зелье выносливости", "stamina", 50, 20),
    "stamina_potion": PotionItem("Зелье выносливости", "stamina", 100, 40),
}


def get_random_loot_from_location(location_type):
    """
    Получить случайный лут с локации

    Args:
        location_type: Тип локации

    Returns:
        list: Список (item, quantity)
    """
    loot = []

    if location_type == "mine":
        # Руда из шахт
        ores = ["copper_ore", "iron_ore", "silver_ore", "gold_ore", "mithril_ore"]
        weights = [0.5, 0.3, 0.12, 0.06, 0.02]  # Вероятности
        ore_type = random.choices(ores, weights=weights)[0]
        quantity = random.randint(1, 3)
        loot.append((PREDEFINED_ITEMS[ore_type], quantity))

    elif location_type == "ruins":
        # Артефакты из руин
        artifacts = ["ancient_coin", "artifact_fragment", "magic_crystal", "old_scroll"]
        weights = [0.5, 0.3, 0.1, 0.1]
        artifact_type = random.choices(artifacts, weights=weights)[0]
        quantity = random.randint(1, 2)
        loot.append((PREDEFINED_ITEMS[artifact_type], quantity))

        # Шанс найти зелье
        if random.random() < 0.3:  # 30% шанс
            potions = ["minor_health_potion", "health_potion", "minor_mana_potion"]
            potion_type = random.choice(potions)
            loot.append((PREDEFINED_ITEMS[potion_type], 1))

    return loot
