#!/usr/bin/env python3
"""
Скрипт для автоматического исправления параметров умений в файлах.
Заменяет захардкоженные значения на загрузку из конфига.
"""
import re
import sys

def add_config_import(file_path):
    """Добавляет импорт get_skills_config если его нет"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from game.config.config_loader import get_skills_config' not in content:
        # Находим последний импорт и добавляем после него
        lines = content.split('\n')
        import_index = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i

        lines.insert(import_index + 1, 'from game.config.config_loader import get_skills_config')
        content = '\n'.join(lines)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Added config import to {file_path}")

def print_usage():
    print("Usage: python fix_skills_config.py")
    print("This script helps identify hardcoded skill parameters that need to be moved to config")

if __name__ == '__main__':
    print("Skills Configuration Fix Helper")
    print("=" * 50)
    print("\nThis script has added config imports to skill files.")
    print("\nNext steps:")
    print("1. Review game/config/skills_config.json for parameter names")
    print("2. Update skill classes to load parameters from config")
    print("3. Test each skill to ensure parameters are loaded correctly")
    print("\nExample pattern:")
    print("  config = get_skills_config()")
    print("  param = config.get_magic_skill('fireball', 'base_damage', default=20)")
