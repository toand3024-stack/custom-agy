#!/usr/bin/env python3
"""Antigravity Custom Background & Glassmorphism Theme Manager.

Patches Antigravity's Electron `app.asar` cleanly (with automatic backup) to
inject custom wallpaper and glassmorphism CSS from this repository, with live
hot-reloading whenever `config.json` or `theme.css` is updated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import sys
from pathlib import Path
from typing import Any

REPO_DIR = Path(__file__).resolve().parent
CONFIG_PATH = REPO_DIR / "config.json"
THEME_CSS_PATH = REPO_DIR / "theme.css"
BACKGROUNDS_DIR = REPO_DIR / "backgrounds"

DEFAULT_ASAR_CANDIDATES = [
    Path.home() / ".local" / "share" / "antigravity" / "resources" / "app.asar",
    Path("/opt/antigravity/resources/app.asar"),
    Path("/usr/lib/antigravity/resources/app.asar"),
]

PATCH_MARKER = "// [AGY-CUSTOM-BG-START]"
BLOCK_SIZE = 4 * 1024 * 1024

INJECTED_HELPER_TEMPLATE = r"""
// [AGY-CUSTOM-BG-START]
function installCustomAntigravityBg(win, hubContents) {
    if (!win || !hubContents || hubContents.isDestroyed?.()) {
        return;
    }
    const bgRepoDir = process.env.ANTIGRAVITY_BG_DIR || __AGY_BG_REPO_DIR__;
    const configPath = path_1.default.join(bgRepoDir, 'config.json');
    const themeCssPath = path_1.default.join(bgRepoDir, 'theme.css');
    const mimeMap = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.avif': 'image/avif',
    };
    const buildPayload = () => {
        if (!fs.existsSync(configPath) || !fs.existsSync(themeCssPath)) {
            return null;
        }
        const cfg = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
        if (cfg.enabled === false) {
            return { css: '', bgDataUri: '', brightness: 1.0 };
        }
        let imgPath = String(cfg.background_image || '');
        if (imgPath && !path_1.default.isAbsolute(imgPath)) {
            imgPath = path_1.default.join(bgRepoDir, imgPath);
        }
        let bgCssVal = 'none';
        let bgDataUri = '';
        if (imgPath && fs.existsSync(imgPath)) {
            const ext = path_1.default.extname(imgPath).toLowerCase();
            const mime = mimeMap[ext] || 'image/jpeg';
            const b64 = fs.readFileSync(imgPath).toString('base64');
            bgDataUri = `data:${mime};base64,${b64}`;
            bgCssVal = `url("${bgDataUri}")`;
        }
        const numOr = (val, fallback) => {
            const n = Number(val);
            return Number.isFinite(n) ? n : fallback;
        };
        const brightnessVal = numOr(cfg.brightness, 1.0);
        const varsCss = [
            ':root {',
            `  --agy-bg-image: ${bgCssVal};`,
            `  --agy-bg-opacity: ${numOr(cfg.opacity, 1.0)};`,
            `  --agy-bg-brightness: ${brightnessVal};`,
            `  --agy-bg-contrast: ${numOr(cfg.contrast, 1.02)};`,
            `  --agy-bg-blur: ${numOr(cfg.blur_px, 0)}px;`,
            `  --agy-sidebar-alpha: ${numOr(cfg.sidebar_opacity, 0.62)};`,
            `  --agy-composer-alpha: ${numOr(cfg.composer_opacity, 0.88)};`,
            '}',
            `body::before { background-image: ${bgCssVal} !important; }`,
        ].join('\n');
        const themeCss = fs.readFileSync(themeCssPath, 'utf-8');
        return {
            css: `${varsCss}\n${themeCss}`,
            bgDataUri,
            brightness: brightnessVal,
        };
    };
    const applyThemeToDom = () => {
        try {
            if (win.isDestroyed?.() || hubContents.isDestroyed?.()) {
                return;
            }
            const payload = buildPayload();
            if (payload === null) {
                return;
            }
            const cssJson = JSON.stringify(payload.css);
            const dataUriJson = JSON.stringify(payload.bgDataUri || '');
            const brightnessVal = Number.isFinite(payload.brightness) ? payload.brightness : 1.0;
            const script = `(() => {
                const id = 'agy-custom-bg-style';
                const cssText = ${cssJson};
                const bgDataUri = ${dataUriJson};
                const brightnessVal = ${brightnessVal};
                const rootStyle = document.documentElement.style;
                const autoContrastProps = [
                    '--agy-home-fg',
                    '--agy-home-shadow',
                    '--agy-header-fg',
                    '--agy-header-shadow',
                    '--agy-canvas-fg',
                    '--agy-canvas-shadow',
                    '--agy-pill-bg',
                    '--agy-pill-border',
                    '--agy-sidebar-bg',
                    '--agy-sidebar-fg',
                    '--agy-sidebar-muted-fg',
                    '--agy-sidebar-shadow',
                    '--agy-sidebar-pill-bg',
                    '--agy-sidebar-border',
                ];
                document.documentElement.classList.remove('dark');
                document.body?.classList.remove('dark', 'dark-theme', 'theme-dark');
                document.body?.classList.add('theme-light');
                let el = document.getElementById(id);
                if (!cssText) {
                    if (el) el.remove();
                    for (const prop of autoContrastProps) {
                        rootStyle.removeProperty(prop);
                    }
                    window.__agyLastToneKey = '';
                    return;
                }
                if (!el) {
                    el = document.createElement('style');
                    el.id = id;
                    (document.head || document.documentElement).appendChild(el);
                }
                if (el.textContent !== cssText) {
                    el.textContent = cssText;
                }
                if (!bgDataUri) {
                    return;
                }
                const toneKey = bgDataUri.length + ':' + bgDataUri.slice(-32) + ':' + brightnessVal;
                if (window.__agyLastToneKey === toneKey) {
                    return;
                }
                window.__agyLastToneKey = toneKey;
                const img = new Image();
                img.onload = () => {
                    try {
                        const canvas = document.createElement('canvas');
                        canvas.width = 64;
                        canvas.height = 64;
                        const ctx = canvas.getContext('2d');
                        if (!ctx) return;
                        ctx.drawImage(img, 0, 0, 64, 64);
                        const data = ctx.getImageData(0, 0, 64, 64).data;
                        let totalSum = 0;
                        let centerSum = 0;
                        let centerCount = 0;
                        for (let y = 0; y < 64; y++) {
                            const inY = y >= 20 && y < 44;
                            for (let x = 0; x < 64; x++) {
                                const idx = (y * 64 + x) * 4;
                                const lum = 0.2126 * data[idx] + 0.7152 * data[idx + 1] + 0.0722 * data[idx + 2];
                                totalSum += lum;
                                if (inY && x >= 16 && x < 48) {
                                    centerSum += lum;
                                    centerCount++;
                                }
                            }
                        }
                        const fullAvg = totalSum / (64 * 64);
                        const centerAvg = centerCount > 0 ? centerSum / centerCount : fullAvg;
                        const weighted = (0.7 * centerAvg + 0.3 * fullAvg) * brightnessVal;
                        const palette = weighted >= 140
                            ? {
                                '--agy-home-fg': '#0F172A',
                                '--agy-home-shadow': '0 1px 10px rgba(255, 255, 255, 0.95), 0 0 3px rgba(255, 255, 255, 1)',
                                '--agy-header-fg': '#0F172A',
                                '--agy-header-shadow': '0 1px 6px rgba(255, 255, 255, 0.95)',
                                '--agy-canvas-fg': '#0F172A',
                                '--agy-canvas-shadow': '0 1px 6px rgba(255, 255, 255, 0.95), 0 0 2px rgba(255, 255, 255, 1)',
                                '--agy-pill-bg': 'rgba(255, 255, 255, 0.86)',
                                '--agy-pill-border': 'rgba(15, 23, 42, 0.14)',
                                '--agy-sidebar-bg': 'rgba(255, 255, 255, var(--agy-sidebar-alpha, 0.62))',
                                '--agy-sidebar-fg': '#0F172A',
                                '--agy-sidebar-muted-fg': '#334155',
                                '--agy-sidebar-shadow': '0 1px 2px rgba(255, 255, 255, 0.95)',
                                '--agy-sidebar-pill-bg': 'rgba(255, 255, 255, 0.84)',
                                '--agy-sidebar-border': 'rgba(15, 23, 42, 0.12)',
                            }
                            : {
                                '--agy-home-fg': '#FFFFFF',
                                '--agy-home-shadow': '0 2px 14px rgba(0, 0, 0, 0.92), 0 1px 4px rgba(0, 0, 0, 0.98)',
                                '--agy-header-fg': '#FFFFFF',
                                '--agy-header-shadow': '0 1px 6px rgba(0, 0, 0, 0.92)',
                                '--agy-canvas-fg': '#F8FAFC',
                                '--agy-canvas-shadow': '0 1px 6px rgba(0, 0, 0, 0.92), 0 0 2px rgba(0, 0, 0, 0.98)',
                                '--agy-pill-bg': 'rgba(12, 16, 28, 0.72)',
                                '--agy-pill-border': 'rgba(255, 255, 255, 0.20)',
                                '--agy-sidebar-bg': 'rgba(12, 16, 28, var(--agy-sidebar-alpha, 0.56))',
                                '--agy-sidebar-fg': '#F8FAFC',
                                '--agy-sidebar-muted-fg': '#CBD5E1',
                                '--agy-sidebar-shadow': '0 1px 4px rgba(0, 0, 0, 0.90)',
                                '--agy-sidebar-pill-bg': 'rgba(255, 255, 255, 0.16)',
                                '--agy-sidebar-border': 'rgba(255, 255, 255, 0.14)',
                            };
                        for (const [k, v] of Object.entries(palette)) {
                            rootStyle.setProperty(k, v, 'important');
                        }
                    } catch (_) {}
                };
                img.src = bgDataUri;
            })();`;
            void hubContents.executeJavaScript(script, true).catch(() => undefined);
        }
        catch (err) {
            console.error('[AGY-CUSTOM-BG] Failed to apply theme:', err);
        }
    };
    const onFileChange = () => {
        applyThemeToDom();
    };
    hubContents.on('dom-ready', applyThemeToDom);
    hubContents.on('did-finish-load', applyThemeToDom);
    const watchTargets = [configPath, themeCssPath];
    for (const target of watchTargets) {
        fs.watchFile(target, { persistent: false, interval: 600 }, onFileChange);
    }
    win.once('closed', () => {
        hubContents.off?.('dom-ready', applyThemeToDom);
        hubContents.off?.('did-finish-load', applyThemeToDom);
        for (const target of watchTargets) {
            fs.unwatchFile(target, onFileChange);
        }
    });
}
// [AGY-CUSTOM-BG-END]
"""


def find_asar_path(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(f"ASAR not found: {p}")
        return p
    for candidate in DEFAULT_ASAR_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate Antigravity app.asar automatically. Pass --asar <path>."
    )


def compute_integrity(data: bytes) -> dict[str, Any]:
    full_hash = hashlib.sha256(data).hexdigest()
    if len(data) == 0:
        blocks = [full_hash]
    else:
        blocks = [
            hashlib.sha256(data[i : i + BLOCK_SIZE]).hexdigest()
            for i in range(0, len(data), BLOCK_SIZE)
        ]
    return {
        "algorithm": "SHA256",
        "hash": full_hash,
        "blockSize": BLOCK_SIZE,
        "blocks": blocks,
    }


def read_asar_header(asar_path: Path) -> tuple[dict[str, Any], int]:
    with asar_path.open("rb") as f:
        header_prefix = f.read(16)
        if len(header_prefix) < 16:
            raise ValueError(f"Invalid ASAR file (too small): {asar_path}")
        u1, u2, _u3, json_len = struct.unpack("<IIII", header_prefix)
        if u1 != 4:
            raise ValueError(f"Unexpected ASAR header pickle prefix u1={u1}")
        header = json.loads(f.read(json_len).decode("utf-8"))
        base_offset = 8 + u2
        return header, base_offset


def get_asar_entry(header: dict[str, Any], rel_path: str) -> dict[str, Any]:
    cur: dict[str, Any] = header
    for part in rel_path.strip("/").split("/"):
        files = cur.get("files")
        if not isinstance(files, dict) or part not in files:
            raise KeyError(f"Entry not found in app.asar: {rel_path}")
        cur = files[part]
    return cur


def read_asar_file(asar_path: Path, rel_path: str) -> bytes:
    header, base_offset = read_asar_header(asar_path)
    entry = get_asar_entry(header, rel_path)
    if entry.get("unpacked") or "offset" not in entry:
        raise ValueError(f"Entry {rel_path} is not packed inside {asar_path}")
    with asar_path.open("rb") as f:
        f.seek(base_offset + int(entry["offset"]))
        return f.read(int(entry["size"]))


def repack_asar(src_asar: Path, dst_asar: Path, replacements: dict[str, bytes]) -> None:
    """Repack `src_asar` into `dst_asar`, replacing specified file payloads."""
    header, old_base = read_asar_header(src_asar)
    new_header = json.loads(json.dumps(header))
    temp_payload = dst_asar.with_name(f"{dst_asar.name}.payload.{os.getpid()}.tmp")
    temp_asar = dst_asar.with_name(f"{dst_asar.name}.{os.getpid()}.tmp")

    current_offset = 0
    try:
        with src_asar.open("rb") as src_f, temp_payload.open("wb") as pay_f:
            def process_dir(node: dict[str, Any], prefix: str = "") -> None:
                nonlocal current_offset
                files = node.get("files", {})
                for name, entry in files.items():
                    rel = f"{prefix}/{name}" if prefix else name
                    if "files" in entry:
                        process_dir(entry, rel)
                    elif entry.get("unpacked") or "offset" not in entry:
                        continue
                    else:
                        if rel in replacements:
                            data = replacements[rel]
                            entry["size"] = len(data)
                            entry["offset"] = str(current_offset)
                            entry["integrity"] = compute_integrity(data)
                            pay_f.write(data)
                            current_offset += len(data)
                        else:
                            size = int(entry["size"])
                            old_off = int(entry["offset"])
                            src_f.seek(old_base + old_off)
                            entry["offset"] = str(current_offset)
                            remaining = size
                            while remaining > 0:
                                chunk = src_f.read(min(remaining, 1024 * 1024))
                                if not chunk:
                                    raise EOFError(
                                        f"Unexpected EOF reading {rel} from {src_asar}"
                                    )
                                pay_f.write(chunk)
                                remaining -= len(chunk)
                            current_offset += size

            process_dir(new_header)

        json_bytes = json.dumps(new_header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        json_len = len(json_bytes)
        pad_len = (4 - (json_len % 4)) % 4
        u3 = 4 + json_len + pad_len
        u2 = 4 + u3
        u1 = 4

        with temp_asar.open("wb") as out_f, temp_payload.open("rb") as pay_f:
            out_f.write(struct.pack("<IIII", u1, u2, u3, json_len))
            out_f.write(json_bytes)
            out_f.write(b"\x00" * pad_len)
            shutil.copyfileobj(pay_f, out_f, length=1024 * 1024)

        os.replace(temp_asar, dst_asar)
    finally:
        for leftover in (temp_payload, temp_asar):
            if leftover.exists():
                leftover.unlink(missing_ok=True)


def patch_utils_js(src_bytes: bytes) -> bytes:
    text = src_bytes.decode("utf-8")
    if PATCH_MARKER in text:
        return src_bytes

    target_call = "    void win.loadURL(url);\n    return win;"
    if target_call not in text:
        raise RuntimeError(
            "Could not find `void win.loadURL(url);` inside dist/utils.js"
        )

    patched_call = (
        "    installCustomAntigravityBg(win, hubContents);\n"
        "    void win.loadURL(url);\n"
        "    return win;"
    )
    text = text.replace(target_call, patched_call, 1)

    helper = INJECTED_HELPER_TEMPLATE.replace(
        "__AGY_BG_REPO_DIR__", json.dumps(str(REPO_DIR))
    )
    text = text.rstrip() + "\n" + helper.lstrip()
    return text.encode("utf-8")


def patch_debug_console_js(src_bytes: bytes) -> bytes:
    text = src_bytes.decode("utf-8")
    target = "function isDebugConsoleEnabled() {\n    return !electron_1.app.isPackaged;\n}"
    if target in text:
        replacement = (
            "function isDebugConsoleEnabled() {\n"
            "    return true; // [AGY-CUSTOM-BG] enable DevTools\n"
            "}"
        )
        return text.replace(target, replacement, 1).encode("utf-8")
    if "// [AGY-CUSTOM-BG]" in text:
        return src_bytes
    return src_bytes


def is_asar_patched(asar_path: Path) -> bool:
    try:
        utils_bytes = read_asar_file(asar_path, "dist/utils.js")
        return PATCH_MARKER.encode("utf-8") in utils_bytes
    except Exception:
        return False


def cmd_install(args: argparse.Namespace) -> int:
    asar_path = find_asar_path(args.asar)
    backup_path = asar_path.with_name(f"{asar_path.name}.bak")

    if not backup_path.exists():
        if is_asar_patched(asar_path):
            print(
                f"Warning: {asar_path} is already patched and no .bak exists. "
                "Using current app.asar as base.",
                file=sys.stderr,
            )
        shutil.copy2(asar_path, backup_path)
        print(f"Created backup: {backup_path}")
    else:
        print(f"Using existing clean backup: {backup_path}")

    utils_orig = read_asar_file(backup_path, "dist/utils.js")
    debug_orig = read_asar_file(backup_path, "dist/debugConsole.js")

    replacements = {
        "dist/utils.js": patch_utils_js(utils_orig),
        "dist/debugConsole.js": patch_debug_console_js(debug_orig),
    }
    repack_asar(backup_path, asar_path, replacements)
    print(f"Patched successfully: {asar_path}")
    print(f"Theme source repo:    {REPO_DIR}")
    print("Restart Antigravity once for the main-process hook to load.")
    print("Afterwards, any change via set-bg.sh or config.json reloads live!")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    asar_path = find_asar_path(args.asar)
    backup_path = asar_path.with_name(f"{asar_path.name}.bak")
    if not backup_path.is_file():
        print(f"No backup found at {backup_path}", file=sys.stderr)
        return 1
    temp_restore = asar_path.with_name(f"{asar_path.name}.restore.{os.getpid()}.tmp")
    shutil.copy2(backup_path, temp_restore)
    os.replace(temp_restore, asar_path)
    print(f"Restored original app.asar from {backup_path}")
    print("Restart Antigravity to revert to the default appearance.")
    return 0


def load_config() -> dict[str, Any]:
    if CONFIG_PATH.is_file():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "enabled": True,
        "background_image": "backgrounds/anime-white-minimal-4k.jpg",
        "opacity": 1.0,
        "brightness": 1.0,
        "contrast": 1.02,
        "blur_px": 0.0,
        "sidebar_opacity": 0.62,
        "composer_opacity": 0.88,
    }


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.utime(CONFIG_PATH, None)


MAX_CSS_VAR_IMAGE_BYTES = 1_300_000
AUTO_CONTRAST_START = "/* [AGY-AUTO-CONTRAST-START] */"
AUTO_CONTRAST_END = "/* [AGY-AUTO-CONTRAST-END] */"


def detect_image_tone(img_path: Path, brightness: float = 1.0) -> tuple[str, float]:
    """Detect whether wallpaper (weighted toward center greeting) is 'light' or 'dark'."""
    try:
        from PIL import Image

        with Image.open(img_path) as raw:
            im = raw.convert("RGB").resize((64, 64), Image.Resampling.BILINEAR)
            pixels = im.load()
            total_sum = 0.0
            center_sum = 0.0
            center_count = 0
            for y in range(64):
                in_y = 20 <= y < 44
                for x in range(64):
                    r, g, b = pixels[x, y]
                    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
                    total_sum += lum
                    if in_y and 16 <= x < 48:
                        center_sum += lum
                        center_count += 1
            full_avg = total_sum / (64 * 64)
            center_avg = center_sum / center_count if center_count else full_avg
            weighted_lum = (0.7 * center_avg + 0.3 * full_avg) * brightness
            tone = "light" if weighted_lum >= 140.0 else "dark"
            return tone, weighted_lum
    except Exception:
        return "light", 180.0


def sync_theme_auto_contrast(tone: str, lum: float) -> None:
    """Update auto-contrast CSS variables in theme.css for immediate live hot-reload."""
    if not THEME_CSS_PATH.is_file():
        return
    if tone == "dark":
        block = (
            f"{AUTO_CONTRAST_START}\n"
            f"/* auto-detected tone: dark (lum={lum:.1f}) -> bright white text & dark glass */\n"
            ":root, body {\n"
            "  --agy-home-fg: #FFFFFF !important;\n"
            "  --agy-home-shadow: 0 2px 14px rgba(0, 0, 0, 0.92), 0 1px 4px rgba(0, 0, 0, 0.98) !important;\n"
            "  --agy-header-fg: #FFFFFF !important;\n"
            "  --agy-header-shadow: 0 1px 6px rgba(0, 0, 0, 0.92) !important;\n"
            "  --agy-canvas-fg: #F8FAFC !important;\n"
            "  --agy-canvas-shadow: 0 1px 6px rgba(0, 0, 0, 0.92), 0 0 2px rgba(0, 0, 0, 0.98) !important;\n"
            "  --agy-pill-bg: rgba(12, 16, 28, 0.72) !important;\n"
            "  --agy-pill-border: rgba(255, 255, 255, 0.20) !important;\n"
            "  --agy-sidebar-bg: rgba(12, 16, 28, var(--agy-sidebar-alpha, 0.56)) !important;\n"
            "  --agy-sidebar-fg: #F8FAFC !important;\n"
            "  --agy-sidebar-muted-fg: #CBD5E1 !important;\n"
            "  --agy-sidebar-shadow: 0 1px 4px rgba(0, 0, 0, 0.90) !important;\n"
            "  --agy-sidebar-pill-bg: rgba(255, 255, 255, 0.16) !important;\n"
            "  --agy-sidebar-border: rgba(255, 255, 255, 0.14) !important;\n"
            "}\n"
            f"{AUTO_CONTRAST_END}"
        )
    else:
        block = (
            f"{AUTO_CONTRAST_START}\n"
            f"/* auto-detected tone: light (lum={lum:.1f}) -> dark text & light glass */\n"
            ":root, body {\n"
            "  --agy-home-fg: #0F172A !important;\n"
            "  --agy-home-shadow: 0 1px 10px rgba(255, 255, 255, 0.95), 0 0 3px rgba(255, 255, 255, 1) !important;\n"
            "  --agy-header-fg: #0F172A !important;\n"
            "  --agy-header-shadow: 0 1px 6px rgba(255, 255, 255, 0.95) !important;\n"
            "  --agy-canvas-fg: #0F172A !important;\n"
            "  --agy-canvas-shadow: 0 1px 6px rgba(255, 255, 255, 0.95), 0 0 2px rgba(255, 255, 255, 1) !important;\n"
            "  --agy-pill-bg: rgba(255, 255, 255, 0.86) !important;\n"
            "  --agy-pill-border: rgba(15, 23, 42, 0.14) !important;\n"
            "  --agy-sidebar-bg: rgba(255, 255, 255, var(--agy-sidebar-alpha, 0.62)) !important;\n"
            "  --agy-sidebar-fg: #0F172A !important;\n"
            "  --agy-sidebar-muted-fg: #334155 !important;\n"
            "  --agy-sidebar-shadow: 0 1px 2px rgba(255, 255, 255, 0.95) !important;\n"
            "  --agy-sidebar-pill-bg: rgba(255, 255, 255, 0.84) !important;\n"
            "  --agy-sidebar-border: rgba(15, 23, 42, 0.12) !important;\n"
            "}\n"
            f"{AUTO_CONTRAST_END}"
        )

    css_text = THEME_CSS_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(AUTO_CONTRAST_START) + r".*?" + re.escape(AUTO_CONTRAST_END),
        flags=re.DOTALL,
    )
    if pattern.search(css_text):
        new_css = pattern.sub(lambda _m: block, css_text, count=1)
    else:
        new_css = css_text.rstrip() + "\n\n" + block + "\n"
    THEME_CSS_PATH.write_text(new_css, encoding="utf-8")
    os.utime(THEME_CSS_PATH, None)


def optimize_wallpaper_size(dest: Path, max_bytes: int = MAX_CSS_VAR_IMAGE_BYTES) -> Path:
    """Ensure copied wallpaper stays under ~1.3MB (~1.75MB Base64 < Chromium 2MB CSS var limit)."""
    if dest.stat().st_size <= max_bytes:
        return dest
    try:
        import io
        from PIL import Image
    except ImportError:
        return dest
    im = Image.open(dest).convert("RGB")
    lo, hi = 75, 92
    best_data = None
    while lo <= hi:
        mid = (lo + hi) // 2
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=mid, optimize=True)
        raw = buf.getvalue()
        if len(raw) <= max_bytes:
            best_data = raw
            lo = mid + 1
        else:
            hi = mid - 1
    if best_data is not None:
        out_path = dest if dest.suffix.lower() in {".jpg", ".jpeg"} else dest.with_suffix(".jpg")
        out_path.write_bytes(best_data)
        if out_path != dest and dest.exists():
            dest.unlink()
        return out_path
    webp_path = dest.with_suffix(".webp")
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=85, method=4)
    webp_path.write_bytes(buf.getvalue())
    if webp_path != dest and dest.exists():
        dest.unlink()
    return webp_path


def cmd_set(args: argparse.Namespace) -> int:
    cfg = load_config()

    if args.image:
        src = Path(args.image).expanduser()
        if not src.is_absolute():
            # Check relative to CWD first, then relative to REPO_DIR
            cwd_candidate = Path.cwd() / src
            repo_candidate = REPO_DIR / src
            if cwd_candidate.is_file():
                src = cwd_candidate.resolve()
            elif repo_candidate.is_file():
                src = repo_candidate.resolve()
            else:
                raise FileNotFoundError(f"Image not found: {args.image}")
        elif not src.is_file():
            raise FileNotFoundError(f"Image not found: {src}")

        BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            rel_to_bg = src.relative_to(BACKGROUNDS_DIR)
            dest = BACKGROUNDS_DIR / rel_to_bg
        except ValueError:
            dest = BACKGROUNDS_DIR / src.name
            if src != dest:
                shutil.copy2(src, dest)
                print(f"Copied wallpaper to: {dest}")

        dest = optimize_wallpaper_size(dest)
        cfg["background_image"] = str(dest.relative_to(REPO_DIR))

    if args.opacity is not None:
        cfg["opacity"] = args.opacity
    if args.brightness is not None:
        cfg["brightness"] = args.brightness
    if args.contrast is not None:
        cfg["contrast"] = args.contrast
    if args.blur is not None:
        cfg["blur_px"] = args.blur
    if args.sidebar_opacity is not None:
        cfg["sidebar_opacity"] = args.sidebar_opacity
    if args.composer_opacity is not None:
        cfg["composer_opacity"] = args.composer_opacity
    if args.disable:
        cfg["enabled"] = False
    elif args.enable:
        cfg["enabled"] = True

    active_rel = str(cfg.get("background_image") or "")
    if active_rel:
        active_img = Path(active_rel)
        if not active_img.is_absolute():
            active_img = REPO_DIR / active_img
        if active_img.is_file():
            try:
                br = float(cfg.get("brightness", 1.0))
            except (TypeError, ValueError):
                br = 1.0
            tone, lum = detect_image_tone(active_img, brightness=br)
            cfg["detected_tone"] = tone
            cfg["detected_luminance"] = round(lum, 1)
            sync_theme_auto_contrast(tone, lum)

    save_config(cfg)
    print(f"Updated config: {CONFIG_PATH}")
    print(json.dumps(cfg, indent=2, ensure_ascii=False))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    try:
        asar_path = find_asar_path(args.asar)
        backup_path = asar_path.with_name(f"{asar_path.name}.bak")
        patched = is_asar_patched(asar_path)
        print(f"ASAR path:      {asar_path}")
        print(f"Backup exists:  {backup_path.is_file()} ({backup_path})")
        print(f"Patch active:   {patched}")
    except FileNotFoundError as exc:
        print(f"ASAR status:    {exc}")

    cfg = load_config()
    print(f"Repo directory: {REPO_DIR}")
    print("Current config:")
    print(json.dumps(cfg, indent=2, ensure_ascii=False))
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    cfg = load_config()
    active_rel = str(cfg.get("background_image") or "")
    active_path = Path(active_rel)
    if active_rel and not active_path.is_absolute():
        active_path = (REPO_DIR / active_path).resolve()

    if not BACKGROUNDS_DIR.is_dir():
        print(f"No backgrounds directory found at {BACKGROUNDS_DIR}")
        return 0

    try:
        from PIL import Image
    except ImportError:
        Image = None  # type: ignore[assignment]

    try:
        brightness = float(cfg.get("brightness", 1.0))
    except (TypeError, ValueError):
        brightness = 1.0

    print(f"Wallpapers in {BACKGROUNDS_DIR}:")
    count = 0
    for entry in sorted(BACKGROUNDS_DIR.iterdir(), key=lambda p: p.name.lower()):
        if entry.name.startswith(".") or not entry.is_file():
            continue
        dims = ""
        if Image is not None:
            try:
                with Image.open(entry) as im:
                    dims = f"{im.width}x{im.height}"
            except Exception:
                continue
        tone, lum = detect_image_tone(entry, brightness=brightness)
        is_active = bool(active_rel) and entry.resolve() == active_path
        marker = "*" if is_active else " "
        size_mb = entry.stat().st_size / (1024 * 1024)
        print(
            f" {marker} backgrounds/{entry.name:<32} {dims:<11} "
            f"{size_mb:5.2f} MB  [{tone:<5} lum={lum:5.1f}]"
        )
        count += 1
    if count == 0:
        print("  (empty)")
    return 0


def cmd_gui(_args: argparse.Namespace) -> int:
    import gui

    return gui.run_gui()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Antigravity custom background & glassmorphism theme."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_gui = sub.add_parser("gui", help="Launch graphical user interface (GUI)")
    p_gui.set_defaults(func=cmd_gui)

    p_list = sub.add_parser("list", help="List available wallpapers in backgrounds/")
    p_list.set_defaults(func=cmd_list)

    p_install = sub.add_parser("install", help="Patch app.asar to load custom theme")
    p_install.add_argument("--asar", help="Explicit path to Antigravity app.asar")
    p_install.set_defaults(func=cmd_install)

    p_restore = sub.add_parser("restore", help="Restore original app.asar from .bak")
    p_restore.add_argument("--asar", help="Explicit path to Antigravity app.asar")
    p_restore.set_defaults(func=cmd_restore)

    p_status = sub.add_parser("status", help="Show patch status and active config")
    p_status.add_argument("--asar", help="Explicit path to Antigravity app.asar")
    p_status.set_defaults(func=cmd_status)

    p_set = sub.add_parser("set", help="Set wallpaper image and/or visual parameters")
    p_set.add_argument("image", nargs="?", help="Path to wallpaper image")
    p_set.add_argument("--opacity", type=float, help="Wallpaper opacity (0.0 - 1.0)")
    p_set.add_argument("--brightness", type=float, help="Brightness multiplier (e.g. 0.95)")
    p_set.add_argument("--contrast", type=float, help="Contrast multiplier (e.g. 1.05)")
    p_set.add_argument("--blur", type=float, help="Background blur in px (e.g. 0, 4, 8)")
    p_set.add_argument("--sidebar-opacity", type=float, help="Sidebar darkness alpha (0.0 - 1.0)")
    p_set.add_argument("--composer-opacity", type=float, help="Composer box alpha (0.0 - 1.0)")
    p_set.add_argument("--enable", action="store_true", help="Enable custom background")
    p_set.add_argument("--disable", action="store_true", help="Temporarily disable custom background")
    p_set.set_defaults(func=cmd_set)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
