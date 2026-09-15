#!/bin/bash

set -e # Dừng ngay nếu có bất kỳ lệnh nào bị lỗi

# ============================================================
# Default arguments
# ============================================================

STORY="${1:-truyen-001}"
START="${2:-102}"
END="${3:-102}"
URL="${4:-https://truyenfull.live/thieu-gia-bi-boi}"

# ============================================================
# Default options
# ============================================================

CRAWL_AND_CLEAN=true
GENERATE_AUDIO=true
CRAWLING_TITLE=true
GENERATE_VIDEO=true

# ============================================================
# Parse options
# ============================================================

for arg in "$@"; do
    case "$arg" in
        --crawl-and-clean=true)
            CRAWL_AND_CLEAN=true
            ;;
        --crawl-and-clean=false)
            CRAWL_AND_CLEAN=false
            ;;
        --generate-audio=true)
            GENERATE_AUDIO=true
            ;;
        --generate-audio=false)
            GENERATE_AUDIO=false
            ;;
        --crawling-title=true)
            CRAWLING_TITLE=true
            ;;
        --crawling-title=false)
            CRAWLING_TITLE=false
            ;;
        --generate-video=true)
            GENERATE_VIDEO=true
            ;;
        --generate-video=false)
            GENERATE_VIDEO=false
            ;;
    esac
done

# ============================================================
# Show configuration
# ============================================================

echo "============================================================"
echo "Story           : $STORY"
echo "Chapters        : $START -> $END"
echo "URL             : $URL"
echo "------------------------------------------------------------"
echo "Crawl & Clean   : $CRAWL_AND_CLEAN"
echo "Generate Audio  : $GENERATE_AUDIO"
echo "Crawling Title  : $CRAWLING_TITLE"
echo "Generate Video  : $GENERATE_VIDEO"
echo "============================================================"

# ============================================================
# 1. Crawling + Cleaning
# ============================================================

if [ "$CRAWL_AND_CLEAN" = true ]; then

    echo ""
    echo "=== 1. Crawling Content $STORY ($START -> $END) ==="

    node craw/crawl.js \
        --story "$STORY" \
        --start "$START" \
        --end "$END" \
        --url "$URL"

    echo ""
    echo "=== 2. Cleaning Content $STORY ($START -> $END) ==="

    node craw/clean1.js

else

    echo ""
    echo "=== 1-2. Crawling & Cleaning SKIPPED ==="

fi

# ============================================================
# 3. Generating TTS Audio
# ============================================================

if [ "$GENERATE_AUDIO" = true ]; then

    echo ""
    echo "=== 3. Generating TTS Audio ==="

    caffeinate -i uv run python \
        tts/generate-mac-m2-v2.py \
        stories/"$STORY" \
        --mode v3turbo \
        --max-chars 512 \
        --batch-size 16 \
        --start "$START" \
        --end "$END" \
        --steps 8

else

    echo ""
    echo "=== 3. Generating TTS Audio SKIPPED ==="

fi

# ============================================================
# 4. Crawling Titles
# ============================================================

if [ "$CRAWLING_TITLE" = true ]; then

    echo ""
    echo "=== 4. Crawling Titles ==="

    node craw/crawl_title.js \
        --url "$URL" \
        --story "$STORY"

else

    echo ""
    echo "=== 4. Crawling Titles SKIPPED ==="

fi

# ============================================================
# 5. Making Video
# ============================================================

if [ "$GENERATE_VIDEO" = true ]; then

    echo ""
    echo "=== 5. Making Video ==="

    uv run python \
        tts/make_video_ver2.py \
        "$STORY" \
        "$START" \
        "$END"

else

    echo ""
    echo "=== 5. Making Video SKIPPED ==="

fi

echo ""
echo "=== DONE! ==="

# ./run.sh truyen-001 102 102 "https://truyenfull.live/thieu-gia-bi-bo-roi" --crawl-and-clean=true --generate-audio=false --crawling-title=false --generate-video=false