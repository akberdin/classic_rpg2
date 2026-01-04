"""
Классы торговцев: Merchant и MagicMerchant

Этот модуль содержит только определения классов торговцев.
AI логика вынесена в merchant_ai.py.
Генерация товаров вынесена в merchant_goods.py.
"""
import random
from game.npc.base import NPC
from game.constants import NPC_TYPE_MERCHANT
from game.npc.merchant_ai import MerchantAI
from game.npc.merchant_goods import (
    MerchantGoodsGenerator,
    MagicGoodsGenerator,
    WarriorGoodsGenerator,
    ShadowGoodsGenerator
)


class Merchant(NPC):
    """Класс Торговца с AI перемещения по waypoints и побега от опасности"""

    def __init__(self, name, x=0, y=0, level=3, merchant_config=None):
        """
        Инициализация Торговца

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
            merchant_config: Конфигурация торговца из map config (опционально)
        """
        super().__init__(name, x, y, npc_type=NPC_TYPE_MERCHANT, level=level)

        # Модификация статов для торговца: средние характеристики, низкий дух
        self._adjust_merchant_stats()

        # AI параметры
        self.state = "travel"  # travel, rest, flee
        self.stuck_counter = 0  # Счетчик для определения застревания
        self.threat = None  # Текущая угроза от которой убегаем
        self.detection_range = 8  # Дальность обнаружения угроз

        # Состояние по умолчанию для расписания
        self.default_state = "travel"

        # Параметры из конфигурации (новая система waypoints)
        self.merchant_id = None  # Уникальный ID торговца
        self.waypoints = []  # Маршрут: [{"x": int, "y": int, "duration": int}, ...]
        self.current_waypoint_index = 0  # Текущая точка маршрута
        self.is_loop = True  # Зациклен ли маршрут
        self.color = (255, 165, 0)  # Цвет отображения (по умолчанию оранжевый)

        # Специализации торговца (категории товаров с качеством 0-N)
        # 0 = не торгует данной категорией
        self.specializations = {
            "jewelry": 1,
            "resources": 1,
            "armor": 1,
            "weapons": 1,
            "potions": 1
        }

        # Параметры респавна и обновления
        self.respawn_time = 48  # Время респавна в глобальных ходах
        self.assortment_update = 120  # Ходов до обновления ассортимента
        self.assortment_update_counter = 0  # Счётчик ходов для обновления
        self.wealth = 1000  # Стартовый капитал торговца

        # Счётчик отдыха в текущей точке (в глобальных ходах)
        self.rest_counter = 0
        self.current_waypoint_duration = 0  # Длительность остановки в текущей точке

        # Система для торговцев без waypoints (используется respawn_manager)
        self.settlements = []
        self.target_location = None
        self.rest_duration = 0

        # Применяем конфигурацию если есть
        if merchant_config:
            self._apply_config(merchant_config)

        # Торговая система - генерируем товары с учётом специализаций
        MerchantGoodsGenerator.generate_goods(self)

    def _apply_config(self, config):
        """
        Применить конфигурацию торговца из map config

        Args:
            config: Словарь с параметрами торговца
        """
        self.merchant_id = config.get('id')
        self.name = config.get('name', self.name)

        # Ранг торговца определяет качество товаров
        rank = config.get('rank', 1)
        # Устанавливаем уровень на основе ранга (ранг 1: 1-10, ранг 2: 11-20, и т.д.)
        self.level = (rank - 1) * 10 + random.randint(1, 10)

        # Waypoints маршрут
        self.waypoints = config.get('waypoints', [])
        if self.waypoints:
            # Начинаем с первой точки
            self.current_waypoint_index = 0
            first_waypoint = self.waypoints[0]
            self.x = first_waypoint.get('x', self.x)
            self.y = first_waypoint.get('y', self.y)
            self.current_waypoint_duration = first_waypoint.get('duration', 20)

        self.is_loop = config.get('is_loop', True)

        # Цвет
        color = config.get('color', [255, 165, 0])
        if isinstance(color, list) and len(color) >= 3:
            self.color = tuple(color[:3])

        # Специализации
        specs = config.get('specializations', {})
        for category, value in specs.items():
            if category in self.specializations:
                self.specializations[category] = value

        # Параметры респавна и обновления
        self.respawn_time = config.get('respawn_time', 48)
        self.assortment_update = config.get('assortment_update', 120)
        self.wealth = config.get('wealth', 1000)

    def set_waypoints(self, waypoints, is_loop=True):
        """
        Установить маршрут движения торговца

        Args:
            waypoints: Список точек [{"x": int, "y": int, "duration": int}, ...]
            is_loop: Зациклить маршрут
        """
        self.waypoints = waypoints
        self.is_loop = is_loop
        self.current_waypoint_index = 0
        if waypoints:
            first_wp = waypoints[0]
            self.current_waypoint_duration = first_wp.get('duration', 20)

    def _adjust_merchant_stats(self):
        """Модификация статов для торговца - не боец, не маг"""
        # Немного повышаем удачу (торговая жилка, макс +5%)
        self.luck = int(self.luck * 1.05)

        # Снижаем боевые характеристики, но компенсируем силу бонусом +10
        self.strength = max(1, int(self.strength * 0.7)) + 10  # Бонус +10 к силе для переноски товаров
        self.dexterity = max(1, int(self.dexterity * 0.8))

        # Снижаем магические характеристики
        self.spirit = max(1, int(self.spirit * 0.4))
        self.intelligence = max(1, int(self.intelligence * 0.8))

        # Обновляем производные статы
        self.update_derived_stats()

    def get_merchant_rank(self):
        """
        Получить ранг торговца на основе уровня

        Returns:
            int: Ранг от 1 до 4
        """
        if self.level <= 10:
            return 1
        elif self.level <= 20:
            return 2
        elif self.level <= 30:
            return 3
        else:
            return 4

    def set_settlements(self, settlements):
        """
        Установить список населенных пунктов для посещения

        Args:
            settlements: Список локаций (Location объектов)
        """
        self.settlements = settlements
        if settlements and not self.target_location:
            MerchantAI._choose_new_destination(self)

    def update_ai(self, context_or_map, all_npcs=None, current_hour=12):
        """
        Обновление AI торговца за 1 глобальный ход

        Args:
            context_or_map: AIContext или карта игры
            all_npcs: Список всех NPC для обнаружения угроз
            current_hour: Текущий час суток (0-23)
        """
        # Поддержка AIContext и старого способа вызова
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            all_npcs = context.all_npcs
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        # Делегируем обновление AI в MerchantAI
        MerchantAI.update(self, game_map, all_npcs, current_hour)

    def can_trade_category(self, category):
        """
        Проверить, торгует ли торговец данной категорией товаров

        Args:
            category: Категория (jewelry, resources, armor, weapons, potions)

        Returns:
            bool: True если торговец торгует этой категорией
        """
        return self.specializations.get(category, 0) > 0

    def get_category_quality(self, category):
        """
        Получить качество товаров для категории (влияет на генерацию)

        Args:
            category: Категория товаров

        Returns:
            int: Уровень качества (0 = не торгует, 1+ = качество)
        """
        return self.specializations.get(category, 0)


class MagicMerchant(Merchant):
    """Класс Торговца магическими товарами для академии магии"""

    def __init__(self, name, x=0, y=0, level=5):
        """
        Инициализация Торговца книгами магии

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
        """
        super().__init__(name, x, y, level)
        # Стационарный торговец - не путешествует
        self.state = "rest"
        # Перегенерируем товары для магического торговца
        MagicGoodsGenerator.generate_goods(self)

    def update_ai(self, context_or_map, all_npcs=None, current_hour=12):
        """Стационарный торговец - только обновляем расписание и выносливость"""
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        self.update_schedule(current_hour, game_map)

        if self.is_hidden():
            return

        # Восстанавливаем выносливость
        self.recover_stamina(is_active_rest=True)


class WarriorMerchant(Merchant):
    """Класс Торговца воинскими товарами для военной академии"""

    def __init__(self, name, x=0, y=0, level=5):
        """
        Инициализация Торговца книгами воинского искусства

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
        """
        super().__init__(name, x, y, level)
        # Стационарный торговец - не путешествует
        self.state = "rest"
        # Перегенерируем товары для военного торговца
        WarriorGoodsGenerator.generate_goods(self)

    def update_ai(self, context_or_map, all_npcs=None, current_hour=12):
        """Стационарный торговец - только обновляем расписание и выносливость"""
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        self.update_schedule(current_hour, game_map)

        if self.is_hidden():
            return

        # Восстанавливаем выносливость
        self.recover_stamina(is_active_rest=True)


class ShadowMerchant(Merchant):
    """Класс Торговца теневыми товарами для Тайного лагеря"""

    def __init__(self, name, x=0, y=0, level=5):
        """
        Инициализация Торговца книгами Тени

        Args:
            name: Имя торговца
            x: Позиция X
            y: Позиция Y
            level: Уровень торговца
        """
        super().__init__(name, x, y, level)
        # Стационарный торговец - не путешествует
        self.state = "rest"
        # Перегенерируем товары для теневого торговца
        ShadowGoodsGenerator.generate_goods(self)

    def update_ai(self, context_or_map, all_npcs=None, current_hour=12):
        """Стационарный торговец - только обновляем расписание и выносливость"""
        from game.core.ai_context import AIContext
        if isinstance(context_or_map, AIContext):
            context = context_or_map
            game_map = context.game_map
            current_hour = context.current_hour
        else:
            game_map = context_or_map

        self.update_schedule(current_hour, game_map)

        if self.is_hidden():
            return

        # Восстанавливаем выносливость
        self.recover_stamina(is_active_rest=True)
