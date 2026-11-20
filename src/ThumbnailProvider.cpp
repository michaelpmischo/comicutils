#include "ThumbnailProvider.h"
#include <gdiplus.h>
#include <string>
#include <shlwapi.h>

#pragma comment(lib, "gdiplus.lib")
#pragma comment(lib, "shlwapi.lib")

extern long g_cDllRef; // Global DLL reference counter

PythonThumbnailProvider::PythonThumbnailProvider() : m_cRef(1), m_szFilePath() {
    InterlockedIncrement(&g_cDllRef);
}

PythonThumbnailProvider::~PythonThumbnailProvider() {
    InterlockedDecrement(&g_cDllRef);
}

// Standard COM Boilerplate IUnknown implementation
IFACEMETHODIMP PythonThumbnailProvider::QueryInterface(REFIID riid, void** ppv) {
    static const QITAB qit[] = {
        QITABENT(PythonThumbnailProvider, IThumbnailProvider),
        QITABENT(PythonThumbnailProvider, IInitializeWithFile),
        { 0 },
    };
    return QISearch(this, qit, riid, ppv);
}

IFACEMETHODIMP_(ULONG) PythonThumbnailProvider::AddRef() {
    return InterlockedIncrement(&m_cRef);
}

IFACEMETHODIMP_(ULONG) PythonThumbnailProvider::Release() {
    ULONG cRef = InterlockedDecrement(&m_cRef);
    if (cRef == 0) delete this;
    return cRef;
}

// Catch target file path from Explorer
IFACEMETHODIMP PythonThumbnailProvider::Initialize(LPCWSTR pszFilePath, DWORD grfMode) {
    wcscpy_s(m_szFilePath, pszFilePath);
    return S_OK;
}

// Core execution loop
IFACEMETHODIMP PythonThumbnailProvider::GetThumbnail(UINT cx, HBITMAP* phbmp, WTS_ALPHATYPE* pdwAlpha) {
    *phbmp = NULL;
    *pdwAlpha = WTSAT_UNKNOWN;

    // 1. Generate pathing details for execution tracking
    wchar_t szTempPath[MAX_PATH];
    wchar_t szTempFile[MAX_PATH];
    GetTempPathW(MAX_PATH, szTempPath);
    GetTempFileNameW(szTempPath, L"pyt", 0, szTempFile);
    
    // Change tmp file extension to flat target .png
    std::wstring pngTempFile = std::wstring(szTempFile) + L".png";

    // 2. Build explicit command line arguments for Python execution
    // "pythonw.exe" executes headless without command-prompt windows flashing open
    std::wstring cmdLine = L"pythonw.exe \"C:\\path\\to\\your\\generator.py\" \"" 
                           + std::wstring(m_szFilePath) + L"\" \"" 
                           + pngTempFile + L"\" " + std::to_wstring(cx);

    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi;
    
    // 3. Spawning Python child process
    if (CreateProcessW(NULL, &cmdLine[0], NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
        // Safe 2-second extraction timeout so Explorer never locks up
        DWORD waitResult = WaitForSingleObject(pi.hProcess, 2000);
        
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);

        if (waitResult == WAIT_OBJECT_0) {
            // Initialize GDI+ tracking framework
            Gdiplus::GdiplusStartupInput gdiplusStartupInput;
            ULONG_PTR gdiplusToken;
            Gdiplus::GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);

            {
                // Load intermediate layout back from Python execution output
                Gdiplus::Bitmap* bitmap = Gdiplus::Bitmap::FromFile(pngTempFile.c_str());
                if (bitmap && bitmap->GetLastStatus() == Gdiplus::Ok) {
                    // Convert GDI+ Bitmap structure directly to unmanaged Win32 HBITMAP
                    bitmap->GetHBITMAP(Gdiplus::Color(255, 255, 255), phbmp);
                    *pdwAlpha = WTSAT_ARGB; // Declare alpha transparency metadata
                }
                if (bitmap) delete bitmap;
            }

            Gdiplus::GdiplusShutdown(gdiplusToken);
        }
    }

    // Cleanup local IO Footprint
    DeleteFileW(szTempFile);
    DeleteFileW(pngTempFile.c_str());

    return (*phbmp != NULL) ? S_OK : E_FAIL;
}