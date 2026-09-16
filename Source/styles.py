"""
WareHousePro - Visual Design & QSS Theme Engine
Adheres to strict accessibility standards, mathematical padding/border radius,
and crisp typography for Windows desktop environments.
"""

APP_QSS = """
/* ==========================================================
   WareHousePro Master Theme (Windows Enterprise Clean)
   ========================================================== */

* {
    font-family: 'Segoe UI', 'Cairo', 'Arial', sans-serif;
    font-size: 13px;
    color: #1e293b;
}

QMainWindow, QDialog {
    background-color: #f8fafc;
}

QWidget#CentralWidget {
    background-color: #f8fafc;
}

/* ---------------- Top Menu Bar ---------------- */
QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 2px 6px;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #f1f5f9;
    color: #0f172a;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

/* ---------------- Sidebar Navigation ---------------- */
QWidget#Sidebar {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
}

QLabel#BrandTitle {
    color: #ffffff;
    font-size: 18px;
    font-weight: bold;
    padding: 16px 12px;
}

QPushButton.NavButton {
    background-color: transparent;
    color: #94a3b8;
    text-align: left;
    padding: 10px 16px;
    border-radius: 6px;
    border: none;
    font-size: 13px;
    font-weight: 500;
}

QPushButton.NavButton:hover {
    background-color: #1e293b;
    color: #ffffff;
}

QPushButton.NavButton:checked {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: bold;
}

/* ---------------- Cards & Content Panels ---------------- */
QFrame.KpiCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
}

QLabel.KpiValue {
    font-size: 26px;
    font-weight: bold;
    color: #0f172a;
}

QLabel.KpiLabel {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
}

/* ---------------- Tables ---------------- */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #f1f5f9;
    selection-background-color: #eff6ff;
    selection-color: #1d4ed8;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    font-weight: 600;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
}

/* ---------------- Inputs & Buttons ---------------- */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 22px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #2563eb;
    background-color: #ffffff;
}

QPushButton.PrimaryBtn {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
}

QPushButton.PrimaryBtn:hover {
    background-color: #1d4ed8;
}

QPushButton.SecondaryBtn {
    background-color: #f1f5f9;
    color: #334155;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 6px;
    border: 1px solid #cbd5e1;
}

QPushButton.SecondaryBtn:hover {
    background-color: #e2e8f0;
}

QPushButton.DangerBtn {
    background-color: #ef4444;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
}

QPushButton.DangerBtn:hover {
    background-color: #dc2626;
}

/* ---------------- Status Bar ---------------- */
QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #e2e8f0;
    color: #64748b;
    font-size: 11px;
}
"""
