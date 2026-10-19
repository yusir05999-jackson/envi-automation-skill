# -*- coding: utf-8 -*-
"""FX 面板自动化 —— 已修正屏幕坐标 (实际 1600x1000)"""
import ctypes
import time
from ctypes import wintypes
from PIL import Image
import os

u = ctypes.windll.user32
g = ctypes.windll.gdi32
EP = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

SW = u.GetSystemMetrics(0)   # 1600
SH = u.GetSystemMetrics(1)   # 1000
OUT = r'E:\work\shots'
os.makedirs(OUT, exist_ok=True)

_n = [0]


def find(title_kw):
    res = []

    def cb(h, l):
        if not u.IsWindowVisible(h):
            return True
        n = u.GetWindowTextLengthW(h)
        if n == 0:
            return True
        b = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(h, b, n + 1)
        r = wintypes.RECT()
        u.GetWindowRect(h, ctypes.byref(r))
        res.append((h, b.value, r.left, r.top,
                    r.right - r.left, r.bottom - r.top))
        return True

    u.EnumWindows(EP(cb), 0)
    for h, t, x, y, w, hh in res:
        if title_kw.lower() in t.lower() and w > 100 and hh > 80:
            return h, t, x, y, w, hh
    return None


def grab(hwnd, tag, scale=1.8):
    _n[0] += 1
    r = wintypes.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = u.GetWindowDC(hwnd)
    mdc = g.CreateCompatibleDC(hdc)
    bmp = g.CreateCompatibleBitmap(hdc, w, h)
    g.SelectObject(mdc, bmp)
    u.PrintWindow(hwnd, mdc, 2)

    class BIH(ctypes.Structure):
        _fields_ = [('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG),
                    ('biHeight', wintypes.LONG), ('biPlanes', wintypes.WORD),
                    ('biBitCount', wintypes.WORD),
                    ('biCompression', wintypes.DWORD),
                    ('biSizeImage', wintypes.DWORD),
                    ('biXPelsPerMeter', wintypes.LONG),
                    ('biYPelsPerMeter', wintypes.LONG),
                    ('biClrUsed', wintypes.DWORD),
                    ('biClrImportant', wintypes.DWORD)]

    bi = BIH()
    bi.biSize = ctypes.sizeof(BIH)
    bi.biWidth = w
    bi.biHeight = -h
    bi.biPlanes = 1
    bi.biBitCount = 32
    bi.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 4)
    g.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1).convert('RGB')
    if scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)),
                         Image.LANCZOS)
    p = os.path.join(OUT, f'{_n[0]:02d}_{tag}.png')
    img.save(p)
    g.DeleteObject(bmp)
    g.DeleteDC(mdc)
    u.ReleaseDC(hwnd, hdc)
    print(f'  [{_n[0]:02d}_{tag}.png] {img.size}')
    return p


ABS, MOVE, LD, LU = 0x8000, 0x0001, 0x0002, 0x0004


def click(hwnd, fx, fy, d=1.2):
    """按窗口内比例坐标点击 (fx, fy 为 0~1 相对位置)"""
    r = wintypes.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    x = r.left + int(fx * (r.right - r.left))
    y = r.top + int(fy * (r.bottom - r.top))
    u.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    u.mouse_event(MOVE | ABS, int(x * 65535 / SW), int(y * 65535 / SH), 0, 0)
    time.sleep(0.22)
    u.mouse_event(LD, 0, 0, 0, 0)
    time.sleep(0.09)
    u.mouse_event(LU, 0, 0, 0, 0)
    time.sleep(d)
    print(f'    click ({fx:.3f},{fy:.3f}) -> ({x},{y})')


def dclick(hwnd, fx, fy, d=1.2):
    r = wintypes.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    x = r.left + int(fx * (r.right - r.left))
    y = r.top + int(fy * (r.bottom - r.top))
    u.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    u.mouse_event(MOVE | ABS, int(x * 65535 / SW), int(y * 65535 / SH), 0, 0)
    time.sleep(0.22)
    for _ in range(2):
        u.mouse_event(LD, 0, 0, 0, 0)
        time.sleep(0.05)
        u.mouse_event(LU, 0, 0, 0, 0)
        time.sleep(0.08)
    time.sleep(d)


def click_abs(x, y, d=1.0):
    u.mouse_event(MOVE | ABS, int(x * 65535 / SW), int(y * 65535 / SH), 0, 0)
    time.sleep(0.22)
    u.mouse_event(LD, 0, 0, 0, 0)
    time.sleep(0.09)
    u.mouse_event(LU, 0, 0, 0, 0)
    time.sleep(d)
    print(f'    click abs ({x},{y})')
