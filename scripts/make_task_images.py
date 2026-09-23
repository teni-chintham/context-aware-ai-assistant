"""Generates the 10 deterministic test images for the multimodal tasks in data/eval/task_bench.json."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "data" / "eval" / "images"
OUT.mkdir(parents=True, exist_ok=True)
W = H = 384


def font(size):
    for f in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/Library/Fonts/Arial.ttf"]:
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            continue
    return ImageFont.load_default()


def canvas(bg="white"):
    im = Image.new("RGB", (W, H), bg)
    return im, ImageDraw.Draw(im)


def centered_text(d, text, size, fill="black"):
    f = font(size)
    box = d.textbbox((0, 0), text, font=f)
    d.text(((W - (box[2] - box[0])) / 2 - box[0], (H - (box[3] - box[1])) / 2 - box[1]), text, font=f, fill=fill)


def save(im, name):
    im.save(OUT / name)


im, d = canvas(); d.ellipse((92, 92, 292, 292), fill=(220, 30, 30)); save(im, "mm-01.png")
im, d = canvas(); d.rectangle((102, 102, 282, 282), fill=(30, 70, 210)); save(im, "mm-02.png")
im, d = canvas(); centered_text(d, "42", 180); save(im, "mm-03.png")
im, d = canvas()
for x in (82, 192, 302):
    d.ellipse((x - 35, 157, x + 35, 227), fill=(20, 150, 50))
save(im, "mm-04.png")
im, d = canvas(); centered_text(d, "CAT", 140); save(im, "mm-05.png")
im, d = canvas(); d.polygon([(192, 72), (322, 302), (62, 302)], fill=(235, 200, 20)); save(im, "mm-06.png")
im, d = canvas()
d.line((50, 330, 340, 330), fill="black", width=3)
d.rectangle((90, 70, 170, 330), fill=(60, 100, 200)); d.rectangle((220, 230, 300, 330), fill=(60, 100, 200))
f = font(40); d.text((115, 335), "A", font=f, fill="black"); d.text((245, 335), "B", font=f, fill="black")
save(im, "mm-07.png")
im, d = canvas("black"); centered_text(d, "STOP", 130, fill="white"); save(im, "mm-08.png")
im, d = canvas(); d.ellipse((40, 122, 180, 262), fill=(220, 30, 30)); d.ellipse((204, 122, 344, 262), fill=(30, 70, 210))
save(im, "mm-09.png")
im, d = canvas(); centered_text(d, "7", 280); save(im, "mm-10.png")
print(f"wrote 10 images to {OUT}")
