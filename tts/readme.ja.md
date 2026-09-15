# VieNeu-TTS — TTS / 動画ガイド

`tts` 配下のスクリプトで、章テキストから音声（WAV）を生成し、静止画＋音声の動画（MP4）を作成します。

リポジトリの**ルートディレクトリ**から実行してください。

---

## 前提となるディレクトリ構成

```text
stories/<story_id>/
  ├── script/           # 章テキスト（1.txt, 2.txt, ...）
  ├── voice/
  │   └── reference.wav # 参照ボイス（クローン用）
  ├── audio/            # TTS 出力（1.wav, 2.wav, ...）
  ├── titles.txt        # 章タイトル一覧（動画字幕用）
  ├── cover.jpeg        # サムネイル（任意）
  └── config.json       # 任意（voice / script_dir / audio_dir など）
```

推奨フロー:

1. `make_audio.py` — テキスト → WAV
2. `make_video_ver4.py` — WAV + 画像 → MP4

---

## 1. `make_audio.py` — 音声生成（TTS）

章ごとの `.txt` を VieNeu（ONNX INT8 / Apple Silicon 向け）で読み上げ、`audio/<章番号>.wav` を出力します。参照ボイスはキャッシュ（`cache/reference.npz`）されます。

### 基本コマンド

```bash
uv run python tts/make_audio.py stories/truyen-001
```

引数なしのデフォルト: **`mode=v3nano`**, **`steps=6`**, **`precision=int8`**, **`batch-size=8`**, **`max-chars=512`**（高速寄り）。

### CLI オプション

| オプション | 意味 | デフォルト |
|---|---|---|
| `story` | 物語ディレクトリ（例: `stories/truyen-001`） | （必須 ※`--all` 以外） |
| `--all` | `stories/` 配下の全物語を処理 | off |
| `--only FILE ...` | 指定ファイルのみ（stem、例: `1` `2`） | すべて |
| `--start N` | 開始章（1 始まり、ソート済み script の位置） | 先頭 |
| `--end N` | 終了章（1 始まり、含む） | 末尾 |
| `--force` | 既存 WAV も再生成 | off（既存はスキップ） |
| `--batch-size N` | バッチサイズ | `8` |
| `--max-chars N` | 1 チャンクあたり最大文字数 | `512` |
| `--mode` | `v3nano` / `v3turbo` | `v3nano` |
| `--steps N` | Euler sampling steps（小さいほど速い） | `6` |

### 実行例

Turbo モード:

```bash
uv run python tts/make_audio.py stories/truyen-001 --mode v3turbo
```

steps を下げてさらに高速化:

```bash
uv run python tts/make_audio.py stories/truyen-001 --steps 6
```

章範囲を指定:

```bash
uv run python tts/make_audio.py stories/truyen-001 --start 102 --end 120
```

`stories/` 全件:

```bash
uv run python tts/make_audio.py --all
```

既存 WAV を強制再生成:

```bash
uv run python tts/make_audio.py stories/truyen-001 --force
```

パイプラインでよく使う組み合わせ例:

```bash
uv run python tts/make_audio.py stories/truyen-001 \
  --mode v3turbo --max-chars 512 --batch-size 16 --steps 8 \
  --start 102 --end 102
```

### 必要なもの

- `stories/<id>/voice/reference.wav`（または `config.json` の `voice`）
- `stories/<id>/script/*.txt`

既存の WAV があり `--force` が無い場合はスキップします。

---

## 2. `make_video_ver4.py` — 動画作成（ffmpeg）

指定章範囲の WAV を連結し、カバー画像（または黒背景）＋章タイトル字幕付きの MP4 を作成します。

### 基本コマンド

```bash
uv run python tts/make_video_ver4.py <STORY_ID> <START_CH> <END_CH>
```

例:

```bash
uv run python tts/make_video_ver4.py truyen-001 1 50
```

| 引数 | 意味 |
|---|---|
| `STORY_ID` | `stories/` 配下のフォルダ名（パスは付けない） |
| `START_CH` | 開始章番号 |
| `END_CH` | 終了章番号（含む） |

### 必要な入力

| パス | 必須 | 説明 |
|---|---|---|
| `stories/<id>/audio/<章>.wav` | 必須 | 範囲内の全章が揃っていること |
| `stories/<id>/titles.txt` | 必須 | 行番号が章番号に対応するタイトル |
| `stories/<id>/cover.jpeg` | 任意 | 無い場合は黒背景 |

WAV はチャンネル数・サンプル幅・サンプルレートが揃っている必要があります。

### 動作概要

- 解像度 `1280x720`、静止画向けエンコード（`libx264` + AAC `128k`）
- 字幕は `titles.txt` の各章タイトル（画面下部）
- 合計が **11時間30分** を超える場合は自動でパート分割
  - 1 パートのみ: `<story_id>_<start>_<end>.mp4`
  - 複数パート: `<story_id>_<first>_<last>_partN.mp4`
- 一時ファイル（concat list / SRT）は完了後に削除

### 依存

- システムに `ffmpeg` が入っていること

---

## 連携の流れ（例）

```bash
# 1) 音声
uv run python tts/make_audio.py stories/truyen-001 --mode v3turbo --start 1 --end 50

# 2) タイトル取得（未作成の場合）
node craw/crawl_title.js --url "<物語URL>" --story truyen-001

# 3) 動画
uv run python tts/make_video_ver4.py truyen-001 1 50
```
