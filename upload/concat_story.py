import os

# ranges = [
#     (1, 95), (96, 166), (167, 238), (239, 309), (310, 380),
#     (381, 451), (452, 520), (521, 590), (591, 659), (660, 729),
#     (730, 798), (799, 867), (868, 938), (939, 1007), (1008, 1075),
#     (1076, 1141), (1142, 1206), (1207, 1272), (1273, 1337), (1338, 1403),
#     (1404, 1468), (1469, 1535), (1536, 1600), (1601, 1666), (1667, 1729),
#     (1730, 1794), (1795, 1859), (1860, 1925), (1926, 1992), (1993, 2061),
#     (2062, 2130), (2131, 2199), (2200, 2266), (2267, 2271)
# ]


def parse_ranges(text):
    ranges = []

    for item in text.split(","):
        item = item.strip()

        if not item:
            continue

        if "-" not in item:
            raise ValueError

        start_raw, end_raw = item.split("-", 1)
        start_chap = int(start_raw.strip())
        end_chap = int(end_raw.strip())

        if end_chap < start_chap:
            raise ValueError

        ranges.append((start_chap, end_chap))

    if not ranges:
        raise ValueError

    return ranges


def ask_ranges():
    while True:
        value = input("Ranges (ví dụ 1-101, 102-197): ").strip()

        try:
            return parse_ranges(value)
        except ValueError:
            print("Định dạng không hợp lệ. Ví dụ: 1-101, 102-197")


def ask_output_dir():
    while True:
        value = input("Thư mục lưu file txt: ").strip().strip('"').strip("'")

        if not value:
            print("Trường này bắt buộc.")
            continue

        output_dir = os.path.abspath(os.path.expanduser(value))
        os.makedirs(output_dir, exist_ok=True)
        return output_dir


def merge_files(ranges, output_dir):
    for part_idx, (start_chap, end_chap) in enumerate(ranges, start=1):
        output_filename = os.path.join(
            output_dir,
            f"Phan_{part_idx:02d}.txt"
        )

        with open(output_filename, 'w', encoding='utf-8') as outfile:
            for chap in range(start_chap, end_chap + 1):
                input_filename = f"stories/qbcc/script/{chap}.txt"

                if os.path.exists(input_filename):
                    with open(input_filename, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                        outfile.write("\n\n")  # Thêm dòng trống giữa các chương
                else:
                    print(f"Cảnh báo: Không tìm thấy file {input_filename}")

        print(f"Đã tạo thành công: {output_filename}")


if __name__ == "__main__":
    ranges = ask_ranges()
    output_dir = ask_output_dir()
    merge_files(ranges, output_dir)
