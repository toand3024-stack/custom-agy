# Antigravity Custom Background & Glassmorphism Theme

Repo tùy biến giao diện **Antigravity** với hình nền 4K full-màn hình, giao diện **kính mờ nền trắng sáng (White Frosted Glass)** (`rgba(255, 255, 255, 0.62–0.88)`), chữ tối sắc nét (`#0F172A` / `#1E293B`), vùng canvas trung tâm trong suốt, cùng khung nhập prompt hiệu ứng kính mờ (**glassmorphism**).

Nền mặc định hiện tại là `backgrounds/anime-white-minimal-4k.jpg` (4K `3840x2160`, anime tối giản nền trắng sáng), kèm bộ sưu tập 4K nền trắng/sáng và vũ trụ:
- **Nền trắng / sáng (Anime & Phong cảnh 4K):**
  - `backgrounds/anime-white-minimal-4k.jpg` (Active — anime tối giản nền trắng, 4K `3840x2160`)
  - `backgrounds/anime-white-art-4k.jpg` (Anime art nền trắng tinh khiết, 4K `3840x2160`)
  - `backgrounds/anime-bright-scenery-4k.jpg` (Phong cảnh anime mây trắng & đồng cỏ sáng, 4K `3840x2160`)
  - `backgrounds/snow-white-scenery-4k.jpg` (Phong cảnh tuyết trắng tối giản, 4K `3840x2160`)
  - `backgrounds/anime-sky-glow-4k.jpg`, `backgrounds/anime-sky-4k.jpg`
- **Vũ trụ & Đêm (4K):** `milkyway-vibrant-4k.jpg`, `milkyway-4k.jpg`, `blackhole-gargantua-4k.jpg`, `blackhole-4k.jpg`, `nebula-4k.jpg`, `anime-stars-4k.jpg`, `cosmic-earth-bright.jpg`, `blackhole.jpg`, `blackhole-bright.jpg`, `evening-glow.jpg`.

## Cơ chế hoạt động

1. `antigravity_bg.py install` sao lưu file gốc `~/.local/share/antigravity/resources/app.asar` thành `app.asar.bak`.
2. Vá `dist/utils.js` (và bật DevTools trong `dist/debugConsole.js`) để gắn hook `installCustomAntigravityBg(win, hubContents)` vào cửa sổ Electron của Antigravity, đồng thời tính lại toàn bộ ASAR header + checksum SHA-256.
3. `antigravity_bg.py set` tự động tối ưu kích thước ảnh nền dưới `1.30 MB` (`<= 1,300,000` bytes) để chuỗi Base64 Data URI luôn nằm dưới ngưỡng `2 MB` CSS custom property của Chromium Blink.
4. Khi Antigravity mở, main process đọc `config.json`, `theme.css` và ảnh nền (mã hóa Base64 Data URI) rồi inject trực tiếp vào giao diện qua `<style id="agy-custom-bg-style">`.
5. `fs.watchFile` theo dõi `config.json` và `theme.css` liên tục — **mọi thay đổi ảnh nền hoặc độ mờ sẽ cập nhật trực tiếp ngay lập tức mà không cần khởi động lại app** (chỉ cần restart 1 lần duy nhất sau khi chạy `install` hoặc sau khi Antigravity tự cập nhật phiên bản mới).

## Cấu trúc thư mục

```text
antigravity-custom-bg/
├── antigravity_bg.py              # Script Python vá app.asar, tối ưu ảnh <1.3MB & CLI chính
├── gui.py                         # Giao diện đồ họa (Tkinter GUI) xem trước & thanh trượt live
├── set-bg.sh                      # Wrapper CLI & GUI (được symlink thành lệnh antigravity-bg)
├── antigravity-custom-bg.desktop  # File desktop launcher mở GUI từ menu ứng dụng Linux
├── config.json                    # Cấu hình ảnh nền, độ sáng, độ mờ, độ trong suốt
├── theme.css                      # CSS White Frosted Glass & hệ thống tự thích nghi sáng/tối
├── backgrounds/
│   ├── anime-white-minimal-4k.jpg  # Anime tối giản nền trắng 4K (3840x2160)
│   ├── anime-white-art-4k.jpg      # Anime art nền trắng tinh khiết 4K (3840x2160)
│   ├── anime-bright-scenery-4k.jpg # Phong cảnh anime mây trắng & đồng cỏ 4K (3840x2160)
│   ├── snow-white-scenery-4k.jpg   # Phong cảnh tuyết trắng tối giản 4K (3840x2160)
│   ├── anime-sky-glow-4k.jpg       # Anime bầu trời & cối xay gió 4K (3840x2160)
│   ├── anime-sky-4k.jpg            # Anime mây trời 4K (3840x2160)
│   ├── anime-stars-4k.jpg          # Anime thành phố đêm đầy sao 4K (3840x2160)
│   ├── milkyway-vibrant-4k.jpg     # Dải Ngân Hà rực rỡ 4K (3840x2160)
│   ├── milkyway-4k.jpg             # Dải Ngân Hà phản chiếu hồ núi 4K (3840x2160)
│   ├── blackhole-gargantua-4k.jpg  # Hố Đen Gargantua 4K (3840x2160)
│   ├── blackhole-4k.jpg            # Hố Đen nghệ thuật 4K (3840x2160)
│   ├── nebula-4k.jpg               # Tinh Vân vàng rực 4K (3840x2160)
│   ├── cosmic-earth-bright.jpg     # Trái Đất quỹ đạo
│   ├── blackhole.jpg               # Hố đen gốc
│   ├── blackhole-bright.jpg        # Hố đen nâng sáng
│   └── evening-glow.jpg            # Hoàng hôn hồ nước
└── assets/
    └── reference.jpg       # Ảnh mẫu giao diện tham khảo
```

## Hướng dẫn sử dụng (GUI & CLI)

Sau khi cài đặt, lệnh `antigravity-bg` được gắn toàn cục tại `~/.local/bin/antigravity-bg`, giúp bạn chạy công cụ từ **bất kỳ thư mục nào** bằng GUI hoặc CLI.

### Cách 1: Giao diện đồ họa (GUI)

Mở bảng điều khiển trực quan với xem trước ảnh (16:9), chọn file ảnh từ máy, kéo thanh trượt độ sáng/độ mờ/độ trong suốt cập nhật **live** sang Antigravity, hoặc cài/khôi phục patch chỉ bằng 1 nút bấm:

```bash
# Chạy từ bất kỳ thư mục nào:
antigravity-bg --gui

# Hoặc chạy trong thư mục repo:
./set-bg.sh --gui
python3 antigravity_bg.py gui
```

Ngoài ra, bạn có thể tìm **"Antigravity Custom Background"** trực tiếp trong Menu Ứng Dụng (App Launcher) của Linux nhờ file desktop launcher `~/.local/share/applications/antigravity-custom-bg.desktop`.

### Cách 2: Dòng lệnh (CLI)

#### 1. Cài đặt lần đầu (hoặc vá lại sau khi Antigravity update)

```bash
chmod +x antigravity_bg.py set-bg.sh gui.py
antigravity-bg --install
```

> Sau lần cài đặt đầu tiên, hãy khởi động lại Antigravity 1 lần để hook được nạp.

#### 2. Xem danh sách ảnh nền có sẵn & đổi ảnh nền (hot-reload)

```bash
# Liệt kê toàn bộ ảnh trong backgrounds/ kèm độ phân giải & tone màu
antigravity-bg --list

# Đổi sang ảnh có sẵn hoặc ảnh bất kỳ trên máy:
antigravity-bg backgrounds/anime-white-art-4k.jpg
antigravity-bg backgrounds/blackhole-gargantua-4k.jpg
antigravity-bg ~/Pictures/my-wallpaper.jpg
```

Script tự động copy ảnh vào `backgrounds/`, nén chuẩn `< 1.3 MB`, nhận diện nền tối/sáng (`detect_image_tone`) để chỉnh màu chữ tự động và hot-reload trực tiếp vào Antigravity.

#### 3. Tinh chỉnh thông số hình ảnh & độ mờ

```bash
antigravity-bg backgrounds/anime-white-minimal-4k.jpg --brightness 1.0 --contrast 1.02 --blur 0 --sidebar-opacity 0.62 --composer-opacity 0.88
```

#### 4. Bật / Tắt tạm thời hoặc khôi phục bản gốc

```bash
# Tắt tạm thời nền custom (live, giữ nguyên patch)
antigravity-bg --disable

# Bật lại nền custom (live)
antigravity-bg --enable

# Kiểm tra trạng thái patch & cấu hình
antigravity-bg --status

# Khôi phục nguyên trạng app.asar gốc (sau đó khởi động lại app)
antigravity-bg --restore
```

## Đưa lên GitHub

```bash
git remote add origin https://github.com/<username>/antigravity-custom-bg.git
git branch -M main
git push -u origin main
```

Khi sang máy mới hoặc cài lại hệ thống, chỉ cần clone repo về và chạy:

```bash
./set-bg.sh --install
```
