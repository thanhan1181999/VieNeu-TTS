# Hướng dẫn dùng `run_interact_from_file.sh`

Script chạy tương tác, tự động hóa chuỗi xử lý: chia file truyện TXT theo chương → làm sạch text → tạo TTS → tạo video → upload YouTube. **Không** crawl từ website.

Nên chạy từ **thư mục gốc của repository**. Lần đầu cần cấp quyền thực thi.

```bash
chmod +x run_interact_from_file.sh
./run_interact_from_file.sh
```

Luồng crawl từ web vẫn dùng `run_interact_with_user.sh`.

---

## Chế độ chạy

| Tình huống | Chế độ | Cần nhập |
|---|---|---|
| Chưa có `stories/<Story>/` (truyện mới) | Đầy đủ | Path file TXT, voice, cover, … |
| Đã có `stories/<Story>/config.json` (lần 2+) | Rút gọn | Story + Start/End + bật/tắt từng bước |
| Có thư mục nhưng chưa có `config.json` (truyện cũ) | Chuyển tiếp | Có `source.txt` thì dùng luôn; chưa có thì hỏi path TXT một lần |

Sau lần chạy đầu, cấu hình được lưu vào `stories/<Story>/config.json`. Từ lần sau không hỏi lại cover / voice / `source.txt`.

File TXT gốc lần đầu bị **move** và đổi tên thành `stories/<Story>/source.txt`. Nếu `source.txt` đã có thì dùng lại, không ghi đè.

---

## Lần đầu (truyện mới)

| Mục | Bắt buộc | Mặc định | Mô tả |
|---|---|---|---|
| `Story` | Có | — | Tên thư mục truyện (`stories/<Story>/`) |
| `Start chapter` | Có | — | Chương bắt đầu cho TTS / video |
| `End chapter` | Có | — | Chương kết thúc cho TTS / video |
| `Story TXT file path` | Có | — | File gốc chứa toàn bộ chương; được move thành `source.txt` |
| `Voice path` | Không | `stories/voices/reference.wav` | File giọng mẫu (copy vào `voice/reference.wav`) |
| `Image cover file path` | Có | — | Ảnh bìa (move thành `cover.<đuôi>`) |

Tiếp theo, chọn có chạy từng bước hay không (`Y/n`):

| Mục | Mặc định | Xử lý tương ứng |
|---|---|---|
| `Split story?` | Yes | `craw/split_story.js` (chia toàn bộ file; không dùng Start/End) |
| `Clean?` | Yes | `craw/clean1.js` |
| `Generate Audio?` | Yes | `tts/make_audio.py` (chỉ Start–End) |
| `Generate Video?` | Yes | `tts/make_video_ver4.py` |
| `Add episode_label?` | Yes | Vẽ chữ «Tập N» góc trên trái (chỉ hỏi khi Generate Video = Yes) |
| `Upload YouTube?` | Yes | `upload/upload_youtube_ver1.py` (hỏi riêng, không phụ thuộc Generate Video) |

**Không có bước Crawling Title.** Tiêu đề chương được ghi vào `titles.txt` lúc chia file.

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
| `Start chapter` / `End chapter` | Khoảng chương lần này cho TTS / video |
| Bật/tắt từng bước | Mặc định theo lần trước; Enter để giữ nguyên |

`source.txt`, cover, voice, title / description / tags YouTube lấy từ `config.json` — không hỏi lại. Thiếu `source.txt` thì báo lỗi.

`Generate Video?` và `Upload YouTube?` chọn độc lập.

---

## Định dạng file TXT gốc

Dòng tiêu đề chương phải **đứng một dòng riêng** và **bắt buộc có dấu hai chấm** `:`. Không phân biệt hoa/thường. Khoảng trắng và số 0 đầu được chấp nhận.

```text
(phần giới thiệu đầu file sẽ bị bỏ)

Chương 1: tiêu đề A
nội dung…

Chương 2: tiêu đề B
nội dung…

CHƯƠNG  03 : tiêu đề C
nội dung…
```

Quy tắc:

- Bắt buộc bắt đầu từ Chương 1 và liền mạch 1, 2, 3, … — thiếu / nhảy / trùng số thì lỗi
- `Chương 01` thành `1.txt` (bỏ số 0 đầu)
- Text trước Chương 1 bị bỏ. Nếu chưa có `script/0.txt` thì vẫn hỏi nhập giới thiệu như luồng cũ
- Mỗi `N.txt` giữ dòng heading + nội dung (TTS đọc cả tên chương)
- Chương không có body vẫn tạo file chỉ gồm heading
- Text sau chương cuối thuộc chương cuối
- Chia **toàn bộ** file. Start/End chỉ dùng cho TTS và video

---

## `titles.txt`

```text
Giới Thiệu Truyện
Chương 1: tiêu đề A
Chương 2: tiêu đề B
```

- Dòng 1 cố định `Giới Thiệu Truyện` (giống crawl web)
- Các dòng sau giữ nguyên dòng heading trong file gốc
- Nếu `titles.txt` đã có thì **không cập nhật** (thêm chương vào `source.txt` cũng không làm file này dài hơn, trừ khi xóa rồi chạy Split lại)

`script/N.txt` đã tồn tại thì skip, không ghi đè.

---

## Ví dụ `config.json`

```json
{
  "source_txt": "stories/truyen-001/source.txt",
  "last_start": "1",
  "last_end": "10",
  "split_story": true,
  "clean": true,
  "generate_audio": true,
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

Script này **không xóa** các field sẵn có như `content_url`. Nếu cùng Story từng chạy luồng crawl web, URL vẫn được giữ.

Mỗi lần chạy xong, script cập nhật `last_start` / `last_end` và các cờ bước.

---

## Luồng chạy

1. Hỏi tên Story → phân loại mới / rút gọn / chuyển tiếp
2. Nhập các mục cần thiết và in lại cấu hình
3. Lần đầu: move file TXT thành `source.txt`; lưu (hoặc cập nhật) `config.json`
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

Bước 5 chỉ chạy khi `Upload YouTube` = Yes. `Generate Video` = No vẫn upload được nếu folder đã có mp4.

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

Nếu `config.json` thiếu trường, script hỏi bổ sung rồi lưu. Cần có `upload/client_secret.json` cho OAuth. Lần đầu mở trình duyệt xác thực, lưu token vào `upload/token.json`; lần sau dùng lại và tự refresh.

---

## Ví dụ nhập

### Lần đầu

```text
Story: truyen-001
Start chapter: 1
End chapter: 10
Story TXT file path: /path/to/full-story.txt
Voice path [stories/voices/reference.wav]:
Image cover file path (required): /path/to/cover.jpg
Split story? [Y/n]:
Clean? [Y/n]:
Generate Audio? [Y/n]:
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
Split story? [Y/n]:
Clean? [Y/n]:
Generate Audio? [Y/n]:
Generate Video? [Y/n]:
Add episode_label? [Y/n]:
Upload YouTube? [Y/n]:
```

---

## Lệnh nội bộ được gọi (tham khảo)

Chia file TXT:

```bash
node craw/split_story.js --story "$STORY"
```

Tùy chọn chỉ định file nguồn trực tiếp:

```bash
node craw/split_story.js \
  --story "$STORY" \
  --source /path/to/story.txt
```

Upload YouTube:

```bash
uv run python upload/upload_youtube_ver1.py --story "$STORY" --thumbnail "$THUMBNAIL_PATH" --label-position "$REVIEW_LABEL_POSITION"
```

---

## Lưu ý

- Cần có sẵn file giọng mẫu, ảnh bìa và file TXT đủ chương trước lần chạy đầu
- File TXT gốc bị **move**, không copy. Muốn giữ bản gốc thì copy trước
- Không ghi đè `stories/<Story>/voice/reference.wav`, `cover.*` hoặc `source.txt` nếu đã tồn tại
- `0.txt` (phần giới thiệu) chỉ hỏi nhập lần đầu khi chưa có file. Đoạn text trước Chương 1 trong file TXT không được dùng
- Chế độ rút gọn yêu cầu đã có `cover.*`, `voice/reference.wav` và `source.txt`
- `titles.txt` đã có thì không tự cập nhật khi thêm chương vào `source.txt`. Muốn cập nhật thì xóa `titles.txt` rồi chạy Split lại
- Khi upload cần file thumbnail; mặc định là `stories/<Story>/thumbnail.jpeg`
- Video được đăng private rồi lên lịch công khai lúc 20:00 giờ Việt Nam; mỗi tập cách nhau 1 ngày
- Kênh YouTube có thể cần xác minh (xác thực điện thoại) mới lên lịch được
- Giới hạn bình luận (chỉ người đăng ký) đặt trên YouTube Studio; API không hỗ trợ
