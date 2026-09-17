#!/bin/bash
set -e

echo "============================================================"
echo "        Story Video Generator"
echo "============================================================"
echo ""

DEFAULT_CRAW_SELECTOR="#chapter-c"
DEFAULT_CRAW_TITLE_SELECTOR="#list-chapter ul.list-chapter"
DEFAULT_VOICE_PATH="stories/voices/reference.wav"

read_required() {
    local prompt="$1" value
    while true; do
        read -r -p "$prompt" value
        [ -n "$value" ] && echo "$value" && return
        echo "This field is required." >&2
    done
}

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

find_cover() {
    local dir="$1" match
    match=$(find "$dir" -maxdepth 1 -type f -name 'cover.*' 2>/dev/null | head -n 1 || true)
    echo "$match"
}

load_config_value() {
    local file="$1" key="$2" default="${3:-}"
    python3 -c "
import json, sys
path, key, default = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, encoding='utf-8') as f:
    data = json.load(f)
value = data.get(key, default)
if value is None:
    value = default
if isinstance(value, bool):
    print('true' if value else 'false')
else:
    print(value)
" "$file" "$key" "$default"
}

save_config() {
    local file="$1"
    CONTENT_URL="$CONTENT_URL" \
    TITLE_URL="$TITLE_URL" \
    CRAW_SELECTOR="$CRAW_SELECTOR" \
    CRAW_TITLE_SELECTOR="$CRAW_TITLE_SELECTOR" \
    START="$START" \
    END="$END" \
    CRAWL_AND_CLEAN="$CRAWL_AND_CLEAN" \
    GENERATE_AUDIO="$GENERATE_AUDIO" \
    CRAWLING_TITLE="$CRAWLING_TITLE" \
    GENERATE_VIDEO="$GENERATE_VIDEO" \
    ADD_EPISODE_LABEL="$ADD_EPISODE_LABEL" \
    python3 -c "
import json, os
config = {
    'content_url': os.environ['CONTENT_URL'],
    'title_url': os.environ['TITLE_URL'],
    'crawl_selector': os.environ['CRAW_SELECTOR'],
    'crawl_title_selector': os.environ['CRAW_TITLE_SELECTOR'],
    'last_start': os.environ['START'],
    'last_end': os.environ['END'],
    'crawl_and_clean': os.environ['CRAWL_AND_CLEAN'] == 'true',
    'generate_audio': os.environ['GENERATE_AUDIO'] == 'true',
    'crawling_title': os.environ['CRAWLING_TITLE'] == 'true',
    'generate_video': os.environ['GENERATE_VIDEO'] == 'true',
    'add_episode_label': os.environ['ADD_EPISODE_LABEL'] == 'true',
}
path = '''$file'''
with open(path, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(f'Saved config: {path}')
"
}

# --- Always ask story name first ---
STORY=$(read_required "Story: ")
STORY_DIR="stories/$STORY"
CONFIG_FILE="$STORY_DIR/config.json"
VOICE_DIR="$STORY_DIR/voice"
AUDIO_DIR="$STORY_DIR/audio"
SCRIPT_DIR="$STORY_DIR/script"
VOICE_DEST="$VOICE_DIR/reference.wav"

if [ -f "$CONFIG_FILE" ]; then
    # ===== SHORT MODE: story already configured =====
    echo ""
    echo "Found existing config: $CONFIG_FILE"
    echo "Short mode — only chapter range and optional steps are required."
    echo ""

    CONTENT_URL=$(load_config_value "$CONFIG_FILE" content_url)
    TITLE_URL=$(load_config_value "$CONFIG_FILE" title_url)
    CRAW_SELECTOR=$(load_config_value "$CONFIG_FILE" crawl_selector "$DEFAULT_CRAW_SELECTOR")
    CRAW_TITLE_SELECTOR=$(load_config_value "$CONFIG_FILE" crawl_title_selector "$DEFAULT_CRAW_TITLE_SELECTOR")

    LAST_START=$(load_config_value "$CONFIG_FILE" last_start)
    LAST_END=$(load_config_value "$CONFIG_FILE" last_end)

    if [ -n "$LAST_START" ] && [ -n "$LAST_END" ]; then
        echo "Last run chapters: $LAST_START -> $LAST_END"
    fi

    START=$(read_required "Start chapter: ")
    END=$(read_required "End chapter: ")

    DEFAULT_CRAWL_AND_CLEAN=$(load_config_value "$CONFIG_FILE" crawl_and_clean true)
    DEFAULT_GENERATE_AUDIO=$(load_config_value "$CONFIG_FILE" generate_audio true)
    DEFAULT_CRAWLING_TITLE=$(load_config_value "$CONFIG_FILE" crawling_title true)
    DEFAULT_GENERATE_VIDEO=$(load_config_value "$CONFIG_FILE" generate_video true)

    CRAWL_AND_CLEAN=$(read_boolean "Crawl & Clean?" "$DEFAULT_CRAWL_AND_CLEAN")
    GENERATE_AUDIO=$(read_boolean "Generate Audio?" "$DEFAULT_GENERATE_AUDIO")
    CRAWLING_TITLE=$(read_boolean "Crawling Title?" "$DEFAULT_CRAWLING_TITLE")
    GENERATE_VIDEO=$(read_boolean "Generate Video?" "$DEFAULT_GENERATE_VIDEO")

    COVER_DEST=$(find_cover "$STORY_DIR")
    if [ -z "$COVER_DEST" ]; then
        echo "ERROR: Cover image not found in $STORY_DIR (expected cover.*)."
        exit 1
    fi
    if [ ! -f "$VOICE_DEST" ]; then
        echo "ERROR: Voice file not found: $VOICE_DEST"
        exit 1
    fi

elif [ -d "$STORY_DIR" ]; then
    # ===== LEGACY: story folder exists but no config.json yet =====
    echo ""
    echo "Story folder exists but no config.json found."
    echo "Collecting missing settings once, then saving config for next runs."
    echo ""

    START=$(read_required "Start chapter: ")
    END=$(read_required "End chapter: ")
    CONTENT_URL=$(read_required "Content URL: ")
    TITLE_URL=$(read_required "Title URL: ")

    read -r -p "Crawl selector [$DEFAULT_CRAW_SELECTOR]: " CRAW_SELECTOR
    CRAW_SELECTOR="${CRAW_SELECTOR:-$DEFAULT_CRAW_SELECTOR}"

    read -r -p "Crawl title selector [$DEFAULT_CRAW_TITLE_SELECTOR]: " CRAW_TITLE_SELECTOR
    CRAW_TITLE_SELECTOR="${CRAW_TITLE_SELECTOR:-$DEFAULT_CRAW_TITLE_SELECTOR}"

    COVER_DEST=$(find_cover "$STORY_DIR")
    if [ -z "$COVER_DEST" ]; then
        while true; do
            IMAGE_COVER_FILE_PATH=$(read_required "Image cover file path (required): ")
            [ -f "$IMAGE_COVER_FILE_PATH" ] && break
            echo "ERROR: Cover image file not found: $IMAGE_COVER_FILE_PATH"
        done
        COVER_EXTENSION="${IMAGE_COVER_FILE_PATH##*.}"
        COVER_DEST="$STORY_DIR/cover.$COVER_EXTENSION"
        NEED_MOVE_COVER=true
    else
        NEED_MOVE_COVER=false
        echo "Using existing cover: $COVER_DEST"
    fi

    if [ -f "$VOICE_DEST" ]; then
        NEED_COPY_VOICE=false
        echo "Using existing voice: $VOICE_DEST"
    else
        read -r -p "Voice path [$DEFAULT_VOICE_PATH]: " VOICE_PATH
        VOICE_PATH="${VOICE_PATH:-$DEFAULT_VOICE_PATH}"
        if [ ! -f "$VOICE_PATH" ]; then
            echo "ERROR: Voice file not found: $VOICE_PATH"
            exit 1
        fi
        NEED_COPY_VOICE=true
    fi

    CRAWL_AND_CLEAN=$(read_boolean "Crawl & Clean?" true)
    GENERATE_AUDIO=$(read_boolean "Generate Audio?" true)
    CRAWLING_TITLE=$(read_boolean "Crawling Title?" true)
    GENERATE_VIDEO=$(read_boolean "Generate Video?" true)

else
    # ===== FULL MODE: brand-new story =====
    echo ""
    echo "New story — please enter full configuration."
    echo ""

    START=$(read_required "Start chapter: ")
    END=$(read_required "End chapter: ")
    CONTENT_URL=$(read_required "Content URL: ")
    TITLE_URL=$(read_required "Title URL: ")

    read -r -p "Crawl selector [$DEFAULT_CRAW_SELECTOR]: " CRAW_SELECTOR
    CRAW_SELECTOR="${CRAW_SELECTOR:-$DEFAULT_CRAW_SELECTOR}"

    read -r -p "Crawl title selector [$DEFAULT_CRAW_TITLE_SELECTOR]: " CRAW_TITLE_SELECTOR
    CRAW_TITLE_SELECTOR="${CRAW_TITLE_SELECTOR:-$DEFAULT_CRAW_TITLE_SELECTOR}"

    read -r -p "Voice path [$DEFAULT_VOICE_PATH]: " VOICE_PATH
    VOICE_PATH="${VOICE_PATH:-$DEFAULT_VOICE_PATH}"

    IMAGE_COVER_FILE_PATH=$(read_required "Image cover file path (required): ")

    CRAWL_AND_CLEAN=$(read_boolean "Crawl & Clean?" true)
    GENERATE_AUDIO=$(read_boolean "Generate Audio?" true)
    CRAWLING_TITLE=$(read_boolean "Crawling Title?" true)
    GENERATE_VIDEO=$(read_boolean "Generate Video?" true)

    if [ ! -f "$VOICE_PATH" ]; then
        echo "ERROR: Voice file not found: $VOICE_PATH"
        exit 1
    fi
    if [ ! -f "$IMAGE_COVER_FILE_PATH" ]; then
        echo "ERROR: Cover image file not found: $IMAGE_COVER_FILE_PATH"
        exit 1
    fi

    COVER_EXTENSION="${IMAGE_COVER_FILE_PATH##*.}"
    COVER_DEST="$STORY_DIR/cover.$COVER_EXTENSION"
    NEED_COPY_VOICE=true
    NEED_MOVE_COVER=true
fi

ADD_EPISODE_LABEL=false
if [ "$GENERATE_VIDEO" = true ]; then
    DEFAULT_ADD_EPISODE_LABEL=true
    if [ -f "$CONFIG_FILE" ]; then
        DEFAULT_ADD_EPISODE_LABEL=$(load_config_value "$CONFIG_FILE" add_episode_label true)
    fi
    ADD_EPISODE_LABEL=$(read_boolean "Add episode_label?" "$DEFAULT_ADD_EPISODE_LABEL")
elif [ -f "$CONFIG_FILE" ]; then
    ADD_EPISODE_LABEL=$(load_config_value "$CONFIG_FILE" add_episode_label false)
fi

mkdir -p "$AUDIO_DIR" "$SCRIPT_DIR" "$VOICE_DIR"

# Setup voice / cover only when needed (first run or missing files).
if [ "${NEED_COPY_VOICE:-false}" = true ]; then
    if [ -e "$VOICE_DEST" ]; then
        echo "WARNING: Voice destination already exists: $VOICE_DEST"
        echo "Refusing to overwrite the existing file."
    else
        cp "$VOICE_PATH" "$VOICE_DEST"
    fi
fi

if [ "${NEED_MOVE_COVER:-false}" = true ]; then
    if [ -e "$COVER_DEST" ]; then
        echo "WARNING: Cover destination already exists: $COVER_DEST"
        echo "Refusing to overwrite the existing file."
    else
        mv "$IMAGE_COVER_FILE_PATH" "$COVER_DEST"
    fi
fi

# Persist config for next short-mode runs.
save_config "$CONFIG_FILE"

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
echo "Voice                : $VOICE_DEST"
echo "Cover Image          : $COVER_DEST"
echo "Config               : $CONFIG_FILE"
echo "------------------------------------------------------------"
echo "Crawl & Clean        : $CRAWL_AND_CLEAN"
echo "Generate Audio       : $GENERATE_AUDIO"
echo "Crawling Title       : $CRAWLING_TITLE"
echo "Generate Video       : $GENERATE_VIDEO"
echo "Add episode_label    : $ADD_EPISODE_LABEL"
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
    caffeinate -i uv run python tts/make_video_ver4.py "$STORY" "$START" "$END" "$ADD_EPISODE_LABEL"
else
    echo ""
    echo "=== 5. Making Video SKIPPED ==="
fi

echo ""
echo "=== DONE! ==="
