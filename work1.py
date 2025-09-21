import os
import argparse
from PIL import Image, ImageDraw, ImageFont
import piexif

def get_exif_date(img_path):
    try:
        exif_dict = piexif.load(img_path)
        date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode()
        return date_str.split(' ')[0].replace(':', '-')
    except Exception:
        return None

def add_watermark(img_path, text, font_size, color, position, save_path):
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", font_size)
    w, h = img.size
    text_w, text_h = draw.textsize(text, font=font)
    pos_dict = {
        "left_top": (10, 10),
        "center": ((w - text_w) // 2, (h - text_h) // 2),
        "right_bottom": (w - text_w - 10, h - text_h - 10)
    }
    draw.text(pos_dict[position], text, font=font, fill=color)
    img.save(save_path)

def main():
    parser = argparse.ArgumentParser(description="图片批量添加拍摄时间水印")
    parser.add_argument("img_dir", help="图片文件夹路径")
    parser.add_argument("--font_size", type=int, default=32, help="字体大小")
    parser.add_argument("--color", default="white", help="字体颜色")
    parser.add_argument("--position", choices=["left_top", "center", "right_bottom"], default="right_bottom", help="水印位置")
    args = parser.parse_args()

    img_dir = args.img_dir
    watermark_dir = os.path.join(img_dir, os.path.basename(img_dir) + "_watermark")
    os.makedirs(watermark_dir, exist_ok=True)

    for fname in os.listdir(img_dir):
        fpath = os.path.join(img_dir, fname)
        if os.path.isfile(fpath) and fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            date = get_exif_date(fpath)
            if date:
                save_path = os.path.join(watermark_dir, fname)
                add_watermark(fpath, date, args.font_size, args.color, args.position, save_path)
                print(f"已处理：{fname}")

if __name__ == "__main__":
    main()
