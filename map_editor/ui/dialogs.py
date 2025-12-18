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
    Guard, GUARD_TYPES, GUARD_NONE
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

            # Check dropdowns
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
                elif dropdown.expanded:
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

            # Close all dropdowns if clicking outside
            for dropdown in self.dropdowns:
                dropdown.expanded = False
            self.active_dropdown = None

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

        # Draw dropdowns LAST so they appear on top of other elements
        for dropdown in self.dropdowns:
            self._draw_dropdown(surface, dropdown)

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
            height += 100  # Space for miners_count and respawn_time sliders
        # Add space for guards (for settlements and academies)
        if loc_type in [LOCATION_VILLAGE, LOCATION_CITY, LOCATION_CAPITAL,
                        LOCATION_MAGIC_SCHOOL, LOCATION_WARRIOR_ACADEMY, 'secret_camp']:
            height += 305  # Space for 5 guard slots (headers + 5*45 + spacing)
        super().__init__("Редактирование локации", 500, height)  # Increased width to 500 for guards
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

        # Spawn radius slider (for all locations)
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
                ("Тип", 20, 180),      # (label, x, width)
                ("Ранг", 210, 80),
                ("Кол-во", 300, 80)
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

        # Draw location type and coordinates info
        y = self.y + 140
        info_lines = [
            f"Тип: {self.location_info.get('type_display', '')}",
            f"Координаты: ({self.location_info.get('x', 0)}, {self.location_info.get('y', 0)})"
        ]

        for line in info_lines:
            text_surface = self.font.render(line, True, (180, 180, 180))
            surface.blit(text_surface, (self.x + 20, y))
            y += 20

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
