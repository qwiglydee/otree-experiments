"""
Utilities to generate and manipulate images
"""
from pathlib import Path
from io import BytesIO
from base64 import b64encode

from PIL import Image, ImageDraw, ImageFont


TEXT_SIZE = 32
TEXT_PADDING = TEXT_SIZE
TEXT_FONT = str(Path(__file__).parent.parent / "_static" / "FreeSansBold.otf")


def generate_image(text):
    dumb = Image.new("RGB", (0, 0))
    font = ImageFont.truetype(TEXT_FONT, TEXT_SIZE)
    w, h = ImageDraw.ImageDraw(dumb).textsize(text, font)
    image = Image.new("RGB", (w + TEXT_PADDING * 2, h + TEXT_PADDING * 2))
    draw = ImageDraw.Draw(image)
    draw.text((TEXT_PADDING, TEXT_PADDING), text, font=font)
    return image


def encode_image(image):
    buf = BytesIO()
    image.save(buf, "PNG")
    buf64 = b64encode(buf.getvalue())
    datauri = b"data:text/plain;base64," + buf64
    return datauri.decode("ascii")
