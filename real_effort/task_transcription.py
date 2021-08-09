from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageMorph
import random

CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
LENGTH = 3
TEXT_SIZE = 32
TEXT_PADDING = TEXT_SIZE
TEXT_FONT = Path(__file__).parent / "assets" / "FreeSansBold.otf"

INPUT_TYPE = "text"
INPUT_HINT = "enter text from the image"


def generate_puzzle_fields():
    text = "".join((random.choice(CHARSET) for _ in range(LENGTH)))
    return dict(text=text, solution=text)


def is_correct(response, puzzle):
    return puzzle.solution.lower() == response.lower()


def render_image(puzzle):
    text = puzzle.text
    dumb = Image.new("RGB", (0, 0))
    font = ImageFont.truetype(str(TEXT_FONT), TEXT_SIZE)
    w, h = ImageDraw.ImageDraw(dumb).textsize(text, font)
    image = Image.new("RGB", (w + TEXT_PADDING * 2, h + TEXT_PADDING * 2))
    draw = ImageDraw.Draw(image)
    draw.text((TEXT_PADDING, TEXT_PADDING), text, font=font)

    # distort
    img = image.convert("L")
    distortions = [
        ImageMorph.MorphOp(op_name="erosion4"),
        ImageMorph.MorphOp(op_name="dilation4"),
    ]
    for op in distortions:
        _, img = op.apply(img)
    return img
