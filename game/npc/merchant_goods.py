"""
Модуль генерации товаров для торговцев.

Отвечает за:
- Генерацию ассортимента торговцев
- Расчёт качества и количества товаров
- Специализации торговцев
"""
import random
from game.item_registry import get_item


class MerchantGoodsGenerator:
    """Генератор товаров для торговцев"""

    @staticmethod
    def generate_goods(merchant):
        """
        Генерация товаров торговца с учетом ранга и специализаций

        Args:
            merchant: Торговец для которого генерируются товары
        """
        from game.inventory import ItemGenerator, EquipmentSlot

        # Очищаем старый ассортимент
        merchant.inventory.items.clear()

        rank = merchant.get_merchant_rank()

        # Увеличиваем инвентарь торговца
        merchant.inventory.max_slots = 40 + (rank * 10)
        merchant.inventory.max_weight = 200.0 + (rank * 50)

        # Золото торговца
        if merchant.wealth > 0:
            merchant.inventory.gold = merchant.wealth
        else:
            base_gold = 200 + merchant.level * 50
            merchant.inventory.gold = int(base_gold * (1 + rank * 0.5) * 3)

        # Генерируем товары по категориям
        if merchant.can_trade_category("potions"):
            MerchantGoodsGenerator._generate_potions(merchant, rank)

        if merchant.can_trade_category("weapons"):
            MerchantGoodsGenerator._generate_weapons(merchant, rank)

        if merchant.can_trade_category("armor"):
            MerchantGoodsGenerator._generate_armor(merchant, rank)

        if merchant.can_trade_category("jewelry"):
            MerchantGoodsGenerator._generate_jewelry(merchant, rank)

        if merchant.can_trade_category("resources"):
            MerchantGoodsGenerator._generate_resources(merchant, rank)

    @staticmethod
    def _generate_potions(merchant, rank):
        """Генерация зелий"""
        spec_quality = merchant.get_category_quality("potions")

        if rank == 1:
            merchant.inventory.add_item(get_item("minor_health_potion"), random.randint(2, 4) * spec_quality)
            merchant.inventory.add_item(get_item("minor_stamina_potion"), random.randint(1, 3) * spec_quality)
        elif rank == 2:
            merchant.inventory.add_item(get_item("minor_health_potion"), random.randint(2, 4))
            merchant.inventory.add_item(get_item("health_potion"), random.randint(2, 4))
            merchant.inventory.add_item(get_item("minor_mana_potion"), random.randint(2, 3))
            merchant.inventory.add_item(get_item("mana_potion"), random.randint(1, 2))
            merchant.inventory.add_item(get_item("minor_stamina_potion"), random.randint(2, 3))
            merchant.inventory.add_item(get_item("stamina_potion"), random.randint(1, 2))
        elif rank in [3, 4]:
            merchant.inventory.add_item(get_item("health_potion"), random.randint(2, 4))
            merchant.inventory.add_item(get_item("mana_potion"), random.randint(2, 3))
            merchant.inventory.add_item(get_item("stamina_potion"), random.randint(2, 3))

    @staticmethod
    def _generate_weapons(merchant, rank):
        """Генерация оружия"""
        from game.inventory import ItemGenerator, WeaponType

        spec_quality = merchant.get_category_quality("weapons")
        allowed_types = MerchantGoodsGenerator._get_allowed_weapon_types(rank)

        if rank == 1:
            num_weapons = random.randint(2, 4) * spec_quality
        else:
            num_weapons = min(random.randint(5, 10), 10)

        for _ in range(num_weapons):
            quality = ItemGenerator.generate_quality_for_shop(rank)
            weapon_type = random.choice(allowed_types)
            weapon = ItemGenerator.generate_weapon_by_type(weapon_type, quality=quality)
            merchant.inventory.add_item(weapon, 1)

    @staticmethod
    def _generate_armor(merchant, rank):
        """Генерация брони"""
        from game.inventory import ItemGenerator, EquipmentSlot

        spec_quality = merchant.get_category_quality("armor")
        allowed_types = MerchantGoodsGenerator._get_allowed_armor_types(rank)

        if rank == 1:
            num_armors = random.randint(3, 5) * spec_quality
        else:
            num_armors = min(random.randint(6, 10), 10)

        for _ in range(num_armors):
            quality = ItemGenerator.generate_quality_for_shop(rank)
            armor_type = random.choice(allowed_types)
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET])
            armor = ItemGenerator.generate_armor(merchant.level, slot=slot, armor_type=armor_type, quality=quality)
            merchant.inventory.add_item(armor, 1)

        # Пояса и рюкзаки
        for _ in range(random.randint(1, 2)):
            quality = ItemGenerator.generate_quality_for_shop(rank)
            belt = ItemGenerator.generate_belt(merchant.level, quality=quality)
            merchant.inventory.add_item(belt, 1)

        for _ in range(random.randint(1, 2)):
            quality = ItemGenerator.generate_quality_for_shop(rank)
            backpack = ItemGenerator.generate_backpack(merchant.level, quality=quality)
            merchant.inventory.add_item(backpack, 1)

    @staticmethod
    def _generate_jewelry(merchant, rank):
        """Генерация украшений"""
        from game.inventory import ItemGenerator

        spec_quality = merchant.get_category_quality("jewelry")

        if rank == 1:
            num_jewelry = random.randint(1, 3) * spec_quality
        elif rank in [2, 3, 4]:
            num_jewelry = random.randint(2, 5) * spec_quality

        for _ in range(min(num_jewelry, 10)):
            quality = ItemGenerator.generate_quality_for_shop(rank)
            jewelry = ItemGenerator.generate_jewelry(merchant.level, quality=quality)
            merchant.inventory.add_item(jewelry, 1)

    @staticmethod
    def _generate_resources(merchant, rank):
        """Генерация ресурсов"""
        spec_quality = merchant.get_category_quality("resources")
        resources = MerchantGoodsGenerator._get_resources_for_rank(rank)

        for resource_id, (min_qty, max_qty) in resources.items():
            item = get_item(resource_id)
            if item:
                quantity = random.randint(min_qty, max_qty) * spec_quality
                merchant.inventory.add_item(item, quantity)

    @staticmethod
    def _get_allowed_weapon_types(rank):
        """Получить разрешенные типы оружия для ранга"""
        from game.inventory import WeaponType

        if rank == 1:
            return [WeaponType.PICKAXE, WeaponType.AXE, WeaponType.BOW,
                    WeaponType.SPEAR, WeaponType.KNIFE, WeaponType.CLUB]
        else:
            return list(WeaponType)

    @staticmethod
    def _get_allowed_armor_types(rank):
        """Получить разрешенные типы брони для ранга"""
        from game.inventory import ArmorType

        if rank == 1:
            return [ArmorType.LIGHT, ArmorType.MEDIUM]
        else:
            return list(ArmorType)

    @staticmethod
    def _get_resources_for_rank(rank):
        """Получить список ресурсов для ранга"""
        if rank == 1:
            return {
                "wood": (3, 8),
                "charcoal": (3, 8),
                "copper_ore": (3, 8),
                "iron_ore": (3, 8),
                "wolf_fang": (1, 3),
                "wolf_hide": (1, 3),
                "bear_fang": (1, 3),
                "bear_hide": (1, 3),
                "bear_meat": (2, 4),
                "deer_hide": (1, 3),
                "deer_meat": (2, 4),
                "poor_fabric": (2, 5),
            }
        elif rank == 2:
            return {
                "copper_ore": (3, 8),
                "iron_ore": (3, 8),
                "silver_ore": (2, 5),
                "gold_ore": (1, 3),
                "charcoal": (3, 8),
                "fabric": (2, 5),
            }
        elif rank in [3, 4]:
            return {
                "copper_ingot": (2, 5),
                "iron_ingot": (2, 5),
                "silver_ingot": (1, 3),
                "gold_ingot": (1, 2),
                "fine_fabric": (1, 3),
            }
        return {}


class MagicGoodsGenerator:
    """Генератор товаров для магического торговца"""

    @staticmethod
    def generate_goods(merchant):
        """Генерация товаров магического торговца"""
        from game.inventory import ItemGenerator, WeaponType, ArmorType, EquipmentSlot, ItemQuality

        merchant.inventory.items.clear()
        merchant.inventory.gold = (random.randint(2000, 5000) + merchant.level * 200) * 3

        # Оружие: жезлы и посохи
        magic_weapon_types = [WeaponType.STAFF, WeaponType.WAND]
        for _ in range(random.randint(5, 10)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            weapon_type = random.choice(magic_weapon_types)
            weapon = ItemGenerator.generate_weapon_by_type(weapon_type, quality=quality)
            merchant.inventory.add_item(weapon, 1)

        # Легкая броня
        for _ in range(random.randint(4, 8)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET])
            armor = ItemGenerator.generate_armor(merchant.level, slot=slot, armor_type=ArmorType.LIGHT, quality=quality)
            merchant.inventory.add_item(armor, 1)

        # Пояса и рюкзаки
        for _ in range(random.randint(1, 2)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            merchant.inventory.add_item(ItemGenerator.generate_belt(merchant.level, quality=quality), 1)
            merchant.inventory.add_item(ItemGenerator.generate_backpack(merchant.level, quality=quality), 1)

        # Украшения
        for _ in range(random.randint(2, 5)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            jewelry = ItemGenerator.generate_jewelry(merchant.level + 2, quality=quality)
            merchant.inventory.add_item(jewelry, 1)

        # Ресурсы и зелья
        merchant.inventory.add_item(get_item("magic_crystal"), random.randint(3, 6))
        merchant.inventory.add_item(get_item("artifact_fragment"), random.randint(2, 4))
        merchant.inventory.add_item(get_item("ancient_coin"), random.randint(3, 6))
        merchant.inventory.add_item(get_item("greater_health_potion"), random.randint(3, 6))
        merchant.inventory.add_item(get_item("mana_potion"), random.randint(4, 8))
        merchant.inventory.add_item(get_item("stamina_potion"), random.randint(3, 6))


class WarriorGoodsGenerator:
    """Генератор товаров для военного торговца"""

    @staticmethod
    def generate_goods(merchant):
        """Генерация товаров военного торговца"""
        from game.inventory import ItemGenerator, WeaponType, ArmorType, EquipmentSlot, ItemQuality

        merchant.inventory.items.clear()
        merchant.inventory.gold = (random.randint(2000, 5000) + merchant.level * 200) * 3

        # Оружие
        warrior_weapon_types = [
            WeaponType.SWORD, WeaponType.AXE, WeaponType.SPEAR,
            WeaponType.BOW, WeaponType.CLUB, WeaponType.KNIFE
        ]
        for _ in range(random.randint(5, 10)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            weapon_type = random.choice(warrior_weapon_types)
            weapon = ItemGenerator.generate_weapon_by_type(weapon_type, quality=quality)
            merchant.inventory.add_item(weapon, 1)

        # Средняя и тяжелая броня
        warrior_armor_types = [ArmorType.MEDIUM, ArmorType.HEAVY]
        for _ in range(random.randint(4, 8)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            armor_type = random.choice(warrior_armor_types)
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET])
            armor = ItemGenerator.generate_armor(merchant.level, slot=slot, armor_type=armor_type, quality=quality)
            merchant.inventory.add_item(armor, 1)

        # Пояса и рюкзаки
        for _ in range(random.randint(1, 2)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            merchant.inventory.add_item(ItemGenerator.generate_belt(merchant.level, quality=quality), 1)
            merchant.inventory.add_item(ItemGenerator.generate_backpack(merchant.level, quality=quality), 1)

        # Украшения
        for _ in range(random.randint(2, 5)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            jewelry = ItemGenerator.generate_jewelry(merchant.level + 2, quality=quality)
            merchant.inventory.add_item(jewelry, 1)

        # Ресурсы и зелья
        merchant.inventory.add_item(get_item("iron_ingot"), random.randint(5, 10))
        merchant.inventory.add_item(get_item("silver_ingot"), random.randint(3, 6))
        merchant.inventory.add_item(get_item("gold_ingot"), random.randint(2, 4))
        merchant.inventory.add_item(get_item("greater_health_potion"), random.randint(3, 6))
        merchant.inventory.add_item(get_item("stamina_potion"), random.randint(4, 8))


class ShadowGoodsGenerator:
    """Генератор товаров для теневого торговца"""

    @staticmethod
    def generate_goods(merchant):
        """Генерация товаров теневого торговца"""
        from game.inventory import ItemGenerator, WeaponType, ArmorType, EquipmentSlot, ItemQuality

        merchant.inventory.items.clear()
        merchant.inventory.gold = (random.randint(1500, 4000) + merchant.level * 150) * 3

        # Оружие
        shadow_weapon_types = [WeaponType.KNIFE, WeaponType.SWORD, WeaponType.BOW]
        for _ in range(random.randint(5, 10)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            weapon_type = random.choice(shadow_weapon_types)
            weapon = ItemGenerator.generate_weapon_by_type(weapon_type, quality=quality)
            merchant.inventory.add_item(weapon, 1)

        # Легкая и средняя броня
        shadow_armor_types = [ArmorType.LIGHT, ArmorType.MEDIUM]
        for _ in range(random.randint(4, 8)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            armor_type = random.choice(shadow_armor_types)
            slot = random.choice([EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET])
            armor = ItemGenerator.generate_armor(merchant.level, slot=slot, armor_type=armor_type, quality=quality)
            merchant.inventory.add_item(armor, 1)

        # Пояса и рюкзаки
        for _ in range(random.randint(1, 2)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            merchant.inventory.add_item(ItemGenerator.generate_belt(merchant.level, quality=quality), 1)
            merchant.inventory.add_item(ItemGenerator.generate_backpack(merchant.level, quality=quality), 1)

        # Украшения
        for _ in range(random.randint(2, 5)):
            quality = random.choice([ItemQuality.UNCOMMON, ItemQuality.RARE])
            jewelry = ItemGenerator.generate_jewelry(merchant.level + 2, quality=quality)
            merchant.inventory.add_item(jewelry, 1)

        # Зелья
        merchant.inventory.add_item(get_item("health_potion"), random.randint(3, 6))
        merchant.inventory.add_item(get_item("greater_health_potion"), random.randint(2, 4))
        merchant.inventory.add_item(get_item("stamina_potion"), random.randint(3, 6))
