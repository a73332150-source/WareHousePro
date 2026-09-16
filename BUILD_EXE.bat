@echo off
chcp 65001 > nul
cls
echo ====================================================================
echo     WareHousePro - Windows Standalone Executable (EXE) Builder
echo ====================================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in system PATH!
    echo Please install Python 3.10+ and check "Add Python to PATH".
    pause
    exit /b 1
)

echo [1/4] Checking and installing required dependencies...
python -m pip install --upgrade pip
python -m pip install PyQt5 pyinstaller

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install required packages.
    pause
    exit /b 1
)

echo.
echo [2/4] Verifying database integrity and Source files...
cd Source
python -c "import database, security, exceptions; db = database.DatabaseManager('test_check.db'); print('[OK] Core modules validated successfully.')"
if exist test_check.db del test_check.db

echo.
echo [3/4] Packaging Standalone Windows Executable (PyInstaller)...
echo Options: --onefile --windowed --clean --noconfirm
python build_exe.py

if %errorlevel% neq 0 (
    echo [ERROR] Packaging failed. See log output above.
    pause
    exit /b 1
)

echo.
echo [4/4] Verification Complete!
echo ====================================================================
echo [SUCCESS] Standalone EXE created successfully at:
echo    dist\WareHousePro.exe
echo.
echo You can now run WareHousePro.exe without needing Python installed!
echo ====================================================================
pause
