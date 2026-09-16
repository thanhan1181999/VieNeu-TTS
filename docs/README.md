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
cd projects/vieneu-test/VieNeu-TTS
./run_interact_with_user.sh
```

- **Lần đầu** (truyện mới): nhập đầy đủ URL, selector, voice, cover, …
- **Lần sau**: chỉ cần `Story` + khoảng chương + chọn bước chạy; cấu hình nằm trong `stories/<Story>/config.json`

bước 5: để upload video lên youtube, chuẩn bị title và description cho mỗi video đã tạo, xác định tags dùng chung cho tất cả video 
lên chatgpt hoặc gemini gõ promt theo ví dụ
copy nội dung trả về theo từng file vào thư mục truyện, đặt tên mỗi file là phan_1_title.txt, phan_1_script.txt
output: 2 file phan_1_title.txt, phan_1_script.txt với mỗi phần truyện; và 1 file chung là tags.txt

promt ví dụ: 
bối cảnh: hiện tại mình muốn đăng video audio truyện lên youtube

yêu cầu 1: vì vậy, với mỗi phần truyện, hãy gợi ý mình cách điền thông tin title và descrition một cách hấp dẫn người nghe nhất (tức là với 34 phần thì có 34 title và 34 description)

yêu cầu 2: tạo các tag cần đánh vào các video để thu hút nhiều người hơn

phần 1: Chương 1 -> Chương 95
phần 2: Chương 96 -> Chương 166
phần 3: Chương 167 -> Chương 238
phần 4: Chương 239 -> Chương 309
phần 5: Chương 310 -> Chương 380
phần 6: Chương 381 -> Chương 451
phần 7: Chương 452 -> Chương 520
phần 8: Chương 521 -> Chương 590
phần 9: Chương 591 -> Chương 659
phần 10: Chương 660 -> Chương 729
phần 11: Chương 730 -> Chương 798
phần 12: Chương 799 -> Chương 867
phần 13: Chương 868 -> Chương 938
phần 14: Chương 939 -> Chương 1007
phần 15: Chương 1008 -> Chương 1075
phần 16: Chương 1076 -> Chương 1141
phần 17: Chương 1142 -> Chương 1206
phần 18: Chương 1207 -> Chương 1272
phần 19: Chương 1273 -> Chương 1337
phần 20: Chương 1338 -> Chương 1403
phần 21: Chương 1404 -> Chương 1468
phần 22: Chương 1469 -> Chương 1535
phần 23: Chương 1536 -> Chương 1600
phần 24: Chương 1601 -> Chương 1666
phần 25: Chương 1667 -> Chương 1729
phần 26: Chương 1730 -> Chương 1794
phần 27: Chương 1795 -> Chương 1859
phần 28: Chương 1860 -> Chương 1925
phần 29: Chương 1926 -> Chương 1992
phần 30: Chương 1993 -> Chương 2061
phần 31: Chương 2062 -> Chương 2130
phần 32: Chương 2131 -> Chương 2199
phần 33: Chương 2200 -> Chương 2266
phần 34: Chương 2267 -> Chương 2271

bước 6: chạy file upload_youtube.py
