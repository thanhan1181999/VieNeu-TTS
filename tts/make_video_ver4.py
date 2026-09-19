#!/usr/bin/env python3

import json
import os
import sys
import subprocess
import wave
from pathlib import Path


VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 1
AUDIO_BITRATE = "128k"
THUMBNAIL_PATH = "thumbnail.jpeg"

# Giới hạn độ dài mỗi video: 11 giờ 30 phút = 41400 giây
MAX_DURATION_SECONDS = (11 * 3600) + (30 * 60) 


def get_wav_metadata(file_path):
    """Read WAV metadata from the header without spawning ffprobe."""
    with wave.open(str(file_path), "rb") as wf:
        params = wf.getparams()

    if params.comptype != "NONE":
        raise RuntimeError(
            f"Unsupported WAV compression in {file_path}: {params.comptype}"
        )

    duration = params.nframes / params.framerate if params.framerate else 0.0

    return {
        "duration": duration,
        "channels": params.nchannels,
        "sample_width": params.sampwidth,
        "sample_rate": params.framerate,
        "comptype": params.comptype,
    }


def format_srt_time(seconds):
    total_ms = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def escape_filter_path(path):
    """
    Escape a filesystem path for FFmpeg's subtitles filter.
    """
    value = str(Path(path).resolve())
    value = value.replace("\\", r"\\")
    value = value.replace(":", r"\:")
    value = value.replace("'", r"\'")
    value = value.replace("[", r"\[")
    value = value.replace("]", r"\]")
    value = value.replace(",", r"\,")
    return value


def run_command(cmd):
    print("\nRunning:")
    print(" ".join(f'"{x}"' if " " in str(x) else str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def parse_bool_arg(value):
    normalized = value.strip().lower()
    if normalized in ("true", "yes", "y", "1"):
        return True
    if normalized in ("false", "no", "n", "0"):
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def ask_bool(prompt, default=True):
    suffix = " [Y/n]: " if default else " [y/N]: "

    while True:
        value = input(prompt + suffix).strip().lower()

        if not value:
            return default

        if value in ("y", "yes"):
            return True

        if value in ("n", "no"):
            return False

        print("Please enter y/yes or n/no.")


def main():
    if len(sys.argv) not in (4, 5):
        print(
            f"Usage: python3 {Path(sys.argv[0]).name} "
            "<STORY_ID> <START_CH> <END_CH> [true|false]"
        )
        sys.exit(1)

    story_id = sys.argv[1]
    start_ch = int(sys.argv[2])
    end_ch = int(sys.argv[3])

    if len(sys.argv) == 5:
        try:
            add_episode_label = parse_bool_arg(sys.argv[4])
        except ValueError:
            print("Argument 4 must be true/false (add episode_label).")
            sys.exit(1)
    else:
        add_episode_label = ask_bool("Add episode_label?", default=True)

    story_dir = Path("stories") / story_id
    audio_dir = story_dir / "audio"
    titles_file = story_dir / "titles.txt"
    cover_file = story_dir / "cover.jpeg"

    if not audio_dir.exists():
        print(f"ERROR: Audio directory not found: {audio_dir}")
        sys.exit(1)

    if not titles_file.exists():
        print(f"ERROR: titles.txt not found: {titles_file}")
        sys.exit(1)

    with open(titles_file, "r", encoding="utf-8") as f:
        titles = [line.rstrip("\n\r") for line in f]

    # Validate audio files existence
    missing_wav_files = []
    print("\n=== Checking audio files ===")
    for ch in range(start_ch, end_ch + 1):
        wav_file = audio_dir / f"{ch}.wav"
        if not wav_file.exists():
            print(f"  Chapter {ch}: MISSING")
            missing_wav_files.append((ch, wav_file))
        else:
            print(f"  Chapter {ch}: OK")

    if missing_wav_files:
        print("\nERROR: Missing WAV files in the requested chapter range.")
        sys.exit(1)

    # Read metadata for all requested chapters
    chapters = []
    for ch in range(start_ch, end_ch + 1):
        wav_file = audio_dir / f"{ch}.wav"
        try:
            info = get_wav_metadata(wav_file)
        except Exception as e:
            print(f"ERROR: Cannot read WAV metadata for {wav_file}: {e}")
            sys.exit(1)

        title = titles[ch] if ch < len(titles) else f"Chapter {ch}"
        chapters.append({
            "ch": ch,
            "wav_file": wav_file,
            "info": info,
            "title": title,
            "duration": info["duration"]
        })

    if not chapters:
        print("ERROR: No WAV files found in the requested chapter range.")
        sys.exit(1)

    # Validate audio format consistency across all files
    reference = chapters[0]["info"]
    mismatches = []
    for item in chapters[1:]:
        info = item["info"]
        for key in ("channels", "sample_width", "sample_rate", "comptype"):
            if info[key] != reference[key]:
                mismatches.append(
                    f"{item['wav_file']}: {key}={info[key]!r}, expected {reference[key]!r}"
                )

    if mismatches:
        print("\nERROR: WAV files do not have consistent audio parameters.")
        for item in mismatches[:50]:
            print("  " + item)
        sys.exit(1)

    # Group chapters into parts based on MAX_DURATION_SECONDS (11h30m)
    parts = []
    current_part = []
    current_duration = 0.0

    for ch_data in chapters:
        # If adding this chapter exceeds MAX_DURATION_SECONDS (and part is not empty)
        if current_part and (current_duration + ch_data["duration"] > MAX_DURATION_SECONDS):
            parts.append(current_part)
            current_part = []
            current_duration = 0.0

        current_part.append(ch_data)
        current_duration += ch_data["duration"]

    if current_part:
        parts.append(current_part)

    print(f"\nTotal audio duration: {sum(c['duration'] for c in chapters) / 3600:.2f} hours")
    print(f"Split into {len(parts)} video part(s) (limit <= 11h 30m each).")

    # Image input configuration
    if cover_file.exists():
        img_args = [
            "-loop", "1",
            "-framerate", str(VIDEO_FPS),
            "-i", str(cover_file),
        ]
    else:
        print("WARNING: cover.jpeg not found. Using black background.")
        img_args = [
            "-f", "lavfi",
            "-i", f"color=c=black:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:r={VIDEO_FPS}",
        ]

    # Process each part and generate corresponding video file
    parts_meta = []

    for part_idx, part_chapters in enumerate(parts, start=1):
        first_ch = part_chapters[0]["ch"]
        last_ch = part_chapters[-1]["ch"]

        if len(parts) == 1:
            output_file = story_dir / f"{story_id}_{start_ch}_{end_ch}.mp4"
        else:
            output_file = story_dir / f"{story_id}_{first_ch}_{last_ch}_part{part_idx}.mp4"

        concat_list = story_dir / f"concat_list_p{part_idx}.txt"
        # Giữ cùng tên với video để dễ đối chiếu sau này
        srt_file = output_file.with_suffix(".srt")
        meta_file = output_file.with_suffix(".json")

        print(f"\n==========================================")
        print(f"Processing Part {part_idx}/{len(parts)} (Chapters {first_ch} to {last_ch})")
        print(f"Output: {output_file.name}")
        print(f"==========================================")

        # Build concat list and SRT content for this part
        srt_entries = []
        current_time = 0.0
        srt_index = 1

        with open(concat_list, "w", encoding="utf-8") as f_concat:
            for item in part_chapters:
                path = str(item["wav_file"].resolve()).replace("\\", "\\\\").replace("'", "'\\''")
                f_concat.write(f"file '{path}'\n")

                start_time = current_time
                end_time = current_time + item["duration"]

                srt_entries.append(
                    f"{srt_index}\n"
                    f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}\n"
                    f"{item['title']}\n"
                )

                current_time = end_time
                srt_index += 1

        with open(srt_file, "w", encoding="utf-8") as f_srt:
            f_srt.write("\n".join(srt_entries))
            f_srt.write("\n")

        # FFmpeg command
        # part_idx bắt đầu từ 1 → nhãn tập hiển thị góc trên trái
        subtitle_path = escape_filter_path(srt_file)
        video_filters = [
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}",
        ]

        if add_episode_label:
            episode_label = f"Tập {part_idx}"
            video_filters.extend(
                [
                    (
                        f"drawtext=text='{episode_label}':"
                        f"font='Roboto Bold':"
                        f"fontsize=130:"
                        f"fontcolor=white@0.15:"
                        f"borderw=10:"
                        f"bordercolor=white@0.5:"
                        f"x=36:y=36"
                    ),
                    (
                        f"drawtext=text='{episode_label}':"
                        f"font='Roboto Bold':"
                        f"fontsize=130:"
                        f"fontcolor=white:"
                        f"borderw=5:"
                        f"bordercolor=black:"
                        f"shadowcolor=black@0.35:"
                        f"shadowx=2:"
                        f"shadowy=2:"
                        f"x=36:y=36"
                    ),
                ]
            )

        video_filters.append(
            f"subtitles=filename='{subtitle_path}':"
            f"force_style='FontName=Roboto,FontSize=26,Bold=1,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,"
            f"Outline=3,Shadow=1,MarginV=30'"
        )

        filter_complex = (
            # =========================
            # VIDEO CHÍNH
            # =========================
            f"[0:v]"
            + ",".join(video_filters)
            + f"[main];"

            # =========================
            # THUMBNAIL
            # =========================
            f"[2:v]"
            f"scale=75:75"
            f"[thumb];"

            # Đặt thumbnail góc dưới bên phải
            f"[main][thumb]"
            f"overlay=W-w-30:H-h-30"
        )

        thumbnail_args = [
            "-loop", "1",
            "-i", str(THUMBNAIL_PATH)
        ]

        cmd_ffmpeg = [
            "ffmpeg", "-y",

            *img_args,

            "-f", "concat",
            "-safe", "0",

            "-i", str(concat_list),

            *thumbnail_args,

            "-map", "0:v:0", # lấy video/hình ảnh từ Input 0
            "-map", "1:a:0", # lấy audio từ Input 1
            "-filter_complex", filter_complex,
            "-r", str(VIDEO_FPS),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "30",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", AUDIO_BITRATE,
            "-t", f"{current_time:.3f}",
            str(output_file),
        ]

        try:
            run_command(cmd_ffmpeg)
        except subprocess.CalledProcessError as e:
            print(f"\nERROR: FFmpeg failed with exit code {e.returncode} on Part {part_idx}.")
            sys.exit(e.returncode)

        # Chỉ xóa concat list tạm; giữ srt_file để tra cứu phụ đề theo chương
        concat_list.unlink(missing_ok=True)

        part_meta = {
            "story_id": story_id,
            "part": part_idx,
            "video": output_file.name,
            "srt_file": srt_file.name,
            "first_ch": first_ch,
            "last_ch": last_ch,
            "total_duration": round(current_time, 3),
            "chapters": [
                {
                    "ch": item["ch"],
                    "title": item["title"],
                    "duration": round(item["duration"], 3),
                    "wav_file": item["wav_file"].name,
                }
                for item in part_chapters
            ],
        }

        with open(meta_file, "w", encoding="utf-8") as f_meta:
            json.dump(part_meta, f_meta, ensure_ascii=False, indent=2)

        parts_meta.append(part_meta)

        print(
            f"Finished Part {part_idx}: {output_file.name} "
            f"({output_file.stat().st_size / (1024 * 1024):.2f} MB) "
            f"| chapters {first_ch}-{last_ch} | srt={srt_file.name} | meta={meta_file.name}"
        )

    # Tóm tắt toàn bộ các part đã ghép
    summary_file = story_dir / f"{story_id}_{start_ch}_{end_ch}_parts.json"
    with open(summary_file, "w", encoding="utf-8") as f_summary:
        json.dump(
            {
                "story_id": story_id,
                "start_ch": start_ch,
                "end_ch": end_ch,
                "parts": parts_meta,
            },
            f_summary,
            ensure_ascii=False,
            indent=2,
        )

    print("\n=== ALL PARTS DONE ===")
    print(f"Saved parts summary: {summary_file}")
    for item in parts_meta:
        print(
            f"  Part {item['part']}: video={item['video']} "
            f"chapters={item['first_ch']}-{item['last_ch']} "
            f"srt={item['srt_file']}"
        )


if __name__ == "__main__":
    main()