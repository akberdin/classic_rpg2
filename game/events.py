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


class RandomEvent:
    """Случайное событие"""

    def __init__(self, event_id, name, description, effect_func, chance=0.1):
        """
        Инициализация события

        Args:
            event_id: ID события
            name: Название события
            description: Описание события
            effect_func: Функция эффекта (принимает player, game)
            chance: Шанс события (0-1)
        """
        self.event_id = event_id
        self.name = name
        self.description = description
        self.effect_func = effect_func
        self.chance = chance


class RandomEventSystem:
    """Система случайных событий"""

    def __init__(self):
        """Инициализация системы событий"""
        self.events = []
        self._setup_events()

    def _setup_events(self):
        """Настроить события"""
        # Положительные события
        self.events.append(RandomEvent(
            "find_gold",
            "Найден кошелёк",
            "Вы нашли кошелёк с золотом на дороге!",
            lambda p, g: self._find_gold(p, g),
            chance=0.08
        ))

        self.events.append(RandomEvent(
            "blessing",
            "Благословение путника",
            "Странствующий монах благословил вас.",
            lambda p, g: self._blessing(p, g),
            chance=0.05
        ))

        self.events.append(RandomEvent(
            "hidden_cache",
            "Тайник",
            "Вы обнаружили тайник под камнем!",
            lambda p, g: self._hidden_cache(p, g),
            chance=0.06
        ))

        self.events.append(RandomEvent(
            "lucky_find",
            "Удачная находка",
            "Вы нашли ценный предмет среди листвы!",
            lambda p, g: self._lucky_find(p, g),
            chance=0.04
        ))

        # Нейтральные события
        self.events.append(RandomEvent(
            "wandering_merchant",
            "Странствующий торговец",
            "Вы встретили странствующего торговца, который поделился советом.",
            lambda p, g: self._wandering_merchant(p, g),
            chance=0.07
        ))

        self.events.append(RandomEvent(
            "ancient_shrine",
            "Древний алтарь",
            "Вы нашли древний алтарь. Помолившись, вы чувствуете прилив сил.",
            lambda p, g: self._ancient_shrine(p, g),
            chance=0.05
        ))

        # Отрицательные события
        self.events.append(RandomEvent(
            "trap",
            "Ловушка",
            "Вы попали в скрытую ловушку!",
            lambda p, g: self._trap(p, g),
            chance=0.06
        ))

        self.events.append(RandomEvent(
            "pickpocket",
            "Карманник",
            "Ловкий вор украл часть вашего золота!",
            lambda p, g: self._pickpocket(p, g),
            chance=0.05
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

        for event in self.events:
            if random.random() < event.chance:
                result = event.effect_func(player, game)
                if result:
                    messages.append(f"[{event.name}] {event.description}")
                    messages.extend(result)
                break  # Только одно событие за раз

        return messages

    def _find_gold(self, player, game):
        """Найти золото"""
        gold = random.randint(5, 20) * player.level
        player.inventory.add_gold(gold)
        return [f"  Получено {gold} золота"]

    def _blessing(self, player, game):
        """Благословение"""
        # Временное увеличение удачи (через восстановление здоровья/маны)
        heal = int(player.max_health * 0.2)
        mana = int(player.max_mana * 0.2)
        player.health = min(player.max_health, player.health + heal)
        player.mana = min(player.max_mana, player.mana + mana)
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
        from game.inventory import PREDEFINED_ITEMS

        # Список возможных находок
        possible_items = [
            "health_potion", "mana_potion", "antidote",
            "copper_ore", "iron_ore", "wood"
        ]

        item_id = random.choice(possible_items)
        if item_id in PREDEFINED_ITEMS:
            item = PREDEFINED_ITEMS[item_id]
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
        player.health = player.max_health
        player.mana = player.max_mana
        player.stamina = player.max_stamina
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
