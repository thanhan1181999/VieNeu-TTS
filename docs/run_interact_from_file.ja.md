# `run_interact_from_file.sh` の使い方

対話式スクリプトです。ローカルの小説 TXT を章ごとに分割 → テキスト整形 → TTS → 動画生成 → YouTube アップロードまでを自動化します。Web からのクロールは行いません。

**リポジトリのルート** から実行してください。初回は実行権限が必要です。

```bash
chmod +x run_interact_from_file.sh
./run_interact_from_file.sh
```

Web からクロールする従来の流れは `run_interact_with_user.sh` を使います。

---

## 実行モード

| 状況 | モード | 入力内容 |
|---|---|---|
| まだ `stories/<Story>/` がない（新規） | フル | TXT パス、voice、cover、… |
| すでに `stories/<Story>/config.json` がある（2回目以降） | 短縮 | Story + Start/End + 各ステップの ON/OFF |
| フォルダはあるが `config.json` がない（既存作品） | 移行 | `source.txt` があればそれを使う。なければ TXT パスを一度聞く |

初回実行後、設定は `stories/<Story>/config.json` に保存されます。次回以降は cover / voice / `source.txt` を再入力しません。

元の TXT は初回に **move** され、`stories/<Story>/source.txt` にリネームされます。すでに `source.txt` がある場合は再利用し、上書きしません。

---

## 初回（新規作品）

| 項目 | 必須 | デフォルト | 説明 |
|---|---|---|---|
| `Story` | はい | — | 作品フォルダ名（`stories/<Story>/`） |
| `Start chapter` | はい | — | TTS / 動画の開始章 |
| `End chapter` | はい | — | TTS / 動画の終了章 |
| `Story TXT file path` | はい | — | 全章が入った元ファイル。`source.txt` へ移動 |
| `Voice path` | いいえ | `stories/voices/reference.wav` | 参照音声（`voice/reference.wav` にコピー） |
| `Image cover file path` | はい | — | 表紙画像（`cover.<拡張子>` へ移動） |

続いて、各ステップを実行するかを選びます（`Y/n`）:

| 項目 | デフォルト | 対応処理 |
|---|---|---|
| `Split story?` | Yes | `craw/split_story.js`（全章を分割。Start/End は使わない） |
| `Clean?` | Yes | `craw/clean1.js` |
| `Generate Audio?` | Yes | `tts/make_audio.py`（Start–End のみ） |
| `Generate Video?` | Yes | `tts/make_video_ver4.py` |
| `Add episode_label?` | Yes | 動画左上に「Tập N」を描画（Generate Video が Yes のときだけ質問） |
| `Upload YouTube?` | Yes | `upload/upload_youtube_ver1.py`（Generate Video とは独立して毎回質問） |

**Crawling Title はありません。** 章タイトルは分割時に `titles.txt` へ書き出します。

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
| `Start chapter` / `End chapter` | 今回 TTS / 動画する章範囲 |
| 各ステップの ON/OFF | 前回の値をデフォルトに。Enter で維持 |

`source.txt`、cover、voice、YouTube の title / description / tags などは `config.json` から読むため、再入力しません。`source.txt` が無ければエラーです。

`Generate Video?` と `Upload YouTube?` は別々に選べます。

---

## 元 TXT の形式

章見出しは **1 行だけ** に置き、コロン `:` が必須です。大文字小文字は区別しません。空白と先頭ゼロは柔軟に受け付けます。

```text
（先頭の紹介文などは捨てる）

Chương 1: タイトルA
本文…

Chương 2: タイトルB
本文…

CHƯƠNG  03 : タイトルC
本文…
```

ルール:

- 必ず Chương 1 から始まり、1, 2, 3, … と連続していること。欠番・飛び番・重複はエラー
- `Chương 01` は `1.txt` になる（先頭ゼロは落とす）
- Chương 1 より前のテキストは捨てる。`script/0.txt` が無ければ、従来どおり紹介文の手入力を求める
- 各 `N.txt` には見出し行 + 本文を残す（TTS が見出しも読む）
- 本文が空でも見出しだけのファイルを作る
- 最後の章より後のテキストは最後の章に属する
- 分割は **ファイル全体**。Start/End は TTS と動画だけに使う

---

## `titles.txt`

```text
Giới Thiệu Truyện
Chương 1: タイトルA
Chương 2: タイトルB
```

- 1 行目は固定で `Giới Thiệu Truyện`（Web クロールと同じ）
- 2 行目以降は元ファイルの見出し行をそのまま使う
- すでに `titles.txt` がある場合は **更新しない**（`source.txt` に章を足しても、このファイルを消さない限り増えない）

`script/N.txt` も既存ファイルは skip し、上書きしません。

---

## `config.json` の例

```json
{
  "source_txt": "stories/truyen-001/source.txt",
  "last_start": "1",
  "last_end": "10",
  "split_story": true,
  "clean": true,
  "generate_audio": true,
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

このスクリプトは既存の `content_url` などを削除しません。同じ Story を Web クロール用スクリプトと併用しても、URL フィールドはそのまま残ります。

実行が終わると `last_start` / `last_end` と各ステップのフラグが更新されます。

---

## 実行の流れ

1. Story 名を聞く → 新規 / 短縮 / 移行を判定
2. 必要な項目を入力し、設定を再表示
3. 初回は元 TXT を `source.txt` へ移動。`config.json` を保存（または更新）
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

ステップ 5 は `Upload YouTube` が Yes のときだけ動きます。`Generate Video` が No でも、既存の mp4 があればアップロードできます。

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
Story TXT file path: /path/to/full-story.txt
Voice path [stories/voices/reference.wav]:
Image cover file path (required): /path/to/cover.jpg
Split story? [Y/n]:
Clean? [Y/n]:
Generate Audio? [Y/n]:
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
Split story? [Y/n]:
Clean? [Y/n]:
Generate Audio? [Y/n]:
Generate Video? [Y/n]:
Add episode_label? [Y/n]:
Upload YouTube? [Y/n]:
```

---

## 内部で呼ぶコマンド（参考）

TXT 分割:

```bash
node craw/split_story.js --story "$STORY"
```

任意で元ファイルを直接指定:

```bash
node craw/split_story.js \
  --story "$STORY" \
  --source /path/to/story.txt
```

YouTube アップロード:

```bash
uv run python upload/upload_youtube_ver1.py --story "$STORY" --thumbnail "$THUMBNAIL_PATH" --label-position "$REVIEW_LABEL_POSITION"
```

---

## 注意

- 初回の前に、参照音声と表紙画像、全章入りの TXT を用意してください
- 元 TXT は **移動** します。コピーではありません。原本を残したい場合は先にコピーしてください
- 既存の `stories/<Story>/voice/reference.wav`、`cover.*`、`source.txt` は上書きしません
- `0.txt`（作品紹介）は、ファイルが無い初回だけ入力します。元 TXT の Chương 1 より前の文章は使いません
- 短縮モードでは `cover.*`、`voice/reference.wav`、`source.txt` が必要です
- `titles.txt` が既にあると、後から `source.txt` に章を足してもタイトルは増えません。更新したいときは `titles.txt` を消してから Split を再実行してください
- アップロード時はサムネイル画像が必要です。デフォルトは `stories/<Story>/thumbnail.jpeg`
- 動画は private で予約公開します。公開時刻はベトナム時間 20:00、パート間は 1 日
- 予約公開には YouTube チャンネルの確認（電話認証など）が必要な場合があります
- コメント制限（登録者のみ）は YouTube Studio 側の設定です。API では指定できません
