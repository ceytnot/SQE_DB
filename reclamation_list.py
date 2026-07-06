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
        self.filter_commodity = tk.StringVar(value="Все")  # ✅ Новый фильтр
        self.tree = None
        self.count_label = None
        self.models = []
        self.suppliers = []
        self.creators = []
        self.commodities = []  # ✅ Список товарных групп
        
        # Ссылки на виджеты фильтров
        self.model_filter = None
        self.supplier_filter = None
        self.creator_filter = None
        self.commodity_filter = None  # ✅ Новый виджет
        
        self.create_widgets()
        self.load_reference_data()
        self.load_data()
    
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
        
        # ✅ Фильтр по товарной группе (Commodity)
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
        
        # Таблица
        table_frame = ttk.Frame(self.root, padding=10)
        table_frame.pack(fill='both', expand=True)
        
        columns = ('ID', 'Commodity', 'Модель', 'Создатель', 'Деталь', 'Поставщик', 
                   'Номер PIR', 'Дата', 'Статус')
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # Настройка колонок
        col_widths = [50, 120, 120, 120, 150, 130, 150, 120, 120]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='center')
        
        # Все ячейки черные
        self.tree.tag_configure('normal', foreground='black')
        
        # Скроллбары
        scroll_y = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Количество записей
        self.count_label = ttk.Label(self.root, text="Всего записей: 0", 
                                     font=('Arial', 10), padding=5)
        self.count_label.pack(side='left', padx=10)
        
        # Подсказка для пользователя
        hint_label = ttk.Label(self.root, text="💡 Нажмите на ID для редактирования", 
                               font=('Arial', 9), foreground='gray')
        hint_label.pack(side='left', padx=20)
        
        # Клик по ID → редактирование
        self.tree.bind('<Button-1>', self.on_click)
        
        # Кнопка "Назад"
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill='x')
        
        ttk.Button(btn_frame, text="← Назад", 
                  command=self.go_back).pack(side='left', padx=10)
        
        ttk.Button(btn_frame, text="🗑️ Удалить выбранную", 
                  command=self.delete_selected).pack(side='right', padx=10)
    
    def load_reference_data(self):
        """Загружает справочные данные для фильтров"""
        try:
            self.models = self.db.get_models()
            self.suppliers = self.db.get_suppliers()
            self.creators = self.db.get_creators()
            self.commodities = self.db.get_commodities()  # ✅ Загружаем товарные группы
            
            if self.model_filter is not None:
                self.model_filter['values'] = ['Все'] + self.models if self.models else ['Все']
            if self.supplier_filter is not None:
                self.supplier_filter['values'] = ['Все'] + self.suppliers if self.suppliers else ['Все']
            if self.creator_filter is not None:
                self.creator_filter['values'] = ['Все'] + self.creators if self.creators else ['Все']
            if self.commodity_filter is not None:  # ✅ Обновляем фильтр commodity
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
        self.filter_commodity.set("Все")  # ✅ Сброс фильтра commodity
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
        commodity_filter = self.filter_commodity.get()  # ✅ Фильтр по commodity
        
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Получаем данные
        rows = self.db.get_all_reclamations()
        count = 0
        
        # Фильтруем и отображаем
        for row in rows:
            # Фильтр по статусу
            if status_filter != 'Все' and row.ncr_status != status_filter:
                continue
            
            # Фильтр по модели
            if model_filter != 'Все' and row.model != model_filter:
                continue
            
            # Фильтр по поставщику
            if supplier_filter != 'Все' and row.supplier != supplier_filter:
                continue
            
            # Фильтр по создателю
            if creator_filter != 'Все' and row.creator != creator_filter:
                continue
            
            # ✅ Фильтр по товарной группе
            if commodity_filter != 'Все' and row.commodity != commodity_filter:
                continue
            
            # Поиск
            if search:
                row_text = ' '.join(str(v).lower() for v in [row.model, row.creator, row.commodity, row.partname, row.supplier, row.full_pir_number] if v)
                if search not in row_text:
                    continue
            
            # Форматируем дату
            date_str = row.date_creation.strftime("%Y-%m-%d %H:%M") if row.date_creation else ''
            
            # ID с иконкой
            id_with_icon = f"📝 {row.id}"
            
            item = self.tree.insert('', 'end', values=(
                id_with_icon,
                row.commodity or '',
                row.model or '',
                row.creator or '',
                row.partname or '',
                row.supplier or '',
                row.full_pir_number or '',
                date_str,
                row.ncr_status or ''
            ))
            
            # Применяем черный цвет ко всей строке
            self.tree.item(item, tags=('normal',))
            count += 1
        
        if self.count_label:
            self.count_label.config(text=f"Всего записей: {count}")
    
    def on_click(self, event):
        """Обработка клика — редактирование только при клике по ID"""
        if self.tree is None:
            return
        
        region = self.tree.identify_region(event.x, event.y)
        if region != 'cell':
            return
        
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        # ID — это колонка #1
        if item and column == '#1':
            self.open_edit_window_from_item(item)
    
    def open_edit_window_from_item(self, item):
        """Открывает окно редактирования по ID из элемента дерева"""
        try:
            id_str = self.tree.item(item, 'values')[0]
            rec_id = int(id_str.replace('📝 ', '').strip())
            self.open_edit_window(rec_id)
        except (ValueError, IndexError) as e:
            messagebox.showerror("Ошибка", f"Не удалось получить ID записи: {e}")
    
    def open_edit_window(self, rec_id):
        """Открывает окно редактирования рекламации"""
        self.root.destroy()
        from create_reclamation import CreateReclamationWindow
        root = tk.Tk()
        CreateReclamationWindow(root, self.db, rec_id)
        root.mainloop()
    
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
        """Открывает окно создания рекламации"""
        self.root.destroy()
        from create_reclamation import CreateReclamationWindow
        root = tk.Tk()
        CreateReclamationWindow(root, self.db)
        root.mainloop()
    
    def go_back(self):
        """Возврат в окно создания"""
        self.root.destroy()
        from create_reclamation import CreateReclamationWindow
        root = tk.Tk()
        CreateReclamationWindow(root, self.db)
        root.mainloop()