"""
Модуль для управления игровым временем
"""


class GameTime:
    """Класс для управления игровым временем"""

    def __init__(self, game):
        """
        Инициализация игрового времени

        Args:
            game: Ссылка на основной объект игры
        """
        self.game = game
        self.game_hour = 6  # Начало игры в 6 утра
        self.game_day = 1

    def advance_time(self, hours=1, skip_player_recovery=False):
        """
        Продвинуть игровое время на указанное количество часов

        Args:
            hours: Количество часов для продвижения
            skip_player_recovery: Не восстанавливать выносливость игрока (используется при отдыхе)
        """
        self.game_hour += hours

        # Если прошло 24 часа, начинается новый день
        while self.game_hour >= 24:
            self.game_hour -= 24
            self.game_day += 1

        # Обновляем AI всех NPC при изменении времени
        for _ in range(hours):
            # Восстанавливаем выносливость игрока (если не пропускаем)
            if not skip_player_recovery:
                self.game.player.recover_stamina()

            # Обновляем перезарядки навыков и статус-эффекты игрока
            self.game.player.skill_manager.tick_cooldowns()
            effect_messages = self.game.player.skill_manager.tick_status_effects()
            for msg in effect_messages:
                print(msg)

            # Собираем всех NPC
            all_npcs = (self.game.guards + self.game.merchants + self.game.mages +
                       self.game.bandits + self.game.miners + self.game.undead)

            # Перестраиваем spatial grid для оптимизации
            self.game.performance_optimizer.rebuild_spatial_grid(all_npcs)

            # Увеличиваем счетчик для оптимизации AI
            self.game.performance_optimizer.increment_counter()

            # Обновляем AI только тех NPC, которых нужно обновлять в этом кадре
            for guard in self.game.guards:
                if self.game.performance_optimizer.should_update_ai(guard, self.game.player.x, self.game.player.y):
                    guard.update_ai(self.game.game_map, all_npcs)

            for merchant in self.game.merchants:
                if self.game.performance_optimizer.should_update_ai(merchant, self.game.player.x, self.game.player.y):
                    merchant.update_ai(self.game.game_map, all_npcs)

            for mage in self.game.mages:
                if self.game.performance_optimizer.should_update_ai(mage, self.game.player.x, self.game.player.y):
                    mage.update_ai(self.game.game_map, all_npcs, self.game.player)

            for bandit in self.game.bandits:
                if self.game.performance_optimizer.should_update_ai(bandit, self.game.player.x, self.game.player.y):
                    bandit.update_ai(self.game.game_map, all_npcs, self.game.player)

            for miner in self.game.miners:
                if self.game.performance_optimizer.should_update_ai(miner, self.game.player.x, self.game.player.y):
                    miner.update_ai(self.game.game_map, all_npcs)

            for undead_npc in self.game.undead:
                if self.game.performance_optimizer.should_update_ai(undead_npc, self.game.player.x, self.game.player.y):
                    undead_npc.update_ai(self.game.game_map, all_npcs, self.game.player)

        # Проверяем, атаковал ли кто-то игрока (принудительное открытие окна боя)
        if self.game.player.attacked_by_npc and not self.game.in_combat:
            attacker = self.game.player.attacked_by_npc
            self.game.player.attacked_by_npc = None  # Сбрасываем флаг
            if attacker.is_alive:  # Проверяем что атакующий еще жив
                self.game._start_combat(attacker)
                print(f"{attacker.name} напал на вас!")

        # Проверяем достижения
        unlocked = self.game.achievement_manager.check_achievements(self.game.player)
        for achievement in unlocked:
            print(f"Достижение разблокировано: {achievement.name}!")
            print(f"   {achievement.description}")

    def get_time_string(self):
        """
        Получить строковое представление времени

        Returns:
            str: Время в формате "День X, ЧЧ:00"
        """
        return f"День {self.game_day}, {self.game_hour:02d}:00"
