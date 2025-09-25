import os
from typing import Tuple, Optional
from PIL import Image

SUPPORTED_INPUT_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
SUPPORTED_OUTPUT_FORMATS = ("JPEG", "PNG")

# Pillow resampling compatibility
try:
    Resampling = Image.Resampling  # type: ignore[attr-defined]
    _LANCZOS = Resampling.LANCZOS
except Exception:
    _LANCZOS = getattr(Image, "LANCZOS", getattr(Image, "ANTIALIAS", getattr(Image, "NEAREST", 1)))


def is_image_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in SUPPORTED_INPUT_EXTS


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def qpixmap_from_pil(img: Image.Image):
    # Convert a PIL Image to QPixmap without PIL.ImageQt to avoid compatibility issues
    from PyQt5.QtGui import QPixmap, QImage
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    w, h = img.size
    buf = img.tobytes("raw", "RGBA")
    qimg = QImage(buf, w, h, 4 * w, QImage.Format_RGBA8888)
    return QPixmap.fromImage(qimg.copy())


def pil_from_qimage(qimage) -> Image.Image:
    # Convert a QImage to PIL Image without PIL.ImageQt
    from PyQt5.QtGui import QImage
    qimg = qimage.convertToFormat(QImage.Format_RGBA8888)
    w, h = qimg.width(), qimg.height()
    ptr = qimg.bits()
    ptr.setsize(qimg.byteCount())
    data = bytes(ptr)
    im = Image.frombuffer("RGBA", (w, h), data, "raw", "RGBA", 0, 1)
    return im.copy()


def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def scale_to_fit(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    w, h = img.size
    if w <= max_w and h <= max_h:
        return img.copy()
    ratio = min(max_w / w, max_h / h)
    new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
    return img.resize(new_size, _LANCZOS)


def make_thumbnail(path: str, size: Tuple[int, int] = (120, 120)) -> Optional[Image.Image]:
    try:
        with Image.open(path) as im:
            im = im.convert("RGBA")
            im.thumbnail(size, _LANCZOS)
            return im
    except Exception:
        return None
