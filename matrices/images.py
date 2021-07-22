"""
Utilities to generate and manipulate images
"""
from pathlib import Path
from io import BytesIO
from base64 import b64encode

from PIL import Image, ImageDraw, ImageFont


TEXT_SIZE = 32
TEXT_PADDING = 16
TEXT_FONT = str(Path(__file__).parent.parent / "_static" / "FreeSansBold.otf")


def generate_image(size: int, content: str):
    font = ImageFont.truetype(TEXT_FONT, TEXT_SIZE)
    cell_w = TEXT_SIZE + TEXT_PADDING * 2
    grid_w = cell_w * size
    image = Image.new("RGB", (grid_w, grid_w))
    draw = ImageDraw.Draw(image)

    for i, char in enumerate(content):
        row = i // size
        col = i % size
        x = col * cell_w
        y = row * cell_w
        mid = cell_w * 0.5
        draw.rectangle([x, y, x + cell_w, y + cell_w])
        draw.text((x + mid, y + mid), char, font=font, anchor="mm")

    return image


def encode_image(image):
    buf = BytesIO()
    image.save(buf, "PNG")
    buf64 = b64encode(buf.getvalue())
    datauri = b"data:text/plain;base64," + buf64
    return datauri.decode("ascii")
