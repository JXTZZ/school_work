# python
import argparse
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
import piexif


def get_exif_date(image_path):
    """
    按顺序尝试获取图片拍摄时间并返回格式 YYYY-MM-DD。
    优先级：
      1) piexif (DateTimeOriginal / DateTimeDigitized / DateTime)
      2) PIL._getexif() (DateTimeOriginal / DateTime)
      3) 文件修改时间 (mtime)
    返回 (date_str, source) 或 (None, None)。
    """
    # 1) piexif
    try:
        exif_dict = piexif.load(image_path)
        candidates = [
            ("Exif", piexif.ExifIFD.DateTimeOriginal),
            ("Exif", piexif.ExifIFD.DateTimeDigitized),
            ("0th", piexif.ImageIFD.DateTime),
        ]
        for ifd_name, tag in candidates:
            if ifd_name in exif_dict:
                val = exif_dict[ifd_name].get(tag)
                if val:
                    if isinstance(val, bytes):
                        val = val.decode("utf-8", errors="ignore")
                    date_part = str(val).split(" ")[0].replace(":", "-")
                    return date_part, "piexif"
    except Exception:
        pass

    # 2) PIL._getexif()
    try:
        img = Image.open(image_path)
        exif = img._getexif()
        if exif:
            for k, v in exif.items():
                name = TAGS.get(k)
                if name in ("DateTimeOriginal", "DateTime"):
                    if isinstance(v, bytes):
                        v = v.decode("utf-8", errors="ignore")
                    date_part = str(v).split(" ")[0].replace(":", "-")
                    return date_part, "PIL._getexif"
    except Exception:
        pass

    # 3) 文件修改时间回退
    try:
        mtime = os.path.getmtime(image_path)
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d"), "mtime"
    except Exception:
        return None, None


def parse_color(color_str):
    """
    解析颜色字符串，支持颜色名或 'r,g,b' 格式，返回 (r,g,b) 元组
    """
    color_dict = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "white": (255, 255, 255),
        "black": (0, 0, 0),
        "yellow": (255, 255, 0),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255)
    }
    if not color_str:
        return (255, 255, 255)
    key = color_str.lower().strip()
    if key in color_dict:
        return color_dict[key]
    if "," in color_str:
        parts = [p.strip() for p in color_str.split(",")]
        if len(parts) == 3:
            try:
                r, g, b = map(int, parts)
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                return (r, g, b)
            except Exception:
                pass
    return (255, 255, 255)


def load_truetype_font(font_size):
    """
    尝试加载常见 TrueType 字体，回退到默认字体
    """
    candidates = [
        "arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, font_size)
        except Exception:
            continue
    return ImageFont.load_default()


def calculate_position(base_width, base_height, text_width, text_height, position):
    padding = 10
    if position == "top-left":
        return padding, padding
    elif position == "top-right":
        return base_width - text_width - padding, padding
    elif position == "bottom-left":
        return padding, base_height - text_height - padding
    elif position == "bottom-right":
        return base_width - text_width - padding, base_height - text_height - padding
    elif position == "center":
        return (base_width - text_width) // 2, (base_height - text_height) // 2
    else:
        return base_width - text_width - padding, base_height - text_height - padding


def add_watermark_to_image(image_path, output_path, font_size, color, position):
    """
    给单张图片添加水印并保存到 output_path
    """
    try:
        image = Image.open(image_path).convert("RGBA")
        date_str, source = get_exif_date(image_path)
        if not date_str:
            print(f"Skipping {os.path.basename(image_path)}: no date available")
            return False

        # 格式化日期（确保 YYYY-MM-DD）
        date_str = date_str.replace(":", "-")

        # 创建透明水印层
        watermark = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark)
        font = load_truetype_font(font_size)

        # 计算文本尺寸，兼容不同 Pillow 版本
        try:
            bbox = draw.textbbox((0, 0), date_str, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except Exception:
            text_width, text_height = draw.textsize(date_str, font=font)

        x, y = calculate_position(image.width, image.height, text_width, text_height, position)

        # 绘制半透明背景框以提高可读性
        draw.rectangle([x - 5, y - 5, x + text_width + 5, y + text_height + 5], fill=(0, 0, 0, 128))

        # 确保颜色为 RGBA
        if isinstance(color, tuple) and len(color) == 3:
            rgba_color = (color[0], color[1], color[2], 255)
        else:
            rgba_color = (255, 255, 255, 255)

        draw.text((x, y), date_str, font=font, fill=rgba_color)

        # 合并并保存（JPEG 转为 RGB）
        result = Image.alpha_composite(image, watermark)
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result.convert("RGB").save(output_path)
        print(f"Processed: {os.path.basename(image_path)} -> {os.path.basename(output_path)} (date source: {source})")
        return True

    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return False


def process_images(input_path, font_size, color, position):
    if not os.path.exists(input_path):
        print(f"Error: Path {input_path} does not exist")
        return

    if os.path.isfile(input_path):
        files = [input_path]
        input_dir = os.path.dirname(input_path) or "."
    else:
        input_dir = input_path
        files = []
        for f in os.listdir(input_dir):
            full = os.path.join(input_dir, f)
            if not os.path.isfile(full):
                continue
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp")):
                files.append(full)

    output_dir = os.path.join(input_dir, f"{os.path.basename(input_dir)}_watermark")
    os.makedirs(output_dir, exist_ok=True)

    success_count = 0
    for file_path in files:
        output_filename = f"watermarked_{os.path.basename(file_path)}"
        output_path = os.path.join(output_dir, output_filename)
        if add_watermark_to_image(file_path, output_path, font_size, color, position):
            success_count += 1

    print(f"\nCompleted! Successfully processed {success_count} images. Output directory: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Add EXIF date watermark to images")
    parser.add_argument("input_path", help="Input image file or directory path")
    parser.add_argument("--font_size", type=int, default=20, help="Font size, default is 20")
    parser.add_argument("--color", type=str, default="white",
                        help="Watermark color, support names or 'r,g,b'")
    parser.add_argument("--position", type=str, default="bottom-right",
                        choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"],
                        help="Watermark position, default is bottom-right")
    args = parser.parse_args()

    color = parse_color(args.color)
    process_images(args.input_path, args.font_size, color, args.position)


if __name__ == "__main__":
    main()
