"""
Модуль инициализации игрока.

Отвечает за:
- Выдачу стартовых предметов
- Начальную настройку инвентаря
- Стартовую экипировку
"""
from game.inventory import ItemGenerator, ItemQuality, ArmorType, EquipmentSlot, WeaponType, WeaponItem
from game.item_registry import get_item


def give_starting_items(player):
    """
    Дать игроку стартовые предметы

    Args:
        player: Игрок
    """
    # Начальное золото
    player.inventory.add_gold(50)

    # Стартовые зелья
    player.inventory.add_item(get_item("minor_health_potion"), 2)
    player.inventory.add_item(get_item("minor_stamina_potion"), 1)

    # Стартовое оружие - топор плохого качества
    starter_weapon = _create_starter_weapon()
    player.inventory.add_item(starter_weapon, 1)
    player.inventory.equip_item(starter_weapon)

    # Легкая плохая нагрудная броня
    starter_chest = ItemGenerator.generate_armor(
        level=1,
        slot=EquipmentSlot.CHEST,
        armor_type=ArmorType.LIGHT,
        quality=ItemQuality.POOR
    )
    player.inventory.add_item(starter_chest, 1)
    player.inventory.equip_item(starter_chest)

    # Легкая плохая обувь
    starter_feet = ItemGenerator.generate_armor(
        level=1,
        slot=EquipmentSlot.FEET,
        armor_type=ArmorType.LIGHT,
        quality=ItemQuality.POOR
    )
    player.inventory.add_item(starter_feet, 1)
    player.inventory.equip_item(starter_feet)

    # Обновляем производные характеристики после экипировки
    player.update_derived_stats()


def _create_starter_weapon():
    """
    Создать стартовое оружие (топор плохого качества)

    Returns:
        WeaponItem: Стартовое оружие
    """
    # Генерируем бонусы из конфига
    stats_bonus, param_bonus, skill_bonus, base_damage = ItemGenerator.generate_bonuses_from_config(
        "weapon", ItemQuality.POOR, WeaponType.AXE
    )

    # Генерируем название
    weapon_name = ItemGenerator.generate_item_name(
        WeaponType.AXE.rus_name, WeaponType.AXE.rus_name, ItemQuality.POOR
    )

    # Рассчитываем стоимость
    weapon_value = ItemGenerator.calculate_item_value(
        "weapon", ItemQuality.POOR, base_damage, stats_bonus, param_bonus, skill_bonus
    )

    # Создаем топор
    return WeaponItem(
        weapon_name, WeaponType.AXE, base_damage, weapon_value,
        ItemQuality.POOR, stats_bonus, param_bonus, skill_bonus
    )
