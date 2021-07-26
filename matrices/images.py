"""
Utilities to generate and manipulate images
"""
from pathlib import Path
from io import BytesIO
from base64 import b64encode

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import sys

    sys.tracebacklimit = 0
    raise SystemExit(
        f"FAILURE: Missing imaging library required in `{__name__}`\nYou need to install it using `pip install Pillow`"
    )


TEXT_SIZE = 32
TEXT_PADDING = 16
TEXT_FONT = Path(__file__).parent / "FreeSansBold.otf"


def generate_image(size: tuple, content: str):
    font = ImageFont.truetype(str(TEXT_FONT), TEXT_SIZE)
    grid_c = TEXT_SIZE + TEXT_PADDING * 2
    grid_w = grid_c * size[0]
    grid_h = grid_c * size[1]
    image = Image.new("RGB", (grid_w, grid_h))
    draw = ImageDraw.Draw(image)

    w = size[0]
    for i, char in enumerate(content):
        row = i // w
        col = i % w
        x = col * grid_c
        y = row * grid_c
        mid = grid_c * 0.5
        draw.rectangle([x, y, x + grid_c, y + grid_c])
        draw.text((x + mid, y + mid), char, font=font, anchor="mm")

    return image


def encode_image(image):
    buf = BytesIO()
    image.save(buf, "PNG")
    buf64 = b64encode(buf.getvalue())
    datauri = b"data:text/plain;base64," + buf64
    return datauri.decode("ascii")
