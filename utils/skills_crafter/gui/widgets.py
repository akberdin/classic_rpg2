"""
Кастомные виджеты для Skills Crafter GUI
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional, List, Dict


class LabeledEntry(ttk.Frame):
    """Поле ввода с меткой"""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        width: int = 30,
        default: str = "",
        tooltip: str = "",
        **kwargs
    ):
        super().__init__(parent)
        self.label = ttk.Label(self, text=label, width=20, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.var = tk.StringVar(value=default)
        self.entry = ttk.Entry(self, textvariable=self.var, width=width, **kwargs)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if tooltip:
            self._create_tooltip(tooltip)

    def _create_tooltip(self, text: str):
        """Создание всплывающей подсказки"""
        tooltip = ToolTip(self.entry, text)

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class LabeledSpinbox(ttk.Frame):
    """Числовое поле с меткой"""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        from_: float = 0,
        to: float = 100,
        increment: float = 1,
        default: float = 0,
        width: int = 10,
        is_float: bool = False,
        tooltip: str = "",
        **kwargs
    ):
        super().__init__(parent)
        self.is_float = is_float

        self.label = ttk.Label(self, text=label, width=20, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        if is_float:
            self.var = tk.DoubleVar(value=default)
        else:
            self.var = tk.IntVar(value=int(default))

        self.spinbox = ttk.Spinbox(
            self,
            from_=from_,
            to=to,
            increment=increment,
            textvariable=self.var,
            width=width,
            **kwargs
        )
        self.spinbox.pack(side=tk.LEFT)

        if tooltip:
            ToolTip(self.spinbox, tooltip)

    def get(self) -> float:
        try:
            return float(self.var.get()) if self.is_float else int(self.var.get())
        except (ValueError, tk.TclError):
            return 0.0 if self.is_float else 0

    def set(self, value: float):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class LabeledCombobox(ttk.Frame):
    """Выпадающий список с меткой"""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        values: List[str],
        display_names: Optional[Dict[str, str]] = None,
        default: str = "",
        width: int = 25,
        tooltip: str = "",
        **kwargs
    ):
        super().__init__(parent)
        self.values = values
        self.display_names = display_names or {}
        self.reverse_names = {v: k for k, v in self.display_names.items()}

        self.label = ttk.Label(self, text=label, width=20, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.var = tk.StringVar()
        display_values = [self.display_names.get(v, v) for v in values]
        self.combobox = ttk.Combobox(
            self,
            textvariable=self.var,
            values=display_values,
            width=width,
            state="readonly",
            **kwargs
        )
        self.combobox.pack(side=tk.LEFT)

        # Установить значение по умолчанию
        if default:
            self.set(default)
        elif values:
            self.set(values[0])

        if tooltip:
            ToolTip(self.combobox, tooltip)

    def get(self) -> str:
        """Получить реальное значение (не отображаемое)"""
        display = self.var.get()
        return self.reverse_names.get(display, display)

    def set(self, value: str):
        """Установить значение (передается реальное значение)"""
        display = self.display_names.get(value, value)
        self.var.set(display)

    def bind_change(self, callback: Callable):
        self.combobox.bind("<<ComboboxSelected>>", lambda e: callback())


class LabeledCheckbox(ttk.Frame):
    """Чекбокс с меткой"""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        default: bool = False,
        tooltip: str = "",
        **kwargs
    ):
        super().__init__(parent)

        self.var = tk.BooleanVar(value=default)
        self.checkbox = ttk.Checkbutton(
            self, text=label, variable=self.var, **kwargs
        )
        self.checkbox.pack(side=tk.LEFT)

        if tooltip:
            ToolTip(self.checkbox, tooltip)

    def get(self) -> bool:
        return self.var.get()

    def set(self, value: bool):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class ScrollableFrame(ttk.Frame):
    """Прокручиваемый фрейм"""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent)

        # Canvas для прокрутки
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_frame = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Прокрутка колесом мыши
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        # Привязка изменения размера canvas
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class CollapsibleFrame(ttk.Frame):
    """Сворачиваемая секция"""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        expanded: bool = True,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self._expanded = expanded

        # Заголовок
        self.header = ttk.Frame(self)
        self.header.pack(fill=tk.X)

        self.toggle_btn = ttk.Button(
            self.header,
            text="▼" if expanded else "▶",
            width=2,
            command=self._toggle
        )
        self.toggle_btn.pack(side=tk.LEFT)

        self.title_label = ttk.Label(
            self.header, text=title, font=("TkDefaultFont", 10, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=5)

        # Содержимое
        self.content = ttk.Frame(self)
        if expanded:
            self.content.pack(fill=tk.BOTH, expand=True, pady=5)

    def _toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.content.pack(fill=tk.BOTH, expand=True, pady=5)
            self.toggle_btn.configure(text="▼")
        else:
            self.content.pack_forget()
            self.toggle_btn.configure(text="▶")


class ToolTip:
    """Всплывающая подсказка"""

    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            self.tooltip,
            text=self.text,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            padding=5
        )
        label.pack()

    def _hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class StatusEffectEditor(ttk.Frame):
    """Редактор одного статус-эффекта"""

    def __init__(
        self,
        parent: tk.Widget,
        effect_types: Dict[str, str],
        on_delete: Callable = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.effect_types = effect_types
        self.on_delete = on_delete

        # Основной контейнер
        self.configure(relief=tk.GROOVE, padding=5)

        # Заголовок с кнопкой удаления
        header = ttk.Frame(self)
        header.pack(fill=tk.X)

        self.type_combo = LabeledCombobox(
            header,
            "Тип эффекта:",
            values=list(effect_types.keys()),
            display_names=effect_types,
            width=20
        )
        self.type_combo.pack(side=tk.LEFT)

        if on_delete:
            delete_btn = ttk.Button(header, text="✕", width=3, command=self._delete)
            delete_btn.pack(side=tk.RIGHT)

        # Параметры
        params = ttk.Frame(self)
        params.pack(fill=tk.X, pady=5)

        # Первый ряд
        row1 = ttk.Frame(params)
        row1.pack(fill=tk.X)

        self.chance_base = LabeledSpinbox(
            row1, "Шанс (база):", 0, 1, 0.1, 1.0, is_float=True,
            tooltip="Базовый шанс срабатывания (1.0 = 100%)"
        )
        self.chance_base.pack(side=tk.LEFT, padx=5)

        self.chance_per_rank = LabeledSpinbox(
            row1, "+ за ранг:", 0, 0.5, 0.05, 0, is_float=True
        )
        self.chance_per_rank.pack(side=tk.LEFT, padx=5)

        # Второй ряд
        row2 = ttk.Frame(params)
        row2.pack(fill=tk.X, pady=2)

        self.duration_base = LabeledSpinbox(
            row2, "Длительность:", 0, 20, 1, 3,
            tooltip="Базовая длительность в ходах"
        )
        self.duration_base.pack(side=tk.LEFT, padx=5)

        self.duration_per_rank = LabeledSpinbox(
            row2, "+ за ранг:", 0, 5, 1, 0
        )
        self.duration_per_rank.pack(side=tk.LEFT, padx=5)

        # Третий ряд
        row3 = ttk.Frame(params)
        row3.pack(fill=tk.X, pady=2)

        self.value_base = LabeledSpinbox(
            row3, "Значение:", 0, 100, 1, 5, is_float=True,
            tooltip="Урон/лечение/бонус за ход"
        )
        self.value_base.pack(side=tk.LEFT, padx=5)

        self.value_per_rank = LabeledSpinbox(
            row3, "+ за ранг:", 0, 20, 1, 2, is_float=True
        )
        self.value_per_rank.pack(side=tk.LEFT, padx=5)

    def _delete(self):
        if self.on_delete:
            self.on_delete(self)
        self.destroy()

    def get_data(self) -> Dict[str, Any]:
        return {
            "effect_type": self.type_combo.get(),
            "chance_base": self.chance_base.get(),
            "chance_per_rank": self.chance_per_rank.get(),
            "duration_base": int(self.duration_base.get()),
            "duration_per_rank": int(self.duration_per_rank.get()),
            "value_base": self.value_base.get(),
            "value_per_rank": self.value_per_rank.get(),
        }

    def set_data(self, data: Dict[str, Any]):
        self.type_combo.set(data.get("effect_type", "poison"))
        self.chance_base.set(data.get("chance_base", 1.0))
        self.chance_per_rank.set(data.get("chance_per_rank", 0))
        self.duration_base.set(data.get("duration_base", 3))
        self.duration_per_rank.set(data.get("duration_per_rank", 0))
        self.value_base.set(data.get("value_base", 5))
        self.value_per_rank.set(data.get("value_per_rank", 2))


class ScalingEditor(ttk.Frame):
    """Редактор масштабирования по атрибуту"""

    def __init__(
        self,
        parent: tk.Widget,
        attributes: Dict[str, str],
        on_delete: Callable = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.attributes = attributes
        self.on_delete = on_delete

        self.configure(relief=tk.GROOVE, padding=3)

        row = ttk.Frame(self)
        row.pack(fill=tk.X)

        self.attr_combo = LabeledCombobox(
            row,
            "Атрибут:",
            values=list(attributes.keys()),
            display_names=attributes,
            width=15
        )
        self.attr_combo.pack(side=tk.LEFT, padx=2)

        self.multiplier = LabeledSpinbox(
            row, "× ", 0, 10, 0.1, 1.0, is_float=True, width=6
        )
        self.multiplier.pack(side=tk.LEFT, padx=2)

        self.per_rank = LabeledSpinbox(
            row, "+ за ранг:", 0, 2, 0.1, 0, is_float=True, width=6
        )
        self.per_rank.pack(side=tk.LEFT, padx=2)

        if on_delete:
            delete_btn = ttk.Button(row, text="✕", width=2, command=self._delete)
            delete_btn.pack(side=tk.RIGHT)

    def _delete(self):
        if self.on_delete:
            self.on_delete(self)
        self.destroy()

    def get_data(self) -> Dict[str, Any]:
        return {
            "attribute": self.attr_combo.get(),
            "multiplier": self.multiplier.get(),
            "multiplier_per_rank": self.per_rank.get(),
        }

    def set_data(self, data: Dict[str, Any]):
        self.attr_combo.set(data.get("attribute", "strength"))
        self.multiplier.set(data.get("multiplier", 1.0))
        self.per_rank.set(data.get("multiplier_per_rank", 0))


class AnimationFrameItem(ttk.Frame):
    """Элемент кадра анимации с превью и кнопками"""

    def __init__(
        self,
        parent: tk.Widget,
        frame_index: int,
        on_select: Callable = None,
        on_delete: Callable = None,
        on_move_up: Callable = None,
        on_move_down: Callable = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.frame_index = frame_index
        self.sprite_path = ""
        self.image = None
        self.photo_image = None

        self.configure(relief=tk.GROOVE, padding=3)

        # Верхняя часть - номер кадра и кнопки
        header = ttk.Frame(self)
        header.pack(fill=tk.X)

        ttk.Label(header, text=f"Кадр {frame_index + 1}", font=("TkDefaultFont", 9, "bold")).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)

        if on_move_up:
            ttk.Button(btn_frame, text="↑", width=2, command=lambda: on_move_up(self)).pack(side=tk.LEFT, padx=1)
        if on_move_down:
            ttk.Button(btn_frame, text="↓", width=2, command=lambda: on_move_down(self)).pack(side=tk.LEFT, padx=1)
        if on_delete:
            ttk.Button(btn_frame, text="✕", width=2, command=lambda: on_delete(self)).pack(side=tk.LEFT, padx=1)

        # Превью спрайта
        preview_frame = ttk.Frame(self)
        preview_frame.pack(fill=tk.X, pady=5)

        self.preview_container = ttk.Frame(preview_frame, width=64, height=64, relief=tk.SUNKEN)
        self.preview_container.pack(side=tk.LEFT, padx=5)
        self.preview_container.pack_propagate(False)

        self.preview_label = ttk.Label(self.preview_container, text="—")
        self.preview_label.pack(expand=True)

        # Кнопка выбора
        select_btn = ttk.Button(preview_frame, text="Выбрать спрайт", command=lambda: on_select(self) if on_select else None)
        select_btn.pack(side=tk.LEFT, padx=5)

        # Путь к файлу
        self.path_label = ttk.Label(preview_frame, text="Не выбран", wraplength=200)
        self.path_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    def set_sprite(self, path: str, image=None):
        """Установка спрайта"""
        self.sprite_path = path
        self.path_label.configure(text=path if path else "Не выбран")

        if image:
            try:
                # Импорт здесь, чтобы избежать проблем при отсутствии PIL
                from PIL import Image, ImageTk

                # Ресайз для превью
                img = image.copy()
                img.thumbnail((64, 64), Image.Resampling.LANCZOS)
                self.photo_image = ImageTk.PhotoImage(img)
                self.preview_label.configure(image=self.photo_image, text="")
            except Exception as e:
                self.preview_label.configure(image="", text="!")
        else:
            self.preview_label.configure(image="", text="—")

    def get_data(self) -> Dict[str, Any]:
        return {
            "sprite_path": self.sprite_path,
            "duration_ms": 100,  # По умолчанию
        }


class AnimationPreview(ttk.Frame):
    """Виджет предпросмотра анимации с управлением воспроизведением"""

    def __init__(
        self,
        parent: tk.Widget,
        preview_size: int = 128,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.preview_size = preview_size
        self.frames: List[Any] = []  # PIL Images
        self.photo_frames: List[Any] = []  # PhotoImage для отображения
        self.current_frame = 0
        self.is_playing = False
        self.fps = 10
        self.loop_mode = "loop"  # once, loop, ping_pong
        self.direction = 1  # 1 = вперед, -1 = назад (для ping_pong)
        self.animation_job = None

        # Основной контейнер
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Превью анимации
        preview_container = ttk.Frame(main_frame)
        preview_container.pack(pady=10)

        self.canvas = tk.Canvas(
            preview_container,
            width=preview_size,
            height=preview_size,
            bg="#2c2c2c",
            highlightthickness=1,
            highlightbackground="#555"
        )
        self.canvas.pack()

        # Текст по умолчанию
        self.default_text = self.canvas.create_text(
            preview_size // 2, preview_size // 2,
            text="Нет кадров",
            fill="#888",
            font=("TkDefaultFont", 10)
        )
        self.image_item = None

        # Индикатор кадра
        self.frame_label = ttk.Label(main_frame, text="Кадр: 0 / 0")
        self.frame_label.pack()

        # Панель управления
        controls = ttk.Frame(main_frame)
        controls.pack(pady=10)

        # Кнопки управления воспроизведением
        self.prev_btn = ttk.Button(controls, text="◀◀", width=4, command=self._prev_frame)
        self.prev_btn.pack(side=tk.LEFT, padx=2)

        self.play_btn = ttk.Button(controls, text="▶", width=4, command=self._toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=2)

        self.next_btn = ttk.Button(controls, text="▶▶", width=4, command=self._next_frame)
        self.next_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(controls, text="◼", width=4, command=self._stop)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        # Настройки
        settings = ttk.Frame(main_frame)
        settings.pack(fill=tk.X, pady=5)

        # FPS
        fps_frame = ttk.Frame(settings)
        fps_frame.pack(fill=tk.X, pady=2)

        ttk.Label(fps_frame, text="FPS:").pack(side=tk.LEFT, padx=5)
        self.fps_var = tk.IntVar(value=10)
        self.fps_spinbox = ttk.Spinbox(
            fps_frame,
            from_=1, to=60,
            textvariable=self.fps_var,
            width=5,
            command=self._on_fps_change
        )
        self.fps_spinbox.pack(side=tk.LEFT)
        self.fps_spinbox.bind("<Return>", lambda e: self._on_fps_change())

        # Режим воспроизведения
        mode_frame = ttk.Frame(settings)
        mode_frame.pack(fill=tk.X, pady=2)

        ttk.Label(mode_frame, text="Режим:").pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="loop")
        self.mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=["once", "loop", "ping_pong"],
            state="readonly",
            width=12
        )
        self.mode_combo.pack(side=tk.LEFT)
        self.mode_combo.bind("<<ComboboxSelected>>", lambda e: self._on_mode_change())

        # Шкала времени (слайдер)
        timeline_frame = ttk.Frame(main_frame)
        timeline_frame.pack(fill=tk.X, pady=5, padx=10)

        self.timeline = ttk.Scale(
            timeline_frame,
            from_=0, to=1,
            orient=tk.HORIZONTAL,
            command=self._on_timeline_change
        )
        self.timeline.pack(fill=tk.X)

    def set_frames(self, images: List[Any]):
        """Установка кадров анимации (PIL Images)"""
        self.frames = images
        self.photo_frames = []

        if not images:
            self.canvas.delete(self.image_item) if self.image_item else None
            self.image_item = None
            self.canvas.itemconfigure(self.default_text, state="normal")
            self.frame_label.configure(text="Кадр: 0 / 0")
            self.timeline.configure(to=1)
            return

        try:
            from PIL import Image, ImageTk

            # Конвертируем все кадры
            for img in images:
                # Ресайз с сохранением пропорций
                img_copy = img.copy()
                img_copy.thumbnail((self.preview_size, self.preview_size), Image.Resampling.LANCZOS)

                # Центрирование на холсте
                photo = ImageTk.PhotoImage(img_copy)
                self.photo_frames.append(photo)

            self.canvas.itemconfigure(self.default_text, state="hidden")
            self.timeline.configure(to=max(0, len(images) - 1))
            self.current_frame = 0
            self._show_frame(0)

        except Exception as e:
            print(f"Error loading frames: {e}")

    def _show_frame(self, index: int):
        """Отображение кадра по индексу"""
        if not self.photo_frames or index < 0 or index >= len(self.photo_frames):
            return

        self.current_frame = index

        # Удаляем старое изображение
        if self.image_item:
            self.canvas.delete(self.image_item)

        # Отображаем новое
        self.image_item = self.canvas.create_image(
            self.preview_size // 2,
            self.preview_size // 2,
            image=self.photo_frames[index],
            anchor=tk.CENTER
        )

        # Обновляем индикаторы
        self.frame_label.configure(text=f"Кадр: {index + 1} / {len(self.photo_frames)}")
        self.timeline.set(index)

    def _toggle_play(self):
        """Переключение воспроизведения"""
        if self.is_playing:
            self._pause()
        else:
            self._play()

    def _play(self):
        """Запуск воспроизведения"""
        if not self.photo_frames:
            return

        self.is_playing = True
        self.play_btn.configure(text="⏸")
        self._animate()

    def _pause(self):
        """Пауза"""
        self.is_playing = False
        self.play_btn.configure(text="▶")
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    def _stop(self):
        """Остановка и сброс"""
        self._pause()
        self.current_frame = 0
        self.direction = 1
        self._show_frame(0)

    def _animate(self):
        """Анимация кадра"""
        if not self.is_playing or not self.photo_frames:
            return

        # Следующий кадр
        next_frame = self.current_frame + self.direction

        if self.loop_mode == "once":
            if next_frame >= len(self.photo_frames):
                self._pause()
                return
            elif next_frame < 0:
                next_frame = 0
        elif self.loop_mode == "loop":
            next_frame = next_frame % len(self.photo_frames)
        elif self.loop_mode == "ping_pong":
            if next_frame >= len(self.photo_frames):
                self.direction = -1
                next_frame = len(self.photo_frames) - 2
            elif next_frame < 0:
                self.direction = 1
                next_frame = 1
            next_frame = max(0, min(next_frame, len(self.photo_frames) - 1))

        self._show_frame(next_frame)

        # Следующий тик
        delay = int(1000 / self.fps)
        self.animation_job = self.after(delay, self._animate)

    def _prev_frame(self):
        """Предыдущий кадр"""
        if self.photo_frames:
            new_frame = (self.current_frame - 1) % len(self.photo_frames)
            self._show_frame(new_frame)

    def _next_frame(self):
        """Следующий кадр"""
        if self.photo_frames:
            new_frame = (self.current_frame + 1) % len(self.photo_frames)
            self._show_frame(new_frame)

    def _on_timeline_change(self, value):
        """Обработка изменения таймлайна"""
        if self.photo_frames:
            frame = int(float(value))
            if frame != self.current_frame:
                self._show_frame(frame)

    def _on_fps_change(self):
        """Обработка изменения FPS"""
        try:
            self.fps = max(1, min(60, self.fps_var.get()))
        except tk.TclError:
            self.fps = 10

    def _on_mode_change(self):
        """Обработка изменения режима"""
        self.loop_mode = self.mode_var.get()
        self.direction = 1

    def get_fps(self) -> int:
        return self.fps

    def set_fps(self, fps: int):
        self.fps = max(1, min(60, fps))
        self.fps_var.set(self.fps)

    def get_loop_mode(self) -> str:
        return self.loop_mode

    def set_loop_mode(self, mode: str):
        if mode in ["once", "loop", "ping_pong"]:
            self.loop_mode = mode
            self.mode_var.set(mode)


class AnimationEditor(ttk.Frame):
    """Полный редактор анимации с кадрами и предпросмотром"""

    MAX_FRAMES = 8

    def __init__(
        self,
        parent: tk.Widget,
        assets_path: str = "",
        on_change: Callable = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.assets_path = assets_path
        self.on_change = on_change
        self.frame_items: List[AnimationFrameItem] = []
        self.loaded_images: List[Any] = []  # PIL Images

        # Горизонтальный layout
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Левая часть - список кадров
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=2)

        # Заголовок
        header = ttk.Frame(left_frame)
        header.pack(fill=tk.X, pady=5)

        ttk.Label(header, text="Кадры анимации (1-8)", font=("TkDefaultFont", 10, "bold")).pack(side=tk.LEFT)

        self.frame_count_label = ttk.Label(header, text="0 / 8")
        self.frame_count_label.pack(side=tk.RIGHT, padx=10)

        # Кнопка загрузки спрайтов
        ttk.Button(header, text="Загрузить спрайты...", command=self._load_sprites).pack(side=tk.RIGHT)

        # Прокручиваемый список кадров
        self.frames_container = ScrollableFrame(left_frame)
        self.frames_container.pack(fill=tk.BOTH, expand=True)

        # Правая часть - превью
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)

        ttk.Label(right_frame, text="Предпросмотр", font=("TkDefaultFont", 10, "bold")).pack(pady=5)

        self.preview = AnimationPreview(right_frame, preview_size=128)
        self.preview.pack(fill=tk.BOTH, expand=True)

    def _load_sprites(self):
        """Загрузка нескольких спрайтов для анимации"""
        from tkinter import filedialog, messagebox
        import os

        # Проверяем лимит
        available_slots = self.MAX_FRAMES - len(self.frame_items)
        if available_slots <= 0:
            messagebox.showwarning(
                "Лимит кадров",
                f"Достигнут максимум кадров ({self.MAX_FRAMES}). Удалите существующие кадры для добавления новых."
            )
            return

        initial_dir = self.assets_path
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()

        filepaths = filedialog.askopenfilenames(
            title=f"Выберите спрайты (макс. {available_slots})",
            initialdir=initial_dir,
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Все файлы", "*.*")
            ]
        )

        if not filepaths:
            return

        # Ограничиваем количество файлов
        if len(filepaths) > available_slots:
            messagebox.showinfo(
                "Ограничение",
                f"Выбрано {len(filepaths)} файлов, но доступно только {available_slots} слотов. "
                f"Будут добавлены первые {available_slots} файлов."
            )
            filepaths = filepaths[:available_slots]

        # Загружаем каждый спрайт
        from PIL import Image

        for filepath in filepaths:
            try:
                # Загружаем изображение
                img = Image.open(filepath)

                # Относительный путь
                try:
                    rel_path = os.path.relpath(filepath, self.assets_path)
                except ValueError:
                    rel_path = filepath

                # Создаем элемент кадра
                frame_item = AnimationFrameItem(
                    self.frames_container.scrollable_frame,
                    frame_index=len(self.frame_items),
                    on_select=self._on_select_sprite,
                    on_delete=self._on_delete_frame,
                    on_move_up=self._on_move_up,
                    on_move_down=self._on_move_down,
                )
                frame_item.pack(fill=tk.X, pady=2, padx=5)

                # Устанавливаем спрайт
                frame_item.set_sprite(rel_path, img)

                self.frame_items.append(frame_item)
                self.loaded_images.append(img)

            except Exception as e:
                print(f"Error loading sprite {filepath}: {e}")

        self._update_frame_count()
        self._update_preview()
        self._notify_change()

    def _on_select_sprite(self, frame_item: AnimationFrameItem):
        """Выбор спрайта для кадра"""
        from tkinter import filedialog
        import os

        initial_dir = self.assets_path
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()

        filepath = filedialog.askopenfilename(
            title="Выберите спрайт",
            initialdir=initial_dir,
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Все файлы", "*.*")
            ]
        )

        if filepath:
            try:
                from PIL import Image

                # Загружаем изображение
                img = Image.open(filepath)

                # Относительный путь
                try:
                    rel_path = os.path.relpath(filepath, self.assets_path)
                except ValueError:
                    rel_path = filepath

                # Находим индекс кадра
                idx = self.frame_items.index(frame_item)

                # Обновляем данные
                frame_item.set_sprite(rel_path, img)
                self.loaded_images[idx] = img

                # Обновляем превью
                self._update_preview()
                self._notify_change()

            except Exception as e:
                print(f"Error loading sprite: {e}")

    def _on_delete_frame(self, frame_item: AnimationFrameItem):
        """Удаление кадра"""
        if frame_item in self.frame_items:
            idx = self.frame_items.index(frame_item)
            self.frame_items.remove(frame_item)
            del self.loaded_images[idx]
            frame_item.destroy()

            # Перенумеровываем кадры
            for i, item in enumerate(self.frame_items):
                item.frame_index = i

            self._update_frame_count()
            self._update_preview()
            self._notify_change()

    def _on_move_up(self, frame_item: AnimationFrameItem):
        """Перемещение кадра вверх"""
        idx = self.frame_items.index(frame_item)
        if idx > 0:
            # Меняем местами
            self.frame_items[idx], self.frame_items[idx-1] = self.frame_items[idx-1], self.frame_items[idx]
            self.loaded_images[idx], self.loaded_images[idx-1] = self.loaded_images[idx-1], self.loaded_images[idx]

            # Перепаковываем виджеты
            self._repack_frames()
            self._update_preview()
            self._notify_change()

    def _on_move_down(self, frame_item: AnimationFrameItem):
        """Перемещение кадра вниз"""
        idx = self.frame_items.index(frame_item)
        if idx < len(self.frame_items) - 1:
            # Меняем местами
            self.frame_items[idx], self.frame_items[idx+1] = self.frame_items[idx+1], self.frame_items[idx]
            self.loaded_images[idx], self.loaded_images[idx+1] = self.loaded_images[idx+1], self.loaded_images[idx]

            # Перепаковываем виджеты
            self._repack_frames()
            self._update_preview()
            self._notify_change()

    def _repack_frames(self):
        """Перепаковка виджетов кадров"""
        for i, item in enumerate(self.frame_items):
            item.frame_index = i
            item.pack_forget()

        for item in self.frame_items:
            item.pack(fill=tk.X, pady=2, padx=5)

    def _update_frame_count(self):
        """Обновление счетчика кадров"""
        self.frame_count_label.configure(text=f"{len(self.frame_items)} / {self.MAX_FRAMES}")

    def _update_preview(self):
        """Обновление превью анимации"""
        valid_images = [img for img in self.loaded_images if img is not None]
        self.preview.set_frames(valid_images)

    def _notify_change(self):
        """Уведомление об изменении"""
        if self.on_change:
            self.on_change()

    def get_frames_data(self) -> List[Dict[str, Any]]:
        """Получение данных кадров"""
        return [item.get_data() for item in self.frame_items]

    def set_frames_data(self, frames: List[Dict[str, Any]]):
        """Установка данных кадров"""
        # Очищаем
        for item in self.frame_items:
            item.destroy()
        self.frame_items.clear()
        self.loaded_images.clear()

        # Добавляем кадры
        for frame_data in frames[:self.MAX_FRAMES]:
            frame_item = AnimationFrameItem(
                self.frames_container.scrollable_frame,
                frame_index=len(self.frame_items),
                on_select=self._on_select_sprite,
                on_delete=self._on_delete_frame,
                on_move_up=self._on_move_up,
                on_move_down=self._on_move_down,
            )
            frame_item.pack(fill=tk.X, pady=2, padx=5)

            # Загружаем спрайт если есть путь
            sprite_path = frame_data.get("sprite_path", "")
            if sprite_path:
                try:
                    from PIL import Image
                    import os

                    full_path = os.path.join(self.assets_path, sprite_path)
                    if os.path.exists(full_path):
                        img = Image.open(full_path)
                        frame_item.set_sprite(sprite_path, img)
                        self.loaded_images.append(img)
                    else:
                        frame_item.set_sprite(sprite_path, None)
                        self.loaded_images.append(None)
                except Exception:
                    frame_item.set_sprite(sprite_path, None)
                    self.loaded_images.append(None)
            else:
                self.loaded_images.append(None)

            self.frame_items.append(frame_item)

        self._update_frame_count()
        self._update_preview()

    def get_fps(self) -> int:
        return self.preview.get_fps()

    def set_fps(self, fps: int):
        self.preview.set_fps(fps)

    def get_loop_mode(self) -> str:
        return self.preview.get_loop_mode()

    def set_loop_mode(self, mode: str):
        self.preview.set_loop_mode(mode)


class AnimationDisplaySettings(ttk.LabelFrame):
    """Настройки отображения анимации на поле боя"""

    def __init__(self, parent: tk.Widget, on_change: Callable = None, **kwargs):
        super().__init__(parent, text="Отображение анимации", **kwargs)
        self.on_change = on_change

        # Импортируем модели
        from ..models import (
            AnimationDisplayType,
            AnimationAnchor,
            ProjectileTrajectory,
        )

        self.display_types = AnimationDisplayType.get_display_names()
        self.anchor_points = AnimationAnchor.get_display_names()
        self.trajectories = ProjectileTrajectory.get_display_names()

        self._create_widgets()

    def _create_widgets(self):
        # Тип отображения
        type_frame = ttk.Frame(self)
        type_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Label(type_frame, text="Тип анимации:").pack(side=tk.LEFT)
        # Используем отображаемое имя, а не ключ
        default_display_type = self.display_types.get("on_target", "На цели")
        self.display_type_var = tk.StringVar(value=default_display_type)
        self.display_type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.display_type_var,
            values=list(self.display_types.values()),
            state="readonly",
            width=25
        )
        self.display_type_combo.pack(side=tk.LEFT, padx=5)
        self.display_type_combo.bind("<<ComboboxSelected>>", self._on_type_changed)

        # Точка привязки
        anchor_frame = ttk.Frame(self)
        anchor_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Label(anchor_frame, text="Точка привязки:").pack(side=tk.LEFT)
        # Используем отображаемое имя, а не ключ
        default_anchor = self.anchor_points.get("center", "Центр")
        self.anchor_var = tk.StringVar(value=default_anchor)
        self.anchor_combo = ttk.Combobox(
            anchor_frame,
            textvariable=self.anchor_var,
            values=list(self.anchor_points.values()),
            state="readonly",
            width=20
        )
        self.anchor_combo.pack(side=tk.LEFT, padx=5)
        self.anchor_combo.bind("<<ComboboxSelected>>", self._notify_change)

        # Контейнер для специфичных настроек
        self.settings_container = ttk.Frame(self)
        self.settings_container.pack(fill=tk.BOTH, expand=True, pady=5)

        # Создаем фреймы для разных типов
        self._create_projectile_settings()
        self._create_beam_settings()
        self._create_area_settings()
        self._create_timing_settings()

        # Показываем нужный фрейм
        self._update_visible_settings()

    def _create_projectile_settings(self):
        """Настройки снаряда"""
        self.projectile_frame = ttk.LabelFrame(
            self.settings_container, text="Настройки снаряда"
        )

        # Скорость
        speed_frame = ttk.Frame(self.projectile_frame)
        speed_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(speed_frame, text="Скорость (пикс/сек):").pack(side=tk.LEFT)
        self.proj_speed_var = tk.DoubleVar(value=300.0)
        ttk.Spinbox(
            speed_frame, textvariable=self.proj_speed_var,
            from_=50, to=1000, increment=50, width=8
        ).pack(side=tk.LEFT, padx=5)

        # Траектория
        traj_frame = ttk.Frame(self.projectile_frame)
        traj_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(traj_frame, text="Траектория:").pack(side=tk.LEFT)
        self.proj_trajectory_var = tk.StringVar(value="straight")
        ttk.Combobox(
            traj_frame,
            textvariable=self.proj_trajectory_var,
            values=list(self.trajectories.values()),
            state="readonly", width=15
        ).pack(side=tk.LEFT, padx=5)

        # Высота дуги
        arc_frame = ttk.Frame(self.projectile_frame)
        arc_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(arc_frame, text="Высота дуги:").pack(side=tk.LEFT)
        self.proj_arc_height_var = tk.DoubleVar(value=50.0)
        ttk.Spinbox(
            arc_frame, textvariable=self.proj_arc_height_var,
            from_=0, to=200, increment=10, width=8
        ).pack(side=tk.LEFT, padx=5)

        # Авто-поворот
        rotate_frame = ttk.Frame(self.projectile_frame)
        rotate_frame.pack(fill=tk.X, pady=2, padx=5)
        self.proj_auto_rotate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            rotate_frame, text="Авто-поворот к цели",
            variable=self.proj_auto_rotate_var
        ).pack(side=tk.LEFT)

        # Смещение угла
        offset_frame = ttk.Frame(self.projectile_frame)
        offset_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(offset_frame, text="Смещение угла (°):").pack(side=tk.LEFT)
        self.proj_rotation_offset_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(
            offset_frame, textvariable=self.proj_rotation_offset_var,
            from_=-180, to=180, increment=15, width=8
        ).pack(side=tk.LEFT, padx=5)

        # След
        trail_frame = ttk.Frame(self.projectile_frame)
        trail_frame.pack(fill=tk.X, pady=2, padx=5)
        self.proj_trail_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            trail_frame, text="След за снарядом",
            variable=self.proj_trail_var
        ).pack(side=tk.LEFT)

        ttk.Label(trail_frame, text="Цвет:").pack(side=tk.LEFT, padx=(10, 0))
        self.proj_trail_color_var = tk.StringVar(value="#FFFFFF")
        ttk.Entry(
            trail_frame, textvariable=self.proj_trail_color_var, width=10
        ).pack(side=tk.LEFT, padx=5)

    def _create_beam_settings(self):
        """Настройки луча"""
        self.beam_frame = ttk.LabelFrame(
            self.settings_container, text="Настройки луча"
        )

        # Ширина
        width_frame = ttk.Frame(self.beam_frame)
        width_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(width_frame, text="Ширина (пикс):").pack(side=tk.LEFT)
        self.beam_width_var = tk.IntVar(value=8)
        ttk.Spinbox(
            width_frame, textvariable=self.beam_width_var,
            from_=1, to=32, increment=1, width=6
        ).pack(side=tk.LEFT, padx=5)

        # Длительность
        dur_frame = ttk.Frame(self.beam_frame)
        dur_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(dur_frame, text="Длительность (мс):").pack(side=tk.LEFT)
        self.beam_duration_var = tk.IntVar(value=500)
        ttk.Spinbox(
            dur_frame, textvariable=self.beam_duration_var,
            from_=100, to=2000, increment=100, width=8
        ).pack(side=tk.LEFT, padx=5)

        # Волнистость
        wave_frame = ttk.Frame(self.beam_frame)
        wave_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(wave_frame, text="Амплитуда волны:").pack(side=tk.LEFT)
        self.beam_wave_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(
            wave_frame, textvariable=self.beam_wave_var,
            from_=0, to=50, increment=5, width=6
        ).pack(side=tk.LEFT, padx=5)

        # Цвета
        color_frame = ttk.Frame(self.beam_frame)
        color_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(color_frame, text="Цвет начала:").pack(side=tk.LEFT)
        self.beam_color_start_var = tk.StringVar(value="#FFFFFF")
        ttk.Entry(
            color_frame, textvariable=self.beam_color_start_var, width=10
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(color_frame, text="Цвет конца:").pack(side=tk.LEFT)
        self.beam_color_end_var = tk.StringVar(value="#FFFFFF")
        ttk.Entry(
            color_frame, textvariable=self.beam_color_end_var, width=10
        ).pack(side=tk.LEFT, padx=5)

        # Свечение
        glow_frame = ttk.Frame(self.beam_frame)
        glow_frame.pack(fill=tk.X, pady=2, padx=5)
        self.beam_glow_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            glow_frame, text="Эффект свечения",
            variable=self.beam_glow_var
        ).pack(side=tk.LEFT)

        ttk.Label(glow_frame, text="Радиус:").pack(side=tk.LEFT, padx=(10, 0))
        self.beam_glow_radius_var = tk.IntVar(value=4)
        ttk.Spinbox(
            glow_frame, textvariable=self.beam_glow_radius_var,
            from_=1, to=16, increment=1, width=5
        ).pack(side=tk.LEFT, padx=5)

    def _create_area_settings(self):
        """Настройки области"""
        self.area_frame = ttk.LabelFrame(
            self.settings_container, text="Настройки области"
        )

        # Радиус
        radius_frame = ttk.Frame(self.area_frame)
        radius_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(radius_frame, text="Радиус (клетки):").pack(side=tk.LEFT)
        self.area_radius_var = tk.IntVar(value=1)
        ttk.Spinbox(
            radius_frame, textvariable=self.area_radius_var,
            from_=1, to=5, increment=1, width=5
        ).pack(side=tk.LEFT, padx=5)

        # Форма
        shape_frame = ttk.Frame(self.area_frame)
        shape_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(shape_frame, text="Форма:").pack(side=tk.LEFT)
        self.area_shape_var = tk.StringVar(value="circle")
        ttk.Combobox(
            shape_frame,
            textvariable=self.area_shape_var,
            values=["circle", "square", "cone", "line"],
            state="readonly", width=10
        ).pack(side=tk.LEFT, padx=5)

        # Цвета
        color_frame = ttk.Frame(self.area_frame)
        color_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(color_frame, text="Цвет заливки:").pack(side=tk.LEFT)
        self.area_fill_color_var = tk.StringVar(value="#FF0000")
        ttk.Entry(
            color_frame, textvariable=self.area_fill_color_var, width=10
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(color_frame, text="Прозрачность:").pack(side=tk.LEFT)
        self.area_alpha_var = tk.DoubleVar(value=0.3)
        ttk.Spinbox(
            color_frame, textvariable=self.area_alpha_var,
            from_=0.1, to=1.0, increment=0.1, width=5
        ).pack(side=tk.LEFT, padx=5)

        # Граница
        border_frame = ttk.Frame(self.area_frame)
        border_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(border_frame, text="Цвет границы:").pack(side=tk.LEFT)
        self.area_border_color_var = tk.StringVar(value="#FFFFFF")
        ttk.Entry(
            border_frame, textvariable=self.area_border_color_var, width=10
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(border_frame, text="Толщина:").pack(side=tk.LEFT)
        self.area_border_width_var = tk.IntVar(value=2)
        ttk.Spinbox(
            border_frame, textvariable=self.area_border_width_var,
            from_=1, to=5, increment=1, width=5
        ).pack(side=tk.LEFT, padx=5)

        # Пульсация
        pulse_frame = ttk.Frame(self.area_frame)
        pulse_frame.pack(fill=tk.X, pady=2, padx=5)
        self.area_pulse_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            pulse_frame, text="Пульсация",
            variable=self.area_pulse_var
        ).pack(side=tk.LEFT)

    def _create_timing_settings(self):
        """Настройки таймингов"""
        self.timing_frame = ttk.LabelFrame(
            self.settings_container, text="Тайминги"
        )

        # Когда применяется урон
        apply_frame = ttk.Frame(self.timing_frame)
        apply_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(apply_frame, text="Применение урона:").pack(side=tk.LEFT)
        self.timing_apply_var = tk.StringVar(value="on_hit")
        ttk.Combobox(
            apply_frame,
            textvariable=self.timing_apply_var,
            values=["on_cast", "on_hit", "on_end"],
            state="readonly", width=10
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(apply_frame, text="(on_cast / on_hit / on_end)").pack(side=tk.LEFT)

        # Задержка
        delay_frame = ttk.Frame(self.timing_frame)
        delay_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(delay_frame, text="Задержка урона (мс):").pack(side=tk.LEFT)
        self.timing_delay_var = tk.IntVar(value=0)
        ttk.Spinbox(
            delay_frame, textvariable=self.timing_delay_var,
            from_=0, to=2000, increment=50, width=8
        ).pack(side=tk.LEFT, padx=5)

        # Мульти-удары
        multi_frame = ttk.Frame(self.timing_frame)
        multi_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(multi_frame, text="Задержка между ударами (мс):").pack(side=tk.LEFT)
        self.timing_multi_delay_var = tk.IntVar(value=200)
        ttk.Spinbox(
            multi_frame, textvariable=self.timing_multi_delay_var,
            from_=50, to=1000, increment=50, width=8
        ).pack(side=tk.LEFT, padx=5)

        # Задержка звука
        sound_frame = ttk.Frame(self.timing_frame)
        sound_frame.pack(fill=tk.X, pady=2, padx=5)
        ttk.Label(sound_frame, text="Задержка звука (мс):").pack(side=tk.LEFT)
        self.timing_sound_delay_var = tk.IntVar(value=0)
        ttk.Spinbox(
            sound_frame, textvariable=self.timing_sound_delay_var,
            from_=0, to=1000, increment=50, width=8
        ).pack(side=tk.LEFT, padx=5)

        # Тайминги всегда видны
        self.timing_frame.pack(fill=tk.X, pady=5, padx=5)

    def _on_type_changed(self, event=None):
        """Обработка изменения типа анимации"""
        self._update_visible_settings()
        self._notify_change()

    def _update_visible_settings(self):
        """Обновление видимости настроек"""
        # Скрываем все специфичные настройки
        self.projectile_frame.pack_forget()
        self.beam_frame.pack_forget()
        self.area_frame.pack_forget()

        # Получаем выбранный тип
        display_name = self.display_type_var.get()
        type_key = None
        for key, name in self.display_types.items():
            if name == display_name:
                type_key = key
                break

        # Показываем нужные настройки
        if type_key == "projectile":
            self.projectile_frame.pack(fill=tk.X, pady=5, padx=5)
        elif type_key in ("beam", "sprite_beam"):
            self.beam_frame.pack(fill=tk.X, pady=5, padx=5)
        elif type_key == "area":
            self.area_frame.pack(fill=tk.X, pady=5, padx=5)

    def _notify_change(self, event=None):
        if self.on_change:
            self.on_change()

    def _get_key_by_display_name(self, display_names: Dict[str, str], display_name: str) -> str:
        """Получить ключ по отображаемому имени"""
        for key, name in display_names.items():
            if name == display_name:
                return key
        return list(display_names.keys())[0]

    def get_data(self) -> Dict[str, Any]:
        """Получить все настройки отображения"""
        display_type = self._get_key_by_display_name(
            self.display_types, self.display_type_var.get()
        )
        anchor = self._get_key_by_display_name(
            self.anchor_points, self.anchor_var.get()
        )
        trajectory = self._get_key_by_display_name(
            self.trajectories, self.proj_trajectory_var.get()
        )

        data = {
            "display_type": display_type,
            "anchor_point": anchor,
            "timing": {
                "damage_apply_at": self.timing_apply_var.get(),
                "damage_delay_ms": self.timing_delay_var.get(),
                "multi_hit_delay_ms": self.timing_multi_delay_var.get(),
                "sound_delay_ms": self.timing_sound_delay_var.get(),
            }
        }

        # Добавляем специфичные настройки
        if display_type == "projectile":
            data["projectile"] = {
                "speed": self.proj_speed_var.get(),
                "trajectory": trajectory,
                "arc_height": self.proj_arc_height_var.get(),
                "auto_rotate": self.proj_auto_rotate_var.get(),
                "rotation_offset": self.proj_rotation_offset_var.get(),
                "trail_enabled": self.proj_trail_var.get(),
                "trail_color": self.proj_trail_color_var.get(),
            }

        elif display_type in ("beam", "sprite_beam"):
            data["beam"] = {
                "width": self.beam_width_var.get(),
                "duration_ms": self.beam_duration_var.get(),
                "wave_amplitude": self.beam_wave_var.get(),
                "color_start": self.beam_color_start_var.get(),
                "color_end": self.beam_color_end_var.get(),
                "glow_enabled": self.beam_glow_var.get(),
                "glow_radius": self.beam_glow_radius_var.get(),
            }

        elif display_type == "area":
            data["area_effect"] = {
                "radius_cells": self.area_radius_var.get(),
                "shape": self.area_shape_var.get(),
                "fill_color": self.area_fill_color_var.get(),
                "fill_alpha": self.area_alpha_var.get(),
                "border_color": self.area_border_color_var.get(),
                "border_width": self.area_border_width_var.get(),
                "pulse_enabled": self.area_pulse_var.get(),
            }

        return data

    def set_data(self, data: Dict[str, Any]):
        """Установить настройки отображения"""
        # Тип отображения
        display_type = data.get("display_type", "on_target")
        display_name = self.display_types.get(display_type, "На цели")
        self.display_type_var.set(display_name)

        # Точка привязки
        anchor = data.get("anchor_point", "center")
        anchor_name = self.anchor_points.get(anchor, "Центр")
        self.anchor_var.set(anchor_name)

        # Тайминги
        timing = data.get("timing", {})
        self.timing_apply_var.set(timing.get("damage_apply_at", "on_hit"))
        self.timing_delay_var.set(timing.get("damage_delay_ms", 0))
        self.timing_multi_delay_var.set(timing.get("multi_hit_delay_ms", 200))
        self.timing_sound_delay_var.set(timing.get("sound_delay_ms", 0))

        # Снаряд
        projectile = data.get("projectile", {})
        self.proj_speed_var.set(projectile.get("speed", 300.0))
        trajectory = projectile.get("trajectory", "straight")
        trajectory_name = self.trajectories.get(trajectory, "Прямая")
        self.proj_trajectory_var.set(trajectory_name)
        self.proj_arc_height_var.set(projectile.get("arc_height", 50.0))
        self.proj_auto_rotate_var.set(projectile.get("auto_rotate", True))
        self.proj_rotation_offset_var.set(projectile.get("rotation_offset", 0.0))
        self.proj_trail_var.set(projectile.get("trail_enabled", False))
        self.proj_trail_color_var.set(projectile.get("trail_color", "#FFFFFF"))

        # Луч
        beam = data.get("beam", {})
        self.beam_width_var.set(beam.get("width", 8))
        self.beam_duration_var.set(beam.get("duration_ms", 500))
        self.beam_wave_var.set(beam.get("wave_amplitude", 0.0))
        self.beam_color_start_var.set(beam.get("color_start", "#FFFFFF"))
        self.beam_color_end_var.set(beam.get("color_end", "#FFFFFF"))
        self.beam_glow_var.set(beam.get("glow_enabled", True))
        self.beam_glow_radius_var.set(beam.get("glow_radius", 4))

        # Область
        area = data.get("area_effect", {})
        self.area_radius_var.set(area.get("radius_cells", 1))
        self.area_shape_var.set(area.get("shape", "circle"))
        self.area_fill_color_var.set(area.get("fill_color", "#FF0000"))
        self.area_alpha_var.set(area.get("fill_alpha", 0.3))
        self.area_border_color_var.set(area.get("border_color", "#FFFFFF"))
        self.area_border_width_var.set(area.get("border_width", 2))
        self.area_pulse_var.set(area.get("pulse_enabled", False))

        # Обновляем видимость
        self._update_visible_settings()
