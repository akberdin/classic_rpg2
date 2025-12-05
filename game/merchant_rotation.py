"""
Система глобальной ротации товаров у торговцев
"""
from game.config.merchant_config import ROTATION_PERIOD_HOURS


class MerchantRotationManager:
    """Менеджер для управления глобальной ротацией товаров"""

    def __init__(self):
        """Инициализация менеджера ротации"""
        self.last_rotation_hour = 0  # Час последней ротации (абсолютный)
        self.rotation_period = ROTATION_PERIOD_HOURS  # Период ротации из конфига

    def get_total_hours(self, game_day, game_hour):
        """
        Вычисляет общее количество прошедших игровых часов

        Args:
            game_day: Текущий игровой день
            game_hour: Текущий игровой час

        Returns:
            int: Общее количество часов с начала игры
        """
        return (game_day - 1) * 24 + int(game_hour)

    def should_rotate(self, game_day, game_hour):
        """
        Проверяет, нужно ли производить ротацию товаров

        Args:
            game_day: Текущий игровой день
            game_hour: Текущий игровой час

        Returns:
            bool: True если нужна ротация, False иначе
        """
        total_hours = self.get_total_hours(game_day, game_hour)
        hours_since_last_rotation = total_hours - self.last_rotation_hour

        return hours_since_last_rotation >= self.rotation_period

    def rotate_all_merchants(self, game):
        """
        Производит ротацию товаров у всех торговцев в игре

        Args:
            game: Объект игры с доступом к карте и NPC
        """
        from game.npc.merchant import Merchant, MagicMerchant
        from game.npc.unique import Alchemist

        # Обновляем время последней ротации
        total_hours = self.get_total_hours(game.game_time.game_day, game.game_time.game_hour)
        self.last_rotation_hour = total_hours

        rotated_count = 0

        # Получаем все локации на карте
        if hasattr(game, 'game_map') and game.game_map:
            for location in game.game_map.locations:
                # Проверяем, есть ли у локации торговец
                if hasattr(location, 'merchant_npc') and location.merchant_npc:
                    npc = location.merchant_npc

                    # Регенерируем товары торговца
                    if isinstance(npc, MagicMerchant):
                        npc._generate_magic_goods()
                    elif isinstance(npc, Alchemist):
                        npc._generate_alchemist_goods()
                    elif isinstance(npc, Merchant):
                        npc._generate_merchant_goods()
                    else:
                        continue

                    rotated_count += 1

        # Выводим информацию о ротации
        print(f"\n[РОТАЦИЯ ТОВАРОВ] Прошло {self.rotation_period} часов ({self.rotation_period // 24} дней)")
        print(f"[РОТАЦИЯ ТОВАРОВ] Обновлен ассортимент у {rotated_count} торговцев")
        print(f"[РОТАЦИЯ ТОВАРОВ] Следующая ротация через {self.rotation_period} часов\n")

    def check_and_rotate(self, game):
        """
        Проверяет необходимость ротации и выполняет её при необходимости

        Args:
            game: Объект игры с доступом к карте и NPC
        """
        if self.should_rotate(game.game_time.game_day, game.game_time.game_hour):
            self.rotate_all_merchants(game)
