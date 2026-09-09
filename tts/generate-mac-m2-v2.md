Cách chạy cơ bản vẫn **giữ nguyên như cũ**, nhưng file cập nhật mới đã hỗ trợ thêm một số tham số (CLI arguments) giúp bạn linh hoạt điều chỉnh tốc độ và mô hình ngay từ dòng lệnh.

**1. Lệnh chạy mặc định (Giữ nguyên như cũ):**

```bash
python tts/generate-mac-m2-v1.py stories/truyen-001

```

*Lưu ý:* Khi chạy lệnh này, script sẽ mặc định áp dụng chế độ tối ưu nhất (**`mode="v3nano"`**, **`steps=8`**, **`precision="int8"`**) để tạo voice nhanh nhất.

---

**2. Các lệnh chạy tùy chỉnh bổ sung (Mới):**

* **Chọn mô hình Turbo thay vì Nano:**
```bash
python tts/generate-mac-m2-v1.py stories/truyen-001 --mode v3turbo

```


* **Chỉnh số bước Euler sampling (Mặc định là 8, hạ xuống giúp tăng tốc hơn nữa):**
```bash
python tts/generate-mac-m2-v1.py stories/truyen-001 --steps 6

```


* **Chạy toàn bộ các truyện trong thư mục `stories/`:**
```bash
python tts/generate-mac-m2-v1.py --all

```


* **Ép tạo lại các file âm thanh đã tồn tại:**
```bash
python tts/generate-mac-m2-v1.py stories/truyen-001 --force

```