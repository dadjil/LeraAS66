import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo
from data_storage import DataStorageManager

class TableDisplayHandler:
    @staticmethod
    def clear_table(table_widget):
        for item in table_widget.get_children():
            table_widget.delete(item)

    @staticmethod
    def extract_numbers(text):
        digits = [ch for ch in str(text) if ch.isdigit()]
        return int("".join(digits)) if digits else 0

    @staticmethod
    def sort_table(table, col, reverse, numeric_sort=False):
        items = [(table.set(item, col), item) for item in table.get_children("")]

        if numeric_sort:
            items.sort(key=lambda x: TableDisplayHandler.extract_numbers(x[0]), reverse=reverse)
        else:
            try:
                items.sort(key=lambda x: x[0].lower(), reverse=reverse)
            except:
                items.sort(reverse=reverse)

        for index, (_, item) in enumerate(items):
            table.move(item, "", index)

        table.heading(col, command=lambda: TableDisplayHandler.sort_table(
            table, col, not reverse, numeric_sort
        ))

class ApplicationInterface:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Парсер велосипедов")
        self.root.geometry("1100x800")

        self.data_manager = DataStorageManager()
        self.async_mode = False

        self._setup_interface()
        self._load_scraping_sessions()

    def _setup_interface(self):
        # Главный контейнер с новой структурой
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Верхняя панель с поиском (теперь вверху)
        search_panel = ttk.LabelFrame(main_container, text="Поиск", padding=10)
        search_panel.pack(fill=tk.X, pady=(0, 15))

        # Поиск по сессиям и товарам в одной строке
        search_frame = ttk.Frame(search_panel)
        search_frame.pack(fill=tk.X)

        # Поиск по сессиям
        ttk.Label(search_frame, text="Поиск сессий:").pack(side=tk.LEFT, padx=(0, 5))
        self.session_search_entry = ttk.Entry(search_frame, width=25)
        self.session_search_entry.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            search_frame,
            text="Найти",
            command=self._search_sessions,
            width=8
        ).pack(side=tk.LEFT)

        # Разделитель
        ttk.Separator(search_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Поиск по товарам
        ttk.Label(search_frame, text="Поиск товаров:").pack(side=tk.LEFT, padx=(0, 5))
        self.model_search_entry = ttk.Entry(search_frame, width=25)
        self.model_search_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            search_frame,
            text="По модели",
            command=self._search_models,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.price_search_entry = ttk.Entry(search_frame, width=10)
        self.price_search_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            search_frame,
            text="По цене",
            command=self._search_prices,
            width=8
        ).pack(side=tk.LEFT)

        # Центральная панель с кнопками управления (теперь в центре)
        control_panel = ttk.Frame(main_container)
        control_panel.pack(fill=tk.X, pady=(0, 15))

        # Кнопки управления в центре
        ttk.Button(
            control_panel,
            text="Запустить парсинг",
            command=self._execute_scraping,
            width=20
        ).pack(side=tk.LEFT, padx=5, expand=True)

        ttk.Button(
            control_panel,
            text="Очистить данные",
            command=self._clear_all_data,
            width=20
        ).pack(side=tk.LEFT, padx=5, expand=True)

        self.async_toggle = ttk.Checkbutton(
            control_panel,
            text="Асинхронный режим",
            command=self._switch_scraping_mode
        )
        self.async_toggle.pack(side=tk.LEFT, padx=5, expand=True)

        # Нижняя панель с таблицами (теперь таблицы вертикально)
        table_panel = ttk.Frame(main_container)
        table_panel.pack(fill=tk.BOTH, expand=True)

        # Таблица сессий сверху
        session_frame = ttk.LabelFrame(table_panel, text="История сессий", padding=10)
        session_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.sessions_table = ttk.Treeview(
            session_frame,
            columns=("id", "timestamp", "count"),
            selectmode="browse",
            height=8
        )

        vsb = ttk.Scrollbar(session_frame, orient="vertical", command=self.sessions_table.yview)
        hsb = ttk.Scrollbar(session_frame, orient="horizontal", command=self.sessions_table.xview)
        self.sessions_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.sessions_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        session_frame.grid_rowconfigure(0, weight=1)
        session_frame.grid_columnconfigure(0, weight=1)

        self.sessions_table.heading("id", text="ID", command=lambda: TableDisplayHandler.sort_table(
            self.sessions_table, "id", False, numeric_sort=True))
        self.sessions_table.heading("timestamp", text="Время", command=lambda: TableDisplayHandler.sort_table(
            self.sessions_table, "timestamp", False))
        self.sessions_table.heading("count", text="Количество", command=lambda: TableDisplayHandler.sort_table(
            self.sessions_table, "count", False, numeric_sort=True))

        self.sessions_table.column("#0", width=0, stretch=tk.NO)
        self.sessions_table.column("id", width=60, anchor=tk.CENTER)
        self.sessions_table.column("timestamp", width=200)
        self.sessions_table.column("count", width=100, anchor=tk.CENTER)

        self.sessions_table.bind("<<TreeviewSelect>>", self._display_session_items)

        # Таблица товаров снизу
        product_frame = ttk.LabelFrame(table_panel, text="Товары выбранной сессии", padding=10)
        product_frame.pack(fill=tk.BOTH, expand=True)

        self.products_table = ttk.Treeview(
            product_frame,
            columns=("ref", "model", "price"),
            height=12
        )

        vsb = ttk.Scrollbar(product_frame, orient="vertical", command=self.products_table.yview)
        hsb = ttk.Scrollbar(product_frame, orient="horizontal", command=self.products_table.xview)
        self.products_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.products_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        product_frame.grid_rowconfigure(0, weight=1)
        product_frame.grid_columnconfigure(0, weight=1)

        self.products_table.heading("ref", text="ID", command=lambda: TableDisplayHandler.sort_table(
            self.products_table, "ref", False, numeric_sort=True))
        self.products_table.heading("model", text="Модель", command=lambda: TableDisplayHandler.sort_table(
            self.products_table, "model", False))
        self.products_table.heading("price", text="Цена", command=lambda: TableDisplayHandler.sort_table(
            self.products_table, "price", False, numeric_sort=True))

        self.products_table.column("#0", width=0, stretch=tk.NO)
        self.products_table.column("ref", width=60, anchor=tk.CENTER)
        self.products_table.column("model", width=300)
        self.products_table.column("price", width=150, anchor=tk.E)

    # Все методы функциональности остаются без изменений
    def _switch_scraping_mode(self):
        self.async_mode = not self.async_mode
        mode = "асинхронный" if self.async_mode else "синхронный"
        showinfo("Режим парсинга", f"Установлен {mode} режим работы")

    def _execute_scraping(self):
        from web_scrapper import SynchronousScraper, AsynchronousScraper

        scraper = AsynchronousScraper() if self.async_mode else SynchronousScraper()
        scraped_items = scraper.scrape_all_pages()

        self.data_manager.store_scraped_data(scraped_items)
        self._load_scraping_sessions()

    def _clear_all_data(self):
        self.data_manager.clear_storage()
        TableDisplayHandler.clear_table(self.sessions_table)
        TableDisplayHandler.clear_table(self.products_table)

    def _load_scraping_sessions(self):
        TableDisplayHandler.clear_table(self.sessions_table)
        sessions = self.data_manager.fetch_all_sessions()

        for session_id, timestamp, count in sessions:
            self.sessions_table.insert('', tk.END, values=(session_id, timestamp, count))

    def _search_sessions(self):
        search_term = self.session_search_entry.get()
        TableDisplayHandler.clear_table(self.sessions_table)

        sessions = self.data_manager.fetch_all_sessions()
        for session_id, timestamp, count in sessions:
            if search_term.lower() in timestamp.lower():
                self.sessions_table.insert('', tk.END, values=(session_id, timestamp, count))

    def _display_session_items(self, event):
        TableDisplayHandler.clear_table(self.products_table)
        selected_items = self.sessions_table.selection()

        if selected_items:
            selected_session = self.sessions_table.item(selected_items[0])
            session_id = selected_session['values'][0]

            products = self.data_manager.fetch_session_items(session_id)
            for model, price, ref in products:
                self.products_table.insert('', tk.END, values=(ref, model, price))

    def _search_models(self):
        search_term = self.model_search_entry.get().lower()
        TableDisplayHandler.clear_table(self.products_table)

        selected_items = self.sessions_table.selection()
        if not selected_items:
            return

        selected_session = self.sessions_table.item(selected_items[0])
        session_id = selected_session['values'][0]

        products = self.data_manager.fetch_session_items(session_id)
        for model, price, ref in products:
            if search_term in model.lower():
                self.products_table.insert('', tk.END, values=(ref, model, price))

    def _search_prices(self):
        try:
            target_price = int(self.price_search_entry.get())
        except ValueError:
            showinfo("Ошибка", "Пожалуйста, введите числовое значение цены")
            return

        TableDisplayHandler.clear_table(self.products_table)
        selected_items = self.sessions_table.selection()

        if not selected_items:
            return

        selected_session = self.sessions_table.item(selected_items[0])
        session_id = selected_session['values'][0]

        products = self.data_manager.fetch_session_items(session_id)
        for model, price, ref in products:
            numeric_price = TableDisplayHandler.extract_numbers(price)
            if numeric_price == target_price:
                self.products_table.insert('', tk.END, values=(ref, model, price))