# Watermark Studio（Windows / macOS）

一个用于给图片添加文本/图片水印的本地图形化工具，支持实时预览、拖拽导入、批量导出、命名规则、JPEG 质量调节与导出缩放等功能。

---

## 功能概览
- 导入：支持拖拽文件/文件夹、文件选择器，显示缩略图与文件名。
- 输入格式：JPEG、PNG（含透明通道）、BMP、TIFF。
- 输出格式：JPEG 或 PNG。
- 导出：默认禁止导出到原图所在文件夹；支持命名规则（保留原名 / 前缀 / 后缀）。
- JPEG 质量滑条（仅对 JPEG 生效）。
- 导出缩放：按宽 / 高 / 百分比缩放（可选）。
- 文本水印：内容、字体文件（.ttf/.otf）、字号、颜色（调色板）、透明度、描边、阴影。
- 图片水印：推荐 PNG（带透明），支持缩放与透明度。
- 布局：九宫格预设、在预览中自由拖拽、旋转。
- 模板：保存 / 加载 / 删除；程序启动自动加载上次设置。

---

## 快速开始（Windows 可执行文件）

- 下载源文件并直接运行：
  - `dist\WatermarkStudio\WatermarkStudio.exe`

- 可在本地构建（已支持 Python 3.13.7）：
  1) 确认本机 Python 位于 `D:\tool\Python\python.exe`（本项目的构建脚本会优先使用该路径），或在运行前设置环境变量 `PYTHON_EXE` 指向你的 `python.exe`。
  2) 在项目根目录（包含 `build-windows.cmd` 的文件夹）打开命令行（cmd.exe）。
  3) 执行构建脚本（自动创建虚拟环境、安装依赖并打包）：
     ```bat
     build-windows.cmd
     ```
  4) 构建成功后运行：
     ```bat
     dist\WatermarkStudio\WatermarkStudio.exe
     ```

提示：
- 构建脚本会优先使用 `D:\tool\Python\python.exe`；若不存在，则尝试 PATH 中的 Python 或 `py -3` 启动器。
- 依赖安装优先选择二进制轮子（wheels），尽量避免源码构建失败。
- 打包会自动收集 Pillow 与 PyQt5 需要的资源与插件。

---

## 使用方法（图形界面）

1) 导入图片
- 将图片文件或整个文件夹拖拽到左侧列表；或点击“添加图片”/“添加文件夹”。
- 支持一次选择多张图片；列表会显示缩略图与文件名。

2) 选择水印类型
- 在“水印类型”下拉中选择“文本水印”或“图片水印”。
- 文本水印：输入文本，可选择字体文件（.ttf/.otf）、字号、透明度、描边宽度与颜色、是否启用阴影与偏移等。
- 图片水印：选择一张本地图片（推荐 PNG，支持透明通道），可调节缩放比例与透明度。

3) 布局与预览
- 实时预览：右侧主预览会实时显示当前设置效果。
- 位置预设（九宫格）：四角、边中与中心，一键定位。
- 自由拖拽：在预览图上点击或拖拽，可将水印移动到任意位置。
- 旋转：通过“旋转”滑条调整角度。

4) 导出
- 请选择与原图不同的“输出文件夹”（默认禁止导出到原文件夹，以避免覆盖）。
- 命名规则：保留原名 / 添加前缀 / 添加后缀（可自定义前缀/后缀内容）。
- 输出格式：JPEG 或 PNG。
- JPEG 质量：仅对 JPEG 生效（0-100）。
- 导出缩放：可按宽度、按高度或按百分比缩放导出尺寸。

5) 模板
- 可将当前全部设置保存为模板，方便下次直接加载。
- 程序会自动保存上次使用的设置，并在启动时自动加载。

---

## 从源码运行（开发）

Windows（cmd.exe）：
```bat
D:\tool\Python\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m app.main
```


## 打包独立应用

Windows（.exe）：
```bat
build-windows.cmd
```
- 输出路径：`dist/WatermarkStudio/WatermarkStudio.exe`
- 分发方式：请打包整个 `dist/WatermarkStudio` 文件夹（EXE 必须与同目录文件一起使用）。


---

## 设置 / 模板存储位置
- Windows：`%APPDATA%\WatermarkStudio\templates.json`

---

## 常见问题排查（FAQ）

1) EXE 启动时报错 `attempted relative import with no known parent package`
- 已修复：入口文件 `app/main.py` 增加了多种导入回退策略（包/脚本/冻结），请删除 `build` 与 `dist` 后重新打包再试。

2) 依赖安装失败（如 `KeyError: '__version__'`、构建 wheel 失败）
- 本项目的 `requirements.txt` 仅包含与 Python 3.13 兼容并提供二进制轮子的版本；构建脚本优先使用 wheels。
- 若仍失败：删除 `.venv` 后重试；或将索引切换为官方 PyPI 源（镜像可能索引滞后）。

3) 报错 `ImageQt.ImageQt` 或预览/缩略图无法显示
- 已修复：`utils.py` 采用 QImage/QPixmap 直接转换，不依赖 ImageQt。

4) 出现 “此时不应有 Install。” 或 Microsoft Store Python 别名干扰
- 构建脚本会忽略 `WindowsApps` 下的 Python 别名，并优先使用 `D:\tool\Python\python.exe`。

5) 打包后运行界面空白 / 缺少 Qt 插件
- 构建脚本（及 .spec）会收集 PyQt5 模块与数据；若仍异常，删除 `build` 与 `dist` 后重打包。

---

## 环境与版本说明
- 已适配 Python 3.13.7。
- 构建脚本优先使用：`D:\tool\Python\python.exe`。
- 关键依赖（固定版本）：
  - Pillow 10.4.0
  - PyQt5 5.15.11
  - PyInstaller 6.16.0

如有其它问题，请附上完整命令行输出（特别是第一处 ERROR 开始的几行），我会进一步协助定位与修复。
