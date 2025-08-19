typedef unsigned long COLORREF;

void outline(int left, int top, int right, int bottom, int thickness,
             COLORREF color, int duration_ms);
void fast_outline(int left, int top, int right, int bottom, int thickness,
                  COLORREF color);
int type_text(char *text, int delay_ms);
int click_mouse(int x, int y);
