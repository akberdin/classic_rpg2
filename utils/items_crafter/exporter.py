"""
Экспортер конфигов для Items Crafter
Экспортирует данные в формат, совместимый с игрой
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from .models import (
    ItemsCrafterProject,
    ResourceItemData,
    WeaponItemData,
    ArmorItemData,
    JewelryItemData,
    PotionItemData,
    RecipeData,
    ItemsConfig,
)


class ItemsExporter:
    """Экспортер предметов и рецептов"""

    def __init__(self, project: ItemsCrafterProject):
        self.project = project

    def export_items_data(self, filepath: str) -> bool:
        """
        Экспорт items_data.json - реестр всех предметов
        """
        try:
            data = {
                "_description": "Реестр всех предметов игры",
                "_version": self.project.version,
                "_generated": datetime.now().isoformat(),
                "resources": [r.to_dict() for r in self.project.resources],
                "weapons": [w.to_dict() for w in self.project.weapons],
                "armor": [a.to_dict() for a in self.project.armors],
                "jewelry": [j.to_dict() for j in self.project.jewelry],
                "potions": [p.to_dict() for p in self.project.potions],
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Ошибка экспорта items_data.json: {e}")
            return False

    def export_items_config(self, filepath: str) -> bool:
        """
        Экспорт items_config.json - параметры предметов по качеству
        """
        try:
            data = self.project.items_config.to_dict()
            data["_generated"] = datetime.now().isoformat()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Ошибка экспорта items_config.json: {e}")
            return False

    def export_crafting_config(self, filepath: str) -> bool:
        """
        Экспорт crafting_config.json - рецепты крафта
        """
        try:
            # Группируем рецепты по станциям
            recipes_by_station: Dict[str, List[Dict]] = {}
            for recipe in self.project.recipes:
                station = recipe.station
                if station not in recipes_by_station:
                    recipes_by_station[station] = []
                recipes_by_station[station].append(recipe.to_dict())

            # Определения станций
            stations = {
                "workbench": {
                    "name": "Мастерская",
                    "description": "Базовая мастерская для создания простых предметов"
                },
                "forge": {
                    "name": "Кузница",
                    "description": "Для создания оружия, доспехов и переплавки руды"
                },
                "alchemy_table": {
                    "name": "Алхимический стол",
                    "description": "Для создания зелий и эликсиров"
                },
                "enchanting_table": {
                    "name": "Стол зачарования",
                    "description": "Для улучшения и зачарования предметов"
                }
            }

            data = {
                "_description": "Конфигурация крафтинговой системы",
                "_version": self.project.version,
                "_generated": datetime.now().isoformat(),
                "stations": stations,
                "recipes": [r.to_dict() for r in self.project.recipes],
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Ошибка экспорта crafting_config.json: {e}")
            return False

    def export_separate_configs(self, output_dir: str) -> Dict[str, bool]:
        """
        Экспорт отдельных конфигов для каждого типа предметов
        """
        results = {}
        os.makedirs(output_dir, exist_ok=True)

        # Ресурсы
        try:
            filepath = os.path.join(output_dir, "resources_config.json")
            data = {
                "_description": "Конфигурация ресурсов",
                "_version": self.project.version,
                "_generated": datetime.now().isoformat(),
                "resources": [r.to_dict() for r in self.project.resources],
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            results["resources"] = True
        except Exception as e:
            print(f"Ошибка экспорта resources_config.json: {e}")
            results["resources"] = False

        # Оружие
        try:
            filepath = os.path.join(output_dir, "weapons_config.json")
            data = {
                "_description": "Конфигурация оружия",
                "_version": self.project.version,
                "_generated": datetime.now().isoformat(),
                "weapons": [w.to_dict() for w in self.project.weapons],
                "parameters": self._get_weapon_parameters(),
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            results["weapons"] = True
        except Exception as e:
            print(f"Ошибка экспорта weapons_config.json: {e}")
            results["weapons"] = False

        # Броня
        try:
            filepath = os.path.join(output_dir, "armor_config.json")
            data = {
                "_description": "Конфигурация брони",
                "_version": self.project.version,
                "_generated": datetime.now().isoformat(),
                "armor": [a.to_dict() for a in self.project.armors],
                "parameters": self._get_armor_parameters(),
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            results["armor"] = True
        except Exception as e:
            print(f"Ошибка экспорта armor_config.json: {e}")
            results["armor"] = False

        # Украшения
        try:
            filepath = os.path.join(output_dir, "jewelry_config.json")
            data = {
                "_description": "Конфигурация украшений",
                "_version": self.project.version,
                "_generated": datetime.now().isoformat(),
                "jewelry": [j.to_dict() for j in self.project.jewelry],
                "parameters": self._get_jewelry_parameters(),
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            results["jewelry"] = True
        except Exception as e:
            print(f"Ошибка экспорта jewelry_config.json: {e}")
            results["jewelry"] = False

        # Зелья
        try:
            filepath = os.path.join(output_dir, "potions_config.json")
            data = {
                "_description": "Конфигурация зелий",
                "_version": self.project.version,
                "_generated": datetime.now().isoformat(),
                "potions": [p.to_dict() for p in self.project.potions],
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            results["potions"] = True
        except Exception as e:
            print(f"Ошибка экспорта potions_config.json: {e}")
            results["potions"] = False

        # Рецепты
        try:
            filepath = os.path.join(output_dir, "recipes_config.json")
            data = {
                "_description": "Конфигурация рецептов",
                "_version": self.project.version,
                "_generated": datetime.now().isoformat(),
                "recipes": [r.to_dict() for r in self.project.recipes],
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            results["recipes"] = True
        except Exception as e:
            print(f"Ошибка экспорта recipes_config.json: {e}")
            results["recipes"] = False

        return results

    def _get_weapon_parameters(self) -> Dict[str, Any]:
        """Получить параметры оружия из конфига"""
        if "weapon" in self.project.items_config.item_parameters:
            return {
                quality: params.to_dict()
                for quality, params in self.project.items_config.item_parameters["weapon"].items()
            }
        return {}

    def _get_armor_parameters(self) -> Dict[str, Any]:
        """Получить параметры брони из конфига"""
        result = {}
        for armor_type in ["light_armor", "medium_armor", "heavy_armor"]:
            if armor_type in self.project.items_config.item_parameters:
                result[armor_type] = {
                    quality: params.to_dict()
                    for quality, params in self.project.items_config.item_parameters[armor_type].items()
                }
        return result

    def _get_jewelry_parameters(self) -> Dict[str, Any]:
        """Получить параметры украшений из конфига"""
        result = {}
        for jewelry_type in ["ring", "amulet", "bracelet"]:
            if jewelry_type in self.project.items_config.item_parameters:
                result[jewelry_type] = {
                    quality: params.to_dict()
                    for quality, params in self.project.items_config.item_parameters[jewelry_type].items()
                }
        return result

    def export_to_game(self, game_config_dir: str) -> Dict[str, bool]:
        """
        Экспорт в формат игры (game/config/)
        """
        results = {}

        # items_data.json
        items_data_path = os.path.join(game_config_dir, "items_data.json")
        results["items_data"] = self.export_items_data(items_data_path)

        # items_config.json
        items_config_path = os.path.join(game_config_dir, "items_config.json")
        results["items_config"] = self.export_items_config(items_config_path)

        # crafting_config.json
        crafting_config_path = os.path.join(game_config_dir, "crafting_config.json")
        results["crafting_config"] = self.export_crafting_config(crafting_config_path)

        return results


class ItemsImporter:
    """Импортер предметов и рецептов из игровых конфигов"""

    @staticmethod
    def import_items_data(filepath: str) -> Optional[Dict[str, List]]:
        """Импорт items_data.json"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                "resources": [ResourceItemData.from_dict(r) for r in data.get("resources", [])],
                "weapons": [WeaponItemData.from_dict(w) for w in data.get("weapons", [])],
                "armors": [ArmorItemData.from_dict(a) for a in data.get("armor", [])],
                "jewelry": [JewelryItemData.from_dict(j) for j in data.get("jewelry", [])],
                "potions": [PotionItemData.from_dict(p) for p in data.get("potions", [])],
            }
        except Exception as e:
            print(f"Ошибка импорта items_data.json: {e}")
            return None

    @staticmethod
    def import_items_config(filepath: str) -> Optional[ItemsConfig]:
        """Импорт items_config.json"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return ItemsConfig.from_dict(data)
        except Exception as e:
            print(f"Ошибка импорта items_config.json: {e}")
            return None

    @staticmethod
    def import_crafting_config(filepath: str) -> Optional[List[RecipeData]]:
        """Импорт crafting_config.json"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            recipes = []
            for recipe_data in data.get("recipes", []):
                recipes.append(RecipeData.from_dict(recipe_data))

            return recipes
        except Exception as e:
            print(f"Ошибка импорта crafting_config.json: {e}")
            return None

    @classmethod
    def import_from_game(cls, game_config_dir: str) -> Optional[ItemsCrafterProject]:
        """
        Импорт полного проекта из игровых конфигов
        """
        project = ItemsCrafterProject()

        # Импорт items_data.json
        items_data_path = os.path.join(game_config_dir, "items_data.json")
        if os.path.exists(items_data_path):
            items_data = cls.import_items_data(items_data_path)
            if items_data:
                project.resources = items_data["resources"]
                project.weapons = items_data["weapons"]
                project.armors = items_data["armors"]
                project.jewelry = items_data["jewelry"]
                project.potions = items_data["potions"]

        # Импорт items_config.json
        items_config_path = os.path.join(game_config_dir, "items_config.json")
        if os.path.exists(items_config_path):
            items_config = cls.import_items_config(items_config_path)
            if items_config:
                project.items_config = items_config

        # Импорт crafting_config.json
        crafting_config_path = os.path.join(game_config_dir, "crafting_config.json")
        if os.path.exists(crafting_config_path):
            recipes = cls.import_crafting_config(crafting_config_path)
            if recipes:
                project.recipes = recipes

        return project


def save_project(project: ItemsCrafterProject, filepath: str) -> bool:
    """Сохранить проект в файл"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения проекта: {e}")
        return False


def load_project(filepath: str) -> Optional[ItemsCrafterProject]:
    """Загрузить проект из файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return ItemsCrafterProject.from_dict(data)
    except Exception as e:
        print(f"Ошибка загрузки проекта: {e}")
        return None
