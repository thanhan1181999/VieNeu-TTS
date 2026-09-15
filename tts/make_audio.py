from __future__ import annotations

import argparse
import gc
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
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
MAX_CHARS = 512

# ============================================================
# UTILS
# ============================================================
def natural_key(path: Path):
    import re
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", path.name)]

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

def load_reference_cache(cache_path: Path, reference_path: Path):
    if not cache_path.exists():
        return None
    try:
        data = np.load(cache_path, allow_pickle=False)
        cached_fingerprint = json.loads(str(data["fingerprint"]))
        current_fingerprint = fingerprint_file(reference_path)
        if cached_fingerprint != current_fingerprint:
            print("Reference cache: MISS (reference changed)")
            return None
        speaker_emb = np.asarray(data["speaker_emb"], dtype=np.float32)
        ref_codes = np.asarray(data["ref_codes"], dtype=np.int64)
        return speaker_emb, ref_codes
    except Exception as e:
        print(f"Reference cache: INVALID ({e})")
        return None

def save_reference_cache(cache_path: Path, reference_path: Path, speaker_emb: np.ndarray, ref_codes: np.ndarray):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = fingerprint_file(reference_path)
    np.savez_compressed(
        cache_path,
        cache_version=np.array(CACHE_VERSION),
        fingerprint=np.array(json.dumps(fingerprint, ensure_ascii=False)),
        speaker_emb=np.asarray(speaker_emb, dtype=np.float32),
        ref_codes=np.asarray(ref_codes, dtype=np.int64),
    )

def get_reference(tts: Vieneu, story_dir: Path, reference_path: Path):
    cache_path = cache_path_for_story(story_dir)
    cached = load_reference_cache(cache_path, reference_path)
    if cached is not None:
        print("Reference cache: HIT")
        speaker_emb, ref_codes = cached
        return speaker_emb, ref_codes

    print("Reference cache: MISS\n    Encoding reference...")
    speaker_emb, ref_codes = tts.encode_reference(reference_path, denoise=True)
    speaker_emb = np.asarray(speaker_emb, dtype=np.float32)
    ref_codes = np.asarray(ref_codes, dtype=np.int64)
    save_reference_cache(cache_path, reference_path, speaker_emb, ref_codes)
    print("    Reference cache: SAVED")
    return speaker_emb, ref_codes

# ============================================================
# FAST TTS GENERATION
# ============================================================
def generate_segment_fast(
    tts, 
    text: str, 
    speaker_emb, 
    ref_codes, 
    voice_path: Path,
    batch_size: int, 
    max_chars: int = MAX_CHARS,
    steps: int = 6,
    sway: float = -1.0
):
    text = text.strip()
    if not text:
        return np.array([], dtype=np.float32), 0, 0

    chunks, gaps = normalize_to_chunks_v3_with_gaps(text, max_chars=max_chars)
    if not chunks:
        return np.array([], dtype=np.float32), 0, 0

    total_chars = len(text)
    avg_chars = total_chars / len(chunks) if chunks else 0
    print(f"    Chars : {total_chars:,} | Chunks: {len(chunks)} (avg {avg_chars:.1f} chars/chunk)")

    infer_start = time.perf_counter()

    # Phân nhánh xử lý riêng để đảm bảo gióng Clone chạy đúng 100%
    if hasattr(tts, "_infer_chunks"):
        # Chế độ Turbo
        sampling = dict(
            temperature=0.8,
            top_k=25,
            top_p=0.95,
            max_new_frames=300,
            repetition_penalty=1.2,
            repetition_window=DEFAULT_REP_WINDOW,
            steps=steps,
            sway=sway,
        )
        wavs = tts._infer_chunks(chunks, speaker_emb, ref_codes, True, max(1, int(batch_size)), sampling)
        combined_audio = join_audio_chunks(wavs, tts.sample_rate, silence_ps=gaps_to_silence(gaps))
        if hasattr(tts, "_apply_watermark"):
            combined_audio = tts._apply_watermark(combined_audio)
    else:
        # Chế độ Nano: Sử dụng trực tiếp file reference audio / voice_name đã đăng ký
        voice_key = f"custom_{voice_path.stem}"
        if voice_key not in getattr(tts, "voices", {}):
            # Đăng ký giọng clone vào danh sách voice của Nano
            tts.add_voice(voice_key, str(voice_path))
        
        combined_audio = tts.infer(
            text, 
            voice=voice_key, 
            steps=steps, 
            sway=sway
        )

    infer_time = time.perf_counter() - infer_start
    return combined_audio, len(chunks), infer_time

# ============================================================
# STORY GENERATION
# ============================================================
def generate_story(
    story_dir: Path, 
    force: bool = False, 
    batch_size: int = DEFAULT_BATCH_SIZE, 
    only: list[str] | None = None, 
    max_chars_override: int | None = None,
    mode: str = "v3nano",
    steps: int = 6,
    start: int | None = None,
    end: int | None = None,
):
    story_dir = story_dir.resolve()
    config_path = story_dir / "config.json"
    config = load_json(config_path, {})

    voice_path = story_dir / config.get("voice", "voice/reference.wav")
    script_dir = story_dir / config.get("script_dir", "script")
    audio_dir = story_dir / config.get("audio_dir", "audio")
    audio_dir.mkdir(parents=True, exist_ok=True)

    max_chars = int(max_chars_override if max_chars_override is not None else config.get("max_chars", MAX_CHARS))

    print(f"\nStory : {story_dir.relative_to(Path.cwd())}\nVoice : {voice_path}\nMode  : {mode} (Precision: INT8, Steps: {steps})\nBatch : {batch_size}\n")

    if not voice_path.exists():
        raise FileNotFoundError(f"Reference voice not found: {voice_path}")
    if not script_dir.exists():
        raise FileNotFoundError(f"Script directory not found: {script_dir}")

    text_files = sorted(script_dir.glob("*.txt"), key=natural_key)
    if only:
        wanted = {Path(name).stem for name in only}
        text_files = [p for p in text_files if p.stem in wanted]

    # Apply start/end range (1-based chapter numbers)
    if start is not None or end is not None:
        start_idx = start if start is not None else 0
        end_idx = (end + 1) if end is not None else len(text_files)
        
        # Validate range
        if start_idx < 0:
            start_idx = 0
        if end_idx > len(text_files):
            end_idx = len(text_files)
        if start_idx >= len(text_files) or start_idx >= end_idx:
            print("No files in the specified range.")
            return
        text_files = text_files[start_idx:end_idx]

    if not text_files:
        print("No matching .txt files found.")
        return

    print(f"Loading VieNeu ({mode} ONNX INT8 optimized for Apple Silicon)...")
    tts = Vieneu(
        mode=mode,
        device="cpu",
        backend="onnx",
        precision="int8",
        threads=8,
        max_batch_size=max(batch_size, 1),
    )

    speaker_emb, ref_codes = get_reference(tts, story_dir, voice_path)

    pending = []
    skipped = 0
    for text_path in text_files:
        stem = text_path.stem
        audio_path = audio_dir / f"{stem}.wav"
        if audio_path.exists() and not force:
            skipped += 1
            continue
        pending.append({"stem": stem, "text_path": text_path, "audio_path": audio_path})

    print(f"Generating {len(pending)} segment(s)... (Skipped: {skipped})\n")

    if not pending:
        print("Nothing to generate.")
        return

    total_start = time.perf_counter()
    generated = 0
    failed = 0
    total_chunks = 0
    total_infer_time = 0.0

    io_pool = ThreadPoolExecutor(max_workers=2)

    def process_item(item, item_index):
        nonlocal generated, failed, total_chunks, total_infer_time
        stem = item["stem"]
        text_path = item["text_path"]
        audio_path = item["audio_path"]

        print(f"[{item_index}/{len(pending)}] {stem}")
        try:
            text = read_text(text_path)
            if not text:
                print("    SKIP: empty text")
                return

            segment_start = time.perf_counter()
            audio, chunk_count, infer_time = generate_segment_fast(
                tts=tts,
                text=text,
                speaker_emb=speaker_emb,
                ref_codes=ref_codes,
                voice_path=voice_path,
                batch_size=batch_size,
                max_chars=max_chars,
                steps=steps,
                sway=-1.0,
            )

            if audio is None or len(audio) == 0:
                raise RuntimeError("No audio generated")

            io_pool.submit(tts.save, audio, audio_path)

            elapsed = time.perf_counter() - segment_start
            duration = len(audio) / tts.sample_rate
            total_chunks += chunk_count
            total_infer_time += infer_time
            generated += 1

            print(f"    OK | chunks={chunk_count} | audio={duration:.1f}s | infer={infer_time:.1f}s | total={elapsed:.1f}s")
        except Exception as e:
            failed += 1
            print(f"    FAILED: {stem} | Error: {e}")

    for batch_start in range(0, len(pending), max(1, batch_size)):
        batch = pending[batch_start : batch_start + max(1, batch_size)]
        for idx, item in enumerate(batch, start=batch_start + 1):
            process_item(item, idx)
        gc.collect()

    io_pool.shutdown(wait=True)
    total_elapsed = time.perf_counter() - total_start
    print(f"\nGenerated: {generated} | Failed: {failed} | Skipped: {skipped} | Total Time: {total_elapsed:.2f}s")

# ============================================================
# DISCOVER STORIES & CLI
# ============================================================
def discover_stories():
    if not DEFAULT_STORY_ROOT.exists():
        return []
    return sorted([p for p in DEFAULT_STORY_ROOT.iterdir() if p.is_dir()], key=natural_key)

def main():
    parser = argparse.ArgumentParser(description="VieNeu-TTS FAST story generator (Mac M2 Ultra Fast)")
    parser.add_argument("story", nargs="?", type=Path, help="Story directory")
    parser.add_argument("--all", action="store_true", help="Generate all stories")
    parser.add_argument("--only", nargs="+", metavar="FILE", help="Generate only specified file(s)")
    parser.add_argument("--start", type=int, default=None, help="Start chapter number (1-based)")
    parser.add_argument("--end", type=int, default=None, help="End chapter number (1-based)")
    parser.add_argument("--force", action="store_true", help="Regenerate existing WAV files")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size")
    parser.add_argument("--max-chars", type=int, default=MAX_CHARS, help="Max chars per chunk")
    parser.add_argument("--mode", type=str, default="v3nano", choices=["v3nano", "v3turbo"], help="Model mode")
    parser.add_argument("--steps", type=int, default=6, help="Euler sampling steps")
    args = parser.parse_args()

    if args.all:
        stories = discover_stories()
        for story in stories:
            generate_story(
                story, 
                force=args.force, 
                batch_size=max(1, args.batch_size), 
                only=args.only, 
                max_chars_override=max(1, int(args.max_chars)),
                mode=args.mode,
                steps=args.steps,
                start=args.start,
                end=args.end,
            )
        return

    if args.story is None:
        print("Please specify a story directory (e.g. python tts/make_audio.py stories/truyen-001)")
        return

    generate_story(
        args.story, 
        force=args.force, 
        batch_size=max(1, args.batch_size), 
        only=args.only, 
        max_chars_override=max(1, int(args.max_chars)),
        mode=args.mode,
        steps=args.steps,
        start=args.start,
        end=args.end,
    )

if __name__ == "__main__":
    main()