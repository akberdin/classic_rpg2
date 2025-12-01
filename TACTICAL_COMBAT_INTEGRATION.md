# Инструкция по интеграции тактического боя

## Что сделано:

1. ✅ Создан конфиг `game/config/tactical_combat_config.json` с параметрами поля боя и радиусами
2. ✅ Добавлены радиусы действия (`tactical_range`) для всех типов оружия в `game/inventory.py`
3. ✅ Добавлен метод `get_tactical_range()` для класса `WeaponItem`
4. ✅ Добавлены радиусы действия для всех умений в `game/config/skills_config.json`
5. ✅ Создан модуль тактического боя `game/tactical_combat/`:
   - `logic.py` - логика боя, управление юнитами, AI врага
   - `renderer.py` - отрисовка поля боя, юнитов, UI
   - `ui_handler.py` - обработка ввода игрока
6. ✅ Создано окно выбора режима боя `game/ui/windows/combat_mode_selection.py`

## Что нужно доделать для полной интеграции:

### 1. В `game/engine.py`:

Добавить после строки 108 (после `self.nearby_npc = None`):
```python
self.combat_mode_menu_open = False
self.tactical_combat_system = None
self.tactical_combat_renderer = None
self.tactical_combat_handler = None
self.in_tactical_combat = False
```

Добавить после строки 140 (после `self.interaction_window = ...`):
```python
self.combat_mode_window = CombatModeSelectionWindow(self.screen, self.font, self.info_font, self.ui_scaler)
```

В метод `start_combat` добавить параметр `tactical=False`:
```python
def start_combat(self, enemy, tactical=False):
    if tactical:
        from game.tactical_combat import TacticalCombatSystem, TacticalCombatRenderer, TacticalCombatUIHandler

        self.tactical_combat_system = TacticalCombatSystem(
            self.player, enemy, self.screen, self.font, self.ui_scaler,
            self.game_map, self.respawn_manager, self.sprite_manager, self
        )
        self.tactical_combat_renderer = TacticalCombatRenderer(
            self.tactical_combat_system, self.screen, self.font, self.ui_scaler
        )
        self.tactical_combat_handler = TacticalCombatUIHandler(
            self.tactical_combat_system, self.tactical_combat_renderer
        )
        self.in_tactical_combat = True
        self.nearby_npc = None
    else:
        # Существующий код для быстрого боя
        ...
```

В метод `render` добавить (после блока с `self.in_combat`):
```python
if self.in_tactical_combat:
    self.tactical_combat_renderer.render()
    return

if self.combat_mode_menu_open and self.nearby_npc:
    self.combat_mode_window.render(self.nearby_npc.name)
```

В метод `_handle_events` добавить:
```python
if self.in_tactical_combat:
    result = self.tactical_combat_handler.handle_input(event)
    if result == "victory":
        self.in_tactical_combat = False
        self.tactical_combat_system = None
    elif result == "defeat":
        self.in_tactical_combat = False
        self.tactical_combat_system = None
        # Обработка поражения
    elif result == "fled":
        self.in_tactical_combat = False
        self.tactical_combat_system = None
    continue

if self.combat_mode_menu_open:
    self.input_handler.handle_combat_mode_choice(event)
    continue
```

### 2. В `game/input_handler.py`:

Заменить строки 176-182 и 181-182 (вызовы `self.ctx.start_combat`) на:
```python
# Открываем меню выбора режима боя
self.ctx.combat_mode_menu_open = True
self.ctx.interaction_menu_open = False
```

Добавить новый метод:
```python
def handle_combat_mode_choice(self, event):
    """Обработка выбора режима боя"""
    if event.type != pygame.KEYDOWN:
        return

    if event.key == pygame.K_1:
        # Быстрый бой
        self.ctx.start_combat(self.ctx.nearby_npc, tactical=False)
        self.ctx.combat_mode_menu_open = False
    elif event.key == pygame.K_2:
        # Тактический бой
        self.ctx.start_combat(self.ctx.nearby_npc, tactical=True)
        self.ctx.combat_mode_menu_open = False
    elif event.key == pygame.K_3 or event.key == pygame.K_ESCAPE:
        # Уйти
        self.ctx.combat_mode_menu_open = False
        self.ctx.nearby_npc = None
```

## Особенности тактического боя:

- Поле 20x10 клеток по 64 пикселя
- Игрок спавнится слева (x=2), враг справа (x=17)
- За ход можно: переместиться (3 клетки), использовать умение или зелье
- Действия:
  - `1` - Переместиться (кликнуть мышью на клетку)
  - `2` - Использовать умение (нажать 1-8 для слота умения)
  - `3` - Использовать зелье (пока не реализовано)
  - `4` - Пропустить ход
  - `ESC` - Попытка сбежать (50% шанс)
- Радиусы действия:
  - Ближний бой: 1 клетка
  - Копья: 2 клетки
  - Луки: 5-12 клеток (зависит от качества)
  - Магия: 0-10 клеток (зависит от заклинания)
