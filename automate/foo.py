from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING, cast

from cffi import FFI

if TYPE_CHECKING:
    from typing import Protocol

    class Winterop(Protocol):
        def outline(
            self, left: int, top: int, right: int, bottom: int, duration_ms: int
        ) -> None: ...


MODULE_NAME = "winterop"
CACHE_FILE = Path(__file__).with_name(f"{MODULE_NAME}.build")


def ensure_extension():
    # src = """
    # #include <windows.h>
    #
    # void outline(int left, int top, int right, int bottom) {
    #     HDC dc = GetDC(NULL);
    #     if (dc == NULL) return;
    #
    #     HPEN pen = CreatePen(PS_SOLID, 2, RGB(0,255,0));
    #     if (pen == NULL) return;
    #     HGDIOBJ old_pen = SelectObject(dc, pen);
    #     if (old_pen == NULL) return;
    #
    #     HGDIOBJ old_brush = SelectObject(dc, GetStockObject(NULL_BRUSH));
    #     if (old_brush == NULL) return;
    #
    #     if (Rectangle(dc, left, top, right, bottom) == 0) return;
    #
    #     SelectObject(dc, old_brush);
    #     SelectObject(dc, old_pen);
    #
    #     DeleteObject(pen);
    #     ReleaseDC(NULL, dc);
    # }
    # """

    src = """
    #include <windows.h>
    #include <stdlib.h>

    typedef struct {
        int left, top, right, bottom;
    } OutlineParams;

    LRESULT CALLBACK OutlineProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
        switch (msg) {
            case WM_ERASEBKGND:
                return 1;
            case WM_PAINT: {
                PAINTSTRUCT ps;
                HDC hdc = BeginPaint(hwnd, &ps);

                OutlineParams *p = (OutlineParams*)GetWindowLongPtr(hwnd, GWLP_USERDATA);

                HBRUSH bg = CreateSolidBrush(RGB(0,0,0));
                FillRect(hdc, &ps.rcPaint, bg);
                DeleteObject(bg);

                HPEN pen = CreatePen(PS_SOLID, 3, RGB(0, 255, 0));
                HGDIOBJ old_pen = SelectObject(hdc, pen);
                HGDIOBJ old_brush = SelectObject(hdc, GetStockObject(NULL_BRUSH));

                Rectangle(hdc, p->left, p->top, p->right, p->bottom);

                SelectObject(hdc, old_brush);
                SelectObject(hdc, old_pen);
                DeleteObject(pen);

                EndPaint(hwnd, &ps);
                return 0;
            }
            case WM_TIMER:
                KillTimer(hwnd, 1);
                PostMessage(hwnd, WM_CLOSE, 0, 0);
                return 0;
            case WM_DESTROY: {
                OutlineParams *p = (OutlineParams*)GetWindowLongPtr(hwnd, GWLP_USERDATA);
                if (p) free(p);
                PostQuitMessage(0);
                return 0;
            }
        }
        return DefWindowProc(hwnd, msg, wParam, lParam);
    }

    __declspec(dllexport)
    void outline(int left, int top, int right, int bottom, int duration_ms) {
        HINSTANCE hInstance = GetModuleHandle(NULL);

        const wchar_t CLASS_NAME[] = L"OutlineOverlay";
        static int registered = 0;
        if (!registered) {
            WNDCLASSW wc = {0};
            wc.lpfnWndProc = OutlineProc;
            wc.hInstance = hInstance;
            wc.lpszClassName = CLASS_NAME;
            wc.hbrBackground = NULL;
            RegisterClassW(&wc);
            registered = 1;
        }

        HWND hwnd = CreateWindowExW(
            WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_TRANSPARENT,
            CLASS_NAME,
            L"",
            WS_POPUP,
            0, 0,
            GetSystemMetrics(SM_CXSCREEN),
            GetSystemMetrics(SM_CYSCREEN),
            NULL, NULL, hInstance, NULL
        );
        if (!hwnd) return;

        OutlineParams *p = malloc(sizeof(OutlineParams));
        p->left = left;
        p->top = top;
        p->right = right;
        p->bottom = bottom;

        SetWindowLongPtr(hwnd, GWLP_USERDATA, (LONG_PTR)p);

        SetLayeredWindowAttributes(hwnd, RGB(0,0,0), 0, LWA_COLORKEY); 
        ShowWindow(hwnd, SW_SHOW);

        InvalidateRect(hwnd, NULL, TRUE);

        SetTimer(hwnd, 1, duration_ms, NULL);

        MSG msg;
        while (GetMessage(&msg, NULL, 0, 0) > 0) {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
    }
    """
    src_hash = hashlib.sha256(src.encode()).hexdigest()

    if importlib.util.find_spec(MODULE_NAME) and CACHE_FILE.exists():
        if CACHE_FILE.read_text() == src_hash:
            return

    print("Compiling CFFI extension...")
    ffi = FFI()
    ffi.cdef("""
        void outline(int left, int top, int right, int bottom, int duration_ms);
    """)
    ffi.set_source(
        MODULE_NAME,
        src,
        libraries=["user32", "gdi32", "kernel32"],
    )
    ffi.compile(verbose=True)

    CACHE_FILE.write_text(src_hash)


ensure_extension()

import winterop

lib = cast("Winterop", winterop.lib)

lib.outline(100, 1000, 1000, 100, 5000)

# for i in range(100):
#     print(lib.outline(100, 1000, 1000, 100, 1000))
