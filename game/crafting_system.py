"""
Система крафта предметов.

Модуль обрабатывает создание предметов из ресурсов.
"""
import json
import os
from typing import Dict, List, Optional, Tuple

# Маппинг ID предметов на их имена из PREDEFINED_ITEMS
ITEM_ID_TO_NAME = {
    # Руды
    "copper_ore": "Медная руда",
    "iron_ore": "Железная руда",
    "silver_ore": "Серебряная руда",
    "gold_ore": "Золотая руда",
    "mithril_ore": "Мифриловая руда",
    # Слитки
    "copper_ingot": "Медный слиток",
    "iron_ingot": "Железный слиток",
    "silver_ingot": "Серебряный слиток",
    "gold_ingot": "Золотой слиток",
    "mithril_ingot": "Мифриловый слиток",
    "steel_ingot": "Стальной слиток",
    # Древесина и деревянные компоненты
    "wood": "Древесина",
    "long_wooden_handle": "Длинная деревянная рукоять",
    "short_wooden_handle": "Короткая деревянная рукоять",
    "wooden_shaft": "Древко",
    # Уголь
    "charcoal": "Древесный уголь",
    # Проволока
    "copper_wire": "Медная проволока",
    "iron_wire": "Железная проволока",
    "steel_wire": "Стальная проволока",
    "silver_wire": "Серебряная проволока",
    "gold_wire": "Золотая проволока",
    "mithril_wire": "Мифриловая проволока",
    # Компоненты оружия - лезвия топоров
    "copper_axe_blade": "Медное лезвие топора",
    "iron_axe_blade": "Железное лезвие топора",
    "steel_axe_blade": "Стальное лезвие топора",
    # Бойки для кирок
    "copper_hammer_head": "Медный боёк",
    "iron_hammer_head": "Железный боёк",
    "steel_hammer_head": "Стальной боёк",
    # Металлические полоски
    "copper_strips": "Медные полоски",
    "iron_strips": "Железные полоски",
    "steel_strips": "Стальные полоски",
    "silver_strips": "Серебряные полоски",
    # Короткие лезвия для ножей
    "copper_short_blade": "Медное короткое лезвие",
    "iron_short_blade": "Железное короткое лезвие",
    "steel_short_blade": "Стальное короткое лезвие",
    # Длинные лезвия для мечей
    "copper_long_blade": "Медное длинное лезвие",
    "iron_long_blade": "Железное длинное лезвие",
    "steel_long_blade": "Стальное длинное лезвие",
    # Наконечники копий
    "copper_spearhead": "Медный наконечник",
    "iron_spearhead": "Железный наконечник",
    "steel_spearhead": "Стальной наконечник",
    # Материалы от животных
    "leather": "Кожа",
    "leather_strips": "Полоски кожи",
    "deer_hide": "Шкура оленя",
    "wolf_hide": "Шкура волка",
    "bear_hide": "Шкура медведя",
    "animal_sinew": "Звериные жилы",
    "deer_antlers": "Рога оленя",
    # Ткань
    "poor_fabric": "Плохая ткань",
    "fabric": "Ткань",
    "fine_fabric": "Отличная ткань",
    # Травы для алхимии
    "chamomile": "Ромашка",
    "mint": "Мята",
    "sage": "Шалфей",
    "ginseng": "Женьшень",
    "mandrake": "Мандрагора",
    # Дополнительные компоненты
    "bowstring": "Тетива",
    "short_horn_handle": "Короткая роговая рукоять",
    # Готовые изделия - оружие
    "poor_axe": "Топор",
    "poor_spear": "Копье",
    "poor_pickaxe": "Кирка",
    "pickaxe": "Кирка",
    "fine_pickaxe": "Кирка",
    "poor_knife": "Нож",
    "knife": "Нож",
    "fine_knife": "Нож",
    "rare_knife": "Нож",
    "poor_sword": "Меч",
    "sword": "Меч",
    "fine_sword": "Меч",
    "rare_sword": "Меч",
    # Готовые изделия - броня
    "poor_light_gloves": "Легкие перчатки",
    "light_gloves": "Легкие перчатки",
    "fine_light_gloves": "Легкие перчатки",
    "poor_light_boots": "Легкая обувь",
    "light_boots": "Легкая обувь",
    "fine_light_boots": "Легкая обувь",
    "poor_backpack": "Рюкзак",
    "backpack": "Рюкзак",
    "fine_backpack": "Рюкзак",
    "rare_backpack": "Рюкзак",
    "poor_light_helmet": "Легкий шлем",
    "light_helmet": "Легкий шлем",
    "fine_light_helmet": "Легкий шлем",
    "poor_belt": "Ремень",
    "belt": "Ремень",
    "fine_belt": "Ремень",
    "rare_belt": "Ремень",
}


class CraftingRecipe:
    """Рецепт крафта"""

    def __init__(self, recipe_data: dict):
        """
        Инициализация рецепта.

        Args:
            recipe_data: Данные рецепта из конфига
        """
        self.id = recipe_data['id']
        self.name = recipe_data['name']
        self.station = recipe_data['station']
        self.result_item = recipe_data['result_item']
        self.result_quantity = recipe_data['result_quantity']
        self.required_level = recipe_data['required_level']
        self.ingredients = recipe_data['ingredients']
        self.category = recipe_data['category']
        self.required_skill = recipe_data.get('required_skill', None)
        self.required_skill_rank = recipe_data.get('required_skill_rank', 1)

    def can_craft(self, player, inventory) -> Tuple[bool, Optional[str]]:
        """
        Проверить, может ли игрок создать предмет.

        Args:
            player: Объект игрока
            inventory: Инвентарь игрока

        Returns:
            Tuple[bool, Optional[str]]: (может ли создать, причина отказа)
        """
        # Проверка известности рецепта
        if hasattr(player, 'known_recipes'):
            if self.id not in player.known_recipes:
                return False, "Рецепт не изучен"

        # Проверка наличия требуемого умения и его ранга
        if hasattr(self, 'required_skill') and self.required_skill:
            if hasattr(player, 'skill_manager'):
                skill = player.skill_manager.get_skill(self.required_skill)
                if not skill:
                    skill_names = {
                        'craftsmanship': 'Изготовление',
                        'alchemy': 'Алхимия',
                        'enchanting': 'Зачарование',
                        'herbalism': 'Травник'
                    }
                    skill_name = skill_names.get(self.required_skill, self.required_skill)
                    return False, f"Требуется умение: {skill_name}"

                required_rank = getattr(self, 'required_skill_rank', 1)
                if skill.rank < required_rank:
                    return False, f"Требуется ранг умения: {required_rank} (текущий: {skill.rank})"

        # Проверка наличия ресурсов
        for ingredient in self.ingredients:
            item_id = ingredient['item']
            required_quantity = ingredient['quantity']

            # Преобразуем ID предмета в его имя из инвентаря
            item_name = ITEM_ID_TO_NAME.get(item_id, item_id)

            # Получаем количество ресурса в инвентаре
            has_quantity = inventory.get_resource_count(item_name)

            if has_quantity < required_quantity:
                return False, f"Недостаточно ресурсов: {item_name} (нужно {required_quantity}, есть {has_quantity})"

        return True, None

    def get_ingredients_text(self) -> List[str]:
        """
        Получить список ингредиентов в текстовом виде.

        Returns:
            List[str]: Список строк с ингредиентами
        """
        result = []
        for ingredient in self.ingredients:
            item_name = ingredient['item']
            quantity = ingredient['quantity']
            result.append(f"{item_name} x{quantity}")
        return result


class CraftingStation:
    """Станция крафта (верстак, кузница и т.д.)"""

    def __init__(self, station_id: str, station_data: dict):
        """
        Инициализация станции крафта.

        Args:
            station_id: ID станции
            station_data: Данные станции из конфига
        """
        self.id = station_id
        self.name = station_data['name']
        self.description = station_data['description']
        self.recipes = []

    def add_recipe(self, recipe: CraftingRecipe):
        """Добавить рецепт к станции."""
        self.recipes.append(recipe)

    def get_available_recipes(self, player) -> List[CraftingRecipe]:
        """
        Получить доступные рецепты для игрока.

        Args:
            player: Объект игрока

        Returns:
            List[CraftingRecipe]: Список доступных рецептов (изученных игроком)
        """
        available = []
        for recipe in self.recipes:
            # Проверка изученности рецепта
            if hasattr(player, 'known_recipes'):
                if recipe.id not in player.known_recipes:
                    continue
            else:
                # Если система изученных рецептов не инициализирована, показываем все
                pass

            # Добавляем рецепт в список, даже если уровень недостаточен
            # Проверка уровня и других требований будет происходить в can_craft
            available.append(recipe)

        return available

    def get_recipes_by_category(self, category: str) -> List[CraftingRecipe]:
        """
        Получить рецепты по категории.

        Args:
            category: Категория рецептов

        Returns:
            List[CraftingRecipe]: Список рецептов категории
        """
        return [recipe for recipe in self.recipes if recipe.category == category]


class CraftingSystem:
    """Система крафта"""

    def __init__(self, config_path: str = None):
        """
        Инициализация системы крафта.

        Args:
            config_path: Путь к файлу конфигурации
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                'config',
                'crafting_config.json'
            )

        self.stations: Dict[str, CraftingStation] = {}
        self.recipes: Dict[str, CraftingRecipe] = {}
        self.categories: Dict[str, str] = {}

        self._load_config(config_path)

    def _load_config(self, config_path: str):
        """
        Загрузить конфигурацию из файла.

        Args:
            config_path: Путь к файлу конфигурации
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Загружаем категории
            self.categories = config.get('categories', {})

            # Загружаем станции
            for station_id, station_data in config['crafting_stations'].items():
                station = CraftingStation(station_id, station_data)
                self.stations[station_id] = station

            # Загружаем рецепты
            for recipe_data in config['recipes']:
                recipe = CraftingRecipe(recipe_data)
                self.recipes[recipe.id] = recipe

                # Добавляем рецепт к соответствующей станции
                if recipe.station in self.stations:
                    self.stations[recipe.station].add_recipe(recipe)

        except FileNotFoundError:
            print(f"Ошибка: файл конфигурации не найден: {config_path}")
        except json.JSONDecodeError as e:
            print(f"Ошибка при разборе JSON: {e}")

    def get_station(self, station_id: str) -> Optional[CraftingStation]:
        """
        Получить станцию крафта по ID.

        Args:
            station_id: ID станции

        Returns:
            Optional[CraftingStation]: Станция или None
        """
        return self.stations.get(station_id)

    def get_recipe(self, recipe_id: str) -> Optional[CraftingRecipe]:
        """
        Получить рецепт по ID.

        Args:
            recipe_id: ID рецепта

        Returns:
            Optional[CraftingRecipe]: Рецепт или None
        """
        return self.recipes.get(recipe_id)

    def craft_item(self, recipe_id: str, player, inventory) -> Tuple[bool, str]:
        """
        Создать предмет по рецепту.

        Args:
            recipe_id: ID рецепта
            player: Объект игрока
            inventory: Инвентарь игрока

        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return False, "Рецепт не найден"

        # Проверяем возможность создания
        can_craft, error_message = recipe.can_craft(player, inventory)
        if not can_craft:
            return False, error_message

        # Удаляем ресурсы из инвентаря
        for ingredient in recipe.ingredients:
            item_id = ingredient['item']
            quantity = ingredient['quantity']
            # Преобразуем ID предмета в его имя из инвентаря
            item_name = ITEM_ID_TO_NAME.get(item_id, item_id)
            inventory.remove_resource(item_name, quantity)

        # Добавляем созданный предмет
        # Пытаемся получить предмет из предопределенных
        from game.inventory import PREDEFINED_ITEMS, ItemGenerator

        result_item = None
        if recipe.result_item in PREDEFINED_ITEMS:
            result_item = PREDEFINED_ITEMS[recipe.result_item]
        else:
            # Если предмет не найден в предопределенных, пытаемся сгенерировать
            # Это для будущего расширения системы
            pass

        if result_item:
            inventory.add_item(result_item, recipe.result_quantity)

            # Увеличиваем опыт умения при успешном крафте
            if hasattr(recipe, 'required_skill') and recipe.required_skill:
                if hasattr(player, 'skill_manager'):
                    skill = player.skill_manager.get_skill(recipe.required_skill)
                    if skill:
                        # Добавляем опыт умению (10 опыта за каждый крафт)
                        exp_gained = 10
                        skill.add_experience(exp_gained)

                        # Информация о качестве зависит от ранга умения
                        quality_info = ""
                        if skill.rank >= 3:
                            quality_info = " [Высокое качество]"
                        elif skill.rank >= 2:
                            quality_info = " [Хорошее качество]"

                        return True, f"Создано: {recipe.name} x{recipe.result_quantity}{quality_info}\n+{exp_gained} опыта к умению {skill.name}"

            return True, f"Создано: {recipe.name} x{recipe.result_quantity}"
        else:
            # Возвращаем ресурсы, если не удалось создать предмет
            for ingredient in recipe.ingredients:
                item_id = ingredient['item']
                quantity = ingredient['quantity']
                # Преобразуем ID предмета в его имя из инвентаря
                item_name = ITEM_ID_TO_NAME.get(item_id, item_id)
                inventory.add_resource(item_name, quantity)
            return False, f"Ошибка: предмет '{recipe.result_item}' не найден в системе"

    def get_all_stations(self) -> List[CraftingStation]:
        """
        Получить все станции крафта.

        Returns:
            List[CraftingStation]: Список всех станций
        """
        return list(self.stations.values())

    def get_recipes_for_station(self, station_id: str, player=None) -> List[CraftingRecipe]:
        """
        Получить рецепты для станции.

        Args:
            station_id: ID станции
            player: Объект игрока (для фильтрации по уровню)

        Returns:
            List[CraftingRecipe]: Список рецептов
        """
        station = self.get_station(station_id)
        if not station:
            return []

        if player:
            return station.get_available_recipes(player)
        return station.recipes

    def get_category_name(self, category_id: str) -> str:
        """
        Получить название категории.

        Args:
            category_id: ID категории

        Returns:
            str: Название категории
        """
        return self.categories.get(category_id, category_id)
