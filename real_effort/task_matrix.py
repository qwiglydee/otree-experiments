from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

TEXT_FONT = Path(__file__).parent / "assets" / "FreeSerifBold.otf"

WIDTH = 5
HEIGHT = 4
TEXT_SIZE = 32
TEXT_PADDING = TEXT_SIZE
IGNORED_CHARS = "↓"
COUNTED_CHAR = "→"

INPUT_TYPE = "number"
INPUT_HINT = f"count symbols {COUNTED_CHAR} in the matrix"


def generate_puzzle_fields():
    """Create new puzzle for a player"""

    rows = []
    for _ in range(HEIGHT):
        row = ''.join(random.choice(IGNORED_CHARS + COUNTED_CHAR) for i in range(WIDTH))
        rows.append(row)
    text = '\n'.join(rows)

    return dict(text=text, solution=str(text.count(COUNTED_CHAR)))


def is_correct(response, puzzle):
    return puzzle.solution == response


def render_image(puzzle):
    font = ImageFont.truetype(str(TEXT_FONT), TEXT_SIZE)
    grid_c = TEXT_SIZE + TEXT_PADDING * 2
    grid_w = grid_c * WIDTH
    grid_h = grid_c * HEIGHT
    image = Image.new("RGB", (grid_w, grid_h))
    draw = ImageDraw.Draw(image)

    for rownum, row in enumerate(puzzle.text.split('\n')):
        for colnum, char in enumerate(row):
            x = colnum * grid_c
            y = rownum * grid_c
            mid = grid_c * 0.5
            draw.rectangle([x, y, x + grid_c, y + grid_c])
            draw.text((x + mid, y + mid), char, font=font, anchor="mm")

    return image
