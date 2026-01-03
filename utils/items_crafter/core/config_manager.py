"""
Менеджер конфигураций v2.0

Управляет сохранением/загрузкой всех конфигов системы предметов.
Конфиги хранятся в utils/items_crafter/configs/ и изолированы от игры.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from .item_models import ItemsProject, BaseItem, Recipe
from .item_templates import TemplatesConfig
from .naming_system import NamingConfig


# ==================== ПУТИ К КОНФИГАМ ====================

def get_configs_dir() -> Path:
    """Получить путь к директории конфигов"""
    # utils/items_crafter/configs/
    current_file = Path(__file__)
    return current_file.parent.parent / "configs"


def ensure_configs_dir():
    """Убедиться что директория конфигов существует"""
    configs_dir = get_configs_dir()
    configs_dir.mkdir(parents=True, exist_ok=True)
    return configs_dir


# ==================== ПОЛНАЯ КОНФИГУРАЦИЯ ====================

@dataclass
class CrafterConfig:
    """
    Полная конфигурация Items Crafter v2.0
    Объединяет все конфиги в одном месте
    """
    # Метаданные
    version: str = "2.0.0"
    name: str = "Новый проект"
    created_at: str = ""
    modified_at: str = ""

    # Основные данные
    project: ItemsProject = field(default_factory=ItemsProject)
    templates: TemplatesConfig = field(default_factory=TemplatesConfig)
    naming: NamingConfig = field(default_factory=NamingConfig)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.modified_at = datetime.now().isoformat()

    def mark_modified(self):
        """Отметить как изменённый"""
        self.modified_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_meta": {
                "version": self.version,
                "name": self.name,
                "created_at": self.created_at,
                "modified_at": self.modified_at,
            },
            "project": self.project.to_dict(),
            "templates": self.templates.to_dict(),
            "naming": self.naming.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrafterConfig":
        meta = data.get("_meta", {})
        return cls(
            version=meta.get("version", "2.0.0"),
            name=meta.get("name", "Новый проект"),
            created_at=meta.get("created_at", ""),
            modified_at=meta.get("modified_at", ""),
            project=ItemsProject.from_dict(data.get("project", {})),
            templates=TemplatesConfig.from_dict(data.get("templates", {})),
            naming=NamingConfig.from_dict(data.get("naming", {})),
        )

    @classmethod
    def create_default(cls) -> "CrafterConfig":
        """Создать конфигурацию с значениями по умолчанию"""
        return cls(
            project=ItemsProject(),
            templates=TemplatesConfig.create_default(),
            naming=NamingConfig.create_default(),
        )


# ==================== МЕНЕДЖЕР КОНФИГОВ ====================

class ConfigManager:
    """
    Менеджер для работы с конфигурациями
    """

    def __init__(self, config: Optional[CrafterConfig] = None):
        self.config = config or CrafterConfig.create_default()
        self.current_file: Optional[Path] = None
        self._is_modified = False

    @property
    def is_modified(self) -> bool:
        return self._is_modified

    def mark_modified(self):
        """Отметить как изменённый"""
        self._is_modified = True
        self.config.mark_modified()

    def mark_saved(self):
        """Отметить как сохранённый"""
        self._is_modified = False

    # ==================== ОПЕРАЦИИ С ФАЙЛАМИ ====================

    def save(self, filepath: Optional[str] = None) -> bool:
        """Сохранить конфигурацию в файл"""
        try:
            if filepath:
                self.current_file = Path(filepath)
            elif not self.current_file:
                # Автоматическое имя файла
                configs_dir = ensure_configs_dir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.current_file = configs_dir / f"project_{timestamp}.json"

            self.config.mark_modified()

            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, ensure_ascii=False, indent=2)

            self.mark_saved()
            return True

        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False

    def load(self, filepath: str) -> bool:
        """Загрузить конфигурацию из файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.config = CrafterConfig.from_dict(data)
            self.current_file = Path(filepath)
            self.mark_saved()
            return True

        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            return False

    def new(self):
        """Создать новую конфигурацию"""
        self.config = CrafterConfig.create_default()
        self.current_file = None
        self._is_modified = False

    # ==================== ЭКСПОРТ ====================

    def export_items_json(self, filepath: str) -> bool:
        """Экспортировать только предметы в JSON"""
        try:
            data = {
                "_description": "Экспорт предметов Items Crafter v2.0",
                "_version": self.config.version,
                "_exported_at": datetime.now().isoformat(),
                "resources": [r.to_dict() for r in self.config.project.resources],
                "weapons": [w.to_dict() for w in self.config.project.weapons],
                "armor": [a.to_dict() for a in self.config.project.armor],
                "jewelry": [j.to_dict() for j in self.config.project.jewelry],
                "consumables": [c.to_dict() for c in self.config.project.consumables],
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Ошибка экспорта предметов: {e}")
            return False

    def export_recipes_json(self, filepath: str) -> bool:
        """Экспортировать только рецепты в JSON"""
        try:
            data = {
                "_description": "Экспорт рецептов Items Crafter v2.0",
                "_version": self.config.version,
                "_exported_at": datetime.now().isoformat(),
                "recipes": [r.to_dict() for r in self.config.project.recipes],
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Ошибка экспорта рецептов: {e}")
            return False

    def export_templates_json(self, filepath: str) -> bool:
        """Экспортировать шаблоны в JSON"""
        try:
            data = {
                "_description": "Экспорт шаблонов Items Crafter v2.0",
                "_version": self.config.version,
                "_exported_at": datetime.now().isoformat(),
                **self.config.templates.to_dict(),
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Ошибка экспорта шаблонов: {e}")
            return False

    def export_naming_json(self, filepath: str) -> bool:
        """Экспортировать словари нейминга в JSON"""
        try:
            data = {
                "_description": "Экспорт словарей нейминга Items Crafter v2.0",
                "_version": self.config.version,
                "_exported_at": datetime.now().isoformat(),
                **self.config.naming.to_dict(),
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Ошибка экспорта словарей: {e}")
            return False

    def export_all(self, output_dir: str) -> Dict[str, bool]:
        """Экспортировать все конфиги в отдельные файлы"""
        results = {}
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results["items"] = self.export_items_json(str(output_path / "items.json"))
        results["recipes"] = self.export_recipes_json(str(output_path / "recipes.json"))
        results["templates"] = self.export_templates_json(str(output_path / "templates.json"))
        results["naming"] = self.export_naming_json(str(output_path / "naming.json"))

        return results

    # ==================== БЫСТРЫЙ ДОСТУП К ПРОЕКТУ ====================

    @property
    def project(self) -> ItemsProject:
        return self.config.project

    @property
    def templates(self) -> TemplatesConfig:
        return self.config.templates

    @property
    def naming(self) -> NamingConfig:
        return self.config.naming

    def get_all_items(self) -> List[BaseItem]:
        return self.project.get_all_items()

    def get_all_recipes(self) -> List[Recipe]:
        return self.project.recipes

    def validate(self) -> List[str]:
        """Валидация всего проекта"""
        return self.project.validate()


# ==================== БУФЕР ОБМЕНА ====================

class ClipboardManager:
    """
    Менеджер буфера обмена для копирования/вырезания/вставки
    """

    def __init__(self):
        self._clipboard: Optional[Dict[str, Any]] = None
        self._clipboard_type: Optional[str] = None
        self._is_cut: bool = False

    def copy(self, item: Any, item_type: str):
        """Копировать объект"""
        if hasattr(item, 'to_dict'):
            self._clipboard = item.to_dict()
        else:
            self._clipboard = item
        self._clipboard_type = item_type
        self._is_cut = False

    def cut(self, item: Any, item_type: str):
        """Вырезать объект"""
        self.copy(item, item_type)
        self._is_cut = True

    def paste(self) -> Optional[Dict[str, Any]]:
        """Вставить объект (возвращает данные, сброс при вырезании)"""
        if self._clipboard is None:
            return None

        result = self._clipboard.copy()

        if self._is_cut:
            self._clipboard = None
            self._clipboard_type = None
            self._is_cut = False

        return result

    def clear(self):
        """Очистить буфер"""
        self._clipboard = None
        self._clipboard_type = None
        self._is_cut = False

    @property
    def has_content(self) -> bool:
        return self._clipboard is not None

    @property
    def content_type(self) -> Optional[str]:
        return self._clipboard_type

    @property
    def is_cut_operation(self) -> bool:
        return self._is_cut


# Глобальный буфер обмена
clipboard = ClipboardManager()
