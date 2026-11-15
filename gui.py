#!/usr/bin/env python3
"""Native Tkinter GUI for Antigravity Custom Background & Glassmorphism Manager."""

from __future__ import annotations

import argparse
import io
import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from PIL import Image, ImageEnhance, ImageFilter, ImageTk

import antigravity_bg as core

DEFAULTS = {
    "opacity": 1.0,
    "brightness": 1.0,
    "contrast": 1.02,
    "blur_px": 0.0,
    "sidebar_opacity": 0.62,
    "composer_opacity": 0.88,
}

# Palette (modern slate dark UI)
BG_ROOT = "#0F172A"
BG_CARD = "#1E293B"
BG_PANEL = "#162032"
BG_INPUT = "#0B1220"
FG_PRIMARY = "#F8FAFC"
FG_MUTED = "#94A3B8"
ACCENT = "#38BDF8"
ACCENT_HOVER = "#0EA5E9"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
DANGER = "#EF4444"
BORDER = "#334155"


def scan_wallpapers(bg_dir: Path = core.BACKGROUNDS_DIR) -> list[dict[str, Any]]:
    """Scan backgrounds directory for valid image files (including extensionless)."""
    bg_dir.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    for entry in sorted(bg_dir.iterdir(), key=lambda p: p.name.lower()):
        if entry.name.startswith(".") or not entry.is_file():
            continue
        try:
            with Image.open(entry) as im:
                width, height = im.size
                fmt = im.format or "IMG"
        except Exception:
            continue
        items.append(
            {
                "path": entry,
                "name": entry.name,
                "rel": str(entry.relative_to(core.REPO_DIR)),
                "size_bytes": entry.stat().st_size,
                "width": width,
                "height": height,
                "format": fmt,
            }
        )
    return items


class AntigravityBgApp(tk.Tk):
    """Main graphical interface window for Antigravity Custom Background Manager."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Antigravity Custom Background Manager")
        self.geometry("1040x700")
        self.minsize(920, 620)
        self.configure(bg=BG_ROOT)

        self._wallpapers: list[dict[str, Any]] = []
        self._selected_path: Path | None = None
        self._preview_photo: ImageTk.PhotoImage | None = None
        self._apply_job: str | None = None
        self._preview_job: str | None = None
        self._loading_ui = True

        self._setup_styles()
        self._build_ui()
        self._load_state()
        self._loading_ui = False

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", background=BG_ROOT, foreground=FG_PRIMARY)
        style.configure("TFrame", background=BG_ROOT)
        style.configure("Card.TFrame", background=BG_CARD)
        style.configure(
            "TLabel", background=BG_ROOT, foreground=FG_PRIMARY, font=("Sans", 10)
        )
        style.configure(
            "Card.TLabel", background=BG_CARD, foreground=FG_PRIMARY, font=("Sans", 10)
        )
        style.configure(
            "Muted.TLabel", background=BG_CARD, foreground=FG_MUTED, font=("Sans", 9)
        )
        style.configure(
            "Title.TLabel",
            background=BG_CARD,
            foreground=FG_PRIMARY,
            font=("Sans", 11, "bold"),
        )
        style.configure(
            "TCheckbutton",
            background=BG_CARD,
            foreground=FG_PRIMARY,
            font=("Sans", 9),
        )
        style.map(
            "TCheckbutton",
            background=[("active", BG_CARD)],
            foreground=[("active", ACCENT)],
        )
        style.configure(
            "Horizontal.TScale",
            background=BG_CARD,
            troughcolor=BG_INPUT,
            sliderlength=16,
        )

    def _make_btn(
        self,
        parent: tk.Misc,
        text: str,
        command: Any,
        bg: str = "#334155",
        fg: str = FG_PRIMARY,
        active_bg: str = "#475569",
        font: tuple[Any, ...] = ("Sans", 9, "bold"),
        padx: int = 12,
        pady: int = 6,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            font=font,
            padx=padx,
            pady=pady,
        )

    def _build_ui(self) -> None:
        # Outer container
        root = tk.Frame(self, bg=BG_ROOT, padx=14, pady=12)
        root.pack(fill="both", expand=True)

        # --- TOP STATUS & ACTION BAR ---
        top_bar = tk.Frame(
            root,
            bg=BG_CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        top_bar.pack(fill="x", pady=(0, 12))

        status_left = tk.Frame(top_bar, bg=BG_CARD)
        status_left.pack(side="left", fill="x", expand=True)

        tk.Label(
            status_left,
            text="ANTIGRAVITY CUSTOM BACKGROUND",
            bg=BG_CARD,
            fg=ACCENT,
            font=("Sans", 12, "bold"),
        ).pack(anchor="w")

        badges_row = tk.Frame(status_left, bg=BG_CARD)
        badges_row.pack(anchor="w", pady=(4, 0))

        self.lbl_patch = tk.Label(
            badges_row,
            text="Patch: --",
            bg=BG_INPUT,
            fg=FG_MUTED,
            font=("Sans", 9, "bold"),
            padx=8,
            pady=3,
        )
        self.lbl_patch.pack(side="left", padx=(0, 8))

        self.lbl_enabled = tk.Label(
            badges_row,
            text="Nền: --",
            bg=BG_INPUT,
            fg=FG_MUTED,
            font=("Sans", 9, "bold"),
            padx=8,
            pady=3,
        )
        self.lbl_enabled.pack(side="left", padx=(0, 8))

        self.lbl_tone = tk.Label(
            badges_row,
            text="Tone: --",
            bg=BG_INPUT,
            fg=FG_MUTED,
            font=("Sans", 9, "bold"),
            padx=8,
            pady=3,
        )
        self.lbl_tone.pack(side="left")

        action_right = tk.Frame(top_bar, bg=BG_CARD)
        action_right.pack(side="right")

        self.btn_toggle = self._make_btn(
            action_right,
            "Tạm tắt nền",
            self._toggle_enabled,
            bg="#0284C7",
            active_bg="#0369A1",
        )
        self.btn_toggle.pack(side="left", padx=4)

        self.btn_install = self._make_btn(
            action_right,
            "Cài Patch (--install)",
            self._run_install,
            bg="#15803D",
            active_bg="#166534",
        )
        self.btn_install.pack(side="left", padx=4)

        self.btn_restore = self._make_btn(
            action_right,
            "Khôi phục gốc",
            self._run_restore,
            bg="#B91C1C",
            active_bg="#991B1B",
        )
        self.btn_restore.pack(side="left", padx=(4, 0))

        # --- MAIN 2-COLUMN BODY ---
        body = tk.Frame(root, bg=BG_ROOT)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=5)
        body.columnconfigure(1, weight=5)
        body.rowconfigure(0, weight=1)

        # LEFT PANEL: GALLERY + PREVIEW
        left_card = tk.Frame(
            body,
            bg=BG_CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=12,
            pady=12,
        )
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        left_header = tk.Frame(left_card, bg=BG_CARD)
        left_header.pack(fill="x", pady=(0, 8))

        tk.Label(
            left_header,
            text="Bộ sưu tập hình nền (backgrounds/)",
            bg=BG_CARD,
            fg=FG_PRIMARY,
            font=("Sans", 11, "bold"),
        ).pack(side="left")

        self._make_btn(
            left_header,
            "Chọn ảnh từ máy...",
            self._browse_wallpaper,
            bg="#0284C7",
            active_bg="#0369A1",
            padx=10,
            pady=4,
        ).pack(side="right")

        # Preview box (16:9 area)
        preview_wrap = tk.Frame(
            left_card,
            bg=BG_INPUT,
            highlightbackground=BORDER,
            highlightthickness=1,
            width=420,
            height=226,
        )
        preview_wrap.pack(fill="x", pady=(0, 6))
        preview_wrap.pack_propagate(False)

        self.lbl_preview = tk.Label(
            preview_wrap,
            text="Chọn một ảnh để xem trước",
            bg=BG_INPUT,
            fg=FG_MUTED,
            font=("Sans", 10),
        )
        self.lbl_preview.pack(fill="both", expand=True)

        self.lbl_img_info = tk.Label(
            left_card,
            text="",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Sans", 9),
            anchor="w",
        )
        self.lbl_img_info.pack(fill="x", pady=(0, 8))

        # Listbox + Scrollbar
        list_frame = tk.Frame(left_card, bg=BG_CARD)
        list_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            bg=BG_INPUT,
            fg=FG_PRIMARY,
            selectbackground="#0284C7",
            selectforeground="#FFFFFF",
            activestyle="none",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            font=("Monospace", 9),
            exportselection=False,
        )
        scrollbar.config(command=self.listbox.yview)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        self.listbox.bind("<Double-Button-1>", lambda _e: self._apply_selected_wallpaper())

        left_footer = tk.Frame(left_card, bg=BG_CARD)
        left_footer.pack(fill="x", pady=(10, 0))

        self._make_btn(
            left_footer,
            "Áp dụng ảnh đang chọn (Hot-Reload)",
            self._apply_selected_wallpaper,
            bg=ACCENT,
            fg="#0F172A",
            active_bg=ACCENT_HOVER,
            pady=8,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._make_btn(
            left_footer,
            "Làm mới",
            self._refresh_wallpapers,
            bg="#334155",
            pady=8,
        ).pack(side="right")

        # RIGHT PANEL: VISUAL SLIDERS & OPTIONS
        right_card = tk.Frame(
            body,
            bg=BG_CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(
            right_card,
            text="Tinh chỉnh hiệu ứng & Kính mờ (Live)",
            bg=BG_CARD,
            fg=FG_PRIMARY,
            font=("Sans", 11, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        self.slider_vars: dict[str, tk.DoubleVar] = {}
        self.slider_value_labels: dict[str, tk.Label] = {}

        slider_specs = [
            ("opacity", "Độ rõ ảnh nền (Opacity)", 0.10, 1.00, 0.02, "{:.2f}"),
            ("brightness", "Độ sáng nền (Brightness)", 0.40, 1.50, 0.02, "{:.2f}"),
            ("contrast", "Độ tương phản (Contrast)", 0.50, 1.50, 0.02, "{:.2f}"),
            ("blur_px", "Độ mờ nền (Blur px)", 0.0, 20.0, 0.5, "{:.1f} px"),
            (
                "sidebar_opacity",
                "Độ đậm thanh bên (Sidebar Opacity)",
                0.10,
                0.95,
                0.02,
                "{:.2f}",
            ),
            (
                "composer_opacity",
                "Độ đậm khung nhập chat (Composer)",
                0.30,
                1.00,
                0.02,
                "{:.2f}",
            ),
        ]

        sliders_container = tk.Frame(right_card, bg=BG_CARD)
        sliders_container.pack(fill="both", expand=True)

        for key, label_text, min_val, max_val, step, fmt in slider_specs:
            row_box = tk.Frame(sliders_container, bg=BG_PANEL, padx=10, pady=8)
            row_box.pack(fill="x", pady=(0, 8))

            top_row = tk.Frame(row_box, bg=BG_PANEL)
            top_row.pack(fill="x")

            tk.Label(
                top_row,
                text=label_text,
                bg=BG_PANEL,
                fg=FG_PRIMARY,
                font=("Sans", 9, "bold"),
            ).pack(side="left")

            val_lbl = tk.Label(
                top_row,
                text="--",
                bg=BG_PANEL,
                fg=ACCENT,
                font=("Monospace", 9, "bold"),
            )
            val_lbl.pack(side="right")

            var = tk.DoubleVar(value=DEFAULTS[key])
            self.slider_vars[key] = var
            self.slider_value_labels[key] = val_lbl

            scale = tk.Scale(
                row_box,
                variable=var,
                from_=min_val,
                to=max_val,
                resolution=step,
                orient="horizontal",
                showvalue=False,
                bg=BG_PANEL,
                fg=FG_PRIMARY,
                troughcolor=BG_INPUT,
                activebackground=ACCENT,
                highlightthickness=0,
                bd=0,
                command=lambda _val, k=key, f=fmt: self._on_slider_changed(k, f),
            )
            scale.pack(fill="x", pady=(4, 0))

        self.auto_apply_var = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(
            right_card,
            text="Tự động cập nhật sang Antigravity khi kéo thanh trượt",
            variable=self.auto_apply_var,
            bg=BG_CARD,
            fg=FG_PRIMARY,
            selectcolor=BG_INPUT,
            activebackground=BG_CARD,
            activeforeground=ACCENT,
            highlightthickness=0,
            font=("Sans", 9),
        )
        chk.pack(anchor="w", pady=(4, 10))

        right_btns = tk.Frame(right_card, bg=BG_CARD)
        right_btns.pack(fill="x")

        self._make_btn(
            right_btns,
            "Lưu & Áp dụng ngay",
            self._apply_sliders_now,
            bg="#15803D",
            active_bg="#166534",
            pady=8,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._make_btn(
            right_btns,
            "Đặt lại mặc định",
            self._reset_sliders,
            bg="#334155",
            pady=8,
        ).pack(side="right")

        # Bottom message bar
        self.lbl_status_msg = tk.Label(
            root,
            text="Sẵn sàng — hot-reload đang theo dõi config.json & theme.css",
            bg=BG_ROOT,
            fg=FG_MUTED,
            font=("Sans", 9),
            anchor="w",
        )
        self.lbl_status_msg.pack(fill="x", pady=(8, 0))

    def _set_message(self, text: str, color: str = FG_MUTED) -> None:
        self.lbl_status_msg.config(text=text, fg=color)

    def _load_state(self) -> None:
        cfg = core.load_config()
        formats = {
            "opacity": "{:.2f}",
            "brightness": "{:.2f}",
            "contrast": "{:.2f}",
            "blur_px": "{:.1f} px",
            "sidebar_opacity": "{:.2f}",
            "composer_opacity": "{:.2f}",
        }
        for key, default in DEFAULTS.items():
            try:
                val = float(cfg.get(key, default))
            except (TypeError, ValueError):
                val = default
            self.slider_vars[key].set(val)
            self.slider_value_labels[key].config(text=formats[key].format(val))

        self._refresh_status_badges(cfg)
        self._refresh_wallpapers(select_active=True)

    def _refresh_status_badges(self, cfg: dict[str, Any] | None = None) -> None:
        if cfg is None:
            cfg = core.load_config()

        # Patch status
        try:
            asar_path = core.find_asar_path(None)
            patched = core.is_asar_patched(asar_path)
            if patched:
                self.lbl_patch.config(text="Patch: ĐANG HOẠT ĐỘNG", fg=SUCCESS)
            else:
                self.lbl_patch.config(text="Patch: CHƯA CÀI", fg=WARNING)
        except FileNotFoundError:
            self.lbl_patch.config(text="Patch: Không tìm thấy app.asar", fg=DANGER)

        # Enabled status
        enabled = cfg.get("enabled", True) is not False
        if enabled:
            self.lbl_enabled.config(text="Nền: ĐANG BẬT", fg=SUCCESS)
            self.btn_toggle.config(text="Tạm tắt nền", bg="#D97706", activebackground="#B45309")
        else:
            self.lbl_enabled.config(text="Nền: ĐANG TẮT", fg=DANGER)
            self.btn_toggle.config(text="Bật lại nền", bg="#15803D", activebackground="#166534")

        # Tone badge
        tone = str(cfg.get("detected_tone", "auto"))
        lum = cfg.get("detected_luminance", "--")
        if tone == "dark":
            self.lbl_tone.config(text=f"Tương phản: Nền tối (lum={lum}) → Chữ trắng", fg="#E2E8F0")
        elif tone == "light":
            self.lbl_tone.config(text=f"Tương phản: Nền sáng (lum={lum}) → Chữ đen", fg="#FDE047")
        else:
            self.lbl_tone.config(text=f"Tương phản: {tone} (lum={lum})", fg=FG_MUTED)

    def _refresh_wallpapers(self, select_active: bool = False) -> None:
        cfg = core.load_config()
        active_rel = str(cfg.get("background_image") or "")
        active_path = Path(active_rel)
        if active_rel and not active_path.is_absolute():
            active_path = (core.REPO_DIR / active_path).resolve()

        self._wallpapers = scan_wallpapers()
        self.listbox.delete(0, "end")

        select_idx = 0 if self._wallpapers else None
        for idx, item in enumerate(self._wallpapers):
            p: Path = item["path"]
            is_active = active_rel and p.resolve() == active_path
            prefix = "★ " if is_active else "  "
            kb_or_mb = (
                f"{item['size_bytes'] / (1024 * 1024):.2f}MB"
                if item["size_bytes"] >= 1024 * 1024
                else f"{item['size_bytes'] // 1024}KB"
            )
            line = f"{prefix}{item['name']:<30} {item['width']}x{item['height']} ({kb_or_mb})"
            self.listbox.insert("end", line)
            if select_active and is_active:
                select_idx = idx
            elif not select_active and self._selected_path and p.resolve() == self._selected_path.resolve():
                select_idx = idx

        if select_idx is not None:
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(select_idx)
            self.listbox.see(select_idx)
            self._select_wallpaper_index(select_idx)

    def _on_listbox_select(self, _event: tk.Event[Any]) -> None:
        sel = self.listbox.curselection()
        if not sel:
            return
        self._select_wallpaper_index(int(sel[0]))

    def _select_wallpaper_index(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._wallpapers):
            return
        item = self._wallpapers[idx]
        self._selected_path = item["path"]
        self._update_preview(item)

    def _update_preview(self, item: dict[str, Any] | None = None) -> None:
        if item is None:
            if not self._selected_path:
                return
            matched = [w for w in self._wallpapers if w["path"] == self._selected_path]
            if not matched:
                return
            item = matched[0]

        img_path: Path = item["path"]
        brightness = float(self.slider_vars["brightness"].get())
        contrast = float(self.slider_vars["contrast"].get())
        blur_px = float(self.slider_vars["blur_px"].get())
        opacity = float(self.slider_vars["opacity"].get())

        try:
            with Image.open(img_path) as raw:
                im = raw.convert("RGB")
                im.thumbnail((420, 224), Image.Resampling.LANCZOS)
                if abs(brightness - 1.0) > 0.01:
                    im = ImageEnhance.Brightness(im).enhance(brightness)
                if abs(contrast - 1.0) > 0.01:
                    im = ImageEnhance.Contrast(im).enhance(contrast)
                if blur_px > 0.2:
                    im = im.filter(ImageFilter.GaussianBlur(radius=max(0.5, blur_px * 0.35)))
                if opacity < 0.99:
                    bg_dark = Image.new("RGB", im.size, (15, 23, 42))
                    im = Image.blend(bg_dark, im, opacity)
                self._preview_photo = ImageTk.PhotoImage(im)
                self.lbl_preview.config(image=self._preview_photo, text="")
        except Exception as exc:
            self.lbl_preview.config(image="", text=f"Không thể xem trước: {exc}")

        tone, lum = core.detect_image_tone(img_path, brightness=brightness)
        tone_vi = "Nền tối → Chữ trắng" if tone == "dark" else "Nền sáng → Chữ đen"
        size_mb = item["size_bytes"] / (1024 * 1024)
        self.lbl_img_info.config(
            text=(
                f"{item['name']}  |  {item['width']}x{item['height']} ({item['format']})  |  "
                f"{size_mb:.2f} MB  |  {tone_vi} (lum={lum:.1f})"
            )
        )

    def _on_slider_changed(self, key: str, fmt: str) -> None:
        val = float(self.slider_vars[key].get())
        self.slider_value_labels[key].config(text=fmt.format(val))
        if self._loading_ui:
            return

        # Debounce preview refresh
        if self._preview_job is not None:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(60, self._update_preview)

        # Debounce live hot-reload to Antigravity
        if self.auto_apply_var.get():
            if self._apply_job is not None:
                self.after_cancel(self._apply_job)
            self._apply_job = self.after(250, self._apply_sliders_now)

    def _build_set_namespace(self, image: str | None = None, enable: bool | None = None) -> argparse.Namespace:
        return argparse.Namespace(
            image=image,
            opacity=round(float(self.slider_vars["opacity"].get()), 2),
            brightness=round(float(self.slider_vars["brightness"].get()), 2),
            contrast=round(float(self.slider_vars["contrast"].get()), 2),
            blur=round(float(self.slider_vars["blur_px"].get()), 1),
            sidebar_opacity=round(float(self.slider_vars["sidebar_opacity"].get()), 2),
            composer_opacity=round(float(self.slider_vars["composer_opacity"].get()), 2),
            enable=(enable is True),
            disable=(enable is False),
        )

    def _apply_sliders_now(self) -> None:
        self._apply_job = None
        try:
            ns = self._build_set_namespace(image=None, enable=None)
            core.cmd_set(ns)
            cfg = core.load_config()
            self._refresh_status_badges(cfg)
            self._set_message("Đã cập nhật thông số & hot-reload sang Antigravity!", SUCCESS)
        except Exception as exc:
            self._set_message(f"Lỗi khi lưu thông số: {exc}", DANGER)

    def _apply_selected_wallpaper(self) -> None:
        if not self._selected_path or not self._selected_path.is_file():
            messagebox.showinfo("Chưa chọn ảnh", "Vui lòng chọn một ảnh trong danh sách.")
            return
        try:
            ns = self._build_set_namespace(image=str(self._selected_path), enable=True)
            core.cmd_set(ns)
            cfg = core.load_config()
            self._refresh_status_badges(cfg)
            self._refresh_wallpapers(select_active=True)
            self._set_message(
                f"Đã áp dụng hình nền: {self._selected_path.name} (auto-contrast: {cfg.get('detected_tone')})",
                SUCCESS,
            )
        except Exception as exc:
            messagebox.showerror("Lỗi áp dụng ảnh", str(exc))
            self._set_message(f"Lỗi: {exc}", DANGER)

    def _browse_wallpaper(self) -> None:
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Chọn ảnh nền từ máy tính",
            initialdir=str(Path.home() / "Pictures"),
            filetypes=[
                ("Ảnh nền", "*.jpg *.jpeg *.png *.webp *.avif *.bmp"),
                ("Tất cả file", "*.*"),
            ],
        )
        if not file_path:
            return
        try:
            ns = self._build_set_namespace(image=file_path, enable=True)
            core.cmd_set(ns)
            cfg = core.load_config()
            self._refresh_status_badges(cfg)
            self._refresh_wallpapers(select_active=True)
            self._set_message(
                f"Đã thêm & áp dụng ảnh: {cfg.get('background_image')} (tự nén <1.3MB)",
                SUCCESS,
            )
        except Exception as exc:
            messagebox.showerror("Không thể nạp ảnh", str(exc))
            self._set_message(f"Lỗi nạp ảnh: {exc}", DANGER)

    def _toggle_enabled(self) -> None:
        cfg = core.load_config()
        currently_enabled = cfg.get("enabled", True) is not False
        ns = self._build_set_namespace(image=None, enable=not currently_enabled)
        core.cmd_set(ns)
        new_cfg = core.load_config()
        self._refresh_status_badges(new_cfg)
        state_str = "ĐÃ BẬT" if not currently_enabled else "ĐÃ TẠM TẮT"
        self._set_message(f"Trạng thái nền custom: {state_str} (live)", SUCCESS)

    def _reset_sliders(self) -> None:
        self._loading_ui = True
        formats = {
            "opacity": "{:.2f}",
            "brightness": "{:.2f}",
            "contrast": "{:.2f}",
            "blur_px": "{:.1f} px",
            "sidebar_opacity": "{:.2f}",
            "composer_opacity": "{:.2f}",
        }
        for key, default in DEFAULTS.items():
            self.slider_vars[key].set(default)
            self.slider_value_labels[key].config(text=formats[key].format(default))
        self._loading_ui = False
        self._update_preview()
        self._apply_sliders_now()

    def _run_install(self) -> None:
        try:
            rc = core.cmd_install(argparse.Namespace(asar=None))
            self._refresh_status_badges()
            if rc == 0:
                self._set_message(
                    "Đã cài patch app.asar thành công! Khởi động lại Antigravity 1 lần nếu vừa cài mới.",
                    SUCCESS,
                )
                messagebox.showinfo(
                    "Cài đặt hoàn tất",
                    "Đã vá app.asar thành công (đã sao lưu app.asar.bak).\n"
                    "Nếu đây là lần đầu hoặc sau khi Antigravity update, hãy khởi động lại app 1 lần.",
                )
        except Exception as exc:
            messagebox.showerror("Lỗi cài patch", str(exc))
            self._set_message(f"Lỗi cài patch: {exc}", DANGER)

    def _run_restore(self) -> None:
        if not messagebox.askyesno(
            "Xác nhận khôi phục",
            "Khôi phục app.asar gốc từ file sao lưu .bak?\n"
            "(Sau đó khởi động lại Antigravity để về giao diện mặc định.)",
        ):
            return
        try:
            rc = core.cmd_restore(argparse.Namespace(asar=None))
            self._refresh_status_badges()
            if rc == 0:
                self._set_message("Đã khôi phục app.asar gốc từ .bak.", WARNING)
                messagebox.showinfo(
                    "Khôi phục hoàn tất",
                    "Đã khôi phục app.asar gốc. Hãy khởi động lại Antigravity.",
                )
            else:
                messagebox.showerror("Lỗi", "Không tìm thấy file sao lưu app.asar.bak.")
        except Exception as exc:
            messagebox.showerror("Lỗi khôi phục", str(exc))


def run_gui() -> int:
    app = AntigravityBgApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_gui())
