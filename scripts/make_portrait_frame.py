import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 480
CX = CY = SIZE // 2
PHOTO_R = 165
GLOW_R = 190

portrait = Image.open("assets/portrait.png").convert("RGB")
w, h = portrait.size
side = min(w, h)
left = (w - side) // 2
crop = portrait.crop((left, 0, left + side, side)).resize(
    (PHOTO_R * 2, PHOTO_R * 2), Image.LANCZOS
)

circle_mask = Image.new("L", (PHOTO_R * 2, PHOTO_R * 2), 0)
ImageDraw.Draw(circle_mask).ellipse((0, 0, PHOTO_R * 2 - 1, PHOTO_R * 2 - 1), fill=255)
photo_circular = Image.new("RGBA", (PHOTO_R * 2, PHOTO_R * 2), (0, 0, 0, 0))
photo_circular.paste(crop, (0, 0), circle_mask)

photo_full_mask = Image.new("L", (SIZE, SIZE), 0)
ImageDraw.Draw(photo_full_mask).ellipse(
    (CX - PHOTO_R, CY - PHOTO_R, CX + PHOTO_R, CY + PHOTO_R), fill=255
)

font = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 14)

rng = random.Random(11)

CELL = 15
COLS = (PHOTO_R * 2) // CELL
ROWS = (PHOTO_R * 2) // CELL
GRID_LEFT = CX - (COLS * CELL) // 2
GRID_TOP = CY - (ROWS * CELL) // 2
TRAIL = 7

col_phase = [rng.randint(0, ROWS + TRAIL) for _ in range(COLS)]
col_speed = [rng.choice([2, 3]) for _ in range(COLS)]
col_chars = [[rng.choice("01") for _ in range(ROWS)] for _ in range(COLS)]

DUR_MS = 95

# reveal progress per frame: sweep down 0->1, then hold fully revealed.
# No recover phase - the animation plays once and rests on the clear photo.
REVEAL_DOWN = 18
HOLD = 6
N_FRAMES = REVEAL_DOWN + HOLD


def reveal_progress(i):
    if i < REVEAL_DOWN:
        return i / (REVEAL_DOWN - 1)
    return 1.0


frames = []
for i in range(N_FRAMES):
    progress = reveal_progress(i)
    reveal_y = (CY - PHOTO_R) + progress * (PHOTO_R * 2)

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # soft pulsing red halo around the whole frame (drawn outside the
    # photo circle, so it must NOT be clipped away with the inner layers)
    glow_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    pulse = 0.55 + 0.45 * math.sin(2 * math.pi * i / N_FRAMES)
    ImageDraw.Draw(glow_layer).ellipse(
        (CX - GLOW_R, CY - GLOW_R, CX + GLOW_R, CY + GLOW_R),
        outline=(232, 20, 44, int(70 * pulse)),
        width=10,
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(8))
    canvas.alpha_composite(glow_layer)

    inner = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # dark backing so not-yet-revealed area reads as solid
    back = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(back).ellipse(
        (CX - PHOTO_R - 3, CY - PHOTO_R - 3, CX + PHOTO_R + 3, CY + PHOTO_R + 3),
        fill=(8, 5, 5, 255),
    )
    inner.alpha_composite(back)

    # revealed portion of the photo: only rows above reveal_y
    revealed = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    revealed.paste(photo_circular, (CX - PHOTO_R, CY - PHOTO_R), photo_circular)
    reveal_clip = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(reveal_clip).rectangle(
        (0, 0, SIZE, reveal_y), fill=255
    )
    revealed.putalpha(
        Image.composite(revealed.getchannel("A"), Image.new("L", (SIZE, SIZE), 0), reveal_clip)
    )
    inner.alpha_composite(revealed)

    # falling binary rain covering the not-yet-revealed area
    rain_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(rain_layer)
    for c in range(COLS):
        head = (i * col_speed[c] + col_phase[c]) % (ROWS + TRAIL) - TRAIL
        x = GRID_LEFT + c * CELL + CELL // 2
        for r in range(ROWS):
            y = GRID_TOP + r * CELL + CELL // 2
            if y < reveal_y - CELL:
                continue  # already revealed, no rain needed here
            d = head - r
            if 0 <= d < TRAIL:
                t = d / TRAIL
                if d == 0:
                    color = (255, 235, 235, 255)
                else:
                    a = int(230 * (1 - t))
                    color = (235, 40, 60, a)
                ch = col_chars[c][r]
                if d <= 1 and rng.random() < 0.3:
                    ch = rng.choice("01")
                    col_chars[c][r] = ch
                rdraw.text((x, y), ch, font=font, fill=color, anchor="mm")
            elif rng.random() < 0.06:
                rdraw.text(
                    (x, y), col_chars[c][r], font=font, fill=(180, 30, 45, 55), anchor="mm"
                )
    rain_mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(rain_mask).rectangle((0, reveal_y - CELL, SIZE, SIZE), fill=255)
    rain_layer.putalpha(
        Image.composite(rain_layer.getchannel("A"), Image.new("L", (SIZE, SIZE), 0), rain_mask)
    )
    inner.alpha_composite(rain_layer)

    # bright scan front riding the reveal boundary
    if 0 < progress < 1:
        front = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        ImageDraw.Draw(front).rectangle(
            (CX - PHOTO_R, reveal_y - 4, CX + PHOTO_R, reveal_y + 4),
            fill=(255, 210, 210, 220),
        )
        front = front.filter(ImageFilter.GaussianBlur(3))
        inner.alpha_composite(front)

    # clip the inner (photo + rain) stack to the circle, then lay it over
    # the un-clipped outer glow, and finish with a crisp edge ring
    inner.putalpha(Image.composite(inner.getchannel("A"), Image.new("L", (SIZE, SIZE), 0), photo_full_mask))
    canvas.alpha_composite(inner)
    edge = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(edge).ellipse(
        (CX - PHOTO_R, CY - PHOTO_R, CX + PHOTO_R, CY + PHOTO_R),
        outline=(232, 20, 44, 170),
        width=2,
    )
    canvas.alpha_composite(edge)

    frames.append(canvas)

BG = (10, 7, 7)
gif_frames = []
for frame in frames:
    alpha = frame.split()[3]
    solid = Image.alpha_composite(Image.new("RGBA", frame.size, BG + (255,)), frame).convert("RGB")
    pal = solid.convert("P", palette=Image.ADAPTIVE, colors=255)
    transparent_mask = alpha.point(lambda a: 255 if a <= 20 else 0)
    pal.paste(255, transparent_mask)
    gif_frames.append(pal)

gif_frames[0].save(
    "assets/portrait-frame.gif",
    save_all=True,
    append_images=gif_frames[1:],
    duration=DUR_MS,
    disposal=2,
    transparency=255,
    optimize=False,
)

print("done")
