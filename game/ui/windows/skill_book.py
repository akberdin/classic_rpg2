"""
Окно книги умений.
"""
import pygame
from game.ui.base import UIHelper


class SkillBookWindow:
    """Окно книги умений для управления изученными умениями и их назначением в слоты"""

    def __init__(self, screen, font, info_font, ui_scaler=None, sprite_manager=None):
        """
        Инициализация окна книги умений

        Args:
            screen: Поверхность pygame для отрисовки
            font: Основной шрифт
            info_font: Шрифт для информации
            ui_scaler: Масштабировщик UI (опционально)
            sprite_manager: Менеджер спрайтов для иконок умений (опционально)
        """
        self.screen = screen
        self.font = font
        self.info_font = info_font
        self.ui_scaler = ui_scaler
        self.sprite_manager = sprite_manager

        # Индексы для навигации
        self.selected_skill_index = 0
        self.selected_slot_index = 0
        self.selected_tab = 0  # 0 - Боевые, 1 - Магические, 2 - Ремесленные

        # Для хранения координат элементов при рендеринге
        self.skill_rects = []  # Список прямоугольников умений
        self.slot_rects = []   # Список прямоугольников слотов
        self.tab_rects = []    # Список прямоугольников вкладок
        self.rank_up_rect = None  # Прямоугольник кнопки повышения ранга

    def handle_mouse_event(self, event, player):
        """
        Обработка событий мыши в окне книги умений

        Args:
            event: Событие pygame
            player: Объект игрока

        Returns:
            bool: True если событие обработано
        """
        import pygame
        from game.skills import SkillCategory

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Проверяем клик по вкладкам
            for i, rect in enumerate(self.tab_rects):
                if rect.collidepoint(mouse_pos):
                    if event.button == 1:  # Левая кнопка
                        self.selected_tab = i
                        self.selected_skill_index = 0
                    return True

            # Проверяем клик по кнопке повышения ранга
            if self.rank_up_rect and self.rank_up_rect.collidepoint(mouse_pos):
                if event.button == 1:  # Левая кнопка
                    categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
                    current_category = categories[self.selected_tab]
                    skills_dict = player.skill_manager.get_all_skills()
                    skills = [skill for skill in skills_dict.values() if skill.category == current_category]

                    if self.selected_skill_index < len(skills):
                        selected_skill = skills[self.selected_skill_index]
                        # Найдем ID умения
                        skill_id = None
                        for sid, skill in skills_dict.items():
                            if skill == selected_skill:
                                skill_id = sid
                                break

                        if skill_id:
                            success, message = player.skill_manager.try_rank_up_skill(skill_id, player)
                            print(message)
                return True

            # Проверяем клик по умениям
            for i, rect in enumerate(self.skill_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_skill_index = i

                    # Левая кнопка мыши - назначить умение в выбранный слот
                    if event.button == 1:
                        categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
                        current_category = categories[self.selected_tab]
                        skills_dict = player.skill_manager.get_all_skills()
                        skills = [skill for skill in skills_dict.values() if skill.category == current_category]

                        if i < len(skills):
                            selected_skill = skills[i]
                            # Найдем ID умения
                            skill_id = None
                            for sid, skill in skills_dict.items():
                                if skill == selected_skill:
                                    skill_id = sid
                                    break

                            if skill_id:
                                player.skill_manager.assign_to_slot(skill_id, self.selected_slot_index)

                    # Правая кнопка мыши - попытка повышения ранга
                    elif event.button == 3:
                        categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
                        current_category = categories[self.selected_tab]
                        skills_dict = player.skill_manager.get_all_skills()
                        skills = [skill for skill in skills_dict.values() if skill.category == current_category]

                        if i < len(skills):
                            selected_skill = skills[i]
                            # Найдем ID умения
                            skill_id = None
                            for sid, skill in skills_dict.items():
                                if skill == selected_skill:
                                    skill_id = sid
                                    break

                            if skill_id:
                                success, message = player.skill_manager.try_rank_up_skill(skill_id, player)
                                print(message)
                    return True

            # Проверяем клик по слотам
            for i, rect in enumerate(self.slot_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_slot_index = i

                    # Левая кнопка мыши - назначить выбранное умение в слот
                    if event.button == 1:
                        categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
                        current_category = categories[self.selected_tab]
                        skills_dict = player.skill_manager.get_all_skills()
                        skills = [skill for skill in skills_dict.values() if skill.category == current_category]

                        if self.selected_skill_index < len(skills):
                            selected_skill = skills[self.selected_skill_index]
                            # Найдем ID умения
                            skill_id = None
                            for sid, skill in skills_dict.items():
                                if skill == selected_skill:
                                    skill_id = sid
                                    break

                            if skill_id:
                                player.skill_manager.assign_to_slot(skill_id, i)

                    # Правая кнопка мыши - убрать умение из слота
                    elif event.button == 3:
                        player.skill_manager.unassign_from_slot(i)
                    return True

        # Обработка колёсика мыши для прокрутки умений
        elif event.type == pygame.MOUSEWHEEL:
            from game.skills import SkillCategory
            categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
            current_category = categories[self.selected_tab]
            skills_dict = player.skill_manager.get_all_skills()
            skills = [skill for skill in skills_dict.values() if skill.category == current_category]

            if event.y > 0:  # Прокрутка вверх
                self.selected_skill_index = max(0, self.selected_skill_index - 1)
            elif event.y < 0:  # Прокрутка вниз
                self.selected_skill_index = min(len(skills) - 1, self.selected_skill_index + 1)
            return True

        return False

    def render(self, player):
        """
        Отрисовать окно книги умений

        Args:
            player: Объект игрока
        """
        import pygame
        from game.skills import SkillCategory

        # Затемняем фон
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Размеры окна (адаптивные) - увеличено для 3 колонок
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        if self.ui_scaler:
            window_width = self.ui_scaler.scale_width(1500)
            window_height = self.ui_scaler.scale_height(800)
        else:
            window_width = min(1500, int(screen_width * 0.90))
            window_height = min(800, int(screen_height * 0.85))

        window_x = (screen_width - window_width) // 2
        window_y = (screen_height - window_height) // 2

        # Фон окна
        pygame.draw.rect(
            self.screen,
            (40, 40, 45),
            (window_x, window_y, window_width, window_height)
        )

        # Рамка окна
        pygame.draw.rect(
            self.screen,
            (200, 200, 200),
            (window_x, window_y, window_width, window_height),
            3
        )

        # Заголовок
        title_text = self.font.render(
            "КНИГА УМЕНИЙ",
            True,
            (255, 215, 0)
        )
        title_rect = title_text.get_rect()
        title_rect.centerx = window_x + window_width // 2
        title_rect.y = window_y + 15
        self.screen.blit(title_text, title_rect)

        # Вкладки категорий
        tabs = ["БОЕВЫЕ", "МАГИЧЕСКИЕ", "РЕМЕСЛЕННЫЕ"]
        tab_width = window_width // 3
        tab_height = 40
        tab_y = window_y + 60

        # Очищаем список прямоугольников вкладок
        self.tab_rects.clear()

        for i, tab_name in enumerate(tabs):
            tab_x = window_x + i * tab_width

            # Сохраняем прямоугольник вкладки для обработки мыши
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
            self.tab_rects.append(tab_rect)

            # Цвет вкладки
            if i == self.selected_tab:
                tab_color = (60, 60, 80)
                text_color = (255, 255, 100)
            else:
                tab_color = (30, 30, 35)
                text_color = (180, 180, 180)

            # Фон вкладки
            pygame.draw.rect(
                self.screen,
                tab_color,
                tab_rect
            )

            # Рамка вкладки
            pygame.draw.rect(
                self.screen,
                (100, 100, 100),
                tab_rect,
                2
            )

            # Текст вкладки
            tab_text = self.font.render(tab_name, True, text_color)
            tab_text_rect = tab_text.get_rect()
            tab_text_rect.center = (tab_x + tab_width // 2, tab_y + tab_height // 2)
            self.screen.blit(tab_text, tab_text_rect)

        # Получаем умения текущей категории
        categories = [SkillCategory.COMBAT, SkillCategory.MAGIC, SkillCategory.CRAFTING]
        current_category = categories[self.selected_tab]
        skills_dict = player.skill_manager.get_all_skills()
        skills = [skill for skill in skills_dict.values() if skill.category == current_category]

        # Область списка умений
        skills_list_y = tab_y + tab_height + 20
        skills_list_height = window_height - 230

        # Очищаем списки rect'ов
        self.skill_rects.clear()

        # Отрисовка списка умений в 3 колонки
        if skills:
            # Параметры колонок
            column_width = (window_width - 80) // 3  # Три колонки с отступами
            column_spacing = 20  # Расстояние между колонками
            skills_per_column = 5  # По 5 умений в каждой колонке
            skill_height = 100  # Высота карточки умения

            for idx, skill in enumerate(skills):
                # Максимум 15 умений (3 колонки по 5)
                if idx >= 15:
                    break

                # Определяем колонку и позицию в колонке
                column = idx // skills_per_column  # 0, 1 или 2
                row = idx % skills_per_column  # 0-4

                # Вычисляем позицию
                skill_x = window_x + 20 + column * (column_width + column_spacing)
                skill_y = skills_list_y + row * (skill_height + 10)

                # Сохраняем прямоугольник умения для обработки мыши
                skill_rect = pygame.Rect(skill_x, skill_y, column_width, skill_height - 5)
                self.skill_rects.append(skill_rect)

                # Фон умения
                if idx == self.selected_skill_index:
                    bg_color = (60, 60, 80)
                else:
                    bg_color = (45, 45, 50)

                pygame.draw.rect(
                    self.screen,
                    bg_color,
                    skill_rect
                )

                # Рамка умения
                pygame.draw.rect(
                    self.screen,
                    (100, 100, 100),
                    skill_rect,
                    2
                )

                # Название умения и ранг
                skill_name_text = self.font.render(
                    f"{skill.name} [Ранг {skill.rank}/{skill.max_rank}]",
                    True,
                    (255, 255, 255)
                )
                self.screen.blit(skill_name_text, (skill_x + 10, skill_y + 5))

                # Текущий эффект ранга (вместо базового описания) с переносом слов
                current_rank_desc = skill.get_current_rank_description() if hasattr(skill, 'get_current_rank_description') else skill.base_description
                # Переносим текст по словам
                desc_lines = UIHelper.wrap_text(current_rank_desc, self.info_font, column_width - 20)
                for line_idx, desc_line in enumerate(desc_lines[:2]):  # Показываем максимум 2 строки
                    skill_desc_text = self.info_font.render(
                        desc_line,
                        True,
                        (150, 255, 150)  # Зелёный цвет для текущего эффекта
                    )
                    self.screen.blit(skill_desc_text, (skill_x + 10, skill_y + 28 + line_idx * 16))

                # Прогресс до следующего ранга (компактная версия для колонок)
                info_y = skill_y + 60
                if skill.rank < skill.max_rank:
                    # Опыт и использования
                    cond_text1 = self.info_font.render(
                        f"Опыт: {skill.experience}/{skill.experience_to_next_rank} | Исп: {skill.use_count}/{skill.get_required_uses_for_rank()}",
                        True,
                        (180, 180, 180)
                    )
                    self.screen.blit(cond_text1, (skill_x + 10, info_y))

                    # Уровень и золото
                    cond_text2 = self.info_font.render(
                        f"Ур: {skill.get_required_player_level_for_rank()} | Золото: {skill.get_gold_cost_for_rank()}",
                        True,
                        (255, 200, 100)
                    )
                    self.screen.blit(cond_text2, (skill_x + 10, info_y + 16))
                else:
                    max_rank_text = self.info_font.render(
                        "МАКС. РАНГ",
                        True,
                        (255, 215, 0)
                    )
                    self.screen.blit(max_rank_text, (skill_x + 10, info_y))

                # Стоимость и перезарядка
                cost_parts = []
                if skill.mana_cost > 0:
                    cost_parts.append(f"MP:{skill.mana_cost}")
                if skill.stamina_cost > 0:
                    cost_parts.append(f"ST:{skill.stamina_cost}")
                if skill.cooldown > 0:
                    cost_parts.append(f"CD:{skill.cooldown}")

                if cost_parts:
                    cost_text = " ".join(cost_parts)
                    cost_render = self.info_font.render(cost_text, True, (150, 150, 200))
                    self.screen.blit(cost_render, (skill_x + column_width - 120, info_y + 16))
        else:
            # Нет умений в этой категории
            no_skills_text = self.font.render(
                "Нет изученных умений в этой категории",
                True,
                (150, 150, 150)
            )
            no_skills_rect = no_skills_text.get_rect()
            no_skills_rect.center = (window_x + window_width // 2, skills_list_y + 100)
            self.screen.blit(no_skills_text, no_skills_rect)

        # Панель слотов быстрого доступа внизу
        slots_panel_y = window_y + window_height - 100
        slot_size = 60
        slot_spacing = 10
        slots_start_x = window_x + (window_width - (slot_size + slot_spacing) * 8) // 2

        # Заголовок слотов
        slots_title = self.font.render("СЛОТЫ БЫСТРОГО ДОСТУПА (1-8)", True, (200, 200, 200))
        slots_title_rect = slots_title.get_rect()
        slots_title_rect.centerx = window_x + window_width // 2
        slots_title_rect.y = slots_panel_y - 30
        self.screen.blit(slots_title, slots_title_rect)

        # Очищаем список rect'ов слотов
        self.slot_rects.clear()

        # Отрисовка слотов
        for i in range(8):
            slot_x = slots_start_x + i * (slot_size + slot_spacing)
            slot_skill = player.skill_manager.get_slot_skill(i)

            # Сохраняем прямоугольник слота для обработки мыши
            slot_rect = pygame.Rect(slot_x, slots_panel_y, slot_size, slot_size)
            self.slot_rects.append(slot_rect)

            # Фон слота
            if i == self.selected_slot_index:
                bg_color = (80, 80, 100)
            elif slot_skill:
                if slot_skill.category == SkillCategory.COMBAT:
                    bg_color = (60, 40, 40)
                elif slot_skill.category == SkillCategory.MAGIC:
                    bg_color = (40, 40, 60)
                elif slot_skill.category == SkillCategory.CRAFTING:
                    bg_color = (50, 50, 40)
                else:
                    bg_color = (40, 40, 40)
            else:
                bg_color = (30, 30, 30)

            pygame.draw.rect(
                self.screen,
                bg_color,
                slot_rect
            )

            # Рамка слота
            pygame.draw.rect(
                self.screen,
                (150, 150, 150) if i == self.selected_slot_index else (100, 100, 100),
                slot_rect,
                3 if i == self.selected_slot_index else 2
            )

            # Номер слота
            slot_num_text = self.font.render(str(i + 1), True, (200, 200, 200))
            self.screen.blit(slot_num_text, (slot_x + 5, slots_panel_y + 5))

            # Если в слоте есть умение
            if slot_skill:
                skill_id = player.skill_manager.get_slot_skill_id(i)
                icon_size = slot_size - 10  # Немного меньше слота для отступов
                icon_x = slot_x + 5
                icon_y = slots_panel_y + 5

                # Пробуем отрисовать спрайт умения
                sprite_drawn = False
                if skill_id and self.sprite_manager:
                    sprite_drawn = self.sprite_manager.render_skill_icon(
                        self.screen,
                        skill_id,
                        icon_x,
                        icon_y,
                        icon_size,
                        fallback_text=slot_skill.name[0]
                    )

                if not sprite_drawn and not self.sprite_manager:
                    # Fallback: первая буква названия
                    icon_font = pygame.font.Font(None, 36)
                    icon_text = icon_font.render(slot_skill.name[0], True, (255, 255, 255))
                    icon_rect = icon_text.get_rect()
                    icon_rect.center = (slot_x + slot_size // 2, slots_panel_y + slot_size // 2)
                    self.screen.blit(icon_text, icon_rect)

        # Подсказки
        hints_y = window_y + window_height - 30
        hint_text = self.info_font.render(
            "ЛКМ - назначить/выбрать | ПКМ - повысить ранг/убрать | Колёсико - листать | K/ESC - закрыть",
            True,
            (180, 180, 180)
        )
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = window_x + window_width // 2
        hint_rect.y = hints_y
        self.screen.blit(hint_text, hint_rect)

        # Всплывающая подсказка при наведении на умение
        mouse_pos = pygame.mouse.get_pos()
        for i, rect in enumerate(self.skill_rects):
            if rect.collidepoint(mouse_pos) and i < len(skills):
                self._render_skill_tooltip(skills[i], mouse_pos)
                break

    def _render_skill_tooltip(self, skill, mouse_pos):
        """
        Отрисовать всплывающую подсказку с развитием умения по рангам

        Args:
            skill: Объект умения
            mouse_pos: Позиция мыши
        """
        import pygame

        # Получаем информацию о развитии по рангам
        progression_info = skill.get_rank_progression_info() if hasattr(skill, 'get_rank_progression_info') else []

        if not progression_info:
            return

        # Параметры подсказки
        tooltip_padding = 10
        line_height = 18
        tooltip_width = 450  # Увеличена ширина для лучшего отображения

        # Формируем строки подсказки
        lines = []
        lines.append((f"Развитие умения: {skill.name}", (255, 215, 0), True))
        lines.append(("", (0, 0, 0), False))  # Пустая строка

        # Описание с переносом слов
        lines.append(("Описание:", (200, 200, 255), True))
        desc_lines = UIHelper.wrap_text(skill.base_description, self.info_font, tooltip_width - tooltip_padding * 2)
        for desc_line in desc_lines:
            lines.append((desc_line, (180, 180, 180), False))

        # Информация о требуемом оружии
        lines.append(("", (0, 0, 0), False))  # Пустая строка
        if hasattr(skill, 'required_weapon_type') and skill.required_weapon_type is not None:
            weapon_name = skill.required_weapon_type.value[0]  # Получаем название из кортежа
            lines.append((f"Оружие: {weapon_name}", (255, 200, 100), False))
        else:
            lines.append(("Оружие: Любое", (200, 200, 200), False))

        lines.append(("", (0, 0, 0), False))  # Пустая строка
        lines.append(("Прогрессия по рангам:", (200, 200, 255), True))

        for i, rank_info in enumerate(progression_info):
            # Подсветка текущего ранга
            if i + 1 == skill.rank:
                lines.append((f"► {rank_info}", (100, 255, 100), False))
            else:
                lines.append((f"  {rank_info}", (180, 180, 180), False))

        # Добавляем информацию о стоимости
        lines.append(("", (0, 0, 0), False))
        cost_info = []
        if skill.mana_cost > 0:
            cost_info.append(f"Мана: {skill.mana_cost}")
        if skill.stamina_cost > 0:
            cost_info.append(f"Выносливость: {skill.stamina_cost}")
        if skill.cooldown > 0:
            cost_info.append(f"Перезарядка: {skill.cooldown}")
        if cost_info:
            lines.append((" | ".join(cost_info), (100, 200, 255), False))

        # Вычисляем размер подсказки
        tooltip_height = tooltip_padding * 2 + len(lines) * line_height

        # Позиция подсказки (справа от курсора)
        tooltip_x = mouse_pos[0] + 15
        tooltip_y = mouse_pos[1] + 15

        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = mouse_pos[0] - tooltip_width - 15
        if tooltip_y + tooltip_height > screen_height:
            tooltip_y = screen_height - tooltip_height - 5

        # Фон подсказки
        pygame.draw.rect(
            self.screen,
            (30, 30, 40),
            (tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        )

        # Рамка
        pygame.draw.rect(
            self.screen,
            (150, 150, 200),
            (tooltip_x, tooltip_y, tooltip_width, tooltip_height),
            2
        )

        # Отрисовка текста с переносом слов
        text_y = tooltip_y + tooltip_padding
        for line_text, line_color, is_bold in lines:
            if line_text:
                font_to_use = self.font if is_bold else self.info_font
                text_surface = font_to_use.render(line_text, True, line_color)
                self.screen.blit(text_surface, (tooltip_x + tooltip_padding, text_y))
            text_y += line_height


