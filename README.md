# Watermark Studio (Windows/Mac)

A local GUI app to add text or image watermarks to photos, with live preview, drag-and-drop import, batch export, naming rules, JPEG quality, and resize options.

## Features Checklist
- Import images: single/multi select, whole folder, drag-and-drop, thumbnail list.
- Input formats: JPEG, PNG (with alpha), BMP, TIFF.
- Output formats: JPEG or PNG.
- Naming rules: keep/prefix/suffix; prevent exporting into source folder by default.
- JPEG quality slider.
- Optional resizing: by width/height/percent.
- Text watermark: content, font file (.ttf/.otf), size, color, opacity, stroke, shadow.
- Image watermark: PNG with alpha, scale (relative to min dimension), opacity.
- Layout: nine-grid presets, click on preview to place watermark freely, rotation.
- Templates: save/load/delete; auto-save last settings and load on startup.

## Install

On Windows (cmd.exe):

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```
python -m app.main
```

## Usage Tips
- Click the left list to switch preview image. Click on the preview to set a free position for the watermark.
- Choose a font file for best text rendering (Arial, etc.). If not set, a system default is used.
- When exporting, choose an output folder different from source folders.
- JPEG quality only affects JPEG output; PNG ignores it.
- Resize options apply to the final watermarked image.

## Project Structure
- `app/engine.py` watermark rendering and export helper
- `app/gui.py` PyQt5 UI
- `app/exporter.py` background export worker (QThread)
- `app/templates.py` template persistence (JSON)
- `app/utils.py` misc helpers
- `app/main.py` entry point

## Known Notes
- Dragging the watermark: click to set position; presets reset free position.
- Fonts selected via file chooser are used by PIL directly.

