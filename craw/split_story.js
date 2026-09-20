const fs = require('fs-extra');
const path = require('path');

/**
 * VieNeu-TTS — chia file truyện TXT thành script/N.txt và titles.txt
 *
 * Ví dụ:
 *
 * node craw/split_story.js --story truyen-001
 *
 * node craw/split_story.js \
 *   --story truyen-001 \
 *   --source /path/to/story.txt
 */

const HEADING_RE = /^\s*chương\s+0*(\d+)\s*:\s*(.*)$/iu;
const INTRO_TITLE_LINE = 'Giới Thiệu Truyện ';

// ==========================================
// PARSE COMMAND LINE ARGUMENTS
// ==========================================

function parseArgs() {
    const args = process.argv.slice(2);

    const config = {
        story: null,
        source: null,
    };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];

        switch (arg) {
            case '--story':
                config.story = args[++i];
                break;

            case '--source':
                config.source = args[++i];
                break;

            case '--help':
            case '-h':
                printHelp();
                process.exit(0);

            default:
                console.error(`[X] Tham số không hợp lệ: ${arg}`);
                printHelp();
                process.exit(1);
        }
    }

    validateConfig(config);

    return config;
}

// ==========================================
// VALIDATE CONFIG
// ==========================================

function validateConfig(config) {
    if (!config.story) {
        console.error('[X] Thiếu tham số: --story');
        printHelp();
        process.exit(1);
    }
}

// ==========================================
// HELP
// ==========================================

function printHelp() {
    console.log(`
==========================================
        VIE NEU STORY SPLITTER
==========================================

Chia file truyện TXT (nhiều chương) thành
stories/<story>/script/N.txt và titles.txt.

Cú pháp:

  node craw/split_story.js [options]


Bắt buộc:

  --story <name>
      Tên thư mục truyện


Tùy chọn:

  --source <path>
      File truyện gốc

      Mặc định:
      stories/<story>/source.txt

  --help
      Hiển thị hướng dẫn


Heading chương (một dòng riêng, bắt buộc có dấu :):

  Chương 1: tiêu đề
  CHƯƠNG  01 : tiêu đề

Số chương phải bắt đầu từ 1 và liền mạch.
File N.txt / titles.txt đã có sẽ bị bỏ qua (không ghi đè).


==========================================
VÍ DỤ
==========================================

  node craw/split_story.js --story truyen-001

  node craw/split_story.js \\
    --story truyen-001 \\
    --source /path/to/story.txt
`);
}

// ==========================================
// PARSE CHAPTERS
// ==========================================

function parseChapters(content) {
    const text = content
        .replace(/^\uFEFF/, '')
        .replace(/\r\n/g, '\n')
        .replace(/\r/g, '\n');

    const lines = text.split('\n');
    const chapters = [];
    let current = null;

    for (const line of lines) {
        const match = line.match(HEADING_RE);
        if (match) {
            const n = Number(match[1]);
            if (current) {
                chapters.push(current);
            }
            current = {
                n,
                headingLine: line,
                bodyLines: [],
            };
            continue;
        }

        if (current) {
            current.bodyLines.push(line);
        }
    }

    if (current) {
        chapters.push(current);
    }

    return chapters;
}

function validateChapters(chapters) {
    if (chapters.length === 0) {
        throw new Error(
            'Không tìm thấy chương nào. Heading phải dạng «Chương N: tiêu đề» trên một dòng riêng.'
        );
    }

    for (let i = 0; i < chapters.length; i++) {
        const expected = i + 1;
        const actual = chapters[i].n;
        if (actual !== expected) {
            throw new Error(
                `Số chương không liền mạch tại vị trí ${i + 1}: ` +
                `kỳ vọng Chương ${expected}, gặp Chương ${actual}.`
            );
        }
    }
}

function buildChapterContent(chapter) {
    const body = chapter.bodyLines.join('\n').replace(/\s+$/, '');
    if (!body) {
        return `${chapter.headingLine}\n`;
    }
    return `${chapter.headingLine}\n${body}\n`;
}

// ==========================================
// SPLIT PROCESS
// ==========================================

async function splitStory(config) {
    const storyDir = path.join(process.cwd(), 'stories', config.story);
    const sourcePath = config.source
        ? path.resolve(config.source)
        : path.join(storyDir, 'source.txt');
    const scriptDir = path.join(storyDir, 'script');
    const titlesPath = path.join(storyDir, 'titles.txt');

    if (!await fs.pathExists(sourcePath)) {
        console.error(`[X] Không tìm thấy file nguồn: ${sourcePath}`);
        process.exit(1);
    }

    const content = await fs.readFile(sourcePath, 'utf8');
    const chapters = parseChapters(content);
    validateChapters(chapters);

    await fs.ensureDir(scriptDir);

    console.log('');
    console.log('==========================================');
    console.log('        VIE NEU STORY SPLITTER');
    console.log('==========================================');
    console.log(`Story       : ${config.story}`);
    console.log(`Source      : ${sourcePath}`);
    console.log(`Chapters    : ${chapters.length} (1 -> ${chapters.length})`);
    console.log(`Script dir  : ${scriptDir}`);
    console.log('==========================================');
    console.log('');

    let written = 0;
    let skipped = 0;

    for (const chapter of chapters) {
        const fileName = `${chapter.n}.txt`;
        const filePath = path.join(scriptDir, fileName);

        if (await fs.pathExists(filePath)) {
            skipped++;
            console.log(`[i] Bỏ qua (đã có): script/${fileName}`);
            continue;
        }

        await fs.writeFile(filePath, buildChapterContent(chapter), 'utf8');
        written++;
        console.log(`[✓] Đã tạo script/${fileName}`);
    }

    if (await fs.pathExists(titlesPath)) {
        console.log('[i] Bỏ qua (đã có): titles.txt');
    } else {
        const titlesBody =
            [INTRO_TITLE_LINE, ...chapters.map((ch) => ch.headingLine)].join('\n') +
            '\n';
        await fs.writeFile(titlesPath, titlesBody, 'utf8');
        console.log(
            `[✓] Đã tạo titles.txt (${chapters.length} chương + 1 dòng giới thiệu)`
        );
    }

    console.log('');
    console.log('==========================================');
    console.log('                 HOÀN TẤT');
    console.log('==========================================');
    console.log(`Tổng số chương : ${chapters.length}`);
    console.log(`Đã tạo         : ${written}`);
    console.log(`Bỏ qua         : ${skipped}`);
    console.log(`titles.txt     : ${titlesPath}`);
    console.log('==========================================');
    console.log('');
}

// ==========================================
// MAIN
// ==========================================

async function main() {
    try {
        const config = parseArgs();
        await splitStory(config);
    } catch (error) {
        console.error(`\n[X] ${error.message}`);
        process.exit(1);
    }
}

main();
