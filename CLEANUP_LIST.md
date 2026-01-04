# Список файлов и директорий к удалению

**Дата:** 2026-01-04

## Директории к удалению (безопасное удаление)

Эти директории пустые и не используются. Можно удалить безопасно.

```bash
# Выполнить для удаления:
rm -rf game/input/
rm -rf game/persistence/
rm -rf game/rendering/
rm -rf game/world/
rm -rf game/entities/npc/
rm -rf game/ui/components/
```

### Детали:

| Директория | Причина удаления | Альтернатива |
|------------|------------------|--------------|
| `game/input/` | Пустой `__init__.py` | Логика в `game/input_handler.py` |
| `game/persistence/` | Пустой `__init__.py` | Логика в `game/save_system.py` |
| `game/rendering/` | Пустой `__init__.py` | Логика в `game/world_renderer.py`, `game/hud_renderer.py` |
| `game/world/` | Пустой `__init__.py` | Логика в `game/map.py` |
| `game/entities/npc/` | Пустой `__init__.py` | Дублирует `game/npc/` |
| `game/ui/components/` | Не импортируется | Классы доступны через `game/ui/base.py` |

---

## Файлы к удалению

```bash
# Выполнить для удаления:
rm promt.txt
```

| Файл | Причина |
|------|---------|
| `promt.txt` | Пустой файл в корне проекта |

---

## Мёртвый код в конфигах (НЕ удалять файлы, удалить секции)

### npc_config.json

Удалить секции:
- `relationships.matrix` (строки 237-445) - дублирует хардкод в constants.py
- `schedules` (строки 149-227) - не используется
- `stat_generation` (строки 24-31) - не используется

### balance_config.json

Удалить секции:
- `skills.*` - устаревшая система навыков
- `luck` - не используется
- `enemy_scaling` - не используется
- `skill_rank_requirements` - не используется
- `loot_events` - не используется

### economy_config.json

Удалить секции:
- `work.*` - не реализовано
- `services.*` - не реализовано

---

## Скрипт полной очистки

```bash
#!/bin/bash
# cleanup_dead_code.sh
# Запускать из корня проекта /home/user/classic_rpg2/

echo "Удаление пустых директорий..."
rm -rf game/input/
rm -rf game/persistence/
rm -rf game/rendering/
rm -rf game/world/
rm -rf game/entities/npc/
rm -rf game/ui/components/

echo "Удаление пустых файлов..."
rm -f promt.txt

echo "Готово! Удалено 6 директорий и 1 файл."
echo ""
echo "ВАЖНО: Не забудьте вручную очистить мёртвые секции в JSON конфигах!"
```

---

## Проверка перед удалением

Выполните эти команды для проверки, что директории действительно не используются:

```bash
# Проверка импортов из game/input/
grep -r "from game.input" game/ --include="*.py"
grep -r "import game.input" game/ --include="*.py"

# Проверка импортов из game/persistence/
grep -r "from game.persistence" game/ --include="*.py"
grep -r "import game.persistence" game/ --include="*.py"

# Проверка импортов из game/rendering/
grep -r "from game.rendering" game/ --include="*.py"
grep -r "import game.rendering" game/ --include="*.py"

# Проверка импортов из game/world/
grep -r "from game.world" game/ --include="*.py"
grep -r "import game.world" game/ --include="*.py"

# Проверка импортов из game/entities/npc/
grep -r "from game.entities.npc" game/ --include="*.py"
grep -r "import game.entities.npc" game/ --include="*.py"

# Проверка импортов из game/ui/components/
grep -r "from game.ui.components" game/ --include="*.py"
grep -r "import game.ui.components" game/ --include="*.py"
```

Все команды должны вернуть пустой результат.
