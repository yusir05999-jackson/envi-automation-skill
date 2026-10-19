# ENVI / IDL 排查手册

实测错误信息原文对照，按「症状 → 定位 → 修复」组织。

---

## A. 许可类

### `License expired` / 许可过期
```
License expires 01-Jan-2026.
```
许可已到期，需重新获取。GUI 可能仍能打开但任务执行失败。

### `由于 ENVI 安装目录没有写入权限，无法申请试用许可`
弹窗指向 `C:\Program Files\NV5`。ENVI 需要写该目录存许可文件。
- 用**管理员权限**运行
- 确认 `C:\Program Files\NV5` 可写

### `Failed to initialize IDL instance`
许可签出失败。检查 `IDL_LICENSE_PATH` 是否指向 `C:\Program Files\NV5\license`。

---

## B. 启动参数类

### `Error opening file: -q`
把 `-q` 当文件名了。**IDL 不接受这种短参数**。

### `Attempt to call undefined procedure: 'QUIT'`
`quit` 不是 IDL 命令。用 **`exit`**。

### `Attempt to call undefined procedure: 'IDL_FUNC'`
同名 `.pro` 未编译。stdin 里要先 `.compile 过程名`，等编译完再调用。

---

## C. 编译错误

### `Syntax error.`（位置在变量名或括号处，行内容看着完全正常）
**文件是 LF 换行**。IDL 需要 CRLF，LF 会导致行尾被截断。

```python
d = open(p,'rb').read()
open(p,'wb').write(d.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
```

### 路径含中文时 Syntax error
IDL 9.2 不支持非 ASCII 字符串字面量。
```python
# ❌ srcPath = 'D:\我的项目\影像数据\sub_quac.hdr'    ← 含中文，编译失败
# ✅ 拷到纯 ASCII 目录
shutil.copy2(src, r'E:\work\data\sub_quac.hdr')
```

### `% 6 Compilation error(s) in module XXX`
逐条看每个错误位置，常见是上一行结尾的问题（逗号、括号未闭合）。

---

## D. 运行时错误

### `Variable is undefined: ENVITASK`
**没先调 `ENVI()` 初始化**。
```idl
e = ENVI()                          ; ← 必须先这句
task = ENVITask('FXSegmentation')
```

### `Attempt to call undefined method: 'ENVI::NEWTASK'`
用了 5.6 的 API。6.2 已废弃，改用 `ENVITask('任务名')`。

### `Object reference type required in this context: FX`
上一行失败了导致变量为空。往上找第一个错误。

### `The output URI already exists`
ENVI 拒绝覆盖已有文件。
```idl
if file_search(seg) ne '' then file_delete, seg
```

### `PRINTF: File is not open for output. Unit: 0`
`/get_lun` 拿到的 unit 被释放后又用，或跨 `free_lun` 混用。
每个阶段独立 `openw` / `printf` / `free_lun`。

### `Metadata tag does not exist: NS` / `Unknown property: BANDS`
属性名猜错了。ENVIRaster 用 `Metadata['MAP INFO']` 等键值形式，
或查文档确认实际属性名。**不确定就干脆别读属性**。

### `Type conversion error: Unable to convert given STRING to Long`
参数类型不对（如把字符串传给数值参数）。

### `No parameter or property name matches PARAMETERNAMES`
ENVITask 的属性名不对。用官方文档，或只设确定存在的（如 `INPUT_RASTER` / `OUTPUT_RASTER_URI`）。

### `No method or function name: ENVITASK` + 日志刷同一条几百次
**任务在无界面模式下静默死循环**（已知：`BinaryLTThresholdRaster`）。
放弃该任务，改用 Python 读栅格算 + 对象级聚合（见 SKILL.md §7）。

---

## E. GUI / 截图

### PrintWindow 截图模糊
抓的是窗口 DIB（逻辑尺寸），放大后必然糊 + LANCZOS 伪影。
**改用 Win+Shift+S**（SKILL.md §5）。

### 鼠标点击位置全错
硬编码了屏幕尺寸。**用 `GetSystemMetrics(0/1)`** 动态取。
本机实测 `1600×1000`，若写死 3200×2000 所有坐标偏移一倍。

### PrintWindow 抓到 0×0 或内容错位
多显示器 + DPI 缩放场景。改用 Win+Shift+S 从屏幕合成器取图。

### 截图被其他窗口遮挡
先最小化遮挡窗口：
```python
other = find_window('WorkBuddy')
if other: u.ShowWindow(other[0], 6)   # SW_MINIMIZE
```

### PowerShell 保存剪贴板报 EMPTY
- 输出目录不存在 → 先 `os.makedirs`
- PowerShell 需 `-STA` 参数（单线程单元）
- 前一次 PowerShell 进程可能持有剪贴板 → 加 `-NoProfile`

### Python 读剪贴板 `GlobalSize` 返回 0
64 位下 `GlobalLock` 的返回被截断。**不要用 Python 读 CF_DIB**，
改用 PowerShell + `System.Windows.Forms.Clipboard::GetImage()`。

### Swing 下拉列表 PrintWindow 抓不到
Java Swing 的弹出层是独立渲染窗口，不在父窗口 DIB 里。
只能截屏（Win+Shift+S），或用键盘 Alt+↓ 展开后回车选择。

### SW_MAXIMIZE 对对话框无效
某些 Swing 对话框不接受最大化。改用鼠标拖边框，或改 ENVI 显示缩放设置。

---

## F. 文件操作

### `safe-delete ... Permission denied`
文件被占用。常见占用者：`editor_sdk` / `WINWORD` / `idl.exe`。
```bash
taskkill //F //IM idl.exe
taskkill //F //IM envi_idl.exe
taskkill //F //IM WINWORD
```
或输出到新文件名避开。

### 中文目录 mklink 失败
`mklink /J` 参数被 shell 解析错。改用 Python `os.path.exists` 判断后直接拷数据到 ASCII 路径。

---

## G. 环境探测清单

开工前先确认：

- [ ] ENVI 安装路径（`C:\Program Files\NV5\ENVI62\...` 或 `Harris\ENVI56\...`）
- [ ] IDL 版本与许可状态（跑个 hello world 看有没有许可报错）
- [ ] `IDL_LICENSE_PATH` 已设
- [ ] 屏幕分辨率（`GetSystemMetrics`）
- [ ] 是否有多个显示器 / DPI 缩放
- [ ] 数据路径是纯 ASCII
