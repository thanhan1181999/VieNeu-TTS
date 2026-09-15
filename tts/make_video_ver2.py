#!/usr/bin/env python3

import os
import sys
import subprocess
import wave
from pathlib import Path


VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 1
AUDIO_BITRATE = "128k"


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


def main():
    if len(sys.argv) != 4:
        print(
            f"Usage: python3 {Path(sys.argv[0]).name} "
            "<STORY_ID> <START_CH> <END_CH>"
        )
        sys.exit(1)

    story_id = sys.argv[1]
    start_ch = int(sys.argv[2])
    end_ch = int(sys.argv[3])

    story_dir = Path("stories") / story_id
    audio_dir = story_dir / "audio"
    titles_file = story_dir / "titles.txt"
    cover_file = story_dir / "cover.jpeg"
    concat_list = story_dir / "concat_list.txt"
    srt_file = story_dir / "subtitles.srt"
    output_file = story_dir / f"{story_id}_{start_ch}_{end_ch}.mp4"

    if not audio_dir.exists():
        print(f"ERROR: Audio directory not found: {audio_dir}")
        sys.exit(1)

    if not titles_file.exists():
        print(f"ERROR: titles.txt not found: {titles_file}")
        sys.exit(1)

    with open(titles_file, "r", encoding="utf-8") as f:
        titles = [line.rstrip("\n\r") for line in f]

    wav_files = []
    metadata = []
    srt_entries = []

    current_time = 0.0
    srt_index = 1

    # Keep the original chapter/title indexing behavior.
    for ch in range(start_ch, end_ch + 1):
        wav_file = audio_dir / f"{ch}.wav"

        if not wav_file.exists():
            print(f"WARNING: Missing WAV, skipping chapter {ch}: {wav_file}")
            continue

        try:
            info = get_wav_metadata(wav_file)
        except Exception as e:
            print(f"ERROR: Cannot read WAV metadata for {wav_file}: {e}")
            sys.exit(1)

        wav_files.append(wav_file)
        metadata.append((wav_file, info))

        title = titles[ch] if ch < len(titles) else f"Chapter {ch}"
        start_time = current_time
        end_time = current_time + info["duration"]

        srt_entries.append(
            f"{srt_index}\n"
            f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}\n"
            f"{title}\n"
        )

        current_time = end_time
        srt_index += 1

    if not wav_files:
        print("ERROR: No WAV files found in the requested chapter range.")
        sys.exit(1)

    # Validate that all WAV files have identical basic audio parameters.
    # This is required for reliable concat-demuxer operation.
    reference = metadata[0][1]
    mismatches = []

    for wav_file, info in metadata[1:]:
        for key in ("channels", "sample_width", "sample_rate", "comptype"):
            if info[key] != reference[key]:
                mismatches.append(
                    f"{wav_file}: {key}={info[key]!r}, "
                    f"expected {reference[key]!r}"
                )

    if mismatches:
        print("\nERROR: WAV files do not have consistent audio parameters.")
        for item in mismatches[:50]:
            print("  " + item)
        if len(mismatches) > 50:
            print(f"  ... and {len(mismatches) - 50} more mismatches")
        print(
            "\nDirect WAV concat was stopped to avoid producing an invalid or "
            "corrupted result."
        )
        sys.exit(1)

    print("\n=== Audio metadata ===")
    print(f"WAV files : {len(wav_files)}")
    print(f"Sample rate: {reference['sample_rate']} Hz")
    print(f"Channels   : {reference['channels']}")
    print(f"Sample width: {reference['sample_width']} bytes")
    print(f"Duration   : {current_time / 3600:.2f} hours")

    # Direct WAV concat. No MP3 intermediate files.
    with open(concat_list, "w", encoding="utf-8") as f:
        for wav_file in wav_files:
            # FFmpeg concat demuxer requires single quotes around paths.
            # Escape backslashes and single quotes for concat syntax.
            path = str(wav_file.resolve())
            path = path.replace("\\", "\\\\").replace("'", "'\\''")
            f.write(f"file '{path}'\n")

    with open(srt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))
        f.write("\n")

    # Image input: one frame per second.
    if cover_file.exists():
        img_args = [
            "-loop", "1",
            "-framerate", str(VIDEO_FPS),
            "-i", str(cover_file),
        ]
    else:
        print(f"WARNING: cover.jpeg not found. Using black background.")
        img_args = [
            "-f", "lavfi",
            "-i", f"color=c=black:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:r={VIDEO_FPS}",
        ]

    # Choice A: force the image to exactly 1280x720.
    # This intentionally allows the tiny aspect-ratio difference of the cover
    # image to be stretched rather than adding bars/cropping.
    subtitle_path = escape_filter_path(srt_file)
    video_filter = (
        f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
        f"subtitles='{subtitle_path}':"
        f"force_style='FontName=Roboto,FontSize=26,Bold=1,"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,"
        f"Outline=3,Shadow=1,MarginV=30'"
    )

    cmd_ffmpeg = [
        "ffmpeg", "-y",
        *img_args,
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-vf", video_filter,
        "-r", str(VIDEO_FPS),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "30",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        # "-shortest",
        "-t", f"{current_time:.3f}", # fix last 69s no music
        str(output_file),
    ]

    try:
        run_command(cmd_ffmpeg)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: FFmpeg failed with exit code {e.returncode}.")
        print(f"Temporary files were kept:")
        print(f"  {concat_list}")
        print(f"  {srt_file}")
        sys.exit(e.returncode)

    # Only remove temporary files after a successful encode.
    concat_list.unlink(missing_ok=True)
    srt_file.unlink(missing_ok=True)

    print("\n=== DONE ===")
    print(f"Output: {output_file}")
    print(f"Size  : {output_file.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
