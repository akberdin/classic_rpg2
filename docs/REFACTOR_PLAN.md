# Промпт для LLM: рефакторинг топ-10 самых нагруженных модулей `classic_rpg2`

> **Как использовать этот файл.**
> Это исполнительный промпт. Открой его в начале сессии, выбери **один этап** (см. секцию «Этапы»), прочитай его целиком, выполни шаги, открой PR, дождись зелёного smoke-теста, замёрдь, переходи к следующему. **Никогда не делай больше одного этапа за PR.**

---

## 1. Роль и цели

Ты — инженер-рефакторер кодовой базы Python/Pygame-игры `classic_rpg2`. Твоя цель — снизить ответственность 10 самых больших/перегруженных модулей, перенося куски кода в правильные дома, **не меняя поведения игры**.

**Что НЕЛЬЗЯ делать:**
1. Менять игровую логику, формулы, баланс, тексты.
2. Добавлять новые фичи, абстракции «на будущее», DI-фреймворки, паттерн-обёртки ради паттернов.
3. Ломать формат сейвов (`save/*.json`). Старые сейвы должны грузиться без потерь.
4. Делать «по дороге» косметику, переименования полей, переформатирование не относящихся к этапу файлов.
5. Сливать несколько этапов в один PR.
6. Удалять shim'ы и старые имена в том же PR, в котором их завёл. Удаление — следующим PR.

**Что НУЖНО делать:**
1. Один этап = один PR. Внутри этапа — атомарные коммиты.
2. На каждом этапе прогонять smoke-тест (см. секцию 4).
3. Если этап затрагивает save-формат — прогонять baseline-snapshot (см. секцию 4).
4. Импорты в остальном коде поправить в том же PR (через shim для совместимости, если нужно).
5. После PR обновлять чек-лист в этом файле (секция «Прогресс»).

---

## 2. Контекст репозитория

- Корень: `/home/user/classic_rpg2`
- Точка входа: `main.py` → `game/engine.py::Game`
- Рабочая ветка: `claude/nifty-lovelace-cadMv`
- Все коммиты — на эту ветку. PR — в `main` (или в ветку, которую укажет пользователь).
- Тестов почти нет: smoke-тест — это запуск `main.py` и/или (после Фазы 0) — `tests/test_smoke.py`.

### Топ-10 файлов (на момент составления плана)

| # | Файл | Строк | Главные сущности |
|---|---|---:|---|
| 1 | `game/inventory.py` | 2719 | `Item`+подклассы, `Inventory`, `ItemGenerator` (~1200), утилиты loot |
| 2 | `game/input_handler.py` | 1798 | `InputHandler` со всеми `handle_*` |
| 3 | `game/events.py` | 1316 | `WeatherSystem`, `RandomEventSystem`, `KillstreakSystem`, `TimeOfDayBonuses` |
| 4 | `game/engine.py` | 1263 | `Game` (главный цикл + всё подряд) |
| 5 | `game/npc_spawner.py` | 1022 | `NPCSpawner.spawn_*` по типам NPC + `_create_patrol_route` (дубль) |
| 6 | `game/world_renderer.py` | 1033 | `WorldRenderer` + `_render_<тип_NPC>` (7 шт) + minimap |
| 7 | `game/constants.py` | 722 | статические литералы + `_init_dynamic_constants()` |
| 8 | `game/character.py` | 716 | `Character` (статы + бой + регенерация + экипировка) |
| 9 | `game/respawn_manager.py` | 639 | `RespawnManager` + утилиты, которые ему не принадлежат |
| 10 | `game/save_system.py` | 550 | `SaveSystem` — централизованная (де)сериализация всех доменов |

---

## 3. Базовые принципы переноса

1. **«Дом» для логики выбирается по доменной принадлежности, а не по «куда удобнее».**
   - Логика боя — в `combat.py`, не в `character.py`.
   - Сериализация объекта — методом самого объекта (`to_dict`/`from_dict`), не в `save_system.py`.
   - Конфигурация — в `config/`, не в `constants.py`.
2. **Shim-файл на переезд.** В исходном файле оставляешь re-export, чтобы старые импорты не падали:
   ```python
   # game/events.py (после Этапа 1)
   # deprecated: переехало в weather.py / random_events.py / game_time.py
   from game.weather import WeatherType, WeatherSystem  # noqa: F401
   from game.random_events import (  # noqa: F401
       RandomEventSystem, EventType, RandomEvent, EventResult,
   )
   from game.game_time import TimeOfDayBonuses  # noqa: F401
   ```
3. **Замена импортов** в потребителях — в **том же PR**, что и перенос. Shim остаётся на 1 PR как страховка, в следующем PR удаляется.
4. **Никаких функциональных правок.** Если по дороге увидел баг — `TODO(refactor): see issue #N` и отдельный PR.
5. **Делегаты сохраняют публичный API.** Когда выносишь метод из класса в свободную функцию, оставь у класса тонкий делегат:
   ```python
   # game/character.py
   def attack(self, target):
       from game.combat.character_combat import attack as _attack
       return _attack(self, target)
   ```
   Делегаты убираются после того, как все вызывающие места переехали на прямой API.

---

## 4. Гейты приёмки

**Smoke-тест (обязательно на каждом этапе):**

```bash
cd /home/user/classic_rpg2
python -c "import main"          # импорт не падает
python -m py_compile $(git ls-files '*.py')  # синтаксис
# headless-запуск (если уже есть tests/test_smoke.py)
python -m pytest tests/test_smoke.py -x -q
```

Если `tests/test_smoke.py` ещё нет — он создаётся в **Фазе 0** (см. секцию 5). До Фазы 0 запускать `main.py` вручную в течение 10 секунд: создать персонажа, сделать шаг, открыть инвентарь, сохраниться, загрузиться. Описать в PR.

**Baseline save-snapshot (для этапов 2, 4, 5, 6, 7):**

В Фазе 0 коммитится `tests/fixtures/baseline_save.json` — автосейв, снятый до начала рефакторинга. На каждом этапе, который трогает сериализацию:

```bash
python -m pytest tests/test_save_compat.py -x -q
```

Тест грузит baseline-сейв и сверяет ключевые инварианты (hp игрока, кол-во NPC, инвентарь, день/час, fog_of_war).

**Гейт мерджа PR:**

- smoke-тест зелёный;
- если затронут save: baseline-тест зелёный;
- ни один публичный импорт из топ-10 файлов не сломан (см. список в Фазе 0);
- PR описание содержит: какой этап, что перенесено, какие импорты обновлены, осталось ли shim'ов.

---

## 5. Фаза 0: подготовка (отдельный PR, делается первым)

**Задачи:**

1. Создать `tests/test_smoke.py`:
   - инициализация `Game()` без открытия окна (mock pygame display, если нужно);
   - один тик `_update()`;
   - вызов `SaveSystem.save_game(game, "test_save")` и `SaveSystem.load_game("test_save")`;
   - проверка, что игрок жив и координаты сохранены.
2. Запустить игру вручную, дойти до стабильного состояния, скопировать `save/autosave.json` → `tests/fixtures/baseline_save.json`. Закоммитить.
3. Создать `tests/test_save_compat.py`: грузит `baseline_save.json` через `SaveSystem.load_game` (предварительно копируя в `save/`), проверяет ключевые поля.
4. Зафиксировать список публичных имён, импортируемых из топ-10 файлов:
   ```bash
   grep -rn "from game\.\(inventory\|input_handler\|events\|engine\|npc_spawner\|world_renderer\|constants\|character\|respawn_manager\|save_system\) import" game/ > docs/refactor_public_api.txt
   ```
   Закоммитить как baseline. На каждом этапе сверяться: ничего не должно пропасть из этого списка (только переехать с shim).

**Гейт Фазы 0:** оба теста зелёные, baseline-сейв в репозитории, `docs/refactor_public_api.txt` закоммичен.

---

## 6. Этапы

Каждый этап ниже — самостоятельный PR. Внутри этапа разрешено 2–4 коммита. Порядок этапов обязателен (зависимости перечислены).

### Этап 1. `events.py` → split (зависимостей нет)

**Целевой объём:** 1316 → ~120 строк.

**Действия:**

1. Создать `game/random_events.py`. Перенести классы:
   - `EventType` (Enum)
   - `RandomEvent`
   - `EventResult`
   - `RandomEventSystem` (стр. ~168–1187 в исходном `events.py`)
2. Перенести `KillstreakSystem` (~1188–1256) в **новый** `game/killstreak.py` (не в `combat.py` — он и так перегружен).
3. Перенести `TimeOfDayBonuses` (~1257–1308) в `game/game_time.py` (если нет — создать). Сюда же позже переедет `get_time_of_day_tint` из `world_renderer.py`, но на этом этапе — только `TimeOfDayBonuses`.
4. `create_game_systems()` (внизу файла) — перенести как приватный `_create_game_systems()` в `engine.py` (он там единственный потребитель; если не единственный — оставить в `game/systems.py`).
5. В `events.py` оставить только `WeatherType`, `WeatherSystem` и переименовать файл в `game/weather.py`.
6. В исходном `events.py` оставить **shim** с re-export всех перемещённых имён (см. секцию 3, пункт 2).
7. Обновить импорты в коде:
   ```bash
   grep -rn "from game.events import\|from game import events" game/ main.py
   ```
   Заменить на прямые импорты из новых модулей. Shim остаётся как страховка до следующего PR.

**Риски:** низкие. Эти системы слабо связаны.

**Приёмка:** smoke-тест зелёный; в `events.py` (shim) ≤ 30 строк; новый `weather.py` существует.

---

### Этап 2. `inventory.py` → split (зависимостей нет, но идёт после Этапа 1 ради порядка)

**Целевой объём:** 2719 → ~700 строк в `inventory.py`.

**Действия:**

1. Создать `game/loot_system.py`. Перенести **целиком** класс `ItemGenerator` (стр. ~1462–2681 в `inventory.py`). Это самая жирная операция — **~1200 строк**.
2. Создать/обновить `game/item_registry.py`. Перенести туда утилиты:
   - `get_random_loot_from_location()` (~2682)
   - `get_predefined_item()` (~2697)
   - `get_item_by_id()` (~2713)
3. Перенести в `item_registry.py` (или в новый `game/items/types.py`) енумы:
   - `ItemQuality`, `ArmorType`, `WeaponType`, `EquipmentSlot` (стр. ~9–85)
4. **Делегирование специальных `use()`:**
   - `RecipeItem.use()` (~287–330) → логика добавления рецепта внутрь `crafting_system.py::CraftingSystem.learn_recipe(player, recipe)`. У `RecipeItem.use()` оставить **только вызов делегата**.
   - `SkillBookItem.use()` (~192–286) → логику изучения скилла перенести в `systems/skills/base.py::SkillManager.learn_from_book(book)`. У `SkillBookItem.use()` — тонкий делегат.
5. В `inventory.py` остаются: `Item`, `ResourceItem`, `PotionItem`, `EquipmentItem` и его подклассы (`WeaponItem`, `ArmorItem`, `JewelryItem`, `ArtifactItem`, `BeltItem`, `TalismanItem`, `BackpackItem`), и контейнер `Inventory`.
6. Shim в `inventory.py`:
   ```python
   from game.loot_system import ItemGenerator  # noqa: F401
   from game.item_registry import (  # noqa: F401
       ItemQuality, ArmorType, WeaponType, EquipmentSlot,
       get_random_loot_from_location, get_predefined_item, get_item_by_id,
   )
   ```
7. Заменить импорты в потребителях. Команды:
   ```bash
   grep -rn "from game.inventory import ItemGenerator\|from game.inventory import .*ItemQuality" game/
   ```

**Риски:** средние. `ItemGenerator` импортируется из многих мест.

**Приёмка:** smoke-тест + baseline-сейв зелёные; `inventory.py` ≤ 800 строк; `loot_system.py` содержит весь генератор.

---

### Этап 3. `constants.py` → split (зависимостей нет)

**Целевой объём:** 722 → ~400 строк в `constants.py`.

**Действия:**

1. Создать `game/config/runtime.py`.
2. Перенести туда:
   - `_init_dynamic_constants()` (~375)
   - `init_constants()` (~716)
   - все вызовы `config_loader`/файлового IO.
3. В `constants.py` оставить **только литералы** (BIOME_*, LOCATION_*, NPC_TYPE_*, и т.д.). Никаких `global ... =` и чтения файлов.
4. Точка вызова: тот, кто сейчас зовёт `init_constants()` (вероятно `main.py` или `engine.py`), теперь зовёт `from game.config.runtime import init_constants; init_constants()`. Shim в `constants.py`:
   ```python
   from game.config.runtime import init_constants, _init_dynamic_constants  # noqa: F401
   ```

**Риски:** низкие, но `constants` импортируется отовсюду. **Все имена** должны остаться доступными через `game.constants` (re-export динамических — через shim).

**Приёмка:** smoke-тест зелёный; в `constants.py` нет вызовов `config_loader` / `open()` / файлового IO.

---

### Этап 4. `character.py` → выделение боя (зависит от Этапа 2)

**Целевой объём:** 716 → ~350 строк.

**Действия:**

1. Создать `game/combat/character_combat.py` (если папки `combat/` нет — создать с `__init__.py`).
2. Перенести как **свободные функции**:
   - `attack(attacker, target, skip_range_check=False)`
   - `can_attack(attacker, target)`
   - `calculate_dodge_chance(character)`
   - `calculate_crit_chance(character)`
   - `_diminishing_returns(stat, base_per_point, bonus)` (бывший `_calculate_chance_with_diminishing_returns`)
   - `take_damage(character, damage)` — **опционально**: можно оставить методом, потому что мутирует hp.
3. У `Character` оставить **делегаты** на эти функции (см. секцию 3, пункт 5). Удаление делегатов — в следующем PR.
4. **`get_total_damage` / `get_total_defense` / `get_magic_defense`** (~594–672) — перенести в `game/equipment/bonuses.py` как `calculate_equipment_bonuses(character)` (или функции по типу). У `Character` — делегаты.
5. **Разрешить циклический импорт** `character.py ↔ entities/player.py`. Сейчас в конце `character.py` отложенный импорт Player — это симптом. После выноса боя зависимость должна исчезнуть. Если осталась — перенести Player-специфичный код, который тянет назад к Character, в `entities/player.py`.

**Риски:** средние. `Character` — центральная модель.

**Приёмка:** smoke-тест + baseline-сейв зелёные; `Character` ≤ 400 строк; нет формул боя внутри класса (только делегаты); импорт `Player` — на верху файла.

---

### Этап 5. `save_system.py` → делегирование сериализации (зависит от Этапов 2, 4)

**Целевой объём:** 550 → ~200 строк.

**Действия:**

1. Внедрить методы `to_dict()` / `from_dict(cls, data)` в доменные классы. Для каждого пункта ниже: код берётся из `save_system.py`, переносится 1:1 в метод соответствующего класса, в `save_system.py` остаётся только вызов.
   - `Item` и подклассы ← `_serialize_item` (26), `_deserialize_item` (78).
   - `Inventory` ← `_serialize_inventory` (301).
   - `Player`/`Character` ← `_serialize_player` (255).
   - `GameMap` ← `_serialize_map` (327).
   - `FogOfWar` ← `_serialize_fog` (436).
   - `AchievementManager` ← `_serialize_achievement_manager` (450).
   - `DungeonManager` ← `_serialize_dungeon_cleared_state` (456).
   - `NPC` (база) и подклассы ← `_serialize_npcs` (351). Общее — в `NPC.to_dict()`, подклассовое — в подклассах.
2. В `save_system.py` остаются только публичные `save_game(game, name)` и `load_game(name)`, плюс `_ensure_save_dir`, `get_save_list`, `delete_save`.
3. **Совместимость JSON-формата строго 1:1.** Никаких изменений ключей, порядка, типов. Тест `tests/test_save_compat.py` (Фаза 0) проверяет это на baseline-сейве.
4. Если хочется добавить версию формата (`"_version": 1`) — **отдельный PR после этого этапа**, не сейчас.

**Риски:** высокие (ломает сейвы у пользователей). Митигация — baseline-snapshot.

**Приёмка:** smoke-тест + baseline-сейв зелёные; `save_system.py` ≤ 250 строк; **ни один тест baseline-сейва не упал**.

---

### Этап 6. `respawn_manager.py` → удаление чужого (зависит от Этапа 5)

**Целевой объём:** 639 → ~250 строк.

**Действия:**

1. `_remove_dead_npc_from_manager()` (133) → перенести как метод `NPCManager.remove(npc)`. В RespawnManager — `npc_manager.remove(npc)`.
2. `_find_mine_by_coords()` (116) → перенести в `dungeon_manager.py::DungeonManager.find_mine_at(x, y)` (или в `map.py`, в зависимости от того, где хранятся шахты).
3. `_extract_name_base()` (169) и `_get_level_range()` (185) → это, по сути, восстановление данных NPC. После Этапа 5 они становятся частью `NPC.from_dict()`. Удалить из respawn.
4. `_create_patrol_route()` (599) — это **дубль** одноимённого метода в `npc_spawner.py`. Создать `game/npc/ai/patrol.py` с функцией `build_patrol_route(center_x, center_y, radius=5)`. В обоих местах вызывать её. **Удаление дубля в `npc_spawner.py` — в Этапе 7**, чтобы не смешивать.
5. После — RespawnManager остаётся с реальной логикой: очередь, таймеры, вызовы фабрик.

**Приёмка:** smoke-тест зелёный; в `respawn_manager.py` нет (де)сериализации, поиска шахт, локальной копии patrol_route.

---

### Этап 7. `npc_spawner.py` → фабрики на NPC-классы (зависит от Этапа 6)

**Целевой объём:** 1022 → ~500 строк. **Разбить на 2 PR.**

**PR 7a — мелкое:**

1. Удалить дубль `_create_patrol_route()` (778) — после Этапа 6 он уже в `game/npc/ai/patrol.py`. Заменить вызовы.
2. `give_starting_items()` — перенести в `player_init.py` (имя файла уже намекает на дом).

**PR 7b — крупное (фабрики):**

3. Превратить per-type `spawn_*` методы в classmethod'ы NPC-классов:
   - `_create_guard_by_type` (209) → `Guard.create(guard_type, location_name, x, y, level, ...)`.
   - `spawn_magic_merchant` / `spawn_warrior_merchant` / `spawn_shadow_merchant` (274–377) → `Merchant.create_magic(...)`, `Merchant.create_warrior(...)`, `Merchant.create_shadow(...)`.
   - Аналогично — для `spawn_bandits` (378), `spawn_miners` (452), `spawn_undead` (562), `spawn_alchemists` (636), `spawn_necromancers` (671), `spawn_animals` (856): **только сама конструкция NPC** уходит в classmethod, оркестрация (сколько, где) остаётся в `NPCSpawner`.
4. `NPCSpawner` после рефакторинга — **диспетчер размещения**: «решить, кого и где» → `Guard.create(...)`, `Merchant.create_magic(...)`, и т.д.

**Приёмка:** smoke-тест + baseline-сейв зелёные; `npc_spawner.py` ≤ 600 строк; нет дублей, нет глубокого конструирования.

---

### Этап 8. `world_renderer.py` → выделение минимапа и NPC-рендера (без зависимостей, можно параллельно с 4–7)

**Целевой объём:** 1033 → ~400 строк. **Разбить на 3 PR.**

**PR 8a — минимап:**

1. Создать `game/ui/minimap.py` с классом `MinimapRenderer(game)`. Перенести методы `render_minimap` (915), `_rebuild_minimap_cache` (990), `invalidate_minimap` (1031).
2. В `WorldRenderer` оставить тонкий делегат `render_minimap()` (опционально) или сразу заменить вызовы у клиентов.

**PR 8b — NPC-рендер:**

3. Перенести `_render_<тип>` (7 методов: guards, merchants, bandits, miners, undead, alchemists, necromancers, animals) как **метод `render(surface, camera_x, camera_y)` у соответствующего NPC-класса**.
4. `_render_single_npc` (244) и `_get_npc_color` (307–427, **120 строк** — словарь цветов) → `_get_npc_color` становится property `npc.color` или методом `npc.get_render_color()`. Маппинг разносится по NPC-классам (каждый знает свой цвет).
5. `_render_all_npcs` (209) превращается в простой цикл `for npc in visible: npc.render(surface, camera_x, camera_y)`.

**PR 8c — освещение:**

6. `get_time_of_day_tint` (32) и `apply_time_of_day_tint` (64) — перенести в `game/game_time.py` или новый `game/world/lighting.py`.

**Приёмка:** smoke-тест зелёный; `world_renderer.py` ≤ 500 строк; добавление нового типа NPC не требует правки `world_renderer.py`.

---

### Этап 9. `engine.py` → разгрузка цикла (зависит от Этапов 1, 5, 8)

**Целевой объём:** 1263 → ~600 строк. **Разбить на 4–5 PR.**

**PR 9a — UI-инициализация:**

1. Создать `game/ui/factory.py::create_all_windows(game)`, который возвращает namespace всех окон. Перенести туда блок инициализации UI из `Game.__init__` (~134–250).

**PR 9b — quest-действия:**

2. `_handle_quest_action(action)` (718) → перенести в `quest_manager.py::QuestManager.apply_action(action, context)`. В engine — делегат.

**PR 9c — interactions/combat/resources:**

3. `_handle_object_interaction()` (955) → `interactions/object_interaction.py`.
4. `_collect_resources()` (951) → `resource_system.py`.
5. `_start_combat()` (961) → `combat.py::start_combat(game, enemy, tactical=False)`.

**PR 9d — подписки на время:**

6. В `game_time.py` ввести подписки: `on_hour(callback)`, `on_day(callback)`.
7. Engine при инициализации регистрирует callbacks вместо того, чтобы дёргать ротации/события на каждом тике сам.

**PR 9e — удаление shim-properties:**

8. `@property guards/merchants/mages/bandits/miners/undead/alchemists/hunters/necromancers/animals` (320–368) — это совместимость с кодом, который думает «у game есть атрибут `guards`». После того как все клиенты переехали на `NPCManager`, удалить.

**Приёмка:** smoke-тест + baseline-сейв зелёные; в `engine.py` остались только init / run / handle_events диспетчер / render оркестрация; ни один метод длиннее 30 строк.

---

### Этап 10. `input_handler.py` → диспетчер по доменам (зависит от Этапов 2, 4, 9) ⚠️ ПОСЛЕДНИМ

**Целевой объём:** 1798 → ~600 строк. **Разбить на 6–7 PR — по одному на доменный модуль.**

**Структура целевая:**

```
game/input/
    __init__.py
    dispatcher.py        # тонкий InputHandler, маршрутизирует по активному окну
    inventory_input.py
    trade_input.py
    character_input.py   # включая skill_book
    quest_input.py
    menus_input.py       # settlement / infrastructure / inquiry
    combat_input.py      # combat_mode_choice + companion
    world_input.py       # handle_key_press, handle_interaction_choice
```

**Действия (по PR):**

- **PR 10a:** `input/inventory_input.py` ← `handle_inventory_input` (25), `handle_inventory_right_click` (114), `handle_inventory_alt_right_click` (184). Логику применения зелий/экипировки перенести в `PotionItem.apply(character)` / `EquipmentItem.equip_on(character)`.
- **PR 10b:** `input/trade_input.py` ← `handle_trade_input` (423), `handle_trade_left_click` (545), `handle_trade_right_click` (564).
- **PR 10c:** `input/character_input.py` ← `handle_character_input` (655), `handle_character_mouse_click` (678), `handle_skill_book_input` (694). `handle_learn_skill` (377) — логику перенести в `SkillManager.learn_skill(skill_id, cost)`.
- **PR 10d:** `input/quest_input.py` ← `handle_quest_input` (1296), `handle_unique_npc_quest` (365), `handle_turn_in_quest` (371).
- **PR 10e:** `input/menus_input.py` ← `handle_settlement_menu_input` (1557), `handle_infrastructure_menu_*` (1600, 1611), `handle_inquiry_menu_*` (1730, 1765).
- **PR 10f:** `input/combat_input.py` ← `handle_combat_mode_choice` (337), `handle_companion_input` (766), `handle_production_crafting_input` (832).
- **PR 10g:** `input/world_input.py` ← `handle_key_press` (856), `handle_interaction_choice` (230).
- **PR 10h:** `input/dispatcher.py` — тонкий `InputHandler`, смотрит на состояние UI и делегирует.

**Приёмка каждого PR:** smoke-тест зелёный; ни один обработчик длиннее 80 строк; внутри обработчиков нет формул урона/скиллов/цен — только маппинг событий в вызовы доменных API.

---

## 7. Сводный график

| # | Этап | Файл | До | После | Сложность | Зависит от |
|---|---|---|---:|---:|---|---|
| 0 | preparation | — | — | — | 🟢 | — |
| 1 | events split | events.py | 1316 | ~120 | 🟢 | — |
| 2 | inventory split | inventory.py | 2719 | ~700 | 🟡 | — |
| 3 | constants split | constants.py | 722 | ~400 | 🟢 | — |
| 4 | character bare | character.py | 716 | ~350 | 🟡 | 2 |
| 5 | save delegated | save_system.py | 550 | ~200 | 🟠 | 2, 4 |
| 6 | respawn slim | respawn_manager.py | 639 | ~250 | 🟢 | 5 |
| 7 | spawner slim | npc_spawner.py | 1022 | ~500 | 🟡 | 6 |
| 8 | world render | world_renderer.py | 1033 | ~400 | 🟡 | — |
| 9 | engine slim | engine.py | 1263 | ~600 | 🟠 | 1, 5, 8 |
| 10 | input dispatch | input_handler.py | 1798 | ~600 | 🟠 | 2, 4, 9 |

**Итого:** ~11 800 → ~4 100 строк в топ-10 (минус ~7 700 строк, которые переезжают по правильным домам, а не пропадают).

---

## 8. Прогресс

> Обновляй этот блок после мерджа каждого PR.

- [ ] Фаза 0 — подготовка
- [ ] Этап 1 — `events.py`
- [ ] Этап 2 — `inventory.py`
- [ ] Этап 3 — `constants.py`
- [ ] Этап 4 — `character.py`
- [ ] Этап 5 — `save_system.py`
- [ ] Этап 6 — `respawn_manager.py`
- [ ] Этап 7a — `npc_spawner.py` (patrol+items)
- [ ] Этап 7b — `npc_spawner.py` (factories)
- [ ] Этап 8a — `world_renderer.py` (minimap)
- [ ] Этап 8b — `world_renderer.py` (npc render)
- [ ] Этап 8c — `world_renderer.py` (lighting)
- [ ] Этап 9a — `engine.py` (UI init)
- [ ] Этап 9b — `engine.py` (quest actions)
- [ ] Этап 9c — `engine.py` (interactions/combat/resources)
- [ ] Этап 9d — `engine.py` (time subscriptions)
- [ ] Этап 9e — `engine.py` (remove shim properties)
- [ ] Этап 10a — `input/inventory_input.py`
- [ ] Этап 10b — `input/trade_input.py`
- [ ] Этап 10c — `input/character_input.py`
- [ ] Этап 10d — `input/quest_input.py`
- [ ] Этап 10e — `input/menus_input.py`
- [ ] Этап 10f — `input/combat_input.py`
- [ ] Этап 10g — `input/world_input.py`
- [ ] Этап 10h — `input/dispatcher.py`

---

## 9. Формат PR

**Заголовок:** `refactor(<этап>): <короткое описание>`

Примеры:
- `refactor(events): extract RandomEventSystem, KillstreakSystem, TimeOfDayBonuses`
- `refactor(inventory): move ItemGenerator to loot_system.py`
- `refactor(save): delegate Item.to_dict / from_dict`

**Тело PR:**

```markdown
## Этап
N (см. docs/REFACTOR_PLAN.md)

## Что перенесено
- <класс/функция> из <старый файл>:<строка> → <новый файл>
- ...

## Импорты
- Обновлено N мест: ...
- Shim в <старый файл>: да/нет

## Проверки
- [ ] smoke-тест зелёный
- [ ] baseline-сейв зелёный (для этапов 2, 4, 5, 6, 7)
- [ ] публичный API не сломан (сверено с docs/refactor_public_api.txt)

## Поведение
Игровых изменений нет.
```

---

## 10. Если что-то идёт не так

- **Smoke-тест упал** — откатить последний коммит, локально разобраться, причину описать в PR. Не «чинить вперёд».
- **Baseline-сейв не грузится** — это блокер, save-формат изменён. Восстановить и переделать.
- **Циклический импорт** — допустим отложенный импорт (внутри функции), но **только как временная мера**, с `TODO(refactor)` и issue.
- **Появилось желание заодно «починить» баг** — не сейчас. Открой отдельную issue, оставь комментарий, продолжи рефакторинг.
- **Файл получается странной формы** (например, `character.py` после Этапа 4 на 500 строк, а не 350) — это нормально, цель — снижение ответственности, не строк. Главное — нет чужой логики.
