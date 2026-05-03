import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker - Личные финансы")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        # Файл для хранения данных
        self.data_file = "expenses.json"
        self.expenses = []
        
        # Категории расходов
        self.categories = ["Еда", "Транспорт", "Развлечения", "Здоровье", 
                          "Коммунальные услуги", "Одежда", "Другое"]
        
        # Загрузка сохранённых данных
        self.load_data()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Обновление таблицы
        self.refresh_table()
    
    def create_widgets(self):
        # Стили
        style = ttk.Style()
        style.theme_use('clam')
        
        # === Панель ввода ===
        input_frame = ttk.LabelFrame(self.root, text="Добавить расход", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # Сумма
        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.amount_entry = ttk.Entry(input_frame, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Категория
        ttk.Label(input_frame, text="Категория:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.category_combo = ttk.Combobox(input_frame, values=self.categories, width=15, state="readonly")
        self.category_combo.grid(row=0, column=3, padx=5, pady=5)
        self.category_combo.current(0)
        
        # Дата
        ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.date_entry = ttk.Entry(input_frame, width=12)
        self.date_entry.grid(row=0, column=5, padx=5, pady=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Кнопка добавления
        self.add_btn = ttk.Button(input_frame, text="➕ Добавить расход", command=self.add_expense)
        self.add_btn.grid(row=0, column=6, padx=10, pady=5)
        
        # === Панель фильтрации ===
        filter_frame = ttk.LabelFrame(self.root, text="Фильтрация", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        # Фильтр по категории
        ttk.Label(filter_frame, text="Категория:").grid(row=0, column=0, padx=5, pady=5)
        self.filter_category = ttk.Combobox(filter_frame, values=["Все"] + self.categories, width=15, state="readonly")
        self.filter_category.grid(row=0, column=1, padx=5, pady=5)
        self.filter_category.current(0)
        
        # Фильтр по дате (период)
        ttk.Label(filter_frame, text="Дата от (ГГГГ-ММ-ДД):").grid(row=0, column=2, padx=5, pady=5)
        self.filter_date_from = ttk.Entry(filter_frame, width=12)
        self.filter_date_from.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="До:").grid(row=0, column=4, padx=5, pady=5)
        self.filter_date_to = ttk.Entry(filter_frame, width=12)
        self.filter_date_to.grid(row=0, column=5, padx=5, pady=5)
        
        # Кнопка применения фильтра
        self.filter_btn = ttk.Button(filter_frame, text="🔍 Применить фильтр", command=self.refresh_table)
        self.filter_btn.grid(row=0, column=6, padx=10, pady=5)
        
        # Кнопка сброса фильтра
        self.reset_btn = ttk.Button(filter_frame, text="❌ Сброс", command=self.reset_filter)
        self.reset_btn.grid(row=0, column=7, padx=5, pady=5)
        
        # === Таблица расходов ===
        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Treeview
        columns = ("ID", "Дата", "Категория", "Сумма")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", 
                                  yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        # Настройка колонок
        self.tree.heading("ID", text="ID")
        self.tree.heading("Дата", text="Дата")
        self.tree.heading("Категория", text="Категория")
        self.tree.heading("Сумма", text="Сумма (₽)")
        
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Дата", width=100, anchor="center")
        self.tree.column("Категория", width=150, anchor="w")
        self.tree.column("Сумма", width=100, anchor="e")
        
        self.tree.pack(fill="both", expand=True)
        
        # === Панель итогов ===
        summary_frame = ttk.Frame(self.root)
        summary_frame.pack(fill="x", padx=10, pady=5)
        
        self.total_label = ttk.Label(summary_frame, text="Общая сумма за период: 0.00 ₽", 
                                     font=("Arial", 12, "bold"))
        self.total_label.pack(side="left", padx=5)
        
        # Кнопка удаления выбранной записи
        self.delete_btn = ttk.Button(summary_frame, text="🗑 Удалить выбранную", command=self.delete_expense)
        self.delete_btn.pack(side="right", padx=5)
        
        # Кнопка сохранения в JSON
        self.save_btn = ttk.Button(summary_frame, text="💾 Сохранить в JSON", command=self.save_to_json)
        self.save_btn.pack(side="right", padx=5)
    
    def validate_amount(self, amount_str):
        """Проверка корректности суммы"""
        try:
            amount = float(amount_str)
            if amount <= 0:
                return False, "Сумма должна быть положительным числом"
            return True, amount
        except ValueError:
            return False, "Сумма должна быть числом"
    
    def validate_date(self, date_str):
        """Проверка корректности даты"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True, date_str
        except ValueError:
            return False, "Дата должна быть в формате ГГГГ-ММ-ДД (например, 2024-12-25)"
    
    def add_expense(self):
        """Добавление нового расхода"""
        # Валидация суммы
        amount_valid, amount_result = self.validate_amount(self.amount_entry.get())
        if not amount_valid:
            messagebox.showerror("Ошибка ввода", amount_result)
            return
        
        # Валидация даты
        date_valid, date_result = self.validate_date(self.date_entry.get())
        if not date_valid:
            messagebox.showerror("Ошибка ввода", date_result)
            return
        
        # Создание записи
        expense = {
            "id": len(self.expenses) + 1 if self.expenses else 1,
            "amount": amount_result,
            "category": self.category_combo.get(),
            "date": date_result
        }
        
        self.expenses.append(expense)
        self.save_data()
        self.refresh_table()
        
        # Очистка поля суммы
        self.amount_entry.delete(0, tk.END)
        
        messagebox.showinfo("Успех", f"Расход {amount_result} ₽ добавлен!")
    
    def delete_expense(self):
        """Удаление выбранной записи"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return
        
        # Получение ID выбранной записи
        item = self.tree.item(selected[0])
        expense_id = item['values'][0]
        
        # Удаление из списка
        self.expenses = [e for e in self.expenses if e['id'] != expense_id]
        
        # Перенумерация ID
        for idx, expense in enumerate(self.expenses, 1):
            expense['id'] = idx
        
        self.save_data()
        self.refresh_table()
        messagebox.showinfo("Успех", "Запись удалена")
    
    def get_filtered_expenses(self):
        """Получение отфильтрованных расходов"""
        filtered = self.expenses.copy()
        
        # Фильтр по категории
        category = self.filter_category.get()
        if category != "Все":
            filtered = [e for e in filtered if e['category'] == category]
        
        # Фильтр по дате
        date_from = self.filter_date_from.get().strip()
        date_to = self.filter_date_to.get().strip()
        
        if date_from:
            try:
                datetime.strptime(date_from, "%Y-%m-%d")
                filtered = [e for e in filtered if e['date'] >= date_from]
            except ValueError:
                if date_from:
                    messagebox.showwarning("Предупреждение", "Неверный формат 'Дата от'")
        
        if date_to:
            try:
                datetime.strptime(date_to, "%Y-%m-%d")
                filtered = [e for e in filtered if e['date'] <= date_to]
            except ValueError:
                if date_to:
                    messagebox.showwarning("Предупреждение", "Неверный формат 'Дата до'")
        
        return filtered
    
    def calculate_total(self, expenses):
        """Подсчёт суммы расходов"""
        return sum(e['amount'] for e in expenses)
    
    def refresh_table(self):
        """Обновление таблицы и итоговой суммы"""
        # Очистка таблицы
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Получение отфильтрованных данных
        filtered = self.get_filtered_expenses()
        
        # Заполнение таблицы
        for expense in filtered:
            self.tree.insert("", "end", values=(
                expense['id'],
                expense['date'],
                expense['category'],
                f"{expense['amount']:.2f}"
            ))
        
        # Подсчёт суммы
        total = self.calculate_total(filtered)
        self.total_label.config(text=f"Общая сумма за период: {total:.2f} ₽")
    
    def reset_filter(self):
        """Сброс фильтров"""
        self.filter_category.current(0)
        self.filter_date_from.delete(0, tk.END)
        self.filter_date_to.delete(0, tk.END)
        self.refresh_table()
    
    def load_data(self):
        """Загрузка данных из JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.expenses = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.expenses = []
    
    def save_data(self):
        """Сохранение данных в JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.expenses, f, ensure_ascii=False, indent=2)
    
    def save_to_json(self):
        """Ручное сохранение в JSON (с уведомлением)"""
        self.save_data()
        messagebox.showinfo("Сохранено", f"Данные сохранены в {self.data_file}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()