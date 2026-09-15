# VieNeu-TTS — 小説クローラーガイド

`craw` フォルダ内のスクリプトは、小説サイトから章本文・章タイトルを取得し、テキストを整形するためのものです。

想定サイト形式: `truyenfull.live`（URLパターン: `/chuong-N/`、`/trang-N/`）

実行場所は **リポジトリのルート** を推奨します。

---

## 処理の流れ（推奨）

1. `crawl_title.js` … 章タイトル一覧を取得
2. `crawl.js` … 各章の本文を取得
3. `clean1.js` … 不要文言削除＋1文1行（文間は空行）に正規化

出力ディレクトリ構成:

```text
stories/<story>/
  ├── titles.txt          # crawl_title.js の出力
  └── script/
      ├── 1.txt           # crawl.js の出力（章ごと）
      ├── 2.txt
      └── ...
```

---

## 1. `crawl.js` — 章本文のクロール

指定した章番号の範囲を順番に取得し、`stories/<story>/script/<章番号>.txt` に保存します。

### 必須パラメータ

| パラメータ | 説明 |
|---|---|
| `--story <name>` | 小説フォルダ名（出力先名） |
| `--start <number>` | 開始章番号（1以上の整数） |
| `--end <number>` | 終了章番号（`--start` 以上） |
| `--url <url>` | 小説のベースURL |

### 任意パラメータ

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `--selector <css>` | `#chapter-c` | 章本文の CSS セレクタ |
| `--delay <ms>` | `1000` | リクエスト間隔（ミリ秒） |
| `--timeout <ms>` | `15000` | HTTP タイムアウト |
| `--retries <number>` | `3` | 失敗時のリトライ回数 |
| `--force` | オフ | 既存ファイルを上書き |
| `--help` / `-h` | — | ヘルプ表示 |

### 動作メモ

- 章URLは `{url}/chuong-{n}/` 形式で組み立てます
- `--force` がない場合、既存の `.txt` はスキップします
- 失敗時はリトライし、章間で `--delay` 待機します

### 呼び出し例（必須のみ）

```bash
node craw/crawl.js \
  --story truyen-001 \
  --start 101 \
  --end 200 \
  --url "https://truyenfull.live/thieu-gia-bi-boi"
```

### 呼び出し例（全パラメータ）

```bash
node craw/crawl.js \
  --story truyen-001 \
  --start 101 \
  --end 200 \
  --url "https://truyenfull.live/thieu-gia-bi-boi" \
  --selector "#chapter-c" \
  --delay 1000 \
  --timeout 15000 \
  --retries 3 \
  --force
```

### 1章だけテストする場合

```bash
node craw/crawl.js \
  --story truyen-001 \
  --start 101 \
  --end 101 \
  --url "https://truyenfull.live/thieu-gia-bi-boi"
```

---

## 2. `crawl_title.js` — 章タイトル一覧のクロール

小説の目次ページを順に巡回し、章タイトルを `stories/<story>/titles.txt` に保存します。

### 必須パラメータ

| パラメータ | 説明 |
|---|---|
| `--story <name>` | 小説フォルダ名 |
| `--url <url>` | 小説のベースURL |

### 任意パラメータ

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `--selector <css>` | `#list-chapter ul.list-chapter` | 章リストの CSS セレクタ |
| `--delay <ms>` | `1000` | ページ間の待機時間 |
| `--timeout <ms>` | `15000` | HTTP タイムアウト |
| `--retries <number>` | `3` | 失敗時のリトライ回数 |
| `--force` | オフ | 既存の `titles.txt` を上書き |
| `--help` / `-h` | — | ヘルプ表示 |

### 動作メモ

- ページURL: 1ページ目は `{url}/`、2ページ目以降は `{url}/trang-{n}/`
- タイトルが0件、または前ページと完全一致した場合に終了します
- ファイル先頭には `Giới Thiệu Truyện` の1行が入ります
- `--force` がない場合、既存ファイルがあれば何もせず終了します

### 呼び出し例（必須のみ）

```bash
node craw/crawl_title.js \
  --story truyen-001 \
  --url "https://truyenfull.live/thieu-gia-bi-boi/"
```

### 呼び出し例（全パラメータ）

```bash
node craw/crawl_title.js \
  --story truyen-001 \
  --url "https://truyenfull.live/thieu-gia-bi-boi/" \
  --selector "#list-chapter ul.list-chapter" \
  --delay 1000 \
  --timeout 15000 \
  --retries 3 \
  --force
```

---

## 3. `clean1.js` — 本文テキストのクリーニング

`stories/<story>/script/*.txt` 内の不要文言を削除し、**1文1行・文と文の間は空行1つ**の形式に正規化します。

### パラメータ

| パラメータ | 必須 | 説明 |
|---|---|---|
| `<storyId>` | 任意 | 小説フォルダ名。省略時は `truyen-001` |

位置引数のみ（`--story` 形式ではありません）。

### 主な処理内容

- サイト宣伝・透かし文言の削除（例: `truyenfull`、`Bạn đang đọc chuyện tại Truyện FULL` など）
- 改行コードの正規化（CRLF → LF）
- 段落内のバラバラな改行をスペースで結合したうえで、文単位に分割
- 出力は「1文につき1行」、文と文のあいだに空行を1つ挿入

### 文の判定ルール

文の区切りは `.` `?` `!` のみ（`;` や `:` では区切らない）。

誤分割を避けるため、次は文区切りとみなしません:

- 略語のピリオド（例: `TP. HCM`、`ThS. Nguyễn Văn A`、`v.v.`、`tr. 15`）
- 小数（例: `3.14`）
- URL / ドメイン（例: `example.com`）やメールアドレス

### 出力フォーマット

- 文頭・文末の余分な空白を削除し、連続スペースを1つに圧縮
- 文頭を大文字化（ベトナム語ロケール）
- 文末に終止符が無い場合は `.` を付与

### 呼び出し例

```bash
# デフォルト（truyen-001）
node craw/clean1.js

# 特定の小説を指定
node craw/clean1.js truyen-001
node craw/clean1.js truyen-002
```

---

## 依存パッケージ

`craw` スクリプトで使用:

- `axios`
- `cheerio`
- `fs-extra`

（リポジトリルートで依存関係をインストール済みであること）

---

## 注意事項

- リクエスト間隔（`--delay`）を短くしすぎると、サイト側の制限に引っかかる可能性があります
- サイトの HTML 構造が変わった場合は `--selector` を調整してください
- `crawl.js` / `crawl_title.js` は既存ファイルを上書きする場合に `--force` が必要です
- `clean1.js` は対象ファイルをその場で上書きします（バックアップはありません）
