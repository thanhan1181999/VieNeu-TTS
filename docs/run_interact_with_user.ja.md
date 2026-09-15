# `run_interact_with_user.sh` 使い方

対話形式で、小説のクロール → テキスト整形 → TTS音声生成 → タイトル取得 → 動画生成までを一連で実行するスクリプトです。

実行場所は **リポジトリのルート** を推奨します。

```bash
./run_interact_with_user.sh
```

---

## 入力項目

スクリプト起動後、次の順で質問されます。

| 項目 | 必須 | デフォルト | 説明 |
|---|---|---|---|
| `Story` | 必須 | — | 小説フォルダ名（`stories/<Story>/` に出力） |
| `Start chapter` | 必須 | — | 開始章番号 |
| `End chapter` | 必須 | — | 終了章番号 |
| `Content URL` | 必須 | — | **本文クロール用** URL（`crawl.js` に渡す） |
| `Title URL` | 必須 | — | **章タイトルクロール用** URL（`crawl_title.js` に渡す） |
| `Crawl selector` | 任意 | `#chapter-c` | 本文の CSS セレクタ（`crawl.js` の `--selector`） |
| `Crawl title selector` | 任意 | `#list-chapter ul.list-chapter` | 章タイトル一覧の CSS セレクタ（`crawl_title.js` の `--selector`） |
| `Voice path` | 任意 | `stories/voices/reference.wav` | 参照音声ファイル |
| `Image cover file path` | 必須 | — | カバー画像のパス |

続けて、各処理を実行するかどうか（`Y/n`）を聞かれます。

| 項目 | デフォルト | 対応処理 |
|---|---|---|
| `Crawl & Clean?` | Yes | `crawl.js` → `clean1.js` |
| `Generate Audio?` | Yes | `tts/make_audio.py` |
| `Crawling Title?` | Yes | `crawl_title.js` |
| `Generate Video?` | Yes | `tts/make_video_ver4.py` |

---

## Content URL と Title URL の違い

サイトによっては、本文ページのベース URL と、章タイトル一覧ページの URL が異なることがあります。

- `Content URL` … 各章本文の取得に使用（`{url}/chuong-{n}/` 形式で組み立て）
- `Title URL` … 章タイトル一覧の取得に使用（`{url}/`、`{url}/trang-{n}/` 形式で組み立て）

同じサイト・同じパスなら、両方に同じ URL を入力してください。

---

## セレクタについて

入力を空のまま Enter すると、デフォルト値が使われます。

- `Crawl selector` デフォルト: `#chapter-c`
- `Crawl title selector` デフォルト: `#list-chapter ul.list-chapter`

サイトの HTML 構造が違う場合のみ、適切な CSS セレクタを指定してください。

---

## 実行の流れ

1. 入力内容の確認表示
2. `stories/<Story>/script/0.txt` が無い場合、小説紹介文の入力（Ctrl+D で確定）
3. （有効時）本文クロール + クリーン
4. （有効時）TTS 音声生成
5. （有効時）章タイトルクロール
6. （有効時）動画生成

---

## 入力例

```text
Story: truyen-001
Start chapter: 1
End chapter: 10
Content URL: https://example.com/truyen-a/
Title URL: https://example.com/truyen-a-list/
Crawl selector [#chapter-c]:          ← Enter でデフォルト
Crawl title selector [#list-chapter ul.list-chapter]:  ← Enter でデフォルト
Voice path [stories/voices/reference.wav]:
Image cover file path (required): /path/to/cover.jpg
Crawl & Clean? [Y/n]:
Generate Audio? [Y/n]:
Crawling Title? [Y/n]:
Generate Video? [Y/n]:
```

本文とタイトルが同じ URL の場合:

```text
Content URL: https://truyenfull.live/thieu-gia-bi-bo-roi/
Title URL: https://truyenfull.live/thieu-gia-bi-bo-roi/
```

---

## 内部で呼ばれるコマンド（参考）

本文クロール:

```bash
node craw/crawl.js \
  --story "$STORY" \
  --start "$START" \
  --end "$END" \
  --url "$CONTENT_URL" \
  --selector "$CRAW_SELECTOR"
```

章タイトルクロール:

```bash
node craw/crawl_title.js \
  --url "$TITLE_URL" \
  --story "$STORY" \
  --selector "$CRAW_TITLE_SELECTOR"
```

---

## 注意事項

- 実行前に参照音声ファイルとカバー画像が存在すること
- 既存の `stories/<Story>/voice/reference.wav` や `cover.*` がある場合は上書きしません
- `0.txt`（紹介文）は初回のみ対話入力を求めます
