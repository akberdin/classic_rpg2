"""Sidebar component for the map editor."""

import pygame
from typing import Dict, List, Tuple, Callable, Optional, Any
from dataclasses import dataclass

from ..tools.brush import BrushSettings, BrushShape, BrushMode
from ..tools.generator import (
    BIOME_WATER, BIOME_SAND, BIOME_PLAINS, BIOME_FOREST,
    BIOME_HILLS, BIOME_MOUNTAIN, BIOME_SWAMP,
    LOCATION_CITY, LOCATION_CAPITAL, LOCATION_VILLAGE, LOCATION_MINE,
    LOCATION_BANDIT_CAMP, LOCATION_RUINS, LOCATION_MAGIC_SCHOOL,
    LOCATION_WARRIOR_ACADEMY, LOCATION_SECRET_CAMP,
    LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER
)
from .toolbar import ToolType


@dataclass
class SliderControl:
    """Slider UI control."""
    rect: pygame.Rect
    label: str
    value: float
    min_val: float
    max_val: float
    step: float = 1.0
    is_int: bool = True
    key: str = ""


class Sidebar:
    """Right sidebar for tool options and properties."""

    BIOME_NAMES = {
        BIOME_WATER: "Вода",
        BIOME_SAND: "Песок",
        BIOME_PLAINS: "Равнина",
        BIOME_FOREST: "Лес",
        BIOME_HILLS: "Холмы",
        BIOME_MOUNTAIN: "Горы",
        BIOME_SWAMP: "Болото"
    }

    LOCATION_NAMES = {
        LOCATION_CAPITAL: "Столица",
        LOCATION_CITY: "Город",
        LOCATION_VILLAGE: "Деревня",
        LOCATION_MINE: "Шахта",
        LOCATION_BANDIT_CAMP: "Лагерь разбойников",
        LOCATION_RUINS: "Руины",
        LOCATION_MAGIC_SCHOOL: "Школа магии",
        LOCATION_WARRIOR_ACADEMY: "Академия воинов",
        LOCATION_SECRET_CAMP: "Тайный лагерь"
    }

    SPAWN_NAMES = {
        LOCATION_SPAWN_WOLF: "Спавн: Волки",
        LOCATION_SPAWN_BEAR: "Спавн: Медведи",
        LOCATION_SPAWN_DEER: "Спавн: Олени"
    }

    def __init__(self, x: int, y: int, width: int, height: int, config: Dict[str, Any]):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.config = config

        # Colors
        ui_config = config.get('ui', {})
        self.bg_color = tuple(ui_config.get('panel_color', [45, 45, 48]))
        self.button_color = tuple(ui_config.get('button_color', [62, 62, 66]))
        self.button_hover = tuple(ui_config.get('button_hover_color', [80, 80, 85]))
        self.button_active = tuple(ui_config.get('button_active_color', [0, 122, 204]))
        self.text_color = tuple(ui_config.get('text_color', [255, 255, 255]))
        self.border_color = tuple(ui_config.get('border_color', [70, 70, 75]))

        # Biome colors
        biome_config = config.get('biomes', {})
        self.biome_colors = {}
        for biome, data in biome_config.items():
            self.biome_colors[biome] = tuple(data.get('color', [128, 128, 128]))

        # Location colors
        loc_config = config.get('locations', {})
        self.location_colors = {}
        for loc_type, data in loc_config.items():
            self.location_colors[loc_type] = tuple(data.get('color', [255, 255, 255]))

        # Font - use default pygame font for crisp rendering
        self.font = pygame.font.Font(None, 18)
        self.font_bold = pygame.font.Font(None, 18)
        self.font_large = pygame.font.Font(None, 22)

        # State
        self.current_tool = ToolType.SELECT
        self.brush_settings = BrushSettings()
        self.selected_biome = BIOME_PLAINS
        self.selected_location = LOCATION_VILLAGE
        self.scroll_offset = 0
        self.max_scroll = 0

        # UI elements
        self.hovered_element: Optional[str] = None
        self.active_slider: Optional[SliderControl] = None
        self.sliders: Dict[str, SliderControl] = {}

        # Callbacks
        self.on_biome_select: Optional[Callable[[str], None]] = None
        self.on_location_select: Optional[Callable[[str], None]] = None
        self.on_brush_change: Optional[Callable[[BrushSettings], None]] = None
        self.on_slider_change: Optional[Callable[[str, float], None]] = None
        self.on_edit_location: Optional[Callable[[Dict[str, Any]], None]] = None

        # Location info display
        self.location_info: Optional[Dict[str, Any]] = None

        # Edit button rect (stored for click detection)
        self._edit_button_rect: Optional[pygame.Rect] = None

    def set_tool(self, tool: ToolType) -> None:
        """Set the current tool to display appropriate options."""
        self.current_tool = tool
        self.scroll_offset = 0

    def set_brush_settings(self, settings: BrushSettings) -> None:
        """Update brush settings."""
        self.brush_settings = settings

    def set_location_info(self, info: Optional[Dict[str, Any]]) -> None:
        """Set location info for display."""
        self.location_info = info

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event. Returns True if event was consumed."""
        # Adjust mouse position relative to sidebar
        if hasattr(event, 'pos'):
            if event.pos[0] < self.x:
                return False

        if event.type == pygame.MOUSEMOTION:
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            self.hovered_element = None

            # Handle slider dragging
            if self.active_slider:
                self._update_slider_value(event.pos[0])
                return True

            return event.pos[0] >= self.x

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.pos[0] < self.x:
                return False

            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            if event.button == 1:  # Left click
                return self._handle_click(local_x, local_y)
            elif event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 20)
                return True
            elif event.button == 5:  # Scroll down
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 20)
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.active_slider:
                self.active_slider = None
                return True

        return False

    def _handle_click(self, local_x: int, local_y: int) -> bool:
        """Handle click within sidebar."""
        # Check edit button click first (available in multiple modes)
        if self._edit_button_rect and self._edit_button_rect.collidepoint(local_x, local_y):
            if self.on_edit_location and self.location_info:
                self.on_edit_location(self.location_info)
            return True

        if self.current_tool == ToolType.BRUSH:
            return self._handle_brush_click(local_x, local_y)
        elif self.current_tool == ToolType.OBJECT:
            return self._handle_object_click(local_x, local_y)
        elif self.current_tool == ToolType.FILL:
            return self._handle_brush_click(local_x, local_y)
        elif self.current_tool == ToolType.SELECT:
            return self._handle_select_click(local_x, local_y)
        return True

    def _handle_select_click(self, local_x: int, local_y: int) -> bool:
        """Handle click in select mode."""
        # Edit button is handled above
        return True

    def _handle_brush_click(self, local_x: int, local_y: int) -> bool:
        """Handle click in brush mode."""
        # Match y_offset to _draw_brush_panel layout
        y_offset = 10  # Start same as draw method
        y_offset += 30  # After section header (returns y + 30)
        button_height = 28
        padding = 4

        for biome in self.BIOME_NAMES.keys():
            btn_rect = pygame.Rect(padding, y_offset, self.width - padding * 2, button_height)
            if btn_rect.collidepoint(local_x, local_y):
                self.selected_biome = biome
                self.brush_settings.biome = biome
                if self.on_biome_select:
                    self.on_biome_select(biome)
                if self.on_brush_change:
                    self.on_brush_change(self.brush_settings)
                return True
            y_offset += button_height + padding

        # Check brush size buttons (after 10px gap + section header)
        y_offset += 10
        y_offset += 30  # Section header
        sizes = self.config.get('brushes', {}).get('sizes', [1, 3, 5, 10, 15, 20])
        btn_width = (self.width - padding * (len(sizes) + 1)) // len(sizes)

        for i, size in enumerate(sizes):
            btn_x = padding + i * (btn_width + padding)
            btn_rect = pygame.Rect(btn_x, y_offset, btn_width, button_height)
            if btn_rect.collidepoint(local_x, local_y):
                self.brush_settings.size = size
                if self.on_brush_change:
                    self.on_brush_change(self.brush_settings)
                return True

        # Check brush shape buttons (after button + 10px gap + section header)
        y_offset += button_height + padding
        y_offset += 10
        y_offset += 30  # Section header
        shapes = [BrushShape.CIRCLE, BrushShape.SQUARE, BrushShape.DIAMOND]
        btn_width = (self.width - padding * 4) // 3

        for i, shape in enumerate(shapes):
            btn_x = padding + i * (btn_width + padding)
            btn_rect = pygame.Rect(btn_x, y_offset, btn_width, button_height)
            if btn_rect.collidepoint(local_x, local_y):
                self.brush_settings.shape = shape
                if self.on_brush_change:
                    self.on_brush_change(self.brush_settings)
                return True

        # Check brush mode buttons (after button + 10px gap + section header)
        y_offset += button_height + padding
        y_offset += 10
        y_offset += 30  # Section header
        modes = [BrushMode.PAINT, BrushMode.SMOOTH, BrushMode.RAISE, BrushMode.LOWER]
        btn_width = (self.width - padding * 5) // 4

        for i, mode in enumerate(modes):
            btn_x = padding + i * (btn_width + padding)
            btn_rect = pygame.Rect(btn_x, y_offset, btn_width, button_height)
            if btn_rect.collidepoint(local_x, local_y):
                self.brush_settings.mode = mode
                if self.on_brush_change:
                    self.on_brush_change(self.brush_settings)
                return True

        return True

    def _handle_object_click(self, local_x: int, local_y: int) -> bool:
        """Handle click in object mode."""
        # Match y_offset to _draw_object_panel layout
        y_offset = 10  # Start same as draw method
        y_offset += 30  # After section header
        button_height = 28
        padding = 4

        # Check location type buttons
        for loc_type in self.LOCATION_NAMES.keys():
            btn_rect = pygame.Rect(padding, y_offset, self.width - padding * 2, button_height)
            if btn_rect.collidepoint(local_x, local_y):
                self.selected_location = loc_type
                if self.on_location_select:
                    self.on_location_select(loc_type)
                return True
            y_offset += button_height + padding

        # Check spawn point buttons
        y_offset += 10  # Gap before spawn section
        y_offset += 30  # Section header

        for loc_type in self.SPAWN_NAMES.keys():
            btn_rect = pygame.Rect(padding, y_offset, self.width - padding * 2, button_height)
            if btn_rect.collidepoint(local_x, local_y):
                self.selected_location = loc_type
                if self.on_location_select:
                    self.on_location_select(loc_type)
                return True
            y_offset += button_height + padding

        return True

    def _update_slider_value(self, mouse_x: int) -> None:
        """Update active slider value based on mouse position."""
        if not self.active_slider:
            return

        slider = self.active_slider
        rel_x = mouse_x - self.x - slider.rect.x
        ratio = max(0, min(1, rel_x / slider.rect.width))

        raw_value = slider.min_val + ratio * (slider.max_val - slider.min_val)

        # Apply step
        if slider.step > 0:
            raw_value = round(raw_value / slider.step) * slider.step

        if slider.is_int:
            raw_value = int(raw_value)

        slider.value = raw_value

        if self.on_slider_change:
            self.on_slider_change(slider.key, slider.value)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the sidebar."""
        # Background
        pygame.draw.rect(surface, self.bg_color,
                        (self.x, self.y, self.width, self.height))
        pygame.draw.line(surface, self.border_color,
                        (self.x, self.y), (self.x, self.y + self.height))

        # Create clipping surface
        clip_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Draw content based on current tool
        if self.current_tool == ToolType.BRUSH or self.current_tool == ToolType.FILL:
            self._draw_brush_panel(clip_surface)
        elif self.current_tool == ToolType.OBJECT:
            self._draw_object_panel(clip_surface)
        elif self.current_tool == ToolType.SELECT:
            self._draw_select_panel(clip_surface)
        else:
            self._draw_default_panel(clip_surface)

        # Blit clipped content
        surface.blit(clip_surface, (self.x, self.y))

    def _draw_section_header(self, surface: pygame.Surface, text: str, y: int) -> int:
        """Draw section header and return new y position."""
        text_surface = self.font_large.render(text, True, self.text_color)
        surface.blit(text_surface, (8, y))
        pygame.draw.line(surface, self.border_color,
                        (8, y + 20), (self.width - 8, y + 20))
        return y + 30

    def _draw_brush_panel(self, surface: pygame.Surface) -> None:
        """Draw brush tool options."""
        y_offset = 10

        # Section: Biomes
        y_offset = self._draw_section_header(surface, "Биомы", y_offset)

        button_height = 28
        padding = 4

        for biome, name in self.BIOME_NAMES.items():
            btn_rect = pygame.Rect(padding, y_offset, self.width - padding * 2, button_height)

            # Button color
            if biome == self.selected_biome:
                color = self.button_active
            else:
                color = self.button_color

            pygame.draw.rect(surface, color, btn_rect, border_radius=4)

            # Biome color indicator
            biome_color = self.biome_colors.get(biome, (128, 128, 128))
            indicator_rect = pygame.Rect(btn_rect.x + 4, btn_rect.y + 4,
                                        20, btn_rect.height - 8)
            pygame.draw.rect(surface, biome_color, indicator_rect, border_radius=2)

            # Text
            text_surface = self.font.render(name, True, self.text_color)
            surface.blit(text_surface, (btn_rect.x + 30, btn_rect.y + 7))

            y_offset += button_height + padding

        # Section: Brush Size
        y_offset += 10
        y_offset = self._draw_section_header(surface, "Размер кисти", y_offset)

        sizes = self.config.get('brushes', {}).get('sizes', [1, 3, 5, 10, 15, 20])
        btn_width = (self.width - padding * (len(sizes) + 1)) // len(sizes)

        for i, size in enumerate(sizes):
            btn_x = padding + i * (btn_width + padding)
            btn_rect = pygame.Rect(btn_x, y_offset, btn_width, button_height)

            color = self.button_active if size == self.brush_settings.size else self.button_color
            pygame.draw.rect(surface, color, btn_rect, border_radius=4)

            text_surface = self.font.render(str(size), True, self.text_color)
            text_rect = text_surface.get_rect(center=btn_rect.center)
            surface.blit(text_surface, text_rect)

        y_offset += button_height + padding

        # Section: Brush Shape
        y_offset += 10
        y_offset = self._draw_section_header(surface, "Форма кисти", y_offset)

        shapes = [
            (BrushShape.CIRCLE, "O"),
            (BrushShape.SQUARE, "[]"),
            (BrushShape.DIAMOND, "<>")
        ]
        btn_width = (self.width - padding * 4) // 3

        for i, (shape, icon) in enumerate(shapes):
            btn_x = padding + i * (btn_width + padding)
            btn_rect = pygame.Rect(btn_x, y_offset, btn_width, button_height)

            color = self.button_active if shape == self.brush_settings.shape else self.button_color
            pygame.draw.rect(surface, color, btn_rect, border_radius=4)

            text_surface = self.font.render(icon, True, self.text_color)
            text_rect = text_surface.get_rect(center=btn_rect.center)
            surface.blit(text_surface, text_rect)

        y_offset += button_height + padding

        # Section: Brush Mode
        y_offset += 10
        y_offset = self._draw_section_header(surface, "Режим", y_offset)

        modes = [
            (BrushMode.PAINT, "P"),
            (BrushMode.SMOOTH, "S"),
            (BrushMode.RAISE, "+"),
            (BrushMode.LOWER, "-")
        ]
        btn_width = (self.width - padding * 5) // 4

        for i, (mode, icon) in enumerate(modes):
            btn_x = padding + i * (btn_width + padding)
            btn_rect = pygame.Rect(btn_x, y_offset, btn_width, button_height)

            color = self.button_active if mode == self.brush_settings.mode else self.button_color
            pygame.draw.rect(surface, color, btn_rect, border_radius=4)

            text_surface = self.font.render(icon, True, self.text_color)
            text_rect = text_surface.get_rect(center=btn_rect.center)
            surface.blit(text_surface, text_rect)

        self.max_scroll = max(0, y_offset + 50 - self.height)

    def _draw_object_panel(self, surface: pygame.Surface) -> None:
        """Draw object placement options."""
        y_offset = 10

        # Section: Location Types
        y_offset = self._draw_section_header(surface, "Типы локаций", y_offset)

        button_height = 28
        padding = 4

        for loc_type, name in self.LOCATION_NAMES.items():
            btn_rect = pygame.Rect(padding, y_offset, self.width - padding * 2, button_height)

            color = self.button_active if loc_type == self.selected_location else self.button_color
            pygame.draw.rect(surface, color, btn_rect, border_radius=4)

            # Location color indicator
            loc_color = self.location_colors.get(loc_type, (255, 255, 255))
            indicator_rect = pygame.Rect(btn_rect.x + 4, btn_rect.y + 4,
                                        20, btn_rect.height - 8)
            pygame.draw.rect(surface, loc_color, indicator_rect, border_radius=2)

            # Text
            text_surface = self.font.render(name, True, self.text_color)
            surface.blit(text_surface, (btn_rect.x + 30, btn_rect.y + 7))

            y_offset += button_height + padding

        # Section: Spawn Points
        y_offset += 10
        y_offset = self._draw_section_header(surface, "Точки спавна", y_offset)

        for loc_type, name in self.SPAWN_NAMES.items():
            btn_rect = pygame.Rect(padding, y_offset, self.width - padding * 2, button_height)

            color = self.button_active if loc_type == self.selected_location else self.button_color
            pygame.draw.rect(surface, color, btn_rect, border_radius=4)

            # Spawn point color indicator (use a distinct color - red tones)
            spawn_color = self.location_colors.get(loc_type, (200, 50, 50))
            indicator_rect = pygame.Rect(btn_rect.x + 4, btn_rect.y + 4,
                                        20, btn_rect.height - 8)
            pygame.draw.rect(surface, spawn_color, indicator_rect, border_radius=2)

            # Text
            text_surface = self.font.render(name, True, self.text_color)
            surface.blit(text_surface, (btn_rect.x + 30, btn_rect.y + 7))

            y_offset += button_height + padding

        # Section: Selected Location Info
        if self.location_info:
            y_offset += 10
            y_offset = self._draw_section_header(surface, "Выбранная локация", y_offset)

            loc_type = self.location_info.get('type', '')
            info_lines = [
                f"Тип: {self.location_info.get('type_display', '')}",
                f"Имя: {self.location_info.get('name', '')}",
                f"X: {self.location_info.get('x', 0)}",
                f"Y: {self.location_info.get('y', 0)}"
            ]

            # Show rank for mines and ruins
            if loc_type in [LOCATION_MINE, LOCATION_RUINS]:
                info_lines.append(f"Ранг: {self.location_info.get('rank', 1)}")

            # Show shop_rank for settlements
            if loc_type in [LOCATION_CITY, LOCATION_CAPITAL, LOCATION_VILLAGE]:
                info_lines.append(f"Ранг магазина: {self.location_info.get('shop_rank', 1)}")

            # Show spawn_radius for all locations
            info_lines.append(f"Радиус спавна: {self.location_info.get('spawn_radius', 5)}")

            if self.location_info.get('is_starting'):
                info_lines.append("(Стартовая деревня)")

            for line in info_lines:
                text_surface = self.font.render(line, True, self.text_color)
                surface.blit(text_surface, (8, y_offset))
                y_offset += 18

        self.max_scroll = max(0, y_offset + 50 - self.height)

    def _draw_select_panel(self, surface: pygame.Surface) -> None:
        """Draw selection tool info."""
        y_offset = 10
        self._edit_button_rect = None  # Reset edit button rect

        y_offset = self._draw_section_header(surface, "Информация", y_offset)

        lines = [
            "Инструмент выбора",
            "",
            "ЛКМ - выбрать локацию",
            "ПКМ - информация",
            "Двойной клик - редактировать",
            "Колесо - масштаб",
            "СКМ - перемещение"
        ]

        for line in lines:
            text_surface = self.font.render(line, True, self.text_color)
            surface.blit(text_surface, (8, y_offset))
            y_offset += 18

        # Show location info if selected
        if self.location_info:
            y_offset += 10
            y_offset = self._draw_section_header(surface, "Выбранная локация", y_offset)

            info_lines = [
                f"Тип: {self.location_info.get('type_display', '')}",
                f"Имя: {self.location_info.get('name', '')}",
                f"Координаты: ({self.location_info.get('x', 0)}, {self.location_info.get('y', 0)})",
                f"Радиус спавна: {self.location_info.get('spawn_radius', 5)}"
            ]

            if self.location_info.get('is_starting'):
                info_lines.append("(Стартовая деревня)")

            for line in info_lines:
                text_surface = self.font.render(line, True, self.text_color)
                surface.blit(text_surface, (8, y_offset))
                y_offset += 18

            # Show connections if any
            connections = self.location_info.get('connections', [])
            if connections:
                y_offset += 5
                y_offset = self._draw_section_header(surface, "Связи", y_offset)

                for target_x, target_y in connections:
                    conn_text = f"→ ({target_x}, {target_y})"
                    text_surface = self.font.render(conn_text, True, (100, 200, 255))
                    surface.blit(text_surface, (8, y_offset))
                    y_offset += 18
            else:
                y_offset += 5
                text_surface = self.font.render("Нет связей", True, (150, 150, 150))
                surface.blit(text_surface, (8, y_offset))
                y_offset += 18

            # Edit button
            y_offset += 10
            btn_rect = pygame.Rect(8, y_offset, self.width - 16, 30)
            self._edit_button_rect = btn_rect

            pygame.draw.rect(surface, self.button_active, btn_rect, border_radius=4)
            edit_text = self.font_bold.render("Редактировать", True, self.text_color)
            text_rect = edit_text.get_rect(center=btn_rect.center)
            surface.blit(edit_text, text_rect)
            y_offset += 40

    def _draw_default_panel(self, surface: pygame.Surface) -> None:
        """Draw default panel when no specific tool is selected."""
        y_offset = 10
        y_offset = self._draw_section_header(surface, "Редактор карт", y_offset)

        lines = [
            "Выберите инструмент",
            "на панели инструментов",
            "",
            "Горячие клавиши:",
            "V - Выбор",
            "B - Кисть",
            "G - Заливка",
            "O - Объекты",
            "E - Ластик",
            "M - Перемещение",
            "C - Связи"
        ]

        for line in lines:
            text_surface = self.font.render(line, True, self.text_color)
            surface.blit(text_surface, (8, y_offset))
            y_offset += 18

    def resize(self, x: int, y: int, width: int, height: int) -> None:
        """Handle window resize."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
