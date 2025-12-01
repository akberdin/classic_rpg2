"""
Модуль для управления игровым временем
"""
from game.core.game_context import GameContext


class GameTime:
    """Класс для управления игровым временем"""

    def __init__(self, game):
        """
        Инициализация игрового времени

        Args:
            game: Ссылка на основной объект игры
        """
        self.game = game  # Сохраняем для специфичных вызовов
        self.ctx = GameContext(game)
        self.game_hour = 6.0  # Начало игры в 6 утра (используем float для дробных часов)
        self.game_day = 1
        self.game_turn = 0  # Счетчик ходов для ротации квестов
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
        self.game_turn += 1  # Увеличиваем счетчик ходов

        # Проверяем и обновляем квесты каждый ход (но ротация происходит раз в 120 ходов)
        if self.ctx.quest_manager and self.ctx.game_map:
            updated_locations = self.ctx.quest_manager.check_and_rotate_all_quests(
                self.ctx.game_map,
                self.game_turn,
                self.ctx.player.level
            )
            if updated_locations:
                print(f"Квесты обновлены в следующих локациях: {', '.join(updated_locations)}")

        # Если прошло 24 часа, начинается новый день
        while self.game_hour >= 24:
            self.game_hour -= 24
            self.game_day += 1

        # Накапливаем часы для обновления AI
        self.accumulated_hours += hours

        # Определяем сколько полных часов прошло
        full_hours_passed = int(self.accumulated_hours)
        self.accumulated_hours -= full_hours_passed

        # Обновляем AI всех NPC только при прохождении полных часов
        for _ in range(full_hours_passed):
            # Восстановление здоровья, маны и выносливости происходит только при активном отдыхе (R)
            # При обычном движении восстановления нет (кроме зелий)

            # Обновляем перезарядки навыков и статус-эффекты игрока
            if hasattr(self.ctx.player, 'skill_manager') and self.ctx.player.skill_manager:
                self.ctx.player.skill_manager.tick_cooldowns()
                effect_messages = self.ctx.player.skill_manager.tick_status_effects()
                for msg in effect_messages:
                    print(msg)

            # Используем новую систему управления NPC через AIContext
            from game.core import get_all_npcs_from_game, update_all_npc_ai_with_context, create_ai_context

            # Собираем всех NPC через вспомогательную функцию
            all_npcs = get_all_npcs_from_game(self.game)

            # Выводим общее количество NPC в мире
            alive_npcs = [npc for npc in all_npcs if npc.is_alive]
            print(f"[Статистика NPC] Живых NPC в мире: {len(alive_npcs)} (всего: {len(all_npcs)})")

            # Перестраиваем spatial grid для оптимизации
            self.ctx.performance_optimizer.rebuild_spatial_grid(all_npcs)

            # Увеличиваем счетчик для оптимизации AI
            self.ctx.performance_optimizer.increment_counter()

            # Создаём контекст AI и обновляем всех NPC
            ai_context = create_ai_context(self.game)
            update_all_npc_ai_with_context(self.game, ai_context)

            # Обрабатываем респавн NPC
            if self.ctx.respawn_manager:
                ready_to_respawn = self.ctx.respawn_manager.update(1)
                for respawn_data in ready_to_respawn:
                    self.ctx.respawn_manager.respawn_npc(respawn_data, self.game)

        # Проверяем, атаковал ли кто-то игрока (открываем меню выбора режима боя)
        if self.ctx.player.attacked_by_npc and not self.ctx.in_combat:
            attacker = self.ctx.player.attacked_by_npc
            self.ctx.player.attacked_by_npc = None  # Сбрасываем флаг
            if attacker.is_alive:  # Проверяем что атакующий еще жив
                # Открываем меню выбора режима боя с флагом агрессии
                self.game.nearby_npc = attacker
                self.game.is_npc_aggression = True
                self.game.combat_mode_menu_open = True
                print(f"{attacker.name} напал на вас! Выберите режим боя!")

        # Проверяем достижения
        if self.ctx.achievement_manager:
            unlocked = self.ctx.achievement_manager.check_achievements(self.ctx.player)
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
