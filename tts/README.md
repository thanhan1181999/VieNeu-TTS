node craw/crawl.js --story truyen-001 --start 102 --end 102 --url "https://truyenfull.live/thieu-gia-bi-bo-roi"

uv run python tts/generate.py stories/truyen-001
uv run python tts/combine.py stories/truyen-001
uv run python tts/subtitles.py stories/truyen-001

uv run python tts/generate.py stories/truyen-001 --batch-size 8

uv run vieneu-web

uv run python tts/generate.py stories/truyen-001                                                                                                                                                                                    ok  at 23:07:13 

============================================================
Story: stories/truyen-001
============================================================
Voice : stories/truyen-001/voice/reference.wav
Style : doc_truyen
Batch : 8
Texts : 100

Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Reference cache: HIT
    speaker_emb: (192,) float32
    ref_codes: (101, 16) int64

Generating 100 segment(s)...

[BATCH] 1-8 / 100
  Sentences: 517 across 8 segment(s)
  OK: 8 segment(s) in 2077.68s

[BATCH] 9-16 / 100
  Sentences: 546 across 8 segment(s)
  OK: 8 segment(s) in 1971.05s

[BATCH] 17-24 / 100
  Sentences: 658 across 8 segment(s)
  OK: 8 segment(s) in 1815.65s

[BATCH] 25-32 / 100
  Sentences: 692 across 8 segment(s)
  OK: 8 segment(s) in 1906.43s

[BATCH] 33-40 / 100
  Sentences: 595 across 8 segment(s)
  OK: 8 segment(s) in 1970.40s

[BATCH] 41-48 / 100
  Sentences: 617 across 8 segment(s)
  OK: 8 segment(s) in 1937.39s

[BATCH] 49-56 / 100
  Sentences: 535 across 8 segment(s)
  OK: 8 segment(s) in 1837.06s

[BATCH] 57-64 / 100
  Sentences: 562 across 8 segment(s)
  OK: 8 segment(s) in 1837.47s

[BATCH] 65-72 / 100
  Sentences: 695 across 8 segment(s)
  OK: 8 segment(s) in 1806.21s

[BATCH] 73-80 / 100
  Sentences: 677 across 8 segment(s)
  OK: 8 segment(s) in 1722.57s

[BATCH] 81-88 / 100
  Sentences: 765 across 8 segment(s)
  OK: 8 segment(s) in 1915.25s

[BATCH] 89-96 / 100
  Sentences: 511 across 8 segment(s)
  OK: 8 segment(s) in 1994.53s

[BATCH] 97-100 / 100
  Sentences: 344 across 4 segment(s)
  OK: 4 segment(s) in 1324.54s

============================================================
Generated : 100
Failed    : 0
Skipped   : 0
Timings   : stories/truyen-001/output/timings.json
Time      : 24123.66s
============================================================

phân tích thời gian chạy
[BATCH] 1-16 / 59
  Sentences: 1598 across 16 segment(s)
  OK: 16 segment(s) in 11214.15s

[BATCH] 17-32 / 59
  Sentences: 1591 across 16 segment(s)
  OK: 16 segment(s) in 7725.74s

[BATCH] 33-48 / 59
  Sentences: 1675 across 16 segment(s)
  OK: 16 segment(s) in 7614.92s

[BATCH] 49-59 / 59
  Sentences: 1047 across 11 segment(s)
  OK: 11 segment(s) in 5339.17s

============================================================
Generated : 59
Failed    : 0
Skipped   : 144
Timings   : stories/truyen-001/output/timings.json
Time      : 31902.52s
============================================================
