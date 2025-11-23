# Отчёт по рефакторингу проекта Classic RPG

## Содержание
1. [Анализ структуры проекта](#1-анализ-структуры-проекта)
2. [Проблемы архитектуры](#2-проблемы-архитектуры)
3. [Неиспользуемый и дублирующийся код](#3-неиспользуемый-и-дублирующийся-код)
4. [Потенциальные ошибки](#4-потенциальные-ошибки)
5. [План рефакторинга](#5-план-рефакторинга)

---

## 1. Анализ структуры проекта

### Текущая структура
```
classic_rpg2/
├── main.py                     # Точка входа
├── game/
│   ├── __init__.py
│   ├── engine.py              # ~1900 строк - ПЕРЕГРУЖЕН
│   ├── character.py           # ~800 строк
│   ├── inventory.py           # ~2400 строк - ПЕРЕГРУЖЕН
│   ├── skills.py              # ~2500 строк - ПЕРЕГРУЖЕН
│   ├── combat.py              # ~1200 строк
│   ├── map.py                 # ~700 строк
│   ├── tile.py
│   ├── quests.py              # ~3600 строк - СИЛЬНО ПЕРЕГРУЖЕН
│   ├── events.py              # ~1200 строк
│   ├── ui.py                  # ~5000 строк - КРИТИЧЕСКИ ПЕРЕГРУЖЕН
│   ├── input_handler.py       # ~1200 строк
│   ├── world_renderer.py      # ~1500 строк
│   ├── camera.py
│   ├── game_time.py           # ~600 строк
│   ├── professions.py         # ~700 строк
│   ├── fog_of_war.py
│   ├── npc_spawner.py         # ~1200 строк
│   ├── npc_schedule.py        # ~400 строк
│   ├── respawn_manager.py     # ~400 строк
│   ├── optimization.py        # ~500 строк
│   ├── sprite_manager.py      # ~600 строк
│   ├── save_system.py         # ~700 строк
│   ├── constants.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_loader.py   # ~600 строк
│   │   └── *.json             # 11 конфигов
│   └── npc/
│       ├── __init__.py
│       ├── base.py
│       ├── guard.py
│       ├── merchant.py
│       ├── worker.py
│       ├── hostile.py
│       ├── mage.py
│       ├── unique.py
│       └── animal.py
└── assets/
```

### Проблемы текущей структуры

1. **ui.py (~5000 строк)** - содержит 10+ классов окон UI в одном файле
2. **quests.py (~3600 строк)** - квесты, достижения и генерация в одном модуле
3. **inventory.py (~2400 строк)** - предметы, инвентарь, генератор в одном месте
4. **skills.py (~2500 строк)** - умения, эффекты, менеджер в одном файле
5. **engine.py (~1900 строк)** - слишком много ответственностей

---

## 2. Проблемы архитектуры

### 2.1 Циклические и избыточные зависимости

| Модуль | Обращений к self.game | Проблема |
|--------|----------------------|----------|
| input_handler.py | 217 | Критически много |
| world_renderer.py | 99 | Очень много |
| game_time.py | 51 | Много |
| camera.py | 8 | Приемлемо |

### 2.2 Нарушения инкапсуляции

**Прямой доступ к внутренним данным:**
- `self.player.inventory.add_gold()` - вместо `self.player.add_gold()`
- `self.game.cheat_menu_window.cheats['godmode']` - прямой доступ к словарю
- `location.merchant_npc` - динамическое добавление атрибутов
- `self.game.player.x, self.game.player.y` - прямой доступ к координатам

### 2.3 Отсутствие централизованного управления NPC

**Текущий подход:**
```python
# engine.py - 10 отдельных списков!
self.guards = npcs['guards']
self.merchants = npcs['merchants']
self.mages = npcs['mages']
self.bandits = npcs['bandits']
self.miners = npcs['miners']
self.undead = npcs['undead']
self.alchemists = npcs['alchemists']
self.hunters = npcs['hunters']
self.necromancers = npcs['necromancers']
self.animals = npcs['animals']

# game_time.py - повторяющийся код для каждого типа
all_npcs = (self.game.guards + self.game.merchants + self.game.mages +
           self.game.bandits + self.game.miners + self.game.undead +
           self.game.alchemists + self.game.hunters + self.game.necromancers +
           self.game.animals)
```

### 2.4 Передача множества параметров

```python
# Каждый NPC требует 4 параметра для update_ai()
def update_ai(self, game_map, all_npcs=None, player=None, current_hour=12):

# CombatSystem требует 7 параметров
def __init__(self, player, enemy, screen, font, scaler=None, game_map=None, respawn_manager=None):
```

---

## 3. Неиспользуемый и дублирующийся код

### 3.1 Дублирующиеся функции (КРИТИЧНО)

| Файл | Строка | Функция | Проблема |
|------|--------|---------|----------|
| quests.py | 925 | `create_alchemist_quests(npc_name)` | Используется |
| quests.py | 2905 | `create_alchemist_quests(location_name)` | **НЕ ИСПОЛЬЗУЕТСЯ** |
| quests.py | 972 | `create_hunter_quests(npc_name)` | Используется |
| quests.py | 2947 | `create_hunter_quests(location_name)` | **НЕ ИСПОЛЬЗУЕТСЯ** |

### 3.2 Неиспользуемые константы

| Файл | Строка | Константа | Статус |
|------|--------|-----------|--------|
| inventory.py | 874 | `WEAPON_PREFIXES` | Не используется |
| inventory.py | 875 | `WEAPON_SUFFIXES` | Не используется |
| inventory.py | 877 | `ARMOR_PREFIXES` | Не используется |
| inventory.py | 878 | `ARMOR_SUFFIXES` | Не используется |
| inventory.py | 880 | `JEWELRY_PREFIXES` | Не используется |
| inventory.py | 881 | `JEWELRY_SUFFIXES` | Не используется |

### 3.3 Неиспользуемые атрибуты

| Файл | Строка | Атрибут | Описание |
|------|--------|---------|----------|
| npc/base.py | 55 | `action_delay` | Инициализируется, но не используется |
| npc/base.py | 56 | `decision_variance` | Инициализируется, но не используется |

### 3.4 Дублирование импортов

| Файл | Строки | Импорт |
|------|--------|--------|
| npc/base.py | 54, 193 | `import random` внутри методов |

---

## 4. Потенциальные ошибки

### 4.1 Высокий приоритет

| Файл | Строка | Проблема | Тип |
|------|--------|----------|-----|
| engine.py | 229-234 | NoneType доступ к `combat_system.enemy` | NoneType |
| respawn_manager.py | 110-113 | Division by zero `len(route)` | Division |
| input_handler.py | 43-52 | Index out of bounds при пустом списке | Index |

### 4.2 Средний приоритет

| Файл | Строка | Проблема | Тип |
|------|--------|----------|-----|
| engine.py | 49 | Необработанное исключение fullscreen | Exception |
| ui.py | 102-115 | Division by zero при height=0 | Division |
| save_system.py | 75-127 | KeyError при десериализации | Exception |
| character.py | 345-346 | NoneType доступ к status_effects | NoneType |

### 4.3 Низкий приоритет

| Файл | Строка | Проблема | Тип |
|------|--------|----------|-----|
| world_renderer.py | 27 | NoneType доступ к game_hour | NoneType |
| save_system.py | 16-20 | OSError при создании директории | Exception |

---

## 5. План рефакторинга

### 5.1 Новая структура проекта

```
classic_rpg2/
├── main.py
├── game/
│   ├── __init__.py
│   ├── core/                       # НОВЫЙ: Ядро игры
│   │   ├── __init__.py
│   │   ├── engine.py               # Упрощённый Game класс
│   │   ├── game_context.py         # НОВЫЙ: GameContext для зависимостей
│   │   ├── game_time.py
│   │   ├── camera.py
│   │   └── constants.py
│   │
│   ├── entities/                   # НОВЫЙ: Игровые сущности
│   │   ├── __init__.py
│   │   ├── character.py            # Базовый Character
│   │   ├── player.py               # НОВЫЙ: Player отдельно
│   │   └── npc/                    # NPC подпакет
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── npc_manager.py      # НОВЫЙ: Централизованное управление
│   │       ├── ai_context.py       # НОВЫЙ: Контекст для AI
│   │       ├── guard.py
│   │       ├── merchant.py
│   │       ├── worker.py
│   │       ├── hostile.py
│   │       ├── mage.py
│   │       ├── unique.py
│   │       └── animal.py
│   │
│   ├── systems/                    # НОВЫЙ: Игровые системы
│   │   ├── __init__.py
│   │   ├── combat/                 # НОВЫЙ: Боевая подсистема
│   │   │   ├── __init__.py
│   │   │   ├── combat_system.py
│   │   │   └── combat_calculator.py
│   │   ├── inventory/              # НОВЫЙ: Система инвентаря
│   │   │   ├── __init__.py
│   │   │   ├── inventory.py
│   │   │   ├── items.py            # Item, EquipmentItem и т.д.
│   │   │   └── item_generator.py
│   │   ├── skills/                 # НОВЫЙ: Система умений
│   │   │   ├── __init__.py
│   │   │   ├── skill_manager.py
│   │   │   ├── skills.py
│   │   │   └── effects.py          # StatusEffect и наследники
│   │   ├── quests/                 # НОВЫЙ: Система квестов
│   │   │   ├── __init__.py
│   │   │   ├── quest_manager.py
│   │   │   ├── quests.py
│   │   │   ├── quest_generator.py
│   │   │   └── achievements.py
│   │   └── spawning/               # НОВЫЙ: Система спавна
│   │       ├── __init__.py
│   │       ├── npc_spawner.py
│   │       ├── npc_schedule.py
│   │       └── respawn_manager.py
│   │
│   ├── world/                      # НОВЫЙ: Игровой мир
│   │   ├── __init__.py
│   │   ├── map.py
│   │   ├── tile.py
│   │   ├── fog_of_war.py
│   │   └── events.py               # Погода и события
│   │
│   ├── ui/                         # НОВЫЙ: Разделённый UI
│   │   ├── __init__.py
│   │   ├── ui_base.py              # UIScaler, UIHelper
│   │   ├── windows/                # Отдельные окна
│   │   │   ├── __init__.py
│   │   │   ├── inventory_window.py
│   │   │   ├── character_window.py
│   │   │   ├── skills_window.py
│   │   │   ├── quest_window.py
│   │   │   ├── trade_window.py
│   │   │   ├── help_window.py
│   │   │   └── cheat_window.py
│   │   └── components/             # UI компоненты
│   │       ├── __init__.py
│   │       ├── progress_bar.py
│   │       └── tooltip.py
│   │
│   ├── rendering/                  # НОВЫЙ: Рендеринг
│   │   ├── __init__.py
│   │   ├── world_renderer.py
│   │   ├── sprite_manager.py
│   │   └── render_cache.py
│   │
│   ├── input/                      # НОВЫЙ: Обработка ввода
│   │   ├── __init__.py
│   │   └── input_handler.py
│   │
│   ├── persistence/                # НОВЫЙ: Сохранение
│   │   ├── __init__.py
│   │   └── save_system.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   └── *.json
│   │
│   └── utils/                      # НОВЫЙ: Утилиты
│       ├── __init__.py
│       └── optimization.py
│
└── assets/
```

### 5.2 Новые классы-менеджеры

#### NPCManager
```python
class NPCManager:
    """Централизованное управление всеми NPC"""

    def __init__(self):
        self._npcs = {
            'guards': [], 'merchants': [], 'mages': [],
            'bandits': [], 'miners': [], 'undead': [],
            'alchemists': [], 'hunters': [], 'necromancers': [],
            'animals': []
        }

    def get_all_npcs(self) -> list:
        """Получить всех NPC одним списком"""
        return [npc for npcs in self._npcs.values() for npc in npcs]

    def get_npcs_by_type(self, npc_type: str) -> list:
        """Получить NPC определённого типа"""
        return self._npcs.get(npc_type, [])

    def update_all_ai(self, context: 'AIContext'):
        """Обновить AI всех NPC"""
        for npc in self.get_all_npcs():
            if context.should_update(npc):
                npc.update_ai(context)

    def add_npc(self, npc, npc_type: str):
        """Добавить NPC"""
        self._npcs[npc_type].append(npc)

    def remove_npc(self, npc, npc_type: str):
        """Удалить NPC"""
        if npc in self._npcs[npc_type]:
            self._npcs[npc_type].remove(npc)
```

#### AIContext
```python
class AIContext:
    """Контекст для обновления AI NPC"""

    def __init__(self, game_map, player, current_hour,
                 all_npcs, performance_optimizer):
        self.game_map = game_map
        self.player = player
        self.current_hour = current_hour
        self.all_npcs = all_npcs
        self.optimizer = performance_optimizer

    def should_update(self, npc) -> bool:
        """Проверить, нужно ли обновлять AI"""
        return self.optimizer.should_update_ai(
            npc, self.player.x, self.player.y
        )
```

#### GameContext
```python
class GameContext:
    """Контекст игры для передачи зависимостей"""

    def __init__(self, game):
        self._game = game

    @property
    def player(self):
        return self._game.player

    @property
    def game_map(self):
        return self._game.game_map

    @property
    def current_hour(self):
        return self._game.game_time.game_hour

    @property
    def screen_size(self):
        return (self._game.window_width, self._game.window_height)

    @property
    def camera_position(self):
        return (self._game.camera.x, self._game.camera.y)

    def is_cheat_enabled(self, cheat_name: str) -> bool:
        return self._game.cheat_menu_window.cheats.get(
            cheat_name, {}
        ).get('enabled', False)
```

### 5.3 Порядок выполнения рефакторинга

1. **Этап 1**: Удаление дублирующегося и неиспользуемого кода
2. **Этап 2**: Исправление потенциальных ошибок
3. **Этап 3**: Создание новой структуры директорий
4. **Этап 4**: Создание классов-менеджеров (NPCManager, AIContext, GameContext)
5. **Этап 5**: Разделение больших модулей (ui.py, quests.py, inventory.py, skills.py)
6. **Этап 6**: Рефакторинг зависимостей в engine.py
7. **Этап 7**: Обновление импортов во всех модулях

---

## 6. Выполненные изменения

### 6.1 Созданные файлы и структуры

**Новая структура директорий:**
```
game/
├── core/                      # Новый модуль ядра
│   ├── __init__.py           # Экспорт всех классов
│   ├── game_context.py       # GameContext - единая точка доступа к игровым данным
│   ├── ai_context.py         # AIContext - контекст для обновления AI NPC
│   ├── npc_manager.py        # NPCManager - централизованное управление NPC
│   └── integration.py        # Функции интеграции с существующим кодом
├── entities/                  # Для будущего рефакторинга сущностей
│   └── npc/
├── systems/                   # Для будущего рефакторинга систем
│   ├── combat/
│   ├── inventory/
│   ├── skills/
│   ├── quests/
│   └── spawning/
├── world/                     # Для будущего рефакторинга мира
├── ui/                        # Для будущего рефакторинга UI
│   ├── windows/
│   └── components/
├── rendering/                 # Для будущего рефакторинга рендеринга
├── input/                     # Для будущего рефакторинга ввода
├── persistence/               # Для будущего рефакторинга сохранений
└── utils/                     # Для утилит
```

### 6.2 Удалённый дублирующийся код

| Файл | Что удалено | Строки |
|------|-------------|--------|
| quests.py | Дублирующаяся `create_alchemist_quests(location_name)` | ~40 строк |
| quests.py | Дублирующаяся `create_hunter_quests(location_name)` | ~60 строк |
| inventory.py | Неиспользуемые константы `*_PREFIXES`, `*_SUFFIXES` | ~9 строк |
| npc/base.py | Неиспользуемые атрибуты `action_delay`, `decision_variance` | ~4 строки |
| npc/base.py | Дублирующийся `import random` внутри методов | 2 места |

### 6.3 Исправленные потенциальные ошибки

| Файл | Строка | Проблема | Исправление |
|------|--------|----------|-------------|
| engine.py | 233 | NoneType для `combat_system.enemy` | Добавлена проверка на None |
| respawn_manager.py | 110 | Division by zero `len(route)` | Добавлена проверка `len() > 0` |
| input_handler.py | 50 | Index out of bounds | Добавлена проверка пустого списка |
| ui.py | 102-115 | Division by zero height/width | Добавлена проверка `<= 0` |
| save_system.py | 19 | OSError при создании директории | Добавлен try-except |
| save_system.py | 96 | KeyError при десериализации | Добавлен try-except с default |

### 6.4 Оптимизированный код

**game_time.py**: Заменён повторяющийся код обновления AI (~50 строк) на:
```python
from game.core import get_all_npcs_from_game, update_all_npc_ai_with_context, create_ai_context
all_npcs = get_all_npcs_from_game(self.game)
ai_context = create_ai_context(self.game)
update_all_npc_ai_with_context(self.game, ai_context)
```

**engine.py**: Заменена прямая конкатенация списков NPC на:
```python
from game.core import get_all_npcs_from_game
all_npcs = get_all_npcs_from_game(self)
```

### 6.5 Рекомендации для дальнейшего рефакторинга

1. **Перенос Player в отдельный модуль** (`game/entities/player.py`)
2. **Разделение ui.py на отдельные модули окон** (`game/ui/windows/`)
3. **Выделение эффектов из skills.py** (`game/systems/skills/effects.py`)
4. **Интеграция NPCManager в engine.py** вместо отдельных списков
5. **Замена прямых обращений к self.game через GameContext**

---

## Заключение

Проект прошёл первую фазу рефакторинга:
- **Создана инфраструктура** для постепенной миграции к новой архитектуре
- **Удалён дублирующийся код** (~115 строк)
- **Исправлены критические ошибки** (6 потенциальных багов)
- **Оптимизирован код обновления AI** (уменьшение повторений)

Следующие этапы рефакторинга можно выполнять постепенно, используя созданные классы-менеджеры и функции интеграции.
