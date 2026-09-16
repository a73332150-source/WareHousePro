"""
WareHousePro - Application Branding & Asset Path Resolver
Supports seamless runtime resolution under both standard Python and PyInstaller frozen bundle.
"""
import sys
import os

APP_NAME = "WareHousePro"
APP_SUBTITLE = "نظام إدارة المستودعات والرقابة المخزنية المتكامل"
APP_VERSION = "2.5.0 Enterprise"
BUILD_ID = "2026.09.EXE-CERTIFIED"
COPYRIGHT = "© 2026 WareHousePro Technologies Inc. All Rights Reserved."

def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    PyInstaller creates a temp folder and stores path in _MEIPASS.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
