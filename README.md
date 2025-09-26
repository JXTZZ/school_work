# Watermark Studio（本地水印工具）

一个用于给图片添加文本/图片水印的本地图形化工具，支持实时预览、拖拽导入、批量导出、命名规则、JPEG 质量与导出缩放等功能。适用于 Windows（当前仓库已提供 Windows 打包脚本）。

---

## 功能概览
- 导入
  - 支持拖拽文件/文件夹，或通过文件选择器导入。
  - 支持批量导入，显示缩略图与文件名。
- 格式
  - 输入：JPEG、PNG（支持透明通道）、BMP、TIFF。
  - 输出：JPEG 或 PNG。
- 导出
  - 默认禁止导出到原图所在文件夹（防止覆盖原图）。
  - 支持命名规则：保留原名 / 前缀 / 后缀（可自定义）。
  - JPEG 质量滑条（0-100，仅对 JPEG 生效）。
  - 导出缩放：按宽 / 高 / 百分比缩放（可选）。
- 水印
  - 文本水印：内容、字体文件（.ttf/.otf）、字号、颜色、透明度、描边、阴影。
  - 图片水印：支持 PNG 透明、水印缩放与透明度。
- 布局与预览
  - 实时预览；点击列表切换预览目标。
  - 九宫格预设位置；在预览中用鼠标拖拽到任意位置。
  - 旋转角度可调。
- 模板
  - 可保存 / 加载 / 删除模板。
  - 程序启动自动加载上次关闭时的设置。

---

## 快速开始（Windows）

- 可执行文件位置（打包后）：
  - 项目根目录：`D:\SchoolWork\WatermarkStudio.exe`

- 直接运行
  - 双击 `WatermarkStudio.exe` 启动。
  - 默认“输出文件夹”为：`D:\SchoolWork\output`（可在界面修改）。

---

## 从源码运行（开发）

Windows（cmd.exe）：

```bat
D:\tool\Python\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m app.main
```

说明：
- 上述第一行可替换为你的 Python 路径；本项目已适配 Python 3.13.7。

---

## 打包生成 EXE（Windows）

在项目根目录（含 `build-windows.cmd`）执行：

```bat
build-windows.cmd
```

- 首次运行会自动创建虚拟环境 `.venv` 并安装依赖。
- 打包完成后，生成：`D:\SchoolWork\WatermarkStudio.exe`（单文件模式）。

如你的 Python 不在 `D:\tool\Python\python.exe`，可在执行脚本前设置环境变量：

```bat
set PYTHON_EXE=D:\你的\python.exe
build-windows.cmd
```

---

## 使用教程（图形界面）

1) 导入图片
- 点击“添加图片”/“添加文件夹”，或把图片/文件夹直接拖到左侧列表。
- 支持批量导入；列表显示缩略图与文件名。

2) 选择水印类型
- 在“水印类型”选择“文本水印”或“图片水印”。
- 文本水印：可设置文本、字体文件（.ttf/.otf）、字号、颜色、透明度、描边宽度与颜色、阴影与偏移。
- 图片水印：选择一张图片（推荐 PNG，支持透明），设置缩放与透明度。

3) 布局与预览
- 预览窗口实时显示效果。
- 位置预设：九宫格（四角、边中、中心）。
- 自由拖拽：在预览中左键按住拖动水印到任意位置。
- 旋转：通过“旋转”滑条调整角度。

4) 导出
- 请选择与原图不同的“输出文件夹”，默认建议为：`D:\SchoolWork\output`。
- 命名规则：保留原名 / 添加前缀 / 添加后缀（可自定义）。
- 输出格式：JPEG 或 PNG。
- JPEG 质量：0-100（仅 JPEG 生效）。
- 导出缩放：按宽/高/百分比缩放导出尺寸。
- 点击“导出选中”或“导出全部”。

5) 模板
- 可将当前设置保存为模板，方便下次直接使用。
- 程序自动保存“上次设置”，启动时自动加载。

---

## 默认输出目录

- 程序默认输出目录会自动定位到项目根目录下的 `output`：
  - `D:\SchoolWork\output`
- 如你加载了旧模板且其中仍是 `dist` 路径，程序会自动修正到根目录 `output`。

---

## 常见问题（FAQ）

1) 双击 EXE 报错 `attempted relative import with no known parent package`
- 已修复：入口 `app/main.py` 提供多种导入回退策略（包/脚本/冻结）。请删除 `build` 与旧的 `dist` 后重新打包。

2) 预览或缩略图转换报错 `ImageQt.ImageQt`
- 已修复：`app/utils.py` 改为使用 QImage/QPixmap 直接转换，不再依赖 `PIL.ImageQt`。

3) 构建时出现 “此时不应有 Install。” 或 Microsoft Store 的 Python 别名干扰
- 构建脚本会忽略 `WindowsApps` 下的别名，并优先使用 `D:\tool\Python\python.exe` 或你通过 `PYTHON_EXE` 指定的路径。

4) 依赖安装失败（如 `KeyError: '__version__'`、构建 wheel 失败）
- 已固定依赖版本并优先安装二进制 wheels。若仍失败，删除 `.venv` 目录后重试，或切换到官方 PyPI 源。

5) 打包后运行界面空白 / 缺少 Qt 插件
- 打包命令已收集 PyQt5 模块与数据；若仍异常，请清理 `build` 后重打包，并确保杀毒软件未干扰。

---

## 目录结构（简要）

- `app/` 源码目录
  - `main.py` 程序入口
  - `gui.py` 图形界面
  - `engine.py` 水印与导出核心逻辑
  - `exporter.py` 导出线程
  - `templates.py` 模板/配置读写
  - `utils.py` 图片与图像转换工具
- `output/` 默认导出目录（运行时自动创建）
- `build-windows.cmd` Windows 一键打包脚本（输出单文件 EXE 到项目根目录）
- `requirements.txt` 依赖版本

---

## 环境与版本

- 推荐 Python：3.13.7
- 关键依赖（固定版本，支持 Py3.13）：
  - Pillow 10.4.0
  - PyQt5 5.15.11
  - PyInstaller 6.16.0（用于打包）

如需 macOS 打包脚本或其它平台支持，请提出需求，我会补充对应脚本与说明。
