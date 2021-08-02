"""
Utilities to generate and manipulate images
"""
from io import BytesIO
from base64 import b64encode

try:
    # PIL is not actually used here; this is just to generate the warning to install Pillow.
    import PIL  # noqa
except ImportError:
    import sys

    sys.tracebacklimit = 0
    raise SystemExit(
        f"FAILURE: Missing imaging library required in `{__name__}`\nYou need to install it using `pip install Pillow`"
    )


def encode_image(image):
    buf = BytesIO()
    image.save(buf, "PNG")
    buf64 = b64encode(buf.getvalue())
    datauri = b"data:text/plain;base64," + buf64
    return datauri.decode("ascii")
