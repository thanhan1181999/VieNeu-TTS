import os

# Định nghĩa các khoảng chương cho 34 phần
ranges = [
    (1, 95), (96, 166), (167, 238), (239, 309), (310, 380),
    (381, 451), (452, 520), (521, 590), (591, 659), (660, 729),
    (730, 798), (799, 867), (868, 938), (939, 1007), (1008, 1075),
    (1076, 1141), (1142, 1206), (1207, 1272), (1273, 1337), (1338, 1403),
    (1404, 1468), (1469, 1535), (1536, 1600), (1601, 1666), (1667, 1729),
    (1730, 1794), (1795, 1859), (1860, 1925), (1926, 1992), (1993, 2061),
    (2062, 2130), (2131, 2199), (2200, 2266), (2267, 2271)
]

def merge_files():
    for part_idx, (start_chap, end_chap) in enumerate(ranges, start=1):
        output_filename = f"upload/truyen-001/Phan_{part_idx:02d}.txt"
        
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            for chap in range(start_chap, end_chap + 1):
                input_filename = f"stories/truyen-001/script/{chap}.txt"
                
                if os.path.exists(input_filename):
                    with open(input_filename, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                        outfile.write("\n\n")  # Thêm dòng trống giữa các chương
                else:
                    print(f"Cảnh báo: Không tìm thấy file {input_filename}")
                    
        print(f"Đã tạo thành công: {output_filename}")

if __name__ == "__main__":
    merge_files()