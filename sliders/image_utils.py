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
except ImportError:
    import sys

    sys.tracebacklimit = 0
    raise SystemExit(MSG_NEED_PIL)


def encode_image(image):
    buf = BytesIO()
    image.save(buf, "PNG")
    buf64 = b64encode(buf.getvalue())
    datauri = b"data:text/plain;base64," + buf64
    return datauri.decode("ascii")
