#!/usr/bin/env python3
"""Generate LINE Rich Menu image for CosmeBuzz - Pro Design v3 (大胆レイアウト)."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import math

W, H = 2500, 1686
HALF_W, HALF_H = W // 2, H // 2

# --- Colors ---
BG_DARK = (18, 18, 26)
ACCENT_ROSE = (220, 140, 158)
ACCENT_TEAL = (78, 205, 196)
ACCENT_PINK = (236, 120, 160)
ACCENT_AMBER = (255, 193, 100)
ACCENT_BLUE = (100, 160, 255)
WHITE = (255, 255, 255)
GRAY = (130, 130, 150)

FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_REGULAR = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
FONT_HEAVY = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def draw_gradient_rect(img, xy, color_top, color_bottom):
    x0, y0, x1, y1 = xy
    draw = ImageDraw.Draw(img)
    for y in range(y0, y1):
        ratio = (y - y0) / max(y1 - y0, 1)
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
        draw.line([(x0, y), (x1, y)], fill=(r, g, b))


def draw_glow(img, cx, cy, radius, color, intensity=0.25):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(radius, 0, -3):
        frac = i / radius
        alpha = int(255 * intensity * (1 - frac ** 1.2))
        alpha = max(0, min(255, alpha))
        od.ellipse(
            [cx - i, cy - i, cx + i, cy + i],
            fill=(*color, alpha)
        )
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"), (0, 0))
    return img


def draw_icon_chart_big(draw, cx, cy, color, scale=1.0):
    """大きなチャートアイコン"""
    s = scale
    bar_data = [
        (-70, 40, 30, 90),
        (-25, -10, 30, 140),
        (20, 20, 30, 110),
        (65, -40, 30, 170),
    ]
    for bx, by, bw, bh in bar_data:
        x0 = int(cx + bx * s)
        y0 = int(cy + by * s)
        x1 = int(cx + (bx + bw) * s)
        y1 = int(cy + (by + bh) * s)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=int(8 * s), fill=color)

    # 上向きトレンド矢印
    ax = int(cx + 95 * s)
    ay = int(cy - 60 * s)
    arrow_size = int(22 * s)
    draw.polygon([
        (ax, ay - arrow_size),
        (ax - arrow_size, ay + int(5 * s)),
        (ax + arrow_size, ay + int(5 * s))
    ], fill=WHITE)
    shaft_w = int(8 * s)
    draw.rectangle((ax - shaft_w // 2, ay + int(5 * s), ax + shaft_w // 2, ay + int(40 * s)), fill=WHITE)


def draw_icon_crown_big(draw, cx, cy, color, scale=1.0):
    """大きな王冠アイコン"""
    s = scale
    points = [
        (cx - int(90 * s), cy + int(50 * s)),
        (cx - int(100 * s), cy - int(30 * s)),
        (cx - int(40 * s), cy + int(10 * s)),
        (cx, cy - int(60 * s)),
        (cx + int(40 * s), cy + int(10 * s)),
        (cx + int(100 * s), cy - int(30 * s)),
        (cx + int(90 * s), cy + int(50 * s)),
    ]
    draw.polygon(points, fill=color)
    # 土台
    draw.rounded_rectangle(
        (cx - int(90 * s), cy + int(52 * s), cx + int(90 * s), cy + int(72 * s)),
        radius=int(6 * s), fill=color
    )
    # 宝石
    gem_r = int(10 * s)
    for dx_s in [-60, 0, 60]:
        dx = int(dx_s * s)
        gy = cy - int(20 * s)
        draw.ellipse((cx + dx - gem_r, gy - gem_r, cx + dx + gem_r, gy + gem_r), fill=WHITE)
    # 頂点の星
    star_y = cy - int(65 * s)
    sr = int(8 * s)
    draw.ellipse((cx - sr, star_y - sr, cx + sr, star_y + sr), fill=WHITE)


def draw_icon_chat_big(draw, cx, cy, color, scale=1.0):
    """大きな吹き出しアイコン"""
    s = scale
    # メイン吹き出し
    bx0 = cx - int(90 * s)
    by0 = cy - int(55 * s)
    bx1 = cx + int(90 * s)
    by1 = cy + int(40 * s)
    draw.rounded_rectangle((bx0, by0, bx1, by1), radius=int(25 * s), fill=color)
    # しっぽ
    draw.polygon([
        (cx - int(30 * s), by1 - int(5 * s)),
        (cx - int(55 * s), cy + int(75 * s)),
        (cx + int(5 * s), by1 - int(5 * s))
    ], fill=color)
    # ドット3つ（会話中）
    dot_r = int(9 * s)
    dot_y = cy - int(8 * s)
    for dx_s in [-35, 0, 35]:
        dx = int(dx_s * s)
        draw.ellipse((cx + dx - dot_r, dot_y - dot_r, cx + dx + dot_r, dot_y + dot_r), fill=WHITE)


def draw_icon_share_big(draw, cx, cy, color, scale=1.0):
    """大きなシェアアイコン（人+矢印）"""
    s = scale
    # メインの人
    head_r = int(28 * s)
    head_cy = cy - int(30 * s)
    draw.ellipse((cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r), fill=color)
    body_w = int(50 * s)
    body_top = cy + int(5 * s)
    body_bot = cy + int(60 * s)
    draw.rounded_rectangle(
        (cx - body_w, body_top, cx + body_w, body_bot),
        radius=int(25 * s), fill=color
    )
    # 右上に共有矢印
    ax = cx + int(65 * s)
    ay = cy - int(45 * s)
    arrow_len = int(40 * s)
    arrow_head = int(18 * s)
    # 矢印の軸（斜め右上）
    draw.line(
        [(ax, ay + arrow_len), (ax + arrow_len, ay)],
        fill=WHITE, width=int(6 * s)
    )
    # 矢印の先端
    draw.polygon([
        (ax + arrow_len + int(5 * s), ay - int(5 * s)),
        (ax + arrow_len - arrow_head, ay - int(2 * s)),
        (ax + arrow_len - int(2 * s), ay + arrow_head)
    ], fill=WHITE)
    # プラスマーク
    px = cx + int(80 * s)
    py = cy + int(25 * s)
    pw = int(5 * s)
    ph = int(18 * s)
    draw.rectangle((px - pw, py - ph, px + pw, py + ph), fill=WHITE)
    draw.rectangle((px - ph, py - pw, px + ph, py + pw), fill=WHITE)


def draw_accent_line(draw, x0, y0, x1, y1, color, width=3):
    """フェード付き仕切り線"""
    is_vertical = (x0 == x1)
    length = (y1 - y0) if is_vertical else (x1 - x0)
    mid = length // 2

    for i in range(length):
        dist = abs(i - mid) / max(mid, 1)
        alpha = max(0, 1 - dist ** 0.7)
        c = tuple(int(color[j] * alpha + BG_DARK[j] * (1 - alpha)) for j in range(3))
        if is_vertical:
            draw.line([(x0 - width // 2, y0 + i), (x0 + width // 2, y0 + i)], fill=c)
        else:
            draw.line([(x0 + i, y0 - width // 2), (x0 + i, y0 + width // 2)], fill=c)


def main():
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    gap = 8  # セル間の隙間

    cells = [
        {
            "bounds": (0, 0, HALF_W - gap // 2, HALF_H - gap // 2),
            "bg_top": (22, 38, 52), "bg_bottom": (18, 26, 36),
            "icon_func": draw_icon_chart_big, "icon_color": ACCENT_TEAL,
            "title": "今日の美容トレンド",
            "subtitle": "ECセール・成分比較・検索トレンド",
            "glow_color": ACCENT_TEAL,
        },
        {
            "bounds": (HALF_W + gap // 2, 0, W, HALF_H - gap // 2),
            "bg_top": (42, 22, 38), "bg_bottom": (30, 18, 26),
            "icon_func": draw_icon_crown_big, "icon_color": ACCENT_PINK,
            "title": "@cosme ランキング",
            "subtitle": "総合ランキングをチェック",
            "glow_color": ACCENT_PINK,
        },
        {
            "bounds": (0, HALF_H + gap // 2, HALF_W - gap // 2, H),
            "bg_top": (36, 30, 20), "bg_bottom": (24, 22, 16),
            "icon_func": draw_icon_chat_big, "icon_color": ACCENT_AMBER,
            "title": "感想・要望",
            "subtitle": "サービス改善にご協力ください",
            "glow_color": ACCENT_AMBER,
        },
        {
            "bounds": (HALF_W + gap // 2, HALF_H + gap // 2, W, H),
            "bg_top": (22, 30, 50), "bg_bottom": (16, 22, 36),
            "icon_func": draw_icon_share_big, "icon_color": ACCENT_BLUE,
            "title": "友達に紹介",
            "subtitle": "コスメバズをシェア",
            "glow_color": ACCENT_BLUE,
        },
    ]

    font_title = load_font(FONT_HEAVY, 72)
    font_sub = load_font(FONT_REGULAR, 36)

    for cell in cells:
        x0, y0, x1, y1 = cell["bounds"]
        cx = (x0 + x1) // 2
        cy = (y0 + y1) // 2
        cell_w = x1 - x0
        cell_h = y1 - y0

        # グラデーション背景
        draw_gradient_rect(img, (x0, y0, x1, y1), cell["bg_top"], cell["bg_bottom"])

        # 大きなグロー
        glow_cy = cy - int(cell_h * 0.08)
        img = draw_glow(img, cx, glow_cy, int(cell_w * 0.4), cell["glow_color"], intensity=0.18)
        draw = ImageDraw.Draw(img)

        # アイコン（大きく、セル上部寄り）
        icon_cy = cy - int(cell_h * 0.15)
        cell["icon_func"](draw, cx, icon_cy, cell["icon_color"], scale=2.2)

        # タイトル（大きくセル下部寄り）
        title_y = cy + int(cell_h * 0.20)
        bbox = draw.textbbox((0, 0), cell["title"], font=font_title)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, title_y), cell["title"], fill=WHITE, font=font_title)

        # サブタイトル
        sub_y = title_y + 85
        bbox2 = draw.textbbox((0, 0), cell["subtitle"], font=font_sub)
        sw = bbox2[2] - bbox2[0]
        draw.text((cx - sw // 2, sub_y), cell["subtitle"], fill=GRAY, font=font_sub)

    # 仕切り線
    draw_accent_line(draw, HALF_W, 30, HALF_W, H - 30, ACCENT_ROSE, width=3)
    draw_accent_line(draw, 30, HALF_H, W - 30, HALF_H, ACCENT_ROSE, width=3)

    # 中央装飾
    dot_r = 8
    draw.ellipse(
        (HALF_W - dot_r, HALF_H - dot_r, HALF_W + dot_r, HALF_H + dot_r),
        fill=ACCENT_ROSE
    )

    out = "/Users/nagashimataku/cosmebuzz-site/richmenu.png"
    img.save(out, "PNG", optimize=True)
    print(f"✅ {out} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
