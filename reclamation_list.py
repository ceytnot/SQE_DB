# reclamation_list.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class ReclamationListWindow:
    def __init__(self, root, db):
        self.root = root
        self.db = db
        self.root.title("Список Рекламаций ")
        self.root.state('zoomed')
        
        self.search_var = tk.StringVar()
        self.filter_status = tk.StringVar(value="Open")
        self.filter_model = tk.StringVar(value="Все")
        self.filter_supplier = tk.StringVar(value="Все")
        self.filter_creator = tk.StringVar(value="Все")
        self.filter_commodity = tk.StringVar(value="Все")
        self.tree = None
        self.count_label = None
        self.models = []
        self.suppliers = []
        self.creators = []
        self.commodities = []
        
        # Ссылки на виджеты фильтров
        self.model_filter = None
        self.supplier_filter = None
        self.creator_filter = None
        self.commodity_filter = None
        
        # Список открытых окон редактирования
        self.edit_windows = []
        
        # ✅ Словарь для хранения цветовых индикаторов
        self.status_colors = {
            'Open': '🟢',           # Зеленый
            'In Progress': '🟡',    # Желтый
            'Under Investigation': '🟠',  # Оранжевый
            'Closed': '🔵',         # Синий
            'Rejected': '🔴',       # Красный
            'Implemented': '🟣'     # Фиолетовый
        }
        
        self.create_widgets()
        self.load_reference_data()
        self.load_data()
        
        # ✅ Добавляем обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """Обработчик закрытия окна с подтверждением"""
        active_windows = [w for w in self.edit_windows if w.winfo_exists()]
        
        if active_windows:
            result = messagebox.askyesno(
                "Подтверждение закрытия",
                f"У вас открыто {len(active_windows)} окно(а) редактирования.\n\n"
                "При закрытии списка все окна редактирования будут закрыты.\n"
                "Вы уверены, что хотите закрыть окно?",
                parent=self.root
            )
        else:
            result = messagebox.askyesno(
                "Подтверждение закрытия",
                "Вы уверены, что хотите закрыть список рекламаций?",
                parent=self.root
            )
        
        if result:
            for window in active_windows:
                try:
                    if window.winfo_exists():
                        window.destroy()
                except:
                    pass
            self.edit_windows.clear()
            self.root.destroy()
    
    def create_widgets(self):
        # Верхняя панель
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill='x')
        
        ttk.Label(top_frame, text="📋 Список рекламаций поставщикам", 
                  font=('Arial', 16, 'bold')).pack(side='left')
        
        ttk.Button(top_frame, text="➕ Создать новую", 
                  command=self.open_create_window).pack(side='right', padx=10)
        
        ttk.Button(top_frame, text="🔄 Обновить", 
                  command=self.load_data).pack(side='right', padx=10)
        
        # Панель фильтров
        filter_frame = ttk.Frame(self.root, padding=10)
        filter_frame.pack(fill='x')
        
        # Поиск
        ttk.Label(filter_frame, text="🔍 Поиск:").pack(side='left', padx=(0, 10))
        self.search_var.trace('w', lambda *args: self.load_data())
        ttk.Entry(filter_frame, textvariable=self.search_var, width=20).pack(side='left', padx=(0, 20))
        
        # Фильтр по статусу
        ttk.Label(filter_frame, text="Статус:").pack(side='left', padx=(0, 10))
        status_filter = ttk.Combobox(filter_frame, textvariable=self.filter_status, 
                                     values=['Все', 'Open', 'In Progress', 'Under Investigation', 'Closed', 'Rejected', 'Implemented'],
                                     width=15)
        status_filter.pack(side='left', padx=(0, 20))
        status_filter.bind('<<ComboboxSelected>>', lambda e: self.load_data())
        
        # Фильтр по модели
        ttk.Label(filter_frame, text="Модель:").pack(side='left', padx=(0, 10))
        self.model_filter = ttk.Combobox(filter_frame, textvariable=self.filter_model,
                                         values=['Все'], width=20)
        self.model_filter.pack(side='left', padx=(0, 20))
        self.model_filter.bind('<<ComboboxSelected>>', lambda e: self.load_data())
        
        # Фильтр по товарной группе
        ttk.Label(filter_frame, text="Товарная группа:").pack(side='left', padx=(0, 10))
        self.commodity_filter = ttk.Combobox(filter_frame, textvariable=self.filter_commodity,
                                             values=['Все'], width=20)
        self.commodity_filter.pack(side='left', padx=(0, 20))
        self.commodity_filter.bind('<<ComboboxSelected>>', lambda e: self.load_data())
        
        # Фильтр по поставщику
        ttk.Label(filter_frame, text="Поставщик:").pack(side='left', padx=(0, 10))
        self.supplier_filter = ttk.Combobox(filter_frame, textvariable=self.filter_supplier,
                                            values=['Все'], width=20)
        self.supplier_filter.pack(side='left', padx=(0, 20))
        self.supplier_filter.bind('<<ComboboxSelected>>', lambda e: self.load_data())
        
        # Фильтр по создателю
        ttk.Label(filter_frame, text="Создатель:").pack(side='left', padx=(0, 10))
        self.creator_filter = ttk.Combobox(filter_frame, textvariable=self.filter_creator,
                                           values=['Все'], width=20)
        self.creator_filter.pack(side='left', padx=(0, 20))
        self.creator_filter.bind('<<ComboboxSelected>>', lambda e: self.load_data())
        
        # Кнопка сброса фильтров
        ttk.Button(filter_frame, text="🔄 Сбросить фильтры", 
                  command=self.reset_filters).pack(side='left', padx=10)
        
        # ✅ Легенда статусов
        legend_frame = ttk.Frame(filter_frame)
        legend_frame.pack(side='right', padx=10)
        
        ttk.Label(legend_frame, text="Легенда:", font=('Arial', 9)).pack(side='left', padx=(0, 5))
        
        for status, color in self.status_colors.items():
            ttk.Label(legend_frame, text=f"{color} {status}", 
                     font=('Arial', 8)).pack(side='left', padx=3)
        
        # Таблица
        table_frame = ttk.Frame(self.root, padding=10)
        table_frame.pack(fill='both', expand=True)
        
        columns = ('ID', 'Commodity', 'Модель', 'Создатель', 'Деталь', 'Поставщик', 
                   'Номер PIR', 'Дата', 'Статус', 'Кол-во', 'VIN', 'Дефект', 'Утилизация','Cutoff', '8D')
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        col_widths = [50, 120, 120, 120, 150, 130, 150, 120, 150, 80, 100, 100, 100, 120, 80]
        col_anchors = ['center', 'center', 'center', 'center', 'center', 'center', 
                       'center', 'center', 'center', 'center', 'center', 'center', 'center', 'center', 'center']
        
        for col, width, anchor in zip(columns, col_widths, col_anchors):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)
        
        # ✅ Настройка цветов для строк в зависимости от статуса
        self.tree.tag_configure('Open', foreground='#2e7d32')  # Темно-зеленый
        self.tree.tag_configure('In Progress', foreground='#f57f17')  # Темно-желтый
        self.tree.tag_configure('Under Investigation', foreground='#e65100')  # Темно-оранжевый
        self.tree.tag_configure('Closed', foreground='#0d47a1')  # Темно-синий
        self.tree.tag_configure('Rejected', foreground='#b71c1c')  # Темно-красный
        self.tree.tag_configure('Implemented', foreground='#4a148c')  # Темно-фиолетовый
        self.tree.tag_configure('default', foreground='black')
        
        scroll_y = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.count_label = ttk.Label(self.root, text="Всего записей: 0", 
                                     font=('Arial', 10), padding=5)
        self.count_label.pack(side='left', padx=10)
        
        hint_label = ttk.Label(self.root, text="💡 Клик по ID или двойной клик для открытия в новом окне", 
                               font=('Arial', 9), foreground='gray')
        hint_label.pack(side='left', padx=20)
        
        self.tree.bind('<Button-1>', self.on_click)
        self.tree.bind('<Double-Button-1>', self.on_double_click)
        
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill='x')
        
        ttk.Button(btn_frame, text="← Назад", 
                  command=self.go_back).pack(side='left', padx=10)
        
        ttk.Button(btn_frame, text="🗑️ Удалить выбранную", 
                  command=self.delete_selected).pack(side='right', padx=10)
        
        self.windows_count_label = ttk.Label(self.root, text="Открыто окон: 0", 
                                            font=('Arial', 9), foreground='blue')
        self.windows_count_label.pack(side='right', padx=10)
    
    def load_reference_data(self):
        """Загружает справочные данные для фильтров"""
        try:
            self.models = self.db.get_models()
            self.suppliers = self.db.get_suppliers()
            self.creators = self.db.get_creators()
            self.commodities = self.db.get_commodities()
            
            if self.model_filter is not None:
                self.model_filter['values'] = ['Все'] + self.models if self.models else ['Все']
            if self.supplier_filter is not None:
                self.supplier_filter['values'] = ['Все'] + self.suppliers if self.suppliers else ['Все']
            if self.creator_filter is not None:
                self.creator_filter['values'] = ['Все'] + self.creators if self.creators else ['Все']
            if self.commodity_filter is not None:
                self.commodity_filter['values'] = ['Все'] + self.commodities if self.commodities else ['Все']
            
        except Exception as e:
            print(f"Ошибка загрузки справочных данных: {e}")
            if self.model_filter is not None:
                self.model_filter['values'] = ['Все']
            if self.supplier_filter is not None:
                self.supplier_filter['values'] = ['Все']
            if self.creator_filter is not None:
                self.creator_filter['values'] = ['Все']
            if self.commodity_filter is not None:
                self.commodity_filter['values'] = ['Все']
    
    def reset_filters(self):
        """Сбрасывает все фильтры"""
        self.filter_status.set("Open")
        self.filter_model.set("Все")
        self.filter_supplier.set("Все")
        self.filter_creator.set("Все")
        self.filter_commodity.set("Все")
        self.search_var.set("")
        self.load_data()
    
    def load_data(self):
        """Загружает данные в таблицу"""
        if self.tree is None:
            return
        
        search = self.search_var.get().strip().lower()
        status_filter = self.filter_status.get()
        model_filter = self.filter_model.get()
        supplier_filter = self.filter_supplier.get()
        creator_filter = self.filter_creator.get()
        commodity_filter = self.filter_commodity.get()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        rows = self.db.get_all_reclamations()
        count = 0
        
        for row in rows:
            if status_filter != 'Все' and row.ncr_status != status_filter:
                continue
            if model_filter != 'Все' and row.model != model_filter:
                continue
            if supplier_filter != 'Все' and row.supplier != supplier_filter:
                continue
            if creator_filter != 'Все' and row.creator != creator_filter:
                continue
            if commodity_filter != 'Все' and row.commodity != commodity_filter:
                continue
            
            if search:
                row_text = ' '.join(str(v).lower() for v in [
                    row.model, row.creator, row.commodity, row.partname, 
                    row.supplier, row.full_pir_number, row.vin, row.comments,
                    row.defect
                ] if v)
                if search not in row_text:
                    continue
            
            date_str = row.date_creation.strftime("%Y-%m-%d %H:%M") if row.date_creation else ''
            cutoff_str = row.cutoff.strftime("%Y-%m-%d") if row.cutoff else ''
            id_with_icon = f"📝 {row.id}"
            
            # ✅ Добавляем цветной индикатор статуса
            status_display = f"{self.status_colors.get(row.ncr_status, '⚪')} {row.ncr_status or ''}"
            
            item = self.tree.insert('', 'end', values=(
                id_with_icon,
                row.commodity or '',
                row.model or '',
                row.creator or '',
                row.partname or '',
                row.supplier or '',
                row.full_pir_number or '',
                date_str,
                status_display,  # ✅ Статус с цветным кружком
                row.failure_quantity or '',
                row.vin or '',
                row.defect or '',
                row.parts_disposal or '',
                cutoff_str,
                '✅' if row.report8d_checkbox else '❌'
            ))
            
            # ✅ Применяем цвет тега в зависимости от статуса
            status = row.ncr_status or 'default'
            if status in ['Open', 'In Progress', 'Under Investigation', 'Closed', 'Rejected', 'Implemented']:
                self.tree.item(item, tags=(status,))
            else:
                self.tree.item(item, tags=('default',))
            
            count += 1
        
        if self.count_label:
            self.count_label.config(text=f"Всего записей: {count}")
    
    def on_click(self, event):
        """Обработка клика — открытие в новом окне при клике по ID"""
        if self.tree is None:
            return
        
        region = self.tree.identify_region(event.x, event.y)
        if region != 'cell':
            return
        
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        if item and column == '#1':
            self.open_edit_window_new(item)
    
    def on_double_click(self, event):
        """Обработка двойного клика — открытие в новом окне"""
        if self.tree is None:
            return
        
        item = self.tree.identify_row(event.y)
        if item:
            self.open_edit_window_new(item)
    
    def open_edit_window_new(self, item):
        """Открывает окно редактирования в новом окне"""
        try:
            id_str = self.tree.item(item, 'values')[0]
            rec_id = int(id_str.replace('📝 ', '').strip())
            self.open_edit_window(rec_id)
        except (ValueError, IndexError) as e:
            messagebox.showerror("Ошибка", f"Не удалось получить ID записи: {e}")
    
    def open_edit_window(self, rec_id):
        """Открывает окно редактирования рекламации в новом независимом окне"""
        from create_reclamation import CreateReclamationWindow
        
        edit_root = tk.Toplevel(self.root)
        edit_root.title(f"Редактирование NCR #{rec_id}")
        edit_root.state('zoomed')
        
        edit_window = CreateReclamationWindow(edit_root, self.db, rec_id)
        
        self.edit_windows.append(edit_root)
        self.update_windows_count()
        
        def on_close():
            if edit_root in self.edit_windows:
                self.edit_windows.remove(edit_root)
            self.update_windows_count()
            edit_root.destroy()
            self.load_data()
        
        edit_root.protocol("WM_DELETE_WINDOW", on_close)
        
        edit_root.focus_force()
        edit_root.lift()
        edit_root.after(50, lambda: edit_root.focus_force())
    
    def update_windows_count(self):
        """Обновляет счетчик открытых окон"""
        if hasattr(self, 'windows_count_label'):
            self.edit_windows = [w for w in self.edit_windows if w.winfo_exists()]
            self.windows_count_label.config(text=f"Открыто окон: {len(self.edit_windows)}")
    
    def delete_selected(self):
        """Удаляет выбранную рекламацию"""
        if self.tree is None:
            return
            
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return
        
        try:
            id_str = self.tree.item(item[0], 'values')[0]
            rec_id = int(id_str.replace('📝 ', '').strip())
        except (ValueError, IndexError) as e:
            messagebox.showerror("Ошибка", f"Не удалось получить ID записи: {e}")
            return
        
        if messagebox.askyesno("Подтверждение", 
                               f"Вы уверены, что хотите удалить рекламацию #{rec_id}?"):
            result = self.db.delete_reclamation(rec_id)
            if result['success']:
                messagebox.showinfo("Успех", result['message'])
                self.load_data()
            else:
                messagebox.showerror("Ошибка", result['message'])
    
    def open_create_window(self):
        """Открывает окно создания рекламации в новом независимом окне"""
        from create_reclamation import CreateReclamationWindow
        
        create_root = tk.Toplevel(self.root)
        create_root.title("Добавление нового NCR")
        create_root.state('zoomed')
        
        create_window = CreateReclamationWindow(create_root, self.db)
        
        self.edit_windows.append(create_root)
        self.update_windows_count()
        
        def on_close():
            if create_root in self.edit_windows:
                self.edit_windows.remove(create_root)
            self.update_windows_count()
            create_root.destroy()
            self.load_data()
        
        create_root.protocol("WM_DELETE_WINDOW", on_close)
        
        create_root.focus_force()
        create_root.lift()
        create_root.after(50, lambda: create_root.focus_force())
    
    def go_back(self):
        """Возврат в главное окно (закрываем список)"""
        for window in self.edit_windows:
            try:
                if window.winfo_exists():
                    window.destroy()
            except:
                pass
        self.edit_windows.clear()
        
        self.root.destroy()
        from create_reclamation import CreateReclamationWindow
        root = tk.Tk()
        CreateReclamationWindow(root, self.db)
        root.mainloop()