Để chạy script `tts/generate.py` đã được tối ưu hóa bằng **uv** trên Mac Mini M2, bạn có thể thực hiện theo các câu lệnh chi tiết dưới đây trong ứng dụng **Terminal**:

1. **Tạo âm thanh cho 1 truyện/thư mục cụ thể:** 1. Chạy cơ bản.
Truyền đường dẫn tới thư mục câu chuyện (ví dụ `stories/truyen-001`):

```bash
uv run python tts/generate.py stories/truyen-001

```


2. **Tạo âm thanh cho TẤT CẢ các truyện:** 2. Chạy hàng loạt.
Sử dụng cờ `--all` để tự động duyệt qua tất cả các thư mục nằm trong `stories/`:

```bash
uv run python tts/generate.py --all

```


3. **Chỉ tạo lại các file script chỉ định:** 3. Chạy file cụ thể.
Sử dụng cờ `--only` nếu bạn chỉ muốn tạo file âm thanh cho một hoặc một vài file `.txt` cụ thể trong script:

```bash
uv run python tts/generate.py stories/truyen-001 --only 001.txt 002.txt

```


4. **Ép buộc tạo lại (Force regenerate):** 4. Ghi đè.
Mặc định script sẽ bỏ qua các file `.wav` đã tồn tại. Nếu bạn muốn ép tạo lại toàn bộ file âm thanh:

```bash
uv run python tts/generate.py stories/truyen-001 --force

```


5. **Thay đổi kích thước batch hoặc max_chars:** 5. Tùy chỉnh tham số.
Bạn có thể điều chỉnh độ dài tối đa của từng chunk văn bản (`--max-chars`) hoặc số lượng đoạn xử lý (`--batch-size`):

```bash
uv run python tts/generate.py stories/truyen-001 --max-chars 256 --batch-size 4

```


---

**Mẹo hữu ích:**

* Cấu trúc thư mục truyện mặc định cần có: `stories/<tên_truyen>/script/*.txt` và `stories/<tên_truyen>/voice/reference.wav`.
* Các file âm thanh xuất ra sẽ nằm tại `stories/<tên_truyen>/audio/`.


Dưới đây là câu lệnh chạy đầy đủ nhất cho file `tts/generate.py` kết hợp cả hai tham số `--max-chars 512` và `--batch-size 8` bằng **uv**:

### Câu lệnh chạy cho 1 truyện cụ thể

```bash
uv run python tts/generate.py stories/truyen-001 --max-chars 512 --batch-size 8

```

### Câu lệnh chạy cho TẤT CẢ các truyện

```bash
uv run python tts/generate.py --all --max-chars 512 --batch-size 8

```

---

### Các cờ mở rộng (Nên kết hợp nếu cần)

* **Ép tạo lại toàn bộ file WAV (`--force`):**
```bash
uv run python tts/generate.py stories/truyen-001 --max-chars 512 --batch-size 8 --force

```


* **Chỉ chạy cho các chương chỉ định (`--only`):**
```bash
uv run python tts/generate.py stories/truyen-001 --max-chars 512 --batch-size 8 --only 405.txt 406.txt

```