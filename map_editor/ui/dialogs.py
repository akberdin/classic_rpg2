"""Dialog windows for the map editor."""

import pygame
from typing import Dict, List, Tuple, Callable, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from ..tools.generator import (
    GeneratorParams,
    LOCATION_CITY, LOCATION_CAPITAL, LOCATION_VILLAGE,
    LOCATION_MINE, LOCATION_RUINS,
    LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY,
    LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER,
    Guard, GUARD_TYPES, GUARD_NONE,
    RESOURCE_TYPES,
    Merchant, MerchantWaypoint, MERCHANT_RANKS
)


@dataclass
class DialogButton:
    """Button in a dialog."""
    rect: pygame.Rect
    text: str
    action: str
    primary: bool = False


@dataclass
class DialogSlider:
    """Slider control in a dialog."""
    rect: pygame.Rect
    label: str
    key: str
    value: float
    min_val: float
    max_val: float
    step: float = 1.0
    is_int: bool = True


@dataclass
class DialogCheckbox:
    """Checkbox control in a dialog."""
    rect: pygame.Rect
    label: str
    key: str
    checked: bool = False


@dataclass
class DialogTextInput:
    """Text input control in a dialog."""
    rect: pygame.Rect
    label: str
    key: str
    value: str = ""
    max_length: int = 50
    active: bool = False


@dataclass
class DialogDropdown:
    """Dropdown/combobox control in a dialog."""
    rect: pygame.Rect
    label: str
    key: str
    options: Dict[str, str]  # key -> display name
    selected: str = ""  # selected option key
    expanded: bool = False


class Dialog:
    """Base dialog class."""

    def __init__(self, title: str, width: int = 400, height: int = 300):
        self.title = title
        self.width = width
        self.height = height
        self.visible = False
        self.result: Optional[str] = None
        self.data: Dict[str, Any] = {}

        # Colors
        self.bg_color = (45, 45, 48)
        self.title_bg = (30, 30, 32)
        self.text_color = (255, 255, 255)
        self.button_color = (62, 62, 66)
        self.button_hover = (80, 80, 85)
        self.button_primary = (0, 122, 204)
        self.border_color = (70, 70, 75)
        self.slider_bg = (30, 30, 32)
        self.slider_fill = (0, 122, 204)

        # Font - use default pygame font for crisp rendering
        self.font = pygame.font.Font(None, 18)
        self.font_title = pygame.font.Font(None, 22)

        # UI elements
        self.buttons: List[DialogButton] = []
        self.sliders: List[DialogSlider] = []
        self.checkboxes: List[DialogCheckbox] = []
        self.text_inputs: List[DialogTextInput] = []
        self.dropdowns: List[DialogDropdown] = []
        self.hovered_button: Optional[int] = None
        self.active_slider: Optional[DialogSlider] = None
        self.active_text_input: Optional[DialogTextInput] = None
        self.active_dropdown: Optional[DialogDropdown] = None

        # Position (will be set when showing)
        self.x = 0
        self.y = 0

        # Callbacks
        self.on_close: Optional[Callable[[str, Dict[str, Any]], None]] = None

    def show(self, screen_width: int, screen_height: int) -> None:
        """Show the dialog centered on screen."""
        self.x = (screen_width - self.width) // 2
        self.y = (screen_height - self.height) // 2
        self.visible = True
        self.result = None

    def hide(self) -> None:
        """Hide the dialog."""
        self.visible = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event. Returns True if event was consumed."""
        if not self.visible:
            return False

        if event.type == pygame.MOUSEMOTION:
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # Update slider if dragging
            if self.active_slider:
                self._update_slider(self.active_slider, local_x)
                return True

            # Update hovered button
            self.hovered_button = None
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(local_x, local_y):
                    self.hovered_button = i
                    break

            return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1:
                return True

            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # Check if click is outside dialog
            if not (0 <= local_x <= self.width and 0 <= local_y <= self.height):
                return True

            # Check buttons
            for button in self.buttons:
                if button.rect.collidepoint(local_x, local_y):
                    self._handle_button_click(button)
                    return True

            # Check sliders
            for slider in self.sliders:
                if slider.rect.collidepoint(local_x, local_y):
                    self.active_slider = slider
                    self._update_slider(slider, local_x)
                    return True

            # Check checkboxes
            for checkbox in self.checkboxes:
                if checkbox.rect.collidepoint(local_x, local_y):
                    checkbox.checked = not checkbox.checked
                    self.data[checkbox.key] = checkbox.checked
                    return True

            # Check dropdowns FIRST (so expanded dropdowns are on top)
            # First pass: check if clicking on expanded dropdown options
            for dropdown in self.dropdowns:
                if dropdown.expanded:
                    # Check if clicking on an option
                    option_height = 28
                    options_y = dropdown.rect.bottom
                    for i, (key, value) in enumerate(dropdown.options.items()):
                        option_rect = pygame.Rect(dropdown.rect.x, options_y + i * option_height,
                                                  dropdown.rect.width, option_height)
                        if option_rect.collidepoint(local_x, local_y):
                            dropdown.selected = key
                            dropdown.expanded = False
                            self.active_dropdown = None
                            self.data[dropdown.key] = key
                            return True

            # Second pass: check if clicking on dropdown headers
            for dropdown in self.dropdowns:
                if dropdown.rect.collidepoint(local_x, local_y):
                    # Toggle dropdown
                    dropdown.expanded = not dropdown.expanded
                    # Close other dropdowns
                    for dd in self.dropdowns:
                        if dd != dropdown:
                            dd.expanded = False
                    self.active_dropdown = dropdown if dropdown.expanded else None
                    return True

            # Close all dropdowns if clicking elsewhere
            dropdown_was_open = any(dd.expanded for dd in self.dropdowns)
            for dropdown in self.dropdowns:
                dropdown.expanded = False
            self.active_dropdown = None

            # If a dropdown was open and we closed it, consume the click
            if dropdown_was_open:
                return True

            # Check text inputs
            for text_input in self.text_inputs:
                if text_input.rect.collidepoint(local_x, local_y):
                    # Deactivate all other inputs
                    for ti in self.text_inputs:
                        ti.active = False
                    text_input.active = True
                    self.active_text_input = text_input
                    return True
                else:
                    text_input.active = False

            self.active_text_input = None

            return True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.active_slider = None
            return self.visible

        elif event.type == pygame.KEYDOWN:
            # Handle text input first
            if self.active_text_input:
                if event.key == pygame.K_BACKSPACE:
                    self.active_text_input.value = self.active_text_input.value[:-1]
                    self.data[self.active_text_input.key] = self.active_text_input.value
                    return True
                elif event.key == pygame.K_RETURN:
                    # Deactivate text input on Enter
                    self.active_text_input.active = False
                    self.active_text_input = None
                    return True
                elif event.key == pygame.K_ESCAPE:
                    # Deactivate text input on Escape
                    self.active_text_input.active = False
                    self.active_text_input = None
                    return True
                elif event.key == pygame.K_TAB:
                    # Move to next text input
                    self._focus_next_text_input()
                    return True
                elif event.unicode and len(self.active_text_input.value) < self.active_text_input.max_length:
                    # Add character (filter control characters)
                    if event.unicode.isprintable():
                        self.active_text_input.value += event.unicode
                        self.data[self.active_text_input.key] = self.active_text_input.value
                return True

            if event.key == pygame.K_ESCAPE:
                self.result = "cancel"
                self.hide()
                if self.on_close:
                    self.on_close("cancel", self.data)
                return True
            elif event.key == pygame.K_RETURN:
                self.result = "ok"
                self.hide()
                if self.on_close:
                    self.on_close("ok", self.data)
                return True

        return self.visible

    def _focus_next_text_input(self) -> None:
        """Focus the next text input field."""
        if not self.text_inputs:
            return

        current_idx = -1
        for i, ti in enumerate(self.text_inputs):
            if ti.active:
                current_idx = i
                ti.active = False
                break

        next_idx = (current_idx + 1) % len(self.text_inputs)
        self.text_inputs[next_idx].active = True
        self.active_text_input = self.text_inputs[next_idx]

    def _handle_button_click(self, button: DialogButton) -> None:
        """Handle button click."""
        self.result = button.action
        self.hide()
        if self.on_close:
            self.on_close(button.action, self.data)

    def _update_slider(self, slider: DialogSlider, local_x: int) -> None:
        """Update slider value based on mouse position."""
        rel_x = local_x - slider.rect.x
        ratio = max(0, min(1, rel_x / slider.rect.width))
        raw_value = slider.min_val + ratio * (slider.max_val - slider.min_val)

        if slider.step > 0:
            raw_value = round(raw_value / slider.step) * slider.step

        if slider.is_int:
            raw_value = int(raw_value)

        slider.value = raw_value
        self.data[slider.key] = slider.value

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog."""
        if not self.visible:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))

        # Dialog background
        dialog_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, dialog_rect, border_radius=8)
        pygame.draw.rect(surface, self.border_color, dialog_rect, width=1, border_radius=8)

        # Title bar
        title_rect = pygame.Rect(self.x, self.y, self.width, 30)
        pygame.draw.rect(surface, self.title_bg, title_rect,
                        border_top_left_radius=8, border_top_right_radius=8)

        title_surface = self.font_title.render(self.title, True, self.text_color)
        surface.blit(title_surface, (self.x + 10, self.y + 7))

        # Draw sliders
        for slider in self.sliders:
            self._draw_slider(surface, slider)

        # Draw checkboxes
        for checkbox in self.checkboxes:
            self._draw_checkbox(surface, checkbox)

        # Draw text inputs
        for text_input in self.text_inputs:
            self._draw_text_input(surface, text_input)

        # Draw buttons
        for i, button in enumerate(self.buttons):
            self._draw_button(surface, button, i == self.hovered_button)

        # Draw dropdowns in two passes:
        # First pass: draw all collapsed dropdowns
        # Second pass: draw expanded dropdown last (so it's on top)
        expanded_dropdown = None
        for dropdown in self.dropdowns:
            if dropdown.expanded:
                expanded_dropdown = dropdown
            else:
                self._draw_dropdown(surface, dropdown)

        # Draw expanded dropdown last so it appears on top
        if expanded_dropdown:
            self._draw_dropdown(surface, expanded_dropdown)

    def _draw_slider(self, surface: pygame.Surface, slider: DialogSlider) -> None:
        """Draw a slider control."""
        rect = pygame.Rect(
            self.x + slider.rect.x,
            self.y + slider.rect.y,
            slider.rect.width,
            slider.rect.height
        )

        # Label
        label_surface = self.font.render(
            f"{slider.label}: {slider.value}",
            True, self.text_color
        )
        surface.blit(label_surface, (rect.x, rect.y - 18))

        # Background
        pygame.draw.rect(surface, self.slider_bg, rect, border_radius=4)

        # Fill
        ratio = (slider.value - slider.min_val) / (slider.max_val - slider.min_val)
        fill_width = int(rect.width * ratio)
        fill_rect = pygame.Rect(rect.x, rect.y, fill_width, rect.height)
        pygame.draw.rect(surface, self.slider_fill, fill_rect, border_radius=4)

        # Border
        pygame.draw.rect(surface, self.border_color, rect, width=1, border_radius=4)

    def _draw_checkbox(self, surface: pygame.Surface, checkbox: DialogCheckbox) -> None:
        """Draw a checkbox control."""
        rect = pygame.Rect(
            self.x + checkbox.rect.x,
            self.y + checkbox.rect.y,
            checkbox.rect.width,
            checkbox.rect.height
        )

        # Box
        box_rect = pygame.Rect(rect.x, rect.y, 18, 18)
        pygame.draw.rect(surface, self.slider_bg, box_rect, border_radius=2)
        pygame.draw.rect(surface, self.border_color, box_rect, width=1, border_radius=2)

        # Check mark
        if checkbox.checked:
            pygame.draw.rect(surface, self.slider_fill,
                           pygame.Rect(box_rect.x + 3, box_rect.y + 3, 12, 12),
                           border_radius=2)

        # Label
        label_surface = self.font.render(checkbox.label, True, self.text_color)
        surface.blit(label_surface, (rect.x + 24, rect.y + 2))

    def _draw_text_input(self, surface: pygame.Surface, text_input: DialogTextInput) -> None:
        """Draw a text input control."""
        rect = pygame.Rect(
            self.x + text_input.rect.x,
            self.y + text_input.rect.y,
            text_input.rect.width,
            text_input.rect.height
        )

        # Label
        label_surface = self.font.render(text_input.label, True, self.text_color)
        surface.blit(label_surface, (rect.x, rect.y - 18))

        # Input background
        bg_color = (50, 50, 55) if text_input.active else self.slider_bg
        pygame.draw.rect(surface, bg_color, rect, border_radius=4)

        # Border (highlight when active)
        border_color = self.slider_fill if text_input.active else self.border_color
        pygame.draw.rect(surface, border_color, rect, width=2 if text_input.active else 1, border_radius=4)

        # Text
        display_text = text_input.value
        if text_input.active:
            # Add cursor
            display_text += "|"

        text_surface = self.font.render(display_text, True, self.text_color)

        # Clip text to fit
        text_rect = text_surface.get_rect(midleft=(rect.x + 8, rect.centery))
        if text_rect.width > rect.width - 16:
            # Show end of text when too long
            text_rect.right = rect.right - 8

        surface.blit(text_surface, text_rect)

    def _draw_dropdown(self, surface: pygame.Surface, dropdown: DialogDropdown) -> None:
        """Draw a dropdown control."""
        rect = pygame.Rect(
            self.x + dropdown.rect.x,
            self.y + dropdown.rect.y,
            dropdown.rect.width,
            dropdown.rect.height
        )

        # Label
        if dropdown.label:
            label_surface = self.font.render(dropdown.label, True, self.text_color)
            surface.blit(label_surface, (rect.x, rect.y - 18))

        # Dropdown background
        bg_color = (50, 50, 55) if dropdown.expanded else self.slider_bg
        pygame.draw.rect(surface, bg_color, rect, border_radius=4)
        pygame.draw.rect(surface, self.border_color, rect, width=1, border_radius=4)

        # Display selected option
        display_text = dropdown.options.get(dropdown.selected, "Нет")
        text_surface = self.font.render(display_text, True, self.text_color)
        surface.blit(text_surface, (rect.x + 8, rect.y + 6))

        # Arrow indicator
        arrow = "▼" if not dropdown.expanded else "▲"
        arrow_surface = self.font.render(arrow, True, self.text_color)
        surface.blit(arrow_surface, (rect.right - 20, rect.y + 6))

        # Draw expanded options if dropdown is open
        if dropdown.expanded:
            option_height = 28
            options_y = rect.bottom
            for i, (key, value) in enumerate(dropdown.options.items()):
                option_rect = pygame.Rect(rect.x, options_y + i * option_height,
                                         rect.width, option_height)
                # Highlight selected option
                if key == dropdown.selected:
                    pygame.draw.rect(surface, (70, 70, 75), option_rect)
                else:
                    pygame.draw.rect(surface, self.slider_bg, option_rect)
                pygame.draw.rect(surface, self.border_color, option_rect, width=1)

                option_text = self.font.render(value, True, self.text_color)
                surface.blit(option_text, (option_rect.x + 8, option_rect.y + 6))

    def _draw_button(self, surface: pygame.Surface, button: DialogButton,
                     hovered: bool) -> None:
        """Draw a button."""
        rect = pygame.Rect(
            self.x + button.rect.x,
            self.y + button.rect.y,
            button.rect.width,
            button.rect.height
        )

        if button.primary:
            color = self.button_primary
        elif hovered:
            color = self.button_hover
        else:
            color = self.button_color

        pygame.draw.rect(surface, color, rect, border_radius=4)

        text_surface = self.font.render(button.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)


class GeneratorDialog(Dialog):
    """Dialog for generator settings."""

    def __init__(self, params: GeneratorParams = None):
        super().__init__("Настройки генератора", 450, 650)
        self.params = params or GeneratorParams()
        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        y = 50
        slider_height = 16
        spacing = 45

        # Map size
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Ширина карты",
            key="width",
            value=self.params.width,
            min_val=50, max_val=500, step=10
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Высота карты",
            key="height",
            value=self.params.height,
            min_val=50, max_val=500, step=10
        ))
        y += spacing

        # Terrain parameters
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Масштаб рельефа",
            key="elevation_scale",
            value=self.params.elevation_scale,
            min_val=50, max_val=300, step=10, is_int=False
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Уровень воды",
            key="water_level",
            value=int(self.params.water_level * 100),
            min_val=10, max_val=50, step=1
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Уровень гор",
            key="mountain_level",
            value=int(self.params.mountain_level * 100),
            min_val=60, max_val=90, step=1
        ))
        y += spacing

        # Location counts
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Количество городов",
            key="city_count",
            value=self.params.city_count,
            min_val=1, max_val=15, step=1
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Количество деревень",
            key="village_count",
            value=self.params.village_count,
            min_val=0, max_val=40, step=1
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Количество шахт",
            key="mine_count",
            value=self.params.mine_count,
            min_val=0, max_val=20, step=1
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Количество руин",
            key="ruins_count",
            value=self.params.ruins_count,
            min_val=0, max_val=100, step=1
        ))
        y += spacing

        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y, self.width - 40, slider_height),
            label="Количество лагерей бандитов",
            key="bandit_camp_count",
            value=self.params.bandit_camp_count,
            min_val=0, max_val=100, step=1
        ))
        y += spacing

        # Options
        self.checkboxes.append(DialogCheckbox(
            rect=pygame.Rect(20, y, self.width - 40, 20),
            label="Температурный градиент",
            key="temperature_gradient",
            checked=self.params.temperature_gradient
        ))
        y += 30

        self.checkboxes.append(DialogCheckbox(
            rect=pygame.Rect(20, y, self.width - 40, 20),
            label="Генерировать пляжи",
            key="generate_beaches",
            checked=self.params.generate_beaches
        ))
        y += 30

        self.checkboxes.append(DialogCheckbox(
            rect=pygame.Rect(20, y, self.width - 40, 20),
            label="Генерировать реки",
            key="generate_rivers",
            checked=self.params.generate_rivers
        ))
        y += 30

        self.checkboxes.append(DialogCheckbox(
            rect=pygame.Rect(20, y, self.width - 40, 20),
            label="Без ограничения дистанции объектов",
            key="ignore_min_distance",
            checked=self.params.ignore_min_distance
        ))
        y += 40

        # Buttons
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Применить",
            action="ok",
            primary=True
        ))

        # Initialize data
        for slider in self.sliders:
            self.data[slider.key] = slider.value
        for checkbox in self.checkboxes:
            self.data[checkbox.key] = checkbox.checked

    def get_params(self) -> GeneratorParams:
        """Get generator params from dialog data."""
        return GeneratorParams(
            width=int(self.data.get('width', 200)),
            height=int(self.data.get('height', 200)),
            elevation_scale=float(self.data.get('elevation_scale', 150)),
            water_level=self.data.get('water_level', 30) / 100.0,
            mountain_level=self.data.get('mountain_level', 75) / 100.0,
            city_count=int(self.data.get('city_count', 5)),
            village_count=int(self.data.get('village_count', 15)),
            mine_count=int(self.data.get('mine_count', 8)),
            ruins_count=int(self.data.get('ruins_count', 10)),
            bandit_camp_count=int(self.data.get('bandit_camp_count', 10)),
            temperature_gradient=self.data.get('temperature_gradient', True),
            generate_beaches=self.data.get('generate_beaches', True),
            generate_rivers=self.data.get('generate_rivers', True),
            ignore_min_distance=self.data.get('ignore_min_distance', False)
        )


class LocationEditDialog(Dialog):
    """Dialog for editing location properties with name input."""

    def __init__(self, location_info: Dict[str, Any] = None):
        self.location_info = location_info or {}
        # Calculate dialog height based on location type
        loc_type = self.location_info.get('type', '')
        height = 450  # Base height increased for spawn_radius slider
        if loc_type in [LOCATION_MINE, LOCATION_RUINS]:
            height += 50  # Space for rank slider
        if loc_type in [LOCATION_CITY, LOCATION_CAPITAL, LOCATION_VILLAGE]:
            height += 50  # Space for shop_rank slider
        if loc_type == LOCATION_MINE:
            height += 170  # Space for miners_count, respawn_time sliders and resource_type dropdown
        # Add space for animal spawn points
        if loc_type in [LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER]:
            height += 150  # Space for animal_count, respawn_time, and spawn_radius sliders
        # Add space for guards (for settlements and academies)
        if loc_type in [LOCATION_VILLAGE, LOCATION_CITY, LOCATION_CAPITAL,
                        LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY, 'secret_camp']:
            height += 305  # Space for 5 guard slots (headers + 5*45 + spacing)
        super().__init__("Редактирование локации", 720, height)  # Increased width to 720 for guards with respawn_time
        # Guard headers (will be set in _setup_controls if location has guards)
        self._guard_headers_y = None
        self._guard_headers = None
        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls with text input for name."""
        y = 50
        loc_type = self.location_info.get('type', '')

        # Name input
        self.text_inputs.append(DialogTextInput(
            rect=pygame.Rect(20, y + 20, self.width - 40, 28),
            label="Название локации:",
            key="name",
            value=self.location_info.get('name', ''),
            max_length=40
        ))
        self.data['name'] = self.location_info.get('name', '')
        y += 70

        # Rank slider for mines and ruins
        if loc_type in [LOCATION_MINE, LOCATION_RUINS]:
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Ранг (сложность)",
                key="rank",
                value=self.location_info.get('rank', 1),
                min_val=1, max_val=4, step=1
            ))
            self.data['rank'] = self.location_info.get('rank', 1)
            y += 50

        # Shop rank slider for settlements
        if loc_type in [LOCATION_CITY, LOCATION_CAPITAL, LOCATION_VILLAGE]:
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Ранг магазина",
                key="shop_rank",
                value=self.location_info.get('shop_rank', 1),
                min_val=1, max_val=4, step=1
            ))
            self.data['shop_rank'] = self.location_info.get('shop_rank', 1)
            y += 50

        # Checkbox for starting village (only for villages)
        if loc_type == LOCATION_VILLAGE:
            self.checkboxes.append(DialogCheckbox(
                rect=pygame.Rect(20, y, self.width - 40, 20),
                label="Сделать стартовой деревней",
                key="set_starting",
                checked=self.location_info.get('is_starting', False)
            ))
            self.data['set_starting'] = self.location_info.get('is_starting', False)
            y += 40

        # Miners count slider (only for mines)
        if loc_type == LOCATION_MINE:
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Количество шахтеров (0-10)",
                key="miners_count",
                value=self.location_info.get('miners_count', 0),
                min_val=0, max_val=10, step=1
            ))
            self.data['miners_count'] = self.location_info.get('miners_count', 0)
            y += 50

        # Respawn time slider (only for mines)
        if loc_type == LOCATION_MINE:
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Время респавна (0-200 ходов)",
                key="respawn_time",
                value=self.location_info.get('respawn_time', 0),
                min_val=0, max_val=200, step=5
            ))
            self.data['respawn_time'] = self.location_info.get('respawn_time', 0)
            y += 50

        # Resource type dropdown (only for mines)
        if loc_type == LOCATION_MINE:
            self.dropdowns.append(DialogDropdown(
                rect=pygame.Rect(20, y + 20, self.width - 40, 28),
                label="Тип добываемого ресурса:",
                key="resource_type",
                options=RESOURCE_TYPES,
                selected=self.location_info.get('resource_type', 'copper')
            ))
            self.data['resource_type'] = self.location_info.get('resource_type', 'copper')
            y += 70

        # Animal spawn settings (only for animal spawn points)
        if loc_type in [LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER]:
            # Animal count slider
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Количество животных (1-10)",
                key="animal_count",
                value=self.location_info.get('animal_count', 3),
                min_val=1, max_val=10, step=1
            ))
            self.data['animal_count'] = self.location_info.get('animal_count', 3)
            y += 50

            # Respawn time slider
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Время респавна (0-999 ходов)",
                key="respawn_time",
                value=self.location_info.get('respawn_time', 50),
                min_val=0, max_val=999, step=5
            ))
            self.data['respawn_time'] = self.location_info.get('respawn_time', 50)
            y += 50

            # Spawn radius slider
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Зона действия (3-10)",
                key="spawn_radius",
                value=self.location_info.get('spawn_radius', 5),
                min_val=3, max_val=10, step=1
            ))
            self.data['spawn_radius'] = self.location_info.get('spawn_radius', 5)
            y += 50

        # Player attitude slider (for all locations)
        self.sliders.append(DialogSlider(
            rect=pygame.Rect(20, y + 20, self.width - 40, 16),
            label="Отношение к игроку (-10 до 10)",
            key="player_attitude",
            value=self.location_info.get('player_attitude', 0),
            min_val=-10, max_val=10, step=1
        ))
        self.data['player_attitude'] = self.location_info.get('player_attitude', 0)
        y += 50

        # Spawn radius slider (for all locations except animal spawns)
        # Animal spawns have their own spawn_radius slider in the animal spawn settings section
        if loc_type not in [LOCATION_SPAWN_WOLF, LOCATION_SPAWN_BEAR, LOCATION_SPAWN_DEER]:
            self.sliders.append(DialogSlider(
                rect=pygame.Rect(20, y + 20, self.width - 40, 16),
                label="Радиус спавна NPC (1-20)",
                key="spawn_radius",
                value=self.location_info.get('spawn_radius', 5),
                min_val=1, max_val=20, step=1
            ))
            self.data['spawn_radius'] = self.location_info.get('spawn_radius', 5)
            y += 50

        # Guards section (for settlements and academies)
        if loc_type in [LOCATION_VILLAGE, LOCATION_CITY, LOCATION_CAPITAL,
                        LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY, 'secret_camp']:
            # Guards title and column headers
            y += 10
            guards = self.location_info.get('guards', [Guard() for _ in range(5)])
            # Ensure we have exactly 5 guards
            while len(guards) < 5:
                guards.append(Guard())

            # Add column headers - store them as a special attribute for rendering
            self._guard_headers_y = y
            self._guard_headers = [
                ("Тип", 20, 180),           # (label, x, width)
                ("Ранг", 210, 80),
                ("Кол-во", 300, 80),
                ("Радиус патр.", 390, 100),  # Patrol radius column
                ("Время респ.", 500, 110)    # Respawn time column
            ]
            y += 25  # Space for headers

            for i in range(5):
                guard = guards[i] if i < len(guards) else Guard()

                # Dropdown for guard type (180px wide)
                self.dropdowns.append(DialogDropdown(
                    rect=pygame.Rect(20, y + 20, 180, 28),
                    label=f"Стража {i+1}:",
                    key=f"guard_{i}_type",
                    options=GUARD_TYPES,
                    selected=guard.guard_type
                ))
                self.data[f"guard_{i}_type"] = guard.guard_type

                # Rank dropdown (80px wide) - changed from text input to dropdown
                rank_options = {
                    "1": "1",
                    "2": "2",
                    "3": "3",
                    "4": "4"
                }
                self.dropdowns.append(DialogDropdown(
                    rect=pygame.Rect(210, y + 20, 80, 28),
                    label="",  # No label, using column header instead
                    key=f"guard_{i}_rank",
                    options=rank_options,
                    selected=str(guard.rank)
                ))
                self.data[f"guard_{i}_rank"] = str(guard.rank)

                # Count input (80px wide)
                self.text_inputs.append(DialogTextInput(
                    rect=pygame.Rect(300, y + 20, 80, 28),
                    label="",  # No label, using column header instead
                    key=f"guard_{i}_count",
                    value=str(guard.count),
                    max_length=2
                ))
                self.data[f"guard_{i}_count"] = str(guard.count)

                # Patrol radius input (100px wide)
                self.text_inputs.append(DialogTextInput(
                    rect=pygame.Rect(390, y + 20, 100, 28),
                    label="",  # No label, using column header instead
                    key=f"guard_{i}_patrol_radius",
                    value=str(guard.patrol_radius),
                    max_length=2
                ))
                self.data[f"guard_{i}_patrol_radius"] = str(guard.patrol_radius)

                # Respawn time input (110px wide)
                self.text_inputs.append(DialogTextInput(
                    rect=pygame.Rect(500, y + 20, 110, 28),
                    label="",  # No label, using column header instead
                    key=f"guard_{i}_respawn_time",
                    value=str(guard.respawn_time),
                    max_length=3
                ))
                self.data[f"guard_{i}_respawn_time"] = str(guard.respawn_time)

                y += 45

            y += 5  # Extra spacing after guards section

        # Connections text input (для шахт, деревень и городов)
        if loc_type in [LOCATION_MINE, LOCATION_VILLAGE, LOCATION_CITY]:
            # Форматируем существующие связи для отображения
            connections = self.location_info.get('connections', [])
            connections_str = '; '.join([f"{x},{y}" for x, y in connections])

            self.text_inputs.append(DialogTextInput(
                rect=pygame.Rect(20, y + 20, self.width - 40, 28),
                label="Связи (x,y; x,y):",
                key="connections",
                value=connections_str,
                max_length=100
            ))
            self.data['connections'] = connections_str
            y += 70

        # Buttons
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(20, btn_y, btn_width, btn_height),
            text="Удалить",
            action="delete"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Сохранить",
            action="ok",
            primary=True
        ))

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog with location info."""
        super().draw(surface)

        if not self.visible:
            return

        # Draw location type info (coordinates moved to bottom)
        y = self.y + 140
        info_lines = [
            f"Тип: {self.location_info.get('type_display', '')}"
        ]

        for line in info_lines:
            text_surface = self.font.render(line, True, (180, 180, 180))
            surface.blit(text_surface, (self.x + 20, y))
            y += 20

        # Draw coordinates at bottom, above "Delete" button
        btn_height = 30
        btn_y = self.height - btn_height - 15
        coords_y = self.y + btn_y - 30  # 30px above the buttons
        coords_text = f"Координаты: ({self.location_info.get('x', 0)}, {self.location_info.get('y', 0)})"
        coords_surface = self.font.render(coords_text, True, (180, 180, 180))
        surface.blit(coords_surface, (self.x + 20, coords_y))

        # Draw guard column headers if guards section is present
        if self._guard_headers_y is not None and self._guard_headers is not None:
            header_y = self.y + self._guard_headers_y
            for label, col_x, col_width in self._guard_headers:
                # Draw header text
                header_text = self.font.render(label, True, (200, 200, 200))
                surface.blit(header_text, (self.x + col_x, header_y))
                # Draw underline
                pygame.draw.line(surface, (100, 100, 105),
                               (self.x + col_x, header_y + 18),
                               (self.x + col_x + col_width - 5, header_y + 18),
                               1)


# Keep old name for backwards compatibility
ObjectDialog = LocationEditDialog


class SaveDialog(Dialog):
    """Dialog for save confirmation."""

    def __init__(self, filename: str = ""):
        super().__init__("Сохранить карту", 400, 150)
        self.filename = filename
        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width * 3 - 30, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width * 2 - 20, btn_y, btn_width, btn_height),
            text="Сохранить как...",
            action="save_as"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Сохранить",
            action="ok",
            primary=True
        ))

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog."""
        super().draw(surface)

        if not self.visible:
            return

        # Draw filename
        text = f"Файл: {self.filename}" if self.filename else "Новая карта (не сохранена)"
        text_surface = self.font.render(text, True, self.text_color)
        surface.blit(text_surface, (self.x + 20, self.y + 60))


class LoadDialog(Dialog):
    """Dialog for selecting a file to load."""

    def __init__(self, directory: str = ""):
        super().__init__("Открыть карту", 500, 400)
        self.directory = directory or str(Path.home())
        self.files: List[str] = []
        self.selected_file: Optional[str] = None
        self.scroll_offset = 0
        self._scan_files()
        self._setup_controls()

    def _scan_files(self) -> None:
        """Scan directory for map files."""
        try:
            path = Path(self.directory)
            self.files = sorted([
                f.name for f in path.glob("*.json")
                if f.is_file()
            ])
        except Exception:
            self.files = []

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Открыть",
            action="ok",
            primary=True
        ))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events including file selection."""
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                local_x = event.pos[0] - self.x
                local_y = event.pos[1] - self.y

                # Check file list area
                list_rect = pygame.Rect(10, 40, self.width - 20, self.height - 100)
                if list_rect.collidepoint(local_x, local_y):
                    # Calculate which file was clicked
                    file_y = local_y - 40 + self.scroll_offset
                    file_idx = file_y // 24
                    if 0 <= file_idx < len(self.files):
                        self.selected_file = self.files[file_idx]
                        self.data['filename'] = str(Path(self.directory) / self.selected_file)
                    return True

            elif event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 24)
                return True
            elif event.button == 5:  # Scroll down
                max_scroll = max(0, len(self.files) * 24 - (self.height - 100))
                self.scroll_offset = min(max_scroll, self.scroll_offset + 24)
                return True

        return super().handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog with file list."""
        super().draw(surface)

        if not self.visible:
            return

        # File list area
        list_rect = pygame.Rect(self.x + 10, self.y + 40, self.width - 20, self.height - 100)
        pygame.draw.rect(surface, self.slider_bg, list_rect, border_radius=4)

        # Draw files
        y = self.y + 44
        for i, filename in enumerate(self.files):
            file_y = y + i * 24 - self.scroll_offset
            if self.y + 40 <= file_y < self.y + self.height - 60:
                # Highlight selected
                if filename == self.selected_file:
                    highlight_rect = pygame.Rect(self.x + 12, file_y - 2, self.width - 24, 22)
                    pygame.draw.rect(surface, self.slider_fill, highlight_rect, border_radius=2)

                text_surface = self.font.render(filename, True, self.text_color)
                surface.blit(text_surface, (self.x + 16, file_y))

        # Border
        pygame.draw.rect(surface, self.border_color, list_rect, width=1, border_radius=4)


class ConfirmDialog(Dialog):
    """Dialog for confirmation with Yes/No buttons."""

    def __init__(self, message: str, title: str = "Подтверждение"):
        super().__init__(title, 400, 180)
        self.message = message
        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        # No button (Esc / Right click)
        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width * 2 - 20, btn_y, btn_width, btn_height),
            text="Нет",
            action="no"
        ))

        # Yes button (Enter / Left click) - primary
        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Да",
            action="yes",
            primary=True
        ))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event. Returns True if event was consumed."""
        if not self.visible:
            return False

        # Handle right click as "No"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right click
            self.result = "no"
            self.hide()
            if self.on_close:
                self.on_close("no", self.data)
            return True

        # Call parent handle_event for normal handling
        return super().handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog."""
        super().draw(surface)

        if not self.visible:
            return

        # Draw message
        y = self.y + 60
        # Split message into multiple lines if needed
        words = self.message.split(' ')
        lines = []
        current_line = ""
        max_width = self.width - 40

        for word in words:
            test_line = current_line + " " + word if current_line else word
            test_surface = self.font.render(test_line, True, self.text_color)
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        for line in lines:
            text_surface = self.font.render(line, True, self.text_color)
            text_rect = text_surface.get_rect(center=(self.x + self.width // 2, y))
            surface.blit(text_surface, text_rect)
            y += 25


class MerchantEditDialog(Dialog):
    """Dialog for editing merchant properties and waypoints."""

    # Predefined merchant colors
    MERCHANT_COLORS = [
        ((255, 165, 0), "Оранжевый"),
        ((255, 215, 0), "Золотой"),
        ((138, 43, 226), "Фиолетовый"),
        ((0, 191, 255), "Голубой"),
        ((50, 205, 50), "Зелёный"),
        ((255, 69, 0), "Красный"),
        ((255, 105, 180), "Розовый"),
        ((64, 224, 208), "Бирюзовый")
    ]

    def __init__(self, merchant: Merchant = None, is_new: bool = False):
        self.merchant = merchant or Merchant()
        self.is_new = is_new
        self.waypoints_copy = [MerchantWaypoint(wp.x, wp.y, wp.duration) for wp in self.merchant.waypoints]

        # Calculate dialog height based on waypoints
        base_height = 450  # Increased for "Add points on map" button
        waypoints_height = min(200, len(self.waypoints_copy) * 30 + 60)
        height = base_height + waypoints_height

        title = "Создать торговца" if is_new else "Редактировать торговца"
        super().__init__(title, 550, height)

        self._waypoint_delete_rects: List[Tuple[pygame.Rect, int]] = []
        self._color_rects: List[Tuple[pygame.Rect, Tuple[int, int, int]]] = []
        self._add_waypoint_rect: Optional[pygame.Rect] = None
        self._add_waypoint_on_map_rect: Optional[pygame.Rect] = None  # Button for adding waypoints on map
        self._selected_color = self.merchant.color

        # Callback for adding waypoints on map
        self.on_add_waypoints_on_map: Optional[Callable[[], None]] = None

        self._setup_controls()

    def _setup_controls(self) -> None:
        """Setup dialog controls."""
        y = 50

        # Name input
        self.text_inputs.append(DialogTextInput(
            rect=pygame.Rect(20, y + 20, self.width - 40, 28),
            label="Имя торговца:",
            key="name",
            value=self.merchant.name,
            max_length=40
        ))
        self.data['name'] = self.merchant.name
        y += 70

        # Rank dropdown
        rank_options = {str(k): v for k, v in MERCHANT_RANKS.items()}
        self.dropdowns.append(DialogDropdown(
            rect=pygame.Rect(20, y + 20, self.width - 40, 28),
            label="Ранг торговца:",
            key="rank",
            options=rank_options,
            selected=str(self.merchant.rank)
        ))
        self.data['rank'] = str(self.merchant.rank)
        y += 70

        # Color selection will be drawn manually
        self.data['color'] = list(self._selected_color)
        y += 60  # Space for color selection

        # Waypoints section - header drawn in draw()
        y += 40  # Space for "Маршрут" header

        # Store waypoints data
        for i, wp in enumerate(self.waypoints_copy):
            self.data[f'wp_{i}_x'] = str(wp.x)
            self.data[f'wp_{i}_y'] = str(wp.y)
            self.data[f'wp_{i}_duration'] = str(wp.duration)

        # Buttons
        btn_width = 100
        btn_height = 30
        btn_y = self.height - btn_height - 15

        if not self.is_new:
            self.buttons.append(DialogButton(
                rect=pygame.Rect(20, btn_y, btn_width, btn_height),
                text="Удалить",
                action="delete"
            ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 120, btn_y, btn_width, btn_height),
            text="Отмена",
            action="cancel"
        ))

        self.buttons.append(DialogButton(
            rect=pygame.Rect(self.width - btn_width - 10, btn_y, btn_width, btn_height),
            text="Сохранить",
            action="ok",
            primary=True
        ))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event with custom waypoint handling."""
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            local_x = event.pos[0] - self.x
            local_y = event.pos[1] - self.y

            # Check color selection
            for rect, color in self._color_rects:
                if rect.collidepoint(local_x, local_y):
                    self._selected_color = color
                    self.data['color'] = list(color)
                    return True

            # Check waypoint delete buttons
            for rect, idx in self._waypoint_delete_rects:
                if rect.collidepoint(local_x, local_y):
                    if 0 <= idx < len(self.waypoints_copy):
                        self.waypoints_copy.pop(idx)
                        # Update data
                        self._update_waypoints_data()
                    return True

            # Check add waypoint button
            if self._add_waypoint_rect and self._add_waypoint_rect.collidepoint(local_x, local_y):
                # Add new waypoint at (0, 0) with default duration
                self.waypoints_copy.append(MerchantWaypoint(x=0, y=0, duration=10))
                self._update_waypoints_data()
                return True

            # Check "Add waypoints on map" button
            if self._add_waypoint_on_map_rect and self._add_waypoint_on_map_rect.collidepoint(local_x, local_y):
                if self.on_add_waypoints_on_map:
                    self.on_add_waypoints_on_map()
                return True

        return super().handle_event(event)

    def _update_waypoints_data(self) -> None:
        """Update waypoints data dictionary."""
        # Clear old waypoint data
        keys_to_remove = [k for k in self.data.keys() if k.startswith('wp_')]
        for k in keys_to_remove:
            del self.data[k]

        # Add current waypoints
        for i, wp in enumerate(self.waypoints_copy):
            self.data[f'wp_{i}_x'] = str(wp.x)
            self.data[f'wp_{i}_y'] = str(wp.y)
            self.data[f'wp_{i}_duration'] = str(wp.duration)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the dialog with merchant-specific elements."""
        # Call parent draw but we'll redraw the expanded dropdown last
        super().draw(surface)

        if not self.visible:
            return

        # Draw color selection
        y = self.y + 170
        color_label = self.font.render("Цвет маркера:", True, self.text_color)
        surface.blit(color_label, (self.x + 20, y))
        y += 25

        self._color_rects = []
        color_size = 24
        padding = 8
        x_offset = self.x + 20

        for color, name in self.MERCHANT_COLORS:
            rect = pygame.Rect(x_offset, y, color_size, color_size)
            self._color_rects.append((pygame.Rect(x_offset - self.x, y - self.y, color_size, color_size), color))

            pygame.draw.rect(surface, color, rect, border_radius=4)
            if color == self._selected_color:
                pygame.draw.rect(surface, (255, 255, 255), rect, width=2, border_radius=4)
            else:
                pygame.draw.rect(surface, (100, 100, 100), rect, width=1, border_radius=4)

            x_offset += color_size + padding

        y += 40

        # Draw waypoints section
        waypoints_label = self.font.render("Маршрут (точки стоянки):", True, self.text_color)
        surface.blit(waypoints_label, (self.x + 20, y))
        y += 25

        self._waypoint_delete_rects = []

        if not self.waypoints_copy:
            no_wp_text = self.font.render("Нет точек маршрута", True, (150, 150, 150))
            surface.blit(no_wp_text, (self.x + 20, y))
            y += 20
        else:
            # Header row
            header_x = self.x + 20
            headers = [("№", 30), ("X", 60), ("Y", 60), ("Длит.", 70), ("", 30)]
            for header, width in headers:
                header_surface = self.font.render(header, True, (180, 180, 180))
                surface.blit(header_surface, (header_x, y))
                header_x += width
            y += 20

            # Waypoint rows
            for i, wp in enumerate(self.waypoints_copy):
                row_x = self.x + 20

                # Number
                num_surface = self.font.render(f"{i + 1}.", True, self.text_color)
                surface.blit(num_surface, (row_x, y + 5))
                row_x += 30

                # X input (simplified - just show value)
                x_rect = pygame.Rect(row_x, y, 50, 24)
                pygame.draw.rect(surface, (50, 50, 55), x_rect, border_radius=4)
                pygame.draw.rect(surface, (70, 70, 75), x_rect, width=1, border_radius=4)
                x_text = self.font.render(str(wp.x), True, self.text_color)
                surface.blit(x_text, (x_rect.x + 5, x_rect.y + 5))
                row_x += 60

                # Y input
                y_rect = pygame.Rect(row_x, y, 50, 24)
                pygame.draw.rect(surface, (50, 50, 55), y_rect, border_radius=4)
                pygame.draw.rect(surface, (70, 70, 75), y_rect, width=1, border_radius=4)
                y_text = self.font.render(str(wp.y), True, self.text_color)
                surface.blit(y_text, (y_rect.x + 5, y_rect.y + 5))
                row_x += 60

                # Duration input
                dur_rect = pygame.Rect(row_x, y, 60, 24)
                pygame.draw.rect(surface, (50, 50, 55), dur_rect, border_radius=4)
                pygame.draw.rect(surface, (70, 70, 75), dur_rect, width=1, border_radius=4)
                dur_text = self.font.render(str(wp.duration), True, self.text_color)
                surface.blit(dur_text, (dur_rect.x + 5, dur_rect.y + 5))
                row_x += 70

                # Delete button
                del_rect = pygame.Rect(row_x, y, 24, 24)
                self._waypoint_delete_rects.append((pygame.Rect(row_x - self.x, y - self.y, 24, 24), i))
                pygame.draw.rect(surface, (150, 50, 50), del_rect, border_radius=4)
                del_text = self.font.render("X", True, (255, 255, 255))
                del_text_rect = del_text.get_rect(center=del_rect.center)
                surface.blit(del_text, del_text_rect)

                y += 28

        y += 10

        # Add waypoint button (manual entry)
        add_btn_rect = pygame.Rect(self.x + 20, y, 150, 26)
        self._add_waypoint_rect = pygame.Rect(20, y - self.y, 150, 26)
        pygame.draw.rect(surface, (50, 120, 50), add_btn_rect, border_radius=4)
        add_text = self.font.render("+ Добавить точку", True, (255, 255, 255))
        add_text_rect = add_text.get_rect(center=add_btn_rect.center)
        surface.blit(add_text, add_text_rect)

        # Add waypoints on map button
        map_btn_rect = pygame.Rect(self.x + 180, y, 200, 26)
        self._add_waypoint_on_map_rect = pygame.Rect(180, y - self.y, 200, 26)
        pygame.draw.rect(surface, (50, 80, 150), map_btn_rect, border_radius=4)
        map_text = self.font.render("Добавить на карте", True, (255, 255, 255))
        map_text_rect = map_text.get_rect(center=map_btn_rect.center)
        surface.blit(map_text, map_text_rect)

        # Hint text
        y += 35
        hint_text = self.font.render("Совет: ПКМ для завершения добавления на карте", True, (150, 150, 150))
        surface.blit(hint_text, (self.x + 20, y))

        # IMPORTANT: Redraw expanded dropdown LAST to fix z-order issue
        # This ensures dropdown options appear on top of all other elements
        for dropdown in self.dropdowns:
            if dropdown.expanded:
                self._draw_dropdown(surface, dropdown)
                break

    def get_merchant(self) -> Merchant:
        """Get the edited merchant with updated values."""
        name = self.data.get('name', '').strip()
        rank = int(self.data.get('rank', '1'))
        color_data = self.data.get('color', [255, 165, 0])
        # Ensure color is a tuple of 3 integers
        if isinstance(color_data, (list, tuple)):
            color = tuple(int(c) for c in color_data[:3])
        else:
            color = (255, 165, 0)

        # Update merchant
        self.merchant.name = name if name else f"Торговец"
        self.merchant.rank = max(1, min(4, rank))  # Clamp rank to 1-4
        self.merchant.color = color
        self.merchant.waypoints = self.waypoints_copy

        return self.merchant

    def add_waypoint_from_map(self, x: int, y: int, duration: int = 10) -> None:
        """Add a waypoint from map click."""
        self.waypoints_copy.append(MerchantWaypoint(x=x, y=y, duration=duration))
        self._update_waypoints_data()
