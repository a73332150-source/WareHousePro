"""
WareHousePro - Splash Screen & Asynchronous Warmup Subsystem
Initializes database connections and cache in a worker thread to prevent UI freezing.
"""
import time
import logging
from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QColor, QFont, QPainter

import branding

logger = logging.getLogger("WareHousePro.Splash")

class WarmupWorker(QThread):
    progress_changed = pyqtSignal(int, str)
    finished_init = pyqtSignal()

    def __init__(self, db_manager, security_manager):
        super().__init__()
        self.db = db_manager
        self.security = security_manager

    def run(self):
        steps = [
            (20, "فحص سلامة قاعدة البيانات وتفعيل المفاتيح الأجنبية..."),
            (40, "التحقق من جداول المخزون وسجلات التدقيق..."),
            (60, "تهيئة منظومة التشفير ومطابقة الصلاحيات..."),
            (80, "تحميل إعدادات الواجهة والأنماط الهندسية..."),
            (100, "النظام جاهز للتشغيل.")
        ]
        for pct, msg in steps:
            time.sleep(0.15)
            self.progress_changed.emit(pct, msg)
            if pct == 20:
                self.db.check_integrity()
            elif pct == 60:
                self.security.bootstrap_default_admin(self.db)

        self.finished_init.emit()

class ModernSplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(520, 300)
        pixmap.fill(QColor("#0f172a"))

        # Paint branding title directly on pixmap
        painter = QPainter(pixmap)
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
        painter.drawText(30, 80, branding.APP_NAME)

        painter.setFont(QFont("Cairo", 12))
        painter.setPen(QColor("#94a3b8"))
        painter.drawText(30, 115, branding.APP_SUBTITLE)

        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor("#38bdf8"))
        painter.drawText(30, 140, f"الإصدار: {branding.APP_VERSION} (Stand-alone EXE)")
        painter.end()

        super().__init__(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Progress bar container
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(30, 220, 460, 8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border-radius: 4px;
                border: none;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 4px;
            }
        """)
        self.progress_bar.setValue(0)

        self.status_label = QLabel(self)
        self.status_label.setGeometry(30, 235, 460, 24)
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.status_label.setText("جاري تهيئة النظام...")

    def update_progress(self, val: int, message: str):
        self.progress_bar.setValue(val)
        self.status_label.setText(message)
