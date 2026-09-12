# Story-to-video pipeline (this fork)

This repository is a **fork** of [pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS). The upstream TTS model, SDK, and Web UI are unchanged.

## Goal

Use the VieNeu-TTS model in a **single command** that goes from downloading a novel to a listen-along video (one still image plus chapter audio).

## Current status

Running `./run.sh`:

1. **Crawls** the story and writes each chapter under `stories/truyen-xxx/script/`.
2. **Cleans** chapter text (`craw/clean1.js`).
3. **Synthesizes** each chapter to audio with VieNeu-TTS (`tts/generate-mac-m2-v2.py`, `v3turbo`).
4. **Builds a video** with ffmpeg: **one image** plus the narration audio files.

Story layout:

```text
stories/truyen-xxx/
  script/          # chapter text (after crawl)
  voice/           # reference voice (reference.wav)
  audio/           # per-chapter WAV (after TTS)
  output/          # narration / video (after mux)
```

## One command

```bash
./run.sh <story-id> <start-chapter> <end-chapter> "<story-url>"
```

Example:

```bash
./run.sh truyen-001 102 102 "https://truyenfull.live/thieu-gia-bi-bo-roi"
```

Defaults in `run.sh` when arguments are omitted:

| Argument | Default |
| --- | --- |
| Story folder | `truyen-001` |
| Start / end chapter | `102` / `102` |
| URL | `https://truyenfull.live/thieu-gia-bi-bo-roi` |

Equivalent manual steps:

```bash
node craw/crawl.js --story truyen-001 --start 102 --end 102 --url "https://truyenfull.live/thieu-gia-bi-bo-roi"
node craw/clean1.js
uv run python tts/generate-mac-m2-v2.py stories/truyen-001 --mode v3turbo --max-chars 512 --batch-size 16 --steps 8
```

Optional WAV concat (`tts/combine.py`) and ffmpeg video encode (one still + audio) run after TTS.
