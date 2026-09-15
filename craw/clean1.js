const fs = require('fs-extra');
const path = require('path');

// 1. Nhận story ID từ dòng lệnh (ví dụ: node clean1.js truyen-002), mặc định là 'truyen-001'
const storyId = process.argv[2] || 'truyen-001';
const STORIES_DIR = path.join(__dirname, `../stories/${storyId}/script`);

// Sắp xếp từ dài đến ngắn để Regex ưu tiên match chuỗi dài trước
const JUNK_TEXTS = [
    // 1. Cụm câu dài
    'Bạn đang đọc chuyện tại Truyện FULL',
    'Bạn đang đọc truyện tại Truyện FULL',

    // 2. Từ ghép từ dài đến ngắn
    'truyenfulllivetruyenfull',
    'nguồn TruyenFull.vn',
    'truyenfull vn',
    'truyenfullvn',
    'truyen full',
    'truyenfull'
];

// Từ viết tắt thường gặp (không tính dấu chấm cuối là ngắt câu)
const ABBREVIATIONS = [
    'tp', 'ths', 'ts', 'gs', 'pgs', 'tt', 'q', 'p', 'h', 'x',
    'ubnd', 'hđnd', 'nxb', 'cty', 'tnhh', 'cp', 'cn', 'btc', 'bch',
    'tr', 'trang', 'đc', 'sl', 'stt', 'sđt', 'mst',
    'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr',
    'vs', 'etc', 'approx', 'dept', 'vol', 'pp', 'ed', 'no', 'nos',
    'kg', 'km', 'cm', 'mm', 'mg', 'ml', 'ltd', 'inc', 'corp'
].sort((a, b) => b.length - a.length);

const ABBREV_REGEX = new RegExp(
    `(?<![\\p{L}\\p{N}])(?:${ABBREVIATIONS.map(escapeRegex).join('|')})\\.`,
    'giu'
);

// TLD thường gặp khi nhận diện domain không có scheme
const DOMAIN_TLD = 'com|net|org|vn|io|edu|gov|info|biz|co|me|tv|xyz|live|app|dev|ai|uk|us|jp|kr';

function escapeRegex(text) {
    return text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&');
}

/**
 * Bảo vệ các chuỗi chứa dấu chấm không phải điểm ngắt câu bằng placeholder.
 */
function protectNonSentenceDots(text) {
    const placeholders = [];

    const protect = (match) => {
        const token = `\uE000${placeholders.length}\uE001`;
        placeholders.push(match);
        return token;
    };

    // Ellipsis dạng ... → … để tách câu ổn định (không tách từng dấu chấm)
    let protectedText = text.replace(/\.{3,}/g, '…');

    // URL có scheme
    protectedText = protectedText.replace(/https?:\/\/[^\s<>"']+/gi, protect);

    // www....
    protectedText = protectedText.replace(/\bwww\.[^\s<>"']+/gi, protect);

    // Email
    protectedText = protectedText.replace(
        /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g,
        protect
    );

    // Domain dạng example.com / sub.example.vn
    protectedText = protectedText.replace(
        new RegExp(
            `\\b[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*\\.(?:${DOMAIN_TLD})\\b`,
            'gi'
        ),
        protect
    );

    // Số thập phân: 3.14 hoặc 3,14
    protectedText = protectedText.replace(/\b\d+[.,]\d+\b/g, protect);

    // v.v. / v.v
    protectedText = protectedText.replace(/\bv\s*\.\s*v\s*\.?/gi, protect);

    // Từ viết tắt trong danh sách (TP. ThS. tr. ...)
    protectedText = protectedText.replace(ABBREV_REGEX, protect);

    // Chữ cái viết tắt 1 ký tự kiểu A. / Đ. đứng trước tên riêng hoặc số
    protectedText = protectedText.replace(
        /(?:^|[^\p{L}\p{N}])(\p{L})\.(?=\s*(?:\p{L}[\p{L}\p{M}'’-]*|\d))/gu,
        (full, letter) => full.slice(0, full.length - letter.length - 1) + protect(`${letter}.`)
    );

    return { text: protectedText, placeholders };
}

function restorePlaceholders(text, placeholders) {
    return text.replace(/\uE000(\d+)\uE001/g, (_, index) => placeholders[Number(index)] ?? '');
}

/**
 * Tách đoạn văn thành các câu dựa trên . ? !
 */
function splitIntoSentences(paragraph) {
    const { text: protectedText, placeholders } = protectNonSentenceDots(paragraph);

    // Tách sau dấu kết thúc câu (. ? ! …), giữ dấu kèm câu; bỏ qua ; và :
    const rawParts = protectedText.split(/(?<=[.?!…])(?=\s+|$)/);

    const sentences = [];
    for (const part of rawParts) {
        const restored = restorePlaceholders(part, placeholders)
            .replace(/\s+/g, ' ')
            .trim();
        if (restored) {
            sentences.push(restored);
        }
    }

    return sentences;
}

/**
 * Chuẩn hoá 1 câu: trim, gộp khoảng trắng, viết hoa đầu câu, thêm '.' nếu thiếu.
 */
function normalizeSentence(sentence) {
    let s = sentence.replace(/\s+/g, ' ').trim();
    if (!s) return '';

    // Viết hoa ký tự chữ cái đầu tiên (bỏ qua dấu mở ngoặc/ngoặc kép đứng trước)
    s = s.replace(
        /^([^\p{L}]*)(\p{L})/u,
        (_, prefix, letter) => prefix + letter.toLocaleUpperCase('vi-VN')
    );

    // Đã có dấu kết thúc câu (có thể kèm dấu đóng ngoặc/ngoặc kép) thì giữ nguyên
    if (/[.?!…]["'»”’)\]\}]*$/u.test(s)) {
        return s;
    }

    return `${s}.`;
}

/**
 * Pipeline chuẩn hoá toàn bộ nội dung file → mỗi câu 1 dòng, cách nhau 1 dòng trống.
 */
function normalizeContent(content, junkRegex) {
    let cleaned = content.replace(junkRegex, ' ');
    cleaned = cleaned.replace(/\r\n/g, '\n');

    // Gộp các dòng lẻ trong cùng đoạn; giữ đoạn như ranh giới mềm
    const paragraphs = cleaned
        .split(/\n\s*\n+/)
        .map((p) =>
            p
                .split('\n')
                .map((line) => line.trim())
                .filter((line) => line.length > 0)
                .join(' ')
                .replace(/[ \t]+/g, ' ')
                .trim()
        )
        .filter((p) => p.length > 0);

    const sentences = [];
    for (const paragraph of paragraphs) {
        const parts = splitIntoSentences(paragraph);
        for (const part of parts) {
            const normalized = normalizeSentence(part);
            if (normalized) {
                sentences.push(normalized);
            }
        }
    }

    return sentences.join('\n\n');
}

async function cleanTextFiles() {
    try {
        console.log(`[*] Đang quét thư mục: ${STORIES_DIR}`);

        if (!await fs.pathExists(STORIES_DIR)) {
            console.error(`[X] Thư mục không tồn tại: ${STORIES_DIR}`);
            return;
        }

        const files = await fs.readdir(STORIES_DIR);
        const txtFiles = files.filter((file) => file.endsWith('.txt'));

        if (txtFiles.length === 0) {
            console.log('[!] Không tìm thấy file .txt nào.');
            return;
        }

        console.log(`[*] Bắt đầu dọn dẹp ${txtFiles.length} file .txt của truyện [${storyId}]...\n`);

        const escapedJunk = JUNK_TEXTS.map(escapeRegex);
        const junkRegex = new RegExp(`(?:\\s*)*(?:${escapedJunk.join('|')})(?:\\s*)*`, 'gi');

        let updatedCount = 0;
        const BATCH_SIZE = 50;

        for (let i = 0; i < txtFiles.length; i += BATCH_SIZE) {
            const chunk = txtFiles.slice(i, i + BATCH_SIZE);

            await Promise.all(chunk.map(async (file) => {
                const filePath = path.join(STORIES_DIR, file);
                const content = await fs.readFile(filePath, 'utf-8');
                const finalContent = normalizeContent(content, junkRegex);

                if (content !== finalContent) {
                    await fs.writeFile(filePath, finalContent, 'utf-8');
                    updatedCount++;
                }
            }));
        }

        console.log(`\n=== HOÀN TẤT: Đã dọn dẹp thành công ${updatedCount}/${txtFiles.length} file! ===`);
    } catch (error) {
        console.error('[X] Có lỗi xảy ra:', error.message);
    }
}

cleanTextFiles();
