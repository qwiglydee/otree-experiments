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
TEXT_PADDING = TEXT_SIZE
TEXT_FONT = Path(__file__).parent / "FreeSerifBold.otf"


def generate_image(text):
    dumb = Image.new("RGB", (0, 0))
    font = ImageFont.truetype(str(TEXT_FONT), TEXT_SIZE)
    w, h = ImageDraw.ImageDraw(dumb).textsize(text, font)
    image = Image.new("RGB", (w + TEXT_PADDING * 2, h + TEXT_PADDING * 2))
    draw = ImageDraw.Draw(image)
    draw.text((TEXT_PADDING, TEXT_PADDING), text, font=font)
    return image


try:
    from PIL import ImageMorph

    # undocumented pil distorsion operators
    # distorsion = [ImageMorph.MorphOp(op_name="erosion4"), ImageMorph.MorphOp(op_name="dilation4")]
    distorsion = [ImageMorph.MorphOp(op_name="dilation4")]
except ImportError:
    print(
        "Image generation won't work. You need to install a module use `pip install Pillow`"
    )
    distorsion = []


def distort_image(image):
    img = image.convert("L")
    for op in distorsion:
        _, img = op.apply(img)
    return img


def encode_image(image):
    buf = BytesIO()
    image.save(buf, "PNG")
    buf64 = b64encode(buf.getvalue())
    datauri = b"data:text/plain;base64," + buf64
    return datauri.decode("ascii")
