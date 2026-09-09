#!/bin/bash
set -e # Dừng ngay nếu có bất kỳ lệnh nào bị lỗi

STORY=${1:-"truyen-001"}
START=${2:-"102"}
END=${3:-"102"}
URL=${4:-"https://truyenfull.live/thieu-gia-bi-bo-roi"}

echo "=== 1. Crawling $STORY ($START -> $END) ==="
node craw/crawl.js --story "$STORY" --start "$START" --end "$END" --url "$URL"

echo "=== 1. clean $STORY ($START -> $END) ==="
node craw/clean1.js

echo "=== 2. Generating TTS Audio ==="
uv run python tts/generate-mac-m2-v2.py stories/"$STORY" --mode v3turbo --max-chars 512 --batch-size 16 --steps 8

# echo "=== 3. Combining Audio Files ==="
# uv run python combine.py stories/"$STORY"

echo "=== DONE! ==="

# ./run.sh truyen-001 102 102 "https://truyenfull.live/thieu-gia-bi-bo-roi"