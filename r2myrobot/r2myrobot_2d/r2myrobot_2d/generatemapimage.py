"""
Generate SVG vector image of the R2MyRobot field using svgwrite.
Adapted from the field drawing logic in main.py (Tkinter version).
"""
import svgwrite
import math

# --- Area definitions (copied from simworld_params.yaml, in mm) ---
# All coordinates are in mm (multiply meters by 1000)
WORLD_POLYGONS = [
    [[50, 50], [6050, 50], [6050, 9500], [50, 9500]],  # Blue main boundary
    [[6100, 50], [12100, 50], [12100, 9500], [6100, 9500]],  # Red main boundary
]
MEIHUA_BLUE = [
    [[1250, 3250], [4850, 3250], [4850, 8060], [1250, 8060]],
]
ARENA_BLUE = [
    [[1550, 9550], [6050, 9550]],
    [[6050, 9550], [6050, 12050]],
    [[6050, 12050], [50, 12050]],
    [[50, 12050], [50, 9550]],
    [[1550, 9550], [1550, 10850]],
]
MEIHUA_RED = [
    [[7300, 3250], [10900, 3250], [10900, 8060], [7300, 8060]],
]
ARENA_RED = [
    [[10550, 9550], [6100, 9550]],
    [[6100, 9550], [6100, 12050]],
    [[6100, 12050], [12100, 12050]],
    [[12100, 12050], [12100, 9550]],
    [[10550, 9550], [10550, 10850]],
]

# --- Drawing helpers for polygons ---
def draw_polygon_mm(dwg, points, color, fill=True, outline=True, outline_outside=False):
    svg_points = [mm_to_svg(x, y) for x, y in points]
    dwg.add(dwg.polygon(
        points=svg_points,
        fill=color if fill else "none",
        stroke="#000000" if (outline and not outline_outside) else "none",
        stroke_width=2 if (outline and not outline_outside) else 0
    ))
    if outline and outline_outside:
        # Draw a polyline with a thicker stroke, slightly outside
        dwg.add(dwg.polyline(
            points=svg_points + [svg_points[0]],
            fill="none",
            stroke="#000000",
            stroke_width=4
        ))

def draw_segment_mm(dwg, p1, p2, color, outline=True):
    svg_p1 = mm_to_svg(*p1)
    svg_p2 = mm_to_svg(*p2)
    dwg.add(dwg.line(svg_p1, svg_p2, stroke="#000000" if outline else color, stroke_width=2))

# Constants (copied from FieldVisualizer)
FIELD_WIDTH = 12150
FIELD_HEIGHT = 12100
SCALE = 1.0  # 1mm = 1 SVG unit (for high-res, can be scaled down in viewer)

# Colors
BG_COLOR = "#FFFFFF"
BLUE_SIDE_BG = "#FFFFFF"
BLUE_SIDE_OVERLAY = "#FFFFFF"
BLUE_SIDE_MAIN = "#FFFFFF"
BLUE_SIDE_GREEN = "#FFFFFF"
BLUE_SIDE_BLUE = "#FFFFFF"
BLUE_SIDE_BROWN = "#FFFFFF"
BLUE_SIDE_YELLOW = "#FFFFFF"
BLUE_SIDE_BEIGE = "#FFFFFF"
RED_SIDE_BG = "#FFFFFF"
RED_SIDE_OVERLAY = "#FFFFFF"
RED_SIDE_MAIN = "#FFFFFF"
RED_SIDE_GREEN = "#FFFFFF"
RED_SIDE_RED = "#FFFFFF"
RED_SIDE_BROWN = "#FFFFFF"
RED_SIDE_YELLOW = "#FFFFFF"
RED_SIDE_BEIGE = "#FFFFFF"

# Helper functions
def mm_to_svg(x, y):
    # SVG Y axis: top-down, so invert Y to match tkinter logic
    return (x * SCALE, (FIELD_HEIGHT - y) * SCALE)

def draw_rect_mm(dwg, x1, y1, x2, y2, color, fill=True, outline=True, outline_outside=False):
    px1, py1 = mm_to_svg(x1, y1)
    px2, py2 = mm_to_svg(x2, y2)
    width = abs(px2 - px1)
    height = abs(py2 - py1)
    x = min(px1, px2)
    y = min(py1, py2)
    # Draw main rect
    dwg.add(dwg.rect(
        insert=(x, y),
        size=(width, height),
        fill=color if fill else "none",
        stroke="#000000" if (outline and not outline_outside) else "none",
        stroke_width=2 if (outline and not outline_outside) else 0
    ))
    # If outline_outside, draw a second rect slightly bigger (stroke outside)
    if outline and outline_outside:
        # SVG stroke is centered on the edge, so to make it outside, expand the rect
        stroke_w = 2
        dwg.add(dwg.rect(
            insert=(x - stroke_w/2, y - stroke_w/2),
            size=(width + stroke_w, height + stroke_w),
            fill="none",
            stroke="#000000",
            stroke_width=stroke_w
        ))

def draw_dot_mm(dwg, x, y, radius, color):
    pass  # dots dihilangkan


def generate_field_svg(filename="field.svg"):
    dwg = svgwrite.Drawing(filename, size=(f"{FIELD_WIDTH*SCALE}", f"{FIELD_HEIGHT*SCALE}"))
    # Base rectangle (white background)
    draw_rect_mm(dwg, 0, 0, FIELD_WIDTH, FIELD_HEIGHT, BG_COLOR, fill=True, outline=False)

    # --- Draw world polygons (outer boundaries) ---
    for poly in WORLD_POLYGONS:
        draw_polygon_mm(dwg, poly, BG_COLOR, fill=True, outline=True, outline_outside=True)

    # --- Draw meihua and arena areas ---
    for poly in MEIHUA_BLUE:
        draw_polygon_mm(dwg, poly, BG_COLOR, fill=True, outline=True)
    for poly in MEIHUA_RED:
        draw_polygon_mm(dwg, poly, BG_COLOR, fill=True, outline=True)
    # Arena blue and red are segments, not closed polygons
    for seg in ARENA_BLUE:
        draw_segment_mm(dwg, seg[0], seg[1], BG_COLOR, outline=True)
    for seg in ARENA_RED:
        draw_segment_mm(dwg, seg[0], seg[1], BG_COLOR, outline=True)

    # --- Center and side elements (brown/white rectangles, as before) ---
    # Center brown
    draw_rect_mm(dwg, 5925, 400, 6225, 1600, BG_COLOR, fill=True, outline=True)
    # Center white
    draw_rect_mm(dwg, 5925, 9940, 6225, 11560, BG_COLOR, fill=True, outline=True)
    # Side brown (left and right, as in original)
    draw_rect_mm(dwg, 2250, 50, 3050, 350, BG_COLOR, fill=True, outline=True)
    draw_rect_mm(dwg, 9100, 50, 9900, 350, BG_COLOR, fill=True, outline=True)

    dwg.save()
    print(f"SVG field saved to {filename}")

if __name__ == "__main__":
    generate_field_svg()
