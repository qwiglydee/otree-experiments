"""
Utilities to generate captcha text and captcha image
"""
from pathlib import Path
from io import BytesIO
from base64 import b64encode
import string
import random

from PIL import Image, ImageDraw, ImageFont, ImageMorph



CHARACTERS = string.ascii_uppercase + string.digits


def generate_text(length):
    return "".join((random.choice(CHARACTERS) for i in range(length)))



TEXT_SIZE = 32
TEXT_PADDING = TEXT_SIZE
TEXT_FONT = str(Path(__file__) / "FreeSansBold.otf")


def generate_image(text):
    dumb = Image.new('RGB', (0, 0))
    font = ImageFont.truetype(TEXT_FONT, TEXT_SIZE)
    w, h = ImageDraw.ImageDraw(dumb).textsize(text, font)
    image = Image.new('RGB', (w + TEXT_PADDING * 2, h + TEXT_PADDING * 2))
    draw = ImageDraw.Draw(image)
    draw.text((TEXT_PADDING, TEXT_PADDING), text, font=font)
    return image


# undocumented pil distorsion operators
distorsion = [ImageMorph.MorphOp(op_name="erosion4"), ImageMorph.MorphOp(op_name="dilation8")]


def distort_image(image):
    img = image.convert('L')
    for op in distorsion:
        _, img = op.apply(img)
    return img


def encode_image(image):
    buf = BytesIO()
    image.save(buf, "PNG")
    bytes = b64encode(buf.getvalue(), )
    datauri = b"data:text/plain;base64," + bytes
    return datauri.decode('ascii')
