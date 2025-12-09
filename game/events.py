"""
Система событий, погоды и дополнительных игровых механик
"""
import random
from enum import Enum


class WeatherType(Enum):
    """Типы погоды"""
    CLEAR = ("clear", "Ясно", (255, 255, 200))
    CLOUDY = ("cloudy", "Облачно", (200, 200, 200))
    RAIN = ("rain", "Дождь", (150, 150, 180))
    STORM = ("storm", "Гроза", (100, 100, 130))
    FOG = ("fog", "Туман", (180, 180, 180))
    SNOW = ("snow", "Снег", (240, 240, 255))

    def __init__(self, value, display_name, tint_color):
        self._value_ = value
        self.display_name = display_name
        self.tint_color = tint_color


class WeatherSystem:
    """Система погоды"""

    def __init__(self):
        """Инициализация системы погоды"""
        self.current_weather = WeatherType.CLEAR
        self.weather_duration = 0  # Часов до смены погоды
        self.weather_intensity = 1.0  # Интенсивность (0.5 - 1.5)

    def update(self, hours_passed=1):
        """
        Обновить погоду

        Args:
            hours_passed: Количество прошедших часов

        Returns:
            str: Сообщение о смене погоды или None
        """
        self.weather_duration -= hours_passed

        if self.weather_duration <= 0:
            old_weather = self.current_weather
            self._change_weather()

            if old_weather != self.current_weather:
                return f"Погода изменилась: {self.current_weather.display_name}"

        return None

    def _change_weather(self):
        """Сменить погоду"""
        # Веса для разных типов погоды
        weather_weights = {
            WeatherType.CLEAR: 35,
            WeatherType.CLOUDY: 25,
            WeatherType.RAIN: 20,
            WeatherType.STORM: 5,
            WeatherType.FOG: 10,
            WeatherType.SNOW: 5
        }

        # Выбираем погоду с учётом весов
        total = sum(weather_weights.values())
        rand = random.randint(1, total)
        cumulative = 0

        for weather, weight in weather_weights.items():
            cumulative += weight
            if rand <= cumulative:
                self.current_weather = weather
                break

        # Устанавливаем длительность (4-12 часов)
        self.weather_duration = random.randint(4, 12)
        self.weather_intensity = random.uniform(0.7, 1.3)

    def get_combat_modifier(self):
        """
        Получить модификатор боя от погоды

        Returns:
            dict: Модификаторы {'accuracy': float, 'evasion': float, 'damage': float}
        """
        modifiers = {'accuracy': 1.0, 'evasion': 1.0, 'damage': 1.0}

        if self.current_weather == WeatherType.RAIN:
            modifiers['accuracy'] = 0.9
            modifiers['evasion'] = 1.1
        elif self.current_weather == WeatherType.STORM:
            modifiers['accuracy'] = 0.8
            modifiers['evasion'] = 1.15
            modifiers['damage'] = 1.1  # Молнии добавляют урон
        elif self.current_weather == WeatherType.FOG:
            modifiers['accuracy'] = 0.85
            modifiers['evasion'] = 1.2
        elif self.current_weather == WeatherType.SNOW:
            modifiers['accuracy'] = 0.95
            modifiers['evasion'] = 0.9  # Труднее двигаться

        return modifiers

    def get_resource_modifier(self):
        """
        Получить модификатор добычи ресурсов от погоды

        Returns:
            float: Множитель добычи
        """
        if self.current_weather == WeatherType.CLEAR:
            return 1.1  # Лучше видно ресурсы
        elif self.current_weather == WeatherType.RAIN:
            return 0.9  # Мокрые руки
        elif self.current_weather == WeatherType.STORM:
            return 0.7  # Опасно работать
        elif self.current_weather == WeatherType.FOG:
            return 0.85  # Плохо видно
        return 1.0


class EventType:
    """Типы событий"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class RandomEvent:
    """Случайное событие"""

    def __init__(self, event_id, name, description, effect_func, chance=0.1,
                 min_rank="Новичок", event_type=None, icon=None):
        """
        Инициализация события

        Args:
            event_id: ID события
            name: Название события
            description: Описание события
            effect_func: Функция эффекта (принимает player, game)
            chance: Шанс события (0-1)
            min_rank: Минимальный ранг для события
            event_type: Тип события (positive/neutral/negative)
            icon: Иконка события (символ)
        """
        self.event_id = event_id
        self.name = name
        self.description = description
        self.effect_func = effect_func
        self.chance = chance
        self.min_rank = min_rank
        self.event_type = event_type or EventType.NEUTRAL
        self.icon = icon or "?"


class EventResult:
    """Результат случайного события для отображения в UI"""

    def __init__(self, event, effects, player_rank):
        self.event = event
        self.effects = effects  # Список строк с эффектами
        self.player_rank = player_rank
        self.timestamp = None  # Можно добавить время события


class RandomEventSystem:
    """Система случайных событий"""

    # Порядок рангов для сравнения
    RANK_ORDER = {
        "Новичок": 1,
        "Обычный": 2,
        "Опытный": 3,
        "Эксперт": 4
    }

    def __init__(self):
        """Инициализация системы событий"""
        self.events = []
        self.last_event_result = None  # Последний результат для UI
        self.turns_since_last_event = 0  # Счетчик ходов с последнего события
        self.min_turns_between_events = 20  # Минимум 20 ходов между событиями
        self._setup_events()

    def _player_rank_sufficient(self, player, required_rank):
        """Проверить, достаточен ли ранг игрока"""
        player_rank = player.get_rank() if hasattr(player, 'get_rank') else "Новичок"
        return self.RANK_ORDER.get(player_rank, 1) >= self.RANK_ORDER.get(required_rank, 1)

    def _setup_events(self):
        """Настроить события"""
        # ======== СОБЫТИЯ ДЛЯ НОВИЧКОВ (1-10 уровень) ========

        # Положительные события для новичков
        self.events.append(RandomEvent(
            "find_gold", "Найден кошелёк",
            "Вы нашли кошелёк с золотом на дороге!",
            lambda p, g: self._find_gold(p, g),
            chance=0.016 / 3, min_rank="Новичок",
            event_type=EventType.POSITIVE, icon="$"
        ))

        self.events.append(RandomEvent(
            "blessing", "Благословение путника",
            "Странствующий монах благословил вас.",
            lambda p, g: self._blessing(p, g),
            chance=0.01 / 3, min_rank="Новичок",
            event_type=EventType.POSITIVE, icon="+"
        ))

        self.events.append(RandomEvent(
            "hidden_cache", "Тайник",
            "Вы обнаружили тайник под камнем!",
            lambda p, g: self._hidden_cache(p, g),
            chance=0.012 / 3, min_rank="Новичок",
            event_type=EventType.POSITIVE, icon="*"
        ))

        self.events.append(RandomEvent(
            "lucky_find", "Удачная находка",
            "Вы нашли ценный предмет среди листвы!",
            lambda p, g: self._lucky_find(p, g),
            chance=0.008 / 3, min_rank="Новичок",
            event_type=EventType.POSITIVE, icon="!"
        ))

        self.events.append(RandomEvent(
            "helpful_traveler", "Попутчик",
            "Дружелюбный путник поделился едой и восстановил ваши силы.",
            lambda p, g: self._helpful_traveler(p, g),
            chance=0.012 / 3, min_rank="Новичок",
            event_type=EventType.POSITIVE, icon="@"
        ))

        # Нейтральные события для новичков
        self.events.append(RandomEvent(
            "wandering_merchant", "Странствующий торговец",
            "Вы встретили странствующего торговца, который поделился советом.",
            lambda p, g: self._wandering_merchant(p, g),
            chance=0.014 / 3, min_rank="Новичок",
            event_type=EventType.NEUTRAL, icon="T"
        ))

        self.events.append(RandomEvent(
            "ancient_shrine", "Древний алтарь",
            "Вы нашли древний алтарь. Помолившись, вы чувствуете прилив сил.",
            lambda p, g: self._ancient_shrine(p, g),
            chance=0.01 / 3, min_rank="Новичок",
            event_type=EventType.NEUTRAL, icon="A"
        ))

        self.events.append(RandomEvent(
            "old_hermit", "Старый отшельник",
            "Старый отшельник рассказал вам древнюю легенду.",
            lambda p, g: self._old_hermit(p, g),
            chance=0.01 / 3, min_rank="Новичок",
            event_type=EventType.NEUTRAL, icon="H"
        ))

        # Отрицательные события для новичков
        self.events.append(RandomEvent(
            "trap", "Ловушка",
            "Вы попали в скрытую ловушку!",
            lambda p, g: self._trap(p, g),
            chance=0.012 / 3, min_rank="Новичок",
            event_type=EventType.NEGATIVE, icon="X"
        ))

        self.events.append(RandomEvent(
            "pickpocket", "Карманник",
            "Ловкий вор украл часть вашего золота!",
            lambda p, g: self._pickpocket(p, g),
            chance=0.01 / 3, min_rank="Новичок",
            event_type=EventType.NEGATIVE, icon="V"
        ))

        self.events.append(RandomEvent(
            "bad_food", "Испорченная еда",
            "Вы съели что-то несвежее и чувствуете слабость.",
            lambda p, g: self._bad_food(p, g),
            chance=0.008 / 3, min_rank="Новичок",
            event_type=EventType.NEGATIVE, icon="~"
        ))

        # ======== СОБЫТИЯ ДЛЯ ОБЫЧНЫХ (11-20 уровень) ========

        # Положительные события
        self.events.append(RandomEvent(
            "treasure_map", "Карта сокровищ",
            "Вы нашли старую карту, ведущую к кладу!",
            lambda p, g: self._treasure_map(p, g),
            chance=0.01 / 3, min_rank="Обычный",
            event_type=EventType.POSITIVE, icon="M"
        ))

        self.events.append(RandomEvent(
            "warrior_spirit", "Дух воина",
            "Дух древнего воина благословил ваше оружие.",
            lambda p, g: self._warrior_spirit(p, g),
            chance=0.008 / 3, min_rank="Обычный",
            event_type=EventType.POSITIVE, icon="W"
        ))

        self.events.append(RandomEvent(
            "rare_herb", "Редкая трава",
            "Вы обнаружили редкую целебную траву!",
            lambda p, g: self._rare_herb(p, g),
            chance=0.01 / 3, min_rank="Обычный",
            event_type=EventType.POSITIVE, icon="H"
        ))

        self.events.append(RandomEvent(
            "fairy_blessing", "Благословение феи",
            "Лесная фея одарила вас магической энергией.",
            lambda p, g: self._fairy_blessing(p, g),
            chance=0.008 / 3, min_rank="Обычный",
            event_type=EventType.POSITIVE, icon="F"
        ))

        # Нейтральные события
        self.events.append(RandomEvent(
            "mysterious_stranger", "Таинственный незнакомец",
            "Загадочный путник предложил вам сделку.",
            lambda p, g: self._mysterious_stranger(p, g),
            chance=0.01 / 3, min_rank="Обычный",
            event_type=EventType.NEUTRAL, icon="?"
        ))

        self.events.append(RandomEvent(
            "ancient_inscription", "Древняя надпись",
            "Вы расшифровали древнюю надпись на камне.",
            lambda p, g: self._ancient_inscription(p, g),
            chance=0.008 / 3, min_rank="Обычный",
            event_type=EventType.NEUTRAL, icon="I"
        ))

        # Отрицательные события
        self.events.append(RandomEvent(
            "cursed_item", "Проклятый предмет",
            "Вы подобрали проклятый предмет и потеряли часть сил.",
            lambda p, g: self._cursed_item(p, g),
            chance=0.008 / 3, min_rank="Обычный",
            event_type=EventType.NEGATIVE, icon="C"
        ))

        self.events.append(RandomEvent(
            "ambush", "Засада",
            "На вас напали из засады! Вы получили ранения, но сбежали.",
            lambda p, g: self._ambush(p, g),
            chance=0.01 / 3, min_rank="Обычный",
            event_type=EventType.NEGATIVE, icon="!"
        ))

        # ======== СОБЫТИЯ ДЛЯ ОПЫТНЫХ (21-30 уровень) ========

        # Положительные события
        self.events.append(RandomEvent(
            "ancient_artifact", "Древний артефакт",
            "Вы обнаружили осколок древнего артефакта!",
            lambda p, g: self._ancient_artifact(p, g),
            chance=0.008 / 3, min_rank="Опытный",
            event_type=EventType.POSITIVE, icon="A"
        ))

        self.events.append(RandomEvent(
            "dragon_scale", "Чешуя дракона",
            "Вы нашли чешуйку древнего дракона - редчайшая находка!",
            lambda p, g: self._dragon_scale(p, g),
            chance=0.006 / 3, min_rank="Опытный",
            event_type=EventType.POSITIVE, icon="D"
        ))

        self.events.append(RandomEvent(
            "elemental_blessing", "Благословение стихий",
            "Духи стихий даровали вам свою силу.",
            lambda p, g: self._elemental_blessing(p, g),
            chance=0.008 / 3, min_rank="Опытный",
            event_type=EventType.POSITIVE, icon="E"
        ))

        self.events.append(RandomEvent(
            "legendary_teacher", "Легендарный учитель",
            "Старый мастер согласился поделиться секретами боевых искусств.",
            lambda p, g: self._legendary_teacher(p, g),
            chance=0.006 / 3, min_rank="Опытный",
            event_type=EventType.POSITIVE, icon="L"
        ))

        # Нейтральные события
        self.events.append(RandomEvent(
            "time_rift", "Разлом времени",
            "Вы прошли через разлом во времени и увидели прошлое.",
            lambda p, g: self._time_rift(p, g),
            chance=0.006 / 3, min_rank="Опытный",
            event_type=EventType.NEUTRAL, icon="T"
        ))

        self.events.append(RandomEvent(
            "divine_vision", "Божественное видение",
            "Вам явилось видение из мира богов.",
            lambda p, g: self._divine_vision(p, g),
            chance=0.006 / 3, min_rank="Опытный",
            event_type=EventType.NEUTRAL, icon="V"
        ))

        # Отрицательные события
        self.events.append(RandomEvent(
            "dark_curse", "Тёмное проклятие",
            "Древнее проклятие ослабило вас.",
            lambda p, g: self._dark_curse(p, g),
            chance=0.008 / 3, min_rank="Опытный",
            event_type=EventType.NEGATIVE, icon="D"
        ))

        self.events.append(RandomEvent(
            "soul_drain", "Похищение души",
            "Призрак попытался похитить часть вашей души.",
            lambda p, g: self._soul_drain(p, g),
            chance=0.006 / 3, min_rank="Опытный",
            event_type=EventType.NEGATIVE, icon="S"
        ))

        # ======== СОБЫТИЯ ДЛЯ ЭКСПЕРТОВ (31-40 уровень) ========

        # Положительные события
        self.events.append(RandomEvent(
            "divine_intervention", "Божественное вмешательство",
            "Боги обратили на вас внимание и даровали великую силу!",
            lambda p, g: self._divine_intervention(p, g),
            chance=0.006 / 3, min_rank="Эксперт",
            event_type=EventType.POSITIVE, icon="G"
        ))

        self.events.append(RandomEvent(
            "legendary_treasure", "Легендарное сокровище",
            "Вы нашли легендарное сокровище древних королей!",
            lambda p, g: self._legendary_treasure(p, g),
            chance=0.004 / 3, min_rank="Эксперт",
            event_type=EventType.POSITIVE, icon="K"
        ))

        self.events.append(RandomEvent(
            "phoenix_feather", "Перо феникса",
            "Перо феникса упало прямо в ваши руки - невероятная удача!",
            lambda p, g: self._phoenix_feather(p, g),
            chance=0.004 / 3, min_rank="Эксперт",
            event_type=EventType.POSITIVE, icon="P"
        ))

        self.events.append(RandomEvent(
            "wisdom_of_ages", "Мудрость веков",
            "Древние духи поделились с вами знаниями прошлого.",
            lambda p, g: self._wisdom_of_ages(p, g),
            chance=0.006 / 3, min_rank="Эксперт",
            event_type=EventType.POSITIVE, icon="W"
        ))

        # Нейтральные события
        self.events.append(RandomEvent(
            "cosmic_alignment", "Космическое выравнивание",
            "Звёзды встали в особое положение, и вы чувствуете их влияние.",
            lambda p, g: self._cosmic_alignment(p, g),
            chance=0.006 / 3, min_rank="Эксперт",
            event_type=EventType.NEUTRAL, icon="*"
        ))

        self.events.append(RandomEvent(
            "ancient_prophecy", "Древнее пророчество",
            "Вы узнали о древнем пророчестве, касающемся вас.",
            lambda p, g: self._ancient_prophecy(p, g),
            chance=0.004 / 3, min_rank="Эксперт",
            event_type=EventType.NEUTRAL, icon="O"
        ))

        # Отрицательные события
        self.events.append(RandomEvent(
            "demonic_attention", "Внимание демона",
            "Могущественный демон обратил на вас внимание.",
            lambda p, g: self._demonic_attention(p, g),
            chance=0.006 / 3, min_rank="Эксперт",
            event_type=EventType.NEGATIVE, icon="B"
        ))

        self.events.append(RandomEvent(
            "temporal_paradox", "Временной парадокс",
            "Парадокс времени вызвал странные последствия.",
            lambda p, g: self._temporal_paradox(p, g),
            chance=0.004 / 3, min_rank="Эксперт",
            event_type=EventType.NEGATIVE, icon="Z"
        ))

    def check_for_event(self, player, game):
        """
        Проверить, произошло ли событие

        Args:
            player: Игрок
            game: Объект игры

        Returns:
            list: Список сообщений о событиях
        """
        messages = []
        player_rank = player.get_rank() if hasattr(player, 'get_rank') else "Новичок"

        # Увеличиваем счетчик ходов
        self.turns_since_last_event += 1

        # Проверяем минимальное время между событиями
        if self.turns_since_last_event < self.min_turns_between_events:
            return messages  # Слишком рано для нового события

        # Фильтруем события по рангу игрока
        available_events = [
            e for e in self.events
            if self._player_rank_sufficient(player, e.min_rank)
        ]

        # Перемешиваем для разнообразия
        random.shuffle(available_events)

        for event in available_events:
            if random.random() < event.chance:
                result = event.effect_func(player, game)
                if result:
                    messages.append(f"[{event.name}] {event.description}")
                    messages.extend(result)

                    # Сохраняем результат для UI
                    self.last_event_result = EventResult(event, result, player_rank)

                    # Сбрасываем счетчик ходов
                    self.turns_since_last_event = 0
                break  # Только одно событие за раз

        return messages

    def get_last_event(self):
        """Получить последнее событие для отображения в UI"""
        return self.last_event_result

    def clear_last_event(self):
        """Очистить последнее событие"""
        self.last_event_result = None

    def _find_gold(self, player, game):
        """Найти золото"""
        gold = random.randint(5, 20) * player.level
        player.inventory.add_gold(gold)
        return [f"  Получено {gold} золота"]

    def _blessing(self, player, game):
        """Благословение"""
        # Временное увеличение удачи (через восстановление здоровья/маны)
        effective_max_health = player.get_effective_max_health()
        effective_max_mana = player.get_effective_max_mana()
        heal = int(effective_max_health * 0.2)
        mana = int(effective_max_mana * 0.2)
        player.health = min(effective_max_health, player.health + heal)
        player.mana = min(effective_max_mana, player.mana + mana)
        return [f"  Восстановлено {heal} здоровья и {mana} маны"]

    def _hidden_cache(self, player, game):
        """Найти тайник"""
        gold = random.randint(10, 30) * player.level
        player.inventory.add_gold(gold)
        exp = random.randint(10, 25) * player.level
        player.add_experience(exp)
        return [f"  Получено {gold} золота и {exp} опыта"]

    def _lucky_find(self, player, game):
        """Удачная находка - получить случайный предмет"""
        from game.item_registry import get_item

        # Список возможных находок
        possible_items = [
            "health_potion", "mana_potion", "antidote",
            "copper_ore", "iron_ore", "wood"
        ]

        item_id = random.choice(possible_items)
        item = get_item(item_id)
        if item:
            player.inventory.add_item(item, 1)
            return [f"  Получено: {item.name}"]
        return []

    def _wandering_merchant(self, player, game):
        """Странствующий торговец"""
        # Даём бонус к следующей торговой сделке через опыт
        exp = random.randint(5, 15) * player.level
        player.add_experience(exp)
        return [f"  Получено {exp} опыта от совета"]

    def _ancient_shrine(self, player, game):
        """Древний алтарь"""
        # Полное восстановление
        player.health = player.get_effective_max_health()
        player.mana = player.get_effective_max_mana()
        player.stamina = player.get_effective_max_stamina()
        return ["  Полностью восстановлены здоровье, мана и выносливость"]

    def _trap(self, player, game):
        """Ловушка"""
        if player.godmode:
            return ["  Ловушка не причинила вам вреда (режим бессмертия)"]

        damage = random.randint(5, 15) + player.level
        player.health = max(1, player.health - damage)
        return [f"  Получено {damage} урона"]

    def _pickpocket(self, player, game):
        """Карманник"""
        if player.inventory.gold > 0:
            stolen = min(player.inventory.gold, random.randint(5, 20) * player.level)
            player.inventory.remove_gold(stolen)
            return [f"  Потеряно {stolen} золота"]
        return ["  Вор ничего не нашёл"]

    # === Новые события для новичков ===

    def _helpful_traveler(self, player, game):
        """Попутчик"""
        effective_max_health = player.get_effective_max_health()
        effective_max_stamina = player.get_effective_max_stamina()
        heal = int(effective_max_health * 0.3)
        stamina = int(effective_max_stamina * 0.5)
        player.health = min(effective_max_health, player.health + heal)
        player.stamina = min(effective_max_stamina, player.stamina + stamina)
        return [f"  Восстановлено {heal} здоровья и {stamina} выносливости"]

    def _old_hermit(self, player, game):
        """Старый отшельник"""
        exp = random.randint(10, 20) * player.level
        player.add_experience(exp)
        return [f"  Получено {exp} опыта от мудрости"]

    def _bad_food(self, player, game):
        """Испорченная еда"""
        if player.godmode:
            return ["  Отравление не подействовало (режим бессмертия)"]

        effective_max_health = player.get_effective_max_health()
        effective_max_stamina = player.get_effective_max_stamina()
        damage = int(effective_max_health * 0.1)
        stamina_loss = int(effective_max_stamina * 0.2)
        player.health = max(1, player.health - damage)
        player.stamina = max(0, player.stamina - stamina_loss)
        return [f"  Потеряно {damage} здоровья и {stamina_loss} выносливости"]

    # === События для обычных ===

    def _treasure_map(self, player, game):
        """Карта сокровищ"""
        gold = random.randint(30, 60) * player.level
        exp = random.randint(20, 40) * player.level
        player.inventory.add_gold(gold)
        player.add_experience(exp)
        return [f"  Получено {gold} золота и {exp} опыта"]

    def _warrior_spirit(self, player, game):
        """Дух воина"""
        # Временное усиление через опыт и восстановление
        exp = random.randint(15, 30) * player.level
        player.add_experience(exp)
        player.health = player.get_effective_max_health()
        return [f"  Получено {exp} опыта, здоровье полностью восстановлено"]

    def _rare_herb(self, player, game):
        """Редкая трава"""
        from game.item_registry import get_item

        # Даём несколько зелий
        potions = ["health_potion", "mana_potion"]
        results = []
        for potion_id in potions:
            item = get_item(potion_id)
            if item:
                quantity = random.randint(1, 3)
                player.inventory.add_item(item, quantity)
                results.append(f"  Получено: {item.name} x{quantity}")
        return results if results else ["  Ничего не найдено"]

    def _fairy_blessing(self, player, game):
        """Благословение феи"""
        effective_max_mana = player.get_effective_max_mana()
        mana = int(effective_max_mana * 0.5)
        exp = random.randint(15, 25) * player.level
        player.mana = min(effective_max_mana, player.mana + mana)
        player.add_experience(exp)
        return [f"  Восстановлено {mana} маны, получено {exp} опыта"]

    def _mysterious_stranger(self, player, game):
        """Таинственный незнакомец"""
        # Случайный эффект - золото или опыт
        if random.random() < 0.5:
            gold = random.randint(20, 50) * player.level
            player.inventory.add_gold(gold)
            return [f"  Незнакомец дал вам {gold} золота"]
        else:
            exp = random.randint(20, 40) * player.level
            player.add_experience(exp)
            return [f"  Незнакомец поделился знаниями: +{exp} опыта"]

    def _ancient_inscription(self, player, game):
        """Древняя надпись"""
        exp = random.randint(25, 45) * player.level
        player.add_experience(exp)
        return [f"  Расшифровка дала {exp} опыта"]

    def _cursed_item(self, player, game):
        """Проклятый предмет"""
        if player.godmode:
            return ["  Проклятие не подействовало (режим бессмертия)"]

        effective_max_health = player.get_effective_max_health()
        effective_max_mana = player.get_effective_max_mana()
        damage = int(effective_max_health * 0.15)
        mana_loss = int(effective_max_mana * 0.2)
        player.health = max(1, player.health - damage)
        player.mana = max(0, player.mana - mana_loss)
        return [f"  Потеряно {damage} здоровья и {mana_loss} маны"]

    def _ambush(self, player, game):
        """Засада"""
        if player.godmode:
            return ["  Вы легко отбили атаку (режим бессмертия)"]

        damage = random.randint(10, 25) + player.level * 2
        gold_lost = min(player.inventory.gold, random.randint(10, 30) * player.level)
        player.health = max(1, player.health - damage)
        if gold_lost > 0:
            player.inventory.remove_gold(gold_lost)
        return [f"  Потеряно {damage} здоровья и {gold_lost} золота"]

    # === События для опытных ===

    def _ancient_artifact(self, player, game):
        """Древний артефакт"""
        from game.item_registry import get_item

        gold = random.randint(50, 100) * player.level
        exp = random.randint(40, 70) * player.level
        player.inventory.add_gold(gold)
        player.add_experience(exp)

        # Шанс на особый предмет
        item = get_item("artifact_fragment")
        if random.random() < 0.3 and item:
            player.inventory.add_item(item, 1)
            return [f"  Получено {gold} золота, {exp} опыта и {item.name}"]
        return [f"  Получено {gold} золота и {exp} опыта"]

    def _dragon_scale(self, player, game):
        """Чешуя дракона"""
        gold = random.randint(80, 150) * player.level
        exp = random.randint(50, 90) * player.level
        player.inventory.add_gold(gold)
        player.add_experience(exp)
        return [f"  Продана за {gold} золота, получено {exp} опыта"]

    def _elemental_blessing(self, player, game):
        """Благословение стихий"""
        # Полное восстановление + бонус
        player.health = player.get_effective_max_health()
        player.mana = player.get_effective_max_mana()
        player.stamina = player.get_effective_max_stamina()
        exp = random.randint(30, 50) * player.level
        player.add_experience(exp)
        return ["  Полное восстановление всех ресурсов", f"  Получено {exp} опыта"]

    def _legendary_teacher(self, player, game):
        """Легендарный учитель"""
        exp = random.randint(60, 100) * player.level
        player.add_experience(exp)
        return [f"  Получено {exp} опыта от тренировки"]

    def _time_rift(self, player, game):
        """Разлом времени"""
        exp = random.randint(40, 70) * player.level
        player.add_experience(exp)
        # Случайный эффект
        if random.random() < 0.5:
            effective_max_health = player.get_effective_max_health()
            heal = int(effective_max_health * 0.3)
            player.health = min(effective_max_health, player.health + heal)
            return [f"  Получено {exp} опыта, восстановлено {heal} здоровья"]
        else:
            gold = random.randint(30, 60) * player.level
            player.inventory.add_gold(gold)
            return [f"  Получено {exp} опыта и {gold} золота из прошлого"]

    def _divine_vision(self, player, game):
        """Божественное видение"""
        exp = random.randint(50, 80) * player.level
        player.add_experience(exp)
        player.mana = player.get_effective_max_mana()
        return [f"  Получено {exp} опыта, мана полностью восстановлена"]

    def _dark_curse(self, player, game):
        """Тёмное проклятие"""
        if player.godmode:
            return ["  Проклятие рассеялось (режим бессмертия)"]

        effective_max_health = player.get_effective_max_health()
        effective_max_mana = player.get_effective_max_mana()
        effective_max_stamina = player.get_effective_max_stamina()
        damage = int(effective_max_health * 0.2)
        mana_loss = int(effective_max_mana * 0.3)
        stamina_loss = int(effective_max_stamina * 0.3)
        player.health = max(1, player.health - damage)
        player.mana = max(0, player.mana - mana_loss)
        player.stamina = max(0, player.stamina - stamina_loss)
        return [f"  Потеряно {damage} здоровья, {mana_loss} маны, {stamina_loss} выносливости"]

    def _soul_drain(self, player, game):
        """Похищение души"""
        if player.godmode:
            return ["  Призрак отступил (режим бессмертия)"]

        effective_max_health = player.get_effective_max_health()
        damage = int(effective_max_health * 0.25)
        exp_loss = random.randint(10, 30) * player.level
        player.health = max(1, player.health - damage)
        # Опыт не может стать отрицательным
        player.experience = max(0, player.experience - exp_loss)
        return [f"  Потеряно {damage} здоровья и {exp_loss} опыта"]

    # === События для экспертов ===

    def _divine_intervention(self, player, game):
        """Божественное вмешательство"""
        # Мощный положительный эффект
        player.health = player.get_effective_max_health()
        player.mana = player.get_effective_max_mana()
        player.stamina = player.get_effective_max_stamina()
        exp = random.randint(100, 150) * player.level
        gold = random.randint(100, 200) * player.level
        player.add_experience(exp)
        player.inventory.add_gold(gold)
        return [
            "  Полное восстановление всех ресурсов",
            f"  Получено {exp} опыта и {gold} золота"
        ]

    def _legendary_treasure(self, player, game):
        """Легендарное сокровище"""
        gold = random.randint(200, 400) * player.level
        exp = random.randint(80, 120) * player.level
        player.inventory.add_gold(gold)
        player.add_experience(exp)
        return [f"  Получено {gold} золота и {exp} опыта"]

    def _phoenix_feather(self, player, game):
        """Перо феникса"""
        # Полное восстановление + большой опыт
        player.health = player.get_effective_max_health()
        player.mana = player.get_effective_max_mana()
        player.stamina = player.get_effective_max_stamina()
        exp = random.randint(120, 180) * player.level
        player.add_experience(exp)
        return [
            "  Полное восстановление всех ресурсов",
            f"  Получено {exp} опыта"
        ]

    def _wisdom_of_ages(self, player, game):
        """Мудрость веков"""
        exp = random.randint(150, 250) * player.level
        player.add_experience(exp)
        return [f"  Получено {exp} опыта"]

    def _cosmic_alignment(self, player, game):
        """Космическое выравнивание"""
        # Случайный мощный эффект
        effect = random.choice(['health', 'mana', 'gold', 'exp'])

        if effect == 'health':
            player.health = player.get_effective_max_health()
            return ["  Здоровье полностью восстановлено силой звёзд"]
        elif effect == 'mana':
            player.mana = player.get_effective_max_mana()
            return ["  Мана полностью восстановлена силой звёзд"]
        elif effect == 'gold':
            gold = random.randint(100, 200) * player.level
            player.inventory.add_gold(gold)
            return [f"  Звёзды даровали {gold} золота"]
        else:
            exp = random.randint(80, 140) * player.level
            player.add_experience(exp)
            return [f"  Звёзды даровали {exp} опыта"]

    def _ancient_prophecy(self, player, game):
        """Древнее пророчество"""
        exp = random.randint(100, 160) * player.level
        player.add_experience(exp)
        return [f"  Знание пророчества дало {exp} опыта"]

    def _demonic_attention(self, player, game):
        """Внимание демона"""
        if player.godmode:
            return ["  Демон отступил перед вашей силой (режим бессмертия)"]

        effective_max_health = player.get_effective_max_health()
        damage = int(effective_max_health * 0.3)
        gold_lost = min(player.inventory.gold, random.randint(50, 100) * player.level)
        player.health = max(1, player.health - damage)
        if gold_lost > 0:
            player.inventory.remove_gold(gold_lost)
        return [f"  Потеряно {damage} здоровья и {gold_lost} золота"]

    def _temporal_paradox(self, player, game):
        """Временной парадокс"""
        if player.godmode:
            return ["  Парадокс вас не затронул (режим бессмертия)"]

        # Случайная потеря
        effect = random.choice(['health', 'mana', 'exp', 'gold'])

        if effect == 'health':
            effective_max_health = player.get_effective_max_health()
            damage = int(effective_max_health * 0.2)
            player.health = max(1, player.health - damage)
            return [f"  Потеряно {damage} здоровья из-за парадокса"]
        elif effect == 'mana':
            effective_max_mana = player.get_effective_max_mana()
            mana_loss = int(effective_max_mana * 0.4)
            player.mana = max(0, player.mana - mana_loss)
            return [f"  Потеряно {mana_loss} маны из-за парадокса"]
        elif effect == 'exp':
            exp_loss = random.randint(30, 60) * player.level
            player.experience = max(0, player.experience - exp_loss)
            return [f"  Потеряно {exp_loss} опыта из-за парадокса"]
        else:
            gold_lost = min(player.inventory.gold, random.randint(40, 80) * player.level)
            if gold_lost > 0:
                player.inventory.remove_gold(gold_lost)
            return [f"  Потеряно {gold_lost} золота из-за парадокса"]


class KillstreakSystem:
    """Система серий убийств"""

    def __init__(self):
        """Инициализация системы серий"""
        self.current_streak = 0
        self.best_streak = 0
        self.streak_timer = 0  # Таймер до сброса серии

    def register_kill(self):
        """
        Зарегистрировать убийство

        Returns:
            dict: Информация о бонусе {'streak': int, 'multiplier': float, 'message': str}
        """
        self.current_streak += 1
        self.streak_timer = 5  # 5 часов до сброса

        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak

        multiplier = self._get_multiplier()
        message = self._get_streak_message()

        return {
            'streak': self.current_streak,
            'multiplier': multiplier,
            'message': message
        }

    def update(self, hours_passed=1):
        """
        Обновить таймер серии

        Args:
            hours_passed: Прошедшие часы
        """
        if self.current_streak > 0:
            self.streak_timer -= hours_passed
            if self.streak_timer <= 0:
                self.current_streak = 0
                self.streak_timer = 0

    def _get_multiplier(self):
        """Получить множитель награды от серии"""
        if self.current_streak >= 10:
            return 2.0
        elif self.current_streak >= 7:
            return 1.75
        elif self.current_streak >= 5:
            return 1.5
        elif self.current_streak >= 3:
            return 1.25
        return 1.0

    def _get_streak_message(self):
        """Получить сообщение о серии"""
        if self.current_streak >= 10:
            return f"ЛЕГЕНДАРНАЯ СЕРИЯ x{self.current_streak}! (x2.0 награда)"
        elif self.current_streak >= 7:
            return f"Невероятная серия x{self.current_streak}! (x1.75 награда)"
        elif self.current_streak >= 5:
            return f"Отличная серия x{self.current_streak}! (x1.5 награда)"
        elif self.current_streak >= 3:
            return f"Серия убийств x{self.current_streak}! (x1.25 награда)"
        return ""


class TimeOfDayBonuses:
    """Бонусы времени суток"""

    @staticmethod
    def get_bonuses(hour):
        """
        Получить бонусы для текущего времени суток

        Args:
            hour: Текущий час (0-23)

        Returns:
            dict: Бонусы {'combat': float, 'stealth': float, 'magic': float,
                        'gathering': float, 'description': str}
        """
        bonuses = {
            'combat': 1.0,
            'stealth': 1.0,
            'magic': 1.0,
            'gathering': 1.0,
            'description': ''
        }

        # Ночь (22:00 - 05:00)
        if hour >= 22 or hour < 5:
            bonuses['stealth'] = 1.3
            bonuses['magic'] = 1.15
            bonuses['combat'] = 0.9
            bonuses['gathering'] = 0.8
            bonuses['description'] = 'Ночь: +30% скрытность, +15% магия, -10% бой, -20% добыча'

        # Раннее утро (05:00 - 08:00)
        elif 5 <= hour < 8:
            bonuses['gathering'] = 1.2
            bonuses['stealth'] = 1.1
            bonuses['description'] = 'Раннее утро: +20% добыча, +10% скрытность'

        # День (08:00 - 17:00)
        elif 8 <= hour < 17:
            bonuses['combat'] = 1.1
            bonuses['gathering'] = 1.1
            bonuses['description'] = 'День: +10% бой, +10% добыча'

        # Вечер (17:00 - 22:00)
        elif 17 <= hour < 22:
            bonuses['magic'] = 1.1
            bonuses['stealth'] = 1.15
            bonuses['description'] = 'Вечер: +10% магия, +15% скрытность'

        return bonuses


def create_game_systems():
    """
    Создать все игровые системы

    Returns:
        tuple: (WeatherSystem, RandomEventSystem, KillstreakSystem)
    """
    return WeatherSystem(), RandomEventSystem(), KillstreakSystem()
