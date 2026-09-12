# Luồng tạo video nghe truyện (fork)

Repo này **fork** từ dự án TTS [pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS). Phần model, SDK và Web UI gốc vẫn giữ nguyên.

## Mục tiêu

Dùng model VieNeu-TTS để chạy **một lệnh** — từ tải truyện đến file video nghe truyện (một ảnh tĩnh + âm thanh các chương).

## Hiện trạng

Chạy `./run.sh` sẽ lần lượt:

1. **Tải truyện** từ nguồn (mặc định [truyenfull.live](https://truyenfull.live)) rồi lưu từng chương vào `stories/truyen-xxx/script/`.
2. **Làm sạch** nội dung chương (`craw/clean1.js`).
3. **Chuyển từng chương thành file âm thanh** bằng model VieNeu-TTS (`tts/generate-mac-m2-v2.py`, mode `v3turbo`).
4. **Tạo video** bằng ffmpeg: **một ảnh** + các file nghe truyện.

Cấu trúc thư mục truyện:

```text
stories/truyen-xxx/
  script/          # văn bản từng chương (sau crawl)
  voice/           # file giọng mẫu (reference.wav)
  audio/           # WAV từng chương (sau TTS)
  output/          # narration / video (sau ghép)
```

## Chạy một lệnh

```bash
./run.sh <tên-truyện> <chương-bắt-đầu> <chương-kết-thúc> "<url-truyện>"
```

Ví dụ:

```bash
./run.sh truyen-001 102 102 "https://truyenfull.live/thieu-gia-bi-bo-roi"
```

Tham số mặc định trong `run.sh` nếu không truyền gì:

| Tham số | Mặc định |
| --- | --- |
| Tên thư mục truyện | `truyen-001` |
| Chương bắt đầu / kết thúc | `102` / `102` |
| URL | `https://truyenfull.live/thieu-gia-bi-bo-roi` |

Các bước tương đương nếu chạy tay:

```bash
node craw/crawl.js --story truyen-001 --start 102 --end 102 --url "https://truyenfull.live/thieu-gia-bi-bo-roi"
node craw/clean1.js
uv run python tts/generate-mac-m2-v2.py stories/truyen-001 --mode v3turbo --max-chars 512 --batch-size 16 --steps 8
```

Ghép WAV (tùy chọn, `tts/combine.py`) và encode video ffmpeg (một ảnh + audio) là bước sau TTS.
