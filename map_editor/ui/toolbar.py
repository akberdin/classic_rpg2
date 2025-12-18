"""Toolbar component for the map editor."""

import pygame
from typing import Dict, List, Tuple, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ToolType(Enum):
    """Available tool types."""
    SELECT = "select"
    BRUSH = "brush"
    FILL = "fill"
    OBJECT = "object"
    ERASER = "eraser"
    MOVE = "move"
    CONNECTION = "connection"


@dataclass
class ToolbarButton:
    """Toolbar button definition."""
    rect: pygame.Rect
    text: str
    tooltip: str
    action: str
    active: bool = False
    enabled: bool = True
    is_separator: bool = False


class Toolbar:
    """Top toolbar for the map editor with Russian labels."""

    def __init__(self, width: int, height: int, config: Dict[str, Any]):
        self.width = width
        self.height = height
        self.config = config

        # Colors from config
        ui_config = config.get('ui', {})
        self.bg_color = tuple(ui_config.get('panel_color', [45, 45, 48]))
        self.button_color = tuple(ui_config.get('button_color', [62, 62, 66]))
        self.button_hover = tuple(ui_config.get('button_hover_color', [80, 80, 85]))
        self.button_active = tuple(ui_config.get('button_active_color', [0, 122, 204]))
        self.text_color = tuple(ui_config.get('text_color', [255, 255, 255]))
        self.border_color = tuple(ui_config.get('border_color', [70, 70, 75]))
        self.separator_color = (80, 80, 85)

        # Font - use default pygame font for crisp rendering
        pygame.font.init()
        self.font = pygame.font.Font(None, 16)
        self.font_small = pygame.font.Font(None, 14)

        # Current state
        self.current_tool = ToolType.SELECT
        self.hovered_button: Optional[str] = None

        # Callbacks
        self.on_tool_change: Optional[Callable[[ToolType], None]] = None
        self.on_action: Optional[Callable[[str], None]] = None

        # Create buttons
        self.buttons: Dict[str, ToolbarButton] = {}
        self._create_buttons()

    def _create_buttons(self) -> None:
        """Create toolbar buttons with Russian text."""
        button_height = 32
        padding = 4
        x = padding
        y = (self.height - button_height) // 2

        # File operations group
        file_buttons = [
            ("Новая", "Новая карта (Ctrl+N)", "new", 55),
            ("Открыть", "Открыть файл (Ctrl+O)", "open", 60),
            ("Сохранить", "Сохранить (Ctrl+S)", "save", 70),
        ]

        for text, tooltip, action, btn_width in file_buttons:
            self.buttons[action] = ToolbarButton(
                rect=pygame.Rect(x, y, btn_width, button_height),
                text=text,
                tooltip=tooltip,
                action=action
            )
            x += btn_width + padding

        # Separator
        x += 8

        # Tool buttons group
        tool_buttons = [
            ("Выбор", "Инструмент выбора (V)", "tool_select", ToolType.SELECT, 50),
            ("Кисть", "Рисование биомов (B)", "tool_brush", ToolType.BRUSH, 50),
            ("Заливка", "Заливка области (G)", "tool_fill", ToolType.FILL, 55),
            ("Объекты", "Размещение объектов (O)", "tool_object", ToolType.OBJECT, 60),
            ("Удалить", "Удаление объектов (E)", "tool_eraser", ToolType.ERASER, 58),
            ("Двигать", "Перемещение объектов (M)", "tool_move", ToolType.MOVE, 55),
            ("Связи", "Создание связей между объектами (C)", "tool_connection", ToolType.CONNECTION, 50),
        ]

        for text, tooltip, action, tool_type, btn_width in tool_buttons:
            self.buttons[action] = ToolbarButton(
                rect=pygame.Rect(x, y, btn_width, button_height),
                text=text,
                tooltip=tooltip,
                action=action,
                active=(tool_type == self.current_tool)
            )
            x += btn_width + padding

        # Separator
        x += 8

        # Generation buttons group
        gen_buttons = [
            ("Генерация", "Настройки и генерация карты (F5)", "generate", 70),
            ("Новый seed", "Перегенерировать с новым seed (F6)", "regenerate", 75),
        ]

        for text, tooltip, action, btn_width in gen_buttons:
            self.buttons[action] = ToolbarButton(
                rect=pygame.Rect(x, y, btn_width, button_height),
                text=text,
                tooltip=tooltip,
                action=action
            )
            x += btn_width + padding

        # Separator
        x += 8

        # View buttons group
        view_buttons = [
            ("+", "Приблизить (+)", "zoom_in", 28),
            ("-", "Отдалить (-)", "zoom_out", 28),
            ("Вписать", "Вписать карту в экран (Home)", "fit_view", 55),
            ("Сетка", "Показать/скрыть сетку (Ctrl+G)", "toggle_grid", 50),
        ]

        for text, tooltip, action, btn_width in view_buttons:
            self.buttons[action] = ToolbarButton(
                rect=pygame.Rect(x, y, btn_width, button_height),
                text=text,
                tooltip=tooltip,
                action=action
            )
            x += btn_width + padding

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event. Returns True if event was consumed."""
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            self.hovered_button = None
            for name, button in self.buttons.items():
                if button.rect.collidepoint(mouse_pos) and button.enabled:
                    self.hovered_button = name
                    break
            return mouse_pos[1] < self.height

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                for name, button in self.buttons.items():
                    if button.rect.collidepoint(mouse_pos) and button.enabled:
                        self._handle_button_click(name, button)
                        return True

        elif event.type == pygame.KEYDOWN:
            return self._handle_hotkey(event)

        return False

    def _handle_button_click(self, name: str, button: ToolbarButton) -> None:
        """Handle button click."""
        action = button.action

        # Tool selection
        if action.startswith("tool_"):
            tool_map = {
                "tool_select": ToolType.SELECT,
                "tool_brush": ToolType.BRUSH,
                "tool_fill": ToolType.FILL,
                "tool_object": ToolType.OBJECT,
                "tool_eraser": ToolType.ERASER,
                "tool_move": ToolType.MOVE,
                "tool_connection": ToolType.CONNECTION
            }
            if action in tool_map:
                self.set_tool(tool_map[action])
        else:
            # Other actions
            if self.on_action:
                self.on_action(action)

    def _handle_hotkey(self, event: pygame.event.Event) -> bool:
        """Handle keyboard shortcuts."""
        mods = pygame.key.get_mods()
        ctrl = mods & pygame.KMOD_CTRL

        # Tool hotkeys (without Ctrl)
        if not ctrl:
            tool_keys = {
                pygame.K_v: ToolType.SELECT,
                pygame.K_b: ToolType.BRUSH,
                pygame.K_g: ToolType.FILL,
                pygame.K_o: ToolType.OBJECT,
                pygame.K_e: ToolType.ERASER,
                pygame.K_m: ToolType.MOVE,
                pygame.K_c: ToolType.CONNECTION
            }
            if event.key in tool_keys:
                self.set_tool(tool_keys[event.key])
                return True

        # File hotkeys (with Ctrl)
        if ctrl:
            if event.key == pygame.K_n:
                if self.on_action:
                    self.on_action("new")
                return True
            elif event.key == pygame.K_o:
                if self.on_action:
                    self.on_action("open")
                return True
            elif event.key == pygame.K_s:
                if self.on_action:
                    self.on_action("save")
                return True
            elif event.key == pygame.K_g:
                if self.on_action:
                    self.on_action("toggle_grid")
                return True

        # Generation hotkeys
        if event.key == pygame.K_F5:
            if self.on_action:
                self.on_action("generate")
            return True
        elif event.key == pygame.K_F6:
            if self.on_action:
                self.on_action("regenerate")
            return True

        # View hotkeys
        if event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS or event.key == pygame.K_EQUALS:
            if self.on_action:
                self.on_action("zoom_in")
            return True
        elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
            if self.on_action:
                self.on_action("zoom_out")
            return True
        elif event.key == pygame.K_HOME:
            if self.on_action:
                self.on_action("fit_view")
            return True

        return False

    def set_tool(self, tool: ToolType) -> None:
        """Set the current tool."""
        self.current_tool = tool

        # Update button states
        for name, button in self.buttons.items():
            if name.startswith("tool_"):
                tool_map = {
                    "tool_select": ToolType.SELECT,
                    "tool_brush": ToolType.BRUSH,
                    "tool_fill": ToolType.FILL,
                    "tool_object": ToolType.OBJECT,
                    "tool_eraser": ToolType.ERASER,
                    "tool_move": ToolType.MOVE,
                    "tool_connection": ToolType.CONNECTION
                }
                button.active = (tool_map.get(name) == tool)

        if self.on_tool_change:
            self.on_tool_change(tool)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the toolbar."""
        # Background
        pygame.draw.rect(surface, self.bg_color, (0, 0, self.width, self.height))
        pygame.draw.line(surface, self.border_color, (0, self.height - 1),
                        (self.width, self.height - 1))

        # Draw separators between button groups
        self._draw_separators(surface)

        # Buttons
        for name, button in self.buttons.items():
            self._draw_button(surface, name, button)

        # Tooltip
        if self.hovered_button:
            self._draw_tooltip(surface)

    def _draw_separators(self, surface: pygame.Surface) -> None:
        """Draw vertical separators between button groups."""
        # Find separator positions (after file, tools, generation groups)
        sep_positions = []

        # After file buttons (after "save")
        if "save" in self.buttons:
            sep_positions.append(self.buttons["save"].rect.right + 6)

        # After tool buttons (after "tool_connection")
        if "tool_connection" in self.buttons:
            sep_positions.append(self.buttons["tool_connection"].rect.right + 6)

        # After generation buttons (after "regenerate")
        if "regenerate" in self.buttons:
            sep_positions.append(self.buttons["regenerate"].rect.right + 6)

        # Draw separators
        for x in sep_positions:
            pygame.draw.line(surface, self.separator_color,
                           (x, 8), (x, self.height - 8))

    def _draw_button(self, surface: pygame.Surface, name: str, button: ToolbarButton) -> None:
        """Draw a single button."""
        # Determine color
        if not button.enabled:
            color = tuple(c // 2 for c in self.button_color)
        elif button.active:
            color = self.button_active
        elif name == self.hovered_button:
            color = self.button_hover
        else:
            color = self.button_color

        # Draw button background
        pygame.draw.rect(surface, color, button.rect, border_radius=4)

        # Draw text
        text_color = self.text_color if button.enabled else tuple(c // 2 for c in self.text_color)
        text_surface = self.font.render(button.text, True, text_color)
        text_rect = text_surface.get_rect(center=button.rect.center)
        surface.blit(text_surface, text_rect)

    def _draw_tooltip(self, surface: pygame.Surface) -> None:
        """Draw tooltip for hovered button."""
        if not self.hovered_button:
            return

        button = self.buttons.get(self.hovered_button)
        if not button:
            return

        # Render tooltip text
        tooltip_surface = self.font_small.render(button.tooltip, True, self.text_color)
        padding = 6

        # Position below button
        x = button.rect.x
        y = button.rect.bottom + 4

        # Background
        bg_rect = pygame.Rect(
            x - padding,
            y,
            tooltip_surface.get_width() + padding * 2,
            tooltip_surface.get_height() + padding * 2
        )

        # Keep on screen
        if bg_rect.right > self.width:
            bg_rect.right = self.width - 4
        if bg_rect.left < 4:
            bg_rect.left = 4

        pygame.draw.rect(surface, (30, 30, 32), bg_rect, border_radius=4)
        pygame.draw.rect(surface, self.border_color, bg_rect, width=1, border_radius=4)

        surface.blit(tooltip_surface, (bg_rect.x + padding, bg_rect.y + padding))

    def set_grid_active(self, active: bool) -> None:
        """Set the grid button active state."""
        if "toggle_grid" in self.buttons:
            self.buttons["toggle_grid"].active = active

    def resize(self, width: int) -> None:
        """Handle window resize."""
        self.width = width
