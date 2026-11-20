#pragma once
#include <windows.h>
#include <thumbcache.h>
#include <shobjidl.h>
#include <wrl/client.h>

// Generate your own unique GUIDs!
// Class ID (CLSID) for your provider
// {87654321-ABCD-EF01-2345-6789ABCDEF02}
extern const CLSID CLSID_PythonThumProvider;

class PythonThumbnailProvider : 
    public IThumbnailProvider, 
    public IInitializeWithFile
{
public:
    // IUnknown
    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv);
    IFACEMETHODIMP_(ULONG) AddRef();
    IFACEMETHODIMP_(ULONG) Release();

    // IInitializeWithFile
    IFACEMETHODIMP Initialize(LPCWSTR pszFilePath, DWORD grfMode);

    // IThumbnailProvider
    IFACEMETHODIMP GetThumbnail(UINT cx, HBITMAP* phbmp, WTS_ALPHATYPE* pdwAlpha);

    PythonThumbnailProvider();

private:
    ~PythonThumbnailProvider();

    long m_cRef;
    wchar_t m_szFilePath[MAX_PATH];
};