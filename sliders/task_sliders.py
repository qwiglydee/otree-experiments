import json
from PIL import Image, ImageDraw
import random

SLIDER_RANGE = 100
SLIDER_EXTRA = 10

SLIDER_STEP = 8
SLIDER_WIDTH = SLIDER_STEP * SLIDER_RANGE
SLIDER_PADDING = SLIDER_STEP * SLIDER_EXTRA
SLIDER_HEIGHT = 16
SLIDER_BBOX = (SLIDER_WIDTH + SLIDER_PADDING, SLIDER_HEIGHT)
SLIDER_MARGIN = 12


def generate_puzzle_fields(count):
    # 1 column × `count` rows
    box_w, box_h = SLIDER_BBOX
    grid_x = box_w + SLIDER_MARGIN
    grid_y = box_h + SLIDER_MARGIN
    total_w = grid_x + SLIDER_MARGIN
    total_h = grid_y * count + SLIDER_MARGIN

    size = [total_w, total_h]

    # coordinates of sliders' bbox centers
    x0 = total_w // 2
    y0 = grid_y // 2 + SLIDER_MARGIN // 2
    coords = [[x0, y0 + grid_y * i] for i in range(count)]

    # middle (target) positions, randomly shifted from center by whole number
    solution = [
        random.randint(-SLIDER_EXTRA // 2, SLIDER_EXTRA // 2) * SLIDER_STEP
        for i in range(count)
    ]

    # initial positions, randomly shifted from center
    initial = [random.randint(-50, 50) * SLIDER_STEP for i in range(count)]
    return dict(size=size, coords=coords, solution=solution, initial=initial)


def is_correct(response, puzzle):
    solution = json.loads(puzzle.solution)
    return [val == sol for val, sol in zip(response, solution)]


def render_image(puzzle):
    puzzle_data = json.loads(puzzle.data)
    size = puzzle_data["size"]
    coords = puzzle_data["coords"]
    solution = json.loads(puzzle.solution)
    initial = puzzle_data["initial"]

    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, size[0], size[1]), fill="#e0e0e0")

    for i in range(len(coords)):
        x0, y0 = coords[i]  # bbox center
        xm = x0 + solution[i]  # actual target center

        # slider bbox
        # w, h = SLIDER_BBOX
        # rx = w // 2
        # ry = h // 2
        # draw.rectangle([x0 - rx, y0 - ry, x0 + rx, y0 + ry], fill="#d8d8d8")

        th = SLIDER_HEIGHT // 2
        # slider main line
        draw.rectangle(
            [xm - 50 * SLIDER_STEP, y0 - th, xm + 50 * SLIDER_STEP, y0 + th],
            fill="#a0a0a0",
        )
        # slider marks
        for v in range(-50, 51):
            xv = xm + v * SLIDER_STEP
            if v == 0:  # middle mark
                draw.line([xv, y0 - th, xv, y0 + th], width=2, fill="#ffa000")
            else:
                draw.line([xv, y0 - th, xv, y0 + th], width=1, fill="#808080")

    return image
