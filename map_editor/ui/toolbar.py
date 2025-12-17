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


@dataclass
class Button:
    """Toolbar button definition."""
    rect: pygame.Rect
    icon: str
    tooltip: str
    action: str
    active: bool = False
    enabled: bool = True
    hotkey: Optional[str] = None


class Toolbar:
    """Top toolbar for the map editor."""

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

        # Font
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 12)
        self.icon_font = pygame.font.SysFont('Segoe UI Symbol', 16)

        # Current state
        self.current_tool = ToolType.SELECT
        self.hovered_button: Optional[str] = None

        # Callbacks
        self.on_tool_change: Optional[Callable[[ToolType], None]] = None
        self.on_action: Optional[Callable[[str], None]] = None

        # Create buttons
        self.buttons: Dict[str, Button] = {}
        self._create_buttons()

    def _create_buttons(self) -> None:
        """Create toolbar buttons."""
        button_size = 36
        padding = 4
        x = padding

        # File operations
        file_buttons = [
            ("new", "Новая карта (Ctrl+N)", "new"),
            ("open", "Открыть (Ctrl+O)", "open"),
            ("save", "Сохранить (Ctrl+S)", "save"),
            ("save_as", "Сохранить как...", "save_as"),
        ]

        for icon, tooltip, action in file_buttons:
            self.buttons[action] = Button(
                rect=pygame.Rect(x, padding, button_size, button_size),
                icon=self._get_icon(action),
                tooltip=tooltip,
                action=action
            )
            x += button_size + padding

        x += padding * 2  # Separator

        # Tool buttons
        tool_buttons = [
            ("select", "Выбор (V)", "tool_select", ToolType.SELECT),
            ("brush", "Кисть (B)", "tool_brush", ToolType.BRUSH),
            ("fill", "Заливка (G)", "tool_fill", ToolType.FILL),
            ("object", "Объекты (O)", "tool_object", ToolType.OBJECT),
            ("eraser", "Ластик (E)", "tool_eraser", ToolType.ERASER),
            ("move", "Перемещение (M)", "tool_move", ToolType.MOVE),
        ]

        for icon, tooltip, action, tool_type in tool_buttons:
            self.buttons[action] = Button(
                rect=pygame.Rect(x, padding, button_size, button_size),
                icon=self._get_icon(icon),
                tooltip=tooltip,
                action=action,
                active=(tool_type == self.current_tool)
            )
            x += button_size + padding

        x += padding * 2  # Separator

        # Generation buttons
        gen_buttons = [
            ("generate", "Генерировать (F5)", "generate"),
            ("regenerate", "Перегенерировать (F6)", "regenerate"),
            ("settings", "Настройки генератора", "gen_settings"),
        ]

        for icon, tooltip, action in gen_buttons:
            self.buttons[action] = Button(
                rect=pygame.Rect(x, padding, button_size, button_size),
                icon=self._get_icon(icon),
                tooltip=tooltip,
                action=action
            )
            x += button_size + padding

        x += padding * 2  # Separator

        # View buttons
        view_buttons = [
            ("zoom_in", "Приблизить (+)", "zoom_in"),
            ("zoom_out", "Отдалить (-)", "zoom_out"),
            ("fit", "Вписать (Home)", "fit_view"),
            ("grid", "Сетка (Ctrl+G)", "toggle_grid"),
        ]

        for icon, tooltip, action in view_buttons:
            self.buttons[action] = Button(
                rect=pygame.Rect(x, padding, button_size, button_size),
                icon=self._get_icon(icon),
                tooltip=tooltip,
                action=action
            )
            x += button_size + padding

    def _get_icon(self, icon_type: str) -> str:
        """Get icon character for button type."""
        icons = {
            "new": "+",
            "open": "O",
            "save": "S",
            "save_as": "SA",
            "select": "V",
            "brush": "B",
            "fill": "G",
            "object": "OB",
            "eraser": "E",
            "move": "M",
            "generate": "GN",
            "regenerate": "RG",
            "settings": "ST",
            "zoom_in": "+",
            "zoom_out": "-",
            "fit": "F",
            "grid": "#"
        }
        return icons.get(icon_type, "?")

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

    def _handle_button_click(self, name: str, button: Button) -> None:
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
                "tool_move": ToolType.MOVE
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

        # Tool hotkeys
        if not ctrl:
            tool_keys = {
                pygame.K_v: ToolType.SELECT,
                pygame.K_b: ToolType.BRUSH,
                pygame.K_g: ToolType.FILL,
                pygame.K_o: ToolType.OBJECT,
                pygame.K_e: ToolType.ERASER,
                pygame.K_m: ToolType.MOVE
            }
            if event.key in tool_keys:
                self.set_tool(tool_keys[event.key])
                return True

        # File hotkeys
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
        if event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
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
                    "tool_move": ToolType.MOVE
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

        # Buttons
        for name, button in self.buttons.items():
            self._draw_button(surface, name, button)

        # Tooltip
        if self.hovered_button:
            self._draw_tooltip(surface)

    def _draw_button(self, surface: pygame.Surface, name: str, button: Button) -> None:
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

        # Draw icon
        text_color = self.text_color if button.enabled else tuple(c // 2 for c in self.text_color)
        icon_surface = self.font.render(button.icon, True, text_color)
        icon_rect = icon_surface.get_rect(center=button.rect.center)
        surface.blit(icon_surface, icon_rect)

    def _draw_tooltip(self, surface: pygame.Surface) -> None:
        """Draw tooltip for hovered button."""
        if not self.hovered_button:
            return

        button = self.buttons.get(self.hovered_button)
        if not button:
            return

        # Render tooltip text
        tooltip_surface = self.font.render(button.tooltip, True, self.text_color)
        padding = 4

        # Position below button
        x = button.rect.x
        y = button.rect.bottom + 4

        # Background
        bg_rect = pygame.Rect(
            x - padding,
            y - padding,
            tooltip_surface.get_width() + padding * 2,
            tooltip_surface.get_height() + padding * 2
        )

        # Keep on screen
        if bg_rect.right > self.width:
            bg_rect.right = self.width - 4

        pygame.draw.rect(surface, self.bg_color, bg_rect, border_radius=2)
        pygame.draw.rect(surface, self.border_color, bg_rect, width=1, border_radius=2)

        surface.blit(tooltip_surface, (bg_rect.x + padding, bg_rect.y + padding))

    def resize(self, width: int) -> None:
        """Handle window resize."""
        self.width = width
