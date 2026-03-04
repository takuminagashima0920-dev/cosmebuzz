#!/usr/bin/env python3
"""Generate LINE Rich Menu image for CosmeBuzz (コスメバズ)."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import math

# --- Canvas ---
W, H = 2500, 1686
BG = "#1C1C24"
CARD_BG = "#282830"
ACCENT = "#DC8C9E"  # rose gold divider
WHITE = "#FFFFFF"
GRAY = "#AAAAAA"
DIVIDER_W = 3

# --- Fonts ---
FONT_BOLD_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_REGULAR_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
FONT_HEAVY_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"

def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

font_main = load_font(FONT_BOLD_PATH, 56)
font_sub = load_font(FONT_REGULAR_PATH, 32)
font_icon_text = load_font(FONT_HEAVY_PATH, 44)

# --- Button definitions ---
buttons = [
    {
        "main": "今日の美容トレンド",
        "sub": "ECセール・成分比較・検索トレンド",
        "accent": "#4ECDC4",
        "icon_symbol": "chart",  # geometric placeholder
        "col": 0, "row": 0,
    },
    {
        "main": "@cosme ランキング",
        "sub": "総合ランキングをチェック",
        "accent": "#E1306C",
        "icon_symbol": "crown",
        "col": 1, "row": 0,
    },
    {
        "main": "感想・要望",
        "sub": "サービス改善にご協力ください",
        "accent": "#FFB800",
        "icon_symbol": "message",
        "col": 0, "row": 1,
    },
    {
        "main": "友達に紹介",
        "sub": "コスメバズをシェア",
        "accent": "#1DA1F2",
        "icon_symbol": "share",
        "col": 1, "row": 1,
    },
]

# --- Create canvas ---
img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# --- Dimensions ---
col_w = W // 2   # 1250
row_h = H // 2   # 843
pad = 30          # padding inside each cell for the card
card_radius = 24

def draw_rounded_rect(draw_obj, xy, radius, fill):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    r = radius
    # Fill main body
    draw_obj.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    draw_obj.rectangle([x0, y0 + r, x1, y1 - r], fill=fill)
    # Corners
    draw_obj.pieslice([x0, y0, x0 + 2*r, y0 + 2*r], 180, 270, fill=fill)
    draw_obj.pieslice([x1 - 2*r, y0, x1, y0 + 2*r], 270, 360, fill=fill)
    draw_obj.pieslice([x0, y1 - 2*r, x0 + 2*r, y1], 90, 180, fill=fill)
    draw_obj.pieslice([x1 - 2*r, y1 - 2*r, x1, y1], 0, 90, fill=fill)


def draw_icon(draw_obj, cx, cy, radius, accent_color, symbol):
    """Draw a colored circle with a simple geometric icon inside."""
    # Outer circle (accent color)
    draw_obj.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=accent_color
    )

    # Inner icon (white geometric shapes)
    ir = int(radius * 0.5)  # icon inner size

    if symbol == "chart":
        # Bar chart icon: 3 bars of different heights
        bar_w = int(ir * 0.4)
        gap = int(ir * 0.15)
        # bar heights
        bars = [ir * 0.5, ir * 0.9, ir * 0.65]
        total_w = 3 * bar_w + 2 * gap
        start_x = cx - total_w // 2
        base_y = cy + ir // 2
        for i, h in enumerate(bars):
            bx = start_x + i * (bar_w + gap)
            draw_obj.rounded_rectangle(
                [bx, base_y - int(h), bx + bar_w, base_y],
                radius=3,
                fill="white"
            )
        # Small trend line on top
        pts = [
            (start_x + bar_w // 2, base_y - int(bars[0]) - 6),
            (start_x + bar_w + gap + bar_w // 2, base_y - int(bars[1]) - 6),
            (start_x + 2 * (bar_w + gap) + bar_w // 2, base_y - int(bars[2]) - 6),
        ]
        draw_obj.line(pts, fill="white", width=3)

    elif symbol == "crown":
        # Crown icon
        cr = ir
        top_y = cy - int(cr * 0.5)
        bot_y = cy + int(cr * 0.45)
        left_x = cx - int(cr * 0.6)
        right_x = cx + int(cr * 0.6)
        mid_x = cx
        # Crown shape (5-point polygon)
        points = [
            (left_x, bot_y),
            (left_x, top_y + int(cr * 0.3)),
            (left_x + int(cr * 0.3), top_y + int(cr * 0.55)),
            (mid_x, top_y),
            (right_x - int(cr * 0.3), top_y + int(cr * 0.55)),
            (right_x, top_y + int(cr * 0.3)),
            (right_x, bot_y),
        ]
        draw_obj.polygon(points, fill="white")
        # Small circles on crown tips
        for px, py in [(left_x, top_y + int(cr * 0.3)),
                       (mid_x, top_y),
                       (right_x, top_y + int(cr * 0.3))]:
            draw_obj.ellipse([px - 4, py - 4, px + 4, py + 4], fill="white")
        # Base band
        draw_obj.rectangle(
            [left_x + 2, bot_y - 8, right_x - 2, bot_y],
            fill=accent_color
        )

    elif symbol == "message":
        # Chat bubble icon
        bw = int(ir * 1.2)
        bh = int(ir * 0.85)
        bx0 = cx - bw // 2
        by0 = cy - bh // 2 - 4
        bx1 = bx0 + bw
        by1 = by0 + bh
        draw_obj.rounded_rectangle([bx0, by0, bx1, by1], radius=10, fill="white")
        # Tail triangle
        tail_pts = [
            (cx - int(ir * 0.15), by1 - 2),
            (cx - int(ir * 0.35), by1 + int(ir * 0.35)),
            (cx + int(ir * 0.15), by1 - 2),
        ]
        draw_obj.polygon(tail_pts, fill="white")
        # Three dots inside bubble
        dot_r = 4
        dot_y = (by0 + by1) // 2
        for dx in [-int(ir * 0.3), 0, int(ir * 0.3)]:
            draw_obj.ellipse(
                [cx + dx - dot_r, dot_y - dot_r, cx + dx + dot_r, dot_y + dot_r],
                fill=accent_color
            )

    elif symbol == "share":
        # People/share icon: two person silhouettes + arrow
        # Person 1 (left)
        p1x = cx - int(ir * 0.3)
        p1y = cy - int(ir * 0.1)
        head_r = int(ir * 0.22)
        draw_obj.ellipse(
            [p1x - head_r, p1y - head_r - int(ir * 0.25),
             p1x + head_r, p1y + head_r - int(ir * 0.25)],
            fill="white"
        )
        # Body
        body_w = int(ir * 0.35)
        draw_obj.pieslice(
            [p1x - body_w, p1y + int(ir * 0.05),
             p1x + body_w, p1y + int(ir * 0.7)],
            180, 360, fill="white"
        )

        # Person 2 (right, slightly behind)
        p2x = cx + int(ir * 0.3)
        p2y = cy - int(ir * 0.1)
        draw_obj.ellipse(
            [p2x - head_r, p2y - head_r - int(ir * 0.25),
             p2x + head_r, p2y + head_r - int(ir * 0.25)],
            fill="white"
        )
        draw_obj.pieslice(
            [p2x - body_w, p2y + int(ir * 0.05),
             p2x + body_w, p2y + int(ir * 0.7)],
            180, 360, fill="white"
        )

        # Small share arrow at bottom right
        ax = cx + int(ir * 0.55)
        ay = cy + int(ir * 0.35)
        arrow_size = int(ir * 0.25)
        draw_obj.polygon([
            (ax, ay - arrow_size),
            (ax + arrow_size, ay),
            (ax, ay + arrow_size),
        ], fill="white")
        draw_obj.rectangle(
            [ax - int(ir * 0.3), ay - 3, ax, ay + 3],
            fill="white"
        )


def text_center_x(draw_obj, text, font, area_cx):
    """Get x position to center text at area_cx."""
    bbox = draw_obj.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    return area_cx - tw // 2


# --- Draw each button ---
for btn in buttons:
    col, row = btn["col"], btn["row"]
    # Cell bounding box
    cell_x0 = col * col_w
    cell_y0 = row * row_h
    cell_x1 = cell_x0 + col_w
    cell_y1 = cell_y0 + row_h

    # Card area (with padding)
    card_x0 = cell_x0 + pad
    card_y0 = cell_y0 + pad
    card_x1 = cell_x1 - pad
    card_y1 = cell_y1 - pad

    # Draw card background
    draw_rounded_rect(draw, (card_x0, card_y0, card_x1, card_y1), card_radius, CARD_BG)

    # Center of the card
    card_cx = (card_x0 + card_x1) // 2
    card_cy = (card_y0 + card_y1) // 2

    # --- Icon circle ---
    icon_radius = 52
    icon_cy = card_cy - 130
    draw_icon(draw, card_cx, icon_cy, icon_radius, btn["accent"], btn["icon_symbol"])

    # --- Main text ---
    main_y = card_cy - 30
    main_x = text_center_x(draw, btn["main"], font_main, card_cx)
    draw.text((main_x, main_y), btn["main"], fill=WHITE, font=font_main)

    # --- Subtitle ---
    sub_y = main_y + 80
    sub_x = text_center_x(draw, btn["sub"], font_sub, card_cx)
    draw.text((sub_x, sub_y), btn["sub"], fill=GRAY, font=font_sub)

    # --- Subtle bottom accent line ---
    line_w = 80
    line_y = sub_y + 60
    draw.rounded_rectangle(
        [card_cx - line_w, line_y, card_cx + line_w, line_y + 4],
        radius=2,
        fill=btn["accent"]
    )

# --- Rose gold divider lines ---
# Vertical center line
draw.rectangle(
    [W // 2 - DIVIDER_W // 2, pad, W // 2 + DIVIDER_W // 2 + 1, H - pad],
    fill=ACCENT
)
# Horizontal center line
draw.rectangle(
    [pad, H // 2 - DIVIDER_W // 2, W - pad, H // 2 + DIVIDER_W // 2 + 1],
    fill=ACCENT
)

# --- Small corner decorations (rose gold dots at intersection) ---
cx, cy = W // 2, H // 2
dot_r = 8
draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=ACCENT)

# --- Save ---
output_path = "/Users/nagashimataku/cosmebuzz-site/richmenu.png"
img.save(output_path, "PNG")
print(f"Rich menu image saved to: {output_path}")
print(f"Size: {img.size}")
