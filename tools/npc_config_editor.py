#!/usr/bin/env python3
"""
NPC Config Editor v3.0 - Модульный редактор NPC

Запускает новую модульную версию редактора из tools/npc_editor/

Структура вкладок:
- Типовые NPC (шаблоны для спавна):
  - Общая: основная информация, характеристики, экипировка
  - Лут: золото и выпадение предметов
  - Умения: умения и способности

- Уникальные NPC (именованные персонажи):
  - Общая: основная информация, характеристики, экипировка
  - Лут: гарантированное золото и предметы
  - Умения: умения и способности
"""

import os
import sys

# Добавляем путь к проекту
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from tools.npc_editor.main import main

if __name__ == '__main__':
    main()
