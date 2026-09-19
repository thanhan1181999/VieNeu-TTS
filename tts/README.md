# VieNeu-TTS — Hướng dẫn TTS / tạo video

Các script trong thư mục `tts` dùng để sinh âm thanh (WAV) từ văn bản chương, rồi ghép ảnh tĩnh + audio thành video (MP4).

Nên chạy lệnh từ **thư mục gốc của repo**.

---

## Cấu trúc thư mục cần có

```text
stories/<story_id>/
  ├── script/           # văn bản từng chương (1.txt, 2.txt, ...)
  ├── voice/
  │   └── reference.wav # giọng mẫu (clone)
  ├── audio/            # output TTS (1.wav, 2.wav, ...)
  ├── titles.txt        # danh sách tiêu đề chương (phụ đề video)
  ├── cover.jpeg        # ảnh bìa (tuỳ chọn)
  └── config.json       # tuỳ chọn (voice / script_dir / audio_dir, ...)
```

Luồng khuyến nghị:

1. `make_audio.py` — text → WAV
2. `make_video_ver4.py` — WAV + ảnh → MP4

---

## 1. `make_audio.py` — Sinh âm thanh (TTS)

Đọc từng file `.txt` trong `script/`, dùng VieNeu (ONNX INT8, tối ưu Apple Silicon) để tạo `audio/<số_chương>.wav`. Giọng tham chiếu được cache tại `cache/reference.npz`.

### Lệnh cơ bản

```bash
uv run python tts/make_audio.py stories/truyen-001
```

Mặc định khi không truyền thêm tham số: **`mode=v3nano`**, **`steps=6`**, **`precision=int8`**, **`batch-size=8`**, **`max-chars=512`** (ưu tiên tốc độ).

### Tham số CLI

| Tham số | Ý nghĩa | Mặc định |
|---|---|---|
| `story` | Thư mục truyện (ví dụ: `stories/truyen-001`) | bắt buộc (trừ khi dùng `--all`) |
| `--all` | Xử lý mọi thư mục trong `stories/` | tắt |
| `--only FILE ...` | Chỉ các file chỉ định (stem, ví dụ: `1` `2`) | tất cả |
| `--start N` | Chương bắt đầu (1-based, theo vị trí trong danh sách `script` đã sort) | đầu danh sách |
| `--end N` | Chương kết thúc (1-based, inclusive) | cuối danh sách |
| `--force` | Tạo lại cả file WAV đã có | tắt (bỏ qua file đã tồn tại) |
| `--batch-size N` | Kích thước batch | `8` |
| `--max-chars N` | Số ký tự tối đa mỗi chunk | `512` |
| `--mode` | `v3nano` / `v3turbo` | `v3nano` |
| `--steps N` | Số bước Euler sampling (càng nhỏ càng nhanh) | `6` |

### Ví dụ

Dùng mô hình Turbo:

```bash
uv run python tts/make_audio.py stories/truyen-001 --mode v3turbo
```

Giảm steps để tăng tốc:

```bash
uv run python tts/make_audio.py stories/truyen-001 --steps 6
```

Chỉ một khoảng chương:

```bash
uv run python tts/make_audio.py stories/truyen-001 --start 102 --end 120
```

Toàn bộ truyện trong `stories/`:

```bash
uv run python tts/make_audio.py --all
```

Ép tạo lại WAV đã có:

```bash
uv run python tts/make_audio.py stories/truyen-001 --force
```

Tổ hợp thường dùng trong pipeline:

```bash
uv run python tts/make_audio.py stories/truyen-001 \
  --mode v3turbo --max-chars 512 --batch-size 16 --steps 8 \
  --start 102 --end 102
```

### Điều kiện cần

- `stories/<id>/voice/reference.wav` (hoặc đường dẫn trong `config.json` → `voice`)
- `stories/<id>/script/*.txt`

Nếu WAV đã tồn tại và không có `--force`, chương đó sẽ được bỏ qua.

---

## 2. `make_video_ver4.py` — Tạo video (ffmpeg)

Nối các file WAV trong khoảng chương, ghép với ảnh bìa (hoặc nền đen) và phụ đề tiêu đề chương thành MP4.

### Lệnh cơ bản

```bash
uv run python tts/make_video_ver4.py <STORY_ID> <START_CH> <END_CH>
```

Ví dụ:

```bash
uv run python tts/make_video_ver4.py truyen-001 1 50
```

| Tham số | Ý nghĩa |
|---|---|
| `STORY_ID` | Tên thư mục trong `stories/` (không kèm đường dẫn) |
| `START_CH` | Số chương bắt đầu |
| `END_CH` | Số chương kết thúc (inclusive) |

### Đầu vào cần có

| Đường dẫn | Bắt buộc | Mô tả |
|---|---|---|
| `stories/<id>/audio/<chương>.wav` | Có | Phải đủ mọi chương trong khoảng |
| `stories/<id>/titles.txt` | Có | Mỗi dòng là tiêu đề; chỉ số dòng tương ứng số chương |
| `stories/<id>/cover.jpeg` | Không | Thiếu thì dùng nền đen |

Các file WAV phải cùng channels / sample width / sample rate.

### Cách hoạt động

- Độ phân giải `1280x720`, encode ảnh tĩnh (`libx264` + AAC `128k`)
- Phụ đề lấy từ tiêu đề từng chương trong `titles.txt` (chữ trắng, phía dưới)
- Trước khi tạo video, kiểm tra số file từ `0.wav` đến file wav số lớn nhất phải bằng số dòng `titles.txt`. Không khớp thì dừng với lỗi validate
- Nếu tổng thời lượng **> 11 giờ 30 phút** thì tự tách thành nhiều phần
  - Tên file luôn là `<story_id>_partN.mp4`
  - Không tạo lại part đã có; lần sau đánh số tiếp từ part còn thiếu
- File tạm (concat list / SRT) được xóa sau khi xong

### Phụ thuộc

- Máy đã cài `ffmpeg`

---

## Chạy nối tiếp (ví dụ)

```bash
# 1) Sinh audio
uv run python tts/make_audio.py stories/truyen-001 --mode v3turbo --start 1 --end 50

# 2) Lấy titles (nếu chưa có)
node craw/crawl_title.js --url "<url-truyện>" --story truyen-001

# 3) Tạo video
uv run python tts/make_video_ver4.py truyen-001 1 50
```
