# VieNeu-TTS — Hướng dẫn crawler truyện

Thư mục `craw` chứa các script dùng để lấy nội dung chương, danh sách tiêu đề chương từ website truyện, rồi làm sạch văn bản.

Dạng site giả định: `truyenfull.live` (URL dạng `/chuong-N/`, `/trang-N/`)

Nên chạy lệnh từ **thư mục gốc của repo**.

---

## Luồng xử lý khuyến nghị

1. `crawl_title.js` — lấy danh sách tên chương
2. `crawl.js` — lấy nội dung từng chương
3. `clean1.js` — xóa chữ rác và chuẩn hóa thành mỗi câu một dòng

Cấu trúc thư mục đầu ra:

```text
stories/<story>/
  ├── titles.txt          # output của crawl_title.js
  └── script/
      ├── 1.txt           # output của crawl.js (theo từng chương)
      ├── 2.txt
      └── ...
```

---

## 1. `crawl.js` — Crawl nội dung chương

Lấy lần lượt các chương trong khoảng chỉ định và lưu vào `stories/<story>/script/<số_chương>.txt`.

### Tham số bắt buộc

| Tham số | Ý nghĩa |
|---|---|
| `--story <name>` | Tên thư mục truyện (tên output) |
| `--start <number>` | Chương bắt đầu (số nguyên ≥ 1) |
| `--end <number>` | Chương kết thúc (≥ `--start`) |
| `--url <url>` | URL gốc của truyện |

### Tham số tùy chọn

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--selector <css>` | `#chapter-c` | CSS selector phần nội dung chương |
| `--delay <ms>` | `1000` | Thời gian nghỉ giữa các request |
| `--timeout <ms>` | `15000` | Timeout HTTP |
| `--retries <number>` | `3` | Số lần thử lại khi lỗi |
| `--force` | tắt | Ghi đè file đã tồn tại |
| `--help` / `-h` | — | Hiện hướng dẫn |

### Ghi chú hoạt động

- URL chương được ghép theo dạng `{url}/chuong-{n}/`
- Không có `--force` thì file `.txt` đã có sẽ bị bỏ qua
- Khi lỗi sẽ retry; giữa các chương sẽ chờ `--delay`

### Ví dụ (chỉ tham số bắt buộc)

```bash
node craw/crawl.js \
  --story truyen-001 \
  --start 101 \
  --end 200 \
  --url "https://truyenfull.live/thieu-gia-bi-boi"
```

### Ví dụ (đầy đủ tham số)

```bash
node craw/crawl.js \
  --story truyen-001 \
  --start 101 \
  --end 200 \
  --url "https://truyenfull.live/thieu-gia-bi-boi" \
  --selector "#chapter-c" \
  --delay 1000 \
  --timeout 15000 \
  --retries 3 \
  --force
```

### Test 1 chương

```bash
node craw/crawl.js \
  --story truyen-001 \
  --start 101 \
  --end 101 \
  --url "https://truyenfull.live/thieu-gia-bi-boi"
```

---

## 2. `crawl_title.js` — Crawl danh sách tên chương

Duyệt các trang mục lục và lưu tên chương vào `stories/<story>/titles.txt`.

### Tham số bắt buộc

| Tham số | Ý nghĩa |
|---|---|
| `--story <name>` | Tên thư mục truyện |
| `--url <url>` | URL gốc của truyện |

### Tham số tùy chọn

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--selector <css>` | `#list-chapter ul.list-chapter` | CSS selector danh sách chương |
| `--delay <ms>` | `1000` | Thời gian nghỉ giữa các trang |
| `--timeout <ms>` | `15000` | Timeout HTTP |
| `--retries <number>` | `3` | Số lần thử lại khi lỗi |
| `--force` | tắt | Ghi đè `titles.txt` nếu đã có |
| `--help` / `-h` | — | Hiện hướng dẫn |

### Ghi chú hoạt động

- URL trang: trang 1 là `{url}/`, từ trang 2 là `{url}/trang-{n}/`
- Dừng khi không còn title, hoặc nội dung trang trùng hệt trang trước
- Dòng đầu file luôn là `Giới Thiệu Truyện`
- Không có `--force` thì nếu file đã tồn tại sẽ thoát luôn

### Ví dụ (chỉ tham số bắt buộc)

```bash
node craw/crawl_title.js \
  --story truyen-001 \
  --url "https://truyenfull.live/thieu-gia-bi-boi/"
```

### Ví dụ (đầy đủ tham số)

```bash
node craw/crawl_title.js \
  --story truyen-001 \
  --url "https://truyenfull.live/thieu-gia-bi-boi/" \
  --selector "#list-chapter ul.list-chapter" \
  --delay 1000 \
  --timeout 15000 \
  --retries 3 \
  --force
```

---

## 3. `clean1.js` — Làm sạch văn bản chương

Xóa chữ rác trong `stories/<story>/script/*.txt` và chuẩn hoá đầu ra theo dạng **mỗi câu một dòng, cách nhau một dòng trống**.

### Tham số

| Tham số | Bắt buộc | Ý nghĩa |
|---|---|---|
| `<storyId>` | Không | Tên thư mục truyện. Mặc định: `truyen-001` |

Dùng positional argument (không dùng dạng `--story`).

### Việc script làm

- Xóa cụm quảng cáo / watermark (ví dụ: `truyenfull`, `Bạn đang đọc chuyện tại Truyện FULL`, …)
- Chuẩn hóa xuống dòng (CRLF → LF)
- Gộp các dòng lẻ trong cùng một đoạn, rồi tách thành từng câu
- Đầu ra: mỗi câu một dòng, giữa hai câu có đúng một dòng trống

### Quy tắc xác định câu

Chỉ coi `.` `?` `!` là dấu ngắt câu (không ngắt ở `;` hay `:`).

Không ngắt câu tại:

- Dấu chấm trong từ viết tắt (ví dụ: `TP. HCM`, `ThS. Nguyễn Văn A`, `v.v.`, `tr. 15`)
- Số thập phân (ví dụ: `3.14`)
- URL / domain (ví dụ: `example.com`) hoặc email

### Quy tắc định dạng đầu ra

- Trim khoảng trắng đầu/cuối câu; gộp nhiều khoảng trắng thành một
- Viết hoa ký tự đầu câu (locale tiếng Việt)
- Thêm dấu `.` ở cuối nếu câu thiếu dấu kết thúc

### Ví dụ gọi

```bash
# Mặc định (truyen-001)
node craw/clean1.js

# Chỉ định truyện
node craw/clean1.js truyen-001
node craw/clean1.js truyen-002
```

---

## Dependencies

Các package dùng trong `craw`:

- `axios`
- `cheerio`
- `fs-extra`

(Cần đã cài dependencies ở thư mục gốc repo.)

---

## Lưu ý

- `--delay` quá thấp dễ bị site giới hạn request
- Nếu HTML site đổi cấu trúc, hãy chỉnh `--selector`
- `crawl.js` / `crawl_title.js` cần `--force` nếu muốn ghi đè file cũ
- `clean1.js` ghi đè trực tiếp file đích (không tạo bản backup)
