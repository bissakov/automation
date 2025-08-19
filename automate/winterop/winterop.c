#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#include <winuser.h>

typedef struct {
  int left, top, right, bottom;
  int thickness;
  COLORREF color;
} OutlineParams;

LRESULT CALLBACK OutlineProc(HWND hwnd, UINT msg, WPARAM wParam,
                             LPARAM lParam) {
  switch (msg) {
  case WM_ERASEBKGND:
    return 1;
  case WM_PAINT: {
    PAINTSTRUCT ps;
    HDC hdc = BeginPaint(hwnd, &ps);

    OutlineParams *p = (OutlineParams *)GetWindowLongPtr(hwnd, GWLP_USERDATA);

    HBRUSH bg = CreateSolidBrush(RGB(0, 0, 0));
    FillRect(hdc, &ps.rcPaint, bg);
    DeleteObject(bg);

    HPEN pen = CreatePen(PS_SOLID, p->thickness, p->color);
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
    OutlineParams *p = (OutlineParams *)GetWindowLongPtr(hwnd, GWLP_USERDATA);
    if (p)
      free(p);
    PostQuitMessage(0);
    return 0;
  }
  }
  return DefWindowProc(hwnd, msg, wParam, lParam);
}

void outline(int left, int top, int right, int bottom, int thickness,
             COLORREF color, int duration_ms) {
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
      WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_TRANSPARENT, CLASS_NAME, L"",
      WS_POPUP, 0, 0, GetSystemMetrics(SM_CXSCREEN),
      GetSystemMetrics(SM_CYSCREEN), NULL, NULL, hInstance, NULL);
  if (!hwnd)
    return;

  OutlineParams *p = malloc(sizeof(OutlineParams));
  p->left = left;
  p->top = top;
  p->right = right;
  p->bottom = bottom;
  p->thickness = thickness;
  p->color = color;

  SetWindowLongPtr(hwnd, GWLP_USERDATA, (LONG_PTR)p);

  SetLayeredWindowAttributes(hwnd, RGB(0, 0, 0), 0, LWA_COLORKEY);
  ShowWindow(hwnd, SW_SHOW);

  InvalidateRect(hwnd, NULL, TRUE);

  SetTimer(hwnd, 1, duration_ms, NULL);

  MSG msg;
  while (GetMessage(&msg, NULL, 0, 0) > 0) {
    TranslateMessage(&msg);
    DispatchMessage(&msg);
  }
}

void fast_outline(int left, int top, int right, int bottom, int thickness,
                  COLORREF color) {
  HDC dc = GetDC(NULL);
  if (dc == NULL)
    return;

  HPEN pen = CreatePen(PS_SOLID, 2, RGB(0, 255, 0));
  if (pen == NULL)
    return;
  HGDIOBJ old_pen = SelectObject(dc, pen);
  if (old_pen == NULL)
    return;

  HGDIOBJ old_brush = SelectObject(dc, GetStockObject(NULL_BRUSH));
  if (old_brush == NULL)
    return;

  if (Rectangle(dc, left, top, right, bottom) == 0)
    return;

  SelectObject(dc, old_brush);
  SelectObject(dc, old_pen);

  if (DeleteObject(pen) == 0)
    return;
  if (ReleaseDC(NULL, dc) == 0)
    return;
}

static void fill_inputs_for_char(char ch, INPUT inputs[2]) {
  ZeroMemory(inputs, 2 * sizeof(INPUT));

  if (ch == '\n') {
    inputs[0].type = INPUT_KEYBOARD;
    inputs[0].ki.wVk = VK_RETURN;

    inputs[1].type = INPUT_KEYBOARD;
    inputs[1].ki.wVk = VK_RETURN;
    inputs[1].ki.dwFlags = KEYEVENTF_KEYUP;
  } else {
    inputs[0].type = INPUT_KEYBOARD;
    inputs[0].ki.wScan = ch;
    inputs[0].ki.dwFlags = KEYEVENTF_UNICODE;

    inputs[1].type = INPUT_KEYBOARD;
    inputs[1].ki.wScan = ch;
    inputs[1].ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP;
  }
}

int type_text(char *text, int delay_ms) {
  uint64_t text_size = strlen(text);

  if (delay_ms == 0) {
    INPUT *inputs = malloc(text_size * 2 * sizeof(INPUT));
    if (!inputs)
      return 1;

    for (size_t i = 0; i < text_size; i++) {
      fill_inputs_for_char(text[i], &inputs[i * 2]);
    }

    UINT sent = SendInput((UINT)(text_size * 2), inputs, sizeof(INPUT));
    free(inputs);
    return sent != text_size * 2;
  }

  for (size_t i = 0; i < text_size; i++) {
    INPUT inputs[2];
    fill_inputs_for_char(text[i], inputs);

    UINT sent = SendInput(2, inputs, sizeof(INPUT));
    if (sent != 2)
      return 1;
    Sleep(delay_ms);
  }

  return 0;
}

int click_mouse(int x, int y) {
  if (SetCursorPos(x, y) == 0)
    return 1;

  INPUT inputs[2];
  ZeroMemory(inputs, 2 * sizeof(INPUT));

  inputs[0].type = INPUT_MOUSE;
  inputs[0].mi.dx = x;
  inputs[0].mi.dy = y;
  inputs[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN;

  inputs[1].type = INPUT_MOUSE;
  inputs[1].mi.dx = x;
  inputs[1].mi.dy = y;
  inputs[1].mi.dwFlags = MOUSEEVENTF_LEFTUP;

  UINT sent = SendInput(2, inputs, sizeof(INPUT));
  if (sent != 2)
    return 1;

  return 0;
}
