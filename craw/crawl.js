const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs-extra');
const path = require('path');

/**
 * VieNeu-TTS Novel Crawler
 *
 * Ví dụ:
 *
 * node craw/crawl.js \
 *   --story truyen-001 \
 *   --start 101 \
 *   --end 200 \
 *   --url "https://truyenfull.live/thieu-gia-bi-boi"
 *
 * Test 1 chương:
 *
 * node craw/crawl.js \
 *   --story truyen-001 \
 *   --start 101 \
 *   --end 101 \
 *   --url "https://truyenfull.live/thieu-gia-bi-boi"
 */

const DEFAULT_SELECTOR = '#chapter-c';
const DEFAULT_DELAY = 1000;
const DEFAULT_TIMEOUT = 15000;
const DEFAULT_RETRIES = 3;


// ==========================================
// PARSE COMMAND LINE ARGUMENTS
// ==========================================

function parseArgs() {
    const args = process.argv.slice(2);

    const config = {
        story: null,
        start: null,
        end: null,
        url: null,
        selector: DEFAULT_SELECTOR,
        delay: DEFAULT_DELAY,
        timeout: DEFAULT_TIMEOUT,
        retries: DEFAULT_RETRIES,
        force: false,
    };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];

        switch (arg) {
            case '--story':
                config.story = args[++i];
                break;

            case '--start':
                config.start = Number(args[++i]);
                break;

            case '--end':
                config.end = Number(args[++i]);
                break;

            case '--url':
                config.url = args[++i];
                break;

            case '--selector':
                config.selector = args[++i];
                break;

            case '--delay':
                config.delay = Number(args[++i]);
                break;

            case '--timeout':
                config.timeout = Number(args[++i]);
                break;

            case '--retries':
                config.retries = Number(args[++i]);
                break;

            case '--force':
                config.force = true;
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
    const missing = [];

    if (!config.story) {
        missing.push('--story');
    }

    if (config.start === null) {
        missing.push('--start');
    }

    if (config.end === null) {
        missing.push('--end');
    }

    if (!config.url) {
        missing.push('--url');
    }

    if (missing.length > 0) {
        console.error(
            `[X] Thiếu tham số: ${missing.join(', ')}`
        );

        printHelp();
        process.exit(1);
    }

    if (!Number.isInteger(config.start) || config.start < 1) {
        console.error(
            '[X] --start phải là số nguyên >= 1'
        );

        process.exit(1);
    }

    if (!Number.isInteger(config.end) ||
        config.end < config.start) {

        console.error(
            '[X] --end phải >= --start'
        );

        process.exit(1);
    }

    if (config.delay < 0) {
        console.error(
            '[X] --delay không được âm'
        );

        process.exit(1);
    }

    if (config.timeout <= 0) {
        console.error(
            '[X] --timeout phải > 0'
        );

        process.exit(1);
    }

    if (config.retries < 1) {
        console.error(
            '[X] --retries phải >= 1'
        );

        process.exit(1);
    }
}


// ==========================================
// HELP
// ==========================================

function printHelp() {
    console.log(`
==========================================
        VIE NEU NOVEL CRAWLER
==========================================

Cú pháp:

  node craw/crawl.js [options]


Bắt buộc:

  --story <name>
      Tên thư mục truyện

  --start <number>
      Chương bắt đầu

  --end <number>
      Chương kết thúc

  --url <url>
      URL truyện gốc


Tùy chọn:

  --selector <css>
      CSS selector của nội dung chương

      Mặc định:
      #chapter-c

  --delay <ms>
      Thời gian nghỉ giữa các request

      Mặc định:
      1000

  --timeout <ms>
      Timeout HTTP request

      Mặc định:
      15000

  --retries <number>
      Số lần thử lại khi request lỗi

      Mặc định:
      3

  --force
      Crawl lại và ghi đè file đã tồn tại

  --help
      Hiển thị hướng dẫn


==========================================
VÍ DỤ
==========================================

Test 1 chương:

  node craw/crawl.js \\
    --story truyen-001 \\
    --start 101 \\
    --end 101 \\
    --url "https://truyenfull.live/thieu-gia-bi-boi"


Crawl chương 101 -> 200:

  node craw/crawl.js \\
    --story truyen-001 \\
    --start 101 \\
    --end 200 \\
    --url "https://truyenfull.live/thieu-gia-bi-boi"


Crawl lại và ghi đè:

  node craw/crawl.js \\
    --story truyen-001 \\
    --start 101 \\
    --end 200 \\
    --url "https://truyenfull.live/thieu-gia-bi-boi" \\
    --force

`);
}


// ==========================================
// SLEEP
// ==========================================

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


// ==========================================
// BUILD CHAPTER URL
// ==========================================

function buildChapterUrl(baseUrl, chapter) {
    const cleanBaseUrl = baseUrl.endsWith('/')
        ? baseUrl.slice(0, -1)
        : baseUrl;

    return `${cleanBaseUrl}/chuong-${chapter}/`;
}


// ==========================================
// HTTP REQUEST
// ==========================================

async function fetchChapter(url, timeout, retries) {
    let lastError = null;

    for (let attempt = 1; attempt <= retries; attempt++) {

        try {

            const response = await axios.get(url, {

                headers: {
                    'User-Agent':
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
                        'AppleWebKit/537.36 (KHTML, like Gecko) ' +
                        'Chrome/120.0.0.0 Safari/537.36',

                    'Accept':
                        'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',

                    'Accept-Language':
                        'vi,en-US;q=0.9,en;q=0.8',
                },

                timeout,

                responseType: 'text',

                validateStatus: status =>
                    status >= 200 && status < 400,
            });

            return response.data;

        } catch (error) {

            lastError = error;

            console.warn(
                `[!] Request thất bại ` +
                `(attempt ${attempt}/${retries}): ` +
                `${error.message}`
            );

            if (attempt < retries) {

                const retryDelay = attempt * 2000;

                console.log(
                    `    → Thử lại sau ` +
                    `${retryDelay / 1000}s...`
                );

                await sleep(retryDelay);
            }
        }
    }

    throw lastError;
}


// ==========================================
// EXTRACT CHAPTER CONTENT
// ==========================================

function extractChapterContent(html, selector) {

    const $ = cheerio.load(html);

    const contentElement = $(selector);

    if (!contentElement.length) {
        return null;
    }

    // <br> → newline
    contentElement
        .find('br')
        .replaceWith('\n');

    // Xóa các tag không cần thiết
    contentElement
        .find('script, style, noscript')
        .remove();

    let content = contentElement.text();

    // Chuẩn hóa newline
    content = content
        .replace(/\r\n/g, '\n')
        .replace(/\r/g, '\n');

    // Xóa whitespace cuối dòng
    content = content
        .split('\n')
        .map(line => line.trim())
        .join('\n');

    // Giảm nhiều dòng trống liên tiếp
    content = content.replace(
        /\n{3,}/g,
        '\n\n'
    );

    return content.trim();
}


// ==========================================
// CRAWL
// ==========================================

async function crawlNovels(config) {

    const outputFolder = path.join(
        process.cwd(),
        'stories',
        config.story,
        'script'
    );

    await fs.ensureDir(outputFolder);

    console.log('');
    console.log('==========================================');
    console.log('         VIE NEU NOVEL CRAWLER');
    console.log('==========================================');

    console.log(`Story       : ${config.story}`);
    console.log(`Start       : ${config.start}`);
    console.log(`End         : ${config.end}`);
    console.log(`URL         : ${config.url}`);
    console.log(`Selector    : ${config.selector}`);
    console.log(`Output      : ${outputFolder}`);
    console.log(`Delay       : ${config.delay} ms`);
    console.log(`Timeout     : ${config.timeout} ms`);
    console.log(`Retries     : ${config.retries}`);
    console.log(
        `Force       : ${config.force ? 'YES' : 'NO'}`
    );

    console.log('==========================================');
    console.log('');

    let success = 0;
    let skipped = 0;
    let failed = 0;

    for (
        let chapter = config.start;
        chapter <= config.end;
        chapter++
    ) {

        const fileName = `${chapter}.txt`;

        const filePath = path.join(
            outputFolder,
            fileName
        );

        const chapterUrl = buildChapterUrl(
            config.url,
            chapter
        );

        console.log(`[*] Chương ${chapter}`);
        console.log(`    URL: ${chapterUrl}`);

        // --------------------------------------
        // SKIP EXISTING FILE
        // --------------------------------------

        if (
            !config.force &&
            await fs.pathExists(filePath)
        ) {

            console.log(
                `    [-] Đã tồn tại → bỏ qua`
            );

            skipped++;

            console.log('');

            continue;
        }

        // --------------------------------------
        // DOWNLOAD
        // --------------------------------------

        try {

            const html = await fetchChapter(
                chapterUrl,
                config.timeout,
                config.retries
            );

            // ----------------------------------
            // EXTRACT
            // ----------------------------------

            const content = extractChapterContent(
                html,
                config.selector
            );

            if (content === null) {

                console.warn(
                    `    [!] Không tìm thấy selector: ` +
                    `${config.selector}`
                );

                failed++;

            } else if (!content.trim()) {

                console.warn(
                    `    [!] Nội dung chương ${chapter} rỗng`
                );

                failed++;

            } else {

                // --------------------------------
                // SAVE
                // --------------------------------

                await fs.writeFile(
                    filePath,
                    content + '\n',
                    'utf8'
                );

                console.log(
                    `    [✓] Đã lưu: ${filePath}`
                );

                console.log(
                    `    [i] ` +
                    `${content.length.toLocaleString()} ký tự`
                );

                success++;
            }

        } catch (error) {

            console.error(
                `    [X] Lỗi chương ${chapter}: ` +
                `${error.message}`
            );

            failed++;
        }

        // --------------------------------------
        // DELAY
        // --------------------------------------

        if (chapter < config.end) {
            await sleep(config.delay);
        }

        console.log('');
    }

    // ==========================================
    // SUMMARY
    // ==========================================

    console.log('==========================================');
    console.log('                 HOÀN TẤT');
    console.log('==========================================');

    console.log(
        `✓ Thành công : ${success}`
    );

    console.log(
        `- Bỏ qua     : ${skipped}`
    );

    console.log(
        `X Lỗi        : ${failed}`
    );

    console.log(
        `Output       : ${outputFolder}`
    );

    console.log('==========================================');
}


// ==========================================
// MAIN
// ==========================================

async function main() {

    try {

        const config = parseArgs();

        await crawlNovels(config);

    } catch (error) {

        console.error('');
        console.error(
            `[X] Fatal error: ${error.message}`
        );

        process.exit(1);
    }
}

main();