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

async function cleanTextFiles() {
    try {
        console.log(`[*] Đang quét thư mục: ${STORIES_DIR}`);

        if (!await fs.pathExists(STORIES_DIR)) {
            console.error(`[X] Thư mục không tồn tại: ${STORIES_DIR}`);
            return;
        }

        const files = await fs.readdir(STORIES_DIR);
        const txtFiles = files.filter(file => file.endsWith('.txt'));

        if (txtFiles.length === 0) {
            console.log('[!] Không tìm thấy file .txt nào.');
            return;
        }

        console.log(`[*] Bắt đầu dọn dẹp ${txtFiles.length} file .txt của truyện [${storyId}]...\n`);

        // Tạo Regex match cả khoảng trắng/dấu cách xung quanh từ rác
        const escapedJunk = JUNK_TEXTS.map(text => text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&'));
        const junkRegex = new RegExp(`(?:\\s*)*(?:${escapedJunk.join('|')})(?:\\s*)*`, 'gi');

        let updatedCount = 0;
        const BATCH_SIZE = 50;

        for (let i = 0; i < txtFiles.length; i += BATCH_SIZE) {
            const chunk = txtFiles.slice(i, i + BATCH_SIZE);

            await Promise.all(chunk.map(async (file) => {
                const filePath = path.join(STORIES_DIR, file);
                const content = await fs.readFile(filePath, 'utf-8');

                // Step 1: Xóa các từ/cụm từ rác
                let cleaned = content.replace(junkRegex, ' ');

                // Step 2: Chuẩn hóa xuống dòng (chuyển CRLF \r\n thành LF \n)
                cleaned = cleaned.replace(/\r\n/g, '\n');

                // Step 3: Tách văn bản thành các đoạn (các đoạn vốn phân cách bởi 2 hoặc nhiều dòng trống)
                const paragraphs = cleaned.split(/\n\s*\n+/);

                // Step 4: Xử lý từng đoạn - gộp các dòng lẻ bị xuống dòng bừa bãi thành 1 dòng duy nhất
                const fixedParagraphs = paragraphs
                    .map(p => {
                        return p
                            .split('\n')
                            .map(line => line.trim())
                            .filter(line => line.length > 0)
                            .join(' ')             // Gộp các dòng lẻ trong 1 câu bằng khoảng trắng
                            .replace(/[ \t]+/g, ' '); // Tối ưu khoảng trắng thừa
                    })
                    .filter(p => p.length > 0);   // Loại bỏ đoạn trống

                // Step 5: Nối lại các đoạn với đúng 1 dòng trống ở giữa (\n\n)
                const finalContent = fixedParagraphs.join('\n\n');

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