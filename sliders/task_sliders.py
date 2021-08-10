import json
from PIL import Image, ImageDraw
import random

SLIDER_SNAP = 4  # size of 1 unit
SLIDER_WIDTH = SLIDER_SNAP * 100
SLIDER_EXTRA = 64  # padding used to randomly shift sliders
SLIDER_TICKS = 10  # every N
SLIDER_HEIGHT = 48
SLIDER_MARGIN = 20  # to fit handle and shade

SLIDER_BBOX = (SLIDER_WIDTH + SLIDER_EXTRA, SLIDER_HEIGHT)

# material design colors
BACK_COLOR = "#E0E0E0"
TRACK_COLOR = "#BB86FC60"
TICK_COLOR = "#6200EE60"
TARGET_COLOR = "#EE6300"
CORRECT_COLOR = "#008B00"


def generate_puzzle_fields(count):
    # 1 column × `count` rows
    grid_w, grid_h = SLIDER_BBOX
    total_w = grid_w + SLIDER_MARGIN * 2
    total_h = grid_h * count

    size = [total_w, total_h]

    # coordinates of sliders' bbox centers
    x0 = total_w // 2
    y0 = grid_h // 2
    coords = [[x0, y0 + grid_h * i] for i in range(count)]

    # target (middle) positions, randomly shifted from bbox center
    solution = [
        random.randint(-SLIDER_EXTRA // 2, SLIDER_EXTRA // 2) for i in range(count)
    ]

    # initial positions, randomly shifted from target, tick-aligned
    initial = [
        solution[i] + random.randint(-50, 50) * SLIDER_SNAP for i in range(count)
    ]
    return dict(size=size, coords=coords, solution=solution, initial=initial)


def is_correct(response, puzzle):
    solution = json.loads(puzzle.solution)
    return [val == sol for val, sol in zip(response, solution)]


def render_image(puzzle):
    puzzle_data = json.loads(puzzle.data)
    size = puzzle_data["size"]
    coords = puzzle_data["coords"]
    solution = json.loads(puzzle.solution)

    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image, "RGBA")

    draw.rectangle((0, 0, size[0], size[1]), fill="#e0e0e0")

    for i in range(len(coords)):
        x0, y0 = coords[i]  # bbox center
        xm = x0 + solution[i]  # actual target center

        # bbox for debug
        # w, h = SLIDER_BBOX
        # draw.rectangle(
        #     [x0 - w / 2, y0 - h / 2, x0 + w / 2, y0 + h / 2],
        #     outline="gray",
        # )

        draw.rounded_rectangle(
            [xm - SLIDER_WIDTH / 2 - 4, y0 - 4, xm + SLIDER_WIDTH / 2 + 4, y0 + 4],
            radius=4,  # PIL cannot draw r=6 w/out antialias
            fill=TRACK_COLOR,
        )

        for v in range(-50, 51, SLIDER_TICKS):
            xv = xm + v * SLIDER_SNAP
            color = TARGET_COLOR if v == 0 else TICK_COLOR
            # draw.rounded_rectangle(
            #     [xv - 2, y0 - 2, xv + 2, y0 + 2], radius=2, fill=BACK_COLOR
            # )
            draw.rounded_rectangle(
                [xv - 2, y0 - 2, xv + 2, y0 + 2], radius=2, fill=color
            )

    return image
