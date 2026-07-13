#!/usr/bin/env python3
"""
2D Field Visualization GUI for R2MyRobot
Menggunakan tkinter untuk menampilkan lapangan dengan grid yang interaktif
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import math
from datetime import datetime
import threading
import time

# ROS2 imports (optional, akan digunakan untuk publish point)
try:
    import rclpy
    from std_msgs.msg import String
    from rclpy.parameter import Parameter
    HAS_ROS = True
except ImportError:
    HAS_ROS = False


class FieldVisualizer:
    """Main GUI class untuk field visualization dengan grid interaktif"""
    
    # Constants untuk dimensi lapangan (dalam mm, akan di-scale untuk display)
    FIELD_WIDTH = 12150
    FIELD_HEIGHT = 12100
    
    # Scale factor (mm to pixels)
    SCALE = 0.05  # 1mm = 0.05px
    
    # Colors
    BG_COLOR = "#C9A792"
    
    # Blue side elements
    BLUE_SIDE_BG = "#81D2D6"
    BLUE_SIDE_OVERLAY = "#949EA0"
    BLUE_SIDE_MAIN = "#80BFD1"
    BLUE_SIDE_GREEN = "#2A7138"
    BLUE_SIDE_BLUE = "#3100FF"
    BLUE_SIDE_BROWN = "#9B5F00"
    BLUE_SIDE_YELLOW = "#E6E22B"
    BLUE_SIDE_BEIGE = "#C0BDB5"
    
    # Red side elements
    RED_SIDE_BG = "#FEBAA3"
    RED_SIDE_OVERLAY = "#949EA0"
    RED_SIDE_MAIN = "#ECA297"
    RED_SIDE_GREEN = "#2A7138"
    RED_SIDE_RED = "#DF2222"
    RED_SIDE_BROWN = "#9B5F00"
    RED_SIDE_YELLOW = "#E6E22B"
    RED_SIDE_BEIGE = "#C0BDB5"
    
    # Grid settings
    GRID_SIZE = 1200  # mm per grid
    
    def __init__(self, root):
        self.root = root
        self.root.title("R2MyRobot 2D Field Visualization")
        
        # Initialize log_text first (will be populated by setup_ui)
        self.log_text = None
        
        # Setup GUI (creates log_text)
        self.setup_ui()
        
        # Setup ROS2 publisher if available (now safe to call log)
        self.ros_initialized = False
        self.publisher = None
        if HAS_ROS:
            self.setup_ros()
            # Ensure we cleanly stop ROS spin when GUI closes
            try:
                self.root.protocol("WM_DELETE_WINDOW", self._on_close)
            except Exception:
                pass
        
        # Grid tracking
        self.zona_biru_grids = []
        self.zona_merah_grids = []
        self.grid_rectangles = {}  # canvas_id -> grid info
        
        # Animation tracking
        self.bounce_animations = {}  # rect_id -> animation state (temporary)
        # Persistent highlighted rectangles (keep highlight until clicked again)
        self.highlighted_rects = {}  # rect_id -> original visual properties
        # Create the field visualization
        self.create_field()
        self.create_grids()
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux scroll down
        self.canvas.bind("<Button-2>", self.on_pan_start)    # Middle click
        self.canvas.bind("<B2-Motion>", self.on_pan_motion)  # Middle click drag
        self.canvas.bind("<ButtonRelease-2>", self.on_pan_end)
        
    def setup_ros(self):
        """Initialize ROS2 node for publishing points and spin in a background thread."""
        try:
            rclpy.init()
            self.node = rclpy.create_node('r2myrobot_2d_gui')
            self.publisher = self.node.create_publisher(String, 'map_2d_mypoint', 10)
            # Subscribe to PoseStamped to keep GUI robot marker in sync with simworld
            from geometry_msgs.msg import PoseStamped
            try:
                self.pose_sub = self.node.create_subscription(PoseStamped, '/r2myrobot/pose_stamped', self._on_pose_stamped, 10)
                self.log("Subscribed to /r2myrobot/pose_stamped for GUI updates", "ROS")
            except Exception as e:
                self.log(f"Failed to subscribe to pose_stamped: {e}", "ERROR")

            # Publisher to request simworld to toggle area borders
            try:
                self.sim_area_pub = self.node.create_publisher(String, '/r2myrobot/simworld/area_toggle', 10)
                self.log("Created simworld area toggle publisher on /r2myrobot/simworld/area_toggle", "ROS")
            except Exception as e:
                self.log(f"Failed to create simworld area publisher: {e}", "ERROR")

            # Start a background thread to spin the rclpy executor so callbacks are delivered
            self._ros_running = True
            self._ros_spin_thread = threading.Thread(target=self._ros_spin_loop, name='r2_spin', daemon=True)
            self._ros_spin_thread.start()

            self.ros_initialized = True
            self.log("ROS2 node initialized and spin thread started", "ROS")
        except Exception as e:
            self.log(f"ROS2 initialization failed: {str(e)}", "ERROR")
    
    def setup_ui(self):
        """Setup tkinter UI components"""
        # Main container with PanedWindow for resizable panels
        main_container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Canvas untuk field
        left_frame = tk.Frame(main_container)
        main_container.add(left_frame, width=600, stretch="always")
        
        canvas_width = int(self.FIELD_WIDTH * self.SCALE) + 20
        canvas_height = int(self.FIELD_HEIGHT * self.SCALE) + 20
        
        # Canvas with scrollbars
        self.canvas_frame = tk.Frame(left_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        h_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=600,
            height=600,
            bg=self.BG_COLOR,
            cursor="cross",
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set,
            scrollregion=(0, 0, canvas_width, canvas_height)
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        h_scroll.config(command=self.canvas.xview)
        v_scroll.config(command=self.canvas.yview)
        
        # Zoom and pan tracking
        self.zoom_level = 1.0
        self.applied_scale = 1.0  # current applied visual scale on the canvas
        self.pan_start = None
        
        # Right: Log panel
        right_frame = tk.Frame(main_container)
        main_container.add(right_frame, width=300, stretch="never")
        
        log_label = tk.Label(right_frame, text="LOG", font=("Arial", 10, "bold"))
        log_label.pack(anchor="w", pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            right_frame,
            width=35,
            height=35,
            state=tk.DISABLED,
            font=("Courier", 8)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Bottom: Navigation bar
        nav_frame = tk.Frame(self.root)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(nav_frame, text="Navigation:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="Reset Field", command=self.reset_field).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="Export Grid Data", command=self.export_grid_data).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="Zoom Reset", command=self.zoom_reset).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="Options", command=self.toggle_options).pack(side=tk.LEFT, padx=2)  # expandable options panel
        
        # Options panel state (declare before creating the side indicator)
        self.options_expanded = False
        self.side_choice = tk.StringVar(value="BLUE")
        self.meihua_blue_var = tk.BooleanVar(value=False)
        self.arena_blue_var = tk.BooleanVar(value=False)
        self.meihua_red_var = tk.BooleanVar(value=False)
        self.arena_red_var = tk.BooleanVar(value=False)
        self.ignore_grid_var = tk.BooleanVar(value=False)
        self.place_robot_mode = False

        self.zoom_label = tk.Label(nav_frame, text="Zoom: 100%", font=("Arial", 8))
        self.zoom_label.pack(side=tk.RIGHT, padx=5)
        # Side indicator: shows current selected side with color
        self.side_indicator = tk.Label(nav_frame, text=self.side_choice.get(), font=("Arial", 9, "bold"), width=6)
        self._update_side_indicator()
        self.side_indicator.pack(side=tk.RIGHT, padx=5)
        self.status_label = tk.Label(nav_frame, text="Ready", font=("Arial", 8))
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Ensure options frame exists and has a creation flag so toggle is safe
        self.options_frame = tk.Frame(self.root, relief=tk.RIDGE, bd=1)
        self.options_widgets_created = False

        # Robot marker id for visual placement
        self.robot_marker_id = None
        # Last received pose (meters)
        self._last_pose = None

    def _on_pose_stamped(self, msg):
        # rclpy callback runs in its own thread; schedule UI update via root.after
        try:
            x = msg.pose.position.x
            y = msg.pose.position.y
            # Orientation -> yaw
            q = msg.pose.orientation
            try:
                # avoid adding tf dependency; compute yaw manually
                yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
            except Exception:
                yaw = 0.0
            # convert meters to mm for GUI
            mx = int(round(x * 1000.0))
            my = int(round(y * 1000.0))
            # Schedule the GUI update on the main thread
            self.root.after(0, lambda: self._update_robot_marker_from_pose(mx, my, yaw))
        except Exception as e:
            self.log(f"Error handling pose_stamped for GUI: {e}", "ERROR")

    def _update_robot_marker_from_pose(self, mx, my, yaw=0.0):
        px, py = self.mm_to_pixels(mx, my)
        r = max(6, int(250 * self.SCALE * self.applied_scale))
        side = self.side_choice.get()
        color = self.BLUE_SIDE_MAIN if side == 'BLUE' else self.RED_SIDE_MAIN
        outline = '#330033'
        if self.robot_marker_id:
            try:
                self.canvas.coords(self.robot_marker_id, px - r, py - r, px + r, py + r)
                self.canvas.itemconfig(self.robot_marker_id, fill=color, outline=outline)
            except Exception:
                pass
        else:
            self.robot_marker_id = self.canvas.create_oval(px - r, py - r, px + r, py + r, fill=color, outline=outline)
        heading_len = max(12, 2 * r)
        hx = px + math.cos(yaw) * heading_len
        hy = py - math.sin(yaw) * heading_len
        if getattr(self, 'robot_heading_id', None):
            try:
                self.canvas.coords(self.robot_heading_id, px, py, hx, hy)
            except Exception:
                pass
        else:
            self.robot_heading_id = self.canvas.create_line(px, py, hx, hy, fill=outline, width=2, arrow=tk.LAST)
        self.status_label.config(text=f"Robot at ({mx},{my}) mm")
    
    def mm_to_pixels(self, x, y):
        """Convert mm coordinates to canvas pixels with Y-axis inversion (cartesian style)"""
        px = int(x * self.SCALE * self.applied_scale)
        canvas_height_px = int(self.FIELD_HEIGHT * self.SCALE * self.applied_scale)
        py = canvas_height_px - int(y * self.SCALE * self.applied_scale)
        return (px, py)
    
    def pixels_to_mm(self, x, y):
        """Convert canvas pixels to mm coordinates with Y-axis inversion"""
        mx = int(x / (self.SCALE * self.applied_scale))
        canvas_height_px = int(self.FIELD_HEIGHT * self.SCALE * self.applied_scale)
        my = int((canvas_height_px - y) / (self.SCALE * self.applied_scale))
        return (mx, my)
    
    def create_field(self):
        """Create the field with all visual elements"""
        self.log("Creating field...", "SYSTEM")
        
        # Base rectangle (lapisan paling bawah)
        self.draw_rect_mm(0, 0, self.FIELD_WIDTH, self.FIELD_HEIGHT, self.BG_COLOR, fill=True)
        
        # BLUE SIDE (sisi biru)
        self.log("Creating blue side...", "SYSTEM")
        self.draw_rect_mm(50, 50, 6050, 12050, self.BLUE_SIDE_BG, fill=True)
        self.draw_rect_mm(50, 2020, 6050, 9550, self.BLUE_SIDE_OVERLAY, fill=True)
        self.draw_rect_mm(50, 2050, 6050, 9500, self.BLUE_SIDE_MAIN, fill=True)
        self.draw_rect_mm(1250, 3250, 4850, 8060, self.BLUE_SIDE_GREEN, fill=True)
        
        # Blue side decorative elements
        self.draw_rect_mm(50, 50, 1050, 1050, self.BLUE_SIDE_BLUE, fill=True)
        self.draw_rect_mm(2250, 50, 3050, 350, self.BLUE_SIDE_BROWN, fill=True)
        self.draw_rect_mm(4250, 50, 5050, 850, self.BLUE_SIDE_BLUE, fill=True)
        self.draw_rect_mm(50, 11050, 1050, 12050, self.BLUE_SIDE_BLUE, fill=True)
        self.draw_rect_mm(3550, 9550, 5050, 9850, self.BLUE_SIDE_YELLOW, fill=True)
        self.draw_rect_mm(50, 9350, 1550, 10850, self.BLUE_SIDE_BEIGE, fill=True)
        
        # RED SIDE (sisi merah)
        self.log("Creating red side...", "SYSTEM")
        self.draw_rect_mm(6100, 50, 12100, 12050, self.RED_SIDE_BG, fill=True)
        self.draw_rect_mm(6100, 2020, 12100, 9550, self.RED_SIDE_OVERLAY, fill=True)
        self.draw_rect_mm(6100, 2050, 12100, 9500, self.RED_SIDE_MAIN, fill=True)
        self.draw_rect_mm(7300, 3250, 10900, 8060, self.RED_SIDE_GREEN, fill=True)
        
        # Red side decorative elements
        self.draw_rect_mm(11100, 50, 12100, 1050, self.RED_SIDE_RED, fill=True)
        self.draw_rect_mm(9100, 50, 9900, 350, self.RED_SIDE_BROWN, fill=True)
        self.draw_rect_mm(7100, 50, 7900, 850, self.RED_SIDE_RED, fill=True)
        self.draw_rect_mm(11100, 11050, 12100, 12050, self.RED_SIDE_RED, fill=True)
        self.draw_rect_mm(7100, 9550, 8600, 9850, self.RED_SIDE_YELLOW, fill=True)
        self.draw_rect_mm(10600, 9350, 12100, 10850, self.RED_SIDE_BEIGE, fill=True)
        
        # CENTER ELEMENTS (tambahan)
        self.log("Creating center elements...", "SYSTEM")
        self.draw_rect_mm(5925, 400, 6225, 1600, self.BLUE_SIDE_BROWN, fill=True)
        self.draw_rect_mm(5925, 9940, 6225, 11560, "#FCF7F5", fill=True)
        
        # Center dots (black dots)
        center_dots_blue = [(2350, 200), (2550, 200), (2750, 200), (2950, 200)]
        center_dots_red = [(9200, 200), (9400, 200), (9600, 200), (9800, 200)]
        center_dots_middle = [(6075, 500), (6075, 700), (6075, 900), (6075, 1100), (6075, 1300), (6075, 1500)]
        
        for x, y in center_dots_blue + center_dots_red + center_dots_middle:
            self.draw_dot_mm(x, y, 8, "black")
        
        self.log("Field created successfully", "SYSTEM")
    
    def create_grids(self):
        """Create clickable grids for blue and red zones"""
        self.log("Creating grids...", "SYSTEM")
        
        # clear existing grids and mappings to avoid duplication when called multiple times
        self.zona_biru_grids.clear()
        self.zona_merah_grids.clear()
        self.grid_rectangles.clear()
        
        # Blue zone grid
        self.create_zone_grid(
            start_x=50,
            start_y=2050,
            end_x=6050,
            end_y=9250,
            grid_size=self.GRID_SIZE,
            zone_name="BLUE",
            grid_list=self.zona_biru_grids
        )
        
        # Red zone grid
        self.create_zone_grid(
            start_x=6100,
            start_y=2050,
            end_x=12100,
            end_y=9250,
            grid_size=self.GRID_SIZE,
            zone_name="RED",
            grid_list=self.zona_merah_grids
        )
        
        self.log(f"Grids created: {len(self.zona_biru_grids)} blue + {len(self.zona_merah_grids)} red", "SYSTEM")
        # Update scrollregion now that all items are created
        self.update_scrollregion()
    
    def create_zone_grid(self, start_x, start_y, end_x, end_y, grid_size, zone_name, grid_list):
        """Create grid for a specific zone"""
        grid_width = end_x - start_x
        grid_height = end_y - start_y
        
        cols = grid_width // grid_size
        rows = grid_height // grid_size
        
        grid_id = 0
        for row in range(rows):
            for col in range(cols):
                x1 = start_x + col * grid_size
                y1 = start_y + row * grid_size
                x2 = x1 + grid_size
                y2 = y1 + grid_size
                
                # Center point of grid
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # Draw grid rectangle
                px1, py1 = self.mm_to_pixels(x1, y1)
                px2, py2 = self.mm_to_pixels(x2, y2)
                
                rect_id = self.canvas.create_rectangle(
                    px1, py1, px2, py2,
                    outline="black",
                    width=1,
                    fill="#000000",
                    stipple="gray25"
                )
                
                grid_info = {
                    "id": grid_id,
                    "zone": zone_name,
                    "rect_id": rect_id,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "center_x": center_x,
                    "center_y": center_y,
                    "row": row,
                    "col": col
                }
                
                grid_list.append(grid_info)
                self.grid_rectangles[rect_id] = grid_info
                grid_id += 1
    
    def draw_rect_mm(self, x1, y1, x2, y2, color, fill=False):
        """Draw rectangle from mm coordinates"""
        px1, py1 = self.mm_to_pixels(x1, y1)
        px2, py2 = self.mm_to_pixels(x2, y2)
        
        self.canvas.create_rectangle(
            px1, py1, px2, py2,
            fill=color if fill else "",
            outline=color if not fill else "",
            width=1
        )
    
    def draw_dot_mm(self, x, y, radius, color):
        """Draw dot from mm coordinates"""
        px, py = self.mm_to_pixels(x, y)
        r = int(radius * self.SCALE)
        self.canvas.create_oval(
            px - r, py - r, px + r, py + r,
            fill=color,
            outline=color
        )
    
    def on_canvas_click(self, event):
        """Handle canvas click events with support for place-robot and ignore-grid modes. Fix: gunakan canvasx/canvasy agar klik tetap akurat setelah scroll."""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        # If place-robot mode active: place exactly where user clicked
        if self.place_robot_mode:
            mx, my = self.pixels_to_mm(cx, cy)
            self.place_robot_at(mx, my)
            self.place_robot_mode = False
            self.status_label.config(text=f"Robot placed: ({mx}, {my})")
            return

        # If ignore-grid mode enabled, publish wherever clicked
        if self.ignore_grid_var.get():
            mx, my = self.pixels_to_mm(cx, cy)
            self.publish_point_mm(mx, my)
            self.status_label.config(text=f"Published point: ({mx}, {my})")
            return

        # Default behavior: check if clicked on a grid rectangle
        items = self.canvas.find_overlapping(cx - 2, cy - 2, cx + 2, cy + 2)
        for item_id in items:
            if item_id in self.grid_rectangles:
                self.on_grid_click(self.grid_rectangles[item_id])
                return

    def place_robot_at(self, mx, my):
        # Remove existing marker
        if self.robot_marker_id:
            try:
                self.canvas.delete(self.robot_marker_id)
            except Exception:
                pass
            self.robot_marker_id = None
        if getattr(self, 'robot_heading_id', None):
            try:
                self.canvas.delete(self.robot_heading_id)
            except Exception:
                pass
            self.robot_heading_id = None
        px, py = self.mm_to_pixels(mx, my)
        r = int(250 * self.SCALE * self.applied_scale)
        side = self.side_choice.get()
        color = self.BLUE_SIDE_MAIN if side == 'BLUE' else self.RED_SIDE_MAIN
        outline = '#330033'
        self.robot_marker_id = self.canvas.create_oval(px - r, py - r, px + r, py + r, fill=color, outline=outline)
        heading_len = max(12, 2 * r)
        hx = px + math.cos(0.0) * heading_len
        hy = py - math.sin(0.0) * heading_len
        self.robot_heading_id = self.canvas.create_line(px, py, hx, hy, fill=outline, width=2, arrow=tk.LAST)
        self.log(f"Robot placed at ({mx},{my}) mm", "SYSTEM")
        self.publish_point_mm(mx, my)

    def publish_point_mm(self, mx, my):
        """Publish a map point as 'x,y' to map_2d_mypoint if ROS is available; always log."""
        self.log(f"Publishing point: ({mx},{my})", "SYSTEM")
        if self.ros_initialized and self.publisher:
            try:
                msg = String()
                msg.data = f"{mx},{my}"
                self.publisher.publish(msg)
                self.log(f"Published to map_2d_mypoint: {msg.data}", "ROS")
            except Exception as e:
                self.log(f"Failed to publish: {e}", "ERROR")
    
    def on_grid_click(self, grid_info):
        """Handle grid click with toggle highlight behavior"""
        rect_id = grid_info["rect_id"]
        grid_id = f"{grid_info['zone']}_{grid_info['row']}_{grid_info['col']}"
        center_x = grid_info["center_x"]
        center_y = grid_info["center_y"]

        # Log the click
        log_msg = f"[{grid_info['zone']}] Grid ({grid_info['row']},{grid_info['col']}) -> Point: ({center_x}, {center_y}) mm"
        self.log(log_msg, "CLICK")

        # Publish to ROS topic if available
        if self.ros_initialized:
            msg = String()
            msg.data = f"{center_x},{center_y}"
            self.publisher.publish(msg)
            self.log(f"Published to map_2d_mypoint: {msg.data}", "ROS")

        # Toggle highlight: if already highlighted, un-highlight; otherwise animate and highlight
        if rect_id in self.highlighted_rects:
            orig = self.highlighted_rects.pop(rect_id)
            try:
                self.canvas.itemconfig(
                    rect_id,
                    fill=orig.get('fill', ''),
                    outline=orig.get('outline', ''),
                    width=orig.get('width', 1),
                    stipple=orig.get('stipple', '')
                )
            except Exception:
                pass
            self.log(f"Un-highlighted grid {grid_id}", "SYSTEM")
        else:
            self.animate_grid_bounce(rect_id)

        # Update status
        self.status_label.config(text=f"Last click: ({center_x}, {center_y})")
    
    def animate_grid_bounce(self, rect_id):
        """Animate grid with bounce effect

        Stores original visual properties (fill, outline, width, stipple) and
        marks the rect as highlighted when the animation finishes. Prevents
        starting a second animation on the same rect while one is running.
        """
        # Prevent concurrent animations on the same rectangle
        if rect_id in self.bounce_animations:
            return

        coords = self.canvas.coords(rect_id)
        if not coords or len(coords) < 4:
            return
        px1, py1, px2, py2 = coords[0], coords[1], coords[2], coords[3]

        # Store original coordinates and visual properties
        original_width = px2 - px1
        original_height = py2 - py1
        center_px = (px1 + px2) / 2
        center_py = (py1 + py2) / 2

        orig_fill = self.canvas.itemcget(rect_id, 'fill') or ''
        orig_outline = self.canvas.itemcget(rect_id, 'outline') or ''
        try:
            orig_width = float(self.canvas.itemcget(rect_id, 'width'))
        except Exception:
            orig_width = 1
        orig_stipple = self.canvas.itemcget(rect_id, 'stipple') or ''

        # save temp animation state
        self.bounce_animations[rect_id] = {
            'fill': orig_fill,
            'outline': orig_outline,
            'width': orig_width,
            'stipple': orig_stipple,
            'coords': (px1, py1, px2, py2)
        }

        def bounce_step(step, max_steps=10):
            # If the item was deleted during animation, abort
            if not self.canvas.find_withtag(rect_id):
                self.bounce_animations.pop(rect_id, None)
                return

            if step > max_steps:
                # Restore original coordinates but keep highlight visuals,
                # and move original visuals into highlighted_rects to allow
                # later un-highlight on click.
                try:
                    self.canvas.coords(rect_id, px1, py1, px2, py2)
                except Exception:
                    pass
                anim = self.bounce_animations.pop(rect_id, None)
                if anim is not None:
                    # Keep current highlight visuals (fill/orange) on canvas,
                    # but remember originals for restoration on un-highlight.
                    self.highlighted_rects[rect_id] = {
                        'fill': anim.get('fill', ''),
                        'outline': anim.get('outline', ''),
                        'width': anim.get('width', 1),
                        'stipple': anim.get('stipple', '')
                    }
                return

            # Scale factor (bounce effect)
            scale = 1.0 - (abs(step - max_steps/2) / (max_steps/2)) * 0.15

            new_width = original_width * scale
            new_height = original_height * scale

            new_x1 = center_px - new_width / 2
            new_y1 = center_py - new_height / 2
            new_x2 = center_px + new_width / 2
            new_y2 = center_py + new_height / 2

            self.canvas.coords(rect_id, new_x1, new_y1, new_x2, new_y2)
            self.canvas.tag_raise(rect_id)

            # Change color temporarily (becomes persistent highlight)
            self.canvas.itemconfig(rect_id, fill="#FFFF00", outline="orange", width=2)

            # Next step
            self.root.after(30, lambda: bounce_step(step + 1, max_steps))

        bounce_step(0)
    
    def log(self, message, prefix="INFO"):
        """Add message to log"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {prefix}: {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_log(self):
        """Clear log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log("Log cleared", "SYSTEM")
    
    def reset_field(self):
        """Reset field visualization"""
        self.canvas.delete("all")
        self.zona_biru_grids.clear()
        self.zona_merah_grids.clear()
        self.grid_rectangles.clear()
        self.create_field()
        self.create_grids()
        # Apply current visual scale to newly created items so the view stays consistent
        if self.applied_scale != 1.0:
            factor = self.applied_scale
            self.canvas.scale("all", 0, 0, factor, factor)
            self.update_scrollregion()
        self.log("Field reset", "SYSTEM")
    
    def export_grid_data(self):
        """Export grid data to file"""
        try:
            with open("/tmp/grid_data.txt", "w") as f:
                f.write("BLUE ZONE GRIDS\n")
                f.write("=" * 50 + "\n")
                for grid in self.zona_biru_grids:
                    f.write(f"Grid ({grid['row']},{grid['col']}): Center=({grid['center_x']}, {grid['center_y']}) mm\n")
                
                f.write("\n\nRED ZONE GRIDS\n")
                f.write("=" * 50 + "\n")
                for grid in self.zona_merah_grids:
                    f.write(f"Grid ({grid['row']},{grid['col']}): Center=({grid['center_x']}, {grid['center_y']}) mm\n")
            
            self.log("Grid data exported to /tmp/grid_data.txt", "SYSTEM")
            messagebox.showinfo("Export", "Grid data exported to /tmp/grid_data.txt")
        except Exception as e:
            self.log(f"Export failed: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel zoom"""
        # Determine zoom direction
        if event.num == 5 or event.delta < 0:
            zoom_factor = 0.9  # Zoom out
        else:
            zoom_factor = 1.1  # Zoom in
        
        # Apply zoom
        self.zoom_level *= zoom_factor
        self.zoom_level = max(0.5, min(3.0, self.zoom_level))  # Clamp between 0.5x and 3x
        
        # Update display
        self.update_zoom()
        self.zoom_label.config(text=f"Zoom: {int(self.zoom_level * 100)}%")
        self.log(f"Zoom: {int(self.zoom_level * 100)}%", "INFO")
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.zoom_level = 1.0
        self.update_zoom()
        self.zoom_label.config(text=f"Zoom: 100%")
        self.log("Zoom reset to 100%", "INFO")
    
    def update_zoom(self):
        """Update canvas scale visually without redrawing items.

        Uses canvas.scale to scale existing items by the factor needed to go from
        the previously applied scale to the desired self.zoom_level. This preserves
        item IDs and internal state (grids, animations) and avoids duplications.
        """
        # compute factor relative to currently applied visual scale
        if self.applied_scale == 0:
            self.applied_scale = 1.0
        factor = self.zoom_level / self.applied_scale
        if factor == 1.0:
            return

        # Scale all canvas items around origin (0,0)
        self.canvas.scale("all", 0, 0, factor, factor)
        self.applied_scale = self.zoom_level

        # Update scroll region using bbox for robust bounds
        self.update_scrollregion()
    
    def update_scrollregion(self):
        """Update canvas scrollregion to fit all items robustly.

        This uses the canvas bbox('all') when available to compute tight bounds
        and falls back to a default field-sized region if nothing is drawn.
        """
        bbox = self.canvas.bbox("all")
        if bbox:
            x1, y1, x2, y2 = bbox
            # ensure offsets and add small padding
            padding = 20
            x1 = min(0, x1)
            y1 = min(0, y1)
            try:
                self.canvas.config(scrollregion=(x1, y1, x2 + padding, y2 + padding))
            except Exception:
                # Fallback to safe defaults
                canvas_width = int(self.FIELD_WIDTH * self.SCALE * self.applied_scale) + 20
                canvas_height = int(self.FIELD_HEIGHT * self.SCALE * self.applied_scale) + 20
                self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        else:
            canvas_width = int(self.FIELD_WIDTH * self.SCALE * self.applied_scale) + 20
            canvas_height = int(self.FIELD_HEIGHT * self.SCALE * self.applied_scale) + 20
            self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

    def create_options_widgets(self):
        if self.options_widgets_created:
            return
        self.options_widgets_created = True

        # Layout: left side controls for side and areas, right side for publish modes
        left_container = tk.Frame(self.options_frame)
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tambahkan canvas dan scrollbar untuk area checkboxes
        left_canvas = tk.Canvas(left_container, width=220, height=260)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scrollbar = tk.Scrollbar(left_container, orient=tk.VERTICAL, command=left_canvas.yview)
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left = tk.Frame(left_canvas)
        left_canvas.create_window((0,0), window=left, anchor="nw")

        def on_configure(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        left.bind("<Configure>", on_configure)

        right = tk.Frame(self.options_frame)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Side selection
        tk.Label(left, text="Side:", font=("Arial", 9, "bold")).pack(anchor="w")
        tk.Radiobutton(left, text="BLUE", variable=self.side_choice, value="BLUE", command=lambda: self._on_side_change('BLUE')).pack(anchor="w")
        tk.Radiobutton(left, text="RED", variable=self.side_choice, value="RED", command=lambda: self._on_side_change('RED')).pack(anchor="w")

        # Area toggles
        tk.Label(left, text="Areas (enable to add walls):", font=("Arial", 9, "bold")).pack(anchor="w", pady=(8,0))
        tk.Checkbutton(left, text="MEIHUA (BLUE)", variable=self.meihua_blue_var, command=lambda: self.on_area_toggle('meihua_blue_enabled', self.meihua_blue_var.get())).pack(anchor="w")
        tk.Checkbutton(left, text="ARENA (BLUE)", variable=self.arena_blue_var, command=lambda: self.on_area_toggle('arena_blue_enabled', self.arena_blue_var.get())).pack(anchor="w")
        tk.Checkbutton(left, text="MEIHUA (RED)", variable=self.meihua_red_var, command=lambda: self.on_area_toggle('meihua_red_enabled', self.meihua_red_var.get())).pack(anchor="w")
        tk.Checkbutton(left, text="ARENA (RED)", variable=self.arena_red_var, command=lambda: self.on_area_toggle('arena_red_enabled', self.arena_red_var.get())).pack(anchor="w")

        # Draw overlays when area vars change (visual borders)
        try:
            self.meihua_blue_var.trace_add('write', lambda *args: self._on_area_var_changed('meihua_blue'))
            self.arena_blue_var.trace_add('write', lambda *args: self._on_area_var_changed('arena_blue'))
            self.meihua_red_var.trace_add('write', lambda *args: self._on_area_var_changed('meihua_red'))
            self.arena_red_var.trace_add('write', lambda *args: self._on_area_var_changed('arena_red'))
        except Exception:
            try:
                self.meihua_blue_var.trace('w', lambda *args: self._on_area_var_changed('meihua_blue'))
                self.arena_blue_var.trace('w', lambda *args: self._on_area_var_changed('arena_blue'))
                self.meihua_red_var.trace('w', lambda *args: self._on_area_var_changed('meihua_red'))
                self.arena_red_var.trace('w', lambda *args: self._on_area_var_changed('arena_red'))
            except Exception:
                pass

        # Right-side: publishing modes
        tk.Label(right, text="Publish Mode:", font=("Arial", 9, "bold")).pack(anchor="w")
        tk.Button(right, text="Place Robot (click canvas)", command=self.enable_place_robot).pack(fill=tk.X, pady=2)
        tk.Checkbutton(right, text="Ignore Grid (publish anywhere on click)", variable=self.ignore_grid_var, command=lambda: self.log(f"Ignore grid mode: {self.ignore_grid_var.get()}", "SYSTEM")).pack(anchor="w", pady=(6,0))
        tk.Button(right, text="Clear Robot Marker", command=self.clear_robot_marker).pack(fill=tk.X, pady=(8,0))

    def toggle_options(self):
        """Show/hide the expandable options panel."""
        if self.options_expanded:
            self.options_frame.pack_forget()
            self.options_expanded = False
            self.log("Options hidden", "SYSTEM")
        else:
            self.create_options_widgets()
            self.options_frame.pack(fill=tk.X, padx=5, pady=(0,5))
            self.options_expanded = True
            self.log("Options shown", "SYSTEM")

    def on_area_toggle(self, param_name, enabled):
        """Toggle area parameter: publish control message to simworld so area borders are added/removed."""
        self.log(f"Area toggle {param_name} -> {enabled}", "SYSTEM")
        if HAS_ROS and self.ros_initialized:
            try:
                # Publish a simple control string 'name:true' or 'name:false'
                if getattr(self, 'sim_area_pub', None):
                    msg = String()
                    msg.data = f"{param_name}:{'true' if enabled else 'false'}"
                    self.sim_area_pub.publish(msg)
                    self.log(f"Published area toggle to simworld: {msg.data}", "ROS")
                else:
                    # Fallback: set local parameter (no effect on simworld)
                    p = Parameter(param_name, enabled)
                    self.node.set_parameters([p])
                    self.log(f"Set local parameter {param_name} = {enabled}", "ROS")
            except Exception as e:
                self.log(f"Failed to toggle area {param_name}: {e}", "ERROR")

    def enable_place_robot(self):
        """Enable single-click place robot mode (next click places robot)."""
        self.place_robot_mode = True
        self.status_label.config(text="Click on canvas to place robot...")
        self.log("Place-robot mode enabled (next click will place robot)", "SYSTEM")
        # Also set the side in the status (helpful reminder)
        self._update_side_indicator()

    def clear_robot_marker(self):
        """Remove any existing robot marker and heading indicator from canvas."""
        if self.robot_marker_id:
            try:
                self.canvas.delete(self.robot_marker_id)
            except Exception:
                pass
            self.robot_marker_id = None
        if getattr(self, 'robot_heading_id', None):
            try:
                self.canvas.delete(self.robot_heading_id)
            except Exception:
                pass
            self.robot_heading_id = None
        self.log("Robot marker cleared", "SYSTEM")

    def _on_area_var_changed(self, name):
        """Area enable/disable: tidak ada visual outline di GUI, hanya kontrol ke simworld."""
        pass

    def _draw_area_outline(self, name, color):
        pass

    def _clear_area_outline(self, name):
        pass

    def _on_side_change(self, side):
        try:
            self.side_choice.set(side)
        except Exception:
            pass
        self.log(f"Side set to {self.side_choice.get()}", "SYSTEM")
        self._update_side_indicator()
        # Update robot marker warna jika ada
        if self.robot_marker_id:
            mx, my = self._last_pose if self._last_pose else (6050, 6050)
            self._update_robot_marker_from_pose(mx, my, 0.0)

    def _update_side_indicator(self):
        """Change the side indicator label color and text based on side_choice."""
        side = self.side_choice.get()
        if side == 'BLUE':
            self.side_indicator.config(text='BLUE', bg=self.BLUE_SIDE_MAIN, fg='black')
        else:
            self.side_indicator.config(text='RED', bg=self.RED_SIDE_MAIN, fg='black')

    def on_pan_start(self, event):
        """Start panning using canvas.scan_mark for smooth dragging."""
        # Prefer the canvas scan API which handles scaling and smooth dragging.
        try:
            self.canvas.scan_mark(event.x, event.y)
        except Exception:
            # Fallback to manual tracking if scan_mark isn't available for some widget
            self.pan_start = (event.x, event.y)
        self.canvas.config(cursor="hand2")
    
    def on_pan_motion(self, event):
        """Handle panning motion using canvas.scan_dragto for smooth movement."""
        # Use scan_dragto when possible; it correctly accounts for widget scaling
        try:
            self.canvas.scan_dragto(event.x, event.y, gain=1)
        except Exception:
            if self.pan_start:
                dx = event.x - self.pan_start[0]
                dy = event.y - self.pan_start[1]

                # Move canvas view (fallback)
                self.canvas.xview_scroll(int(-dx / 5), "units")
                self.canvas.yview_scroll(int(-dy / 5), "units")

                self.pan_start = (event.x, event.y)
    
    def on_pan_end(self, event):
        """End panning"""
        self.pan_start = None
        self.canvas.config(cursor="cross")

    def _ros_spin_loop(self):
        """Background loop that periodically spins rclpy to process callbacks."""
        try:
            while getattr(self, '_ros_running', False):
                try:
                    rclpy.spin_once(self.node, timeout_sec=0.1)
                except Exception:
                    # Keep spinning until shutdown; log occasionally
                    time.sleep(0.05)
            # cleanup on exit
        except Exception:
            pass

    def _on_close(self):
        """Handle GUI close event: stop ROS spin and shutdown node cleanly."""
        # Stop ros spin
        try:
            self._ros_running = False
        except Exception:
            pass
        # Give spin thread a moment to exit
        try:
            if getattr(self, '_ros_spin_thread', None):
                self._ros_spin_thread.join(timeout=1.0)
        except Exception:
            pass
        # Destroy ROS node and shutdown rclpy
        try:
            if getattr(self, 'node', None):
                try:
                    self.node.destroy_node()
                except Exception:
                    pass
            try:
                rclpy.shutdown()
            except Exception:
                pass
        except Exception:
            pass
        # Then close the Tk mainloop
        try:
            self.root.quit()
        except Exception:
            pass


def main():
    """Main entry point"""
    root = tk.Tk()
    root.geometry("1400x800")
    
    app = FieldVisualizer(root)
    root.mainloop()
    
    # Cleanup ROS
    if app.ros_initialized:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
