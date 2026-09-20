import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from create_review_image import (
    DEFAULT_POSITION,
    FONT_SIZE,
    ask_position,
    create_episode_image,
    load_font,
    normalize_position,
)


# ============================================================
# CẤU HÌNH
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

# YouTube category
# 22 = People & Blogs
CATEGORY_ID = "22"

# YouTube chỉ cho đặt publishAt khi privacyStatus = private.
# Đến giờ hẹn, YouTube tự chuyển video sang public.
DEFAULT_PRIVACY_STATUS = "private"
DEFAULT_PLAYLIST_ID = "PLerSSQqUz9Wc"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
PUBLISH_HOUR_VN = 20

# YouTube Data API không hỗ trợ đặt "who can comment" khi upload.
# Mặc định mong muốn: chỉ người đăng ký được bình luận.
# Cần đặt sẵn trên YouTube Studio (Settings > Community).

YOUTUBE_TITLE_MAX_LEN = 100
PART_VIDEO_RE_TEMPLATE = r"^{story_id}_part(\d+)\.mp4$"

CONFIG_KEYS = (
    "youtube_title",
    "youtube_description",
    "description_story_name",
    "author",
    "genre",
    "playlist_id",
    "privacy_status",
    "tags",
    "thumbnail_path",
    "review_label_position",
)


# ============================================================
# HỎI CẤU HÌNH KHI CHẠY
# ============================================================

def ask_required(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Trường này bắt buộc.")


def ask_with_default(prompt, default):
    value = input(prompt).strip()
    if not value:
        return default
    return value


def default_thumbnail_path(story_id):
    return os.path.join(REPO_ROOT, "stories", story_id, "thumbnail.jpeg")


def ask_thumbnail(default):
    while True:
        value = ask_with_default(
            f"Thumbnail path [{default}]: ",
            default,
        )
        if os.path.isfile(value):
            return value
        print(f"Không tìm thấy file: {value}")


def ask_multiline(prompt):
    print(prompt)
    print("(Enter xuống dòng, Ctrl+D để hoàn tất)")
    lines = []
    try:
        while True:
            lines.append(input())
    except EOFError:
        pass
    value = "\n".join(lines).strip()
    while not value:
        print("Trường này bắt buộc.")
        print(prompt)
        print("(Enter xuống dòng, Ctrl+D để hoàn tất)")
        lines = []
        try:
            while True:
                lines.append(input())
        except EOFError:
            pass
        value = "\n".join(lines).strip()
    return value


# ============================================================
# CONFIG / LOG
# ============================================================

def story_paths(story_id):
    video_dir = os.path.join(REPO_ROOT, "stories", story_id)
    return {
        "video_dir": video_dir,
        "config_file": os.path.join(video_dir, "config.json"),
        "log_file": os.path.join(video_dir, "upload_log.json"),
    }


def load_json_file(path, default):
    if not os.path.isfile(path):
        return default

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_story_config(config_file):
    data = load_json_file(config_file, {})
    if not isinstance(data, dict):
        return {}
    return data


def merge_story_config(config_file, updates):
    config = load_story_config(config_file)
    config.update(updates)
    save_json_file(config_file, config)
    return config


def load_upload_log(log_file):
    data = load_json_file(log_file, {"parts": {}})
    parts = data.get("parts", {}) if isinstance(data, dict) else {}
    normalized = {}
    for key, value in parts.items():
        normalized[str(key)] = value
    return {"parts": normalized}


def mark_part_uploaded(log_file, part, video_id, filename, publish_at=None):
    log = load_upload_log(log_file)
    entry = {
        "part": part,
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "filename": filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    if publish_at is not None:
        entry["publish_at"] = publish_at.isoformat()
    log["parts"][str(part)] = entry
    save_json_file(log_file, log)
    return log


def parse_publish_at(value):
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(VN_TZ)


def latest_scheduled_publish(upload_log):
    latest = None
    parts = upload_log.get("parts", {}) if isinstance(upload_log, dict) else {}
    for item in parts.values():
        if not isinstance(item, dict):
            continue
        scheduled = parse_publish_at(item.get("publish_at"))
        if scheduled is None:
            continue
        if latest is None or scheduled > latest:
            latest = scheduled
    return latest


def first_available_publish_at(now=None, after=None):
    """
    Slot 20:00 giờ Việt Nam sớm nhất còn ở tương lai.
    Nếu after có giá trị, slot phải sau after đúng ít nhất 1 ngày (cùng giờ 20:00).
    """
    now = now or datetime.now(VN_TZ)
    slot = now.replace(
        hour=PUBLISH_HOUR_VN,
        minute=0,
        second=0,
        microsecond=0,
    )
    if now >= slot:
        slot += timedelta(days=1)

    if after is not None:
        after_local = after.astimezone(VN_TZ)
        next_after = after_local.replace(
            hour=PUBLISH_HOUR_VN,
            minute=0,
            second=0,
            microsecond=0,
        ) + timedelta(days=1)
        if next_after > slot:
            slot = next_after

    return slot


def schedule_pending_parts(pending_parts, upload_log):
    after = latest_scheduled_publish(upload_log)
    scheduled = {}
    for part, _video_path in pending_parts:
        slot = first_available_publish_at(after=after)
        scheduled[part] = slot
        after = slot
    return scheduled


def format_vn_publish_time(dt):
    return dt.astimezone(VN_TZ).strftime("%H:%M %d/%m/%Y")


def youtube_publish_at(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def scan_part_videos(video_dir, story_id):
    if not os.path.isdir(video_dir):
        raise FileNotFoundError(
            f"Không tìm thấy thư mục video:\n{video_dir}"
        )

    pattern = re.compile(
        PART_VIDEO_RE_TEMPLATE.format(story_id=re.escape(story_id))
    )
    found = []

    for name in os.listdir(video_dir):
        match = pattern.fullmatch(name)
        if not match:
            continue
        part = int(match.group(1))
        found.append((part, os.path.join(video_dir, name)))

    found.sort(key=lambda item: item[0])
    return found


def review_image_path(video_dir, part):
    return os.path.join(video_dir, f"review_part{part}.jpeg")


def create_review_images(source_thumbnail, video_dir, parts, position=DEFAULT_POSITION):
    """
    Tạo 1 ảnh review cho mỗi part từ thumbnail gốc,
    overlay chữ Tập N giống create_review_image.py.
    """
    position = normalize_position(position)
    print()
    print("Tạo review image...")
    print(f"  Ảnh nguồn : {source_thumbnail}")
    print(f"  Số part   : {len(parts)}")
    print(f"  Vị trí    : {position}")

    source_image = Image.open(source_thumbnail)
    font = load_font(FONT_SIZE)
    outputs = {}

    for part in parts:
        output_path = review_image_path(video_dir, part)
        create_episode_image(
            source_image=source_image,
            episode_number=part,
            output_path=Path(output_path),
            font=font,
            position=position,
        )
        outputs[part] = output_path
        print(f"  ✓ Part {part}: {output_path}")

    return outputs


def prompt_missing_upload_fields(config, story_id):
    updated = dict(config)

    if not str(updated.get("youtube_title", "")).strip():
        updated["youtube_title"] = ask_required("YouTube title: ")

    if not str(updated.get("youtube_description", "")).strip():
        updated["youtube_description"] = ask_multiline("YouTube description:")

    if not str(updated.get("description_story_name", "")).strip():
        updated["description_story_name"] = ask_required(
            "Tên truyện (description_story_name): "
        )

    if not str(updated.get("author", "")).strip():
        updated["author"] = ask_required("Tác giả: ")

    if not str(updated.get("genre", "")).strip():
        updated["genre"] = ask_required("Thể loại: ")

    if not str(updated.get("tags", "")).strip():
        updated["tags"] = ask_required(
            "Tags (phân tách bằng dấu phẩy): "
        )

    if not str(updated.get("playlist_id", "")).strip():
        updated["playlist_id"] = ask_with_default(
            f"Playlist ID [{DEFAULT_PLAYLIST_ID}]: ",
            DEFAULT_PLAYLIST_ID,
        )

    updated["privacy_status"] = DEFAULT_PRIVACY_STATUS

    thumbnail = str(updated.get("thumbnail_path", "")).strip()
    if not thumbnail or not os.path.isfile(thumbnail):
        updated["thumbnail_path"] = ask_thumbnail(
            default_thumbnail_path(story_id)
        )

    try:
        updated["review_label_position"] = normalize_position(
            updated.get("review_label_position", "")
        )
    except ValueError:
        updated["review_label_position"] = ask_position(DEFAULT_POSITION)

    return updated


def resolve_upload_config(
    story_id=None,
    thumbnail_path=None,
    review_label_position=None,
):
    if not story_id:
        story_id = ask_required(
            "Mã truyện / thư mục video (ví dụ tn60): "
        )

    paths = story_paths(story_id)
    original_config = load_story_config(paths["config_file"])
    config = dict(original_config)
    if thumbnail_path:
        config["thumbnail_path"] = thumbnail_path
    if review_label_position:
        config["review_label_position"] = review_label_position
    filled = prompt_missing_upload_fields(config, story_id)

    new_values = {
        key: filled[key]
        for key in CONFIG_KEYS
        if filled.get(key) != original_config.get(key)
    }
    if new_values:
        merge_story_config(paths["config_file"], new_values)
        print(f"Đã lưu cấu hình upload vào {paths['config_file']}")

    return {
        "story_id": story_id,
        "video_dir": paths["video_dir"],
        "config_file": paths["config_file"],
        "log_file": paths["log_file"],
        "youtube_title": filled["youtube_title"].strip(),
        "youtube_description": filled["youtube_description"].strip(),
        "description_story_name": filled["description_story_name"].strip(),
        "author": filled["author"].strip(),
        "genre": filled["genre"].strip(),
        "playlist_id": filled["playlist_id"].strip(),
        "privacy_status": filled["privacy_status"].strip().lower(),
        "tags": filled["tags"].strip(),
        "thumbnail_path": filled["thumbnail_path"].strip(),
        "review_label_position": filled["review_label_position"],
    }


# ============================================================
# AUTHENTICATION
# ============================================================

def _save_credentials(credentials):
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(credentials.to_json())
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:
        pass


def _load_saved_credentials():
    if not os.path.isfile(TOKEN_FILE):
        return None
    try:
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    except (ValueError, OSError) as exc:
        print(f"  Không đọc được token đã lưu ({exc}). Sẽ xác thực lại.")
        return None
    granted = set(credentials.scopes or [])
    if granted and not set(SCOPES).issubset(granted):
        print("  Token không đủ quyền (scopes). Sẽ xác thực lại.")
        return None
    return credentials


def _run_oauth_flow():
    print("  Mở trình duyệt để xác thực Google...")
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        SCOPES,
    )
    credentials = flow.run_local_server(port=0, prompt="consent")
    _save_credentials(credentials)
    print(f"  ✓ Đã lưu token: {TOKEN_FILE}")
    return credentials


def get_authenticated_service():
    """
    Đăng nhập YouTube. Lần đầu mở trình duyệt, sau đó dùng token đã lưu.
    Access token hết hạn được refresh tự động, không cần xác thực lại.
    """
    credentials = _load_saved_credentials()

    if credentials and credentials.valid:
        print(f"  ✓ Dùng token đã lưu: {TOKEN_FILE}")
    elif credentials and credentials.expired and credentials.refresh_token:
        print("  Token hết hạn, đang refresh...")
        try:
            credentials.refresh(Request())
            _save_credentials(credentials)
            print(f"  ✓ Đã refresh token: {TOKEN_FILE}")
        except RefreshError:
            print("  Refresh thất bại, cần xác thực lại trên trình duyệt.")
            credentials = _run_oauth_flow()
    else:
        credentials = _run_oauth_flow()

    return build(
        "youtube",
        "v3",
        credentials=credentials,
    )


# ============================================================
# ĐỌC TAGS
# ============================================================

def parse_tags(content):
    """
    Chuẩn hóa tags cho YouTube API.

    - Bỏ dấu # ở đầu
    - Bỏ khoảng trắng thừa
    - Bỏ tag rỗng
    - Bỏ tag trùng
    - Giới hạn tổng độ dài tags để tránh lỗi invalidTags
    """

    tags = []
    seen = set()

    for tag in content.split(","):
        tag = tag.strip()

        if tag.startswith("#"):
            tag = tag[1:].strip()

        if not tag:
            continue

        normalized = tag.lower()
        if normalized in seen:
            continue

        seen.add(normalized)
        tags.append(tag)

    MAX_TAGS_LENGTH = 450
    valid_tags = []
    total_length = 0

    for tag in tags:
        additional_length = len(tag)
        if valid_tags:
            additional_length += 1

        if total_length + additional_length > MAX_TAGS_LENGTH:
            print(f"⚠️ Bỏ tag do vượt giới hạn: #{tag}")
            continue

        valid_tags.append(tag)
        total_length += additional_length

    print()
    print(f"Tags gốc      : {len(tags)}")
    print(f"Tags sử dụng   : {len(valid_tags)}")
    print(f"Tổng ký tự     : {total_length}")

    return valid_tags


# ============================================================
# TẠO TITLE + DESCRIPTION
# ============================================================

def build_video_title(base_title, part):
    prefix = f"TRUYỆN HAY | "
    suffix = f" ( Phần {part})"
    title = f"{prefix}{base_title}{suffix}"
    if len(title) <= YOUTUBE_TITLE_MAX_LEN:
        return title

    keep = YOUTUBE_TITLE_MAX_LEN - len(suffix)
    if keep < 1:
        return title[:YOUTUBE_TITLE_MAX_LEN]
    return f"{base_title[:keep].rstrip()}{suffix}"


def build_description(
    story_description,
    description_story_name,
    author,
    genre,
    hash_tag,
):
    """
    Tạo description hoàn chỉnh cho YouTube.
    """

    return f"""🎧 {description_story_name}

🔥 **NỘI DUNG TẬP NÀY:**
{story_description}
---

📌 **THÔNG TIN TRUYỆN:**
• Tác giả: {author}
• Thể loại: {genre}

---

👍 Đừng quên **LIKE, SHARE** và **ĐĂNG KÝ KÊNH** để ủng hộ team và không bỏ lỡ các tập tiếp theo nhé!
💬 Hãy để lại bình luận cảm nhận của bạn về truyện bên dưới nha!

{hash_tag}

---
"""


# ============================================================
# UPLOAD 1 VIDEO
# ============================================================

def set_thumbnail(youtube, video_id, thumbnail_path):
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(thumbnail_path)
    ).execute()
    print(f"Đã đặt thumbnail: {thumbnail_path}")


def upload_video(
    youtube,
    file_path,
    title,
    description,
    tags,
    category_id="22",
    privacy_status="private",
    publish_at=None,
    playlist_id=None,
    thumbnail_path=None,
):
    """
    Upload một video lên YouTube.
    Có publish_at thì video ở private và được lên lịch công khai.
    """

    status = {
        "privacyStatus": privacy_status,
        "selfDeclaredMadeForKids": False,
    }
    if publish_at is not None:
        status["privacyStatus"] = "private"
        status["publishAt"] = youtube_publish_at(publish_at)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": status,
    }

    media = MediaFileUpload(
        file_path,
        chunksize=-1,
        resumable=True
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = None

    print()
    print("Đang tải video lên...")

    while response is None:
        status, response = request.next_chunk()

        if status:
            progress = int(status.progress() * 100)
            print(f"  Đã upload: {progress}%")

    video_id = response.get("id")

    print()
    print("✅ Upload thành công!")
    print(f"   Video ID: {video_id}")
    print(f"   URL: https://www.youtube.com/watch?v={video_id}")
    if publish_at is not None:
        print(
            f"   Lên lịch công khai: "
            f"{format_vn_publish_time(publish_at)} giờ VN"
        )

    if playlist_id:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
        print(f"Added to playlist: {playlist_id}")

    if thumbnail_path:
        try:
            set_thumbnail(youtube, video_id, thumbnail_path)
        except Exception as exc:
            print()
            print("⚠️ Không đặt được thumbnail (video đã lên YouTube):")
            print(f"   {exc}")

    return video_id


# ============================================================
# MAIN
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Upload các video part chưa đăng lên YouTube."
    )
    parser.add_argument(
        "--story",
        default="",
        help="Mã truyện / thư mục trong stories/",
    )
    parser.add_argument(
        "--thumbnail",
        default="",
        help="Đường dẫn thumbnail (mặc định: stories/<story>/thumbnail.jpeg)",
    )
    parser.add_argument(
        "--label-position",
        default="",
        help=(
            "Vị trí chữ Tập N trên review image: "
            "top_left / middle_left / bottom_left"
        ),
    )
    return parser.parse_args()


def main():
    print()
    print("=" * 70)
    print("UPLOAD YOUTUBE")
    print("=" * 70)

    args = parse_args()
    config = resolve_upload_config(
        story_id=args.story.strip() or None,
        thumbnail_path=args.thumbnail.strip() or None,
        review_label_position=args.label_position.strip() or None,
    )

    story_id = config["story_id"]
    video_dir = config["video_dir"]
    log_file = config["log_file"]
    privacy_status = config["privacy_status"]
    playlist_id = config["playlist_id"]
    description_story_name = config["description_story_name"]
    author = config["author"]
    genre = config["genre"]
    youtube_title = config["youtube_title"]
    youtube_description = config["youtube_description"]
    thumbnail_path = os.path.abspath(config["thumbnail_path"])
    review_label_position = config["review_label_position"]

    print()
    print("Kiểm tra file...")

    if not os.path.isfile(CLIENT_SECRET_FILE):
        raise FileNotFoundError(
            f"Không tìm thấy file:\n{CLIENT_SECRET_FILE}"
        )
    print(f"  ✓ {CLIENT_SECRET_FILE}")

    if not os.path.isfile(thumbnail_path):
        raise FileNotFoundError(
            f"Không tìm thấy thumbnail:\n{thumbnail_path}"
        )
    print(f"  ✓ {thumbnail_path}")

    part_videos = scan_part_videos(video_dir, story_id)
    print()
    print("Thư mục video:")
    print(f"  {video_dir}")
    print(f"  Số file part: {len(part_videos)}")

    if not part_videos:
        print()
        print(f"Không tìm thấy video dạng {story_id}_partN.mp4 để upload.")
        return

    review_images = create_review_images(
        source_thumbnail=thumbnail_path,
        video_dir=video_dir,
        parts=[part for part, _ in part_videos],
        position=review_label_position,
    )

    upload_log = load_upload_log(log_file)
    uploaded_parts = upload_log["parts"]

    pending = []
    skipped = []
    for part, video_path in part_videos:
        if str(part) in uploaded_parts:
            skipped.append(part)
            continue
        pending.append((part, video_path))

    publish_schedule = schedule_pending_parts(pending, upload_log)

    print()
    print("Đang đọc tags...")
    tags = parse_tags(config["tags"])
    hash_tag = ", ".join(f"#{tag}" for tag in tags)
    description = build_description(
        youtube_description,
        description_story_name,
        author,
        genre,
        hash_tag,
    )

    print()
    print("=" * 70)
    print("CẤU HÌNH UPLOAD")
    print("=" * 70)
    print(f"Mã truyện     : {story_id}")
    print(
        f"Parts         : {', '.join(str(part) for part, _ in part_videos) or 'không'}"
    )
    print(
        f"Đã đăng       : {', '.join(str(part) for part in skipped) if skipped else 'không'}"
    )
    print(
        f"Sẽ upload     : {', '.join(str(part) for part, _ in pending) if pending else 'không'}"
    )
    print(f"Category ID   : {CATEGORY_ID}")
    print(f"Privacy       : {privacy_status} (lên lịch công khai)")
    print(
        f"Giờ đăng      : {PUBLISH_HOUR_VN:02d}:00 giờ Việt Nam, "
        "mỗi tập cách 1 ngày"
    )
    if publish_schedule:
        print("Lịch publish  :")
        for part, _video_path in pending:
            print(
                f"  Phần {part}: "
                f"{format_vn_publish_time(publish_schedule[part])} "
                "(giờ VN)"
            )
    print(f"Playlist ID   : {playlist_id}")
    print(
        "Bình luận     : người đăng ký "
        "(đặt trên YouTube Studio; API không hỗ trợ)"
    )
    print(f"Title gốc     : {youtube_title}")
    print(f"Tên truyện    : {description_story_name}")
    print(f"Tác giả       : {author}")
    print(f"Thể loại      : {genre}")
    print(f"Thumbnail     : {thumbnail_path}")
    print(f"Label position: {review_label_position}")
    print(
        f"Review images : {len(review_images)} file "
        f"(review_partN.jpeg)"
    )
    print(f"Hash tag      : {hash_tag}")
    print(f"Số tags       : {len(tags)}")
    print(f"Log           : {log_file}")
    print("=" * 70)

    if not pending:
        print()
        print("Không có part mới cần upload.")
        print("=" * 70)
        print("HOÀN TẤT")
        print("=" * 70)
        return

    print()
    print("Đang đăng nhập YouTube...")
    youtube = get_authenticated_service()
    print("✓ Đăng nhập YouTube thành công.")

    success = []
    failed = []

    for part, video_path in pending:
        print()
        print()
        print("#" * 70)
        print(f"# PHẦN {part}")
        print("#" * 70)

        video_filename = os.path.basename(video_path)
        print()
        print("File:")
        print(f"  {video_filename}")

        if not os.path.isfile(video_path):
            print()
            print("❌ Không tìm thấy video:")
            print(f"   {video_path}")
            failed.append({
                "part": part,
                "reason": "Không tìm thấy file video",
            })
            continue

        title = build_video_title(youtube_title, part)

        print()
        print("Thông tin upload:")
        print("  Title:")
        print(f"    {title}")
        print()
        print("  Category ID:")
        print(f"    {CATEGORY_ID}")
        print()
        print("  Privacy:")
        print(f"    {privacy_status}")
        print()
        print("  Publish at:")
        print(
            f"    {format_vn_publish_time(publish_schedule[part])} "
            "(giờ VN)"
        )
        print()
        print("  Tags:")
        print(f"    {len(tags)} tags")
        print()
        print("  Review image:")
        print(f"    {review_images[part]}")

        try:
            publish_at = publish_schedule[part]
            video_id = upload_video(
                youtube=youtube,
                file_path=video_path,
                title=title,
                description=description,
                tags=tags,
                category_id=CATEGORY_ID,
                privacy_status=privacy_status,
                publish_at=publish_at,
                playlist_id=playlist_id,
                thumbnail_path=review_images[part],
            )
            mark_part_uploaded(
                log_file,
                part,
                video_id,
                video_filename,
                publish_at=publish_at,
            )
            success.append({
                "part": part,
                "video_id": video_id,
                "publish_at": publish_at,
            })
        except Exception as e:
            print()
            print(f"❌ Upload Phần {part} thất bại!")
            print(f"   Lỗi: {e}")
            failed.append({
                "part": part,
                "reason": str(e),
            })
            continue

    print()
    print()
    print("=" * 70)
    print("KẾT QUẢ UPLOAD")
    print("=" * 70)

    print()
    print(f"✅ Thành công: {len(success)} phần")
    if success:
        for item in success:
            scheduled = item.get("publish_at")
            schedule_text = ""
            if scheduled is not None:
                schedule_text = (
                    f"  (công khai {format_vn_publish_time(scheduled)} giờ VN)"
                )
            print(
                f"   Phần {item['part']}: "
                f"https://www.youtube.com/watch?v={item['video_id']}"
                f"{schedule_text}"
            )

    print()
    print(f"⏭️ Bỏ qua (đã đăng): {len(skipped)} phần")
    if skipped:
        for part in skipped:
            print(f"   Phần {part}")

    print()
    print(f"❌ Thất bại: {len(failed)} phần")
    if failed:
        for item in failed:
            print(f"   Phần {item['part']}: {item['reason']}")

    print()
    print(f"Tổng số file part   : {len(part_videos)}")
    print(f"Thành công          : {len(success)}")
    print(f"Đã đăng từ trước    : {len(skipped)}")
    print(f"Thất bại            : {len(failed)}")

    print()
    print("=" * 70)
    print("HOÀN TẤT")
    print("=" * 70)


if __name__ == "__main__":
    main()
