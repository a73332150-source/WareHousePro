"""
WareHousePro - Application Menu Bar & Action Routing
Features keyboard accelerators and role-based action gating.
"""
from PyQt5.QtWidgets import QMenuBar, QAction, QMessageBox

class AppMenuBar(QMenuBar):
    def __init__(self, parent, security_manager):
        super().__init__(parent)
        self.main_win = parent
        self.security = security_manager
        self._create_menus()

    def _create_menus(self):
        # 1. File Menu
        file_menu = self.addMenu("ملف (File)")

        backup_act = QAction("نسخ احتياطي لقاعدة البيانات...", self)
        backup_act.setShortcut("Ctrl+B")
        backup_act.triggered.connect(self.main_win.create_backup)
        backup_act.setEnabled(self.security.has_permission("DATABASE_BACKUP"))
        file_menu.addAction(backup_act)

        file_menu.addSeparator()

        logout_act = QAction("تسجيل الخروج", self)
        logout_act.triggered.connect(self.main_win.logout)
        file_menu.addAction(logout_act)

        exit_act = QAction("إغلاق البرنامج", self)
        exit_act.setShortcut("Alt+F4")
        exit_act.triggered.connect(self.main_win.close)
        file_menu.addAction(exit_act)

        # 2. Operations Menu
        ops_menu = self.addMenu("العمليات (Operations)")

        new_prod_act = QAction("إضافة صنف جديد...", self)
        new_prod_act.setShortcut("Ctrl+N")
        new_prod_act.triggered.connect(self.main_win.open_add_product)
        new_prod_act.setEnabled(self.security.has_permission("MANAGE_PRODUCTS"))
        ops_menu.addAction(new_prod_act)

        move_act = QAction("تسجيل حركة مخزنية...", self)
        move_act.setShortcut("Ctrl+M")
        move_act.triggered.connect(self.main_win.open_record_movement)
        move_act.setEnabled(self.security.has_permission("RECORD_MOVEMENT"))
        ops_menu.addAction(move_act)

        # 3. Reports Menu
        reports_menu = self.addMenu("التقارير (Reports)")

        export_act = QAction("تصدير جرد المخزون (CSV)...", self)
        export_act.triggered.connect(self.main_win.export_inventory)
        reports_menu.addAction(export_act)

        # 4. Help Menu
        help_menu = self.addMenu("مساعدة (Help)")

        about_act = QAction("حول WareHousePro...", self)
        about_act.triggered.connect(self.main_win.open_about_dialog)
        help_menu.addAction(about_act)
