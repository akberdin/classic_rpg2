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
        self.game_hour = 6.0  # Начало игры в 6 утра (используем float для дробных часов)
        self.game_day = 1
        self.accumulated_hours = 0.0  # Накопленные дробные часы для обновления AI

    @property
    def hour(self):
        """
        Свойство для доступа к текущему часу

        Returns:
            int: Текущий час (0-23)
        """
        return self.game_hour

    def advance_time(self, hours=1, skip_player_recovery=False):
        """
        Продвинуть игровое время на указанное количество часов

        Args:
            hours: Количество часов для продвижения (может быть дробным)
            skip_player_recovery: Не восстанавливать выносливость игрока (используется при отдыхе)
        """
        self.game_hour += hours

        # Если прошло 24 часа, начинается новый день
        while self.game_hour >= 24:
            self.game_hour -= 24
            self.game_day += 1

            # Проверяем и обновляем квесты раз в 5 дней
            if hasattr(self.game, 'quest_manager') and hasattr(self.game, 'game_map'):
                updated_locations = self.game.quest_manager.check_and_rotate_all_quests(
                    self.game.game_map,
                    self.game_day,
                    self.game.player.level
                )
                if updated_locations:
                    print(f"Квесты обновлены в следующих локациях: {', '.join(updated_locations)}")

        # Накапливаем часы для обновления AI
        self.accumulated_hours += hours

        # Определяем сколько полных часов прошло
        full_hours_passed = int(self.accumulated_hours)
        self.accumulated_hours -= full_hours_passed

        # Обновляем AI всех NPC только при прохождении полных часов
        for _ in range(full_hours_passed):
            # Восстанавливаем выносливость и здоровье игрока (если не пропускаем)
            if not skip_player_recovery:
                self.game.player.recover_stamina()
                self.game.player.recover_health()

            # Обновляем перезарядки навыков и статус-эффекты игрока
            if hasattr(self.game.player, 'skill_manager') and self.game.player.skill_manager:
                self.game.player.skill_manager.tick_cooldowns()
                effect_messages = self.game.player.skill_manager.tick_status_effects()
                for msg in effect_messages:
                    print(msg)

            # Собираем всех NPC
            all_npcs = (self.game.guards + self.game.merchants + self.game.mages +
                       self.game.bandits + self.game.miners + self.game.undead +
                       self.game.alchemists + self.game.hunters + self.game.necromancers +
                       self.game.animals)

            # Перестраиваем spatial grid для оптимизации
            self.game.performance_optimizer.rebuild_spatial_grid(all_npcs)

            # Увеличиваем счетчик для оптимизации AI
            self.game.performance_optimizer.increment_counter()

            # Получаем текущий час для расписаний NPC
            current_hour = int(self.game_hour) % 24

            # Обновляем AI только тех NPC, которых нужно обновлять в этом кадре
            for guard in self.game.guards:
                if self.game.performance_optimizer.should_update_ai(guard, self.game.player.x, self.game.player.y):
                    guard.update_ai(self.game.game_map, all_npcs, self.game.player, current_hour)

            for merchant in self.game.merchants:
                if self.game.performance_optimizer.should_update_ai(merchant, self.game.player.x, self.game.player.y):
                    merchant.update_ai(self.game.game_map, all_npcs, current_hour)

            for mage in self.game.mages:
                if self.game.performance_optimizer.should_update_ai(mage, self.game.player.x, self.game.player.y):
                    mage.update_ai(self.game.game_map, all_npcs, self.game.player, current_hour)

            for bandit in self.game.bandits:
                if self.game.performance_optimizer.should_update_ai(bandit, self.game.player.x, self.game.player.y):
                    bandit.update_ai(self.game.game_map, all_npcs, self.game.player, current_hour)

            for miner in self.game.miners:
                if self.game.performance_optimizer.should_update_ai(miner, self.game.player.x, self.game.player.y):
                    miner.update_ai(self.game.game_map, all_npcs, current_hour)

            for undead_npc in self.game.undead:
                if self.game.performance_optimizer.should_update_ai(undead_npc, self.game.player.x, self.game.player.y):
                    undead_npc.update_ai(self.game.game_map, all_npcs, self.game.player, current_hour)

            # Алхимики не нуждаются в обновлении AI (статичные торговцы)
            # но обновляем для консистентности
            for alchemist in self.game.alchemists:
                if self.game.performance_optimizer.should_update_ai(alchemist, self.game.player.x, self.game.player.y):
                    alchemist.update_ai(self.game.game_map, all_npcs, current_hour)

            # Охотники патрулируют и охотятся
            for hunter in self.game.hunters:
                if self.game.performance_optimizer.should_update_ai(hunter, self.game.player.x, self.game.player.y):
                    hunter.update_ai(self.game.game_map, all_npcs, self.game.player, current_hour)

            # Некроманты - враждебные маги
            for necromancer in self.game.necromancers:
                if self.game.performance_optimizer.should_update_ai(necromancer, self.game.player.x, self.game.player.y):
                    necromancer.update_ai(self.game.game_map, all_npcs, self.game.player, current_hour)

            # Животные - волки, медведи, олени
            for animal in self.game.animals:
                if self.game.performance_optimizer.should_update_ai(animal, self.game.player.x, self.game.player.y):
                    animal.update_ai(self.game.game_map, all_npcs, self.game.player, current_hour)

            # Обрабатываем респавн NPC
            if hasattr(self.game, 'respawn_manager'):
                ready_to_respawn = self.game.respawn_manager.update(1)
                for respawn_data in ready_to_respawn:
                    self.game.respawn_manager.respawn_npc(respawn_data, self.game)

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
            str: Время в формате "День X, ЧЧ:ММ"
        """
        hours = int(self.game_hour)
        minutes = int((self.game_hour - hours) * 60)
        return f"День {self.game_day}, {hours:02d}:{minutes:02d}"
