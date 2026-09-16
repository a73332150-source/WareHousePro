"""
WareHousePro - About and Diagnostics Dialog
Shows build version, Python/SQLite runtime metrics and copyright.
"""
import sys
import sqlite3
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
import branding

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"حول {branding.APP_NAME}")
        self.setFixedSize(450, 320)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel(branding.APP_NAME)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2563eb;")
        layout.addWidget(title)

        subtitle = QLabel(branding.APP_SUBTITLE)
        subtitle.setStyleSheet("font-size: 13px; color: #475569;")
        layout.addWidget(subtitle)

        details = QLabel(
            f"<b>الإصدار:</b> {branding.APP_VERSION}<br>"
            f"<b>رقم البناء:</b> {branding.BUILD_ID}<br>"
            f"<b>محرك قواعد البيانات:</b> SQLite {sqlite3.sqlite_version} (WAL + Foreign Keys Enabled)<br>"
            f"<b>بيئة التشغيل:</b> Python {sys.version.split()[0]} (Standalone Windows Executable)<br>"
            f"<b>حالة الأمان:</b> مؤمن بـ PBKDF2 + حماية العمليات الذرية (ACID)"
        )
        details.setStyleSheet("background-color: #f1f5f9; border-radius: 6px; padding: 12px; font-size: 12px;")
        layout.addWidget(details)

        copy = QLabel(branding.COPYRIGHT)
        copy.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(copy)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("إغلاق")
        ok_btn.setProperty("class", "PrimaryBtn")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
