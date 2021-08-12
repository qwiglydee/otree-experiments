import math
import json
from PIL import Image, ImageDraw
import random

SLIDER_SNAP = 4  # size of 1 unit
SLIDER_WIDTH = SLIDER_SNAP * 100
SLIDER_EXTRA = 64  # padding used to randomly shift sliders
SLIDER_TICKS = 10  # every N
SLIDER_HEIGHT = 48
SLIDER_MARGIN = 15  # to fit handle and shade

SLIDER_BBOX = (SLIDER_WIDTH + SLIDER_EXTRA, SLIDER_HEIGHT)

# material design colors
BACK_COLOR = "#E0E0E0"
TRACK_COLOR = "#BB86FC60"
TICK_COLOR = "#6200EE60"
TARGET_COLOR = "#EE6300"
CORRECT_COLOR = "#008B00"


def generate_layout(params):
    """Generate grid of sliders"""

    count = params['num_sliders']
    columns = params['num_columns']
    rows = math.ceil(count / columns)

    grid_w, grid_h = SLIDER_BBOX
    total_w = (grid_w + SLIDER_MARGIN * 2) * columns
    total_h = grid_h * rows

    # coordinates of sliders' bbox centers
    def center(i):
        col = math.floor(i / rows)
        row = i % rows
        x = (grid_w + SLIDER_MARGIN * 2) * (col + 0.5)
        y = grid_h * (row + 0.5)
        return x, y

    grid = [center(i) for i in range(count)]

    return dict(size=[total_w, total_h], grid=grid)


def generate_slider():
    """Generate a slider, with target center position shifted within grid cell"""
    target = random.randint(-SLIDER_EXTRA // 2, SLIDER_EXTRA // 2)
    initial = target + random.randint(-50, 50) * SLIDER_SNAP

    return target, initial


def snap_value(value, center):
    return round((value - center) / SLIDER_SNAP) * SLIDER_SNAP + center


def render_image(layout, targets):
    size = layout["size"]
    grid = layout["grid"]

    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image, "RGBA")

    draw.rectangle((0, 0, size[0], size[1]), fill="#e0e0e0")

    for i, target in enumerate(targets):
        x0, y0 = grid[i]  # bbox center
        xm = x0 + target

        # bbox for debug
        w, h = SLIDER_BBOX
        draw.rectangle(
            [x0 - w / 2, y0 - h / 2, x0 + w / 2, y0 + h / 2],
            outline="gray",
        )

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
