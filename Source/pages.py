"""
WareHousePro - Core Application Views & Multi-threading Logic
Uses non-blocking QThread workers for database exports and analytical queries.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QHeaderView,
    QFrame, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from dialogs import ProductDialog, MovementDialog

class ExportWorker(QThread):
    finished_export = pyqtSignal(str)
    failed_export = pyqtSignal(str)

    def __init__(self, products, file_path):
        super().__init__()
        self.products = products
        self.file_path = file_path

    def run(self):
        try:
            import csv
            with open(self.file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["رمز الصنف", "اسم الصنف", "التصنيف", "الرصيد", "الحد الأدنى", "سعر الوحدة", "المورد", "الموقع"])
                for p in self.products:
                    writer.writerow([
                        p.get("sku", ""),
                        p.get("name", ""),
                        p.get("category_name", ""),
                        p.get("quantity", 0),
                        p.get("min_threshold", 0),
                        p.get("unit_price", 0.0),
                        p.get("supplier_name", ""),
                        p.get("location_bin", "")
                    ])
            self.finished_export.emit(self.file_path)
        except Exception as e:
            self.failed_export.emit(str(e))

class DashboardPage(QWidget):
    def __init__(self, db_manager, main_window):
        super().__init__()
        self.db = db_manager
        self.main_win = main_window
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header Title
        title = QLabel("لوحة التحكم والمؤشرات التشغيلية")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a;")
        layout.addWidget(title)

        # KPI Row
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self.card_total_prod = self._create_kpi_card("إجمالي الأصناف", "0 صنف")
        self.card_total_units = self._create_kpi_card("إجمالي الوحدات المخزنة", "0 قطعة")
        self.card_valuation = self._create_kpi_card("القيمة التقديرية للمخزون", "0.00 ر.س")
        self.card_low_stock = self._create_kpi_card("تنبيهات نقص المخزون", "0 صنف", is_alert=True)

        kpi_layout.addWidget(self.card_total_prod)
        kpi_layout.addWidget(self.card_total_units)
        kpi_layout.addWidget(self.card_valuation)
        kpi_layout.addWidget(self.card_low_stock)
        layout.addLayout(kpi_layout)

        # Quick Actions Bar
        actions_frame = QFrame()
        actions_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;")
        act_layout = QHBoxLayout(actions_frame)

        act_label = QLabel("إجراءات سريعة:")
        act_label.setStyleSheet("font-weight: bold; color: #334155;")
        act_layout.addWidget(act_label)

        btn_add_prod = QPushButton("+ إضافة صنف جديد")
        btn_add_prod.setProperty("class", "PrimaryBtn")
        btn_add_prod.clicked.connect(self.main_win.open_add_product)
        act_layout.addWidget(btn_add_prod)

        btn_move = QPushButton("تسجيل حركة إدخال / إخراج")
        btn_move.setProperty("class", "SecondaryBtn")
        btn_move.clicked.connect(self.main_win.open_record_movement)
        act_layout.addWidget(btn_move)

        act_layout.addStretch()
        layout.addWidget(actions_frame)

        # Recent Movements Table
        recent_title = QLabel("أحدث الحركات المخزنية المسجلة")
        recent_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1e293b; margin-top: 10px;")
        layout.addWidget(recent_title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["الوقت والتاريخ", "رمز الصنف", "اسم الصنف", "نوع الحركة", "الكمية", "المستخدم المسؤول"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.refresh()

    def _create_kpi_card(self, label: str, default_val: str, is_alert: bool = False) -> QFrame:
        card = QFrame()
        card.setProperty("class", "KpiCard")
        l = QVBoxLayout(card)
        l.setSpacing(6)

        lbl = QLabel(label)
        lbl.setProperty("class", "KpiLabel")

        val = QLabel(default_val)
        val.setProperty("class", "KpiValue")
        if is_alert:
            val.setStyleSheet("color: #ef4444;")

        l.addWidget(lbl)
        l.addWidget(val)
        card.value_widget = val
        return card

    def refresh(self):
        kpis = self.db.get_dashboard_kpis()
        self.card_total_prod.value_widget.setText(f"{kpis['total_products']} صنف")
        self.card_total_units.value_widget.setText(f"{kpis['total_units']:,} قطعة")
        self.card_valuation.value_widget.setText(f"{kpis['total_valuation']:,.2f} ر.س")
        self.card_low_stock.value_widget.setText(f"{kpis['low_stock_count']} صنف")

        movements = self.db.get_recent_movements(20)
        self.table.setRowCount(len(movements))
        for row, m in enumerate(movements):
            self.table.setItem(row, 0, QTableWidgetItem(str(m["created_at"])))
            self.table.setItem(row, 1, QTableWidgetItem(str(m["sku"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(m["product_name"])))
            m_type = "وارد (+)" if m["movement_type"] == "IN" else "منصرف (-)"
            self.table.setItem(row, 3, QTableWidgetItem(m_type))
            self.table.setItem(row, 4, QTableWidgetItem(str(m["quantity"])))
            self.table.setItem(row, 5, QTableWidgetItem(str(m["user_name"] or "النظام")))

class InventoryPage(QWidget):
    def __init__(self, db_manager, main_window):
        super().__init__()
        self.db = db_manager
        self.main_win = main_window
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Top Bar (Search + Filter + Actions)
        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم أو الرمز (SKU) أو المورد...")
        self.search_input.textChanged.connect(self.refresh)
        top_bar.addWidget(self.search_input, stretch=2)

        self.cat_filter = QComboBox()
        self.cat_filter.addItem("جميع التصنيفات", None)
        conn = self.db._get_connection()
        for cat in conn.execute("SELECT id, name FROM categories;").fetchall():
            self.cat_filter.addItem(cat["name"], cat["id"])
        self.cat_filter.currentIndexChanged.connect(self.refresh)
        top_bar.addWidget(self.cat_filter, stretch=1)

        self.btn_export = QPushButton("تصدير إلى CSV")
        self.btn_export.setProperty("class", "SecondaryBtn")
        self.btn_export.clicked.connect(self._export_csv)
        top_bar.addWidget(self.btn_export)

        layout.addLayout(top_bar)

        # Inventory Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "الرمز (SKU)", "اسم الصنف", "التصنيف", "الرصيد المتوفر", "حد التنبيه", "سعر الوحدة", "الموقع"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        search = self.search_input.text()
        cat_id = self.cat_filter.currentData()
        products = self.db.get_all_products(search=search, category_id=cat_id)
        self.table.setRowCount(len(products))

        for row, p in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(str(p["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(p["sku"]))
            self.table.setItem(row, 2, QTableWidgetItem(p["name"]))
            self.table.setItem(row, 3, QTableWidgetItem(p["category_name"] or "-"))

            qty_item = QTableWidgetItem(str(p["quantity"]))
            if p["quantity"] <= p["min_threshold"]:
                qty_item.setForeground(Qt.red)
            self.table.setItem(row, 4, qty_item)

            self.table.setItem(row, 5, QTableWidgetItem(str(p["min_threshold"])))
            self.table.setItem(row, 6, QTableWidgetItem(f"{p['unit_price']:.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(p["location_bin"] or "-"))

    def _export_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "حفظ ملف المخزون", "inventory_report.csv", "CSV Files (*.csv)")
        if file_path:
            products = self.db.get_all_products()
            self.worker = ExportWorker(products, file_path)
            self.worker.finished_export.connect(lambda p: QMessageBox.information(self, "نجاح التصدير", f"تم تصدير المخزون بنجاح إلى:\n{p}"))
            self.worker.failed_export.connect(lambda err: QMessageBox.critical(self, "فشل التصدير", f"حدث خطأ أثناء التصدير:\n{err}"))
            self.worker.start()
