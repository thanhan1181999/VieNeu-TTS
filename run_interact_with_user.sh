#!/bin/bash
set -e

echo "============================================================"
echo "        Story Video Generator"
echo "============================================================"
echo ""

while true; do read -r -p "Story: " STORY; [ -n "$STORY" ] && break; echo "Story is required."; done
while true; do read -r -p "Start chapter: " START; [ -n "$START" ] && break; echo "Start chapter is required."; done
while true; do read -r -p "End chapter: " END; [ -n "$END" ] && break; echo "End chapter is required."; done
while true; do read -r -p "Content URL: " CONTENT_URL; [ -n "$CONTENT_URL" ] && break; echo "Content URL is required."; done
while true; do read -r -p "Title URL: " TITLE_URL; [ -n "$TITLE_URL" ] && break; echo "Title URL is required."; done

DEFAULT_CRAW_SELECTOR="#chapter-c"
DEFAULT_CRAW_TITLE_SELECTOR="#list-chapter ul.list-chapter"

read -r -p "Crawl selector [$DEFAULT_CRAW_SELECTOR]: " CRAW_SELECTOR
CRAW_SELECTOR="${CRAW_SELECTOR:-$DEFAULT_CRAW_SELECTOR}"

read -r -p "Crawl title selector [$DEFAULT_CRAW_TITLE_SELECTOR]: " CRAW_TITLE_SELECTOR
CRAW_TITLE_SELECTOR="${CRAW_TITLE_SELECTOR:-$DEFAULT_CRAW_TITLE_SELECTOR}"

DEFAULT_VOICE_PATH="stories/voices/reference.wav"
read -r -p "Voice path [$DEFAULT_VOICE_PATH]: " VOICE_PATH
VOICE_PATH="${VOICE_PATH:-$DEFAULT_VOICE_PATH}"

while true; do
    read -r -p "Image cover file path (required): " IMAGE_COVER_FILE_PATH
    [ -n "$IMAGE_COVER_FILE_PATH" ] && break
    echo "Image cover file path is required."
done

read_boolean() {
    local prompt="$1" default="$2" value
    while true; do
        if [ "$default" = true ]; then read -r -p "$prompt [Y/n]: " value; else read -r -p "$prompt [y/N]: " value; fi
        case "${value:-}" in
            y|Y|yes|YES|Yes) echo true; return;;
            n|N|no|NO|No) echo false; return;;
            "") echo "$default"; return;;
            *) echo "Please enter y/yes or n/no." >&2;;
        esac
    done
}

CRAWL_AND_CLEAN=$(read_boolean "Crawl & Clean?" true)
GENERATE_AUDIO=$(read_boolean "Generate Audio?" true)
CRAWLING_TITLE=$(read_boolean "Crawling Title?" true)
GENERATE_VIDEO=$(read_boolean "Generate Video?" true)

STORY_DIR="stories/$STORY"
VOICE_DIR="$STORY_DIR/voice"
AUDIO_DIR="$STORY_DIR/audio"
SCRIPT_DIR="$STORY_DIR/script"

# Validate source files before modifying the story directory.
if [ ! -f "$VOICE_PATH" ]; then
    echo "ERROR: Voice file not found: $VOICE_PATH"
    exit 1
fi
if [ ! -f "$IMAGE_COVER_FILE_PATH" ]; then
    echo "ERROR: Cover image file not found: $IMAGE_COVER_FILE_PATH"
    exit 1
fi

# Keep the original image extension.
COVER_EXTENSION="${IMAGE_COVER_FILE_PATH##*.}"
COVER_DEST="$STORY_DIR/cover.$COVER_EXTENSION"
VOICE_DEST="$VOICE_DIR/reference.wav"

mkdir -p "$AUDIO_DIR" "$SCRIPT_DIR" "$VOICE_DIR"

# Do not overwrite existing destination files.
if [ -e "$VOICE_DEST" ]; then
    echo "WARNING: Voice destination already exists: $VOICE_DEST"
    echo "Refusing to overwrite the existing file."
else
    cp "$VOICE_PATH" "$VOICE_DEST"
fi
if [ -e "$COVER_DEST" ]; then
    echo "WARING: Cover destination already exists: $COVER_DEST"
    echo "Refusing to overwrite the existing file."
else
    mv "$IMAGE_COVER_FILE_PATH" "$COVER_DEST"
fi


echo ""
echo "============================================================"
echo "Configuration"
echo "============================================================"
echo "Story                : $STORY"
echo "Chapters             : $START -> $END"
echo "Content URL          : $CONTENT_URL"
echo "Title URL            : $TITLE_URL"
echo "Crawl selector       : $CRAW_SELECTOR"
echo "Crawl title selector : $CRAW_TITLE_SELECTOR"
echo "Voice Path           : $VOICE_PATH"
echo "Cover Image          : $COVER_DEST"
echo "------------------------------------------------------------"
echo "Crawl & Clean        : $CRAWL_AND_CLEAN"
echo "Generate Audio       : $GENERATE_AUDIO"
echo "Crawling Title       : $CRAWLING_TITLE"
echo "Generate Video       : $GENERATE_VIDEO"
echo "============================================================"

echo ""
# Kiểm tra và yêu cầu nhập phần giới thiệu nếu chưa có 0.txt
if [ ! -f "$SCRIPT_DIR/0.txt" ]; then
    echo "=== Kiểm tra giới thiệu truyện ==="
    echo "Chưa tìm thấy $SCRIPT_DIR/0.txt."
    echo "Vui lòng nhập nội dung giới thiệu truyện (bấm Enter để xuống dòng, bấm Ctrl+D để hoàn tất):"
    echo "------------------------------------------------------------"
        
    # Đọc dữ liệu nhiều dòng từ terminal cho đến khi bấm Ctrl+D
    cat > "$SCRIPT_DIR/0.txt"

    echo "------------------------------------------------------------"
    echo "Đã lưu nội dung vào $SCRIPT_DIR/0.txt"
    echo ""
fi

if [ "$CRAWL_AND_CLEAN" = true ]; then
    echo ""
    echo "=== 1. Crawling Content $STORY ($START -> $END) ==="
    node craw/crawl.js --story "$STORY" --start "$START" --end "$END" --url "$CONTENT_URL" --selector "$CRAW_SELECTOR"
    echo ""
    echo "=== 2. Cleaning Content $STORY ($START -> $END) ==="
    node craw/clean1.js "$STORY"
else
    echo ""
    echo "=== 1-2. Crawling & Cleaning SKIPPED ==="
fi

if [ "$GENERATE_AUDIO" = true ]; then
    echo ""
    echo "=== 3. Generating TTS Audio ==="
    caffeinate -i uv run python tts/make_audio.py stories/"$STORY" --mode v3turbo --max-chars 512 --batch-size 16 --start "$START" --end "$END" --steps 8
else
    echo ""
    echo "=== 3. Generating TTS Audio SKIPPED ==="
fi

if [ "$CRAWLING_TITLE" = true ]; then
    echo ""
    echo "=== 4. Crawling Titles ==="
    node craw/crawl_title.js --url "$TITLE_URL" --story "$STORY" --selector "$CRAW_TITLE_SELECTOR"
else
    echo ""
    echo "=== 4. Crawling Titles SKIPPED ==="
fi

if [ "$GENERATE_VIDEO" = true ]; then
    echo ""
    echo "=== 5. Making Video ==="
    caffeinate -i uv run python tts/make_video_ver4.py "$STORY" "$START" "$END"
else
    echo ""
    echo "=== 5. Making Video SKIPPED ==="
fi

echo ""
echo "=== DONE! ==="
