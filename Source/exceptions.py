"""
WareHousePro - Centralized Exception Hierarchy & Crash Recovery
Translates database and runtime faults into user-friendly localized messages.
"""
import sys
import os
import traceback
import logging

logger = logging.getLogger("WareHousePro.Exceptions")

class WareHouseProException(Exception):
    """Base exception class for all WareHousePro runtime faults."""
    def __init__(self, message_ar: str, technical_details: str = ""):
        super().__init__(message_ar)
        self.message_ar = message_ar
        self.technical_details = technical_details

class DatabaseError(WareHouseProException):
    """Raised for connection faults, SQL syntax or execution failures."""
    pass

class DatabaseIntegrityError(DatabaseError):
    """Raised when foreign keys or unique constraints are breached."""
    pass

class InsufficientStockError(WareHouseProException):
    """Raised when outbound stock exceeds current on-hand inventory."""
    pass

class RecordNotFoundError(WareHouseProException):
    """Raised when querying a non-existent entity."""
    pass

class AuthenticationError(WareHouseProException):
    """Raised during failed login attempts."""
    pass

class PermissionDeniedError(WareHouseProException):
    """Raised when an action exceeds user role authorization."""
    pass

class ValidationError(WareHouseProException):
    """Raised when user input violates validation boundaries."""
    pass

def setup_global_exception_handler():
    """
    Installs a resilient sys.excepthook that intercepts uncaught exceptions,
    writes a structured crash log, and prevents silent UI termination.
    """
    def excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        crash_report = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.critical(f"UNHANDLED EXCEPTION CAUGHT:\n{crash_report}")

        try:
            with open("warehousepro_crash.log", "a", encoding="utf-8") as f:
                import datetime
                f.write(f"\n[{datetime.datetime.now().isoformat()}] CRITICAL RUNTIME FAULT:\n")
                f.write(crash_report)
                f.write("-" * 80 + "\n")
        except Exception as file_err:
            print(f"Failed to append to crash log: {file_err}")

        # If Qt is active, attempt to display a modal dialog
        try:
            from PyQt5.QtWidgets import QMessageBox, QApplication
            if QApplication.instance():
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("خطأ غير متوقع في النظام")
                msg_box.setText("حدث خطأ تقني غير متوقع. تم حفظ تقرير الخطأ بأمان دون فقدان البيانات.")
                msg_box.setDetailedText(crash_report)
                msg_box.exec_()
        except ImportError:
            pass

    sys.excepthook = excepthook
