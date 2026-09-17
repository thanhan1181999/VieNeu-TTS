from PIL import Image

# Resize ảnh logo về kích thước nhỏ (ví dụ 200x200)
with Image.open("thumbnail.jpeg") as img:
    # Resize mịn với chất lượng cao
    img_small = img.resize((200, 200), Image.Resampling.LANCZOS)
    img_small.save("thumbnail.jpeg", optimize=True)

print("Đã tạo thumbnail nhỏ thành công!")