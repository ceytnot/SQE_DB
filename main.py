# main.py
import tkinter as tk
from tkinter import messagebox
from database import Database
from reclamation_list import ReclamationListWindow  # ← Сразу загружаем список

def main():
    try:
        db = Database()
        print("✅ Подключение к базе данных установлено")
    except Exception as e:
        print(f"❌ Ошибка подключения к базе: {e}")
        
        root = tk.Tk()
        root.withdraw()
        
        retry = messagebox.askretrycancel(
            "Ошибка подключения", 
            f"Не удалось подключиться к базе данных.\n\n"
            f"Ошибка: {str(e)}\n\n"
            f"Проверьте:\n"
            f"1. Путь к файлу Access правильный\n"
            f"2. Пароль правильный\n"
            f"3. Файл не открыт в другой программе"
        )
        root.destroy()
        
        if retry:
            main()
        return
    
    # ✅ Сразу открываем список рекламаций
    root = tk.Tk()
    ReclamationListWindow(root, db)
    root.mainloop()

if __name__ == "__main__":
    main()