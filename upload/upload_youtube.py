import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Phạm vi truy cập (Scope) bắt buộc để upload video
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    """Xác thực người dùng và khởi tạo YouTube API client."""
    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    credentials = flow.run_local_server(port=0)
    return build('youtube', 'v3', credentials=credentials)

def upload_video(file_path, title, description, category_id="22", privacy_status="private"):
    """
    Upload video lên YouTube.
    
    privacy_status: 'private' (riêng tư), 'unlisted' (không công khai), 'public' (công khai)
    category_id: 22 (People & Blogs), 28 (Science & Technology), 20 (Gaming)...
    """
    youtube = get_authenticated_service()

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['python', 'upload', 'automation'],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    # Upload video dưới dạng Resumable Media Upload (chia nhỏ file để upload ổn định)
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    print("Đang tải video lên...")
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Đã upload {int(status.progress() * 100)}%")

    print(f"Upload thành công! Video ID: {response.get('id')}")

if __name__ == '__main__':
    # Đổi đường dẫn tới file video của bạn
    VIDEO_PATH = "/Users/a.nguyen/projects/vieneu-test/VieNeu-TTS/stories/truyen-001/truyen-001_0_2271_part3.mp4"
    
    upload_video(
        file_path=VIDEO_PATH,
        title="Video Test Upload từ Python",
        description="Video này được tự động tải lên bằng Python Script.",
        privacy_status="private" # Khuyên dùng 'private' hoặc 'unlisted' khi chạy thử
    )