# có thể sửa thêm public, playlist, who can comment
import os
import re

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ============================================================
# CẤU HÌNH
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]

# Thư mục chứa script hiện tại
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Thư mục chứa các video
VIDEO_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "../stories/truyen-001")
)

# File title + description
TITLE_DESCRIPTION_FILE = os.path.join(
    BASE_DIR,
    "title_and_desscription.txt"
)

# File tags
TAGS_FILE = os.path.join(
    BASE_DIR,
    "thieu_gia_bi_bo_roi_tag.txt"
)

# File OAuth
CLIENT_SECRET_FILE = os.path.join(
    BASE_DIR,
    "client_secret.json"
)

# Upload từ Phần 4 đến Phần 34
START_PART = 8
END_PART = 34

# YouTube category
# 22 = People & Blogs
CATEGORY_ID = "22"

# private / unlisted / public
PRIVACY_STATUS = "public"

PLAYLIST_ID= "PLerSSQqUz9Wc"

SKIP_PARTS = [1,2,3,4,5,6,7,9,10,11,12,14,13,15,16,20,21]

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

def build_description(story_description):
    """
    Tạo description hoàn chỉnh cho YouTube.
    """

    return f"""🎧 **Thiếu Gia Bị Bỏ Rơi**
Mời các bạn cùng nghe bộ truyện Đô Thị - Tiên Hiệp - Trọng Sinh siêu hay của tác giả Nga Thị Lão Ngũ!

🔥 **NỘI DUNG TẬP NÀY:**
{story_description}
---

📌 **THÔNG TIN TRUYỆN:**
• Tác giả: Nga Thị Lão Ngũ
• Thể loại: Tiên Hiệp, Đô Thị, Trọng Sinh, Huyền Huyễn

---

👍 Đừng quên **LIKE, SHARE** và **ĐĂNG KÝ KÊNH** để ủng hộ team và không bỏ lỡ các tập tiếp theo nhé!
💬 Hãy để lại bình luận cảm nhận của bạn về truyện bên dưới nha!

#ThieuGiaBiBoRoi #AudioTruyen #TruyenTienHiep #TruyenDoThi #DiepMac #TruyenFull

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

    # video_id = response["id"]

    # if playlist_id:
    #     youtube.playlistItems().insert(
    #         part="snippet",
    #         body={
    #             "snippet": {
    #                 "playlistId": playlist_id,
    #                 "resourceId": {
    #                     "kind": "youtube#video",
    #                     "videoId": video_id
    #                 }
    #             }
    #         }
    #     ).execute()

    #     print(f"Added to playlist: {playlist_id}")
    return video_id


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("UPLOAD YOUTUBE")
    print("THIẾU GIA BỊ BỎ RƠI")
    print("=" * 70)

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

    if not os.path.isdir(VIDEO_DIR):

        raise FileNotFoundError(
            f"Không tìm thấy thư mục video:\n{VIDEO_DIR}"
        )

    print()
    print(f"Thư mục video:")
    print(f"  {VIDEO_DIR}")

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
        f"Phần bắt đầu : {START_PART}"
    )

    print(
        f"Phần kết thúc : {END_PART}"
    )

    print(
        f"Category ID   : {CATEGORY_ID}"
    )

    print(
        f"Privacy       : {PRIVACY_STATUS}"
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
        START_PART,
        END_PART + 1
    ):

        if part in SKIP_PARTS:
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
            f"truyen-001_0_2271_part{part}.mp4"
        )

        video_path = os.path.join(
            VIDEO_DIR,
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
            story_description
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
        print(f"    {PRIVACY_STATUS}")

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
                privacy_status=PRIVACY_STATUS,
                playlist_id=PLAYLIST_ID   
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

    total = END_PART - START_PART + 1

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