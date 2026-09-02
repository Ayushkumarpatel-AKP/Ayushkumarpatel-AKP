import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

SIZE = 480
CX = CY = SIZE // 2
PHOTO_R = 165
RING_R = 195
RING_R2 = 216
GLOW_R = 228

portrait = Image.open("assets/portrait.png").convert("RGB")
w, h = portrait.size
side = min(w, h)
left = (w - side) // 2
crop = portrait.crop((left, 0, left + side, side)).resize(
    (PHOTO_R * 2, PHOTO_R * 2), Image.LANCZOS
)

mask = Image.new("L", (PHOTO_R * 2, PHOTO_R * 2), 0)
ImageDraw.Draw(mask).ellipse((0, 0, PHOTO_R * 2 - 1, PHOTO_R * 2 - 1), fill=255)
photo_circular = Image.new("RGBA", (PHOTO_R * 2, PHOTO_R * 2), (0, 0, 0, 0))
photo_circular.paste(crop, (0, 0), mask)

photo_circle_mask_full = Image.new("L", (SIZE, SIZE), 0)
ImageDraw.Draw(photo_circle_mask_full).ellipse(
    (CX - PHOTO_R, CY - PHOTO_R, CX + PHOTO_R, CY + PHOTO_R), fill=255
)

font_outer = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 16)
font_inner = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 11)

N_FRAMES = 20
DUR_MS = 110

rng = random.Random(7)

N1 = 40  # outer digit ring
N2 = 64  # inner digit ring

digits1 = [rng.choice("01") for _ in range(N1)]
digits2 = [rng.choice("01") for _ in range(N2)]

frames = []
for i in range(N_FRAMES):
    angle1 = i * (360 / N_FRAMES)
    angle2 = -i * (360 / N_FRAMES) * 1.6

    for idx in range(N1):
        if rng.random() < 0.20:
            digits1[idx] = "1" if digits1[idx] == "0" else "0"
    for idx in range(N2):
        if rng.random() < 0.20:
            digits2[idx] = "1" if digits2[idx] == "0" else "0"

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # pulsing red halo
    glow_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_layer)
    pulse = 0.55 + 0.45 * math.sin(2 * math.pi * i / N_FRAMES)
    alpha = int(85 * pulse)
    gdraw.ellipse(
        (CX - GLOW_R, CY - GLOW_R, CX + GLOW_R, CY + GLOW_R),
        outline=(232, 20, 44, alpha),
        width=12,
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(9))
    canvas.alpha_composite(glow_layer)

    # inner denser digit ring - dim white/red flicker, counter-rotating
    ring2_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    r2draw = ImageDraw.Draw(ring2_layer)
    for idx in range(N2):
        theta = math.radians(angle2 + idx * (360 / N2))
        x = CX + RING_R * math.cos(theta)
        y = CY + RING_R * math.sin(theta)
        a = 55 + int(85 * abs(math.sin(math.radians(idx * 6 - i * 15))))
        col = (255, 255, 255, a) if digits2[idx] == "1" else (255, 90, 100, a)
        r2draw.text((x, y), digits2[idx], font=font_inner, fill=col, anchor="mm")
    canvas.alpha_composite(ring2_layer)

    # outer bright digit ring, clockwise
    ring1_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    r1draw = ImageDraw.Draw(ring1_layer)
    for idx in range(N1):
        theta = math.radians(angle1 + idx * (360 / N1))
        x = CX + RING_R2 * math.cos(theta)
        y = CY + RING_R2 * math.sin(theta)
        a = 150 + int(105 * abs(math.sin(math.radians(idx * 9 + i * 20))))
        col = (255, 70, 85, a) if digits1[idx] == "1" else (255, 200, 205, a)
        r1draw.text((x, y), digits1[idx], font=font_outer, fill=col, anchor="mm")
    canvas.alpha_composite(ring1_layer)

    # dark backing so the photo edge stays crisp against the digit rings
    back = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(back).ellipse(
        (CX - PHOTO_R - 4, CY - PHOTO_R - 4, CX + PHOTO_R + 4, CY + PHOTO_R + 4),
        fill=(10, 7, 7, 255),
    )
    canvas.alpha_composite(back)

    canvas.alpha_composite(photo_circular, (CX - PHOTO_R, CY - PHOTO_R))

    # scanline sweep across the face, clipped to the photo circle
    scan_y = (CY - PHOTO_R) + (2 * PHOTO_R) * (i / N_FRAMES)
    scan_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(scan_layer).rectangle(
        (CX - PHOTO_R, scan_y - 3, CX + PHOTO_R, scan_y + 3), fill=(255, 45, 65, 130)
    )
    scan_layer.putalpha(
        ImageChops.multiply(scan_layer.getchannel("A"), photo_circle_mask_full)
    )
    canvas.alpha_composite(scan_layer)

    # thin definition ring right at the photo edge
    edge = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(edge).ellipse(
        (CX - PHOTO_R, CY - PHOTO_R, CX + PHOTO_R, CY + PHOTO_R),
        outline=(232, 20, 44, 160),
        width=2,
    )
    canvas.alpha_composite(edge)

    frames.append(canvas.convert("RGBA"))

# GIF has no real alpha channel: composite onto the theme's dark backing
# color first, then threshold near-transparent pixels to a single
# transparent index so the circle still reads as cut out on any background.
BG = (10, 7, 7)
gif_frames = []
for frame in frames:
    alpha = frame.split()[3]
    solid = Image.alpha_composite(
        Image.new("RGBA", frame.size, BG + (255,)), frame
    ).convert("RGB")
    pal = solid.convert("P", palette=Image.ADAPTIVE, colors=255)
    transparent_mask = alpha.point(lambda a: 255 if a <= 20 else 0)
    pal.paste(255, transparent_mask)
    gif_frames.append(pal)

gif_frames[0].save(
    "assets/portrait-frame.gif",
    save_all=True,
    append_images=gif_frames[1:],
    duration=DUR_MS,
    loop=0,
    disposal=2,
    transparency=255,
    optimize=False,
)

print("done")
