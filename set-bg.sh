#!/usr/bin/env bash
set -euo pipefail

SOURCE_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "${SOURCE_PATH}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/antigravity_bg.py"

if [[ $# -eq 0 ]]; then
  exec python3 "${PY_SCRIPT}" status
fi

case "$1" in
  --gui|gui)
    shift
    exec python3 "${PY_SCRIPT}" gui "$@"
    ;;
  --list|list|-l)
    shift
    exec python3 "${PY_SCRIPT}" list "$@"
    ;;
  --enable|enable)
    shift
    exec python3 "${PY_SCRIPT}" set --enable "$@"
    ;;
  --disable|disable)
    shift
    exec python3 "${PY_SCRIPT}" set --disable "$@"
    ;;
  --install|install)
    shift
    exec python3 "${PY_SCRIPT}" install "$@"
    ;;
  --restore|restore)
    shift
    exec python3 "${PY_SCRIPT}" restore "$@"
    ;;
  --status|status)
    shift
    exec python3 "${PY_SCRIPT}" status "$@"
    ;;
  set)
    shift
    exec python3 "${PY_SCRIPT}" set "$@"
    ;;
  -h|--help|help)
    cat <<'EOF'
Antigravity Custom Background Manager (CLI + GUI)

Cách mở giao diện đồ họa (GUI):
  antigravity-bg --gui                     Mở bảng điều khiển GUI (chọn ảnh + thanh trượt live)
  ./set-bg.sh --gui                        Mở GUI trực tiếp từ thư mục repo

Cách dùng nhanh bằng dòng lệnh (CLI - chạy từ bất kỳ đâu):
  antigravity-bg <đường_dẫn_ảnh> [tùy chọn] Đổi hình nền ngay lập tức (hot-reload)
  antigravity-bg --list                    Liệt kê toàn bộ ảnh trong backgrounds/ & tone màu
  antigravity-bg --enable                  Bật nền custom (live)
  antigravity-bg --disable                 Tạm tắt nền custom (live)
  antigravity-bg --install                 Cài đặt / vá lại app.asar (sau khi update app)
  antigravity-bg --restore                 Khôi phục giao diện gốc từ app.asar.bak
  antigravity-bg --status                  Xem trạng thái hiện tại

Tùy chọn khi đổi nền:
  --opacity <0.0-1.0>           Độ rõ ảnh nền (mặc định: 1.0)
  --brightness <số>             Độ sáng ảnh nền (mặc định: 1.0)
  --contrast <số>               Độ tương phản ảnh nền (mặc định: 1.02)
  --blur <px>                   Độ mờ ảnh nền theo px (mặc định: 0)
  --sidebar-opacity <0.0-1.0>   Độ đậm nền kính mờ sidebar (mặc định: 0.62)
  --composer-opacity <0.0-1.0>  Độ đậm khung nhập chat (mặc định: 0.88)
  --enable / --disable          Bật / tắt nền custom
EOF
    exit 0
    ;;
  *)
    exec python3 "${PY_SCRIPT}" set "$@"
    ;;
esac
