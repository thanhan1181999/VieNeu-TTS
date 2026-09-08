const fs = require('fs-extra');
const path = require('path');

const STORIES_DIR = path.join(__dirname, '../stories/truyen-001/script');

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

        console.log(`[*] Bắt đầu dọn dẹp ${txtFiles.length} file .txt...\n`);

        // Tạo Regex match cả khoảng trắng/dấu cách xung quanh từ rác
        const escapedJunk = JUNK_TEXTS.map(text => text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&'));
        const junkRegex = new RegExp(`(?:\\s*)*(?:${escapedJunk.join('|')})(?:\\s*)*`, 'gi');

        let updatedCount = 0;
        const BATCH_SIZE = 50; // Xử lý song song mỗi lần 50 file để tránh quá tải I/O

        for (let i = 0; i < txtFiles.length; i += BATCH_SIZE) {
            const chunk = txtFiles.slice(i, i + BATCH_SIZE);

            await Promise.all(chunk.map(async (file) => {
                const filePath = path.join(STORIES_DIR, file);
                const content = await fs.readFile(filePath, 'utf-8');

                // 1. Xóa rác
                let cleaned = content.replace(junkRegex, ' ');

                // 2. Tối ưu khoảng trắng thừa trên cùng 1 dòng
                cleaned = cleaned.replace(/[ \t]+/g, ' ');

                // 3. Xóa các dòng trống thừa (nhiều hơn 2 dòng trống liên tiếp -> giữ lại tối đa 1)
                cleaned = cleaned.replace(/\n\s*\n\s*\n+/g, '\n\n');

                const finalContent = cleaned.trim();

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