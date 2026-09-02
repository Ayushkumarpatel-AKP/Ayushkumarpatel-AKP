import math
from PIL import Image, ImageDraw, ImageFilter

SIZE = 480
CX = CY = SIZE // 2
PHOTO_R = 165
RING_R = 190
GLOW_R = 210

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

N_FRAMES = 16
DUR_MS = 130

colors = [(232, 20, 44, 235), (255, 84, 112, 235), (122, 12, 22, 235)]

frames = []
for i in range(N_FRAMES):
    angle = i * (360 / N_FRAMES)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    glow_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_layer)
    pulse = 0.6 + 0.4 * math.sin(2 * math.pi * i / N_FRAMES)
    alpha = int(90 * pulse)
    gdraw.ellipse(
        (CX - GLOW_R, CY - GLOW_R, CX + GLOW_R, CY + GLOW_R),
        outline=(232, 20, 44, alpha),
        width=17,
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(11))
    canvas.alpha_composite(glow_layer)

    ring_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(ring_layer)
    n_dashes = 6
    dash_deg = 28
    gap_deg = (360 - n_dashes * dash_deg) / n_dashes
    for d in range(n_dashes):
        start = angle + d * (dash_deg + gap_deg)
        end = start + dash_deg
        color = colors[d % len(colors)]
        rdraw.arc(
            (CX - RING_R, CY - RING_R, CX + RING_R, CY + RING_R),
            start,
            end,
            fill=color,
            width=6,
        )
    canvas.alpha_composite(ring_layer)

    ring2 = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    r2draw = ImageDraw.Draw(ring2)
    n2 = 18
    dash2 = 6
    gap2 = (360 - n2 * dash2) / n2
    angle2 = -angle * 1.4
    for d in range(n2):
        start = angle2 + d * (dash2 + gap2)
        end = start + dash2
        r2draw.arc(
            (
                CX - RING_R - 9,
                CY - RING_R - 9,
                CX + RING_R + 9,
                CY + RING_R + 9,
            ),
            start,
            end,
            fill=(255, 255, 255, 90),
            width=2,
        )
    canvas.alpha_composite(ring2)

    back = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(back).ellipse(
        (CX - PHOTO_R - 4, CY - PHOTO_R - 4, CX + PHOTO_R + 4, CY + PHOTO_R + 4),
        fill=(10, 7, 7, 255),
    )
    canvas.alpha_composite(back)

    canvas.alpha_composite(photo_circular, (CX - PHOTO_R, CY - PHOTO_R))

    edge = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(edge).ellipse(
        (CX - PHOTO_R, CY - PHOTO_R, CX + PHOTO_R, CY + PHOTO_R),
        outline=(26, 16, 16, 255),
        width=3,
    )
    canvas.alpha_composite(edge)

    frames.append(canvas.convert("RGBA"))

frames[0].save(
    "assets/portrait-frame.webp",
    save_all=True,
    append_images=frames[1:],
    duration=DUR_MS,
    loop=0,
    format="WEBP",
    quality=78,
    method=4,
)

print("done")
