const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs-extra');
const path = require('path');

const DEFAULT_SELECTOR = '#list-chapter ul.list-chapter';
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

    if (!config.story) missing.push('--story');
    if (!config.url) missing.push('--url');

    if (missing.length > 0) {
        console.error(`[X] Thiếu tham số: ${missing.join(', ')}`);
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
     VIE NEU CHAPTER TITLE CRAWLER
==========================================

Cú pháp:
  node crawl_title.js [options]

Bắt buộc:
  --story <name>        Tên thư mục truyện
  --url <url>          Link truyện gốc

Tùy chọn:
  --force              Ghi đè file nếu đã tồn tại
  --delay <ms>         Thời gian nghỉ giữa các request (Mặc định: 1000ms)

Ví dụ:
  node crawl_title.js \\
    --story thieu-gia-bi-bo-roi \\
    --url "https://truyenfull.live/thieu-gia-bi-bo-roi/"
`);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ==========================================
// BUILD PAGE URL
// ==========================================

function buildPageUrl(baseUrl, page) {
    const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    if (page === 1) {
        return `${cleanBaseUrl}/`;
    }
    return `${cleanBaseUrl}/trang-${page}/`;
}

// ==========================================
// HTTP REQUEST
// ==========================================

async function fetchPage(url, timeout, retries) {
    let lastError = null;

    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const response = await axios.get(url, {
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                },
                timeout,
                responseType: 'text',
                validateStatus: status => status >= 200 && status < 400,
            });
            return response.data;
        } catch (error) {
            lastError = error;
            console.warn(`[!] Request thất bại (lần ${attempt}/${retries}): ${error.message}`);
            if (attempt < retries) {
                await sleep(attempt * 2000);
            }
        }
    }
    throw lastError;
}

// ==========================================
// EXTRACT TITLES
// ==========================================

function extractTitles(html, selector) {
    const $ = cheerio.load(html);
    const titles = [];

    $(`${selector}`).each((_, element) => {
        const titleText = $(element).text().trim();
        if (titleText) {
            titles.push(titleText);
        }
    });

    return titles;
}

// ==========================================
// CRAWL TITLES PROCESS
// ==========================================

async function crawlTitles(config) {
    const outputPath = path.join(
        process.cwd(),
        'stories',
        config.story,
        'titles.txt'
    );

    await fs.ensureDir(path.dirname(outputPath));

    if (await fs.pathExists(outputPath) && !config.force) {
        console.log(`[✓] File đầu ra đã tồn tại: ${outputPath}`);
        console.log(`    Đã hoàn thành thành công. Dùng tham số --force nếu bạn muốn ghi đè.\n`);
        process.exit(0);
    }

    await fs.writeFile(outputPath, 'Giới Thiệu Truyện \n', 'utf8');

    console.log('');
    console.log('==========================================');
    console.log('     VIE NEU CHAPTER TITLE CRAWLER');
    console.log('==========================================');
    console.log(`Story       : ${config.story}`);
    console.log(`URL         : ${config.url}`);
    console.log(`Selector   : ${config.selector}`);
    console.log(`Output File : ${outputPath}`);
    console.log('==========================================\n');

    let totalTitles = 0;
    let page = 1;
    let previousTitlesString = ""; // Chuỗi dùng để so sánh trùng lặp với trang trước

    while (true) {
        const pageUrl = buildPageUrl(config.url, page);
        console.log(`[*] Đang cào Trang ${page}...`);
        console.log(`    URL: ${pageUrl}`);

        try {
            const html = await fetchPage(pageUrl, config.timeout, config.retries);
            const titles = extractTitles(html, config.selector);

            // 1. Kiểm tra nếu không tìm thấy title nào
            if (titles.length === 0) {
                console.log(`\n[i] Không tìm thấy tên chương nào ở Trang ${page}. Dừng quá trình crawl.`);
                break;
            }

            const currentTitlesString = titles.join('\n');

            // 2. Kiểm tra nếu nội dung trang hiện tại trùng hệt 100% với trang trước (Server bị fallback)
            if (currentTitlesString === previousTitlesString) {
                console.log(`\n[!] Phát hiện Trang ${page} bị lặp lại nội dung của Trang ${page - 1} (Đã hết trang thực tế). Dừng quá trình crawl.`);
                break;
            }

            // Ghi nhận dữ liệu trang hợp lệ
            previousTitlesString = currentTitlesString;

            const contentToWrite = currentTitlesString + '\n';
            await fs.appendFile(outputPath, contentToWrite, 'utf8');

            totalTitles += titles.length;
            console.log(`    [✓] Đã lấy ${titles.length} tên chương.`);

        } catch (error) {
            console.error(`    [X] Lỗi tại trang ${page}: ${error.message}`);
            console.log(`    [i] Dừng quá trình cào do phát sinh lỗi kết nối.`);
            break;
        }

        page++;
        await sleep(config.delay);
        console.log('');
    }

    console.log('\n==========================================');
    console.log('                 HOÀN TẤT');
    console.log('==========================================');
    console.log(`Tổng số trang thực tế : ${page - 1}`);
    console.log(`Tổng số chương lấy được: ${totalTitles}`);
    console.log(`File đầu ra            : ${outputPath}`);
    console.log('==========================================\n');
}

// ==========================================
// MAIN
// ==========================================

async function main() {
    try {
        const config = parseArgs();
        await crawlTitles(config);
    } catch (error) {
        console.error(`\n[X] Fatal error: ${error.message}`);
        process.exit(1);
    }
}

main();