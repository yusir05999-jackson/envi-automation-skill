# -*- coding: utf-8 -*-
"""
Win+Shift+S 自动化截图 v2
用 PowerShell + System.Drawing 读取剪贴板 (更可靠)
流程: 模拟快捷键 -> 等覆盖层 -> 拖拽选区 -> 回车 -> PowerShell 落盘
"""
import ctypes
import time
import subprocess
import os
from ctypes import wintypes
from PIL import Image

u = ctypes.windll.user32

SW = u.GetSystemMetrics(0)
SH = u.GetSystemMetrics(1)
VK = {'LWIN': 0x5B, 'SHIFT': 0x10, 'S': 0x53, 'ENTER': 0x0D, 'ESC': 0x1B}
ABS, MOVE, LD, LU = 0x8000, 0x0001, 0x0002, 0x0004

# PowerShell: 剪贴板图像落盘
PS_SAVE = r'''
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$img = [System.Windows.Forms.Clipboard]::GetImage()
if ($img -eq $null) { Write-Output "EMPTY"; exit 1 }
$img.Save("{PATH}", [System.Drawing.Imaging.ImageFormat]::Png)
Write-Output ("OK " + $img.Width + "x" + $img.Height)
'''


def kd(vk, down=True):
    u.keybd_event(vk, 0, 0 if down else 2, 0)
    time.sleep(0.04)


def tap(vk):
    kd(vk, True); time.sleep(0.05); kd(vk, False); time.sleep(0.1)


def win_shift_s():
    kd(VK['LWIN']); kd(VK['SHIFT']); kd(VK['S'])
    kd(VK['S'], False); kd(VK['SHIFT'], False); kd(VK['LWIN'], False)


def move(x, y):
    u.mouse_event(MOVE | ABS, int(x * 65535 / SW), int(y * 65535 / SH), 0, 0)
    time.sleep(0.12)


def drag(x1, y1, x2, y2, steps=26):
    move(x1, y1)
    u.mouse_event(LD, 0, 0, 0, 0)
    time.sleep(0.18)
    for i in range(1, steps + 1):
        u.mouse_event(MOVE | ABS,
                      int((x1 + (x2 - x1) * i / steps) * 65535 / SW),
                      int((y1 + (y2 - y1) * i / steps) * 65535 / SH), 0, 0)
        time.sleep(0.022)
    time.sleep(0.2)
    u.mouse_event(LU, 0, 0, 0, 0)
    time.sleep(0.4)


def wait_ui(timeout=8):
    EP = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    t0 = time.time()
    while time.time() - t0 < timeout:
        hit = []

        def cb(h, l):
            if u.IsWindowVisible(h):
                n = u.GetWindowTextLengthW(h)
                if n:
                    b = ctypes.create_unicode_buffer(n + 1)
                    u.GetWindowTextW(h, b, n + 1)
                    if '截图工具覆盖' in b.value:
                        r = wintypes.RECT()
                        u.GetWindowRect(h, ctypes.byref(r))
                        hit.append((r.left, r.top,
                                    r.right - r.left, r.bottom - r.top))
            return True

        u.EnumWindows(EP(cb), 0)
        if hit:
            return hit[0]
        time.sleep(0.35)
    return None


def ps_save_clipboard(path):
    ps = PS_SAVE.replace('{PATH}', path.replace('\\', '\\\\'))
    r = subprocess.run(
        ['powershell', '-NoProfile', '-STA', '-Command', ps],
        capture_output=True, timeout=40)
    out = r.stdout.decode('utf-8', errors='ignore').strip()
    err = r.stderr.decode('utf-8', errors='ignore').strip()
    return out, err


def snap(x1, y1, x2, y2, path, tag=''):
    if os.path.exists(path):
        os.remove(path)
    print(f'[{tag}] Win+Shift+S')
    win_shift_s()
    time.sleep(1.3)

    ui = wait_ui(8)
    if not ui:
        print(f'[{tag}] UI 未出现')
        return None
    print(f'[{tag}] UI 就绪 {ui[2]}x{ui[3]}')

    print(f'[{tag}] 拖拽 ({x1},{y1})->({x2},{y2})')
    drag(x1, y1, x2, y2)
    time.sleep(0.9)

    print(f'[{tag}] 回车')
    tap(VK['ENTER'])
    time.sleep(2.0)

    print(f'[{tag}] 剪贴板落盘')
    out, err = ps_save_clipboard(path)
    print(f'[{tag}] PS: {out or err}')
    if os.path.exists(path):
        im = Image.open(path)
        print(f'[{tag}] OK {im.size}')
        return im.size
    return None


if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else r'E:/work/snip_test.png'
    box = [int(v) for v in sys.argv[2:6]] if len(sys.argv) >= 6 else \
          [300, 150, 1100, 750]
    snap(box[0], box[1], box[2], box[3], out, tag='t')
