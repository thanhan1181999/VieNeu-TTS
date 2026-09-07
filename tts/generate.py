from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from vieneu import Vieneu
from vieneu.v3turbo import (
    DEFAULT_REP_WINDOW,
    gaps_to_silence,
    join_audio_chunks,
    normalize_to_chunks_v3_with_gaps,
)


# ============================================================
# CONFIG
# ============================================================

DEFAULT_BATCH_SIZE = 8
CACHE_VERSION = 1
DEFAULT_STORY_ROOT = Path("stories")

# Chunk tối đa.
# VieNeu mặc định cũng dùng 256.
MAX_CHARS = 512


# ============================================================
# UTILS
# ============================================================

def natural_key(path: Path):
    """
    Sort:
        001.txt
        002.txt
        010.txt
        100.txt
    thay vì:
        001.txt
        010.txt
        100.txt
        002.txt
    """
    import re

    return [
        int(x) if x.isdigit() else x.lower()
        for x in re.split(r"(\d+)", path.name)
    ]


def load_json(path: Path, default=None):
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


# ============================================================
# REFERENCE CACHE
# ============================================================

def fingerprint_file(path: Path) -> dict[str, Any]:
    """
    Tạo fingerprint nhẹ cho reference.wav.

    Chỉ dùng stat + hash một phần file để phát hiện reference
    thay đổi mà không cần hash toàn bộ file.
    """
    stat = path.stat()

    h = hashlib.sha256()

    with path.open("rb") as f:
        first = f.read(1024 * 1024)
        h.update(first)

        if stat.st_size > 1024 * 1024:
            f.seek(max(0, stat.st_size - 1024 * 1024))
            h.update(f.read(1024 * 1024))

    return {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256_partial": h.hexdigest(),
    }


def cache_path_for_story(story_dir: Path) -> Path:
    return story_dir / "cache" / "reference.npz"


def load_reference_cache(
    cache_path: Path,
    reference_path: Path,
):
    """
    Load cached:
        speaker_emb
        ref_codes

    Trả về None nếu cache không tồn tại hoặc reference đã thay đổi.
    """

    if not cache_path.exists():
        return None

    try:
        data = np.load(cache_path, allow_pickle=False)

        cached_fingerprint = json.loads(
            str(data["fingerprint"])
        )

        current_fingerprint = fingerprint_file(reference_path)

        if cached_fingerprint != current_fingerprint:
            print("Reference cache: MISS (reference changed)")
            return None

        speaker_emb = np.asarray(
            data["speaker_emb"],
            dtype=np.float32,
        )

        ref_codes = np.asarray(
            data["ref_codes"],
            dtype=np.int64,
        )

        return speaker_emb, ref_codes

    except Exception as e:
        print(f"Reference cache: INVALID ({e})")
        return None


def save_reference_cache(
    cache_path: Path,
    reference_path: Path,
    speaker_emb: np.ndarray,
    ref_codes: np.ndarray,
):
    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fingerprint = fingerprint_file(reference_path)

    np.savez_compressed(
        cache_path,
        cache_version=np.array(CACHE_VERSION),
        fingerprint=np.array(
            json.dumps(
                fingerprint,
                ensure_ascii=False,
            )
        ),
        speaker_emb=np.asarray(
            speaker_emb,
            dtype=np.float32,
        ),
        ref_codes=np.asarray(
            ref_codes,
            dtype=np.int64,
        ),
    )


def get_reference(
    tts: Vieneu,
    story_dir: Path,
    reference_path: Path,
):
    """
    Load reference từ cache hoặc encode một lần.
    """

    cache_path = cache_path_for_story(story_dir)

    cached = load_reference_cache(
        cache_path,
        reference_path,
    )

    if cached is not None:
        print("Reference cache: HIT")

        speaker_emb, ref_codes = cached

        print(
            f"    speaker_emb: {speaker_emb.shape} "
            f"{speaker_emb.dtype}"
        )

        print(
            f"    ref_codes: {ref_codes.shape} "
            f"{ref_codes.dtype}"
        )

        return speaker_emb, ref_codes

    print("Reference cache: MISS")
    print("    Encoding reference...")

    speaker_emb, ref_codes = tts.encode_reference(
        reference_path,
        denoise=True,
    )

    speaker_emb = np.asarray(
        speaker_emb,
        dtype=np.float32,
    )

    ref_codes = np.asarray(
        ref_codes,
        dtype=np.int64,
    )

    save_reference_cache(
        cache_path,
        reference_path,
        speaker_emb,
        ref_codes,
    )

    print("    Reference cache: SAVED")

    print(
        f"    speaker_emb: {speaker_emb.shape} "
        f"{speaker_emb.dtype}"
    )

    print(
        f"    ref_codes: {ref_codes.shape} "
        f"{ref_codes.dtype}"
    )

    return speaker_emb, ref_codes


# ============================================================
# FAST TTS
# ============================================================

def generate_segment_fast(
    tts,
    text: str,
    speaker_emb,
    ref_codes,
    style: str,
    batch_size: int,
    max_chars: int = MAX_CHARS,
):
    """
    FAST MODE.

    Không split sentence.

    Toàn bộ text được đưa thẳng vào:
        normalize_to_chunks_v3_with_gaps()

    Hàm này tự ưu tiên:
        - paragraph boundary
        - sentence boundary
        - phrase boundary

    và chỉ cắt bên trong câu khi thực sự không thể
    giữ câu trong giới hạn max_chars.

    Sau đó:

        all chunks
             ↓
        _infer_chunks()  <-- chỉ gọi interface 1 lần
             ↓
        join_audio_chunks()
             ↓
        watermark 1 lần
    """

    text = text.strip()

    if not text:
        return np.array([], dtype=np.float32), 0, 0

    # ========================================================
    # 1. CHUNK TOÀN BỘ TEXT
    # ========================================================

    chunks, gaps = normalize_to_chunks_v3_with_gaps(
        text,
        max_chars=max_chars,
    )

    if not chunks:
        return np.array([], dtype=np.float32), 0, 0

    total_chars = len(text)

    avg_chars = (
        total_chars / len(chunks)
        if chunks
        else 0
    )

    print(
        f"    Chars : {total_chars:,}"
    )

    print(
        f"    Chunks: {len(chunks)} "
        f"(avg {avg_chars:.1f} chars/chunk)"
    )

    # ========================================================
    # 2. INFERENCE
    # ========================================================

    sampling = dict(
        temperature=0.8,
        top_k=25,
        top_p=0.95,
        max_new_frames=300,
        repetition_penalty=1.2,
        repetition_window=DEFAULT_REP_WINDOW,
    )

    infer_start = time.perf_counter()

    # ========================================================
    # QUAN TRỌNG
    #
    # Chỉ gọi _infer_chunks() MỘT LẦN cho toàn bộ segment.
    #
    # CPU/ONNX bên trong VieNeu vẫn chạy từng chunk tuần tự,
    # nhưng generate.py không gọi API/interface riêng cho từng
    # chunk nữa.
    # ========================================================

    # VieNeu-TTS v3 Turbo has had two _infer_chunks signatures:
    #
    #   newer: (chunks, speaker_emb, ref_codes, style, use_ref_codes,
    #            batch_size, sampling)
    #   older: (chunks, speaker_emb, ref_codes, style, use_ref_codes,
    #            sampling)
    #
    # CPU/ONNX does not benefit from chunk batching anyway, so support both
    # signatures without changing the inference behavior.
    import inspect

    infer_chunks_fn = tts._infer_chunks
    infer_params = inspect.signature(infer_chunks_fn).parameters

    if "batch_size" in infer_params:
        wavs = infer_chunks_fn(
            chunks,
            speaker_emb,
            ref_codes,
            # style,
            True,
            max(1, int(batch_size)),
            sampling,
        )
    else:
        wavs = infer_chunks_fn(
            chunks,
            speaker_emb,
            ref_codes,
            # style,
            True,
            sampling,
        )

    infer_time = time.perf_counter() - infer_start

    # ========================================================
    # 3. JOIN AUDIO
    # ========================================================

    combined_audio = join_audio_chunks(
        wavs,
        tts.sample_rate,
        silence_ps=gaps_to_silence(gaps),
    )

    # ========================================================
    # 4. WATERMARK
    #
    # Chỉ watermark MỘT LẦN cho toàn bộ segment.
    # ========================================================

    combined_audio = tts._apply_watermark(
        combined_audio
    )

    return (
        combined_audio,
        len(chunks),
        infer_time,
    )


# ============================================================
# STORY GENERATION
# ============================================================

def generate_story(
    story_dir: Path,
    force: bool = False,
    batch_size: int = DEFAULT_BATCH_SIZE,
    only: list[str] | None = None,
    max_chars_override: int | None = None,
):
    story_dir = story_dir.resolve()

    config_path = story_dir / "config.json"

    config = load_json(
        config_path,
        {},
    )

    # --------------------------------------------------------
    # Paths
    # --------------------------------------------------------

    voice_path = story_dir / config.get(
        "voice",
        "voice/reference.wav",
    )

    script_dir = story_dir / config.get(
        "script_dir",
        "script",
    )

    audio_dir = story_dir / config.get(
        "audio_dir",
        "audio",
    )

    audio_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    style = config.get(
        "style",
        "doc_truyen",
    )

    max_chars = int(
        max_chars_override
        if max_chars_override is not None
        else config.get(
            "max_chars",
            MAX_CHARS,
        )
    )

    # --------------------------------------------------------
    # Banner
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print()
    print(f"Story: {story_dir.relative_to(Path.cwd())}")
    print()
    print("=" * 60)
    print()

    print(f"Voice : {voice_path}")
    print(f"Style : {style}")
    print(f"Batch : {batch_size}")
    print(f"Max chars/chunk : {max_chars}")
    print()

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if not voice_path.exists():
        raise FileNotFoundError(
            f"Reference voice not found: {voice_path}"
        )

    if not script_dir.exists():
        raise FileNotFoundError(
            f"Script directory not found: {script_dir}"
        )

    text_files = sorted(
        script_dir.glob("*.txt"),
        key=natural_key,
    )

    if only:
        wanted = {Path(name).stem for name in only}
        text_files = [
            p for p in text_files
            if p.stem in wanted
        ]

    if not text_files:
        print("No matching .txt files found.")
        return

    print(f"Texts : {len(text_files)}")
    print()

    # --------------------------------------------------------
    # Init TTS
    # --------------------------------------------------------

    print("Loading VieNeu...")

    tts = Vieneu(
        mode="v3turbo",
        device="auto",
        backend="auto",
        threads=0,
        max_batch_size=max(
            batch_size,
            1,
        ),
    )

    print(
        f"Backend: {getattr(tts, 'backend', 'unknown')}"
    )

    print()

    # --------------------------------------------------------
    # Reference
    # --------------------------------------------------------

    speaker_emb, ref_codes = get_reference(
        tts,
        story_dir,
        voice_path,
    )

    print()

    # --------------------------------------------------------
    # Build pending list
    # --------------------------------------------------------

    pending = []

    skipped = 0

    for text_path in text_files:

        stem = text_path.stem

        audio_path = (
            audio_dir /
            f"{stem}.wav"
        )

        if (
            audio_path.exists()
            and not force
        ):
            skipped += 1
            continue

        pending.append(
            {
                "stem": stem,
                "text_path": text_path,
                "audio_path": audio_path,
            }
        )

    print(
        f"Generating {len(pending)} segment(s)..."
    )

    if skipped:
        print(
            f"Skipped existing: {skipped}"
        )

    print()

    if not pending:
        print("Nothing to generate.")
        return

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    total_start = time.perf_counter()

    generated = 0
    failed = 0

    total_chunks = 0
    total_infer_time = 0.0

    # --------------------------------------------------------
    # Batch
    #
    # Batch ở đây chỉ là nhóm SEGMENT để quản lý.
    #
    # Trên CPU/ONNX, VieNeu vẫn inference chunk tuần tự.
    # --------------------------------------------------------

    for batch_start in range(
        0,
        len(pending),
        max(1, batch_size),
    ):

        batch = pending[
            batch_start:
            batch_start + max(1, batch_size)
        ]

        batch_end = (
            batch_start +
            len(batch)
        )

        print(
            f"[BATCH] "
            f"{batch_start + 1}-{batch_end} "
            f"/ {len(pending)}"
        )

        batch_start_time = (
            time.perf_counter()
        )

        for item_index, item in enumerate(
            batch,
            start=batch_start + 1,
        ):

            stem = item["stem"]

            text_path = item["text_path"]

            audio_path = item["audio_path"]

            print()
            print(
                f"[{item_index}/{len(pending)}] "
                f"{stem}"
            )

            try:
                text = read_text(
                    text_path
                )

                if not text:
                    print(
                        "    SKIP: empty text"
                    )
                    continue

                segment_start = (
                    time.perf_counter()
                )

                (
                    audio,
                    chunk_count,
                    infer_time,
                ) = generate_segment_fast(
                    tts=tts,
                    text=text,
                    speaker_emb=speaker_emb,
                    ref_codes=ref_codes,
                    style=style,
                    batch_size=batch_size,
                    max_chars=max_chars,
                )

                if (
                    audio is None
                    or len(audio) == 0
                ):
                    raise RuntimeError(
                        "No audio generated"
                    )

                # ------------------------------------------------
                # Save
                # ------------------------------------------------

                tts.save(
                    audio,
                    audio_path,
                )

                elapsed = (
                    time.perf_counter()
                    - segment_start
                )

                duration = (
                    len(audio)
                    / tts.sample_rate
                )

                total_chunks += chunk_count
                total_infer_time += infer_time

                generated += 1

                print(
                    f"    OK"
                    f" | chunks={chunk_count}"
                    f" | audio={duration:.1f}s"
                    f" | infer={infer_time:.1f}s"
                    f" | total={elapsed:.1f}s"
                )

            except Exception as e:

                failed += 1

                print(
                    f"    FAILED: {stem}"
                )

                print(
                    f"    Error: {e}"
                )

        batch_elapsed = (
            time.perf_counter()
            - batch_start_time
        )

        print()

        print(
            f"[BATCH DONE] "
            f"{batch_end - batch_start + 1}"
            f"-{batch_end} / {len(pending)} "
            f"in {batch_elapsed:.2f}s"
        )

        print()

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total_elapsed = (
        time.perf_counter()
        - total_start
    )

    print()
    print("=" * 60)
    print()
    print(f"Generated : {generated}")
    print(f"Failed    : {failed}")
    print(f"Skipped   : {skipped}")
    print(
        f"Chunks    : {total_chunks:,}"
    )
    print(
        f"Infer     : {total_infer_time:.2f}s"
    )
    print(
        f"Time      : {total_elapsed:.2f}s"
    )

    if total_chunks:
        print(
            f"Avg infer/chunk : "
            f"{total_infer_time / total_chunks:.2f}s"
        )

    print()
    print("=" * 60)
    print()


# ============================================================
# DISCOVER STORIES
# ============================================================

def discover_stories():
    if not DEFAULT_STORY_ROOT.exists():
        return []

    return sorted(
        [
            p
            for p in DEFAULT_STORY_ROOT.iterdir()
            if p.is_dir()
        ],
        key=natural_key,
    )


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "VieNeu-TTS FAST story generator "
            "(chunk-first, no sentence timing)"
        )
    )

    parser.add_argument(
        "story",
        nargs="?",
        type=Path,
        help="Story directory",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all stories",
    )

    parser.add_argument(
        "--only",
        nargs="+",
        metavar="FILE",
        help=(
            "Generate only the specified text file(s), e.g. "
            "--only 101.txt or --only 101.txt 102.txt"
        ),
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate existing WAV files",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=(
            "Number of segments grouped for progress "
            "management. On CPU this does NOT make "
            "chunks run in parallel."
        ),
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=MAX_CHARS,
        help=(
            "Maximum chars per VieNeu chunk "
            "(default: 256)"
        ),
    )

    args = parser.parse_args()

    if args.all:

        stories = discover_stories()

        if not stories:
            print(
                "No stories found."
            )
            return

        for story in stories:

            generate_story(
                story,
                force=args.force,
                batch_size=max(
                    1,
                    args.batch_size,
                ),
                only=args.only,
                max_chars_override=max(1, int(args.max_chars)),
            )

        return

    if args.story is None:

        print(
            "Please specify a story."
        )

        print(
            "Example:"
        )

        print(
            "python tts/generate.py "
            "stories/truyen-001"
        )

        return

    generate_story(
        args.story,
        force=args.force,
        batch_size=max(
            1,
            args.batch_size,
        ),
        only=args.only,
        max_chars_override=max(1, int(args.max_chars)),
    )


if __name__ == "__main__":
    main()