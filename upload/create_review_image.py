#!/usr/bin/env python3

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# CONFIG
# ============================================================

FONT_SIZE = 130

X = 36
Y = 36

# Font Roboto Bold
FONT_PATH = "/Users/a.nguyen/projects/vieneu-test/VieNeu-TTS/upload/DroidSans-Bold.ttf"


# ============================================================
# LOAD FONT
# ============================================================

def load_font(size):
    if not Path(FONT_PATH).exists():
        raise FileNotFoundError(
            f"Không tìm thấy font:\n{FONT_PATH}\n\n"
            "Hãy sửa FONT_PATH thành đường dẫn font Roboto Bold trên máy."
        )

    return ImageFont.truetype(FONT_PATH, size)


# ============================================================
# CREATE ONE IMAGE
# ============================================================

def create_episode_image(
    source_image: Image.Image,
    episode_number: int,
    output_path: Path,
    font: ImageFont.FreeTypeFont,
):
    image = source_image.copy()

    draw = ImageDraw.Draw(image)

    episode_label = f"Tập {episode_number}"

    # ========================================================
    # LỚP 1: Glow
    # Tương đương:
    #
    # fontcolor=white@0.15
    # borderw=10
    # bordercolor=white@0.5
    # ========================================================

    # Pillow không hỗ trợ opacity trực tiếp trên ImageDraw
    # nên tạo một layer RGBA riêng.
    glow_layer = Image.new(
        "RGBA",
        image.size,
        (0, 0, 0, 0)
    )

    glow_draw = ImageDraw.Draw(glow_layer)

    glow_draw.text(
        (X, Y),
        episode_label,
        font=font,
        fill=(255, 255, 255, int(255 * 0.15)),
        stroke_width=10,
        stroke_fill=(255, 255, 255, int(255 * 0.5)),
    )

    image = Image.alpha_composite(
        image.convert("RGBA"),
        glow_layer
    )

    # ========================================================
    # LỚP 2: Chữ chính
    #
    # fontcolor=white
    # borderw=5
    # bordercolor=black
    # shadowcolor=black@0.35
    # shadowx=2
    # shadowy=2
    # ========================================================

    main_layer = Image.new(
        "RGBA",
        image.size,
        (0, 0, 0, 0)
    )

    main_draw = ImageDraw.Draw(main_layer)

    # Shadow
    main_draw.text(
        (X + 2, Y + 2),
        episode_label,
        font=font,
        fill=(0, 0, 0, int(255 * 0.35)),
        stroke_width=5,
        stroke_fill=(0, 0, 0, int(255 * 0.35)),
    )

    # Chữ chính
    main_draw.text(
        (X, Y),
        episode_label,
        font=font,
        fill=(255, 255, 255, 255),
        stroke_width=5,
        stroke_fill=(0, 0, 0, 255),
    )

    image = Image.alpha_composite(
        image,
        main_layer
    )

    # ========================================================
    # SAVE
    # ========================================================

    image = image.convert("RGB")

    image.save(
        output_path,
        "JPEG",
        quality=95
    )


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) != 3:
        print(
            f"Usage:\n"
            f"  python {Path(sys.argv[0]).name} <image> <so_tap>\n\n"
            f"Example:\n"
            f"  python {Path(sys.argv[0]).name} thumbnail.jpeg 10"
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])
    episode_count = int(sys.argv[2])

    if not input_path.exists():
        print(f"Không tìm thấy ảnh: {input_path}")
        sys.exit(1)

    if episode_count <= 0:
        print("Số tập phải > 0")
        sys.exit(1)

    # --------------------------------------------------------
    # Load source image
    # --------------------------------------------------------

    source_image = Image.open(input_path)

    print(f"Ảnh nguồn : {input_path}")
    print(f"Kích thước: {source_image.size}")
    print(f"Số tập    : {episode_count}")

    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    output_dir = Path("upload/output")
    output_dir.mkdir(exist_ok=True)

    # --------------------------------------------------------
    # Font
    # --------------------------------------------------------

    font = load_font(FONT_SIZE)

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    for episode_number in range(1, episode_count + 1):

        output_path = output_dir / f"tap_{episode_number}.jpeg"

        create_episode_image(
            source_image=source_image,
            episode_number=episode_number,
            output_path=output_path,
            font=font,
        )

        print(f"Đã tạo: {output_path}")

    print()
    print(f"Hoàn thành! Đã tạo {episode_count} ảnh.")
    print(f"Thư mục: {output_dir.resolve()}")


if __name__ == "__main__":
    main()