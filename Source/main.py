"""
WareHousePro - Master Entry Point & Application Controller
Enforces single-instance mutex, global exception handling, High-DPI scaling,
and clean lifecycle shutdown.
"""
import sys
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt

# Ensure local imports work in both frozen and script modes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import branding
from database import DatabaseManager
from security import SecurityManager
from styles import APP_QSS
from splash import ModernSplashScreen, WarmupWorker
from pages import DashboardPage, InventoryPage
from menu_bar import AppMenuBar
from dialogs import ProductDialog, MovementDialog
from about_dialog import AboutDialog
from exceptions import setup_global_exception_handler, InsufficientStockError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s"
)
logger = logging.getLogger("WareHousePro.Main")

class MainWindow(QMainWindow):
    def __init__(self, db_manager, security_manager):
        super().__init__()
        self.db = db_manager
        self.security = security_manager
        self.setWindowTitle(f"{branding.APP_NAME} - {branding.APP_SUBTITLE} ({branding.APP_VERSION})")
        self.resize(1180, 720)
        self._init_ui()

    def _init_ui(self):
        # Central widget with sidebar + content stack
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Navigation
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 16, 12, 16)
        side_layout.setSpacing(8)

        brand_lbl = QLabel(branding.APP_NAME)
        brand_lbl.setObjectName("BrandTitle")
        side_layout.addWidget(brand_lbl)

        user_info = QLabel(f"المستخدم: {self.security.current_user['full_name']}\n({self.security.current_user['role'].value})")
        user_info.setStyleSheet("color: #64748b; font-size: 11px; margin-bottom: 12px; padding-left: 8px;")
        side_layout.addWidget(user_info)

        self.btn_nav_dash = QPushButton("📊 لوحة المؤشرات")
        self.btn_nav_dash.setProperty("class", "NavButton")
        self.btn_nav_dash.setCheckable(True)
        self.btn_nav_dash.setChecked(True)
        self.btn_nav_dash.clicked.connect(lambda: self._switch_page(0))
        side_layout.addWidget(self.btn_nav_dash)

        self.btn_nav_inv = QPushButton("📦 إدارة المخزون")
        self.btn_nav_inv.setProperty("class", "NavButton")
        self.btn_nav_inv.setCheckable(True)
        self.btn_nav_inv.clicked.connect(lambda: self._switch_page(1))
        side_layout.addWidget(self.btn_nav_inv)

        side_layout.addStretch()

        btn_about = QPushButton("ℹ️ حول النظام")
        btn_about.setProperty("class", "NavButton")
        btn_about.clicked.connect(self.open_about_dialog)
        side_layout.addWidget(btn_about)

        main_layout.addWidget(sidebar)

        # Stacked Pages
        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage(self.db, self)
        self.inventory_page = InventoryPage(self.db, self)

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.inventory_page)
        main_layout.addWidget(self.stack)

        # Menu Bar & Status Bar
        self.setMenuBar(AppMenuBar(self, self.security))
        self.statusBar().showMessage(f"متصل بقاعدة البيانات الآمنة | المستخدم الحالي: {self.security.current_user['username']}")

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.btn_nav_dash.setChecked(index == 0)
        self.btn_nav_inv.setChecked(index == 1)
        if index == 0:
            self.dashboard_page.refresh()
        elif index == 1:
            self.inventory_page.refresh()

    def open_add_product(self):
        conn = self.db._get_connection()
        cats = [dict(r) for r in conn.execute("SELECT id, name FROM categories;").fetchall()]
        dlg = ProductDialog(self, cats)
        if dlg.exec_():
            data = dlg.get_data()
            try:
                self.db.add_product(
                    sku=data["sku"],
                    name=data["name"],
                    category_id=data["category_id"],
                    quantity=data["quantity"],
                    min_threshold=data["min_threshold"],
                    unit_price=data["unit_price"],
                    supplier_name=data["supplier_name"],
                    location_bin=data["location_bin"],
                    user_id=self.security.current_user["id"]
                )
                QMessageBox.information(self, "نجاح", "تمت إضافة الصنف بنجاح في قاعدة البيانات.")
                self.dashboard_page.refresh()
                self.inventory_page.refresh()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"تعذر إضافة الصنف:\n{e}")

    def open_record_movement(self):
        products = self.db.get_all_products()
        if not products:
            QMessageBox.warning(self, "تنبيه", "لا توجد أي أصناف مسجلة بالمستودع بعد.")
            return

        dlg = MovementDialog(self, products)
        if dlg.exec_():
            data = dlg.get_data()
            try:
                self.db.record_stock_movement(
                    product_id=data["product_id"],
                    movement_type=data["movement_type"],
                    quantity=data["quantity"],
                    unit_price=0.0,
                    reference_no=data["reference_no"],
                    notes=data["notes"],
                    user_id=self.security.current_user["id"]
                )
                QMessageBox.information(self, "نجاح", "تم تثبيت الحركة المخزنية وتحديث الرصيد بنجاح.")
                self.dashboard_page.refresh()
                self.inventory_page.refresh()
            except InsufficientStockError as err:
                QMessageBox.critical(self, "رصيد غير كافٍ", str(err))
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل تسجيل الحركة:\n{e}")

    def create_backup(self):
        dest, _ = QFileDialog.getSaveFileName(self, "حفظ نسخة احتياطية", "warehousepro_backup.db", "SQLite Database (*.db)")
        if dest:
            import shutil
            try:
                shutil.copy2(self.db.db_path, dest)
                QMessageBox.information(self, "نسخ احتياطي", f"تم إنشاء النسخة الاحتياطية بنجاح في:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل النسخ الاحتياطي: {e}")

    def export_inventory(self):
        self.inventory_page._export_csv()

    def open_about_dialog(self):
        AboutDialog(self).exec_()

    def logout(self):
        self.security.logout()
        self.close()

def main():
    setup_global_exception_handler()

    # Enable High DPI scaling for crisp Windows rendering
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)

    db_manager = DatabaseManager()
    security_manager = SecurityManager()

    # Launch Splash Screen
    splash = ModernSplashScreen()
    splash.show()

    worker = WarmupWorker(db_manager, security_manager)
    worker.progress_changed.connect(splash.update_progress)

    def launch_main():
        splash.finish(None)
        # For seamless desktop demo, auto-login default Admin if not set
        security_manager.login("admin", "Admin@123", db_manager)
        win = MainWindow(db_manager, security_manager)
        win.show()
        # Keep reference to prevent GC collection
        app.main_window = win

    worker.finished_init.connect(launch_main)
    worker.start()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
