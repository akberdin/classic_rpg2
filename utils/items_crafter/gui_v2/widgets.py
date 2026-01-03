"""
Виджеты GUI v2.0 с поддержкой буфера обмена

Все текстовые поля поддерживают:
- Ctrl+C - копировать
- Ctrl+X - вырезать
- Ctrl+V - вставить
- Ctrl+A - выделить всё
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List, Dict, Any, Tuple


# ==================== БАЗОВЫЕ ВИДЖЕТЫ С БУФЕРОМ ОБМЕНА ====================

class ClipboardMixin:
    """Миксин для поддержки буфера обмена в виджетах"""

    def setup_clipboard_bindings(self, widget: tk.Widget):
        """Настроить горячие клавиши буфера обмена"""
        widget.bind('<Control-c>', self._on_copy)
        widget.bind('<Control-x>', self._on_cut)
        widget.bind('<Control-v>', self._on_paste)
        widget.bind('<Control-a>', self._on_select_all)

        # Контекстное меню
        self._context_menu = tk.Menu(widget, tearoff=0)
        self._context_menu.add_command(label="Вырезать", command=self._do_cut, accelerator="Ctrl+X")
        self._context_menu.add_command(label="Копировать", command=self._do_copy, accelerator="Ctrl+C")
        self._context_menu.add_command(label="Вставить", command=self._do_paste, accelerator="Ctrl+V")
        self._context_menu.add_separator()
        self._context_menu.add_command(label="Выделить всё", command=self._do_select_all, accelerator="Ctrl+A")

        widget.bind('<Button-3>', self._show_context_menu)

    def _show_context_menu(self, event):
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()

    def _on_copy(self, event=None):
        self._do_copy()
        return "break"

    def _on_cut(self, event=None):
        self._do_cut()
        return "break"

    def _on_paste(self, event=None):
        self._do_paste()
        return "break"

    def _on_select_all(self, event=None):
        self._do_select_all()
        return "break"

    def _do_copy(self):
        """Переопределяется в наследниках"""
        pass

    def _do_cut(self):
        """Переопределяется в наследниках"""
        pass

    def _do_paste(self):
        """Переопределяется в наследниках"""
        pass

    def _do_select_all(self):
        """Переопределяется в наследниках"""
        pass


class ClipboardEntry(ttk.Entry, ClipboardMixin):
    """Entry с поддержкой буфера обмена"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_clipboard_bindings(self)

    def _do_copy(self):
        if self.selection_present():
            self.clipboard_clear()
            self.clipboard_append(self.selection_get())

    def _do_cut(self):
        if self.selection_present():
            self._do_copy()
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)

    def _do_paste(self):
        try:
            text = self.clipboard_get()
            if self.selection_present():
                self.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.insert(tk.INSERT, text)
        except tk.TclError:
            pass

    def _do_select_all(self):
        self.select_range(0, tk.END)
        self.icursor(tk.END)


class ClipboardText(tk.Text, ClipboardMixin):
    """Text с поддержкой буфера обмена"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_clipboard_bindings(self)

    def _do_copy(self):
        try:
            text = self.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)
        except tk.TclError:
            pass

    def _do_cut(self):
        try:
            self._do_copy()
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass

    def _do_paste(self):
        try:
            text = self.clipboard_get()
            try:
                self.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
            self.insert(tk.INSERT, text)
        except tk.TclError:
            pass

    def _do_select_all(self):
        self.tag_add(tk.SEL, "1.0", tk.END)
        self.mark_set(tk.INSERT, tk.END)


# ==================== СОСТАВНЫЕ ВИДЖЕТЫ ====================

class LabeledEntry(ttk.Frame):
    """Поле ввода с меткой"""

    def __init__(
        self,
        parent,
        label: str,
        width: int = 30,
        variable: Optional[tk.StringVar] = None,
        readonly: bool = False,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.var = variable or tk.StringVar()
        state = "readonly" if readonly else "normal"
        self.entry = ClipboardEntry(self, textvariable=self.var, width=width, state=state)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

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
        parent,
        label: str,
        from_: int = 0,
        to: int = 9999,
        variable: Optional[tk.IntVar] = None,
        width: int = 10,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.var = variable or tk.IntVar(value=from_)
        self.spinbox = ttk.Spinbox(
            self, from_=from_, to=to, textvariable=self.var, width=width
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

    def __init__(
        self,
        parent,
        label: str,
        from_: float = 0.0,
        to: float = 999.9,
        increment: float = 0.1,
        variable: Optional[tk.DoubleVar] = None,
        width: int = 10,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.var = variable or tk.DoubleVar(value=from_)
        self.spinbox = ttk.Spinbox(
            self, from_=from_, to=to, increment=increment,
            textvariable=self.var, width=width
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

    def __init__(
        self,
        parent,
        label: str,
        values: List[str],
        variable: Optional[tk.StringVar] = None,
        width: int = 25,
        state: str = "readonly",
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.var = variable or tk.StringVar()
        self.combo = ttk.Combobox(
            self, textvariable=self.var, values=values, width=width, state=state
        )
        self.combo.pack(side=tk.LEFT)

        if values:
            self.combo.current(0)

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str):
        self.var.set(value)

    def set_values(self, values: List[str]):
        self.combo["values"] = values

    def bind_change(self, callback: Callable):
        self.combo.bind("<<ComboboxSelected>>", lambda e: callback())


class LabeledCheckbox(ttk.Frame):
    """Флажок с меткой"""

    def __init__(
        self,
        parent,
        label: str,
        variable: Optional[tk.BooleanVar] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.var = variable or tk.BooleanVar(value=False)
        self.checkbox = ttk.Checkbutton(self, text=label, variable=self.var)
        self.checkbox.pack(side=tk.LEFT)

    def get(self) -> bool:
        return self.var.get()

    def set(self, value: bool):
        self.var.set(value)

    def bind_change(self, callback: Callable):
        self.var.trace_add("write", lambda *args: callback())


class RangeEditor(ttk.Frame):
    """Редактор диапазона min-max"""

    def __init__(
        self,
        parent,
        label: str,
        from_: int = 0,
        to: int = 9999,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.label = ttk.Label(self, text=label, width=15, anchor="e")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.min_var = tk.IntVar(value=0)
        self.min_spin = ttk.Spinbox(self, from_=from_, to=to, textvariable=self.min_var, width=8)
        self.min_spin.pack(side=tk.LEFT)

        ttk.Label(self, text=" - ").pack(side=tk.LEFT)

        self.max_var = tk.IntVar(value=0)
        self.max_spin = ttk.Spinbox(self, from_=from_, to=to, textvariable=self.max_var, width=8)
        self.max_spin.pack(side=tk.LEFT)

    def get(self) -> Tuple[int, int]:
        try:
            return (self.min_var.get(), self.max_var.get())
        except tk.TclError:
            return (0, 0)

    def set(self, min_val: int, max_val: int):
        self.min_var.set(min_val)
        self.max_var.set(max_val)

    def bind_change(self, callback: Callable):
        self.min_var.trace_add("write", lambda *args: callback())
        self.max_var.trace_add("write", lambda *args: callback())


class LabeledTextarea(ttk.Frame):
    """Многострочное текстовое поле с меткой"""

    def __init__(
        self,
        parent,
        label: str,
        height: int = 3,
        width: int = 40,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.label = ttk.Label(self, text=label, anchor="nw")
        self.label.pack(side=tk.TOP, anchor="w", pady=(0, 2))

        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text = ClipboardText(text_frame, height=height, width=width, wrap=tk.WORD)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.configure(yscrollcommand=scrollbar.set)

    def get(self) -> str:
        return self.text.get("1.0", tk.END).strip()

    def set(self, value: str):
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", value)

    def bind_change(self, callback: Callable):
        self.text.bind("<<Modified>>", lambda e: self._on_modified(callback))

    def _on_modified(self, callback: Callable):
        if self.text.edit_modified():
            callback()
            self.text.edit_modified(False)


# ==================== ПАНЕЛЬ СПИСКА ====================

class ItemListPanel(ttk.Frame):
    """
    Панель со списком элементов и кнопками управления
    Поддерживает поиск, добавление, удаление, копирование
    """

    def __init__(
        self,
        parent,
        on_select: Optional[Callable[[str], None]] = None,
        on_add: Optional[Callable[[], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        on_duplicate: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.on_select = on_select
        self.on_add = on_add
        self.on_delete = on_delete
        self.on_duplicate = on_duplicate

        self._items: List[Tuple[str, str]] = []  # [(id, display_name), ...]
        self._selected_id: Optional[str] = None

        self._create_widgets()

    def _create_widgets(self):
        # Поиск
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_list())
        self.search_entry = ClipboardEntry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Список
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5)

        self.listbox = tk.Listbox(list_frame, exportselection=False)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="Добавить", command=self._on_add, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self._on_delete, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Копировать", command=self._on_duplicate, width=10).pack(side=tk.LEFT, padx=2)

    def set_items(self, items: List[Tuple[str, str]]):
        """Установить список элементов"""
        self._items = items
        self._filter_list()

    def get_selected_id(self) -> Optional[str]:
        """Получить ID выбранного элемента"""
        return self._selected_id

    def select_item(self, item_id: str):
        """Выбрать элемент по ID"""
        for i, (id_, _) in enumerate(self._filtered_items):
            if id_ == item_id:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(i)
                self.listbox.see(i)
                self._selected_id = item_id
                break

    def _filter_list(self):
        """Фильтровать список по поисковому запросу"""
        query = self.search_var.get().lower()

        self._filtered_items = []
        for id_, name in self._items:
            if query in id_.lower() or query in name.lower():
                self._filtered_items.append((id_, name))

        self.listbox.delete(0, tk.END)
        for id_, name in self._filtered_items:
            display = f"{name} [{id_}]"
            self.listbox.insert(tk.END, display)

    def _on_listbox_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self._filtered_items):
                self._selected_id = self._filtered_items[idx][0]
                if self.on_select:
                    self.on_select(self._selected_id)

    def _on_add(self):
        if self.on_add:
            self.on_add()

    def _on_delete(self):
        if self._selected_id and self.on_delete:
            self.on_delete(self._selected_id)

    def _on_duplicate(self):
        if self._selected_id and self.on_duplicate:
            self.on_duplicate(self._selected_id)


# ==================== РЕДАКТОР БОНУСОВ ХАРАКТЕРИСТИК ====================

class StatBonusEditor(ttk.Frame):
    """Редактор бонусов к характеристикам"""

    def __init__(
        self,
        parent,
        stat_options: List[Tuple[str, str]],  # [(value, display_name), ...]
        on_change: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.stat_options = stat_options
        self.on_change = on_change
        self._bonuses: List[Dict[str, Any]] = []

        self._create_widgets()

    def _create_widgets(self):
        # Заголовок
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(header, text="Бонусы к характеристикам", font=("", 9, "bold")).pack(side=tk.LEFT)

        # Таблица
        columns = ("stat", "value", "percent")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=4)
        self.tree.heading("stat", text="Характеристика")
        self.tree.heading("value", text="Значение")
        self.tree.heading("percent", text="%")
        self.tree.column("stat", width=150)
        self.tree.column("value", width=80)
        self.tree.column("percent", width=40)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="Добавить", command=self._add_bonus, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Изменить", command=self._edit_bonus, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self._remove_bonus, width=10).pack(side=tk.LEFT, padx=2)

    def get_bonuses(self) -> List[Dict[str, Any]]:
        return self._bonuses.copy()

    def set_bonuses(self, bonuses: List[Dict[str, Any]]):
        self._bonuses = bonuses.copy()
        self._refresh_tree()

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for bonus in self._bonuses:
            stat = bonus.get("stat", "")
            value = bonus.get("value", 0)
            is_percent = "Да" if bonus.get("is_percent", False) else ""

            # Найти отображаемое имя
            display_name = stat
            for val, name in self.stat_options:
                if val == stat:
                    display_name = name
                    break

            self.tree.insert("", tk.END, values=(display_name, value, is_percent))

    def _add_bonus(self):
        dialog = StatBonusDialog(self, self.stat_options)
        self.wait_window(dialog)
        if dialog.result:
            self._bonuses.append(dialog.result)
            self._refresh_tree()
            if self.on_change:
                self.on_change()

    def _edit_bonus(self):
        selection = self.tree.selection()
        if not selection:
            return

        idx = self.tree.index(selection[0])
        if idx < len(self._bonuses):
            dialog = StatBonusDialog(self, self.stat_options, self._bonuses[idx])
            self.wait_window(dialog)
            if dialog.result:
                self._bonuses[idx] = dialog.result
                self._refresh_tree()
                if self.on_change:
                    self.on_change()

    def _remove_bonus(self):
        selection = self.tree.selection()
        if not selection:
            return

        idx = self.tree.index(selection[0])
        if idx < len(self._bonuses):
            del self._bonuses[idx]
            self._refresh_tree()
            if self.on_change:
                self.on_change()


class StatBonusDialog(tk.Toplevel):
    """Диалог добавления/редактирования бонуса"""

    def __init__(
        self,
        parent,
        stat_options: List[Tuple[str, str]],
        initial: Optional[Dict[str, Any]] = None
    ):
        super().__init__(parent)
        self.title("Бонус характеристики")
        self.resizable(False, False)

        self.stat_options = stat_options
        self.result: Optional[Dict[str, Any]] = None

        self._create_widgets(initial)

        # Модальность
        self.transient(parent)
        self.grab_set()

        # Центрирование
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

    def _create_widgets(self, initial: Optional[Dict[str, Any]]):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Характеристика
        ttk.Label(frame, text="Характеристика:").grid(row=0, column=0, sticky="e", pady=5)
        self.stat_var = tk.StringVar()
        stat_names = [name for _, name in self.stat_options]
        self.stat_combo = ttk.Combobox(frame, textvariable=self.stat_var, values=stat_names, state="readonly", width=20)
        self.stat_combo.grid(row=0, column=1, pady=5, padx=(5, 0))

        # Значение
        ttk.Label(frame, text="Значение:").grid(row=1, column=0, sticky="e", pady=5)
        self.value_var = tk.IntVar(value=1)
        self.value_spin = ttk.Spinbox(frame, from_=-999, to=999, textvariable=self.value_var, width=10)
        self.value_spin.grid(row=1, column=1, sticky="w", pady=5, padx=(5, 0))

        # Процент
        self.percent_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Процентное значение", variable=self.percent_var).grid(
            row=2, column=0, columnspan=2, pady=5
        )

        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(btn_frame, text="OK", command=self._on_ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy, width=10).pack(side=tk.LEFT, padx=5)

        # Заполнение начальными значениями
        if initial:
            stat_value = initial.get("stat", "")
            for i, (val, name) in enumerate(self.stat_options):
                if val == stat_value:
                    self.stat_combo.current(i)
                    break
            self.value_var.set(initial.get("value", 1))
            self.percent_var.set(initial.get("is_percent", False))
        elif self.stat_options:
            self.stat_combo.current(0)

    def _on_ok(self):
        # Получить значение stat
        idx = self.stat_combo.current()
        if idx >= 0 and idx < len(self.stat_options):
            stat_value = self.stat_options[idx][0]
        else:
            stat_value = ""

        self.result = {
            "stat": stat_value,
            "value": self.value_var.get(),
            "is_percent": self.percent_var.get(),
        }
        self.destroy()


# ==================== РЕДАКТОР ИНГРЕДИЕНТОВ ====================

class IngredientEditor(ttk.Frame):
    """Редактор ингредиентов рецепта"""

    def __init__(
        self,
        parent,
        get_items_callback: Callable[[], List[Tuple[str, str]]],
        on_change: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.get_items = get_items_callback
        self.on_change = on_change
        self._ingredients: List[Dict[str, Any]] = []

        self._create_widgets()

    def _create_widgets(self):
        # Заголовок
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(header, text="Ингредиенты", font=("", 9, "bold")).pack(side=tk.LEFT)

        # Таблица
        columns = ("item", "quantity")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=5)
        self.tree.heading("item", text="Предмет")
        self.tree.heading("quantity", text="Количество")
        self.tree.column("item", width=200)
        self.tree.column("quantity", width=80)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="Добавить", command=self._add_ingredient, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Изменить", command=self._edit_ingredient, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self._remove_ingredient, width=10).pack(side=tk.LEFT, padx=2)

    def get_ingredients(self) -> List[Dict[str, Any]]:
        return self._ingredients.copy()

    def set_ingredients(self, ingredients: List[Dict[str, Any]]):
        self._ingredients = ingredients.copy()
        self._refresh_tree()

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        items = dict(self.get_items())
        for ing in self._ingredients:
            item_id = ing.get("item_id", "")
            quantity = ing.get("quantity", 1)
            display_name = items.get(item_id, item_id)
            self.tree.insert("", tk.END, values=(f"{display_name} [{item_id}]", quantity))

    def _add_ingredient(self):
        items = self.get_items()
        if not items:
            return

        dialog = IngredientDialog(self, items)
        self.wait_window(dialog)
        if dialog.result:
            self._ingredients.append(dialog.result)
            self._refresh_tree()
            if self.on_change:
                self.on_change()

    def _edit_ingredient(self):
        selection = self.tree.selection()
        if not selection:
            return

        idx = self.tree.index(selection[0])
        if idx < len(self._ingredients):
            items = self.get_items()
            dialog = IngredientDialog(self, items, self._ingredients[idx])
            self.wait_window(dialog)
            if dialog.result:
                self._ingredients[idx] = dialog.result
                self._refresh_tree()
                if self.on_change:
                    self.on_change()

    def _remove_ingredient(self):
        selection = self.tree.selection()
        if not selection:
            return

        idx = self.tree.index(selection[0])
        if idx < len(self._ingredients):
            del self._ingredients[idx]
            self._refresh_tree()
            if self.on_change:
                self.on_change()


class IngredientDialog(tk.Toplevel):
    """Диалог добавления/редактирования ингредиента"""

    def __init__(
        self,
        parent,
        items: List[Tuple[str, str]],
        initial: Optional[Dict[str, Any]] = None
    ):
        super().__init__(parent)
        self.title("Ингредиент")
        self.resizable(False, False)

        self.items = items
        self.result: Optional[Dict[str, Any]] = None

        self._create_widgets(initial)

        self.transient(parent)
        self.grab_set()
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

    def _create_widgets(self, initial: Optional[Dict[str, Any]]):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Предмет
        ttk.Label(frame, text="Предмет:").grid(row=0, column=0, sticky="e", pady=5)
        self.item_var = tk.StringVar()
        item_names = [f"{name} [{id_}]" for id_, name in self.items]
        self.item_combo = ttk.Combobox(frame, textvariable=self.item_var, values=item_names, state="readonly", width=30)
        self.item_combo.grid(row=0, column=1, pady=5, padx=(5, 0))

        # Количество
        ttk.Label(frame, text="Количество:").grid(row=1, column=0, sticky="e", pady=5)
        self.qty_var = tk.IntVar(value=1)
        self.qty_spin = ttk.Spinbox(frame, from_=1, to=999, textvariable=self.qty_var, width=10)
        self.qty_spin.grid(row=1, column=1, sticky="w", pady=5, padx=(5, 0))

        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(btn_frame, text="OK", command=self._on_ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy, width=10).pack(side=tk.LEFT, padx=5)

        # Начальные значения
        if initial:
            item_id = initial.get("item_id", "")
            for i, (id_, _) in enumerate(self.items):
                if id_ == item_id:
                    self.item_combo.current(i)
                    break
            self.qty_var.set(initial.get("quantity", 1))
        elif self.items:
            self.item_combo.current(0)

    def _on_ok(self):
        idx = self.item_combo.current()
        if idx >= 0 and idx < len(self.items):
            item_id = self.items[idx][0]
        else:
            item_id = ""

        self.result = {
            "item_id": item_id,
            "quantity": self.qty_var.get(),
        }
        self.destroy()


# ==================== РЕДАКТОР ПАРАМЕТРОВ ПО КАЧЕСТВУ ====================

class QualityParamsEditor(ttk.Frame):
    """Редактор параметров для каждого уровня качества"""

    def __init__(
        self,
        parent,
        qualities: List[Tuple[str, str, str]],  # [(value, name, color), ...]
        on_change: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.qualities = qualities
        self.on_change = on_change
        self._params: Dict[str, Dict[str, Any]] = {}

        self._create_widgets()

    def _create_widgets(self):
        # Notebook с вкладками по качеству
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self._quality_frames: Dict[str, ttk.Frame] = {}
        self._quality_widgets: Dict[str, Dict[str, Any]] = {}

        for quality_value, quality_name, quality_color in self.qualities:
            frame = ttk.Frame(self.notebook, padding=5)
            self.notebook.add(frame, text=quality_name)
            self._quality_frames[quality_value] = frame

            widgets = {}

            # Множитель основного параметра
            widgets["main_mult"] = LabeledFloatSpinbox(frame, "Множитель:", from_=0.1, to=10.0, increment=0.1)
            widgets["main_mult"].pack(fill=tk.X, pady=2)
            widgets["main_mult"].set(1.0)

            # Разброс основного параметра
            widgets["main_variance"] = RangeEditor(frame, "Разброс %:", from_=50, to=200)
            widgets["main_variance"].pack(fill=tk.X, pady=2)
            widgets["main_variance"].set(90, 110)

            # Количество бонусов
            widgets["bonus_count"] = RangeEditor(frame, "Бонусов:", from_=0, to=10)
            widgets["bonus_count"].pack(fill=tk.X, pady=2)
            widgets["bonus_count"].set(0, 0)

            # Множитель бонусов
            widgets["bonus_mult"] = LabeledFloatSpinbox(frame, "Множ. бонуса:", from_=0.0, to=10.0, increment=0.1)
            widgets["bonus_mult"].pack(fill=tk.X, pady=2)
            widgets["bonus_mult"].set(1.0)

            # Множитель цены
            widgets["price_mult"] = LabeledFloatSpinbox(frame, "Множ. цены:", from_=0.1, to=500.0, increment=0.5)
            widgets["price_mult"].pack(fill=tk.X, pady=2)
            widgets["price_mult"].set(1.0)

            self._quality_widgets[quality_value] = widgets

    def get_params(self) -> Dict[str, Dict[str, Any]]:
        result = {}
        for quality_value, widgets in self._quality_widgets.items():
            main_variance = widgets["main_variance"].get()
            bonus_count = widgets["bonus_count"].get()

            result[quality_value] = {
                "main_stat_multiplier": widgets["main_mult"].get(),
                "main_stat_variance": list(main_variance),
                "bonus_count": list(bonus_count),
                "bonus_value_multiplier": widgets["bonus_mult"].get(),
                "price_multiplier": widgets["price_mult"].get(),
            }
        return result

    def set_params(self, params: Dict[str, Dict[str, Any]]):
        for quality_value, data in params.items():
            if quality_value in self._quality_widgets:
                widgets = self._quality_widgets[quality_value]

                widgets["main_mult"].set(data.get("main_stat_multiplier", 1.0))

                variance = data.get("main_stat_variance", [90, 110])
                if isinstance(variance, list) and len(variance) == 2:
                    widgets["main_variance"].set(variance[0], variance[1])

                bonus = data.get("bonus_count", [0, 0])
                if isinstance(bonus, list) and len(bonus) == 2:
                    widgets["bonus_count"].set(bonus[0], bonus[1])

                widgets["bonus_mult"].set(data.get("bonus_value_multiplier", 1.0))
                widgets["price_mult"].set(data.get("price_multiplier", 1.0))
