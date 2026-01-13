Добавим в игру систему регулярных и разовых обычных квестов, которые определяются параметрами конфига карты (game/maps/map1_config.json):
# Интеграция системы регулярных квестов

## Обзор системы

В редакторе карт реализована система конфигурации регулярных квестов. Квесты привязаны к локациям-источникам (города, деревни, академии воинов/магов, тайный лагерь) и сохраняются в файле конфигурации карты `map_config.json`.

## Структура данных квестов в конфиге

### Расположение квестов

Квесты хранятся внутри объекта локации в массиве `quests`:

```json
{
  "locations": [
    {
      "id": "loc_uuid_123",
      "type": "city",
      "name": "Столица",
      "x": 150,
      "y": 200,
      "quests": [
        { ... },
        { ... }
      ]
    }
  ]
}
```

### Полная структура квеста

```json
{
  "id": "quest_uuid_456",
  "quest_type": "gather_resource",
  "name": "Добыча древесины",
  "description": "Принесите древесину для строительства",
  "target_type": "wood",
  "target_item_id": "",
  "target_amount": 10,
  "time_limit": 100,
  "difficulty": 2,
  "min_player_attitude": 0,
  "target_location_id": "",
  "target_location_name": "",
  "target_floor": 0,
  "reward_gold": 150,
  "reward_item_id": "",
  "reward_item_amount": 1,
  "reward_exp": 75,
  "reward_reputation": 10,
  "completion_event_id": "",
  "is_repeatable": true,
  "cooldown": 50,
  "fail_attitude_penalty": 0,
  "scaling_factor": 1.1
}
```

---

## Типы квестов (quest_type)

### 1. `gather_resource` - Добыча ресурса

Игрок должен собрать определенное количество ресурса.

**Используемые поля:**
- `target_type` - тип ресурса
- `target_amount` - количество

**Возможные значения target_type:**

| Значение | Описание |
|----------|----------|
| `wood` | Древесина |
| `iron_ore` | Железная руда |
| `copper_ore` | Медная руда |
| `gold_ore` | Золотая руда |
| `silver_ore` | Серебряная руда |
| `mithril_ore` | Мифриловая руда |

**Пример:**
```json
{
  "quest_type": "gather_resource",
  "target_type": "iron_ore",
  "target_amount": 20,
  "name": "Железо для кузницы",
  "reward_gold": 200
}
```

---

### 2. `hunt_animals` - Охота на животных

Игрок должен убить определенное количество животных.

**Используемые поля:**
- `target_type` - тип животного
- `target_amount` - количество

**Возможные значения target_type:**

| Значение | Описание |
|----------|----------|
| `wolf` | Волк |
| `bear` | Медведь |
| `deer` | Олень |

**Пример:**
```json
{
  "quest_type": "hunt_animals",
  "target_type": "wolf",
  "target_amount": 5,
  "name": "Защита от волков",
  "reward_gold": 100,
  "reward_exp": 50
}
```

---

### 3. `deliver_message` - Доставка послания

Игрок должен доставить послание в указанную локацию.

**Используемые поля:**
- `target_location_id` - ID целевой локации
- `target_location_name` - название локации (для отображения)

**Допустимые типы целевых локаций:**
- `city` - город
- `capital` - столица
- `village` - деревня
- `warrior_academy` - академия воинов
- `magic_school` - школа магии
- `secret_camp` - тайный лагерь

**Пример:**
```json
{
  "quest_type": "deliver_message",
  "target_location_id": "loc_uuid_789",
  "target_location_name": "Деревня Oakwood",
  "name": "Срочное письмо",
  "time_limit": 50,
  "reward_gold": 75,
  "reward_reputation": 15
}
```

---

### 4. `clear_location` - Зачистка локации

Игрок должен зачистить подземелье (шахту или руины) - полностью или конкретный этаж.

**Используемые поля:**
- `target_location_id` - ID целевой локации (шахта/руины)
- `target_location_name` - название локации
- `target_floor` - целевой этаж:
  - `0` = зачистить ВСЕ этажи
  - `1-10` = зачистить конкретный этаж

**Допустимые типы целевых локаций:**
- `mine` - шахта
- `ruins` - руины

**Пример (все этажи):**
```json
{
  "quest_type": "clear_location",
  "target_location_id": "loc_mine_001",
  "target_location_name": "Заброшенная шахта",
  "target_floor": 0,
  "name": "Полная зачистка шахты",
  "difficulty": 4,
  "reward_gold": 500,
  "reward_exp": 300
}
```

**Пример (конкретный этаж):**
```json
{
  "quest_type": "clear_location",
  "target_location_id": "loc_ruins_002",
  "target_location_name": "Древние руины",
  "target_floor": 3,
  "name": "Зачистить 3-й этаж руин",
  "difficulty": 3,
  "reward_gold": 200
}
```

---

### 5. `collect_items` - Сбор предметов

Игрок должен собрать определенное количество предметов по ID.

**Используемые поля:**
- `target_item_id` - ID предмета из базы игры
- `target_amount` - количество предметов

**Пример:**
```json
{
  "quest_type": "collect_items",
  "target_item_id": "herb_healing",
  "target_amount": 10,
  "name": "Сбор лечебных трав",
  "description": "Целитель просит собрать лечебные травы",
  "reward_gold": 120,
  "reward_exp": 60
}
```

**Пример с наградой предметом:**
```json
{
  "quest_type": "collect_items",
  "target_item_id": "crystal_magic",
  "target_amount": 5,
  "name": "Магические кристаллы",
  "description": "Принесите магические кристаллы для исследований",
  "reward_gold": 0,
  "reward_item_id": "potion_mana_large",
  "reward_item_amount": 3,
  "reward_exp": 100
}
```

---

## Общие поля для всех типов квестов

| Поле | Тип | Описание | Значение по умолчанию |
|------|-----|----------|----------------------|
| `id` | string | Уникальный идентификатор (UUID) | автогенерация |
| `name` | string | Название квеста | "" |
| `description` | string | Описание квеста | "" |
| `target_item_id` | string | ID предмета для сбора (только для collect_items) | "" |
| `time_limit` | int | Лимит времени в ходах (0 = без лимита) | 0 |
| `difficulty` | int | Сложность (1-5) | 1 |
| `min_player_attitude` | int | Минимальное отношение игрока для получения квеста (-10 до 10) | 0 |
| `reward_gold` | int | Награда золотом | 100 |
| `reward_item_id` | string | ID предмета в качестве награды | "" |
| `reward_item_amount` | int | Количество предметов награды | 1 |
| `reward_exp` | int | Награда опытом | 50 |
| `reward_reputation` | int | Награда репутацией | 5 |
| `completion_event_id` | string | ID события для запуска после завершения квеста | "" |
| `is_repeatable` | bool | Повторяемый квест | true |
| `cooldown` | int | Перезарядка в ходах | 100 |
| `fail_attitude_penalty` | int | Штраф к отношению при провале квеста (0-20) | 0 |
| `scaling_factor` | float | Коэффициент масштабирования (1.0-2.0) | 1.1 |

## Уровни сложности

| Значение | Название |
|----------|----------|
| 1 | Легкий |
| 2 | Нормальный |
| 3 | Сложный |
| 4 | Очень сложный |
| 5 | Экстремальный |

## Локации-источники квестов

Квесты могут выдаваться только в этих типах локаций:
- `city` - город
- `capital` - столица
- `village` - деревня
- `warrior_academy` - академия воинов
- `magic_school` - школа магии
- `secret_camp` - тайный лагерь

---

## Требования и штрафы

### Минимальное отношение (min_player_attitude)

Поле `min_player_attitude` определяет минимальное значение `player_attitude` локации к игроку, необходимое для получения квеста.

| Параметр | Тип | Диапазон | По умолчанию |
|----------|-----|----------|--------------|
| `min_player_attitude` | int | -10 до 10 | 0 |

**Пример использования:**
```json
{
  "quest_type": "clear_location",
  "name": "Зачистка древних руин",
  "min_player_attitude": 3,
  "difficulty": 4
}
```
Этот квест будет доступен только если `player_attitude` локации к игроку >= 3.

### Штраф за провал (fail_attitude_penalty)

Поле `fail_attitude_penalty` определяет штраф к `player_attitude` при провале квеста (истечение времени или отказ).

| Параметр | Тип | Диапазон | По умолчанию |
|----------|-----|----------|--------------|
| `fail_attitude_penalty` | int | 0 до 20 | 0 |

**Пример:**
```json
{
  "quest_type": "deliver_message",
  "name": "Срочное донесение",
  "time_limit": 50,
  "fail_attitude_penalty": 5
}
```
Если игрок не успеет доставить послание вовремя, `player_attitude` локации уменьшится на 5.

---

## Событие завершения (completion_event_id)

Поле `completion_event_id` позволяет указать ID события, которое будет запущено после успешного завершения квеста. Это дополнение к стандартным наградам, а не замена.

| Параметр | Тип | По умолчанию |
|----------|-----|--------------|
| `completion_event_id` | string | "" |

**Примеры использования:**

```json
{
  "quest_type": "clear_location",
  "name": "Очистить заброшенную шахту",
  "completion_event_id": "unlock_mine_001",
  "reward_gold": 500
}
```
После завершения квеста игрок получит 500 золота И будет запущено событие `unlock_mine_001`.

```json
{
  "quest_type": "deliver_message",
  "name": "Тайное послание",
  "completion_event_id": "start_secret_storyline",
  "reward_reputation": 10
}
```
После доставки послания будет запущено событие начала секретной сюжетной линии.

### Интеграция в игре

```python
def complete_quest(self, quest: QuestInstance) -> dict:
    """Завершить квест и выдать награды."""
    rewards = {
        'gold': quest.reward_gold,
        'exp': quest.reward_exp,
        'reputation': quest.reward_reputation
    }

    # Выдать стандартные награды
    self.player.gold += rewards['gold']
    self.player.add_exp(rewards['exp'])

    # Выдать предмет если указан
    if quest.reward_item_id:
        self.player.inventory.add_item(quest.reward_item_id, quest.reward_item_amount)

    # Запустить событие завершения если указано
    if quest.completion_event_id:
        self.event_manager.trigger_event(quest.completion_event_id)

    return rewards
```

---

## Система масштабирования (scaling_factor)

### Назначение

Коэффициент `scaling_factor` позволяет автоматически масштабировать сложность и награды квестов в зависимости от уровня игрока.

### Параметры

| Параметр | Тип | Описание | Диапазон |
|----------|-----|----------|----------|
| `scaling_factor` | float | Коэффициент масштабирования | 1.0 - 2.0 (по умолчанию 1.1) |

### Формула масштабирования

```python
def calculate_scaled_value(base_value: int, scaling_factor: float,
                           player_level: int, difficulty: int) -> int:
    """
    Вычисляет масштабированное значение для квеста.

    Args:
        base_value: Базовое значение (target_amount, reward_gold и т.д.)
        scaling_factor: Коэффициент из конфига квеста (1.0 - 2.0)
        player_level: Текущий уровень игрока
        difficulty: Сложность квеста (1-5)

    Returns:
        Масштабированное значение (округленное до целого)
    """
    # Множитель сложности: 1.0, 1.2, 1.4, 1.6, 1.8
    difficulty_multiplier = 1.0 + (difficulty - 1) * 0.2

    # Множитель уровня (экспоненциальный рост)
    level_multiplier = scaling_factor ** (player_level - 1)

    # Финальное значение
    scaled = base_value * level_multiplier * difficulty_multiplier

    return max(1, round(scaled))
```

### Примеры расчета

**Квест с scaling_factor = 1.1, difficulty = 2:**

| Уровень игрока | base_value | Результат |
|----------------|------------|-----------|
| 1 | 10 | 10 × 1.0 × 1.2 = **12** |
| 5 | 10 | 10 × 1.46 × 1.2 = **18** |
| 10 | 10 | 10 × 2.36 × 1.2 = **28** |
| 20 | 10 | 10 × 6.12 × 1.2 = **73** |

**Квест с scaling_factor = 1.2, difficulty = 3:**

| Уровень игрока | base_value | Результат |
|----------------|------------|-----------|
| 1 | 100 | 100 × 1.0 × 1.4 = **140** |
| 5 | 100 | 100 × 2.07 × 1.4 = **290** |
| 10 | 100 | 100 × 5.16 × 1.4 = **722** |

### Что масштабируется

**Масштабируемые поля:**

| Поле | Описание |
|------|----------|
| `target_amount` | Количество ресурсов/животных/предметов |
| `reward_gold` | Награда золотом |
| `reward_exp` | Награда опытом |

**НЕ масштабируемые поля:**

| Поле | Причина |
|------|---------|
| `reward_reputation` | Репутация - фиксированная награда |
| `reward_item_id` | ID предмета - фиксированное значение |
| `reward_item_amount` | Количество предметов - фиксированное значение |
| `time_limit` | Время на выполнение не зависит от уровня |
| `cooldown` | Перезарядка фиксирована |
| `target_floor` | Этаж - фиксированное значение |
| `target_item_id` | ID предмета - фиксированное значение |

---

## Пример реализации в игре

### Класс экземпляра квеста

```python
class QuestInstance:
    """Экземпляр активного квеста у игрока."""

    def __init__(self, quest_config: dict, player_level: int):
        self.config = quest_config
        self.player_level = player_level
        self.quest_type = quest_config.get('quest_type', 'gather_resource')

        # Получаем параметры масштабирования
        scaling = quest_config.get('scaling_factor', 1.1)
        difficulty = quest_config.get('difficulty', 1)

        # Масштабируем цели (для gather/hunt/collect)
        base_amount = quest_config.get('target_amount', 10)
        self.target_amount = self._scale(base_amount, scaling, difficulty)
        self.current_amount = 0

        # Для collect_items - ID предмета
        self.target_item_id = quest_config.get('target_item_id', '')

        # Для deliver/clear - целевая локация
        self.target_location_id = quest_config.get('target_location_id', '')
        self.target_floor = quest_config.get('target_floor', 0)

        # Масштабируем награды
        self.reward_gold = self._scale(
            quest_config.get('reward_gold', 100), scaling, difficulty
        )
        self.reward_exp = self._scale(
            quest_config.get('reward_exp', 50), scaling, difficulty
        )
        # Репутация НЕ масштабируется
        self.reward_reputation = quest_config.get('reward_reputation', 5)

        # Награда предметом (НЕ масштабируется)
        self.reward_item_id = quest_config.get('reward_item_id', '')
        self.reward_item_amount = quest_config.get('reward_item_amount', 1)

        # Время и перезарядка
        self.time_limit = quest_config.get('time_limit', 0)
        self.time_remaining = self.time_limit
        self.cooldown = quest_config.get('cooldown', 100)

    def _scale(self, base: int, scaling: float, difficulty: int) -> int:
        """Применить масштабирование."""
        diff_mult = 1.0 + (difficulty - 1) * 0.2
        level_mult = scaling ** (self.player_level - 1)
        return max(1, round(base * level_mult * diff_mult))

    def update_progress(self, event_type: str, event_data: dict) -> bool:
        """
        Обновить прогресс квеста.

        Args:
            event_type: Тип события ('resource_gathered', 'animal_killed',
                        'item_collected', 'location_visited', 'floor_cleared')
            event_data: Данные события

        Returns:
            True если прогресс обновлен
        """
        if self.quest_type == 'gather_resource' and event_type == 'resource_gathered':
            if event_data.get('resource_type') == self.config.get('target_type'):
                self.current_amount += event_data.get('amount', 1)
                return True

        elif self.quest_type == 'hunt_animals' and event_type == 'animal_killed':
            if event_data.get('animal_type') == self.config.get('target_type'):
                self.current_amount += 1
                return True

        elif self.quest_type == 'collect_items' and event_type == 'item_collected':
            if event_data.get('item_id') == self.target_item_id:
                self.current_amount += event_data.get('amount', 1)
                return True

        elif self.quest_type == 'deliver_message' and event_type == 'location_visited':
            if event_data.get('location_id') == self.target_location_id:
                self.current_amount = 1
                return True

        elif self.quest_type == 'clear_location' and event_type == 'floor_cleared':
            if event_data.get('location_id') == self.target_location_id:
                if self.target_floor == 0:  # Все этажи
                    # Проверяем все ли этажи зачищены
                    pass
                elif event_data.get('floor') == self.target_floor:
                    self.current_amount = 1
                    return True

        return False

    def is_complete(self) -> bool:
        """Проверить выполнение квеста."""
        if self.quest_type in ('gather_resource', 'hunt_animals', 'collect_items'):
            return self.current_amount >= self.target_amount
        elif self.quest_type in ('deliver_message', 'clear_location'):
            return self.current_amount >= 1
        return False

    def is_expired(self) -> bool:
        """Проверить истек ли срок квеста."""
        if self.time_limit <= 0:
            return False
        return self.time_remaining <= 0

    def tick(self) -> None:
        """Обновить таймер (вызывается каждый ход)."""
        if self.time_limit > 0 and self.time_remaining > 0:
            self.time_remaining -= 1
```

### Менеджер квестов

```python
class QuestManager:
    """Менеджер квестов игрока."""

    def __init__(self, player):
        self.player = player
        self.active_quests: List[QuestInstance] = []
        self.completed_quests: Set[str] = set()  # ID выполненных неповторяемых квестов
        self.cooldowns: Dict[str, int] = {}  # ID квеста -> оставшийся cooldown

    def get_available_quests(self, location) -> List[dict]:
        """Получить доступные квесты в локации."""
        available = []
        for quest_config in location.quests:
            quest_id = quest_config.get('id')

            # Пропускаем неповторяемые выполненные квесты
            if not quest_config.get('is_repeatable', True):
                if quest_id in self.completed_quests:
                    continue

            # Пропускаем квесты на перезарядке
            if quest_id in self.cooldowns and self.cooldowns[quest_id] > 0:
                continue

            # Пропускаем уже взятые квесты
            if any(q.config.get('id') == quest_id for q in self.active_quests):
                continue

            available.append(quest_config)

        return available

    def accept_quest(self, quest_config: dict) -> QuestInstance:
        """Принять квест."""
        quest = QuestInstance(quest_config, self.player.level)
        self.active_quests.append(quest)
        return quest

    def complete_quest(self, quest: QuestInstance) -> dict:
        """Завершить квест и получить награды."""
        rewards = {
            'gold': quest.reward_gold,
            'exp': quest.reward_exp,
            'reputation': quest.reward_reputation,
            'item_id': quest.reward_item_id,
            'item_amount': quest.reward_item_amount
        }

        # Выдаем награды
        self.player.gold += rewards['gold']
        self.player.add_exp(rewards['exp'])
        self.player.add_reputation(rewards['reputation'])

        # Выдаем предмет если указан
        if rewards['item_id']:
            self.player.inventory.add_item(rewards['item_id'], rewards['item_amount'])

        # Обрабатываем повторяемость
        quest_id = quest.config.get('id')
        if quest.config.get('is_repeatable', True):
            self.cooldowns[quest_id] = quest.cooldown
        else:
            self.completed_quests.add(quest_id)

        # Удаляем из активных
        self.active_quests.remove(quest)

        return rewards

    def tick(self) -> None:
        """Обновить состояние (вызывается каждый ход)."""
        # Обновляем таймеры активных квестов
        for quest in self.active_quests:
            quest.tick()

        # Уменьшаем cooldown'ы
        for quest_id in list(self.cooldowns.keys()):
            self.cooldowns[quest_id] -= 1
            if self.cooldowns[quest_id] <= 0:
                del self.cooldowns[quest_id]
```

---

## Полный пример конфигурации локации с квестами

```json
{
  "id": "loc_city_001",
  "type": "city",
  "name": "Ривервуд",
  "x": 100,
  "y": 150,
  "guards": [],
  "quests": [
    {
      "id": "q1",
      "quest_type": "gather_resource",
      "name": "Древесина для стройки",
      "description": "Городу нужна древесина для ремонта стен",
      "target_type": "wood",
      "target_amount": 15,
      "time_limit": 0,
      "difficulty": 1,
      "min_player_attitude": 0,
      "target_location_id": "",
      "target_location_name": "",
      "target_floor": 0,
      "reward_gold": 100,
      "reward_exp": 50,
      "reward_reputation": 5,
      "completion_event_id": "",
      "is_repeatable": true,
      "cooldown": 100,
      "fail_attitude_penalty": 0,
      "scaling_factor": 1.1
    },
    {
      "id": "q2",
      "quest_type": "hunt_animals",
      "name": "Охота на волков",
      "description": "Волки угрожают караванам",
      "target_type": "wolf",
      "target_amount": 8,
      "time_limit": 200,
      "difficulty": 2,
      "target_location_id": "",
      "target_location_name": "",
      "target_floor": 0,
      "reward_gold": 150,
      "reward_exp": 100,
      "reward_reputation": 10,
      "is_repeatable": true,
      "cooldown": 150,
      "scaling_factor": 1.15
    },
    {
      "id": "q3",
      "quest_type": "deliver_message",
      "name": "Письмо в столицу",
      "description": "Срочное донесение королю",
      "target_type": "wood",
      "target_amount": 10,
      "time_limit": 50,
      "difficulty": 1,
      "target_location_id": "loc_capital_001",
      "target_location_name": "Королевская столица",
      "target_floor": 0,
      "reward_gold": 75,
      "reward_exp": 25,
      "reward_reputation": 20,
      "is_repeatable": true,
      "cooldown": 200,
      "scaling_factor": 1.05
    },
    {
      "id": "q4",
      "quest_type": "clear_location",
      "name": "Зачистка старой шахты",
      "description": "Монстры захватили шахту, верните её",
      "target_type": "wood",
      "target_item_id": "",
      "target_amount": 10,
      "time_limit": 0,
      "difficulty": 4,
      "min_player_attitude": 5,
      "target_location_id": "loc_mine_nearby",
      "target_location_name": "Старая шахта",
      "target_floor": 0,
      "reward_gold": 500,
      "reward_item_id": "",
      "reward_item_amount": 1,
      "reward_exp": 250,
      "reward_reputation": 25,
      "completion_event_id": "unlock_mine_resources",
      "is_repeatable": true,
      "cooldown": 500,
      "fail_attitude_penalty": 10,
      "scaling_factor": 1.2
    },
    {
      "id": "q5",
      "quest_type": "collect_items",
      "name": "Сбор редких трав",
      "description": "Целитель просит собрать редкие травы",
      "target_type": "",
      "target_item_id": "herb_healing",
      "target_amount": 10,
      "time_limit": 0,
      "difficulty": 2,
      "target_location_id": "",
      "target_location_name": "",
      "target_floor": 0,
      "reward_gold": 50,
      "reward_item_id": "potion_health",
      "reward_item_amount": 3,
      "reward_exp": 80,
      "reward_reputation": 8,
      "is_repeatable": true,
      "cooldown": 200,
      "scaling_factor": 1.1
    }
  ]
}
```

---

## Рекомендации по интеграции

### 1. Загрузка квестов

При загрузке карты парсить массив `quests` для каждой локации и создавать объекты квестов.

### 2. Отображение доступных квестов

При входе игрока в локацию-источник показывать список доступных квестов (учитывая cooldown и выполненные неповторяемые).

### 3. Принятие квеста

- Проверить, что квест не на перезарядке
- Создать экземпляр квеста с масштабированными значениями
- Если есть `time_limit` - запустить таймер

### 4. Отслеживание прогресса

- `gather_resource`: отслеживать сбор ресурсов указанного типа (`target_type`)
- `hunt_animals`: отслеживать убийства животных указанного типа (`target_type`)
- `collect_items`: отслеживать сбор предметов по ID (`target_item_id`)
- `deliver_message`: проверять посещение целевой локации
- `clear_location`: отслеживать зачистку этажей/всей локации

### 5. Завершение квеста

- Выдать масштабированные награды (gold, exp) и фиксированную репутацию
- Если указан `reward_item_id` - выдать предмет в количестве `reward_item_amount`
- Если `is_repeatable` = true, запустить cooldown
- Если `is_repeatable` = false, пометить квест как выполненный навсегда
