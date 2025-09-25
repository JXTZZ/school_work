from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Optional, Tuple, Literal
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# Pillow resampling compatibility (Pillow 9/10+)
try:
    Resampling = Image.Resampling  # type: ignore[attr-defined]
    _LANCZOS = Resampling.LANCZOS
    _BICUBIC = Resampling.BICUBIC
except Exception:
    # Fallbacks for older Pillow names; avoid referencing NEAREST to silence analyzers
    _LANCZOS = getattr(Image, "LANCZOS", getattr(Image, "ANTIALIAS", getattr(Image, "BILINEAR", 1)))
    _BICUBIC = getattr(Image, "BICUBIC", getattr(Image, "BILINEAR", _LANCZOS))

PositionPreset = Literal[
    "top-left","top-center","top-right",
    "middle-left","center","middle-right",
    "bottom-left","bottom-center","bottom-right"
]


@dataclass
class TextStyle:
    font_path: Optional[str] = None  # path to .ttf/.otf; if None, default
    font_size: int = 36
    color: Tuple[int, int, int] = (255, 255, 255)
    opacity: int = 80  # 0-100
    stroke_width: int = 0
    stroke_color: Tuple[int, int, int] = (0, 0, 0)
    shadow: bool = False
    shadow_offset: Tuple[int, int] = (2, 2)


@dataclass
class ImageStyle:
    path: Optional[str] = None
    scale: float = 0.25  # relative to base image min(width,height)
    opacity: int = 80  # 0-100


@dataclass
class WatermarkSettings:
    mode: Literal["text", "image"] = "text"
    text: str = "Sample Watermark"
    text_style: TextStyle = field(default_factory=TextStyle)
    image_style: ImageStyle = field(default_factory=ImageStyle)
    rotation: float = 0.0  # degrees
    position: PositionPreset = "bottom-right"
    offset: Tuple[int, int] = (10, 10)  # padding from edge for presets
    # free position in normalized coordinates (0..1). If not None, use this and ignore preset
    free_pos_norm: Optional[Tuple[float, float]] = None


@dataclass
class ExportSettings:
    output_dir: str = ""
    prevent_overwrite_original: bool = True
    naming_mode: Literal["keep", "prefix", "suffix"] = "suffix"
    prefix: str = "wm_"
    suffix: str = "_watermarked"
    out_format: Literal["JPEG", "PNG"] = "JPEG"
    jpeg_quality: int = 90  # 0-100
    resize_mode: Literal["none", "width", "height", "percent"] = "none"
    resize_value: int = 0  # px for width/height, percent for percent


DEFAULT_FONT_CANDIDATES = [
    "arial.ttf",
    os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "arial.ttf"),
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def load_font(path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    for c in DEFAULT_FONT_CANDIDATES:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def apply_resize(im: Image.Image, exp: ExportSettings) -> Image.Image:
    if exp.resize_mode == "none":
        return im
    w, h = im.size
    if exp.resize_mode == "width" and exp.resize_value > 0:
        new_w = exp.resize_value
        ratio = new_w / w
        new_h = max(1, int(h * ratio))
        return im.resize((new_w, new_h), _LANCZOS)
    if exp.resize_mode == "height" and exp.resize_value > 0:
        new_h = exp.resize_value
        ratio = new_h / h
        new_w = max(1, int(w * ratio))
        return im.resize((new_w, new_h), _LANCZOS)
    if exp.resize_mode == "percent" and exp.resize_value > 0:
        ratio = exp.resize_value / 100.0
        return im.resize((max(1, int(w * ratio)), max(1, int(h * ratio))), _LANCZOS)
    return im


def compute_anchor(base_size: Tuple[int, int], wm_size: Tuple[int, int], preset: PositionPreset, offset=(10, 10)) -> Tuple[int, int]:
    bw, bh = base_size
    ww, wh = wm_size
    ox, oy = offset
    mapping = {
        "top-left": (ox, oy),
        "top-center": ((bw - ww) // 2, oy),
        "top-right": (bw - ww - ox, oy),
        "middle-left": (ox, (bh - wh) // 2),
        "center": ((bw - ww) // 2, (bh - wh) // 2),
        "middle-right": (bw - ww - ox, (bh - wh) // 2),
        "bottom-left": (ox, bh - wh - oy),
        "bottom-center": ((bw - ww) // 2, bh - wh - oy),
        "bottom-right": (bw - ww - ox, bh - wh - oy),
    }
    return mapping.get(preset, mapping["bottom-right"])


def render_text_watermark(base: Image.Image, settings: WatermarkSettings) -> Image.Image:
    txt = settings.text or ""
    style = settings.text_style
    font = load_font(style.font_path, style.font_size)

    # Create transparent layer for text
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    # measure text
    try:
        bbox = draw.textbbox((0, 0), txt, font=font, stroke_width=style.stroke_width)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        # Fallback for very old Pillow
        tw, th = font.getsize(txt)

    # position
    if settings.free_pos_norm:
        x = int(settings.free_pos_norm[0] * (base.size[0] - tw))
        y = int(settings.free_pos_norm[1] * (base.size[1] - th))
    else:
        x, y = compute_anchor(base.size, (tw, th), settings.position, settings.offset)

    # shadow
    if style.shadow:
        sx = x + style.shadow_offset[0]
        sy = y + style.shadow_offset[1]
        draw.text((sx, sy), txt, font=font, fill=(0, 0, 0, int(255 * style.opacity / 100)),
                  stroke_width=style.stroke_width, stroke_fill=(0, 0, 0, int(255 * style.opacity / 100)))

    # main text
    r, g, b = style.color
    alpha = int(255 * style.opacity / 100)
    draw.text((x, y), txt, font=font, fill=(r, g, b, alpha),
              stroke_width=style.stroke_width,
              stroke_fill=(*style.stroke_color, alpha))

    # rotation
    if settings.rotation:
        layer = layer.rotate(settings.rotation, resample=_BICUBIC, expand=1)
        # after rotation, we need to re-anchor the rotated layer onto base centered
        bg = Image.new("RGBA", base.size, (0, 0, 0, 0))
        # paste centered
        bx, by = (base.size[0] - layer.size[0]) // 2, (base.size[1] - layer.size[1]) // 2
        bg.alpha_composite(layer, (bx, by))
        layer = bg

    out = base.copy()
    out.alpha_composite(layer)
    return out


def render_image_watermark(base: Image.Image, settings: WatermarkSettings) -> Image.Image:
    style = settings.image_style
    if not style.path or not os.path.exists(style.path):
        return base.copy()
    wm = Image.open(style.path).convert("RGBA")
    # scale relative to min dimension
    bw, bh = base.size
    target = int(min(bw, bh) * max(0.01, min(5.0, style.scale)))
    # keep aspect ratio: scale so that wm width equals target
    ratio = target / wm.width if wm.width else 1.0
    new_size = (max(1, int(wm.width * ratio)), max(1, int(wm.height * ratio)))
    wm = wm.resize(new_size, _LANCZOS)

    # opacity
    if style.opacity < 100:
        alpha = wm.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(style.opacity / 100.0)  # type: ignore
        wm.putalpha(alpha)

    # rotation
    if settings.rotation:
        wm = wm.rotate(settings.rotation, resample=_BICUBIC, expand=1)

    # position
    if settings.free_pos_norm:
        x = int(settings.free_pos_norm[0] * (bw - wm.width))
        y = int(settings.free_pos_norm[1] * (bh - wm.height))
    else:
        x, y = compute_anchor((bw, bh), wm.size, settings.position, settings.offset)

    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.alpha_composite(wm, (x, y))

    out = base.copy()
    out.alpha_composite(layer)
    return out


def apply_watermark(img: Image.Image, wm: WatermarkSettings) -> Image.Image:
    base = img.convert("RGBA")
    if wm.mode == "text":
        return render_text_watermark(base, wm)
    else:
        return render_image_watermark(base, wm)


def export_image(src_path: str, wm: WatermarkSettings, exp: ExportSettings) -> Tuple[bool, str]:
    try:
        im = Image.open(src_path).convert("RGBA")
        im = apply_watermark(im, wm)
        im = apply_resize(im, exp)

        # naming
        name, ext = os.path.splitext(os.path.basename(src_path))
        if exp.naming_mode == "keep":
            out_name = name
        elif exp.naming_mode == "prefix":
            out_name = f"{exp.prefix}{name}"
        else:
            out_name = f"{name}{exp.suffix}"
        # format extension
        out_ext = ".jpg" if exp.out_format == "JPEG" else ".png"
        out_path = os.path.join(exp.output_dir, out_name + out_ext)

        # prevent overwrite into original folder
        if exp.prevent_overwrite_original:
            src_dir = os.path.abspath(os.path.dirname(src_path))
            out_dir = os.path.abspath(exp.output_dir)
            if src_dir == out_dir:
                return False, f"Output folder must differ from source folder for {src_path}"

        os.makedirs(exp.output_dir, exist_ok=True)
        if exp.out_format == "JPEG":
            im.convert("RGB").save(out_path, "JPEG", quality=max(0, min(100, exp.jpeg_quality)))
        else:
            im.save(out_path, "PNG")
        return True, out_path
    except Exception as e:
        return False, str(e)
