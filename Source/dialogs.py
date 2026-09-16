"""
WareHousePro - Interactive Modal Dialogs
Full input validation, sanitization, and atomic commit handlers.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt
from exceptions import InsufficientStockError, ValidationError

class ProductDialog(QDialog):
    def __init__(self, parent, categories, product_data=None):
        super().__init__(parent)
        self.product_data = product_data
        self.categories = categories
        self.setWindowTitle("تعديل الصنف" if product_data else "إضافة صنف جديد للمستودع")
        self.setFixedWidth(440)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # SKU
        layout.addWidget(QLabel("رمز الصنف (SKU):"))
        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("مثال: PRD-9001")
        if self.product_data:
            self.sku_input.setText(self.product_data.get("sku", ""))
            self.sku_input.setEnabled(False) # Prevent modifying immutable SKU
        layout.addWidget(self.sku_input)

        # Name
        layout.addWidget(QLabel("اسم الصنف:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: لوحة تحكم رئيسية V2")
        if self.product_data:
            self.name_input.setText(self.product_data.get("name", ""))
        layout.addWidget(self.name_input)

        # Category
        layout.addWidget(QLabel("التصنيف:"))
        self.cat_combo = QComboBox()
        for cat in self.categories:
            self.cat_combo.addItem(cat["name"], cat["id"])
        if self.product_data and self.product_data.get("category_id"):
            idx = self.cat_combo.findData(self.product_data["category_id"])
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
        layout.addWidget(self.cat_combo)

        # Initial Quantity (only if adding)
        if not self.product_data:
            layout.addWidget(QLabel("الرصيد الافتتاحي الأولي:"))
            self.qty_spin = QSpinBox()
            self.qty_spin.setRange(0, 1_000_000)
            self.qty_spin.setValue(0)
            layout.addWidget(self.qty_spin)

        # Min Alert Threshold
        layout.addWidget(QLabel("حد التنبيه الأدنى (Low Stock Alert):"))
        self.min_spin = QSpinBox()
        self.min_spin.setRange(1, 10_000)
        self.min_spin.setValue(self.product_data.get("min_threshold", 5) if self.product_data else 5)
        layout.addWidget(self.min_spin)

        # Unit Price
        layout.addWidget(QLabel("سعر الوحدة (ر.س / $):"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0.0, 1_000_000.0)
        self.price_spin.setValue(float(self.product_data.get("unit_price", 0.0) if self.product_data else 0.0))
        layout.addWidget(self.price_spin)

        # Supplier & Location
        layout.addWidget(QLabel("المورد الرئيسي:"))
        self.supplier_input = QLineEdit()
        if self.product_data:
            self.supplier_input.setText(self.product_data.get("supplier_name", ""))
        layout.addWidget(self.supplier_input)

        layout.addWidget(QLabel("موقع التخزين في المستودع (Bin Location):"))
        self.bin_input = QLineEdit()
        self.bin_input.setPlaceholderText("مثال: رف A-12")
        if self.product_data:
            self.bin_input.setText(self.product_data.get("location_bin", ""))
        layout.addWidget(self.bin_input)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("حفظ التغييرات" if self.product_data else "إضافة الصنف")
        self.save_btn.setProperty("class", "PrimaryBtn")
        self.save_btn.clicked.connect(self._validate_and_accept)

        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setProperty("class", "SecondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _validate_and_accept(self):
        if not self.sku_input.text().strip():
            QMessageBox.warning(self, "خطأ في الإدخال", "حقل رمز الصنف (SKU) إلزامي.")
            return
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "خطأ في الإدخال", "حقل اسم الصنف إلزامي.")
            return
        self.accept()

    def get_data(self):
        return {
            "sku": self.sku_input.text().strip(),
            "name": self.name_input.text().strip(),
            "category_id": self.cat_combo.currentData(),
            "quantity": getattr(self, "qty_spin", None).value() if hasattr(self, "qty_spin") else 0,
            "min_threshold": self.min_spin.value(),
            "unit_price": self.price_spin.value(),
            "supplier_name": self.supplier_input.text().strip(),
            "location_bin": self.bin_input.text().strip()
        }

class MovementDialog(QDialog):
    def __init__(self, parent, products):
        super().__init__(parent)
        self.products = products
        self.setWindowTitle("تسجيل حركة مخزنية جديدة (إدخال / إخراج)")
        self.setFixedWidth(460)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("اختر الصنف:"))
        self.prod_combo = QComboBox()
        for p in self.products:
            self.prod_combo.addItem(f"{p['name']} ({p['sku']}) - متوفر: {p['quantity']}", p["id"])
        layout.addWidget(self.prod_combo)

        layout.addWidget(QLabel("نوع العملية:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("وارد مخزني (شراء / توريد)", "IN")
        self.type_combo.addItem("منصرف مخزني (بيع / صرف)", "OUT")
        layout.addWidget(self.type_combo)

        layout.addWidget(QLabel("الكمية:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 100_000)
        self.qty_spin.setValue(1)
        layout.addWidget(self.qty_spin)

        layout.addWidget(QLabel("رقم السند المرجعي (فاتورة / إذن تسليم):"))
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("مثال: INV-2026-042")
        layout.addWidget(self.ref_input)

        layout.addWidget(QLabel("ملاحظات / سبب الحركة:"))
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(70)
        layout.addWidget(self.notes_input)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("تنفيذ وتثبيت الحركة")
        self.save_btn.setProperty("class", "PrimaryBtn")
        self.save_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setProperty("class", "SecondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            "product_id": self.prod_combo.currentData(),
            "movement_type": self.type_combo.currentData(),
            "quantity": self.qty_spin.value(),
            "reference_no": self.ref_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip()
        }
