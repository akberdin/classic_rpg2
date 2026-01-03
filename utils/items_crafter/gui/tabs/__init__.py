"""
Вкладки редактора для различных типов предметов
"""

from .base_tab import BaseEditorTab
from .resources_tab import ResourcesTab
from .weapons_tab import WeaponsTab
from .armor_tab import ArmorTab
from .jewelry_tab import JewelryTab
from .potions_tab import PotionsTab
from .recipes_tab import RecipesTab

__all__ = [
    'BaseEditorTab',
    'ResourcesTab',
    'WeaponsTab',
    'ArmorTab',
    'JewelryTab',
    'PotionsTab',
    'RecipesTab',
]
