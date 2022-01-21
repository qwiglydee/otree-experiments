"""
Utilities to generate and manipulate images
"""
from io import BytesIO
from base64 import b64encode

MSG_NEED_PIL = """
FAILURE: Before using these real-effort tasks,
You need to: 
(1) run "pip install Pillow"
(2) add Pillow to your requirements.txt
"""

try:
    # PIL is not actually used here; this is just to generate the warning to install Pillow.
    import PIL  # noqa
    from PIL import Image, ImageDraw, ImageFont, ImageMorph
except ImportError:
    import sys

    sys.tracebacklimit = 0
    raise SystemExit(MSG_NEED_PIL)


def render_text(C, text):
    dumb = Image.new("RGB", (0, 0))
    font = ImageFont.truetype(str(C.TEXT_FONT), C.TEXT_SIZE)
    w, h = ImageDraw.ImageDraw(dumb).textsize(text, font)
    image = Image.new("RGB", (w + C.TEXT_PADDING * 2, h + C.TEXT_PADDING * 2))
    draw = ImageDraw.Draw(image)
    draw.text((C.TEXT_PADDING, C.TEXT_PADDING), text, font=font)

    # distort
    img = image.convert("L")
    distortions = [
        ImageMorph.MorphOp(op_name="erosion4"),
        ImageMorph.MorphOp(op_name="dilation4"),
    ]
    for op in distortions:
        _, img = op.apply(img)
    return img


def encode_image(image):
    buf = BytesIO()
    image.save(buf, "PNG")
    buf64 = b64encode(buf.getvalue())
    datauri = b"data:text/plain;base64," + buf64
    return datauri.decode("ascii")
