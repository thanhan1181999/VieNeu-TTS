# Hướng dẫn dùng `run_interact_with_user.sh`

Script chạy tương tác, tự động hóa chuỗi xử lý: crawl truyện → làm sạch text → tạo TTS → crawl tiêu đề chương → tạo video.

Nên chạy từ **thư mục gốc của repository**.

```bash
./run_interact_with_user.sh
```

---

## Các đầu vào

Sau khi chạy, script hỏi lần lượt:

| Mục | Bắt buộc | Mặc định | Mô tả |
|---|---|---|---|
| `Story` | Có | — | Tên thư mục truyện (xuất ra `stories/<Story>/`) |
| `Start chapter` | Có | — | Chương bắt đầu |
| `End chapter` | Có | — | Chương kết thúc |
| `Content URL` | Có | — | URL dùng để **crawl nội dung** (truyền vào `crawl.js`) |
| `Title URL` | Có | — | URL dùng để **crawl tiêu đề chương** (truyền vào `crawl_title.js`) |
| `Crawl selector` | Không | `#chapter-c` | CSS selector nội dung chương (`--selector` của `crawl.js`) |
| `Crawl title selector` | Không | `#list-chapter ul.list-chapter` | CSS selector danh sách tiêu đề (`--selector` của `crawl_title.js`) |
| `Voice path` | Không | `stories/voices/reference.wav` | File giọng mẫu |
| `Image cover file path` | Có | — | Đường dẫn ảnh bìa |

Tiếp theo, chọn có chạy từng bước hay không (`Y/n`):

| Mục | Mặc định | Xử lý tương ứng |
|---|---|---|
| `Crawl & Clean?` | Yes | `crawl.js` → `clean1.js` |
| `Generate Audio?` | Yes | `tts/make_audio.py` |
| `Crawling Title?` | Yes | `crawl_title.js` |
| `Generate Video?` | Yes | `tts/make_video_ver4.py` |

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

1. In lại cấu hình đã nhập
2. Nếu chưa có `stories/<Story>/script/0.txt` thì hỏi nhập phần giới thiệu (Ctrl+D để kết thúc)
3. (Nếu bật) Crawl nội dung + clean
4. (Nếu bật) Sinh audio TTS
5. (Nếu bật) Crawl tiêu đề chương
6. (Nếu bật) Tạo video

---

## Ví dụ nhập

```text
Story: truyen-001
Start chapter: 1
End chapter: 10
Content URL: https://example.com/truyen-a/
Title URL: https://example.com/truyen-a-list/
Crawl selector [#chapter-c]:          ← Enter để dùng mặc định
Crawl title selector [#list-chapter ul.list-chapter]:  ← Enter để dùng mặc định
Voice path [stories/voices/reference.wav]:
Image cover file path (required): /path/to/cover.jpg
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

- Cần có sẵn file giọng mẫu và ảnh bìa trước khi chạy
- Không ghi đè `stories/<Story>/voice/reference.wav` hoặc `cover.*` nếu đã tồn tại
- `0.txt` (phần giới thiệu) chỉ hỏi nhập lần đầu khi chưa có file
