from docx import Document
from PIL import Image, ImageDraw, ImageFont
import os

DOCX_PATH = r"C:\Users\user\Documents\pa-finance.2\Audit\docs\Оценка преподавателя по уроку №7.docx"
OUTPUT_PATH = r"C:\Users\user\Documents\pa-finance.2\Audit\docs\Оценка преподавателя по уроку №7.png"

BG_COLOR = (255, 255, 255)
TEXT_COLOR = (30, 30, 30)
ACCENT_COLOR = (0, 102, 204)
SEPARATOR_COLOR = (200, 200, 200)
PADDING = 60
LINE_HEIGHT = 26
FONT_SIZE = 14
TITLE_SIZE = 20
SUBTITLE_SIZE = 12

def get_font(size):
    try:
        return ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", size)
    except:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

doc = Document(DOCX_PATH)

max_width = 0
all_lines = []
font = get_font(FONT_SIZE)
title_font = get_font(TITLE_SIZE)
sub_font = get_font(SUBTITLE_SIZE)

for p in doc.paragraphs:
    text = p.text.strip()
    if not text:
        all_lines.append(("", font))
        continue
    style_name = p.style.name if p.style else ""
    if "Heading" in style_name or "Заголовок" in style_name:
        all_lines.append((text, get_font(18)))
    elif "Title" in style_name:
        all_lines.append((text, title_font))
    elif "Subtitle" in style_name:
        all_lines.append((text, sub_font))
    else:
        all_lines.append((text, font))

# Calculate dimensions
draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
content_width = 700
y = PADDING
for text, f in all_lines:
    if not text:
        y += LINE_HEIGHT
        continue
    lines = wrap_text(text, f, content_width, draw)
    line_height = LINE_HEIGHT + 4
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=f)
        w = bbox[2] - bbox[0]
        if w > max_width:
            max_width = w
        y += line_height

total_width = max_width + PADDING * 2 + 40
total_height = y + PADDING
total_width = max(total_width, 800)
total_height = max(total_height, 600)

img = Image.new("RGB", (total_width, total_height), BG_COLOR)
draw = ImageDraw.Draw(img)

y = PADDING
x = PADDING + 20
content_width = total_width - PADDING * 2 - 40

for text, f in all_lines:
    if not text:
        y += LINE_HEIGHT
        continue
    lines = wrap_text(text, f, content_width, draw)
    line_height = LINE_HEIGHT + 6
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=f)
        draw.text((x, y), line, font=f, fill=TEXT_COLOR)
        y += line_height

img.save(OUTPUT_PATH, "PNG")
print(f"Скрин сохранён: {OUTPUT_PATH}")
print(f"Размер: {total_width}x{total_height}")
