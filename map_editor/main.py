#!/usr/bin/env python3
"""
Classic RPG Map Editor
Standalone visual map editor for creating and editing game maps.

Usage:
    python -m map_editor.main
    # or
    python map_editor/main.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def main():
    """Main entry point for the map editor."""
    try:
        from map_editor.editor import MapEditor

        print("=" * 50)
        print("Classic RPG - Map Editor v1.0")
        print("=" * 50)
        print()
        print("Управление:")
        print("  V - Инструмент выбора")
        print("  B - Кисть биомов")
        print("  G - Заливка")
        print("  O - Размещение объектов")
        print("  E - Удаление объектов")
        print("  M - Перемещение объектов")
        print()
        print("  F5 - Генерировать новую карту")
        print("  F6 - Перегенерировать (новый seed)")
        print("  Ctrl+S - Сохранить")
        print("  Ctrl+O - Открыть")
        print()
        print("  Колесо мыши - Масштаб")
        print("  СКМ (средняя кнопка) - Перемещение камеры")
        print("  +/- - Масштаб")
        print("  Home - Вписать карту в экран")
        print()
        print("Запуск редактора...")
        print()

        editor = MapEditor()
        editor.run()

    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("Убедитесь, что pygame установлен: pip install pygame")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
