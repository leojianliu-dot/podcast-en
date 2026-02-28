#!/usr/bin/env python3
"""
Generate a podcast cover image (3000x3000 PNG).

Apple Podcasts requires minimum 1400x1400, recommends 3000x3000.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Output
OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cover.png")
SIZE = 3000

# Colors
BG_DARK = (15, 23, 42)        # Slate 900
ACCENT = (59, 130, 246)        # Blue 500
ACCENT_LIGHT = (96, 165, 250)  # Blue 400
WHITE = (255, 255, 255)
GRAY = (148, 163, 184)         # Slate 400
SUBTLE = (30, 41, 59)          # Slate 800


def draw_rounded_rect(draw, xy, radius, fill):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.pieslice([x0, y0, x0 + 2 * radius, y0 + 2 * radius], 180, 270, fill=fill)
    draw.pieslice([x1 - 2 * radius, y0, x1, y0 + 2 * radius], 270, 360, fill=fill)
    draw.pieslice([x0, y1 - 2 * radius, x0 + 2 * radius, y1], 90, 180, fill=fill)
    draw.pieslice([x1 - 2 * radius, y1 - 2 * radius, x1, y1], 0, 90, fill=fill)


def main():
    img = Image.new("RGB", (SIZE, SIZE), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Background gradient effect — subtle horizontal bars
    for i in range(0, SIZE, 6):
        opacity = int(8 + 4 * ((i % 60) / 60))
        draw.line([(0, i), (SIZE, i)], fill=(opacity, opacity + 2, opacity + 8))

    # Decorative top accent bar
    draw.rectangle([0, 0, SIZE, 18], fill=ACCENT)

    # Globe / signal icon area (abstract radio waves)
    cx, cy = SIZE // 2, 950
    for r in range(6):
        radius = 200 + r * 120
        alpha = max(30, 180 - r * 28)
        color = (ACCENT[0], ACCENT[1], ACCENT[2])
        thickness = max(4, 14 - r * 2)
        # Draw arc segments
        draw.arc(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            200, 340,
            fill=(*color,),
            width=thickness,
        )
        draw.arc(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            20, 160,
            fill=(*color,),
            width=thickness,
        )

    # Center dot
    dot_r = 60
    draw_rounded_rect(draw, [cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], dot_r, ACCENT)

    # Inner ring
    inner_r = 120
    draw.ellipse(
        [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
        outline=ACCENT_LIGHT, width=10,
    )

    # Title: "DAILY NEWS"
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 280)
    except OSError:
        font_title = ImageFont.truetype("arial.ttf", 280)

    title1 = "DAILY"
    title2 = "NEWS"
    bbox1 = draw.textbbox((0, 0), title1, font=font_title)
    bbox2 = draw.textbbox((0, 0), title2, font=font_title)
    w1 = bbox1[2] - bbox1[0]
    w2 = bbox2[2] - bbox2[0]

    y_title = 1520
    draw.text(((SIZE - w1) // 2, y_title), title1, fill=WHITE, font=font_title)
    draw.text(((SIZE - w2) // 2, y_title + 300), title2, fill=ACCENT_LIGHT, font=font_title)

    # Subtitle: "BRIEFING"
    try:
        font_sub = ImageFont.truetype("arial.ttf", 160)
    except OSError:
        font_sub = ImageFont.truetype("arial.ttf", 160)

    sub = "BRIEFING"
    bbox_sub = draw.textbbox((0, 0), sub, font=font_sub)
    w_sub = bbox_sub[2] - bbox_sub[0]
    draw.text(((SIZE - w_sub) // 2, y_title + 630), sub, fill=GRAY, font=font_sub)

    # Divider line
    line_y = y_title + 850
    line_w = 800
    draw.line(
        [(SIZE // 2 - line_w // 2, line_y), (SIZE // 2 + line_w // 2, line_y)],
        fill=ACCENT, width=6,
    )

    # Tagline
    try:
        font_tag = ImageFont.truetype("arial.ttf", 90)
    except OSError:
        font_tag = ImageFont.truetype("arial.ttf", 90)

    tag = "AI-Generated News Podcast"
    bbox_tag = draw.textbbox((0, 0), tag, font=font_tag)
    w_tag = bbox_tag[2] - bbox_tag[0]
    draw.text(((SIZE - w_tag) // 2, line_y + 50), tag, fill=GRAY, font=font_tag)

    # Bottom accent bar
    draw.rectangle([0, SIZE - 18, SIZE, SIZE], fill=ACCENT)

    # Save
    img.save(OUTPUT, "PNG", optimize=True)
    file_size = os.path.getsize(OUTPUT) / 1024
    print(f"Cover image saved: {OUTPUT}")
    print(f"Size: {SIZE}x{SIZE}px, {file_size:.0f} KB")


if __name__ == "__main__":
    main()
