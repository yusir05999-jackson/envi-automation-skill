# ENVI Automation Skill

> 自动化操作 ENVI / IDL 完成遥感影像处理任务 —— 面向 AI Agent 的实践指南

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

---

## 这是什么

一个 **Claude Code / Cursor / WorkBuddy 等 AI Agent 可直接加载的 Skill**，
把「用 ENVI 做遥感处理」这件事的踩坑全部固化下来。

作者在真实项目中（高分辨率影像城市地物提取）花了十余轮试错才跑通 ENVI 6.2，
把过程浓缩成这个 skill —— **下一个 Agent 装上它，不用再踩一遍。**

---

## 解决的核心问题

| 症状 | 真实原因 | 本 skill 的解法 |
|---|---|---|
| `idl.exe -e` 不执行 | 参数被当成文件名 | **stdin 管道**（唯一可靠方式） |
| `Variable is undefined: ENVITASK` | 没先初始化 | **必须先 `ENVI()`** |
| `undefined method: 'ENVI::NEWTASK'` | 用了 5.6 的 API | 6.2 改 `ENVITask('...')` |
| Syntax error（位置诡异） | 文件是 LF 换行 | **必须 CRLF** |
| 中文路径编译失败 | IDL 不支持非 ASCII | **路径全改纯 ASCII** |
| `quit` 挂起 | 不是 IDL 命令 | 用 **`exit`** |
| 界面截图很糊 | 抓窗口 DIB 再放大 | **Win+Shift+S 截物理像素** |
| 鼠标点击全偏移 | 硬编码屏幕尺寸 | **`GetSystemMetrics()`** |

---

## 安装

### 方式一：Claude Code / WorkBuddy

```bash
git clone https://github.com/yusir05999-jackson/envi-automation-skill.git \
  ~/.workbuddy/skills/envi-automation
```

### 方式二：手动

下载后把整个 `envi-automation/` 目录放到你的 skills 目录下：
- Claude Code: `~/.claude/skills/envi-automation/`
- WorkBuddy: `~/.workbuddy/skills/envi-automation/`
- Cursor: `.cursor/rules/`（取 `SKILL.md`）

---

## 快速上手

```python
import os, sys, time, subprocess

# 1) 定位 ENVI
import glob
IDL = None
for pat in [r'C:\Program Files\NV5\ENVI*\IDL*\bin\bin.x86_64\idl.exe',
            r'C:\Program Files\Harris\ENVI*\IDL*\bin\bin.x86_64\idl.exe']:
    hits = glob.glob(pat)
    if hits:
        IDL = hits[0]; break

# 2) 用 stdin 管道执行 IDL（不要用 -e）
env = dict(os.environ)
env['IDL_LICENSE_PATH'] = r'C:\Program Files\NV5\license'

p = subprocess.Popen([IDL], cwd=r'E:\work', stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
p.stdin.write(b'.compile my_task\n'); p.stdin.flush()
time.sleep(15)
p.stdin.write(b'my_task\n');     p.stdin.flush()
out, _ = p.communicate(timeout=3600)
print(out.decode('gbk', errors='ignore'))
```

**IDL 分割任务**（`example_pipeline.pro`）：

```idl
pro segment_task
  compile_opt idl2
  e = ENVI()                              ; ← 必须先初始化
  raster = e.OpenRaster('E:/work/data/sub_quac.hdr')

  task = ENVITask('FXSegmentation')
  task.INPUT_RASTER     = raster
  task.SEGMENT_ALGORITHM = 'Edge'
  task.SEGMENT_VALUE    = 50.0
  task.SEGMENT_BANDS    = [6L]
  task.MERGE_ALGORITHM  = 'Full Lambda Schedule'
  task.MERGE_VALUE      = 60.0
  task.KERNEL_SIZE      = 3.0
  task.OUTPUT_RASTER_URI = 'E:/work/seg.dat'

  task.Execute
  e.Close
end
```

**高清截图**：

```python
sys.path.insert(0, 'scripts')
from win_snip import snap
snap(0, 0, 1600, 1000, r'E:\work\shot.png')   # → 3200×2000 原生像素
```

---

## 目录结构

```
envi-automation/
├── SKILL.md                        主文档（速查表 + 完整指南 + 决策树）
├── README.md                       本文件
├── LICENSE                         MIT
├── references/
│   └── troubleshooting.md          错误信息原文对照手册
└── scripts/
    ├── win_snip.py                 Win+Shift+S 截图模块
    ├── gui_driver.py               窗口查找 / 点击 / 置顶
    └── example_pipeline.pro        IDL 分割任务模板
```

---

## SKILL.md 内容导航

| 章节 | 内容 |
|---|---|
| §0 | 三分钟速查表（8 个高频症状） |
| §1 | 环境探测（`find_envi()`，不靠猜路径） |
| §2 | stdin 管道执行 IDL（**唯一可靠方式**） |
| §3 | ENVI 6.2 API（5.6→6.2 变更对照、任务参数） |
| §4 | GUI 自动化（窗口查找、置顶、坐标换算） |
| §5 | Win+Shift+S 高清截图 |
| §6 | Python 读取 ENVI 栅格（含整数溢出坑） |
| §7 | 面向对象分类配方 |
| §8 | 遥感制图规范（四要素、字体、配色） |
| §9 | 已验证的完整案例 |
| §10 | 排查决策树 |

---

## 已验证案例：城市地物提取

| 环节 | 方法 | 结果 |
|---|---|---|
| 分割 | `FXSegmentation` Edge/50/FullLambda/60 | 182,127 对象 |
| 像元规则 | NDVI<0.28 且 NDSI<0.13 | 2.699 km² |
| 对象过滤 | 纯度>50% 且 ≥200 m² | 1,318 对象，0.965 km² |
| 精度 | 14 个人工判读 ROI | OA=0.7857, Kappa=0.3226 |

---

## 环境要求

- Windows 10/11
- ENVI 5.6 / 6.x（需有效许可）
- Python 3.8+
- `pip install pillow numpy scipy`

---

## 许可

MIT © YuShihao

**免责声明**：本项目仅提供技术方法，不包含任何 ENVI 商业软件或许可材料。
使用者需自行拥有合法 ENVI 许可，遵守 NV5 Geospatial 的许可条款。
