import sys
import os
import subprocess


def get_duration(file_path):
    """Lấy thời lượng âm thanh (giây) bằng ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def format_srt_time(seconds):
    """Định dạng thời gian chuẩn SRT (HH:MM:SS,mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def main():
    if len(sys.argv) < 4:
        print("Cú pháp: python3 make_video.py <STORY_ID> <START_CH> <END_CH>")
        sys.exit(1)

    story_id = sys.argv[1]
    start_ch = int(sys.argv[2])
    end_ch = int(sys.argv[3])

    story_dir = os.path.join("stories", story_id)
    audio_dir = os.path.join(story_dir, "audio")
    titles_file = os.path.join(story_dir, "titles.txt")
    cover_file = os.path.join(story_dir, "cover.jpeg")
    mp3_dir = os.path.join(story_dir, "mp3_temp")
    output_file = os.path.join(story_dir, f"{story_id}_ch{start_ch}_to_ch{end_ch}.mp4")

    if not os.path.exists(story_dir):
        print(f"Lỗi: Không tìm thấy thư mục {story_dir}")
        sys.exit(1)

    if not os.path.exists(titles_file):
        print(f"Lỗi: Không tìm thấy {titles_file}")
        sys.exit(1)

    os.makedirs(mp3_dir, exist_ok=True)

    with open(titles_file, "r", encoding="utf-8") as f:
        titles = [line.strip() for line in f if line.strip()]

    concat_list = os.path.join(story_dir, "concat_list.txt")
    srt_file = os.path.join(story_dir, "subtitles.srt")

    current_time = 0.0
    srt_entries = []

    print(f"\n---> Đang xử lý bộ [{story_id}] từ chương {start_ch} đến {end_ch}...")

    with open(concat_list, "w", encoding="utf-8") as concat_f:
        srt_index = 1
        for ch in range(start_ch, end_ch + 1):
            wav_path = os.path.join(audio_dir, f"{ch}.wav")
            mp3_path = os.path.join(mp3_dir, f"{ch}.mp3")

            if not os.path.exists(wav_path):
                print(f"Cảnh báo: Không thấy {wav_path}, bỏ qua.")
                continue

            if not os.path.exists(mp3_path):
                print(f"[{ch}] Đang nén {ch}.wav -> {ch}.mp3 (128kbps)...")
                cmd_convert = [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-i", wav_path,
                    "-codec:a", "libmp3lame", "-b:a", "128k",
                    mp3_path
                ]
                subprocess.run(cmd_convert, check=True)

            abs_mp3 = os.path.abspath(mp3_path).replace("\\", "/")
            concat_f.write(f"file '{abs_mp3}'\n")

            duration = get_duration(mp3_path)
            title = titles[ch] if ch < len(titles) else f"Chương {ch}"

            start_str = format_srt_time(current_time)
            end_str = format_srt_time(current_time + duration)
            srt_entries.append(f"{srt_index}\n{start_str} --> {end_str}\n{title}\n\n")

            current_time += duration
            srt_index += 1

    with open(srt_file, "w", encoding="utf-8") as f:
        f.writelines(srt_entries)

    if os.path.exists(cover_file):
        img_args = ["-loop", "1", "-i", cover_file]
    else:
        print("LƯU Ý: Không tìm thấy cover.jpeg, dùng nền đen mặc định.")
        img_args = ["-f", "lavfi", "-i", "color=c=black:s=1280x720:r=25"]

    print("\n---> Đang tạo Video bằng FFmpeg...")

    # Homebrew ffmpeg không có libass (filter subtitles/drawtext).
    # Mux SRT thành track phụ đề mềm (mov_text) — không cần thư viện thêm.
    cmd_ffmpeg = [
        "ffmpeg", "-y",
        *img_args,
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-i", srt_file,
        "-map", "0:v:0", "-map", "1:a:0", "-map", "2:s:0",
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=vie",
        "-shortest", output_file
    ]

    subprocess.run(cmd_ffmpeg, check=True)

    if os.path.exists(concat_list):
        os.remove(concat_list)
    if os.path.exists(srt_file):
        os.remove(srt_file)

    print(f"\n=== HOÀN THÀNH! Video xuất ra tại: {output_file} ===")


if __name__ == "__main__":
    main()
