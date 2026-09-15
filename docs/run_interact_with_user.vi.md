# Hướng dẫn dùng `run_interact_with_user.sh`

Script chạy tương tác, tự động hóa chuỗi xử lý: crawl truyện → làm sạch text → tạo TTS → crawl tiêu đề chương → tạo video.

Nên chạy từ **thư mục gốc của repository**.

```bash
./run_interact_with_user.sh
```

---

## Chế độ chạy

| Tình huống | Chế độ | Cần nhập |
|---|---|---|
| Chưa có `stories/<Story>/` (truyện mới) | Đầy đủ | URL, selector, voice, cover, … |
| Đã có `stories/<Story>/config.json` (lần 2+) | Rút gọn | Story + Start/End + bật/tắt từng bước |
| Có thư mục nhưng chưa có `config.json` (truyện cũ) | Chuyển tiếp | Hỏi URL/selector một lần để tạo config; cover/voice nếu đã có thì dùng luôn |

Sau lần chạy đầu, cấu hình được lưu vào `stories/<Story>/config.json`. Từ lần sau không hỏi lại cover / voice (dùng `cover.*` và `voice/reference.wav` có sẵn).

---

## Lần đầu (truyện mới)

| Mục | Bắt buộc | Mặc định | Mô tả |
|---|---|---|---|
| `Story` | Có | — | Tên thư mục truyện (`stories/<Story>/`) |
| `Start chapter` | Có | — | Chương bắt đầu |
| `End chapter` | Có | — | Chương kết thúc |
| `Content URL` | Có | — | URL crawl nội dung (`crawl.js`) |
| `Title URL` | Có | — | URL crawl tiêu đề (`crawl_title.js`) |
| `Crawl selector` | Không | `#chapter-c` | CSS selector nội dung chương |
| `Crawl title selector` | Không | `#list-chapter ul.list-chapter` | CSS selector danh sách tiêu đề |
| `Voice path` | Không | `stories/voices/reference.wav` | File giọng mẫu (copy vào `voice/reference.wav`) |
| `Image cover file path` | Có | — | Ảnh bìa (move thành `cover.<đuôi>`) |

Tiếp theo, chọn có chạy từng bước hay không (`Y/n`):

| Mục | Mặc định | Xử lý tương ứng |
|---|---|---|
| `Crawl & Clean?` | Yes | `crawl.js` → `clean1.js` |
| `Generate Audio?` | Yes | `tts/make_audio.py` |
| `Crawling Title?` | Yes | `crawl_title.js` |
| `Generate Video?` | Yes | `tts/make_video_ver4.py` |

---

## Lần sau (chế độ rút gọn)

| Mục | Mô tả |
|---|---|
| `Story` | Tên thư mục đã có `config.json` |
| `Start chapter` / `End chapter` | Khoảng chương lần này |
| Bật/tắt từng bước | Mặc định theo lần trước; Enter để giữ nguyên |

URL, selector, cover, voice được lấy từ `config.json` / file có sẵn — không hỏi lại.

---

## Ví dụ `config.json`

```json
{
  "content_url": "https://truyenfull.live/example/",
  "title_url": "https://truyenfull.live/example/",
  "crawl_selector": "#chapter-c",
  "crawl_title_selector": "#list-chapter ul.list-chapter",
  "last_start": "1",
  "last_end": "10",
  "crawl_and_clean": true,
  "generate_audio": true,
  "crawling_title": true,
  "generate_video": true
}
```

Mỗi lần chạy xong, script cập nhật `last_start` / `last_end` và các cờ bước.

---

## Content URL và Title URL khác nhau thế nào?

Một số website dùng URL base khác nhau cho trang nội dung chương và trang danh sách tiêu đề.

- `Content URL` — dùng lấy nội dung từng chương (ghép dạng `{url}/chuong-{n}/`)
- `Title URL` — dùng lấy danh sách tiêu đề (ghép dạng `{url}/`, `{url}/trang-{n}/`)

Nếu cùng một URL thì nhập giống nhau cho cả hai ô.

---

## Về selector

Bấm Enter để dùng giá trị mặc định:

- `Crawl selector` mặc định: `#chapter-c`
- `Crawl title selector` mặc định: `#list-chapter ul.list-chapter`

Chỉ cần đổi khi cấu trúc HTML của site khác với mặc định.

---

## Luồng chạy

1. Hỏi tên Story → phân loại mới / rút gọn / chuyển tiếp
2. Nhập các mục cần thiết và in lại cấu hình
3. Lưu (hoặc cập nhật) `config.json`
4. Nếu chưa có `script/0.txt` thì hỏi nhập phần giới thiệu (Ctrl+D để kết thúc)
5. Chạy các bước đang bật

---

## Ví dụ nhập

### Lần đầu

```text
Story: truyen-001
Start chapter: 1
End chapter: 10
Content URL: https://example.com/truyen-a/
Title URL: https://example.com/truyen-a/
Crawl selector [#chapter-c]:
Crawl title selector [#list-chapter ul.list-chapter]:
Voice path [stories/voices/reference.wav]:
Image cover file path (required): /path/to/cover.jpg
Crawl & Clean? [Y/n]:
Generate Audio? [Y/n]:
Crawling Title? [Y/n]:
Generate Video? [Y/n]:
```

### Lần 2 trở đi

```text
Story: truyen-001
Found existing config: stories/truyen-001/config.json
Short mode — only chapter range and optional steps are required.

Last run chapters: 1 -> 10
Start chapter: 11
End chapter: 20
Crawl & Clean? [Y/n]:
Generate Audio? [Y/n]:
Crawling Title? [Y/n]:
Generate Video? [Y/n]:
```

Khi nội dung và tiêu đề dùng cùng URL:

```text
Content URL: https://truyenfull.live/thieu-gia-bi-bo-roi/
Title URL: https://truyenfull.live/thieu-gia-bi-bo-roi/
```

---

## Lệnh nội bộ được gọi (tham khảo)

Crawl nội dung:

```bash
node craw/crawl.js \
  --story "$STORY" \
  --start "$START" \
  --end "$END" \
  --url "$CONTENT_URL" \
  --selector "$CRAW_SELECTOR"
```

Crawl tiêu đề:

```bash
node craw/crawl_title.js \
  --url "$TITLE_URL" \
  --story "$STORY" \
  --selector "$CRAW_TITLE_SELECTOR"
```

---

## Lưu ý

- Cần có sẵn file giọng mẫu và ảnh bìa trước lần chạy đầu
- Không ghi đè `stories/<Story>/voice/reference.wav` hoặc `cover.*` nếu đã tồn tại
- `0.txt` (phần giới thiệu) chỉ hỏi nhập lần đầu khi chưa có file
- Chế độ rút gọn yêu cầu đã có `cover.*` và `voice/reference.wav`
