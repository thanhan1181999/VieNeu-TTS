# Hướng dẫn dùng `run_interact_with_user.sh`

Script chạy tương tác, tự động hóa chuỗi xử lý: crawl truyện → làm sạch text → tạo TTS → crawl tiêu đề chương → tạo video → upload YouTube.

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
| `Add episode_label?` | Yes | Vẽ chữ «Tập N» góc trên trái (chỉ hỏi khi Generate Video = Yes) |
| `Upload YouTube?` | Yes | `upload/upload_youtube_ver1.py` (hỏi riêng, không phụ thuộc Generate Video) |

Nếu `Upload YouTube?` = Yes và `config.json` chưa có các trường dưới đây, script hỏi thêm một lần rồi lưu; lần sau không hỏi lại.

| Mục | Bắt buộc | Mặc định | Mô tả |
|---|---|---|---|
| `YouTube title` | Có | — | Dùng chung cho mọi video; cuối title thêm ` ( Phần N)` |
| `YouTube description` | Có | — | Dùng chung cho mọi video; nhét vào template có sẵn (nhiều dòng, Ctrl+D để xong) |
| `Tên truyện (description_story_name)` | Có | — | Tên truyện ở đầu description |
| `Tác giả` | Có | — | Tác giả |
| `Thể loại` | Có | — | Thể loại |
| `Tags` | Có | — | Phân tách bằng dấu phẩy (`#` tùy chọn) |
| `Playlist ID` | Không | `PLerSSQqUz9Wc` | Playlist sẽ gắn video |
| `Thumbnail path` | Không | `stories/<Story>/thumbnail.jpeg` | Ảnh thumbnail YouTube |
| `Label position` | Không | `top_left` | Vị trí chữ «Tập N»: `top_left` / `middle_left` / `bottom_left` |

---

## Lần sau (chế độ rút gọn)

| Mục | Mô tả |
|---|---|
| `Story` | Tên thư mục đã có `config.json` |
| `Start chapter` / `End chapter` | Khoảng chương lần này |
| Bật/tắt từng bước | Mặc định theo lần trước; Enter để giữ nguyên |

URL, selector, cover, voice, title / description / tags YouTube lấy từ `config.json` — không hỏi lại.

`Generate Video?` và `Upload YouTube?` chọn độc lập. Có thể chỉ tạo video, chỉ upload mp4 có sẵn, làm cả hai, hoặc bỏ cả hai.

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
  "generate_video": true,
  "add_episode_label": true,
  "upload_youtube": true,
  "youtube_title": "AUDIO Truyện Dị Giới | Example",
  "youtube_description": "Đoạn giới thiệu truyện",
  "description_story_name": "Example",
  "author": "Tên tác giả",
  "genre": "Thể loại",
  "tags": "#tag1, #tag2",
  "playlist_id": "PLerSSQqUz9Wc",
  "privacy_status": "private",
  "thumbnail_path": "stories/truyen-001/thumbnail.jpeg",
  "review_label_position": "top_left"
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

## Cách tạo video theo part

`tts/make_video_ver4.py` gom chương thành từng part sao cho không vượt khoảng 11 giờ 30 phút.

- Tên file luôn là `stories/<Story>/<Story>_partN.mp4`
- Part đã tạo xong (có cả `.mp4` và `.json`) **không tạo lại**
- Lần chạy sau chỉ xử lý chương chưa có trong part cũ, đánh số tiếp từ part tiếp theo

---

## Upload YouTube

Bước 6 chỉ chạy khi `Upload YouTube` = Yes. `Generate Video` = No vẫn upload được nếu folder đã có mp4.

- Gọi `upload/upload_youtube_ver1.py --story "$STORY" --thumbnail "$THUMBNAIL_PATH" --label-position "$REVIEW_LABEL_POSITION"`
- Quét mọi file `<Story>_partN.mp4` trong `stories/<Story>/`
- Title giống nhau, chỉ khác hậu tố ` ( Phần N)`
- Description giống nhau cho mọi video (template + đoạn mô tả hỏi lúc đầu)
- Thumbnail lấy đường dẫn hỏi lúc đầu (mặc định: `stories/<Story>/thumbnail.jpeg`)
- Mỗi part được tạo `review_partN.jpeg` (chữ «Tập N») rồi dùng làm thumbnail YouTube. Vị trí chữ: `top_left` / `middle_left` / `bottom_left`
- Video luôn ở chế độ `private` và gắn `publishAt` để công khai lúc 20:00 giờ Việt Nam
- Tập chưa đăng đầu tiên: 20:00 tối nay (giờ VN). Nếu đã quá 20:00 thì chuyển sang 20:00 ngày mai
- Tập sau đăng sau tập trước đúng 1 ngày (cùng giờ 20:00)
- Nếu lần trước đã có `publish_at` trong log, lần này tiếp tục từ ngày hôm sau của lịch cũ (không trùng ngày)
- Part đã đăng được ghi vào `stories/<Story>/upload_log.json`; lần sau bỏ qua
- Một tập lỗi thì vẫn tiếp tục các tập còn lại

Chạy độc lập:

```bash
uv run python upload/upload_youtube_ver1.py --story <Story>
```

Nếu `config.json` thiếu trường, script hỏi bổ sung rồi lưu. Cần có `upload/client_secret.json` cho OAuth.

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
Add episode_label? [Y/n]:
Upload YouTube? [Y/n]:
YouTube title: AUDIO Truyện Dị Giới | Example
YouTube description:
(Enter xuống dòng, Ctrl+D để hoàn tất)
Tên truyện (description_story_name): Example
Tác giả: Tên tác giả
Thể loại: Tiên hiệp
Tags (phân tách bằng dấu phẩy): #tag1, #tag2
Playlist ID [PLerSSQqUz9Wc]:
Thumbnail path [stories/truyen-001/thumbnail.jpeg]:
Chọn [1/2/3, mặc định top_left]:
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
Add episode_label? [Y/n]:
Upload YouTube? [Y/n]:
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

Upload YouTube:

```bash
uv run python upload/upload_youtube_ver1.py --story "$STORY" --thumbnail "$THUMBNAIL_PATH" --label-position "$REVIEW_LABEL_POSITION"
```

---

## Lưu ý

- Cần có sẵn file giọng mẫu và ảnh bìa trước lần chạy đầu
- Không ghi đè `stories/<Story>/voice/reference.wav` hoặc `cover.*` nếu đã tồn tại
- `0.txt` (phần giới thiệu) chỉ hỏi nhập lần đầu khi chưa có file
- Chế độ rút gọn yêu cầu đã có `cover.*` và `voice/reference.wav`
- Khi upload cần file thumbnail; mặc định là `stories/<Story>/thumbnail.jpeg`
- Video được đăng private rồi lên lịch công khai lúc 20:00 giờ Việt Nam; mỗi tập cách nhau 1 ngày
- Kênh YouTube có thể cần xác minh (xác thực điện thoại) mới lên lịch được
- Giới hạn bình luận (chỉ người đăng ký) đặt trên YouTube Studio; API không hỗ trợ
