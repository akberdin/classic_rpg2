"""
Виджеты для Items Crafter
Переиспользуемые компоненты UI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Callable, List, Dict, Any, Tuple


class LabeledEntry(ttk.Frame):
    """Поле ввода с меткой"""

    def __init__(self, parent, label: str, width: int = 30, **kwargs):
        super().__init__(parent)
        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width, **kwargs)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class LabeledSpinbox(ttk.Frame):
    """Числовое поле с меткой"""

    def __init__(self, parent, label: str, from_: int = 0, to: int = 9999,
                 width: int = 10, **kwargs):
        super().__init__(parent)
        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))
        self.var = tk.IntVar(value=0)
        self.spinbox = ttk.Spinbox(
            self, textvariable=self.var, from_=from_, to=to,
            width=width, **kwargs
        )
        self.spinbox.pack(side=tk.LEFT)

    def get(self) -> int:
        try:
            return self.var.get()
        except tk.TclError:
            return 0

    def set(self, value: int):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class LabeledFloatSpinbox(ttk.Frame):
    """Числовое поле с плавающей точкой и меткой"""

    def __init__(self, parent, label: str, from_: float = 0.0, to: float = 100.0,
                 increment: float = 0.1, width: int = 10, **kwargs):
        super().__init__(parent)
        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))
        self.var = tk.DoubleVar(value=0.0)
        self.spinbox = ttk.Spinbox(
            self, textvariable=self.var, from_=from_, to=to,
            increment=increment, width=width, **kwargs
        )
        self.spinbox.pack(side=tk.LEFT)

    def get(self) -> float:
        try:
            return self.var.get()
        except tk.TclError:
            return 0.0

    def set(self, value: float):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class LabeledCombobox(ttk.Frame):
    """Выпадающий список с меткой"""

    def __init__(self, parent, label: str, values: List[str],
                 width: int = 20, **kwargs):
        super().__init__(parent)
        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))
        self.var = tk.StringVar()
        self.combobox = ttk.Combobox(
            self, textvariable=self.var, values=values,
            width=width, state="readonly", **kwargs
        )
        self.combobox.pack(side=tk.LEFT)
        if values:
            self.combobox.current(0)

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str):
        self.var.set(value)

    def set_values(self, values: List[str]):
        self.combobox['values'] = values

    def bind_change(self, callback: Callable):
        self.combobox.bind("<<ComboboxSelected>>", lambda e: callback())


class LabeledCheckbox(ttk.Frame):
    """Флажок с меткой"""

    def __init__(self, parent, label: str, **kwargs):
        super().__init__(parent)
        self.var = tk.BooleanVar(value=False)
        self.checkbox = ttk.Checkbutton(
            self, text=label, variable=self.var, **kwargs
        )
        self.checkbox.pack(side=tk.LEFT)

    def get(self) -> bool:
        return self.var.get()

    def set(self, value: bool):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class RangeEditor(ttk.Frame):
    """Редактор диапазона значений (min-max)"""

    def __init__(self, parent, label: str, from_: int = 0, to: int = 9999, **kwargs):
        super().__init__(parent)
        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.min_var = tk.IntVar(value=0)
        self.min_spinbox = ttk.Spinbox(
            self, textvariable=self.min_var, from_=from_, to=to, width=8
        )
        self.min_spinbox.pack(side=tk.LEFT)

        ttk.Label(self, text=" - ").pack(side=tk.LEFT)

        self.max_var = tk.IntVar(value=0)
        self.max_spinbox = ttk.Spinbox(
            self, textvariable=self.max_var, from_=from_, to=to, width=8
        )
        self.max_spinbox.pack(side=tk.LEFT)

    def get(self) -> Tuple[int, int]:
        try:
            return (self.min_var.get(), self.max_var.get())
        except tk.TclError:
            return (0, 0)

    def set(self, min_val: int, max_val: int):
        self.min_var.set(min_val)
        self.max_var.set(max_val)

    def set_from_list(self, values: Optional[List[int]]):
        if values and len(values) == 2:
            self.set(values[0], values[1])
        else:
            self.set(0, 0)

    def bind_change(self, callback: Callable):
        self.min_var.trace_add("write", lambda *args: callback())
        self.max_var.trace_add("write", lambda *args: callback())


class MultiSelectList(ttk.Frame):
    """Список с множественным выбором"""

    def __init__(self, parent, label: str, options: Dict[str, str],
                 height: int = 6, **kwargs):
        super().__init__(parent)
        self.options = options

        ttk.Label(self, text=label).pack(anchor=tk.W)

        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            list_frame, selectmode=tk.MULTIPLE, height=height,
            yscrollcommand=scrollbar.set, exportselection=False
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Заполняем список
        self._keys = list(options.keys())
        for key in self._keys:
            self.listbox.insert(tk.END, options[key])

    def get_selected_keys(self) -> List[str]:
        """Получить ключи выбранных элементов"""
        selected_indices = self.listbox.curselection()
        return [self._keys[i] for i in selected_indices]

    def set_selected_keys(self, keys: List[str]):
        """Установить выбранные элементы по ключам"""
        self.listbox.selection_clear(0, tk.END)
        for key in keys:
            if key in self._keys:
                index = self._keys.index(key)
                self.listbox.selection_set(index)

    def bind_change(self, callback: Callable):
        self.listbox.bind("<<ListboxSelect>>", lambda e: callback())


class ItemListPanel(ttk.Frame):
    """Панель со списком предметов и кнопками управления"""

    def __init__(self, parent, on_select: Callable, on_add: Callable,
                 on_delete: Callable, on_duplicate: Optional[Callable] = None):
        super().__init__(parent)
        self.on_select = on_select
        self.on_add = on_add
        self.on_delete = on_delete
        self.on_duplicate = on_duplicate

        # Поиск
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_list())
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Список
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set,
            exportselection=False
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._on_list_select)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="Добавить", command=self.on_add).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self._delete_selected).pack(side=tk.LEFT, padx=2)
        if self.on_duplicate:
            ttk.Button(btn_frame, text="Копировать", command=self._duplicate_selected).pack(side=tk.LEFT, padx=2)

        # Данные
        self._items: List[Tuple[str, str]] = []  # (id, display_name)
        self._filtered_items: List[Tuple[str, str]] = []

    def set_items(self, items: List[Tuple[str, str]]):
        """Установить список предметов: [(id, display_name), ...]"""
        self._items = items
        self._filter_list()

    def _filter_list(self):
        """Фильтрация списка по поисковому запросу"""
        query = self.search_var.get().lower()
        if query:
            self._filtered_items = [
                (item_id, name) for item_id, name in self._items
                if query in name.lower() or query in item_id.lower()
            ]
        else:
            self._filtered_items = self._items.copy()

        self.listbox.delete(0, tk.END)
        for item_id, name in self._filtered_items:
            self.listbox.insert(tk.END, f"{name} [{item_id}]")

    def _on_list_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self._filtered_items):
                item_id = self._filtered_items[index][0]
                self.on_select(item_id)

    def _delete_selected(self):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self._filtered_items):
                item_id = self._filtered_items[index][0]
                if messagebox.askyesno("Подтверждение", f"Удалить '{item_id}'?"):
                    self.on_delete(item_id)

    def _duplicate_selected(self):
        if not self.on_duplicate:
            return
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self._filtered_items):
                item_id = self._filtered_items[index][0]
                self.on_duplicate(item_id)

    def select_item(self, item_id: str):
        """Выбрать предмет в списке по ID"""
        for i, (id_, _) in enumerate(self._filtered_items):
            if id_ == item_id:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(i)
                self.listbox.see(i)
                break


class IngredientEditor(ttk.Frame):
    """Редактор ингредиентов рецепта"""

    def __init__(self, parent, available_items: List[Tuple[str, str]], **kwargs):
        super().__init__(parent)
        self.available_items = available_items  # [(id, name), ...]

        ttk.Label(self, text="Ингредиенты:").pack(anchor=tk.W)

        # Список ингредиентов
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            list_frame, columns=("item", "quantity"),
            show="headings", height=5,
            yscrollcommand=scrollbar.set
        )
        self.tree.heading("item", text="Предмет")
        self.tree.heading("quantity", text="Кол-во")
        self.tree.column("item", width=200)
        self.tree.column("quantity", width=60)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Добавить", command=self._add_ingredient).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self._remove_ingredient).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Изменить", command=self._edit_ingredient).pack(side=tk.LEFT, padx=2)

        self._ingredients: List[Dict[str, Any]] = []

    def set_available_items(self, items: List[Tuple[str, str]]):
        """Обновить список доступных предметов"""
        self.available_items = items

    def get_ingredients(self) -> List[Dict[str, Any]]:
        """Получить список ингредиентов"""
        return self._ingredients.copy()

    def set_ingredients(self, ingredients: List[Dict[str, Any]]):
        """Установить список ингредиентов"""
        self._ingredients = ingredients.copy()
        self._refresh_tree()

    def _refresh_tree(self):
        """Обновить дерево"""
        self.tree.delete(*self.tree.get_children())
        for ing in self._ingredients:
            item_id = ing.get("item", "")
            quantity = ing.get("quantity", 1)
            # Находим название предмета
            item_name = item_id
            for id_, name in self.available_items:
                if id_ == item_id:
                    item_name = name
                    break
            self.tree.insert("", tk.END, values=(item_name, quantity))

    def _add_ingredient(self):
        """Добавить ингредиент"""
        dialog = IngredientDialog(self, self.available_items)
        self.wait_window(dialog)
        if dialog.result:
            self._ingredients.append(dialog.result)
            self._refresh_tree()

    def _remove_ingredient(self):
        """Удалить выбранный ингредиент"""
        selection = self.tree.selection()
        if selection:
            index = self.tree.index(selection[0])
            if 0 <= index < len(self._ingredients):
                del self._ingredients[index]
                self._refresh_tree()

    def _edit_ingredient(self):
        """Редактировать выбранный ингредиент"""
        selection = self.tree.selection()
        if selection:
            index = self.tree.index(selection[0])
            if 0 <= index < len(self._ingredients):
                current = self._ingredients[index]
                dialog = IngredientDialog(
                    self, self.available_items,
                    current_item=current.get("item"),
                    current_quantity=current.get("quantity", 1)
                )
                self.wait_window(dialog)
                if dialog.result:
                    self._ingredients[index] = dialog.result
                    self._refresh_tree()


class IngredientDialog(tk.Toplevel):
    """Диалог добавления/редактирования ингредиента"""

    def __init__(self, parent, available_items: List[Tuple[str, str]],
                 current_item: str = "", current_quantity: int = 1):
        super().__init__(parent)
        self.title("Ингредиент")
        self.geometry("400x150")
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.available_items = available_items

        # Предмет
        ttk.Label(self, text="Предмет:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.item_var = tk.StringVar()
        item_names = [f"{name} [{id_}]" for id_, name in available_items]
        self.item_combo = ttk.Combobox(self, textvariable=self.item_var, values=item_names, width=35)
        self.item_combo.grid(row=0, column=1, padx=10, pady=10)

        # Устанавливаем текущее значение
        if current_item:
            for i, (id_, name) in enumerate(available_items):
                if id_ == current_item:
                    self.item_combo.current(i)
                    break

        # Количество
        ttk.Label(self, text="Количество:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.quantity_var = tk.IntVar(value=current_quantity)
        self.quantity_spin = ttk.Spinbox(self, textvariable=self.quantity_var, from_=1, to=999, width=10)
        self.quantity_spin.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="OK", command=self._ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=10)

    def _ok(self):
        selection = self.item_combo.current()
        if selection >= 0:
            item_id = self.available_items[selection][0]
            self.result = {
                "item": item_id,
                "quantity": self.quantity_var.get()
            }
        self.destroy()


class QualityParametersEditor(ttk.LabelFrame):
    """Редактор параметров по качеству для экипировки"""

    def __init__(self, parent, title: str = "Параметры по качеству", **kwargs):
        super().__init__(parent, text=title)

        self.quality_tabs = ttk.Notebook(self)
        self.quality_tabs.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.quality_frames: Dict[str, ttk.Frame] = {}
        self.quality_widgets: Dict[str, Dict[str, Any]] = {}

        qualities = [
            ("poor", "Плохое"),
            ("common", "Обычное"),
            ("uncommon", "Необычное"),
            ("rare", "Редкое"),
            ("epic", "Эпическое"),
            ("legendary", "Легендарное"),
            ("artifact", "Артефакт"),
        ]

        for quality_id, quality_name in qualities:
            frame = ttk.Frame(self.quality_tabs)
            self.quality_tabs.add(frame, text=quality_name)
            self.quality_frames[quality_id] = frame
            self._create_quality_widgets(frame, quality_id)

    def _create_quality_widgets(self, frame: ttk.Frame, quality_id: str):
        """Создать виджеты для одного качества"""
        widgets = {}

        # Урон (для оружия)
        widgets["damage_range"] = RangeEditor(frame, "Урон:")
        widgets["damage_range"].pack(fill=tk.X, padx=5, pady=2)

        # Защита (для брони)
        widgets["defense_range"] = RangeEditor(frame, "Защита:")
        widgets["defense_range"].pack(fill=tk.X, padx=5, pady=2)

        # Количество статов
        widgets["stats_count_range"] = RangeEditor(frame, "Кол-во статов:")
        widgets["stats_count_range"].pack(fill=tk.X, padx=5, pady=2)

        # Бонус статов
        widgets["stat_bonus_range"] = RangeEditor(frame, "Бонус статов:")
        widgets["stat_bonus_range"].pack(fill=tk.X, padx=5, pady=2)

        # Количество параметров
        widgets["params_count_range"] = RangeEditor(frame, "Кол-во парам.:")
        widgets["params_count_range"].pack(fill=tk.X, padx=5, pady=2)

        # Бонус параметров
        widgets["param_bonus_range"] = RangeEditor(frame, "Бонус парам.:")
        widgets["param_bonus_range"].pack(fill=tk.X, padx=5, pady=2)

        self.quality_widgets[quality_id] = widgets

    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Получить все параметры"""
        result = {}
        for quality_id, widgets in self.quality_widgets.items():
            params = {}
            damage = widgets["damage_range"].get()
            if damage != (0, 0):
                params["damage_range"] = list(damage)
            defense = widgets["defense_range"].get()
            if defense != (0, 0):
                params["defense_range"] = list(defense)
            stats_count = widgets["stats_count_range"].get()
            params["stats_count_range"] = list(stats_count)
            stat_bonus = widgets["stat_bonus_range"].get()
            if stat_bonus != (0, 0):
                params["stat_bonus_range"] = list(stat_bonus)
            params_count = widgets["params_count_range"].get()
            params["params_count_range"] = list(params_count)
            param_bonus = widgets["param_bonus_range"].get()
            if param_bonus != (0, 0):
                params["param_bonus_range"] = list(param_bonus)
            result[quality_id] = params
        return result

    def set_parameters(self, params: Dict[str, Dict[str, Any]]):
        """Установить все параметры"""
        for quality_id, widgets in self.quality_widgets.items():
            if quality_id in params:
                quality_params = params[quality_id]
                widgets["damage_range"].set_from_list(quality_params.get("damage_range"))
                widgets["defense_range"].set_from_list(quality_params.get("defense_range"))
                widgets["stats_count_range"].set_from_list(quality_params.get("stats_count_range"))
                widgets["stat_bonus_range"].set_from_list(quality_params.get("stat_bonus_range"))
                widgets["params_count_range"].set_from_list(quality_params.get("params_count_range"))
                widgets["param_bonus_range"].set_from_list(quality_params.get("param_bonus_range"))


class ColorPicker(ttk.Frame):
    """Выбор цвета"""

    def __init__(self, parent, label: str = "Цвет:", **kwargs):
        super().__init__(parent)
        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.color = (255, 255, 255)
        self.color_label = tk.Label(
            self, width=3, height=1, bg=self._rgb_to_hex(self.color),
            relief=tk.RAISED
        )
        self.color_label.pack(side=tk.LEFT)

        self.rgb_label = ttk.Label(self, text="(255, 255, 255)")
        self.rgb_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(self, text="...", width=3, command=self._pick_color).pack(side=tk.LEFT)

    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _pick_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(
            initialcolor=self._rgb_to_hex(self.color),
            title="Выберите цвет"
        )
        if color[0]:
            self.set(tuple(int(c) for c in color[0]))

    def get(self) -> Tuple[int, int, int]:
        return self.color

    def set(self, rgb: Tuple[int, int, int]):
        self.color = rgb
        self.color_label.configure(bg=self._rgb_to_hex(rgb))
        self.rgb_label.configure(text=f"({rgb[0]}, {rgb[1]}, {rgb[2]})")


class ScrollableFrame(ttk.Frame):
    """Прокручиваемый фрейм"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent)

        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Прокрутка колесом мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
