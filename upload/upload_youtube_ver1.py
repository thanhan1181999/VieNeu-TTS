import os
import re

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ============================================================
# CẤU HÌNH
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

# Thư mục chứa script hiện tại
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# File title + description
TITLE_DESCRIPTION_FILE = os.path.join(
    BASE_DIR,
    "title_and_desscription.txt"
)

# File tags
TAGS_FILE = os.path.join(
    BASE_DIR,
    "tag.txt"
)

# File OAuth
CLIENT_SECRET_FILE = os.path.join(
    BASE_DIR,
    "client_secret.json"
)

# YouTube category
# 22 = People & Blogs
CATEGORY_ID = "22"

# private / unlisted / public
DEFAULT_PRIVACY_STATUS = "public"

DEFAULT_PLAYLIST_ID = "PLerSSQqUz9Wc"

# YouTube Data API không hỗ trợ đặt "who can comment" khi upload.
# Mặc định mong muốn: chỉ người đăng ký được bình luận.
# Cần đặt sẵn trên YouTube Studio (Settings > Community).

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


def ask_int(prompt):
    while True:
        value = input(prompt).strip()
        try:
            return int(value)
        except ValueError:
            print("Vui lòng nhập số nguyên.")


def ask_privacy(default=DEFAULT_PRIVACY_STATUS):
    allowed = {"public", "unlisted", "private"}

    while True:
        value = input(
            f"Privacy status [{default}] "
            "(public / unlisted / private): "
        ).strip().lower()

        if not value:
            return default

        if value in allowed:
            return value

        print("Chỉ nhận: public / unlisted / private")


def parse_skip_parts(text):
    text = text.strip()

    if not text:
        return []

    parts = []

    for item in text.split(","):
        item = item.strip()

        if not item:
            continue

        parts.append(int(item))

    return parts


def prompt_upload_config():
    print()
    print("Nhập cấu hình upload:")
    print()

    story_id = ask_required(
        "Mã truyện / thư mục video (ví dụ tn60): "
    )

    video_dir = os.path.abspath(
        os.path.join(BASE_DIR, "../stories", story_id)
    )

    start_part = ask_int("Phần bắt đầu: ")
    end_part = ask_int("Phần kết thúc: ")

    while end_part < start_part:
        print("Phần kết thúc phải >= phần bắt đầu.")
        end_part = ask_int("Phần kết thúc: ")

    while True:
        skip_raw = input(
            "Các phần bỏ qua (ví dụ 3,5,7; Enter = không skip): "
        ).strip()

        try:
            skip_parts = parse_skip_parts(skip_raw)
            break
        except ValueError:
            print("Vui lòng nhập các số, cách nhau bởi dấu phẩy.")

    privacy_status = ask_privacy()

    playlist_id = ask_with_default(
        f"Playlist ID [{DEFAULT_PLAYLIST_ID}]: ",
        DEFAULT_PLAYLIST_ID
    )

    description_story_name = ask_required(
        "Tên truyện (description_story_name): "
    )

    author = ask_required("Tác giả: ")
    genre = ask_required("Thể loại: ")

    return {
        "story_id": story_id,
        "video_dir": video_dir,
        "start_part": start_part,
        "end_part": end_part,
        "skip_parts": skip_parts,
        "privacy_status": privacy_status,
        "playlist_id": playlist_id,
        "description_story_name": description_story_name,
        "author": author,
        "genre": genre,
    }


# ============================================================
# AUTHENTICATION
# ============================================================

def get_authenticated_service():
    """
    Đăng nhập YouTube một lần.
    Service này sẽ được dùng cho toàn bộ các video.
    """

    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        SCOPES
    )

    credentials = flow.run_local_server(port=0)

    return build(
        "youtube",
        "v3",
        credentials=credentials
    )


# ============================================================
# ĐỌC TITLE + DESCRIPTION
# ============================================================

def load_title_descriptions(file_path):
    """
    Đọc title và description từ file có format:

    Phần 1: ...
    Tiêu đề YouTube: ...
    Mô tả (Description): ...

    Phần 2: ...
    Tiêu đề YouTube: ...
    Mô tả (Description): ...

    ...

    Trả về:

    {
        1: {
            "title": "...",
            "description": "..."
        },
        2: {
            "title": "...",
            "description": "..."
        }
    }
    """

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:
        lines = f.readlines()

    result = {}

    current_part = None
    current_title = None
    current_description = []

    reading_description = False

    for raw_line in lines:

        line = raw_line.rstrip("\n")

        # ----------------------------------------------------
        # Phần X:
        # ----------------------------------------------------

        match = re.match(
            r"^\s*Tập\s+(\d+)\s*:",
            line
        )

        if match:

            # Lưu phần trước đó
            if (
                current_part is not None
                and current_title is not None
            ):
                result[current_part] = {
                    "title": current_title.strip(),
                    "description": "\n".join(
                        current_description
                    ).strip()
                }

            current_part = int(
                match.group(1)
            )

            current_title = None
            current_description = []

            reading_description = False

            continue

        # ----------------------------------------------------
        # Tiêu đề YouTube:
        # ----------------------------------------------------

        if line.startswith(
            "Tiêu đề YouTube:"
        ):

            current_title = line[
                len("Tiêu đề YouTube:"):
            ].strip()

            reading_description = False

            continue

        # ----------------------------------------------------
        # Mô tả (Description):
        # ----------------------------------------------------

        if line.startswith(
            "Mô tả (Description):"
        ):

            description_first_line = line[
                len("Mô tả (Description):"):
            ].strip()

            current_description = []

            if description_first_line:
                current_description.append(
                    description_first_line
                )

            reading_description = True

            continue

        # ----------------------------------------------------
        # Nội dung description
        # ----------------------------------------------------

        if reading_description:

            current_description.append(
                line
            )

    # --------------------------------------------------------
    # Lưu phần cuối cùng
    # --------------------------------------------------------

    if (
        current_part is not None
        and current_title is not None
    ):
        result[current_part] = {
            "title": current_title.strip(),
            "description": "\n".join(
                current_description
            ).strip()
        }

    return result

# ============================================================
# ĐỌC TAGS
# ============================================================

def load_tags(file_path):
    """
    Đọc tags từ file và chuẩn hóa cho YouTube API.

    - Bỏ dấu # ở đầu
    - Bỏ khoảng trắng thừa
    - Bỏ tag rỗng
    - Bỏ tag trùng
    - Giới hạn tổng độ dài tags để tránh lỗi invalidTags
    """

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:
        content = f.read()

    tags = []
    seen = set()

    for tag in content.split(","):

        tag = tag.strip()

        # Bỏ dấu #
        if tag.startswith("#"):
            tag = tag[1:].strip()

        if not tag:
            continue

        # Chuẩn hóa để kiểm tra trùng
        normalized = tag.lower()

        if normalized in seen:
            continue

        seen.add(normalized)

        tags.append(tag)

    # --------------------------------------------------------
    # Giới hạn tổng độ dài tags
    #
    # YouTube giới hạn tổng số ký tự của video tags.
    # Giữ một khoảng an toàn thay vì sử dụng sát giới hạn.
    # --------------------------------------------------------

    MAX_TAGS_LENGTH = 450

    valid_tags = []
    total_length = 0

    for tag in tags:

        # +1 cho dấu phân cách giữa các tag
        additional_length = len(tag)

        if valid_tags:
            additional_length += 1

        if total_length + additional_length > MAX_TAGS_LENGTH:
            print(
                f"⚠️ Bỏ tag do vượt giới hạn: #{tag}"
            )
            continue

        valid_tags.append(tag)

        total_length += additional_length

    print()
    print(
        f"Tags gốc      : {len(tags)}"
    )

    print(
        f"Tags sử dụng   : {len(valid_tags)}"
    )

    print(
        f"Tổng ký tự     : {total_length}"
    )

    return valid_tags

# ============================================================
# TẠO DESCRIPTION
# ============================================================

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

def upload_video(
    youtube,
    file_path,
    title,
    description,
    tags,
    category_id="22",
    privacy_status="private",
    playlist_id=None
):
    """
    Upload một video lên YouTube.
    """

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },

        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
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
            progress = int(
                status.progress() * 100
            )

            print(
                f"  Đã upload: {progress}%"
            )

    video_id = response.get("id")

    print()
    print("✅ Upload thành công!")
    print(f"   Video ID: {video_id}")
    print(
        f"   URL: https://www.youtube.com/watch?v={video_id}"
    )

    # ==========================================
    # ADD VIDEO VÀO PLAYLIST
    # ==========================================

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

    return video_id


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("UPLOAD YOUTUBE")
    print("=" * 70)

    config = prompt_upload_config()

    story_id = config["story_id"]
    video_dir = config["video_dir"]
    start_part = config["start_part"]
    end_part = config["end_part"]
    skip_parts = config["skip_parts"]
    privacy_status = config["privacy_status"]
    playlist_id = config["playlist_id"]
    description_story_name = config["description_story_name"]
    author = config["author"]
    genre = config["genre"]

    # --------------------------------------------------------
    # Kiểm tra các file cần thiết
    # --------------------------------------------------------

    print()
    print("Kiểm tra file...")

    required_files = [
        TITLE_DESCRIPTION_FILE,
        TAGS_FILE,
        CLIENT_SECRET_FILE
    ]

    for file_path in required_files:

        if not os.path.isfile(file_path):

            raise FileNotFoundError(
                f"Không tìm thấy file:\n{file_path}"
            )

        print(f"  ✓ {file_path}")

    # --------------------------------------------------------
    # Kiểm tra thư mục video
    # --------------------------------------------------------

    if not os.path.isdir(video_dir):

        raise FileNotFoundError(
            f"Không tìm thấy thư mục video:\n{video_dir}"
        )

    print()
    print(f"Thư mục video:")
    print(f"  {video_dir}")

    # --------------------------------------------------------
    # Đọc title + description
    # --------------------------------------------------------

    print()
    print("Đang đọc title + description...")

    title_descriptions = load_title_descriptions(
        TITLE_DESCRIPTION_FILE
    )

    print(
        f"✓ Đã đọc {len(title_descriptions)} phần."
    )

    # --------------------------------------------------------
    # Đọc tags
    # --------------------------------------------------------

    print()
    print("Đang đọc tags...")

    tags = load_tags(
        TAGS_FILE
    )

    hash_tag = ", ".join(
        f"#{tag}" for tag in tags
    )

    print(
        f"✓ Đã đọc {len(tags)} tags."
    )

    # --------------------------------------------------------
    # Hiển thị cấu hình
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("CẤU HÌNH UPLOAD")
    print("=" * 70)

    print(
        f"Mã truyện     : {story_id}"
    )

    print(
        f"Phần bắt đầu : {start_part}"
    )

    print(
        f"Phần kết thúc : {end_part}"
    )

    print(
        f"Bỏ qua        : {skip_parts if skip_parts else 'không'}"
    )

    print(
        f"Category ID   : {CATEGORY_ID}"
    )

    print(
        f"Privacy       : {privacy_status}"
    )

    print(
        f"Playlist ID   : {playlist_id}"
    )

    print(
        f"Bình luận     : người đăng ký "
        "(đặt trên YouTube Studio; API không hỗ trợ)"
    )

    print(
        f"Tên truyện    : {description_story_name}"
    )

    print(
        f"Tác giả       : {author}"
    )

    print(
        f"Thể loại      : {genre}"
    )

    print(
        f"Hash tag      : {hash_tag}"
    )

    print(
        f"Số tags       : {len(tags)}"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Đăng nhập YouTube MỘT LẦN
    # --------------------------------------------------------

    print()
    print("Đang đăng nhập YouTube...")

    youtube = get_authenticated_service()

    print("✓ Đăng nhập YouTube thành công.")

    # --------------------------------------------------------
    # Danh sách kết quả
    # --------------------------------------------------------

    success = []

    failed = []

    # --------------------------------------------------------
    # Upload từng phần
    # --------------------------------------------------------

    for part in range(
        start_part,
        end_part + 1
    ):

        if part in skip_parts:
                print(f"⏭️ PHẦN {part}: SKIP")
                continue
        print()
        print()
        print("#" * 70)
        print(f"# PHẦN {part}")
        print("#" * 70)

        # ----------------------------------------------------
        # Tên file video
        # ----------------------------------------------------

        video_filename = (
            f"{story_id}_part{part}.mp4"
        )

        video_path = os.path.join(
            video_dir,
            video_filename
        )

        print()
        print(f"File:")
        print(f"  {video_filename}")

        # ----------------------------------------------------
        # Kiểm tra video
        # ----------------------------------------------------

        if not os.path.isfile(video_path):

            print()
            print("❌ Không tìm thấy video:")
            print(f"   {video_path}")

            failed.append({
                "part": part,
                "reason": "Không tìm thấy file video"
            })

            continue

        # ----------------------------------------------------
        # Kiểm tra title + description
        # ----------------------------------------------------

        if part not in title_descriptions:

            print()
            print(
                f"❌ Không tìm thấy "
                f"title/description của Phần {part}"
            )

            failed.append({
                "part": part,
                "reason": (
                    "Không tìm thấy title/description"
                )
            })

            continue

        # ----------------------------------------------------
        # Lấy title
        # ----------------------------------------------------

        title = title_descriptions[part]["title"]

        # ----------------------------------------------------
        # Lấy description riêng của phần
        # ----------------------------------------------------

        story_description = (
            title_descriptions[part]["description"]
        )

        # ----------------------------------------------------
        # Tạo description hoàn chỉnh
        # ----------------------------------------------------

        description = build_description(
            story_description,
            description_story_name,
            author,
            genre,
            hash_tag,
        )

        # ----------------------------------------------------
        # Hiển thị thông tin
        # ----------------------------------------------------

        print()
        print("Thông tin upload:")
        print(f"  Title:")
        print(f"    {title}")

        print()
        print(f"  Category ID:")
        print(f"    {CATEGORY_ID}")

        print()
        print(f"  Privacy:")
        print(f"    {privacy_status}")

        print()
        print(f"  Tags:")
        print(f"    {len(tags)} tags")

        # ----------------------------------------------------
        # Upload
        # ----------------------------------------------------

        try:

            video_id = upload_video(
                youtube=youtube,
                file_path=video_path,
                title=title,
                description=description,
                tags=tags,
                category_id=CATEGORY_ID,
                privacy_status=privacy_status,
                playlist_id=playlist_id 
            )

            success.append({
                "part": part,
                "video_id": video_id
            })

        except Exception as e:

            print()
            print(
                f"❌ Upload Phần {part} thất bại!"
            )

            print(
                f"   Lỗi: {e}"
            )

            failed.append({
                "part": part,
                "reason": str(e)
            })

            # Không dừng chương trình.
            # Tiếp tục upload phần tiếp theo.
            continue

    # ========================================================
    # TỔNG KẾT
    # ========================================================

    print()
    print()
    print("=" * 70)
    print("KẾT QUẢ UPLOAD")
    print("=" * 70)

    # --------------------------------------------------------
    # Thành công
    # --------------------------------------------------------

    print()
    print(
        f"✅ Thành công: {len(success)} phần"
    )

    if success:

        for item in success:

            part = item["part"]

            video_id = item["video_id"]

            print(
                f"   Phần {part}: "
                f"https://www.youtube.com/watch?v={video_id}"
            )

    # --------------------------------------------------------
    # Thất bại
    # --------------------------------------------------------

    print()
    print(
        f"❌ Thất bại: {len(failed)} phần"
    )

    if failed:

        for item in failed:

            print(
                f"   Phần {item['part']}: "
                f"{item['reason']}"
            )

    # --------------------------------------------------------
    # Tổng số
    # --------------------------------------------------------

    total = end_part - start_part + 1

    print()
    print(
        f"Tổng số cần upload: {total}"
    )

    print(
        f"Thành công          : {len(success)}"
    )

    print(
        f"Thất bại            : {len(failed)}"
    )

    print()
    print("=" * 70)
    print("HOÀN TẤT")
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()