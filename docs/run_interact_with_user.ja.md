# `run_interact_with_user.sh` の使い方

対話式スクリプトです。小説のクロール → テキスト整形 → TTS → 章タイトル取得 → 動画生成 → YouTube アップロードまでを自動化します。

**リポジトリのルート** から実行してください。

```bash
./run_interact_with_user.sh
```

---

## 実行モード

| 状況 | モード | 入力内容 |
|---|---|---|
| まだ `stories/<Story>/` がない（新規） | フル | URL、selector、voice、cover、… |
| すでに `stories/<Story>/config.json` がある（2回目以降） | 短縮 | Story + Start/End + 各ステップの ON/OFF |
| フォルダはあるが `config.json` がない（既存作品） | 移行 | URL/selector を一度聞いて config を作成。cover/voice があればそれを使う |

初回実行後、設定は `stories/<Story>/config.json` に保存されます。次回以降は cover / voice を再入力しません（既存の `cover.*` と `voice/reference.wav` を使います）。

---

## 初回（新規作品）

| 項目 | 必須 | デフォルト | 説明 |
|---|---|---|---|
| `Story` | はい | — | 作品フォルダ名（`stories/<Story>/`） |
| `Start chapter` | はい | — | 開始章 |
| `End chapter` | はい | — | 終了章 |
| `Content URL` | はい | — | 本文クロール用 URL（`crawl.js`） |
| `Title URL` | はい | — | 章タイトルクロール用 URL（`crawl_title.js`） |
| `Crawl selector` | いいえ | `#chapter-c` | 本文の CSS selector |
| `Crawl title selector` | いいえ | `#list-chapter ul.list-chapter` | タイトル一覧の CSS selector |
| `Voice path` | いいえ | `stories/voices/reference.wav` | 参照音声（`voice/reference.wav` にコピー） |
| `Image cover file path` | はい | — | 表紙画像（`cover.<拡張子>` へ移動） |

続いて、各ステップを実行するかを選びます（`Y/n`）:

| 項目 | デフォルト | 対応処理 |
|---|---|---|
| `Crawl & Clean?` | Yes | `crawl.js` → `clean1.js` |
| `Generate Audio?` | Yes | `tts/make_audio.py` |
| `Crawling Title?` | Yes | `crawl_title.js` |
| `Generate Video?` | Yes | `tts/make_video_ver4.py` |
| `Add episode_label?` | Yes | 動画左上に「Tập N」を描画（Generate Video が Yes のときだけ質問） |
| `Upload YouTube?` | Yes | `upload/upload_youtube_ver1.py`（Generate Video とは独立して毎回質問） |

`Upload YouTube?` が Yes で、まだ `config.json` に無い場合だけ、次を追加で聞きます。値は保存され、次回以降は再質問しません。

| 項目 | 必須 | デフォルト | 説明 |
|---|---|---|---|
| `YouTube title` | はい | — | 全動画で共通。末尾に ` ( Phần N)` が付く |
| `YouTube description` | はい | — | 全動画で共通。既存テンプレートに差し込む（複数行可、Ctrl+D で確定） |
| `Tên truyện (description_story_name)` | はい | — | description 先頭の作品名 |
| `Tác giả` | はい | — | 作者 |
| `Thể loại` | はい | — | ジャンル |
| `Tags` | はい | — | カンマ区切り（`#` は任意） |
| `Playlist ID` | いいえ | `PLerSSQqUz9Wc` | 追加先プレイリスト |
| `Thumbnail path` | いいえ | `stories/<Story>/thumbnail.jpeg` | YouTube のサムネイル画像 |
| `Label position` | いいえ | `top_left` | 文字「Tập N」の位置: `top_left` / `middle_left` / `bottom_left` |

---

## 2回目以降（短縮モード）

| 項目 | 説明 |
|---|---|
| `Story` | すでに `config.json` があるフォルダ名 |
| `Start chapter` / `End chapter` | 今回の章範囲 |
| 各ステップの ON/OFF | 前回の値をデフォルトに。Enter で維持 |

URL、selector、cover、voice、YouTube の title / description / tags などは `config.json` から読むため、再入力しません。

`Generate Video?` と `Upload YouTube?` は別々に選べます。動画だけ作る、既存 mp4 だけアップロードする、両方やる、どちらもスキップする、いずれも可能です。

---

## `config.json` の例

```json
{
  "content_url": "https://truyenfull.live/example/",
  "title_url": "https://truyenfull.live/example/",
  "crawl_selector": "#chapter-c",
  "crawl_title_selector": "#list-chapter ul.list-chapter",
  "last_start": "1",
  "last_end": "10",
  "crawl_and_clean": true,
  "generate_audio": true,
  "crawling_title": true,
  "generate_video": true,
  "add_episode_label": true,
  "upload_youtube": true,
  "youtube_title": "AUDIO Truyện Dị Giới | Example",
  "youtube_description": "作品の紹介文",
  "description_story_name": "Example",
  "author": "作者名",
  "genre": "ジャンル",
  "tags": "#tag1, #tag2",
  "playlist_id": "PLerSSQqUz9Wc",
  "privacy_status": "private",
  "thumbnail_path": "stories/truyen-001/thumbnail.jpeg",
  "review_label_position": "top_left"
}
```

実行が終わると `last_start` / `last_end` と各ステップのフラグが更新されます。

---

## Content URL と Title URL の違い

サイトによっては、本文ページとタイトル一覧ページでベース URL が異なります。

- `Content URL` — 各章の本文（`{url}/chuong-{n}/` のような形）
- `Title URL` — タイトル一覧（`{url}/`、`{url}/trang-{n}/` のような形）

同じ URL なら、両方に同じ値を入れてください。

---

## selector について

Enter を押すとデフォルトを使います。

- `Crawl selector` デフォルト: `#chapter-c`
- `Crawl title selector` デフォルト: `#list-chapter ul.list-chapter`

サイトの HTML がデフォルトと違うときだけ変更します。

---

## 実行の流れ

1. Story 名を聞く → 新規 / 短縮 / 移行を判定
2. 必要な項目を入力し、設定を再表示
3. `config.json` を保存（または更新）
4. `script/0.txt` が無ければ作品紹介を入力（Ctrl+D で終了）
5. ON になっているステップを実行

---

## 動画パートの作り方

`tts/make_video_ver4.py` は、約 11 時間 30 分を超えないように章をパートへ分割します。

- 出力ファイル名は常に `stories/<Story>/<Story>_partN.mp4`
- すでに完成している part（`.mp4` と `.json` の両方があるもの）は **作り直しません**
- 次の実行では、未作成の章だけを対象に、次の part 番号から続けます

---

## YouTube アップロード

ステップ 6 は `Upload YouTube` が Yes のときだけ動きます。`Generate Video` が No でも、既存の mp4 があればアップロードできます。

- `upload/upload_youtube_ver1.py --story "$STORY" --thumbnail "$THUMBNAIL_PATH" --label-position "$REVIEW_LABEL_POSITION"` を呼びます
- `stories/<Story>/` 内の `<Story>_partN.mp4` をスキャンします
- タイトルは共通で、末尾だけ ` ( Phần N)` が変わります
- description は全動画で同じです（テンプレート + 初回に聞いた本文）
- サムネイルは初回に聞いたパスを使う（デフォルト: `stories/<Story>/thumbnail.jpeg`）
- 各 part 用に `review_partN.jpeg` を作り、それを YouTube サムネイルにする。文字位置は `top_left` / `middle_left` / `bottom_left`
- 公開設定は常に `private`。ベトナム時間 20:00 に公開されるよう `publishAt` を付ける
- 最初の未投稿パートは「今夜 20:00（ベトナム時間）」。すでに 20:00 を過ぎていれば翌日 20:00
- 次のパートは前のパートの 1 日後の 20:00。以降も 1 日ずつずらす
- 前回までに予約した `publish_at` があれば、その翌日以降から続ける（同じ日に重ならない）
- すでにアップロードした part は `stories/<Story>/upload_log.json` に記録し、次回はスキップします
- 1 本失敗しても、残りの part は続行します

独立して動かす場合:

```bash
uv run python upload/upload_youtube_ver1.py --story <Story>
```

`config.json` に足りない項目があれば、そのときだけ質問して保存します。OAuth 用の `upload/client_secret.json` が必要です。初回だけブラウザで認証し、トークンを `upload/token.json` に保存します。次回以降は自動で再利用・refresh します。

---

## 入力例

### 初回

```text
Story: truyen-001
Start chapter: 1
End chapter: 10
Content URL: https://example.com/truyen-a/
Title URL: https://example.com/truyen-a/
Crawl selector [#chapter-c]:
Crawl title selector [#list-chapter ul.list-chapter]:
Voice path [stories/voices/reference.wav]:
Image cover file path (required): /path/to/cover.jpg
Crawl & Clean? [Y/n]:
Generate Audio? [Y/n]:
Crawling Title? [Y/n]:
Generate Video? [Y/n]:
Add episode_label? [Y/n]:
Upload YouTube? [Y/n]:
YouTube title: AUDIO Truyện Dị Giới | Example
YouTube description:
(Enter で改行、Ctrl+D で確定)
Tên truyện (description_story_name): Example
Tác giả: 作者名
Thể loại: ジャンル
Tags (phân tách bằng dấu phẩy): #tag1, #tag2
Playlist ID [PLerSSQqUz9Wc]:
Thumbnail path [stories/truyen-001/thumbnail.jpeg]:
Chọn [1/2/3, mặc định top_left]:
```

### 2回目以降

```text
Story: truyen-001
Found existing config: stories/truyen-001/config.json
Short mode — only chapter range and optional steps are required.

Last run chapters: 1 -> 10
Start chapter: 11
End chapter: 20
Crawl & Clean? [Y/n]:
Generate Audio? [Y/n]:
Crawling Title? [Y/n]:
Generate Video? [Y/n]:
Add episode_label? [Y/n]:
Upload YouTube? [Y/n]:
```

本文とタイトルが同じ URL のとき:

```text
Content URL: https://truyenfull.live/thieu-gia-bi-bo-roi/
Title URL: https://truyenfull.live/thieu-gia-bi-bo-roi/
```

---

## 内部で呼ぶコマンド（参考）

本文クロール:

```bash
node craw/crawl.js \
  --story "$STORY" \
  --start "$START" \
  --end "$END" \
  --url "$CONTENT_URL" \
  --selector "$CRAW_SELECTOR"
```

タイトルクロール:

```bash
node craw/crawl_title.js \
  --url "$TITLE_URL" \
  --story "$STORY" \
  --selector "$CRAW_TITLE_SELECTOR"
```

YouTube アップロード:

```bash
uv run python upload/upload_youtube_ver1.py --story "$STORY" --thumbnail "$THUMBNAIL_PATH" --label-position "$REVIEW_LABEL_POSITION"
```

---

## 注意

- 初回の前に、参照音声と表紙画像を用意してください
- 既存の `stories/<Story>/voice/reference.wav` や `cover.*` は上書きしません
- `0.txt`（作品紹介）は、ファイルが無い初回だけ入力します
- 短縮モードでは `cover.*` と `voice/reference.wav` が必要です
- アップロード時はサムネイル画像が必要です。デフォルトは `stories/<Story>/thumbnail.jpeg`
- 動画は private で予約公開します。公開時刻はベトナム時間 20:00、パート間は 1 日
- 予約公開には YouTube チャンネルの確認（電話認証など）が必要な場合があります
- コメント制限（登録者のみ）は YouTube Studio 側の設定です。API では指定できません
