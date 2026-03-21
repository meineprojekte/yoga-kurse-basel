#!/usr/bin/env python3
"""Generate OG image (1200x630 PNG) for social media sharing."""

from PIL import Image, ImageDraw, ImageFont
import os

WIDTH, HEIGHT = 1200, 630
OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'img', 'og-image.png')

# Colors
PURPLE = (107, 91, 149)
GOLD = (212, 163, 115)
WHITE = (255, 255, 255)
LIGHT_WHITE = (255, 255, 255, 200)

img = Image.new('RGBA', (WIDTH, HEIGHT))
draw = ImageDraw.Draw(img)

# Gradient background (purple to gold, diagonal)
for y in range(HEIGHT):
    for x in range(WIDTH):
        ratio = (x / WIDTH * 0.6 + y / HEIGHT * 0.4)
        r = int(PURPLE[0] + (GOLD[0] - PURPLE[0]) * ratio)
        g = int(PURPLE[1] + (GOLD[1] - PURPLE[1]) * ratio)
        b = int(PURPLE[2] + (GOLD[2] - PURPLE[2]) * ratio)
        img.putpixel((x, y), (r, g, b, 255))

# Try to load nice fonts, fallback to default
def get_font(size, bold=False):
    font_paths = [
        # macOS
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/SFNSDisplay.ttf',
        '/Library/Fonts/Arial.ttf',
        # Linux
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]
    if bold:
        font_paths = [
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        ] + font_paths

    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

# Yoga emoji/icon — draw a simple meditation figure
def draw_meditation_figure(draw, cx, cy, scale=1.0):
    s = scale
    # Head
    draw.ellipse([cx-15*s, cy-55*s, cx+15*s, cy-25*s], fill=WHITE)
    # Body
    draw.polygon([
        (cx, cy-25*s),
        (cx-8*s, cy+15*s),
        (cx+8*s, cy+15*s)
    ], fill=WHITE)
    # Left arm
    draw.line([(cx-5*s, cy-10*s), (cx-35*s, cy+5*s)], fill=WHITE, width=int(4*s))
    # Right arm
    draw.line([(cx+5*s, cy-10*s), (cx+35*s, cy+5*s)], fill=WHITE, width=int(4*s))
    # Legs (lotus position)
    draw.arc([cx-30*s, cy+5*s, cx+5*s, cy+30*s], 0, 180, fill=WHITE, width=int(4*s))
    draw.arc([cx-5*s, cy+5*s, cx+30*s, cy+30*s], 0, 180, fill=WHITE, width=int(4*s))

# Draw decorative circle behind figure
cx, cy = WIDTH // 2, 200
draw.ellipse([cx-70, cy-70, cx+70, cy+70], outline=(255, 255, 255, 100), width=3)
draw_meditation_figure(draw, cx, cy, scale=1.5)

# Title
font_title = get_font(72, bold=True)
font_sub = get_font(32)
font_stats = get_font(28)

title = "Yoga Schweiz"
bbox = draw.textbbox((0, 0), title, font=font_title)
tw = bbox[2] - bbox[0]
draw.text(((WIDTH - tw) // 2, 300), title, fill=WHITE, font=font_title)

# Subtitle
sub = "Alle Yoga-Studios der Schweiz auf einen Blick"
bbox = draw.textbbox((0, 0), sub, font=font_sub)
sw = bbox[2] - bbox[0]
draw.text(((WIDTH - sw) // 2, 390), sub, fill=WHITE, font=font_sub)

# Stats line
stats = "266 Studios  ·  26 Kantone  ·  Täglich aktualisiert"
bbox = draw.textbbox((0, 0), stats, font=font_stats)
stw = bbox[2] - bbox[0]

# Stats background pill
pill_y = 455
pill_h = 50
pill_x = (WIDTH - stw) // 2 - 25
pill_w = stw + 50
draw.rounded_rectangle(
    [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
    radius=25,
    fill=(255, 255, 255, 40)
)
draw.text(((WIDTH - stw) // 2, pill_y + 8), stats, fill=WHITE, font=font_stats)

# Bottom bar
draw.rectangle([0, HEIGHT - 60, WIDTH, HEIGHT], fill=(0, 0, 0, 60))
font_url = get_font(22)
url = "yoga-schweiz.ch"
bbox = draw.textbbox((0, 0), url, font=font_url)
uw = bbox[2] - bbox[0]
draw.text(((WIDTH - uw) // 2, HEIGHT - 45), url, fill=WHITE, font=font_url)

# Save
img = img.convert('RGB')
img.save(OUTPUT, 'PNG', quality=95)
print(f"OG image saved: {OUTPUT}")
print(f"Size: {os.path.getsize(OUTPUT) // 1024} KB")
