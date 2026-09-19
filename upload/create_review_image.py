#!/usr/bin/env python3

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# CONFIG
# ============================================================

FONT_SIZE = 130

MARGIN_X = 36
MARGIN_Y = 36

POSITION_TOP_LEFT = "top_left"
POSITION_MIDDLE_LEFT = "middle_left"
POSITION_BOTTOM_LEFT = "bottom_left"
DEFAULT_POSITION = POSITION_TOP_LEFT
VALID_POSITIONS = (
    POSITION_TOP_LEFT,
    POSITION_MIDDLE_LEFT,
    POSITION_BOTTOM_LEFT,
)

FONT_PATH = str(Path(__file__).resolve().parent / "DroidSans-Bold.ttf")


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


def normalize_position(position):
    aliases = {
        "1": POSITION_TOP_LEFT,
        "top": POSITION_TOP_LEFT,
        "top_left": POSITION_TOP_LEFT,
        "top-left": POSITION_TOP_LEFT,
        "2": POSITION_MIDDLE_LEFT,
        "middle": POSITION_MIDDLE_LEFT,
        "middle_left": POSITION_MIDDLE_LEFT,
        "middle-left": POSITION_MIDDLE_LEFT,
        "center_left": POSITION_MIDDLE_LEFT,
        "3": POSITION_BOTTOM_LEFT,
        "bottom": POSITION_BOTTOM_LEFT,
        "bottom_left": POSITION_BOTTOM_LEFT,
        "bottom-left": POSITION_BOTTOM_LEFT,
    }
    key = str(position or "").strip().lower()
    if key in aliases:
        return aliases[key]
    raise ValueError(
        "Vị trí không hợp lệ. Chỉ nhận: "
        "top_left / middle_left / bottom_left"
    )


def label_xy(image_size, font, text, position=DEFAULT_POSITION):
    """Tọa độ vẽ chữ Tập N: luôn mép trái, đổi theo trên / giữa / dưới."""
    _width, height = image_size
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    bbox = dummy.textbbox((0, 0), text, font=font, stroke_width=10)
    text_h = bbox[3] - bbox[1]
    x = MARGIN_X
    pos = normalize_position(position)

    if pos == POSITION_MIDDLE_LEFT:
        y = max(0, (height - text_h) // 2)
    elif pos == POSITION_BOTTOM_LEFT:
        y = max(0, height - text_h - MARGIN_Y)
    else:
        y = MARGIN_Y

    return x, y


# ============================================================
# CREATE ONE IMAGE
# ============================================================

def create_episode_image(
    source_image: Image.Image,
    episode_number: int,
    output_path: Path,
    font: ImageFont.FreeTypeFont,
    position=DEFAULT_POSITION,
):
    image = source_image.copy()

    episode_label = f"Tập {episode_number}"
    x, y = label_xy(image.size, font, episode_label, position)

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
        (x, y),
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
        (x + 2, y + 2),
        episode_label,
        font=font,
        fill=(0, 0, 0, int(255 * 0.35)),
        stroke_width=5,
        stroke_fill=(0, 0, 0, int(255 * 0.35)),
    )

    # Chữ chính
    main_draw.text(
        (x, y),
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
# HỎI CẤU HÌNH KHI CHẠY
# ============================================================

def ask_image_path(prompt):
    while True:
        value = input(prompt).strip().strip('"').strip("'")

        if not value:
            print("Trường này bắt buộc.")
            continue

        input_path = Path(value).expanduser()

        if input_path.is_file():
            return input_path

        print(f"Không tìm thấy ảnh: {input_path}")


def ask_position(default=DEFAULT_POSITION):
    default = normalize_position(default)
    print("Vị trí chữ Tập N:")
    print("  1) top_left     (phía trên bên trái)")
    print("  2) middle_left  (phía giữa bên trái)")
    print("  3) bottom_left  (phía dưới bên trái)")

    while True:
        value = input(f"Chọn [1/2/3, mặc định {default}]: ").strip()
        if not value:
            return default
        try:
            return normalize_position(value)
        except ValueError as exc:
            print(exc)


def ask_episode_number(prompt):
    while True:
        value = input(prompt).strip()

        try:
            episode_number = int(value)
        except ValueError:
            print("Vui lòng nhập số nguyên.")
            continue

        if episode_number <= 0:
            print("episode_number phải > 0")
            continue

        return episode_number


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("CREATE REVIEW IMAGE")
    print()

    input_path = ask_image_path("Đường dẫn ảnh gốc: ")
    episode_number = ask_episode_number("episode_number: ")
    position = ask_position()

    # --------------------------------------------------------
    # Load source image
    # --------------------------------------------------------

    source_image = Image.open(input_path)

    print()
    print(f"Ảnh nguồn       : {input_path}")
    print(f"Kích thước      : {source_image.size}")
    print(f"episode_number  : {episode_number}")
    print(f"position        : {position}")

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

    output_path = output_dir / f"tap_{episode_number}.jpeg"

    create_episode_image(
        source_image=source_image,
        episode_number=episode_number,
        output_path=output_path,
        font=font,
        position=position,
    )

    print(f"Đã tạo: {output_path}")
    print()
    print("Hoàn thành!")
    print(f"Thư mục: {output_dir.resolve()}")


if __name__ == "__main__":
    main()