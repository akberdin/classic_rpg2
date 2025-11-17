# Система инвентаря и лута

## Обзор

Комплексная система управления предметами, экипировкой и генерацией лута для RPG игры.

## Основные возможности

### 1. Качество предметов (ItemQuality)

Система поддерживает 7 уровней качества:
- **Плохое** (POOR) - множитель 0.5
- **Обычное** (COMMON) - множитель 1.0
- **Необычное** (UNCOMMON) - множитель 1.5
- **Редкое** (RARE) - множитель 2.0
- **Эпическое** (EPIC) - множитель 3.0
- **Легендарное** (LEGENDARY) - множитель 5.0
- **Артефакт** (ARTIFACT) - множитель 10.0

Качество влияет на:
- Стоимость предмета
- Эффективность бонусов
- Редкость при генерации

### 2. Типы оружия (WeaponType)

- **Нож** - легкое, быстрое оружие (множитель урона 1.0, вес 0.5 кг)
- **Дубина** - простое оружие (множитель 1.2, вес 2.0 кг)
- **Меч** - сбалансированное оружие (множитель 1.5, вес 3.0 кг)
- **Копье** - оружие с хорошим уроном (множитель 1.4, вес 2.5 кг)
- **Лук** - дальнобойное оружие (множитель 1.3, вес 1.5 кг)
- **Посох** - магическое оружие (множитель 1.1, вес 2.0 кг)
- **Жезл** - легкое магическое оружие (множитель 1.0, вес 0.8 кг)

### 3. Типы доспехов (ArmorType)

- **Легкое** (LIGHT) - множитель защиты 1.0
- **Среднее** (MEDIUM) - множитель защиты 1.5
- **Тяжелое** (HEAVY) - множитель защиты 2.0

Вес доспехов зависит от типа и слота экипировки.

### 4. Слоты экипировки

- **WEAPON** - оружие (1 слот)
- **HEAD** - шлем (1 слот)
- **CHEST** - нагрудник/кираса (1 слот)
- **HANDS** - перчатки (1 слот)
- **FEET** - сапоги (1 слот)
- **RING_1-4** - кольца (4 слота)
- **AMULET** - амулет (1 слот)
- **BRACELET_1-2** - браслеты (2 слота)

**Всего: 12 слотов экипировки**

### 5. Типы предметов

#### ResourceItem
Ресурсы для крафта и продажи:
- Медная руда, Железная руда, Серебряная руда, Золотая руда, Мифриловая руда
- Древние монеты, Фрагменты артефактов, Магические кристаллы

#### PotionItem
Зелья с различными эффектами:
- Восстановление здоровья
- Восстановление маны
- Восстановление выносливости

Эффективность зависит от качества.

#### WeaponItem
Оружие с уроном и бонусами к характеристикам.

#### ArmorItem
Доспехи с защитой и бонусами к характеристикам.

#### JewelryItem
Украшения с бонусами к характеристикам (обычно лучшего качества).

#### ArtifactItem
Уникальные предметы с мощными бонусами и спецэффектами.

## Генератор предметов (ItemGenerator)

### Методы генерации

#### generate_weapon(level, quality=None)
```python
weapon = ItemGenerator.generate_weapon(level=10, quality=ItemQuality.EPIC)
```
Генерирует случайное оружие заданного уровня и качества.

#### generate_armor(level, slot=None, armor_type=None, quality=None)
```python
armor = ItemGenerator.generate_armor(
    level=10,
    slot=EquipmentSlot.CHEST,
    armor_type=ArmorType.HEAVY,
    quality=ItemQuality.RARE
)
```
Генерирует доспехи для конкретного слота.

#### generate_jewelry(level, slot=None, quality=None)
```python
ring = ItemGenerator.generate_jewelry(level=10, slot=EquipmentSlot.RING_1)
```
Генерирует украшение (обычно хорошего качества).

#### generate_loot_for_location(location_type, level)
```python
loot = ItemGenerator.generate_loot_for_location('ruins', level=5)
```
Генерирует лут для конкретного типа локации:
- **mine** - руды
- **ruins** - артефакты, экипировка, зелья
- **bandit_camp** - оружие, доспехи, золото

#### generate_npc_equipment(npc_type, level)
```python
equipment = ItemGenerator.generate_npc_equipment('guard', level=5)
```
Генерирует соответствующую экипировку для типа NPC:
- **guard** - полный комплект средних/тяжелых доспехов, меч/копье
- **bandit** - частичные легкие доспехи, простое оружие
- **merchant** - легкое оружие, украшения

## Система инвентаря (Inventory)

### Основные возможности

```python
inventory = Inventory(max_slots=20, max_weight=100.0)
```

#### Управление предметами
- `add_item(item, quantity)` - добавить предмет (с проверкой веса)
- `remove_item(item_name, quantity)` - удалить предмет
- `get_item(item_name)` - получить предмет
- `has_item(item_name, quantity)` - проверить наличие

#### Управление экипировкой
- `equip_item(item_name)` - экипировать предмет
- `unequip_item(slot)` - снять предмет
- `get_equipped_item(slot)` - получить экипированный предмет
- `get_total_stats_bonus()` - получить суммарные бонусы от экипировки

#### Свойства
- `current_weight` - текущий вес всех предметов
- `equipment` - словарь экипированных предметов

## Интеграция с персонажами

### Методы Character

#### get_base_stats()
Базовые характеристики без учета экипировки.

#### get_stats()
Характеристики с учетом бонусов от экипировки.

#### get_total_damage()
Урон с учетом экипированного оружия.

#### get_total_defense()
Защита с учетом экипированных доспехов.

### Пример использования

```python
from game.character import Player
from game.inventory import ItemGenerator, ItemQuality

# Создаем игрока
player = Player("Герой", 0, 0)

# Генерируем и экипируем оружие
weapon = ItemGenerator.generate_weapon(level=10, quality=ItemQuality.EPIC)
player.inventory.add_item(weapon, 1)
player.inventory.equip_item(weapon.name)

# Проверяем характеристики
print(f"Базовая сила: {player.get_base_stats()['strength']}")
print(f"Сила с бонусами: {player.get_stats()['strength']}")
print(f"Общий урон: {player.get_total_damage()}")
print(f"Общая защита: {player.get_total_defense()}")
```

## Боевая система

Урон и защита теперь учитывают экипировку:
- Урон = базовый урон персонажа + урон оружия + бонусы
- Итоговый урон = урон атакующего - защита цели (минимум 1)
- Критический удар удваивает урон
- Уворот полностью избегает урона

## NPC с автоматической экипировкой

При создании NPC автоматически генерируется и экипируется соответствующее снаряжение:

```python
from game.character import Guard, Bandit, Merchant

# Стражник с тяжелыми доспехами
guard = Guard("Стражник", 10, 10, level=5)

# Бандит с легким снаряжением
bandit = Bandit("Бандит", 20, 20, level=3)

# Торговец с украшениями
merchant = Merchant("Торговец", 30, 30, level=4)
```

## Масштабируемость системы

Система спроектирована для легкого расширения:

1. **Добавление новых типов оружия**: добавьте значение в `WeaponType`
2. **Добавление новых качеств**: добавьте значение в `ItemQuality`
3. **Новые типы предметов**: наследуйте от `EquipmentItem` или `Item`
4. **Новые генераторы**: добавьте методы в `ItemGenerator`

## Примеры кода

### Создание артефакта

```python
from game.inventory import ArtifactItem, EquipmentSlot

artifact = ArtifactItem(
    name="Кольцо Всевластия",
    slot=EquipmentSlot.RING_1,
    value=10000,
    stats_bonus={
        'strength': 10,
        'intelligence': 10,
        'luck': 10
    },
    special_effect="Даёт власть над всеми остальными кольцами"
)
```

### Полная экипировка персонажа

```python
from game.inventory import ItemGenerator, EquipmentSlot, ArmorType

# Оружие
weapon = ItemGenerator.generate_weapon(level=10)
player.inventory.add_item(weapon, 1)
player.inventory.equip_item(weapon.name)

# Полный комплект доспехов
for slot in [EquipmentSlot.HEAD, EquipmentSlot.CHEST,
             EquipmentSlot.HANDS, EquipmentSlot.FEET]:
    armor = ItemGenerator.generate_armor(level=10, slot=slot,
                                        armor_type=ArmorType.HEAVY)
    player.inventory.add_item(armor, 1)
    player.inventory.equip_item(armor.name)

# Украшения
for slot in [EquipmentSlot.AMULET, EquipmentSlot.RING_1,
             EquipmentSlot.BRACELET_1]:
    jewelry = ItemGenerator.generate_jewelry(level=10, slot=slot)
    player.inventory.add_item(jewelry, 1)
    player.inventory.equip_item(jewelry.name)
```

## Технические детали

- Все предметы имеют вес в килограммах
- Качество влияет на цену экспоненциально
- Бонусы от качества применяются с меньшим множителем, чем цена
- Защита вычитается из урона, но минимальный урон всегда 1
- NPC автоматически получают инвентарь при создании
- Экипировка автоматически применяет бонусы к характеристикам
