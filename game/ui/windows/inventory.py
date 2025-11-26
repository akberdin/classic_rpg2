"""
Окно инвентаря.
"""
import pygame
from game.ui.base import UIHelper
from game.inventory import EquipmentSlot


class InventoryWindow:
    """Улучшенное окно инвентаря с экипировкой"""

    def __init__(self, screen, font, info_font, scaler=None):
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.scaler = scaler
        self.selected_inventory_index = 0
        self.selected_equipment_slot = None
        self.mode = "inventory"  # "inventory" или "equipment"
        self.equipment_slot_rects = {}  # Словарь {slot: (rect, item)} для tooltip экипировки

    def render(self, player, mouse_pos=None):
        """
        Отрисовка окна инвентаря

        Args:
            player: Объект игрока
            mouse_pos: Позиция мыши (x, y) для tooltip
        """
        # Получаем размеры экрана
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Затемнение фона
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные)
        if self.scaler:
            window_width = self.scaler.scale_width(900)
            window_height = self.scaler.scale_height(650)
        else:
            window_width = min(900, int(screen_width * 0.85))
            window_height = min(650, int(screen_height * 0.75))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна с градиентом
        UIHelper.draw_gradient_rect(
            self.screen, window_x, window_y, window_width, window_height,
            (35, 35, 45), (55, 55, 70)
        )

        # Рамка
        pygame.draw.rect(
            self.screen,
            (120, 120, 150),
            (window_x, window_y, window_width, window_height),
            3
        )

        # Заголовок
        title_text = self.font.render("ИНВЕНТАРЬ И ЭКИПИРОВКА", True, (255, 215, 0))
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + int(10 * (window_height / 650))
        self.screen.blit(title_text, title_rect)

        # Информация о золоте и весе
        gold_text = self.info_font.render(
            f"Золото: {player.inventory.gold}  |  Вес: {player.inventory.current_weight}/{player.inventory.max_weight} кг",
            True,
            (255, 215, 0)
        )
        gold_rect = gold_text.get_rect()
        gold_rect.centerx = window_x + window_width // 2
        gold_rect.y = window_y + int(40 * (window_height / 650))
        self.screen.blit(gold_text, gold_rect)

        # Разделитель
        separator_y = int(70 * (window_height / 650))
        pygame.draw.line(
            self.screen,
            (100, 100, 120),
            (window_x + int(10 * (window_width / 900)), window_y + separator_y),
            (window_x + window_width - int(10 * (window_width / 900)), window_y + separator_y),
            2
        )

        # Левая панель - экипировка (адаптивные размеры)
        margin = int(20 * (window_width / 900))
        panel_y_offset = int(85 * (window_height / 650))
        equipment_panel_x = window_x + margin
        equipment_panel_y = window_y + panel_y_offset
        equipment_panel_width = int(400 * (window_width / 900))
        equipment_panel_height = int(500 * (window_height / 650))

        self._render_equipment_panel(
            player,
            equipment_panel_x,
            equipment_panel_y,
            equipment_panel_width,
            equipment_panel_height
        )

        # Правая панель - предметы (адаптивные размеры)
        inventory_panel_x = window_x + int(440 * (window_width / 900))
        inventory_panel_y = window_y + panel_y_offset
        inventory_panel_width = int(440 * (window_width / 900))
        inventory_panel_height = int(500 * (window_height / 650))

        self._render_inventory_panel(
            player,
            inventory_panel_x,
            inventory_panel_y,
            inventory_panel_width,
            inventory_panel_height
        )

        # Подсказки внизу
        hints_y = window_y + window_height - int(40 * (window_height / 650))
        hint_text = self.info_font.render(
            "W/S - выбор | E - экипировать | U - использовать | D/DEL - выбросить | I/ESC - закрыть",
            True,
            (180, 180, 180)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = hints_y
        self.screen.blit(hint_text, hint_rect)

        # Отрисовка tooltip при наведении мыши
        if mouse_pos:
            mouse_x, mouse_y = mouse_pos
            # Проверяем, наведён ли курсор на экипированный предмет
            is_equipped_item = False
            for slot, (rect, eq_item) in self.equipment_slot_rects.items():
                if rect.collidepoint(mouse_x, mouse_y) and eq_item:
                    is_equipped_item = True
                    break

            item = self.get_item_at_mouse(player, mouse_x, mouse_y)
            if item:
                # Не показываем сравнение для экипированных предметов
                self.render_item_tooltip(item, mouse_x, mouse_y, player, show_comparison=not is_equipped_item)

    def _render_equipment_panel(self, player, x, y, width, height):
        """Отрисовка панели экипировки"""
        # Очищаем словарь координат слотов
        self.equipment_slot_rects.clear()

        # Фон панели
        UIHelper.draw_panel(self.screen, x, y, width, height, (45, 45, 55), (100, 100, 120))

        # Заголовок (адаптивный отступ)
        title = self.font.render("Экипировка", True, (150, 200, 255))
        self.screen.blit(title, (x + int(10 * (width / 400)), y + int(5 * (height / 500))))

        # Слоты экипировки (адаптивные размеры)
        slot_y = y + int(40 * (height / 500))
        slot_height = max(18, int(22 * (height / 500)))

        # Группировка слотов
        slot_groups = [
            ("Оружие", [EquipmentSlot.WEAPON]),
            ("Доспехи", [EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.HANDS, EquipmentSlot.FEET]),
            ("Кольца", [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]),
            ("Украшения", [EquipmentSlot.AMULET, EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]),
        ]

        slot_names = {
            EquipmentSlot.WEAPON: "Оружие",
            EquipmentSlot.HEAD: "Голова",
            EquipmentSlot.CHEST: "Торс",
            EquipmentSlot.HANDS: "Руки",
            EquipmentSlot.FEET: "Ноги",
            EquipmentSlot.RING_1: "Кольцо 1",
            EquipmentSlot.RING_2: "Кольцо 2",
            EquipmentSlot.RING_3: "Кольцо 3",
            EquipmentSlot.RING_4: "Кольцо 4",
            EquipmentSlot.AMULET: "Амулет",
            EquipmentSlot.BRACELET_1: "Браслет 1",
            EquipmentSlot.BRACELET_2: "Браслет 2",
        }

        # Адаптивные отступы
        margin_left = int(15 * (width / 400))
        margin_sides = int(30 * (width / 400))
        text_offset = int(130 * (width / 400))
        text_margin = int(20 * (width / 400))

        for group_name, slots in slot_groups:
            # Название группы
            group_text = self.info_font.render(f"[{group_name}]", True, (180, 180, 200))
            self.screen.blit(group_text, (x + margin_left, slot_y))
            slot_y += max(16, int(20 * (height / 500)))

            for slot in slots:
                item = player.inventory.get_equipped_item(slot)

                # Создаём прямоугольник слота и сохраняем для tooltip
                slot_rect = pygame.Rect(x + margin_left, slot_y, width - margin_sides, slot_height - 2)
                self.equipment_slot_rects[slot] = (slot_rect, item)

                # Фон слота
                slot_color = (60, 60, 70) if item else (40, 40, 50)
                pygame.draw.rect(
                    self.screen,
                    slot_color,
                    slot_rect
                )

                # Рамка слота
                border_color = (100, 150, 200) if self.selected_equipment_slot == slot else (80, 80, 90)
                pygame.draw.rect(
                    self.screen,
                    border_color,
                    slot_rect,
                    2 if self.selected_equipment_slot == slot else 1
                )

                # Название слота
                slot_name_text = self.info_font.render(
                    f"{slot_names[slot]}:",
                    True,
                    (150, 150, 150)
                )
                self.screen.blit(slot_name_text, (x + text_margin, slot_y + int(8 * (height / 500))))

                # Экипированный предмет
                if item:
                    item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
                    item_text = self.info_font.render(
                        item_name[:30],
                        True,
                        item.quality.color if hasattr(item, 'quality') else (200, 200, 200)
                    )
                    self.screen.blit(item_text, (x + text_offset, slot_y + int(8 * (height / 500))))
                else:
                    empty_text = self.info_font.render("---", True, (100, 100, 100))
                    self.screen.blit(empty_text, (x + text_offset, slot_y + int(8 * (height / 500))))

                slot_y += slot_height

            slot_y += max(6, int(8 * (height / 500)))

    def _render_inventory_panel(self, player, x, y, width, height):
        """Отрисовка панели предметов"""
        # Фон панели
        UIHelper.draw_panel(self.screen, x, y, width, height, (45, 45, 55), (100, 100, 120))

        # Заголовок (адаптивные отступы)
        title = self.font.render("Предметы", True, (150, 200, 255))
        self.screen.blit(title, (x + int(10 * (width / 440)), y + int(5 * (height / 500))))

        # Информация о слотах
        all_items = player.inventory.get_all_items()
        slots_text = self.info_font.render(
            f"Слотов: {len(all_items)}/{player.inventory.max_slots}",
            True,
            (180, 180, 180)
        )
        self.screen.blit(slots_text, (x + width - int(150 * (width / 440)), y + int(10 * (height / 500))))

        # Список предметов
        if not all_items:
            empty_text = self.info_font.render("Инвентарь пуст", True, (150, 150, 150))
            empty_rect = empty_text.get_rect()
            empty_rect.centerx = x + width // 2
            empty_rect.y = y + int(100 * (height / 500))
            self.screen.blit(empty_text, empty_rect)
        else:
            items_y = y + int(40 * (height / 500))
            item_height = max(24, int(30 * (height / 500)))
            max_visible_items = max(10, int(14 * (height / 500)))
            start_index = max(0, self.selected_inventory_index - max_visible_items + 1)
            end_index = min(len(all_items), start_index + max_visible_items)

            # Адаптивные отступы
            margin_h = int(10 * (width / 440))
            margin_sides = int(20 * (width / 440))
            text_margin = int(20 * (width / 440))
            weight_offset = int(120 * (width / 440))
            value_offset = int(60 * (width / 440))

            for i in range(start_index, end_index):
                item, quantity = all_items[i]
                display_index = i - start_index

                # Цвет фона для выбранного предмета
                if i == self.selected_inventory_index:
                    pygame.draw.rect(
                        self.screen,
                        (80, 80, 100),
                        (x + margin_h, items_y + display_index * item_height, width - margin_sides, item_height - 2)
                    )

                # Рамка предмета
                if i == self.selected_inventory_index:
                    pygame.draw.rect(
                        self.screen,
                        (120, 150, 200),
                        (x + margin_h, items_y + display_index * item_height, width - margin_sides, item_height - 2),
                        2
                    )

                # Название и количество
                item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
                item_color = item.quality.color if hasattr(item, 'quality') else (200, 200, 200)

                # Показываем количество только для стакающихся предметов или если quantity > 1
                is_stackable = item.is_stackable if hasattr(item, 'is_stackable') else True
                display_name = f"{item_name} x{quantity}" if (is_stackable and quantity > 1) or (not is_stackable and quantity > 1) else item_name
                if quantity > 1:
                    display_name = f"{item_name} x{quantity}"
                else:
                    display_name = item_name

                # Используем цвет качества предмета всегда, даже для выделенного
                item_text = self.info_font.render(
                    display_name,
                    True,
                    item_color
                )
                self.screen.blit(item_text, (x + text_margin, items_y + display_index * item_height + int(7 * (height / 500))))

                # Вес
                weight_text = self.info_font.render(
                    f"{item.weight * quantity:.1f}кг",
                    True,
                    (150, 150, 150)
                )
                self.screen.blit(weight_text, (x + width - weight_offset, items_y + display_index * item_height + int(7 * (height / 500))))

                # Стоимость
                value_text = self.info_font.render(
                    f"{item.value}з",
                    True,
                    (255, 215, 0)
                )
                self.screen.blit(value_text, (x + width - value_offset, items_y + display_index * item_height + int(7 * (height / 500))))

    def render_item_tooltip(self, item, mouse_x, mouse_y, player=None, show_comparison=True):
        """
        Отрисовка всплывающей подсказки для предмета с возможным сравнением

        Args:
            item: Предмет для отображения
            mouse_x: X координата мыши
            mouse_y: Y координата мыши
            player: Игрок для сравнения с экипировкой
            show_comparison: Показывать ли окна сравнения (False для экипированных предметов)
        """
        from game.inventory import EquipmentItem, WeaponItem, ArmorItem, JewelryItem, PotionItem, EquipmentSlot

        # Размеры подсказки
        tooltip_width = 320
        tooltip_padding = 12
        line_height = 22

        # Собираем информацию о предмете
        lines = []

        # Название предмета
        item_name = item.get_full_name() if hasattr(item, 'get_full_name') else item.name
        item_color = item.quality.color if hasattr(item, 'quality') else (200, 200, 200)
        lines.append((item_name, item_color, True))  # True = жирный шрифт

        # Тип предмета
        if isinstance(item, WeaponItem):
            lines.append((f"Тип: {item.weapon_type}", (180, 180, 180), False))
        elif isinstance(item, ArmorItem):
            lines.append((f"Тип: {item.armor_type}", (180, 180, 180), False))
        elif isinstance(item, JewelryItem):
            # Определяем тип украшения по слоту
            from game.inventory import EquipmentSlot
            jewelry_types = {
                EquipmentSlot.RING_1: "Кольцо",
                EquipmentSlot.RING_2: "Кольцо",
                EquipmentSlot.RING_3: "Кольцо",
                EquipmentSlot.RING_4: "Кольцо",
                EquipmentSlot.AMULET: "Амулет",
                EquipmentSlot.BRACELET_1: "Браслет",
                EquipmentSlot.BRACELET_2: "Браслет",
            }
            jewelry_type = jewelry_types.get(item.slot, "Украшение")
            lines.append((f"Тип: {jewelry_type}", (180, 180, 180), False))
        elif isinstance(item, PotionItem):
            lines.append(("Тип: Зелье", (180, 180, 180), False))

        # УРОН И БРОНЯ СВЕРХУ (сразу после типа)
        if isinstance(item, EquipmentItem):
            if hasattr(item, 'attack') and item.attack > 0:
                lines.append((f"Урон: +{item.attack}", (255, 100, 100), False))
            if hasattr(item, 'defense') and item.defense > 0:
                lines.append((f"Броня: +{item.defense}", (100, 150, 255), False))

            lines.append(("", (0, 0, 0), False))  # Пустая строка

            # Бонусы к характеристикам
            if item.stats_bonus:
                for stat, bonus in item.stats_bonus.items():
                    if stat in ['damage', 'defense']:  # Пропускаем урон и защиту, они уже отображены
                        continue
                    stat_names = {
                        'strength': 'Сила',
                        'dexterity': 'Ловкость',
                        'constitution': 'Телосложение',
                        'spirit': 'Дух',
                        'intelligence': 'Интеллект',
                        'luck': 'Удача'
                    }
                    stat_name = stat_names.get(stat, stat)
                    actual_bonus = item.get_stat_bonus(stat)
                    lines.append((f"{stat_name}: +{actual_bonus}", (150, 255, 150), False))

            # Процентные бонусы к параметрам
            if hasattr(item, 'param_bonus') and item.param_bonus:
                for param, bonus in item.param_bonus.items():
                    param_names = {
                        'health': 'Здоровье',
                        'mana': 'Мана',
                        'stamina': 'Выносливость'
                    }
                    param_name = param_names.get(param, param)
                    lines.append((f"{param_name}: +{bonus}%", (100, 200, 255), False))

            # Бонусы к навыкам
            if hasattr(item, 'skill_bonus') and item.skill_bonus:
                # Словарь названий умений по ID с указанием типа оружия
                skill_names = {
                    'basic_attack': 'Базовая атака',
                    'power_strike': 'Мощный удар',
                    'poison_strike': 'Отравляющий удар',
                    'stun_strike': 'Оглушающий удар',
                    'battle_cry': 'Боевой клич',
                    'precise_shot': 'Точный выстрел (Лук)',
                    'rapid_fire': 'Скорострельность (Лук)',
                    'piercing_arrow': 'Пронзающая стрела (Лук)',
                    'backstab': 'Удар в спину (Нож)',
                    'bleeding_cut': 'Кровоточащий порез (Нож)',
                    'shadow_step': 'Шаг сквозь тень (Нож)',
                    'whirlwind_strike': 'Вихревой удар (Меч)',
                    'shield_breaker': 'Сокрушение щита (Меч)',
                    'blade_dance': 'Танец клинков (Меч)',
                    'heal': 'Исцеление',
                    'regeneration': 'Регенерация',
                    'stamina_recovery': 'Восстановление сил',
                    'mage_shield': 'Магический щит',
                    'fireball': 'Огненный шар',
                    'ice_bolt': 'Ледяная стрела',
                    'lightning': 'Молния',
                    'magic_missile': 'Магическая стрела',
                    'mining': 'Рудокопство',
                    'lumberjacking': 'Лесорубство'
                }
                for skill_id, bonus in item.skill_bonus.items():
                    skill_name = skill_names.get(skill_id, skill_id)
                    lines.append((f"Умение: {skill_name} [Ранг {bonus}]", (255, 200, 100), False))

        # Эффекты зелья
        if isinstance(item, PotionItem):
            lines.append(("", (0, 0, 0), False))
            if hasattr(item, 'health_restore') and item.health_restore > 0:
                lines.append((f"Восстановление HP: +{item.health_restore}", (100, 255, 100), False))
            if hasattr(item, 'mana_restore') and item.mana_restore > 0:
                lines.append((f"Восстановление маны: +{item.mana_restore}", (100, 150, 255), False))
            if hasattr(item, 'stamina_restore') and item.stamina_restore > 0:
                lines.append((f"Восстановление выносливости: +{item.stamina_restore}", (255, 255, 100), False))

        # Вес и стоимость
        lines.append(("", (0, 0, 0), False))
        lines.append((f"Вес: {item.weight:.1f} кг", (200, 200, 200), False))
        lines.append((f"Стоимость: {item.value} золота", (255, 215, 0), False))

        # Описание
        if hasattr(item, 'description') and item.description:
            lines.append(("", (0, 0, 0), False))
            lines.append((item.description, (150, 150, 150), False))

        # Максимальная ширина текста
        max_text_width = tooltip_width - tooltip_padding * 2

        # Обрабатываем перенос строк для длинных текстов
        wrapped_lines = []
        for line_text, line_color, is_bold in lines:
            if line_text == "":
                wrapped_lines.append((line_text, line_color, is_bold))
            else:
                font_to_use = self.font if is_bold else self.info_font
                # Проверяем, помещается ли текст
                test_surface = font_to_use.render(line_text, True, line_color)
                if test_surface.get_width() <= max_text_width:
                    wrapped_lines.append((line_text, line_color, is_bold))
                else:
                    # Переносим по словам
                    wrapped = UIHelper.wrap_text(line_text, font_to_use, max_text_width)
                    for wrapped_line in wrapped:
                        wrapped_lines.append((wrapped_line, line_color, is_bold))

        # Вычисляем высоту подсказки с учетом переносов
        actual_line_count = 0
        empty_line_count = 0
        for line_text, _, _ in wrapped_lines:
            if line_text == "":
                empty_line_count += 1
            else:
                actual_line_count += 1
        tooltip_height = tooltip_padding * 2 + actual_line_count * line_height + empty_line_count * (line_height // 2)

        # Позиция подсказки (справа от курсора, но в пределах экрана)
        tooltip_x = mouse_x + 15
        tooltip_y = mouse_y + 15

        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = mouse_x - tooltip_width - 15
        if tooltip_y + tooltip_height > screen_height:
            tooltip_y = screen_height - tooltip_height - 5

        # Фон подсказки с градиентом
        UIHelper.draw_gradient_rect(
            self.screen, tooltip_x, tooltip_y, tooltip_width, tooltip_height,
            (40, 40, 50), (60, 60, 75)
        )

        # Рамка
        pygame.draw.rect(
            self.screen,
            (150, 150, 200),
            (tooltip_x, tooltip_y, tooltip_width, tooltip_height),
            2
        )

        # Отрисовка текста
        text_y = tooltip_y + tooltip_padding
        for line_text, line_color, is_bold in wrapped_lines:
            if line_text == "":  # Пустая строка
                text_y += line_height // 2
                continue

            font_to_use = self.font if is_bold else self.info_font
            text_surface = font_to_use.render(line_text, True, line_color)
            self.screen.blit(text_surface, (tooltip_x + tooltip_padding, text_y))
            text_y += line_height

        # Отрисовка окон сравнения для экипируемых предметов (только если не наводим на экипировку)
        if player and isinstance(item, EquipmentItem) and show_comparison:
            self._render_comparison_tooltips(item, tooltip_x, tooltip_y, tooltip_width, tooltip_height, player)

    def _render_comparison_tooltips(self, item, main_tooltip_x, main_tooltip_y, main_width, main_height, player):
        """
        Отрисовка окон сравнения для экипируемых предметов

        Args:
            item: Предмет для сравнения
            main_tooltip_x, main_tooltip_y: Позиция основного tooltip
            main_width, main_height: Размеры основного tooltip
            player: Игрок
        """
        from game.inventory import EquipmentSlot, WeaponItem, ArmorItem, JewelryItem

        # Определяем слоты для сравнения
        comparison_slots = []
        if hasattr(item, 'slot'):
            slot = item.slot
            # Для колец и браслетов показываем все занятые слоты
            if slot in [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]:
                comparison_slots = [EquipmentSlot.RING_1, EquipmentSlot.RING_2, EquipmentSlot.RING_3, EquipmentSlot.RING_4]
            elif slot in [EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]:
                comparison_slots = [EquipmentSlot.BRACELET_1, EquipmentSlot.BRACELET_2]
            else:
                comparison_slots = [slot]

        # Собираем экипированные предметы для сравнения (только непустые слоты)
        equipped_items = []
        for comp_slot in comparison_slots:
            equipped = player.inventory.get_equipped_item(comp_slot)
            if equipped:
                equipped_items.append((comp_slot, equipped))

        if not equipped_items:
            return

        # Отрисовываем окна сравнения
        comp_width = 250
        comp_padding = 10
        line_height = 20
        screen_width = self.screen.get_width()

        # Позиция окон сравнения - слева от основного или справа
        comp_x = main_tooltip_x - comp_width - 10
        if comp_x < 5:
            comp_x = main_tooltip_x + main_width + 10
        if comp_x + comp_width > screen_width - 5:
            return  # Нет места для сравнения

        comp_y = main_tooltip_y

        for slot, equipped in equipped_items:
            lines = []

            # Заголовок
            slot_names = {
                EquipmentSlot.WEAPON: "Оружие",
                EquipmentSlot.HEAD: "Голова",
                EquipmentSlot.CHEST: "Торс",
                EquipmentSlot.HANDS: "Руки",
                EquipmentSlot.FEET: "Ноги",
                EquipmentSlot.RING_1: "Кольцо 1",
                EquipmentSlot.RING_2: "Кольцо 2",
                EquipmentSlot.RING_3: "Кольцо 3",
                EquipmentSlot.RING_4: "Кольцо 4",
                EquipmentSlot.AMULET: "Амулет",
                EquipmentSlot.BRACELET_1: "Браслет 1",
                EquipmentSlot.BRACELET_2: "Браслет 2",
            }
            lines.append((f"[{slot_names.get(slot, 'Слот')}]", (200, 200, 100), True))

            # Название экипированного предмета
            equipped_name = equipped.get_full_name() if hasattr(equipped, 'get_full_name') else equipped.name
            equipped_color = equipped.quality.color if hasattr(equipped, 'quality') else (200, 200, 200)
            lines.append((equipped_name[:25], equipped_color, False))
            lines.append(("", (0, 0, 0), False))

            # Сравнение характеристик
            # Урон
            item_attack = getattr(item, 'attack', 0)
            equip_attack = getattr(equipped, 'attack', 0)
            if item_attack or equip_attack:
                diff = item_attack - equip_attack
                diff_color = (100, 255, 100) if diff > 0 else ((255, 100, 100) if diff < 0 else (180, 180, 180))
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                lines.append((f"Урон: {diff_str}", diff_color, False))

            # Броня
            item_defense = getattr(item, 'defense', 0)
            equip_defense = getattr(equipped, 'defense', 0)
            if item_defense or equip_defense:
                diff = item_defense - equip_defense
                diff_color = (100, 255, 100) if diff > 0 else ((255, 100, 100) if diff < 0 else (180, 180, 180))
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                lines.append((f"Броня: {diff_str}", diff_color, False))

            # Бонусы к характеристикам
            stat_names = {
                'strength': 'Сила', 'dexterity': 'Ловкость', 'constitution': 'Телосл.',
                'spirit': 'Дух', 'intelligence': 'Интеллект', 'luck': 'Удача'
            }
            all_stats = set()
            if item.stats_bonus:
                all_stats.update(item.stats_bonus.keys())
            if equipped.stats_bonus:
                all_stats.update(equipped.stats_bonus.keys())

            for stat in all_stats:
                if stat in ['damage', 'defense']:
                    continue
                item_bonus = item.get_stat_bonus(stat) if hasattr(item, 'get_stat_bonus') else 0
                equip_bonus = equipped.get_stat_bonus(stat) if hasattr(equipped, 'get_stat_bonus') else 0
                diff = item_bonus - equip_bonus
                if diff != 0:
                    diff_color = (100, 255, 100) if diff > 0 else (255, 100, 100)
                    diff_str = f"+{diff}" if diff > 0 else str(diff)
                    lines.append((f"{stat_names.get(stat, stat)}: {diff_str}", diff_color, False))

            # Процентные бонусы к параметрам (важно для бижутерии)
            param_names = {
                'health': 'Здоровье', 'mana': 'Мана', 'stamina': 'Выносливость'
            }
            item_param_bonus = getattr(item, 'param_bonus', {}) or {}
            equip_param_bonus = getattr(equipped, 'param_bonus', {}) or {}
            all_params = set(item_param_bonus.keys()) | set(equip_param_bonus.keys())

            for param in all_params:
                item_pb = item_param_bonus.get(param, 0)
                equip_pb = equip_param_bonus.get(param, 0)
                diff = item_pb - equip_pb
                if diff != 0:
                    diff_color = (100, 255, 100) if diff > 0 else (255, 100, 100)
                    diff_str = f"+{diff}%" if diff > 0 else f"{diff}%"
                    lines.append((f"{param_names.get(param, param)}: {diff_str}", diff_color, False))

            # Вычисляем высоту
            comp_height = comp_padding * 2 + len(lines) * line_height

            # Фон сравнения
            UIHelper.draw_gradient_rect(
                self.screen, comp_x, comp_y, comp_width, comp_height,
                (50, 40, 40), (70, 55, 55)
            )
            pygame.draw.rect(self.screen, (150, 120, 120), (comp_x, comp_y, comp_width, comp_height), 2)

            # Текст
            text_y = comp_y + comp_padding
            for line_text, line_color, is_bold in lines:
                if line_text == "":
                    text_y += line_height // 2
                    continue
                font_to_use = self.font if is_bold else self.info_font
                text_surface = font_to_use.render(line_text, True, line_color)
                self.screen.blit(text_surface, (comp_x + comp_padding, text_y))
                text_y += line_height

            comp_y += comp_height + 5

    def get_item_at_mouse(self, player, mouse_x, mouse_y, check_equipment=False):
        """
        Получить предмет под курсором мыши

        Args:
            player: Объект игрока
            mouse_x: X координата мыши
            mouse_y: Y координата мыши
            check_equipment: Если True, проверяет только инвентарь (не экипировку)

        Returns:
            Item или None
        """
        # Проверяем слоты экипировки только если не отключено
        if not check_equipment:
            for slot, (rect, item) in self.equipment_slot_rects.items():
                if rect.collidepoint(mouse_x, mouse_y) and item:
                    return item

        # Получаем размеры экрана
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        # Размеры окна (адаптивные)
        if self.scaler:
            window_width = self.scaler.scale_width(900)
            window_height = self.scaler.scale_height(650)
        else:
            window_width = min(900, int(screen_width * 0.85))
            window_height = min(650, int(screen_height * 0.75))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Правая панель - предметы
        margin = int(20 * (window_width / 900))
        panel_y_offset = int(85 * (window_height / 650))
        inventory_panel_x = window_x + int(440 * (window_width / 900))
        inventory_panel_y = window_y + panel_y_offset
        inventory_panel_width = int(440 * (window_width / 900))
        inventory_panel_height = int(500 * (window_height / 650))

        # Проверяем, находится ли курсор в области предметов
        if not (inventory_panel_x <= mouse_x <= inventory_panel_x + inventory_panel_width and
                inventory_panel_y <= mouse_y <= inventory_panel_y + inventory_panel_height):
            return None

        # Вычисляем индекс предмета
        all_items = player.inventory.get_all_items()
        if not all_items:
            return None

        items_y = inventory_panel_y + int(40 * (inventory_panel_height / 500))
        item_height = max(24, int(30 * (inventory_panel_height / 500)))
        max_visible_items = max(10, int(14 * (inventory_panel_height / 500)))

        relative_y = mouse_y - items_y
        if relative_y < 0:
            return None

        item_index = int(relative_y / item_height)
        start_index = max(0, self.selected_inventory_index - max_visible_items + 1)
        actual_index = start_index + item_index

        if 0 <= actual_index < len(all_items):
            item, quantity = all_items[actual_index]
            return item

        return None

    def get_equipment_slot_at_mouse(self, mouse_x, mouse_y):
        """
        Получить слот экипировки под курсором мыши

        Args:
            mouse_x: X координата мыши
            mouse_y: Y координата мыши

        Returns:
            tuple: (EquipmentSlot, Item) или (None, None)
        """
        for slot, (rect, item) in self.equipment_slot_rects.items():
            if rect.collidepoint(mouse_x, mouse_y):
                return (slot, item)
        return (None, None)


