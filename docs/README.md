# Auto Story Video Generator

Tự động hóa toàn bộ quy trình tải truyện, tạo giọng đọc (TTS) và tổng hợp video đọc truyện hoàn chỉnh để đăng YouTube chỉ với **1 dòng lệnh**.

---

## 📋 Quy trình chuẩn bị (4 bước)

### Bước 1: Lấy link truyện
1. Truy cập [TruyenFull Live](https://truyenfull.live/) và tìm bộ truyện bạn muốn làm video.
2. Sao chép **2 URL** (có thể giống nhau):
   * **Content URL** — dùng crawl nội dung chương
   * **Title URL** — dùng crawl danh sách tiêu đề chương
   * **Output:** *(Ví dụ: `https://truyenfull.live/thieu-gia-bi-bo-roi/`)*
3. (Tuỳ chọn) Ghi nhớ CSS selector nếu site khác mặc định:
   * Nội dung: `#chapter-c`
   * Tiêu đề: `#list-chapter ul.list-chapter`

Chi tiết tham số: [run_interact_with_user.vi.md](./run_interact_with_user.vi.md) / [run_interact_with_user.ja.md](./run_interact_with_user.ja.md)

---

### Bước 2: Tạo ảnh bìa (Thumbnail / Cover)
1. Sử dụng **ChatGPT** hoặc **Gemini** để tạo ảnh minh họa phù hợp với cốt truyện.
   * **Prompt gợi ý:**
     > *"Mình đang muốn tạo 1 ảnh làm avatar/thumbnail cho video audio truyện: [DÁN_LINK_TRUYỆN]. Hãy ghi thêm vào trong ảnh 1 câu ngắn thu hút người xem nhé."*
2. Tải ảnh về máy tính.
   * **Output:** Đường dẫn lưu file ảnh trên máy local *(Ví dụ: `/path/to/cover.jpg`)*

---

### Bước 3: Chuẩn bị giọng đọc mẫu (Voice Sample)
1. Ghi âm giọng đọc của chính bạn hoặc tải một file âm thanh mẫu (.mp3) từ trên mạng về máy.
   * **Output:** Đường dẫn lưu file `.mp3` trên máy local *(Ví dụ: `/path/to/voice_sample.mp3`)*

---

### Bước 4: Chạy Script tự động
Mở Terminal và thực thi lệnh sau:
```bash
./run_interact_with_user.sh
```
- **Lần đầu** (truyện mới): nhập đầy đủ URL, selector, voice, cover, …
- **Lần sau**: chỉ cần `Story` + khoảng chương + chọn bước chạy; cấu hình nằm trong `stories/<Story>/config.json`

bước 5: ghép text truyện thành từng phần txt giống các phần trong video, upload lên notebookLM
uv run python upload/concat_story.py

bước 6: để upload video lên youtube, chuẩn bị title và description cho mỗi video đã tạo, xác định tags dùng chung cho tất cả video 
lên notebookLM gõ promt theo ví dụ

promt ví dụ: 
```
bối cảnh: hiện tại mình muốn đăng video audio truyện lên youtube
yêu cầu 1: với mỗi phần truyện, hãy gợi ý mình cách điền thông tin title và descrition một cách hấp dẫn người nghe nhất (tức là với x phần thì có x title và x description)
format file title_and_desscription có dạng:
Tập 1: xxx
Tiêu đề YouTube: AUDIO Truyện Dị Giới | xxx
Mô tả (Description): xxx

Tập 2: xxx
Tiêu đề YouTube: AUDIO Truyện Dị Giới | xxx
Mô tả (Description): xxx

Tập 3: xxx
Tiêu đề YouTube: AUDIO Truyện Dị Giới | xxx
Mô tả (Description): xxx

Tập 4: xxx
Tiêu đề YouTube: AUDIO Truyện Dị Giới | xxx
Mô tả (Description): xxx

yêu cầu 2: tạo các tag cần đánh vào các video để thu hút nhiều người hơn
format file tag có dạng
#tag_1, #tag_2, ...
```

bước 7: chạy file upload_youtube.py
trước khi chạy cần đổi tên các file mp4 (xoá thông tin chương ở giữa)

bước 8: chuẩn bị 1 ảnh bìa chính, chạy script để tạo ảnh bìa cho mỗi video

bước 9: thêm tay thủ công ảnh thumbnail + tạo playlist