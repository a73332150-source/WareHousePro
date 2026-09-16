"""
WareHousePro - PyInstaller Automated Packaging Script
Builds a standalone, windowed Windows executable with assets and zero console flicker.
"""
import os
import sys
import shutil
import subprocess

def run_build():
    print("=" * 65)
    print("      WareHousePro Windows Executable Builder (PyInstaller)     ")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(base_dir, "main.py")
    dist_dir = os.path.join(base_dir, "..", "dist")
    build_dir = os.path.join(base_dir, "..", "build")

    if not os.path.exists(main_script):
        print(f"[ERROR] Main script not found at: {main_script}")
        sys.exit(1)

    # PyInstaller arguments
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",              # Standalone single file executable
        "--windowed",             # Hide the black console window
        "--name", "WareHousePro", # Output: WareHousePro.exe
        "--hidden-import", "PyQt5.sip",
        "--hidden-import", "PyQt5.QtCore",
        "--hidden-import", "PyQt5.QtGui",
        "--hidden-import", "PyQt5.QtWidgets",
        "--distpath", dist_dir,
        "--workpath", build_dir,
        f"--add-data={base_dir}{os.pathsep}Source",
        main_script
    ]

    print(f"[INFO] Executing PyInstaller command:")
    print(" ".join(pyinstaller_args))
    print("-" * 65)

    try:
        res = subprocess.run(pyinstaller_args, check=True)
        print("=" * 65)
        print("[SUCCESS] Build completed successfully!")
        print(f"[OUTPUT] Standalone executable generated at: {dist_dir}/WareHousePro.exe")
        print("=" * 65)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    run_build()
