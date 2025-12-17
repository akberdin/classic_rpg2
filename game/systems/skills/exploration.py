"""
Навыки исследования подземелий (EXPLORATION)

Содержит:
- KeenEyeSkill - пассивный навык обнаружения объектов
- DisarmTrapSkill - активный навык обезвреживания ловушек
- LockpickingSkill - активный навык взлома тайников
- TreasureHunterSkill - пассивный навык синергии и бонусов
"""
import random
from game.systems.skills.base import Skill, SkillCategory


class KeenEyeSkill(Skill):
    """
    Пассивный навык: Острый Глаз (Keen Eye)

    Способность замечать скрытые объекты, тайники и ловушки в подземельях.
    Чем выше ранг, тем выше шанс обнаружения и радиус автообнаружения.
    """

    def __init__(self):
        super().__init__(
            name="Острый Глаз",
            description="Способность замечать скрытые объекты, тайники и ловушки в подземельях",
            category=SkillCategory.EXPLORATION,
            mana_cost=0,
            stamina_cost=0,
            cooldown=0,
            max_rank=5,
            tactical_range=0  # Пассивный навык
        )

        # Статистика для прогресса
        self.objects_detected = 0  # Количество обнаруженных объектов

    def get_detection_bonus(self) -> int:
        """Получить бонус к обнаружению на основе ранга"""
        bonuses = {
            1: 2,
            2: 4,
            3: 6,
            4: 8,
            5: 10
        }
        return bonuses.get(self.rank, 2)

    def get_auto_detect_radius(self) -> int:
        """Получить радиус автообнаружения на основе ранга"""
        radii = {
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 5
        }
        return radii.get(self.rank, 1)

    def get_detection_chance_bonus(self) -> float:
        """Получить процентный бонус к шансу обнаружения"""
        bonuses = {
            1: 0.15,  # +15%
            2: 0.20,  # +20%
            3: 0.25,  # +25%
            4: 0.30,  # +30%
            5: 0.40   # +40%
        }
        return bonuses.get(self.rank, 0.15)

    def can_auto_detect(self, object_level: int) -> bool:
        """
        Проверить, можно ли автоматически обнаружить объект данного уровня

        Args:
            object_level: Уровень объекта (1-5)

        Returns:
            bool: Можно ли автоматически обнаружить
        """
        # Ранг 1: нет автообнаружения
        # Ранг 2: автообнаружение уровня 1
        # Ранг 3: автообнаружение уровней 1-2
        # Ранг 4: автообнаружение уровней 1-3
        # Ранг 5: автообнаружение уровней 1-4

        if self.rank == 1:
            return False
        elif self.rank == 2:
            return object_level == 1
        elif self.rank == 3:
            return object_level <= 2
        elif self.rank == 4:
            return object_level <= 3
        else:  # rank 5
            return object_level <= 4

    def has_sixth_sense(self) -> bool:
        """Проверить, есть ли способность 'Шестое Чувство' (Ранг 5)"""
        return self.rank >= 5

    def on_object_detected(self):
        """Вызывается при обнаружении объекта"""
        self.objects_detected += 1
        self.experience += 5  # +5 опыта за обнаружение

    def get_required_uses_for_rank(self):
        """Переопределяем: прогресс по обнаруженным объектам, а не использованиям"""
        requirements = {
            1: 0,
            2: 50,   # Нужно обнаружить 50 объектов для ранга 2
            3: 150,  # 150 для ранга 3
            4: 300,  # 300 для ранга 4
            5: 500   # 500 для ранга 5
        }
        return requirements.get(self.rank + 1, 0)

    def can_rank_up(self, player):
        """Проверить возможность повышения ранга"""
        if self.rank >= self.max_rank:
            return False, "Достигнут максимальный ранг"

        # Проверка уровня игрока
        required_level = self.get_required_player_level_for_rank()
        if player.level < required_level:
            return False, f"Требуется уровень {required_level}"

        # Проверка обнаруженных объектов
        required_detected = self.get_required_uses_for_rank()
        if self.objects_detected < required_detected:
            return False, f"Требуется обнаружить {required_detected} объектов (текущих: {self.objects_detected})"

        # Проверка золота
        required_gold = self.get_gold_cost_for_rank()
        if player.inventory.gold < required_gold:
            return False, f"Требуется {required_gold} золота"

        return True, "Можно повысить ранг"

    @property
    def description(self):
        """Переопределяем описание с деталями ранга"""
        base = super().description
        bonus = self.get_detection_bonus()
        radius = self.get_auto_detect_radius()
        chance = int(self.get_detection_chance_bonus() * 100)

        details = f"\n  Бонус к обнаружению: +{bonus}"
        details += f"\n  Радиус автообнаружения: {radius} клеток"
        details += f"\n  Шанс обнаружения: +{chance}%"
        details += f"\n  Обнаружено объектов: {self.objects_detected}"

        if self.has_sixth_sense():
            details += "\n  ⭐ ШЕСТОЕ ЧУВСТВО: Подсказка о количестве скрытых объектов в комнате"

        return base + details


class DisarmTrapSkill(Skill):
    """
    Активный навык: Обезвреживание Ловушек (Disarm Trap)

    Позволяет безопасно обезвреживать ловушки с уменьшенным уроном при провале.
    Требует, чтобы ловушка была обнаружена.
    """

    def __init__(self):
        super().__init__(
            name="Обезвреживание",
            description="Осторожное обезвреживание ловушек с минимальным риском",
            category=SkillCategory.EXPLORATION,
            mana_cost=0,
            stamina_cost=15,
            cooldown=2,
            max_rank=5,
            tactical_range=1  # Соседняя клетка
        )

        # Статистика
        self.traps_disarmed = 0

    def get_disarm_bonus(self) -> int:
        """Получить бонус к обезвреживанию на основе ранга"""
        bonuses = {
            1: 3,
            2: 5,
            3: 7,
            4: 10,
            5: 13
        }
        return bonuses.get(self.rank, 3)

    def get_damage_reduction(self) -> float:
        """Получить уменьшение урона при провале (0.0 = нет урона, 1.0 = полный урон)"""
        reductions = {
            1: 0.60,  # 60% урона (40% снижение)
            2: 0.40,  # 40% урона (60% снижение)
            3: 0.25,  # 25% урона (75% снижение)
            4: 0.10,  # 10% урона (90% снижение)
            5: 0.00   # Нет урона при провале
        }
        return reductions.get(self.rank, 0.60)

    def can_reroll(self) -> bool:
        """Можно ли попробовать еще раз (Ранг 2+)"""
        return self.rank >= 2

    def can_salvage_trap(self) -> bool:
        """Можно ли переработать ловушку в компоненты (Ранг 3+)"""
        return self.rank >= 3

    def can_reprogram_trap(self) -> bool:
        """Можно ли перепрограммировать ловушку против врагов (Ранг 4+)"""
        return self.rank >= 4

    def can_carry_traps(self) -> bool:
        """Можно ли забирать обезвреженные ловушки (Ранг 5)"""
        return self.rank >= 5

    def use(self, player, trap):
        """
        Использовать навык обезвреживания

        Args:
            player: Игрок
            trap: Объект ловушки

        Returns:
            dict: Результат обезвреживания
        """
        # Проверка ресурсов
        if player.stamina < self.stamina_cost:
            return {
                "success": False,
                "message": "Недостаточно выносливости!"
            }

        # Проверка кулдауна
        if self.current_cooldown > 0:
            return {
                "success": False,
                "message": f"Навык на перезарядке! Осталось ходов: {self.current_cooldown}"
            }

        # Проверка, что ловушка обнаружена
        if not trap.is_detected:
            return {
                "success": False,
                "message": "Ловушка не обнаружена! Сначала найдите её."
            }

        if trap.is_disarmed:
            return {
                "success": False,
                "message": "Ловушка уже обезврежена."
            }

        # Расходуем ресурсы
        player.stamina -= self.stamina_cost
        self.current_cooldown = self.cooldown

        # Бросок на обезвреживание
        disarm_roll = random.randint(1, 20) + player.dexterity // 2 + player.luck // 4 + self.get_disarm_bonus()

        if disarm_roll >= trap.disarm_dc:
            # Успех!
            trap.is_disarmed = True
            self.traps_disarmed += 1
            self.experience += 10
            self.use_count += 1

            result = {
                "success": True,
                "message": f"✓ Вы успешно обезвредили ловушку '{trap.name}' ({trap.level_name})!",
                "trap_disarmed": True
            }

            # Дополнительные бонусы по рангам
            if self.can_salvage_trap() and random.random() < 0.20:
                # Переработка в компоненты
                result["salvaged"] = True
                result["message"] += "\n  +Получены компоненты ловушки!"

            return result
        else:
            # Провал
            self.experience += 3  # Меньше опыта за провал

            damage_mult = self.get_damage_reduction()
            if damage_mult == 0.0:
                # Ранг 5 - полная защита
                return {
                    "success": False,
                    "message": f"✗ Провал обезвреживания, но ваше мастерство защитило вас от урона!",
                    "trap_disarmed": False,
                    "damage": 0
                }
            else:
                # Частичный урон
                damage = int(trap.damage * damage_mult)
                defense = player.get_total_defense() if hasattr(player, 'get_total_defense') else 0
                actual_damage = max(1, damage - defense // 2)

                player.health -= actual_damage
                if player.health < 0:
                    player.health = 0

                reduction_pct = int((1.0 - damage_mult) * 100)
                message = f"✗ Провал! Ловушка частично сработала: {actual_damage} урона ({reduction_pct}% снижение)"

                if player.health <= 0:
                    message += "\n  ☠ Вы погибли!"

                return {
                    "success": False,
                    "message": message,
                    "trap_disarmed": False,
                    "damage": actual_damage,
                    "player_dead": player.health <= 0
                }

    def on_trap_disarmed(self):
        """Вызывается при успешном обезвреживании"""
        self.traps_disarmed += 1

    def get_required_uses_for_rank(self):
        """Прогресс по обезвреженным ловушкам"""
        requirements = {
            1: 0,
            2: 30,
            3: 80,
            4: 150,
            5: 300
        }
        return requirements.get(self.rank + 1, 0)

    def can_rank_up(self, player):
        """Проверить возможность повышения ранга"""
        if self.rank >= self.max_rank:
            return False, "Достигнут максимальный ранг"

        # Проверка уровня
        required_level = self.get_required_player_level_for_rank()
        if player.level < required_level:
            return False, f"Требуется уровень {required_level}"

        # Проверка обезвреженных ловушек
        required_disarmed = self.get_required_uses_for_rank()
        if self.traps_disarmed < required_disarmed:
            return False, f"Требуется обезвредить {required_disarmed} ловушек (текущих: {self.traps_disarmed})"

        # Проверка золота
        required_gold = self.get_gold_cost_for_rank()
        if player.inventory.gold < required_gold:
            return False, f"Требуется {required_gold} золота"

        # Проверка Keen Eye
        if self.rank == 0:  # Для изучения Ранга 1
            keen_eye = player.skill_manager.get_skill("Острый Глаз")
            if not keen_eye or keen_eye.rank < 1:
                return False, "Требуется навык 'Острый Глаз' (Ранг 1)"

        return True, "Можно повысить ранг"

    @property
    def description(self):
        """Описание с деталями"""
        base = super().description
        bonus = self.get_disarm_bonus()
        reduction = int((1.0 - self.get_damage_reduction()) * 100)

        details = f"\n  Бонус к обезвреживанию: +{bonus}"
        details += f"\n  Снижение урона при провале: {reduction}%"
        details += f"\n  Обезврежено ловушек: {self.traps_disarmed}"
        details += f"\n  Стоимость: {self.stamina_cost} выносливости"
        details += f"\n  Перезарядка: {self.cooldown} ходов"

        if self.can_reroll():
            details += "\n  ⭐ Можно попробовать дважды"
        if self.can_salvage_trap():
            details += "\n  ⭐ Переработка в компоненты (20% шанс)"
        if self.can_reprogram_trap():
            details += "\n  ⭐ Перепрограммирование против врагов"
        if self.can_carry_traps():
            details += "\n  ⭐ Можно забрать ловушку"

        return base + details


class LockpickingSkill(Skill):
    """
    Активный навык: Взлом (Lockpicking)

    Позволяет взламывать тайники с бонусом к качеству лута и дополнительными предметами.
    """

    def __init__(self):
        super().__init__(
            name="Взлом",
            description="Искусное вскрытие тайников с улучшенным лутом",
            category=SkillCategory.EXPLORATION,
            mana_cost=0,
            stamina_cost=20,
            cooldown=3,
            max_rank=5,
            tactical_range=1
        )

        # Статистика
        self.stashes_lockpicked = 0

    def get_lockpick_bonus(self) -> int:
        """Бонус к броску взлома"""
        bonuses = {
            1: 2,
            2: 4,
            3: 6,
            4: 8,
            5: 10
        }
        return bonuses.get(self.rank, 2)

    def get_quality_bonus(self) -> int:
        """Бонус к качеству лута (в процентах)"""
        bonuses = {
            1: 10,
            2: 20,
            3: 30,
            4: 40,
            5: 50
        }
        return bonuses.get(self.rank, 10)

    def get_extra_item_chance(self) -> float:
        """Шанс дополнительного предмета"""
        chances = {
            1: 0.00,  # Нет доп. предметов
            2: 0.10,  # 10% шанс
            3: 0.15,  # 15% шанс
            4: 0.25,  # 25% шанс
            5: 1.00   # Гарантировано
        }
        return chances.get(self.rank, 0.00)

    def get_stamina_cost(self) -> int:
        """Стоимость с учетом ранга"""
        if self.rank >= 5:
            return 10  # Снижение для ранга 5
        return self.stamina_cost

    def can_stealth_lockpick(self) -> bool:
        """Стелс-взлом (Ранг 4+)"""
        return self.rank >= 4

    def can_see_contents(self) -> bool:
        """Treasure Sense - видеть содержимое (Ранг 5)"""
        return self.rank >= 5

    def use(self, player, stash):
        """
        Использовать навык взлома

        Args:
            player: Игрок
            stash: Объект тайника

        Returns:
            dict: Результат взлома
        """
        cost = self.get_stamina_cost()

        # Проверка ресурсов
        if player.stamina < cost:
            return {
                "success": False,
                "message": "Недостаточно выносливости!"
            }

        # Проверка кулдауна
        if self.current_cooldown > 0:
            return {
                "success": False,
                "message": f"Навык на перезарядке! Осталось ходов: {self.current_cooldown}"
            }

        # Проверка, что тайник обнаружен
        if not stash.is_detected:
            return {
                "success": False,
                "message": "Тайник не обнаружен! Сначала найдите его."
            }

        if stash.is_looted:
            return {
                "success": False,
                "message": "Тайник уже обыскан."
            }

        # Расходуем ресурсы
        player.stamina -= cost
        self.current_cooldown = self.cooldown

        # Бросок на взлом
        lockpick_dc = stash.detection_dc + (stash.stash_level.value * 2)
        lockpick_roll = random.randint(1, 20) + player.dexterity // 2 + player.intelligence // 3 + self.get_lockpick_bonus()

        if lockpick_roll >= lockpick_dc:
            # Успех взлома!
            self.stashes_lockpicked += 1
            self.experience += 15
            self.use_count += 1

            # Теперь обыскиваем тайник с бонусами
            # Применяем бонус качества и шанс доп. предметов
            quality_bonus = self.get_quality_bonus()
            extra_item_chance = self.get_extra_item_chance()

            # Помечаем что взлом был успешен (для генерации лута)
            stash._lockpicking_quality_bonus = quality_bonus
            stash._lockpicking_extra_chance = extra_item_chance

            # Обыскиваем
            loot_result = stash.loot(player)

            result = {
                "success": True,
                "message": f"✓ Успешный взлом {stash.name} ({stash.level_name})!",
                "quality_bonus": quality_bonus,
                "loot": loot_result
            }

            if loot_result.get("trap_triggered"):
                result["message"] += "\n  ⚠ Но ловушка всё равно сработала при обыске!"

            return result
        else:
            # Провал взлома
            self.experience += 5  # Меньше опыта

            # Проверка шанса избежать ловушки
            if self.rank >= 3:
                avoid_chance = 0.50 if self.rank == 3 else 0.80
                if random.random() < avoid_chance:
                    return {
                        "success": False,
                        "message": f"✗ Провал взлома, но вы избежали последствий!",
                        "lockpick_failed": True
                    }

            # Ловушка срабатывает (если есть)
            if stash.has_trap and stash.trap and not stash.trap.is_disarmed:
                trap_result = stash.trap.trigger(player)
                return {
                    "success": False,
                    "message": f"✗ Провал взлома! Ловушка сработала!\n{trap_result['message']}",
                    "lockpick_failed": True,
                    "trap_triggered": True,
                    "trap_result": trap_result
                }
            else:
                return {
                    "success": False,
                    "message": f"✗ Провал взлома! Тайник остался закрыт.",
                    "lockpick_failed": True
                }

    def get_required_uses_for_rank(self):
        """Прогресс по взломанным тайникам"""
        requirements = {
            1: 0,
            2: 40,
            3: 100,
            4: 200,
            5: 400
        }
        return requirements.get(self.rank + 1, 0)

    def can_rank_up(self, player):
        """Проверить возможность повышения ранга"""
        if self.rank >= self.max_rank:
            return False, "Достигнут максимальный ранг"

        required_level = self.get_required_player_level_for_rank()
        if player.level < required_level:
            return False, f"Требуется уровень {required_level}"

        required_lockpicked = self.get_required_uses_for_rank()
        if self.stashes_lockpicked < required_lockpicked:
            return False, f"Требуется взломать {required_lockpicked} тайников (текущих: {self.stashes_lockpicked})"

        required_gold = self.get_gold_cost_for_rank()
        if player.inventory.gold < required_gold:
            return False, f"Требуется {required_gold} золота"

        # Проверка Keen Eye
        if self.rank == 0:
            keen_eye = player.skill_manager.get_skill("Острый Глаз")
            if not keen_eye or keen_eye.rank < 1:
                return False, "Требуется навык 'Острый Глаз' (Ранг 1)"

        return True, "Можно повысить ранг"

    @property
    def description(self):
        """Описание с деталями"""
        base = super().description
        bonus = self.get_lockpick_bonus()
        quality = self.get_quality_bonus()
        extra = int(self.get_extra_item_chance() * 100)
        cost = self.get_stamina_cost()

        details = f"\n  Бонус к взлому: +{bonus}"
        details += f"\n  Бонус качества лута: +{quality}%"
        if extra > 0:
            details += f"\n  Шанс доп. предмета: {extra}%"
        details += f"\n  Взломано тайников: {self.stashes_lockpicked}"
        details += f"\n  Стоимость: {cost} выносливости"
        details += f"\n  Перезарядка: {self.cooldown} ходов"

        if self.can_stealth_lockpick():
            details += "\n  ⭐ Стелс-взлом"
        if self.can_see_contents():
            details += "\n  ⭐ TREASURE SENSE: Видите содержимое до взлома"

        return base + details


class TreasureHunterSkill(Skill):
    """
    Пассивный навык: Охотник за Сокровищами (Treasure Hunter)

    Синергия с другими навыками исследования, улучшает общую эффективность.
    Бонусы к золоту и редким предметам.
    """

    def __init__(self):
        super().__init__(
            name="Охотник за Сокровищами",
            description="Мастерство поиска сокровищ с дополнительными бонусами",
            category=SkillCategory.EXPLORATION,
            mana_cost=0,
            stamina_cost=0,
            cooldown=0,
            max_rank=5,
            tactical_range=0
        )

    def get_gold_bonus(self) -> float:
        """Процентный бонус к золоту"""
        bonuses = {
            1: 0.05,   # +5%
            2: 0.10,   # +10%
            3: 0.15,   # +15%
            4: 0.20,   # +20%
            5: 0.30    # +30%
        }
        return bonuses.get(self.rank, 0.05)

    def get_rarity_bonus(self) -> float:
        """Процентный бонус к шансу редких предметов"""
        bonuses = {
            1: 0.03,   # +3%
            2: 0.06,   # +6%
            3: 0.10,   # +10%
            4: 0.15,   # +15%
            5: 0.20    # +20%
        }
        return bonuses.get(self.rank, 0.03)

    def has_minimap_directions(self) -> bool:
        """Показывает направление к ближайшему объекту (Ранг 2+)"""
        return self.rank >= 2

    def has_level_identification(self) -> bool:
        """Автоматически показывает уровень обнаруженных объектов (Ранг 3+)"""
        return self.rank >= 3

    def has_fortunes_favor(self) -> bool:
        """Каждый 10-й тайник дает двойной лут (Ранг 4+)"""
        return self.rank >= 4

    def has_legendary_luck(self) -> bool:
        """5% шанс найти уникальные артефакты (Ранг 5)"""
        return self.rank >= 5

    def get_stamina_reduction(self) -> float:
        """Снижение стоимости навыков EXPLORATION (Ранг 5)"""
        if self.rank >= 5:
            return 0.25  # 25% снижение
        return 0.0

    def apply_gold_bonus(self, base_gold: int) -> int:
        """Применить бонус к золоту"""
        multiplier = 1.0 + self.get_gold_bonus()
        return int(base_gold * multiplier)

    def should_trigger_fortunes_favor(self, loot_count: int) -> bool:
        """Проверить, должен ли сработать Fortune's Favor"""
        if not self.has_fortunes_favor():
            return False
        return loot_count % 10 == 0

    def can_rank_up(self, player):
        """Проверить возможность повышения ранга"""
        if self.rank >= self.max_rank:
            return False, "Достигнут максимальный ранг"

        required_level = self.get_required_player_level_for_rank()
        if player.level < required_level:
            return False, f"Требуется уровень {required_level}"

        required_gold = self.get_gold_cost_for_rank()
        if player.inventory.gold < required_gold:
            return False, f"Требуется {required_gold} золота"

        # Проверка требований по другим навыкам
        keen_eye = player.skill_manager.get_skill("Острый Глаз")

        if self.rank == 0:  # Для изучения Ранга 1
            if not keen_eye or keen_eye.rank < 2:
                return False, "Требуется навык 'Острый Глаз' (Ранг 2)"
        elif self.rank == 4:  # Для Ранга 5
            # Все EXPLORATION навыки должны быть Ранг 4+
            disarm = player.skill_manager.get_skill("Обезвреживание")
            lockpick = player.skill_manager.get_skill("Взлом")

            if not keen_eye or keen_eye.rank < 4:
                return False, "Требуется 'Острый Глаз' (Ранг 4+)"
            if not disarm or disarm.rank < 4:
                return False, "Требуется 'Обезвреживание' (Ранг 4+)"
            if not lockpick or lockpick.rank < 4:
                return False, "Требуется 'Взлом' (Ранг 4+)"

        return True, "Можно повысить ранг"

    @property
    def description(self):
        """Описание с деталями"""
        base = super().description
        gold = int(self.get_gold_bonus() * 100)
        rarity = int(self.get_rarity_bonus() * 100)

        details = f"\n  Бонус к золоту: +{gold}%"
        details += f"\n  Бонус к редким предметам: +{rarity}%"

        if self.has_minimap_directions():
            details += "\n  ⭐ Миникарта показывает направление к объектам"
        if self.has_level_identification():
            details += "\n  ⭐ Автоматическое определение уровня объектов"
        if self.has_fortunes_favor():
            details += "\n  ⭐ FORTUNE'S FAVOR: Каждый 10-й тайник дает х2 лут"
        if self.has_legendary_luck():
            details += "\n  ⭐ LEGENDARY LUCK: 5% шанс уникальных артефактов"
            details += "\n  ⭐ Все навыки EXPLORATION: -25% стоимости"

        return base + details


# Список всех навыков EXPLORATION для регистрации
EXPLORATION_SKILLS = {
    "keen_eye": KeenEyeSkill,
    "disarm_trap": DisarmTrapSkill,
    "lockpicking": LockpickingSkill,
    "treasure_hunter": TreasureHunterSkill,
}
