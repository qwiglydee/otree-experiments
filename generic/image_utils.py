"""
Utilities to generate and manipulate images
"""
from io import BytesIO
from base64 import b64encode
from pathlib import Path

MSG_NEED_PIL = """
FAILURE: Before using these real-effort tasks,
You need to: 
(1) run "pip install Pillow"
(2) add Pillow to your requirements.txt
"""

try:
    # PIL is not actually used here; this is just to generate the warning to install Pillow.
    import PIL  # noqa
except ImportError:
    import sys

    sys.tracebacklimit = 0
    raise SystemExit(MSG_NEED_PIL)

from PIL import Image, ImageDraw, ImageFont, ImageMorph


TEXT_FONT = Path(__file__).parent / "assets" / "FreeSansBold.otf"
TEXT_SIZE = 32
TEXT_PADDING = TEXT_SIZE
TEXT_COLOR = "#000000"
TEXT_BACKGROND = "#FFFFFF"


def render_text(text):
    dumb = Image.new("RGB", (0, 0))
    font = ImageFont.truetype(str(TEXT_FONT), TEXT_SIZE)
    w, h = ImageDraw.ImageDraw(dumb).textsize(text, font)

    w += TEXT_PADDING * 2
    h += TEXT_PADDING * 2
    image = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, w, h], fill=TEXT_BACKGROND)
    draw.text((TEXT_PADDING, TEXT_PADDING), text, font=font, fill=TEXT_COLOR)
    return image


def distort_image(img):
    img = img.convert("L")
    distortions = [
        ImageMorph.MorphOp(op_name="erosion4"),
        ImageMorph.MorphOp(op_name="dilation4"),
    ]
    for op in distortions:
        _, img = op.apply(img)

    # the distorsion leaves black border
    w, h = img.width, img.height
    img = img.crop([1, 1, w - 1, h - 1])

    return img


def encode_image(image):
    buf = BytesIO()
    image.save(buf, "PNG")
    buf64 = b64encode(buf.getvalue())
    datauri = b"data:image/png;base64," + buf64
    return datauri.decode("ascii")
