# create_reclamation.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import shutil
import config

class CreateReclamationWindow:
    """NCR window to create and modify reclamation"""
    def __init__(self, root, db, rec_id=None):
        self.root = root
        self.db = db
        self.rec_id = rec_id
        self.edit_mode = rec_id is not None
        
        self.root.title("Редактирование NCR" if self.edit_mode else "Добавление нового NCR")
        self.root.state('zoomed')

        # initialize STATIC DATA before widget creation
        self.models = []
        self.suppliers = []
        self.commodities = []
        
        # Словарь для хранения комбобоксов
        self.comboboxes = {}
        
        # Список загруженных файлов
        self.attached_files = []
        self.file_paths = {}  # {имя_файла: полный_путь}
        self.thumbnail_images = []  # Для хранения ссылок на миниатюры
        self.thumbnails = {}  # {имя_файла: PhotoImage}
        self.selected_file = None
        
        # Стили
        self.setup_styles()
        
        # Словарь для хранения переменных полей
        self.vars = {}
        
        # Создаем status_var ДО загрузки данных
        self.status_var = tk.StringVar(value="⏳ Загрузка данных...")
        
        # Создаем виджеты
        self.create_widgets()
        
        # get data from DB
        self.load_reference_data()
        
        # Если редактирование — загружаем рекламацию
        if self.edit_mode:
            self.load_reclamation_data()
            self.load_attached_files()
        
        # Настройка горячих клавиш
        self.setup_bindings()
    
    def setup_styles(self):
        """Настройка стилей"""
        style = ttk.Style()
        style.configure("Title.TLabel", font=('Arial', 18, 'bold'))
        style.configure("Field.TLabel", font=('Arial', 10))
        style.configure("Accent.TButton", font=('Arial', 10, 'bold'))
        style.configure("Status.TLabel", font=('Arial', 9))
        style.configure("Info.TLabel", font=('Arial', 9), foreground='gray')
    
    def create_widgets(self):
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Верхняя панель
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill='x', pady=(0, 20))
        
        title = ttk.Label(top_frame, text="New Non Conformity Report", 
                          style="Title.TLabel")
        title.pack(side='left')
        
        # Кнопки в верхней панели
        ttk.Button(top_frame, text="🔄 Обновить справочники", 
                  command=self.refresh_reference_data).pack(side='right', padx=10)
        
        ttk.Button(top_frame, text="📋 Список рекламаций", 
                  command=self.open_list_window).pack(side='right', padx=10)
        
        # Контейнер для полей ввода (две колонки)
        fields_container = ttk.Frame(main_frame)
        fields_container.pack(fill='both', expand=True)
        
        # Левая колонка (все поля ввода)
        left_frame = ttk.LabelFrame(fields_container, text="Информация о рекламации", padding=15)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Правая колонка (галерея изображений)
        right_frame = ttk.LabelFrame(fields_container, text="Галерея изображений", padding=15)
        right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # ==================== ЛЕВАЯ КОЛОНКА ====================
        
        # Определяем все поля в левой колонке
        left_fields = [
            ('model', 'Модель *', 'combobox', self.models),
            ('commodity', 'Товарная группа', 'combobox', self.commodities),
            ('creator', 'Создатель', 'entry', None),
            ('partnumber', 'Номер детали *', 'entry', None),
            ('partname', 'Наименование детали', 'entry', None),
            ('supplier', 'Поставщик *', 'combobox', self.suppliers),
            ('full_pir_number', 'Номер PIR', 'entry', None),
            ('repetition', 'Повторяемость', 'entry', None),
            ('ncr_status', 'Статус NCR', 'combobox', config.NCR_STATUSES),
        ]
        
        # Создаем поля на левой панели
        for key, label, widget_type, values in left_fields:
            self._create_field(left_frame, key, label, widget_type, values)
        
        # Поле для описания (многострочное)
        desc_frame = ttk.LabelFrame(left_frame, text="Описание проблемы", padding=10)
        desc_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        self.description_text = tk.Text(desc_frame, height=6, font=('Arial', 10), wrap='word')
        self.description_text.pack(fill='both', expand=True)
        
        # ==================== ПРАВАЯ КОЛОНКА (Галерея) ====================
        
        # Кнопки управления файлами
        file_btn_frame = ttk.Frame(right_frame)
        file_btn_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(file_btn_frame, text="📎 Добавить файлы", 
                  command=self.add_file).pack(side='left', padx=5)
        
        ttk.Button(file_btn_frame, text="🗑️ Удалить выбранный", 
                  command=self.remove_selected_file).pack(side='left', padx=5)
        
        ttk.Button(file_btn_frame, text="📂 Открыть папку", 
                  command=self.open_files_folder).pack(side='left', padx=5)
        
        # Список файлов (слева)
        list_frame = ttk.Frame(right_frame)
        list_frame.pack(side='left', fill='y', padx=(0, 10))
        
        ttk.Label(list_frame, text="Файлы:", font=('Arial', 9)).pack(anchor='w')
        
        self.file_listbox = tk.Listbox(list_frame, height=12, width=20)
        self.file_listbox.pack(side='left', fill='both', expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        self.file_listbox.bind('<Double-Button-1>', self.on_file_double_click)
        
        file_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_listbox.yview)
        file_scrollbar.pack(side='right', fill='y')
        self.file_listbox.configure(yscrollcommand=file_scrollbar.set)
        
        # Галерея изображений (справа)
        gallery_frame = ttk.Frame(right_frame)
        gallery_frame.pack(side='left', fill='both', expand=True)
        
        # Canvas с прокруткой для галереи
        canvas_frame = ttk.Frame(gallery_frame)
        canvas_frame.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Внутренний фрейм для миниатюр
        self.gallery_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.gallery_frame, anchor='nw')
        
        self.gallery_frame.bind('<Configure>', self._on_gallery_configure)
    
    def _on_gallery_configure(self, event):
        """Обновляет область прокрутки при изменении размера галереи"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def _create_field(self, parent, key, label, widget_type, values):
        """Создает одно поле ввода"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=5)
        
        label_text = label + (' *' if '*' in label else '')
        ttk.Label(frame, text=label_text + ':', style="Field.TLabel", 
                  width=20, anchor='e').pack(side='left', padx=(0, 10))
        
        if widget_type == 'entry':
            self.vars[key] = tk.StringVar()
            widget = ttk.Entry(frame, textvariable=self.vars[key], width=30)
            widget.pack(side='left', fill='x', expand=True)
            
            widget.bind('<FocusIn>', lambda e, k=label: self.status_var.set(f"Введите {k.lower()}"))
            widget.bind('<FocusOut>', lambda e: self.status_var.set("Готов к работе"))
        
        elif widget_type == 'combobox':
            self.vars[key] = tk.StringVar()
            widget = ttk.Combobox(frame, textvariable=self.vars[key], 
                                  values=values if values else [], width=28)
            widget.pack(side='left', fill='x', expand=True)
            widget.set('')
            
            self.comboboxes[key] = widget
            
            widget.bind('<FocusIn>', lambda e, k=label: self.status_var.set(f"Введите или выберите {k.lower()}"))
            widget.bind('<FocusOut>', lambda e: self.status_var.set("Готов к работе"))
            widget.bind('<KeyRelease>', self._on_combobox_keyrelease)
        
        return widget
    
    def _on_combobox_keyrelease(self, event):
        """Обработка ввода в комбобоксе для автодополнения"""
        widget = event.widget
        current_text = widget.get()
        
        if len(current_text) < 2:
            return
        
        if 'model' in str(widget):
            matches = [m for m in self.models if current_text.lower() in m.lower()]
            if matches:
                widget['values'] = matches
        elif 'supplier' in str(widget):
            matches = [s for s in self.suppliers if current_text.lower() in s.lower()]
            if matches:
                widget['values'] = matches
        elif 'commodity' in str(widget):
            matches = [c for c in self.commodities if current_text.lower() in c.lower()]
            if matches:
                widget['values'] = matches
    
    def load_reference_data(self):
        """Загружает справочные данные из базы"""
        self.status_var.set("⏳ Загрузка данных из базы...")
        self.root.update()
        
        try:
            self.models = self.db.get_models()
            self.suppliers = self.db.get_suppliers()
            self.commodities = self.db.get_commodities()
            
            self.update_comboboxes()
            self.status_var.set(f"✅ Загружено: {len(self.models)} моделей, {len(self.suppliers)} поставщиков, {len(self.commodities)} товарных групп")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки справочных данных: {e}")
            self.models = config.MODELS
            self.suppliers = config.SUPPLIERS
            self.commodities = []
            self.update_comboboxes()
            self.status_var.set("⚠️ Используются значения по умолчанию")
    
    def load_reclamation_data(self):
        """Загружает данные рекламации для редактирования"""
        self.status_var.set(f"⏳ Загрузка рекламации #{self.rec_id}...")
        self.root.update()
        
        rec = self.db.get_reclamation_by_id(self.rec_id)
        
        if rec:
            self.vars['model'].set(rec.model or '')
            self.vars['commodity'].set(rec.commodity or '')
            self.vars['creator'].set(rec.creator or '')
            self.vars['partnumber'].set(rec.partnumber or '')
            self.vars['partname'].set(rec.partname or '')
            self.vars['supplier'].set(rec.supplier or '')
            self.vars['full_pir_number'].set(rec.full_pir_number or '')
            self.vars['repetition'].set(rec.repetition or '')
            self.vars['ncr_status'].set(rec.ncr_status or '')
            
            if rec.description:
                self.description_text.insert('1.0', rec.description)
            
            self.status_var.set(f"✅ Рекламация #{self.rec_id} загружена для редактирования")
        else:
            messagebox.showerror("Ошибка", f"Рекламация #{self.rec_id} не найдена")
            self.status_var.set("❌ Ошибка загрузки")
    
    def load_attached_files(self):
        """Загружает список прикрепленных файлов для существующей рекламации"""
        if not self.rec_id:
            return
        
        folder_path = self.get_ncr_folder()
        if os.path.exists(folder_path):
            try:
                files = os.listdir(folder_path)
                for file in files:
                    full_path = os.path.join(folder_path, file)
                    self.attached_files.append(file)
                    self.file_paths[file] = full_path
                    self.file_listbox.insert(tk.END, file)
                self.render_gallery()
            except Exception as e:
                print(f"Ошибка загрузки файлов: {e}")
    
    def get_ncr_folder(self):
        """Возвращает путь к папке для файлов рекламации"""
        base_path = r"X:\SQE_DB\NCR"
        if self.rec_id:
            return os.path.join(base_path, str(self.rec_id))
        return base_path
    
    def add_file(self):
        """Добавляет файл к рекламации"""
        file_paths = filedialog.askopenfilenames(
            title="Выберите файлы для прикрепления",
            filetypes=[
                ("Все файлы", "*.*"),
                ("Документы", "*.pdf;*.doc;*.docx;*.xls;*.xlsx"),
                ("Изображения", "*.jpg;*.jpeg;*.png;*.bmp;*.gif"),
                ("Архивы", "*.zip;*.rar;*.7z")
            ]
        )
        
        if not file_paths:
            return
        
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            
            if file_name in self.attached_files:
                messagebox.showwarning("Внимание", f"Файл '{file_name}' уже добавлен")
                continue
            
            self.attached_files.append(file_name)
            self.file_paths[file_name] = file_path
            self.file_listbox.insert(tk.END, file_name)
            
            if self.rec_id:
                self.copy_file_to_ncr_folder(file_path, file_name)
        
        self.render_gallery()
        self.status_var.set(f"✅ Добавлено файлов: {len(file_paths)}")
    
    def copy_file_to_ncr_folder(self, source_path, file_name):
        """Копирует файл в папку рекламации"""
        folder_path = self.get_ncr_folder()
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"📁 Создана папка: {folder_path}")
        
        dest_path = os.path.join(folder_path, file_name)
        
        counter = 1
        while os.path.exists(dest_path):
            name, ext = os.path.splitext(file_name)
            new_name = f"{name}_{counter}{ext}"
            dest_path = os.path.join(folder_path, new_name)
            counter += 1
        
        try:
            shutil.copy2(source_path, dest_path)
            self.file_paths[file_name] = dest_path
            print(f"✅ Файл скопирован: {dest_path}")
        except Exception as e:
            print(f"❌ Ошибка копирования: {e}")
            messagebox.showerror("Ошибка", f"Не удалось скопировать файл:\n{e}")
    
    def render_gallery(self):
        """Отображает все изображения в виде галереи миниатюр"""
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()
        self.thumbnail_images.clear()
        self.thumbnails = {}
        
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
        sorted_files = sorted(self.attached_files)
        
        for file_name in sorted_files:
            file_path = self.file_paths.get(file_name)
            if not file_path or not os.path.exists(file_path):
                continue
            
            if file_name.lower().endswith(image_extensions):
                try:
                    self.create_thumbnail(file_name, file_path)
                except Exception as e:
                    print(f"Ошибка создания миниатюры для {file_name}: {e}")
        
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def create_thumbnail(self, file_name, file_path):
        """Создает миниатюру для изображения"""
        try:
            from PIL import Image, ImageTk
            
            img = Image.open(file_path)
            thumb_size = (120, 120)
            img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            self.thumbnails[file_name] = photo
            self.thumbnail_images.append(photo)
            
            thumb_frame = ttk.Frame(self.gallery_frame)
            thumb_frame.pack(side='left', padx=5, pady=5)
            
            img_label = ttk.Label(thumb_frame, image=photo, relief='solid', cursor='hand2')
            img_label.pack()
            
            name_label = ttk.Label(thumb_frame, text=file_name[:15] + ('...' if len(file_name) > 15 else ''), 
                                  font=('Arial', 7), foreground='gray')
            name_label.pack()
            
            img_label.bind('<Button-1>', lambda e, f=file_name: self.on_thumbnail_click(f))
            img_label.bind('<Double-Button-1>', lambda e, f=file_path: self.open_file(f))
            img_label.bind('<Button-3>', lambda e, f=file_name: self.show_thumbnail_context_menu(e, f))
            
        except Exception as e:
            print(f"Ошибка создания миниатюры: {e}")
    
    def on_thumbnail_click(self, file_name):
        """Обработка клика по миниатюре"""
        try:
            index = self.attached_files.index(file_name)
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(index)
            self.file_listbox.see(index)
            self.selected_file = file_name
            self.status_var.set(f"📷 Выбрано изображение: {file_name}")
        except ValueError:
            pass
    
    def show_thumbnail_context_menu(self, event, file_name):
        """Контекстное меню для миниатюры"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="📂 Открыть", command=lambda: self.open_file(self.file_paths.get(file_name)))
        menu.add_command(label="🗑️ Удалить", command=lambda: self.remove_file(file_name))
        menu.post(event.x_root, event.y_root)
    
    def open_file(self, file_path):
        """Открывает файл в приложении по умолчанию"""
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Ошибка", f"Файл не найден:\n{file_path}")
            return
        
        try:
            os.startfile(file_path)
            self.status_var.set(f"📂 Открыт файл: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
    
    def remove_file(self, file_name):
        """Удаляет файл по имени"""
        if file_name not in self.attached_files:
            return
        
        if not messagebox.askyesno("Подтверждение", f"Удалить файл '{file_name}'?"):
            return
        
        self.attached_files.remove(file_name)
        if file_name in self.file_paths:
            del self.file_paths[file_name]
        
        for i in range(self.file_listbox.size()):
            if self.file_listbox.get(i) == file_name:
                self.file_listbox.delete(i)
                break
        
        if file_name in self.thumbnails:
            del self.thumbnails[file_name]
        
        if self.rec_id:
            folder_path = self.get_ncr_folder()
            file_path = os.path.join(folder_path, file_name)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Ошибка удаления файла: {e}")
        
        self.render_gallery()
        self.status_var.set(f"🗑️ Файл '{file_name}' удален")
    
    def on_file_select(self, event):
        """Обработка выбора файла из списка"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        file_name = self.file_listbox.get(index)
        self.selected_file = file_name
        self.status_var.set(f"📄 Выбран файл: {file_name}")
    
    def on_file_double_click(self, event):
        """Обработка двойного клика по файлу"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        file_name = self.file_listbox.get(index)
        file_path = self.file_paths.get(file_name)
        self.open_file(file_path)
    
    def remove_selected_file(self):
        """Удаляет выбранный файл из списка"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите файл для удаления")
            return
        
        index = selection[0]
        file_name = self.file_listbox.get(index)
        self.remove_file(file_name)
    
    def open_files_folder(self):
        """Открывает папку с файлами рекламации"""
        if not self.rec_id:
            messagebox.showinfo("Информация", "Сначала сохраните рекламацию")
            return
        
        folder_path = self.get_ncr_folder()
        if os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            messagebox.showinfo("Информация", "Папка с файлами еще не создана")
    
    def update_comboboxes(self):
        """Обновляет значения в комбобоксах"""
        if 'model' in self.comboboxes:
            self.comboboxes['model']['values'] = self.models
            if not self.comboboxes['model'].get():
                self.comboboxes['model'].set('')
        
        if 'supplier' in self.comboboxes:
            self.comboboxes['supplier']['values'] = self.suppliers
            if not self.comboboxes['supplier'].get():
                self.comboboxes['supplier'].set('')
        
        if 'commodity' in self.comboboxes:
            self.comboboxes['commodity']['values'] = self.commodities
            if not self.comboboxes['commodity'].get():
                self.comboboxes['commodity'].set('')
    
    def refresh_reference_data(self):
        """Обновляет справочные данные из базы"""
        self.load_reference_data()
        self.status_var.set("✅ Справочники обновлены")
    
    def setup_bindings(self):
        """Настройка горячих клавиш"""
        self.root.bind('<Control-s>', lambda e: self.save_reclamation())
        self.root.bind('<Control-Shift-C>', lambda e: self.clear_fields())
        self.root.bind('<F5>', lambda e: self.refresh_reference_data())
        self.root.bind('<Escape>', lambda e: self.root.quit())
    
    def save_reclamation(self):
        """Сохраняет или обновляет рекламацию в базе данных"""
        self.status_var.set("⏳ Сохранение...")
        self.root.update()
        
        try:
            data = {}
            for key, var in self.vars.items():
                data[key] = var.get().strip()
            
            data['description'] = self.description_text.get('1.0', 'end-1c').strip()
            data['date_creation'] = datetime.now()
            
            required_fields = ['model', 'partnumber', 'supplier']
            missing = [f for f in required_fields if not data.get(f)]
            
            if missing:
                field_names = {
                    'model': 'Модель',
                    'partnumber': 'Номер детали',
                    'supplier': 'Поставщик'
                }
                msg = "Заполните обязательные поля:\n" + "\n".join(f"• {field_names[f]}" for f in missing)
                messagebox.showwarning("Внимание", msg)
                self.status_var.set("❌ Ошибка: не заполнены обязательные поля")
                return
            
            if self.edit_mode:
                result = self.db.update_reclamation(self.rec_id, data)
                if result['success']:
                    self.save_files_after_save()
                    messagebox.showinfo("Успех", f"✅ Рекламация #{self.rec_id} обновлена!")
                    self.status_var.set(f"✅ Рекламация #{self.rec_id} обновлена")
                    self.open_list_window()
                else:
                    messagebox.showerror("Ошибка", f"❌ {result['message']}")
                    self.status_var.set(f"❌ Ошибка: {result['message']}")
            else:
                result = self.db.save_reclamation(data)
                
                if result['success']:
                    self.rec_id = result['id']
                    current_model = self.vars['model'].get().strip()
                    full_pir = f"AGS-{current_model}-{self.rec_id:04d}"
                    self.db.update_reclamation(self.rec_id, {'full_pir_number': full_pir})
                    self.save_files_after_save()
                    
                    messagebox.showinfo("Успех", f"✅ Рекламация сохранена!\nID: {self.rec_id}\nНомер: {full_pir}")
                    self.status_var.set(f"✅ Рекламация #{self.rec_id} сохранена")
                    self.clear_fields()
                    self.refresh_reference_data()
                    self.edit_mode = True
                    self.root.title(f"Редактирование NCR #{self.rec_id}")
                else:
                    messagebox.showerror("Ошибка", f"❌ {result['message']}")
                    self.status_var.set(f"❌ Ошибка: {result['message']}")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"❌ Ошибка при сохранении:\n{str(e)}")
            self.status_var.set(f"❌ Ошибка: {str(e)}")
    
    def save_files_after_save(self):
        """Сохраняет прикрепленные файлы после сохранения рекламации"""
        if not self.rec_id or not self.attached_files:
            return
        
        folder_path = self.get_ncr_folder()
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        for file_name in self.attached_files:
            source_path = self.file_paths.get(file_name)
            if source_path and os.path.exists(source_path):
                self.copy_file_to_ncr_folder(source_path, file_name)
    
    def clear_fields(self):
        """Очищает все поля"""
        for key, var in self.vars.items():
            var.set('')
        self.description_text.delete('1.0', 'end')
        self.attached_files = []
        self.file_paths = {}
        self.file_listbox.delete(0, tk.END)
        self.thumbnails = {}
        self.thumbnail_images = []
        self.render_gallery()
        self.status_var.set("Поля очищены")
    
    def open_list_window(self):
        """Открывает окно со списком рекламаций"""
        self.root.destroy()
        from reclamation_list import ReclamationListWindow
        root = tk.Tk()
        ReclamationListWindow(root, self.db)
        root.mainloop()