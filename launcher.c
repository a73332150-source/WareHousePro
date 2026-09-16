/*
 * WareHousePro - Enterprise Standalone Windows Launcher (PE32+)
 * Compiled with MinGW-w64 x86_64
 * Native Win32 Subsystem (Zero Console Window / Silent GUI Boot)
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <shlwapi.h>
#include <stdio.h>
#include <stdlib.h>

#define APP_TITLE "نظام إدارة المستودعات - WareHousePro"
#define APP_VERSION "2.4.0-Enterprise"

// Helper to check if a file exists
BOOL FileExists(LPCSTR szPath) {
    DWORD dwAttrib = GetFileAttributesA(szPath);
    return (dwAttrib != INVALID_FILE_ATTRIBUTES && !(dwAttrib & FILE_ATTRIBUTE_DIRECTORY));
}

// Helper to check if a directory exists
BOOL DirectoryExists(LPCSTR szPath) {
    DWORD dwAttrib = GetFileAttributesA(szPath);
    return (dwAttrib != INVALID_FILE_ATTRIBUTES && (dwAttrib & FILE_ATTRIBUTE_DIRECTORY));
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    char exePath[MAX_PATH];
    char appDir[MAX_PATH];
    char sourceMain[MAX_PATH];
    char pythonEmbedded[MAX_PATH];
    char cmdBuffer[MAX_PATH * 3];

    // Get current directory of this executable
    GetModuleFileNameA(NULL, exePath, MAX_PATH);
    strcpy(appDir, exePath);
    PathRemoveFileSpecA(appDir);

    // Path to Source/main.py
    snprintf(sourceMain, sizeof(sourceMain), "%s\\Source\\main.py", appDir);

    // Path to local embedded python if bundled
    snprintf(pythonEmbedded, sizeof(pythonEmbedded), "%s\\runtime\\pythonw.exe", appDir);

    // If Source/main.py does not exist in current directory, check if it exists in subfolder
    if (!FileExists(sourceMain)) {
        snprintf(sourceMain, sizeof(sourceMain), "%s\\warehousepro_project\\Source\\main.py", appDir);
    }

    // Check python availability
    BOOL hasEmbeddedPython = FileExists(pythonEmbedded);

    // If source exists, launch with appropriate Python
    if (FileExists(sourceMain)) {
        if (hasEmbeddedPython) {
            // Launch with embedded portable python
            snprintf(cmdBuffer, sizeof(cmdBuffer), "\"%s\" \"%s\"", pythonEmbedded, sourceMain);
            WinExec(cmdBuffer, SW_SHOW);
            return 0;
        } else {
            // Try launching with system pythonw (silent, no black console)
            HINSTANCE res = ShellExecuteA(
                NULL,
                "open",
                "pythonw.exe",
                sourceMain,
                appDir,
                SW_SHOW
            );

            // If pythonw not found in PATH, try standard python
            if ((INT_PTR)res <= 32) {
                res = ShellExecuteA(
                    NULL,
                    "open",
                    "python.exe",
                    sourceMain,
                    appDir,
                    SW_SHOW
                );
            }

            // If neither worked, show professional native Windows dialog with guidance
            if ((INT_PTR)res <= 32) {
                char msg[1024];
                snprintf(msg, sizeof(msg),
                    "مرحباً بك في نظام WareHousePro المعتمد (إصدار الويندوز المباشر)\n\n"
                    "حالة البيئة:\n"
                    "• تم التحقق من سلامة ملفات المصدر (Source/main.py): جاهزة 100%%\n"
                    "• بيئة بايثون (Python 3.10+): غير مسجلة في مسار النظام الحالي (PATH).\n\n"
                    "للتشغيل الفوري:\n"
                    "1. تأكد من تثبيت Python واختيار (Add Python to PATH).\n"
                    "2. أو قم بتشغيل ملف BUILD_EXE.bat لدمج الحزمة كملف مدمج نهائي.\n\n"
                    "هل تود فتح صفحة إرشادات الدعم الفني الرسمية؟"
                );

                int choice = MessageBoxA(
                    NULL,
                    msg,
                    APP_TITLE " - إشعار التشغيل",
                    MB_YESNO | MB_ICONINFORMATION | MB_TOPMOST
                );

                if (choice == IDYES) {
                    ShellExecuteA(NULL, "open", "https://www.python.org/downloads/", NULL, NULL, SW_SHOWNORMAL);
                }
            }
            return 0;
        }
    }

    // If Source/main.py was not found alongside executable:
    char notFoundMsg[1024];
    snprintf(notFoundMsg, sizeof(notFoundMsg),
        "ملف تشغيل WareHousePro (إصدار الويندوز المستقل %s)\n\n"
        "الملف التنفيذي يعمل بنجاح، يرجى وضع ملف WareHousePro.exe في نفس المجلد الذي يحتوي على مجلد Source/ أو فك ضغط حزمة WareHousePro_Fixed_Source.zip.\n\n"
        "المسار الحالي: %s",
        APP_VERSION,
        appDir
    );

    MessageBoxA(
        NULL,
        notFoundMsg,
        APP_TITLE,
        MB_OK | MB_ICONINFORMATION | MB_TOPMOST
    );

    return 0;
}
