import os
from typing import List, Optional
from PIL import Image
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QFileDialog, QListWidget, QListWidgetItem,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter, QGroupBox, QLineEdit,
    QSpinBox, QSlider, QColorDialog, QComboBox, QCheckBox, QMessageBox, QStylePainter, QStyleOption, QStyle
)

from .utils import is_image_file, make_thumbnail, qpixmap_from_pil
from .engine import (
    WatermarkSettings, ExportSettings, TextStyle, ImageStyle,
    apply_watermark
)
from .exporter import ExportWorker
from . import templates as tmpl


class ImageListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setIconSize(QSize(80, 80))
        self.setAcceptDrops(True)
        self.setSelectionMode(self.ExtendedSelection)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            paths = []
            for url in e.mimeData().urls():
                p = url.toLocalFile()
                if os.path.isdir(p):
                    for root, _, files in os.walk(p):
                        for f in files:
                            full = os.path.join(root, f)
                            if is_image_file(full):
                                paths.append(full)
                else:
                    if is_image_file(p):
                        paths.append(p)
            wnd = self.window()
            if hasattr(wnd, 'add_images'):
                wnd.add_images(paths)  # type: ignore[attr-defined]
            e.acceptProposedAction()
        else:
            super().dropEvent(e)


class PreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_path: Optional[str] = None
        self.pixmap: Optional[QPixmap] = None
        self.wm_settings: Optional[WatermarkSettings] = None
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self._dragging = False

    def set_watermark_settings(self, wm: WatermarkSettings):
        self.wm_settings = wm

    def set_image_path(self, path: Optional[str]):
        self.current_path = path
        self.update_preview()

    def update_preview(self):
        if not self.current_path:
            self.pixmap = None
            self.update()
            return
        try:
            with Image.open(self.current_path) as im:
                im = im.convert("RGBA")
                if self.wm_settings:
                    im = apply_watermark(im, self.wm_settings)
                self.pixmap = qpixmap_from_pil(im)
        except Exception:
            self.pixmap = None
        self.update()

    def _norm_from_event(self, event) -> Optional[tuple]:
        if not self.pixmap:
            return None
        w, h = self.width(), self.height()
        pm_w, pm_h = self.pixmap.width(), self.pixmap.height()
        scale = min(w / pm_w, h / pm_h)
        disp_w, disp_h = int(pm_w * scale), int(pm_h * scale)
        off_x, off_y = (w - disp_w) // 2, (h - disp_h) // 2
        x = event.x() - off_x
        y = event.y() - off_y
        if 0 <= x <= disp_w and 0 <= y <= disp_h:
            nx = max(0.0, min(1.0, x / disp_w))
            ny = max(0.0, min(1.0, y / disp_h))
            return (nx, ny)
        return None

    def mousePressEvent(self, event):
        if not self.pixmap or not self.wm_settings:
            return
        if event.button() == Qt.LeftButton:
            norm = self._norm_from_event(event)
            if norm:
                self.wm_settings.free_pos_norm = norm
                self._dragging = True
                self.update_preview()

    def mouseMoveEvent(self, event):
        if self._dragging and self.wm_settings and self.pixmap:
            norm = self._norm_from_event(event)
            if norm:
                self.wm_settings.free_pos_norm = norm
                self.update_preview()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False

    def paintEvent(self, e):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QStylePainter(self)
        p.drawPrimitive(QStyle.PE_Widget, opt)
        p.end()

        if not self.pixmap:
            return
        painter = QStylePainter(self)
        w, h = self.width(), self.height()
        pm_w, pm_h = self.pixmap.width(), self.pixmap.height()
        scale = min(w / pm_w, h / pm_h)
        disp_w, disp_h = int(pm_w * scale), int(pm_h * scale)
        x, y = (w - disp_w) // 2, (h - disp_h) // 2
        painter.drawPixmap(x, y, self.pixmap.scaled(disp_w, disp_h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        painter.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Watermark Studio")
        self.resize(1200, 800)
        self.files: List[str] = []

        # 计算默认输出目录：优先固定为工程根目录的 output
        def _default_output_dir() -> str:
            try:
                import sys
                from pathlib import Path
                if getattr(sys, 'frozen', False):
                    exe_path = Path(sys.executable).resolve()
                    # 兼容两种布局：
                    # 1) 老布局: dist/WatermarkStudio/WatermarkStudio.exe -> 上跳三级到工程根
                    # 2) 新布局: 工程根/WatermarkStudio.exe -> 直接使用父目录作为根
                    parent = exe_path.parent
                    if parent.name.lower() == 'watermarkstudio' and parent.parent.name.lower() == 'dist':
                        root = parent.parent.parent
                    else:
                        root = parent
                else:
                    # 源码运行：当前文件 app/gui.py，上两级到达工程根目录
                    root = Path(__file__).resolve().parent.parent
                return str((root / "output").resolve())
            except Exception:
                # 回退：使用当前工作目录
                return os.path.join(os.getcwd(), "output")

        # State
        self.wm = WatermarkSettings()
        self.exp = ExportSettings(output_dir=_default_output_dir())

        # UI
        self.list_widget = ImageListWidget()
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.preview = PreviewWidget()
        self.preview.set_watermark_settings(self.wm)

        # Debounced preview update
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(150)
        self._debounce.timeout.connect(self.preview.update_preview)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        btns = QHBoxLayout()
        self.btn_add_files = QPushButton("添加图片")
        self.btn_add_folder = QPushButton("添加文件夹")
        self.btn_remove = QPushButton("移除选中")
        self.btn_clear = QPushButton("清空")
        for b in (self.btn_add_files, self.btn_add_folder, self.btn_remove, self.btn_clear):
            btns.addWidget(b)
        left_layout.addLayout(btns)
        left_layout.addWidget(self.list_widget)

        self.btn_add_files.clicked.connect(self.add_files_dialog)
        self.btn_add_folder.clicked.connect(self.add_folder_dialog)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear.clicked.connect(self.clear_list)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self.preview)
        right_layout.addWidget(self._build_controls())

        sp = QSplitter()
        sp.addWidget(left)
        sp.addWidget(right)
        sp.setStretchFactor(1, 1)
        self.setCentralWidget(sp)

        # Load last template if exists
        last = tmpl.load_last()
        if last:
            self.wm, self.exp = last
            # 若上次保存的输出目录位于 dist 文件夹内或与 EXE 布局不一致，自动重写到工程根目录 output
            try:
                from pathlib import Path
                import sys as _sys
                outp = Path(self.exp.output_dir).resolve()
                needs_rewrite = "dist" in [p.name.lower() for p in outp.parts]
                if getattr(_sys, 'frozen', False):
                    exe_path = Path(_sys.executable).resolve()
                    parent = exe_path.parent
                    if parent.name.lower() == 'watermarkstudio' and parent.parent.name.lower() == 'dist':
                        expected_root = parent.parent.parent
                    else:
                        expected_root = parent
                    expected_out = (expected_root / 'output').resolve()
                    if outp != expected_out:
                        needs_rewrite = True
                if needs_rewrite:
                    def _default_output_dir_inner() -> str:
                        import sys as __sys
                        from pathlib import Path as __Path
                        if getattr(__sys, 'frozen', False):
                            exe_path = __Path(__sys.executable).resolve()
                            parent = exe_path.parent
                            if parent.name.lower() == 'watermarkstudio' and parent.parent.name.lower() == 'dist':
                                root = parent.parent.parent
                            else:
                                root = parent
                        else:
                            root = __Path(__file__).resolve().parent.parent
                        return str((root / "output").resolve())
                    self.exp.output_dir = _default_output_dir_inner()
            except Exception:
                pass
            self.preview.set_watermark_settings(self.wm)
            self._apply_state_to_ui()

    # ========== List management ==========
    def add_images(self, paths: List[str]):
        added = 0
        for p in paths:
            if not is_image_file(p):
                continue
            if p in self.files:
                continue
            self.files.append(p)
            thumb = make_thumbnail(p)
            icon = QIcon(qpixmap_from_pil(thumb)) if thumb else QIcon()
            item = QListWidgetItem(icon, os.path.basename(p))
            item.setToolTip(p)
            self.list_widget.addItem(item)
            added += 1
        if added and not self.list_widget.currentItem():
            self.list_widget.setCurrentRow(0)
        self.statusBar().showMessage(f"已添加 {added} 个文件，总计 {len(self.files)}")

    def add_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "Images (*.jpg *.jpeg *.png *.bmp *.tif *.tiff)")
        self.add_images(files)

    def add_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not folder:
            return
        paths = []
        for root, _, fs in os.walk(folder):
            for f in fs:
                full = os.path.join(root, f)
                if is_image_file(full):
                    paths.append(full)
        self.add_images(paths)

    def remove_selected(self):
        rows = sorted([self.list_widget.row(i) for i in self.list_widget.selectedItems()], reverse=True)
        for r in rows:
            del self.files[r]
            self.list_widget.takeItem(r)
        self.on_selection_changed()

    def clear_list(self):
        self.files.clear()
        self.list_widget.clear()
        self.preview.set_image_path(None)

    def on_selection_changed(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.files):
            self.preview.set_image_path(self.files[row])
        else:
            self.preview.set_image_path(None)

    # ========== Controls ==========
    def _build_controls(self) -> QWidget:
        box = QGroupBox("设置")
        layout = QVBoxLayout(box)

        # Mode
        mode_row = QHBoxLayout()
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["文本水印", "图片水印"])
        self.cmb_mode.currentIndexChanged.connect(self.on_mode_changed)
        mode_row.addWidget(QLabel("水印类型:"))
        mode_row.addWidget(self.cmb_mode)
        layout.addLayout(mode_row)

        # Text controls
        self.grp_text = QGroupBox("文本水印")
        tl = QVBoxLayout(self.grp_text)
        row1 = QHBoxLayout()
        self.ed_text = QLineEdit(self.wm.text)
        row1.addWidget(QLabel("内容:"))
        row1.addWidget(self.ed_text)
        tl.addLayout(row1)

        row_font = QHBoxLayout()
        self.ed_font = QLineEdit(self.wm.text_style.font_path or "")
        self.btn_font = QPushButton("选择字体文件(.ttf/.otf)")
        self.btn_font.clicked.connect(self.choose_font)
        row_font.addWidget(QLabel("字体文件:"))
        row_font.addWidget(self.ed_font)
        row_font.addWidget(self.btn_font)
        tl.addLayout(row_font)

        row_size = QHBoxLayout()
        self.sp_font_size = QSpinBox(); self.sp_font_size.setRange(6, 400); self.sp_font_size.setValue(self.wm.text_style.font_size)
        row_size.addWidget(QLabel("字号:"))
        row_size.addWidget(self.sp_font_size)
        tl.addLayout(row_size)

        row_color = QHBoxLayout()
        self.btn_color = QPushButton("选择颜色")
        self.btn_color.clicked.connect(self.choose_color)
        self.sld_opacity = QSlider(Qt.Horizontal); self.sld_opacity.setRange(0, 100); self.sld_opacity.setValue(self.wm.text_style.opacity)
        row_color.addWidget(QLabel("颜色:"))
        row_color.addWidget(self.btn_color)
        row_color.addWidget(QLabel("透明度:"))
        row_color.addWidget(self.sld_opacity)
        tl.addLayout(row_color)

        row_stroke = QHBoxLayout()
        self.sp_stroke = QSpinBox(); self.sp_stroke.setRange(0, 20); self.sp_stroke.setValue(self.wm.text_style.stroke_width)
        self.btn_stroke_color = QPushButton("描边颜色")
        self.btn_stroke_color.clicked.connect(self.choose_stroke_color)
        row_stroke.addWidget(QLabel("描边宽度:"))
        row_stroke.addWidget(self.sp_stroke)
        row_stroke.addWidget(self.btn_stroke_color)
        tl.addLayout(row_stroke)

        row_shadow = QHBoxLayout()
        self.chk_shadow = QCheckBox("阴影"); self.chk_shadow.setChecked(self.wm.text_style.shadow)
        self.sp_shadow_x = QSpinBox(); self.sp_shadow_x.setRange(-50, 50); self.sp_shadow_x.setValue(self.wm.text_style.shadow_offset[0])
        self.sp_shadow_y = QSpinBox(); self.sp_shadow_y.setRange(-50, 50); self.sp_shadow_y.setValue(self.wm.text_style.shadow_offset[1])
        row_shadow.addWidget(self.chk_shadow)
        row_shadow.addWidget(QLabel("偏移X")); row_shadow.addWidget(self.sp_shadow_x)
        row_shadow.addWidget(QLabel("偏移Y")); row_shadow.addWidget(self.sp_shadow_y)
        tl.addLayout(row_shadow)

        # Image watermark controls
        self.grp_image = QGroupBox("图片水印")
        il = QVBoxLayout(self.grp_image)
        row_ip = QHBoxLayout()
        self.ed_img_wm = QLineEdit(self.wm.image_style.path or "")
        self.btn_img_wm = QPushButton("选择图片")
        self.btn_img_wm.clicked.connect(self.choose_wm_image)
        row_ip.addWidget(QLabel("水印图片:"))
        row_ip.addWidget(self.ed_img_wm)
        row_ip.addWidget(self.btn_img_wm)
        il.addLayout(row_ip)
        row_scale = QHBoxLayout()
        self.sld_scale = QSlider(Qt.Horizontal); self.sld_scale.setRange(1, 500); self.sld_scale.setValue(int(self.wm.image_style.scale * 100))
        self.sld_img_opacity = QSlider(Qt.Horizontal); self.sld_img_opacity.setRange(0, 100); self.sld_img_opacity.setValue(self.wm.image_style.opacity)
        row_scale.addWidget(QLabel("缩放(% of min边):")); row_scale.addWidget(self.sld_scale)
        row_scale.addWidget(QLabel("透明度:")); row_scale.addWidget(self.sld_img_opacity)
        il.addLayout(row_scale)

        # Position and rotation
        grp_pos = QGroupBox("位置与旋转")
        pl = QHBoxLayout(grp_pos)
        self.cmb_pos = QComboBox()
        self.cmb_pos.addItems(["top-left","top-center","top-right","middle-left","center","middle-right","bottom-left","bottom-center","bottom-right"])
        self.cmb_pos.setCurrentText(self.wm.position)
        self.sp_rot = QSlider(Qt.Horizontal); self.sp_rot.setRange(-180, 180); self.sp_rot.setValue(int(self.wm.rotation))
        self.sp_off_x = QSpinBox(); self.sp_off_x.setRange(0, 200); self.sp_off_x.setValue(self.wm.offset[0])
        self.sp_off_y = QSpinBox(); self.sp_off_y.setRange(0, 200); self.sp_off_y.setValue(self.wm.offset[1])
        self.btn_use_preset = QPushButton("使用预设(取消拖拽位置)")
        self.btn_use_preset.clicked.connect(self.clear_free_pos)

        pl.addWidget(QLabel("九宫格:"))
        pl.addWidget(self.cmb_pos)
        pl.addWidget(QLabel("旋转:"))
        pl.addWidget(self.sp_rot)
        pl.addWidget(QLabel("边距X:")); pl.addWidget(self.sp_off_x)
        pl.addWidget(QLabel("边距Y:")); pl.addWidget(self.sp_off_y)
        pl.addWidget(self.btn_use_preset)

        # Export group
        grp_exp = QGroupBox("导出")
        el = QVBoxLayout(grp_exp)
        row_out = QHBoxLayout()
        self.ed_out = QLineEdit(self.exp.output_dir)
        self.btn_out = QPushButton("选择输出文件夹")
        self.btn_out.clicked.connect(self.choose_output_dir)
        row_out.addWidget(QLabel("输出文件夹:"))
        row_out.addWidget(self.ed_out)
        row_out.addWidget(self.btn_out)
        el.addLayout(row_out)

        row_fmt = QHBoxLayout()
        self.cmb_fmt = QComboBox(); self.cmb_fmt.addItems(["JPEG", "PNG"])
        self.cmb_fmt.setCurrentText(self.exp.out_format)
        self.sld_quality = QSlider(Qt.Horizontal); self.sld_quality.setRange(0, 100); self.sld_quality.setValue(self.exp.jpeg_quality)
        row_fmt.addWidget(QLabel("格式:")); row_fmt.addWidget(self.cmb_fmt)
        row_fmt.addWidget(QLabel("JPEG质量:")); row_fmt.addWidget(self.sld_quality)
        el.addLayout(row_fmt)

        row_name = QHBoxLayout()
        self.cmb_name_mode = QComboBox(); self.cmb_name_mode.addItems(["keep","prefix","suffix"]); self.cmb_name_mode.setCurrentText(self.exp.naming_mode)
        self.ed_prefix = QLineEdit(self.exp.prefix)
        self.ed_suffix = QLineEdit(self.exp.suffix)
        row_name.addWidget(QLabel("命名规则:")); row_name.addWidget(self.cmb_name_mode)
        row_name.addWidget(QLabel("前缀:")); row_name.addWidget(self.ed_prefix)
        row_name.addWidget(QLabel("后缀:")); row_name.addWidget(self.ed_suffix)
        el.addLayout(row_name)

        row_resize = QHBoxLayout()
        self.cmb_resize = QComboBox(); self.cmb_resize.addItems(["none","width","height","percent"]); self.cmb_resize.setCurrentText(self.exp.resize_mode)
        self.sp_resize = QSpinBox(); self.sp_resize.setRange(0, 10000); self.sp_resize.setValue(self.exp.resize_value)
        row_resize.addWidget(QLabel("缩放方式:")); row_resize.addWidget(self.cmb_resize)
        row_resize.addWidget(QLabel("数值:")); row_resize.addWidget(self.sp_resize)
        el.addLayout(row_resize)

        row_btns = QHBoxLayout()
        self.btn_export_sel = QPushButton("导出选中")
        self.btn_export_all = QPushButton("导出全部")
        row_btns.addWidget(self.btn_export_sel)
        row_btns.addWidget(self.btn_export_all)
        el.addLayout(row_btns)

        # Templates
        grp_tpl = QGroupBox("模板")
        tl2 = QHBoxLayout(grp_tpl)
        self.cmb_tpl = QComboBox(); self._refresh_tpl_list()
        self.btn_tpl_load = QPushButton("加载")
        self.btn_tpl_save = QPushButton("保存为…")
        self.btn_tpl_delete = QPushButton("删除")
        tl2.addWidget(self.cmb_tpl); tl2.addWidget(self.btn_tpl_load); tl2.addWidget(self.btn_tpl_save); tl2.addWidget(self.btn_tpl_delete)

        layout.addWidget(self.grp_text)
        layout.addWidget(self.grp_image)
        layout.addWidget(grp_pos)
        layout.addWidget(grp_exp)
        layout.addWidget(grp_tpl)

        # Connections
        self.ed_text.textChanged.connect(self.on_settings_changed)
        self.ed_font.textChanged.connect(self.on_settings_changed)
        self.sp_font_size.valueChanged.connect(self.on_settings_changed)
        self.sld_opacity.valueChanged.connect(self.on_settings_changed)
        self.sp_stroke.valueChanged.connect(self.on_settings_changed)
        self.chk_shadow.toggled.connect(self.on_settings_changed)
        self.sp_shadow_x.valueChanged.connect(self.on_settings_changed)
        self.sp_shadow_y.valueChanged.connect(self.on_settings_changed)

        self.ed_img_wm.textChanged.connect(self.on_settings_changed)
        self.sld_scale.valueChanged.connect(self.on_settings_changed)
        self.sld_img_opacity.valueChanged.connect(self.on_settings_changed)

        self.cmb_pos.currentTextChanged.connect(self.on_settings_changed)
        self.sp_rot.valueChanged.connect(self.on_settings_changed)
        self.sp_off_x.valueChanged.connect(self.on_settings_changed)
        self.sp_off_y.valueChanged.connect(self.on_settings_changed)

        self.cmb_fmt.currentTextChanged.connect(self.on_export_changed)
        self.sld_quality.valueChanged.connect(self.on_export_changed)
        self.cmb_name_mode.currentTextChanged.connect(self.on_export_changed)
        self.ed_prefix.textChanged.connect(self.on_export_changed)
        self.ed_suffix.textChanged.connect(self.on_export_changed)
        self.cmb_resize.currentTextChanged.connect(self.on_export_changed)
        self.sp_resize.valueChanged.connect(self.on_export_changed)

        self.btn_export_sel.clicked.connect(self.export_selected)
        self.btn_export_all.clicked.connect(self.export_all)

        self.btn_tpl_load.clicked.connect(self.load_template)
        self.btn_tpl_save.clicked.connect(self.save_template)
        self.btn_tpl_delete.clicked.connect(self.delete_template)

        self.on_mode_changed(0)
        return box

    def _refresh_tpl_list(self):
        self.cmb_tpl.clear()
        self.cmb_tpl.addItems(sorted(tmpl.list_templates().keys()))

    def on_mode_changed(self, idx: int):
        text_mode = (self.cmb_mode.currentIndex() == 0)
        self.wm.mode = "text" if text_mode else "image"
        self.grp_text.setVisible(text_mode)
        self.grp_image.setVisible(not text_mode)
        self.on_settings_changed()

    def clear_free_pos(self):
        self.wm.free_pos_norm = None
        self.on_settings_changed()

    def choose_font(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择字体文件", "", "Font Files (*.ttf *.otf)")
        if f:
            self.ed_font.setText(f)

    def choose_wm_image(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择水印图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if f:
            self.ed_img_wm.setText(f)

    def choose_color(self):
        c = QColorDialog.getColor(QColor(*self.wm.text_style.color), self, "选择颜色")
        if c.isValid():
            self.wm.text_style.color = (c.red(), c.green(), c.blue())
            self.on_settings_changed()

    def choose_stroke_color(self):
        c = QColorDialog.getColor(QColor(*self.wm.text_style.stroke_color), self, "描边颜色")
        if c.isValid():
            self.wm.text_style.stroke_color = (c.red(), c.green(), c.blue())
            self.on_settings_changed()

    def choose_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出文件夹", self.ed_out.text() or os.getcwd())
        if d:
            self.ed_out.setText(d)

    def on_settings_changed(self):
        # pull from UI to state
        self.wm.text = self.ed_text.text()
        self.wm.text_style.font_path = self.ed_font.text() or None
        self.wm.text_style.font_size = self.sp_font_size.value()
        self.wm.text_style.opacity = self.sld_opacity.value()
        self.wm.text_style.stroke_width = self.sp_stroke.value()
        # color/stroke color are updated via dialogs
        self.wm.text_style.shadow = self.chk_shadow.isChecked()
        self.wm.text_style.shadow_offset = (self.sp_shadow_x.value(), self.sp_shadow_y.value())

        self.wm.image_style.path = self.ed_img_wm.text() or None
        self.wm.image_style.scale = max(0.01, self.sld_scale.value() / 100.0)
        self.wm.image_style.opacity = self.sld_img_opacity.value()

        self.wm.position = self.cmb_pos.currentText()
        self.wm.rotation = float(self.sp_rot.value())
        self.wm.offset = (self.sp_off_x.value(), self.sp_off_y.value())

        tmpl.save_last(self.wm, self.exp)
        self._debounce.start()

    def on_export_changed(self):
        self.exp.output_dir = self.ed_out.text()
        self.exp.out_format = self.cmb_fmt.currentText()
        self.exp.jpeg_quality = self.sld_quality.value()
        self.exp.naming_mode = self.cmb_name_mode.currentText()
        self.exp.prefix = self.ed_prefix.text()
        self.exp.suffix = self.ed_suffix.text()
        self.exp.resize_mode = self.cmb_resize.currentText()
        self.exp.resize_value = self.sp_resize.value()

        tmpl.save_last(self.wm, self.exp)

    def export_selected(self):
        rows = [self.list_widget.row(i) for i in self.list_widget.selectedItems()]
        files = [self.files[r] for r in rows if 0 <= r < len(self.files)]
        self._export(files)

    def export_all(self):
        self._export(self.files[:])

    def _export(self, files: List[str]):
        if not files:
            QMessageBox.information(self, "导出", "没有可导出的文件")
            return
        out_dir = self.ed_out.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "导出", "请选择输出文件夹")
            return
        # Prevent exporting into original folder
        if os.path.abspath(os.path.dirname(files[0])) == os.path.abspath(out_dir):
            QMessageBox.warning(self, "导出", "为防止覆盖原图，禁止导出到原文件夹，请选择其他位置")
            return
        self.exp.output_dir = out_dir

        self.worker = ExportWorker(files, self.wm, self.exp)
        self.worker.progress.connect(self.on_export_progress)
        self.worker.finished.connect(self.on_export_finished)
        self.statusBar().showMessage("开始导出…")
        self.worker.start()

    def on_export_progress(self, cur: int, total: int, path: str, ok: bool, msg: str):
        base = os.path.basename(path)
        if ok:
            self.statusBar().showMessage(f"[{cur}/{total}] 导出成功: {base} -> {msg}")
        else:
            self.statusBar().showMessage(f"[{cur}/{total}] 失败: {base} ({msg})")

    def on_export_finished(self, success: int, total: int):
        self.statusBar().showMessage(f"导出完成: 成功 {success}/{total}")
        QMessageBox.information(self, "导出", f"导出完成: 成功 {success}/{total}")

    def _apply_state_to_ui(self):
        # wm
        self.cmb_mode.setCurrentIndex(0 if self.wm.mode == "text" else 1)
        self.ed_text.setText(self.wm.text)
        self.ed_font.setText(self.wm.text_style.font_path or "")
        self.sp_font_size.setValue(self.wm.text_style.font_size)
        self.sld_opacity.setValue(self.wm.text_style.opacity)
        self.sp_stroke.setValue(self.wm.text_style.stroke_width)
        self.chk_shadow.setChecked(self.wm.text_style.shadow)
        self.sp_shadow_x.setValue(self.wm.text_style.shadow_offset[0])
        self.sp_shadow_y.setValue(self.wm.text_style.shadow_offset[1])

        self.ed_img_wm.setText(self.wm.image_style.path or "")
        self.sld_scale.setValue(int(self.wm.image_style.scale * 100))
        self.sld_img_opacity.setValue(self.wm.image_style.opacity)

        self.cmb_pos.setCurrentText(self.wm.position)
        self.sp_rot.setValue(int(self.wm.rotation))
        self.sp_off_x.setValue(self.wm.offset[0])
        self.sp_off_y.setValue(self.wm.offset[1])

        # export
        self.ed_out.setText(self.exp.output_dir)
        self.cmb_fmt.setCurrentText(self.exp.out_format)
        self.sld_quality.setValue(self.exp.jpeg_quality)
        self.cmb_name_mode.setCurrentText(self.exp.naming_mode)
        self.ed_prefix.setText(self.exp.prefix)
        self.ed_suffix.setText(self.exp.suffix)
        self.cmb_resize.setCurrentText(self.exp.resize_mode)
        self.sp_resize.setValue(self.exp.resize_value)

    def save_template(self):
        name, ok = QFileDialog.getSaveFileName(self, "模板名称(输入文件名即可)", "", "Template (*.json)")
        if not name:
            return
        # Use the base name without extension as template key
        key = os.path.splitext(os.path.basename(name))[0]
        tmpl.save_template(key, self.wm, self.exp)
        self._refresh_tpl_list()
        self.statusBar().showMessage(f"模板已保存: {key}")

    def load_template(self):
        key = self.cmb_tpl.currentText()
        if not key:
            return
        loaded = tmpl.load_template(key)
        if not loaded:
            QMessageBox.warning(self, "模板", "模板不存在或损坏")
            return
        self.wm, self.exp = loaded
        # 若模板中的输出目录位于 dist 文件夹内，自动重写到工程根目录 output
        try:
            from pathlib import Path
            import sys as _sys
            outp = Path(self.exp.output_dir).resolve()
            needs_rewrite = "dist" in [p.name.lower() for p in outp.parts]
            if getattr(_sys, 'frozen', False):
                exe_path = Path(_sys.executable).resolve()
                parent = exe_path.parent
                if parent.name.lower() == 'watermarkstudio' and parent.parent.name.lower() == 'dist':
                    expected_root = parent.parent.parent
                else:
                    expected_root = parent
                expected_out = (expected_root / 'output').resolve()
                if outp != expected_out:
                    needs_rewrite = True
            if needs_rewrite:
                def _default_output_dir_inner() -> str:
                    import sys as __sys
                    from pathlib import Path as __Path
                    if getattr(__sys, 'frozen', False):
                        exe_path = __Path(__sys.executable).resolve()
                        parent = exe_path.parent
                        if parent.name.lower() == 'watermarkstudio' and parent.parent.name.lower() == 'dist':
                            root = parent.parent.parent
                        else:
                            root = parent
                    else:
                        root = __Path(__file__).resolve().parent.parent
                    return str((root / "output").resolve())
                self.exp.output_dir = _default_output_dir_inner()
        except Exception:
            pass
        self.preview.set_watermark_settings(self.wm)
        self._apply_state_to_ui()
        self.preview.update_preview()

    def delete_template(self):
        key = self.cmb_tpl.currentText()
        if not key:
            return
        if tmpl.delete_template(key):
            self._refresh_tpl_list()
            self.statusBar().showMessage(f"已删除模板: {key}")
        else:
            QMessageBox.warning(self, "模板", "删除失败")
