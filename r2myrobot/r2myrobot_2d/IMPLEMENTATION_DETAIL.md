# Dokumentasi Implementasi R2MyRobot 2D Field GUI

## Overview

Aplikasi ini mengimplementasikan visualisasi lapangan 2D untuk R2MyRobot dengan spesifikasi detail dari file `asr26lap.txt`. Aplikasi dibangun dengan Python 3 menggunakan tkinter untuk GUI dan ROS2 untuk komunikasi inter-process.

---

## Spesifikasi Implementasi Detail

### 1. Dimensi Lapangan

**Lapangan Keseluruhan:**
- Lebar (Width): 12100 mm
- Tinggi (Height): 12150 mm
- Skala display: 1 mm = 0.05 pixel (sehingga lapangan 12100x12150 mm = 605x607.5 pixel)

### 2. Sisi Biru (Blue Side)

**Area Utama: (50, 50) → (6050, 12050)**

#### Layer struktur (dari bawah ke atas):
1. **Layer 1 (Paling Bawah)**: Rectangle #81D2D6 dari (50,50) ke (6050,12050)
2. **Layer 2**: Rectangle #949EA0 dari (50,2020) ke (6050,9550)
3. **Layer 3**: Rectangle #80BFD1 dari (50,2050) ke (6050,9500) - **Area Grid** 
4. **Layer 4**: Rectangle #2A7138 (zona hijau) dari (1250,3250) ke (4850,8060)
5. **Layer 5-6**: Dekoratif (warna biru, coklat, kuning, beige)

#### Grid Zona Biru:
- **Area**: (50, 2050) → (6050, 9250)
- **Grid Size**: 1200 x 1200 mm
- **Jumlah Grid**: 5 kolom × 6 baris = 30 grid
- **Kolom**: 0-4
- **Baris**: 0-5
- **Array Name**: `zona2gridbiru`
- **Koordinat Perhitungan**: Dari start point (50, 2050)

### 3. Sisi Merah (Red Side)

**Area Utama: (6100, 50) → (12100, 12050)**

#### Layer struktur (mirror dari blue side):
1. **Layer 1**: Rectangle #FEBAA3 dari (6100,50) ke (12100,12050)
2. **Layer 2**: Rectangle #949EA0 dari (6100,2020) ke (12100,9550)
3. **Layer 3**: Rectangle #ECA297 dari (6100,2050) ke (12100,9500) - **Area Grid**
4. **Layer 4**: Rectangle #2A7138 (zona hijau) dari (7300,3250) ke (10900,8060)
5. **Layer 5-6**: Dekoratif (warna merah, coklat, kuning, beige)

#### Grid Zona Merah:
- **Area**: (6100, 2050) → (12100, 9250)
- **Grid Size**: 1200 x 1200 mm
- **Jumlah Grid**: 5 kolom × 6 baris = 30 grid
- **Kolom**: 0-4
- **Baris**: 0-5
- **Array Name**: `zona2gridmerah`
- **Koordinat Perhitungan**: Dari start point (6100, 2050)

### 4. Elemen Tengah (Center Elements)

**Bar Tengah (Brown/Coklat):**
- Rectangle dari (5925, 400) ke (6225, 1600)
- Warna: #9B5F00

**Area Beige Tengah Bawah:**
- Rectangle dari (5925, 9940) ke (6225, 11560)
- Warna: #FCF7F5

**Black Dots (Titik Hitam Tebal):**
- Zona Tengah: (6075, 500), (6075, 700), (6075, 900), (6075, 1100), (6075, 1300), (6075, 1500)
- Zona Biru Top: (2350, 200), (2550, 200), (2750, 200), (2950, 200)
- Zona Merah Top: (9200, 200), (9400, 200), (9600, 200), (9800, 200)

---

## Kode Struktur

### File Utama

```
r2myrobot_2d/
├── __init__.py                      # Package initialization
├── main.py                          # GUI application (utama)
├── __main__.py                      # Module runner
└── point_listener_example.py        # Example ROS2 subscriber
```

### Class: FieldVisualizer

**Inheritance**: None (standalone)

**Inisialisasi**:
```python
app = FieldVisualizer(root)  # root = tk.Tk()
```

**Key Attributes**:
- `self.canvas`: tkinter Canvas untuk drawing
- `self.zona_biru_grids`: List[GridInfo] untuk zona biru
- `self.zona_merah_grids`: List[GridInfo] untuk zona merah
- `self.grid_rectangles`: Dict[canvas_id → GridInfo]
- `self.publisher`: ROS2 Publisher ke topic `2dmap_mypoint`

**Key Methods**:

| Method | Purpose |
|--------|---------|
| `create_field()` | Render semua layer lapangan |
| `create_grids()` | Generate grid untuk kedua zona |
| `create_zone_grid()` | Generate grid single zone |
| `draw_rect_mm(x1,y1,x2,y2,color,fill)` | Draw rectangle dari mm coords |
| `draw_dot_mm(x,y,radius,color)` | Draw dot dari mm coords |
| `on_canvas_click(event)` | Handle canvas mouse click |
| `on_grid_click(grid_info)` | Handle grid click dengan publish |
| `animate_grid_bounce(rect_id)` | Animasi bounce effect |
| `mm_to_pixels(x,y)` | Konversi mm → pixels |
| `pixels_to_mm(x,y)` | Konversi pixels → mm |
| `log(message, prefix)` | Tambah entry ke log panel |

### GridInfo Data Structure

Setiap grid memiliki informasi lengkap:

```python
{
    "id": int,              # Unique ID dalam zona (0-29)
    "zone": str,            # "BLUE" atau "RED"
    "rect_id": int,         # Canvas rectangle ID untuk event handling
    "x1": int,              # Top-left X (mm)
    "y1": int,              # Top-left Y (mm)
    "x2": int,              # Bottom-right X (mm)
    "y2": int,              # Bottom-right Y (mm)
    "center_x": int,        # Center point X (mm)
    "center_y": int,        # Center point Y (mm)
    "row": int,             # Row index (0-5)
    "col": int              # Column index (0-4)
}
```

---

## Event Flow

### 1. Grid Click Event

```
User clicks on Canvas
    ↓
on_canvas_click(event)
    ↓
Find overlapping grid rectangle
    ↓
on_grid_click(grid_info)
    ├─ Log entry dengan timestamp
    ├─ Publish (x,y) ke ROS topic "2dmap_mypoint"
    ├─ Animate bounce effect
    └─ Update status label
```

### 2. Animation Flow

```
animate_grid_bounce(rect_id)
    ├─ Initial state: original size
    ├─ Step 1-10: Scale 1.0 → 0.85 → 1.0 (bounce)
    │   ├─ Color: yellow (#FFFF00)
    │   ├─ Outline: orange
    │   └─ Width: 2px
    ├─ Each step: 30ms delay
    └─ Final: Restore to original
```

### 3. ROS2 Publishing

```
on_grid_click()
    ├─ Check: if self.ros_initialized
    ├─ Create message: String(data="x,y")
    ├─ Publish to "2dmap_mypoint"
    └─ Log: "Published to 2dmap_mypoint: x,y"
```

---

## Color Mapping

### Blue Side Colors
```python
BLUE_SIDE_BG = "#81D2D6"        # Light cyan (layer 1)
BLUE_SIDE_OVERLAY = "#949EA0"   # Gray (layer 2)
BLUE_SIDE_MAIN = "#80BFD1"      # Blue (layer 3 - grid area)
BLUE_SIDE_GREEN = "#2A7138"     # Dark green
BLUE_SIDE_BLUE = "#3100FF"      # Pure blue
BLUE_SIDE_BROWN = "#9B5F00"     # Brown
BLUE_SIDE_YELLOW = "#E6E22B"    # Yellow
BLUE_SIDE_BEIGE = "#C0BDB5"     # Beige
```

### Red Side Colors
```python
RED_SIDE_BG = "#FEBAA3"         # Peach (layer 1)
RED_SIDE_OVERLAY = "#949EA0"    # Gray (layer 2)
RED_SIDE_MAIN = "#ECA297"       # Light salmon (layer 3 - grid area)
RED_SIDE_GREEN = "#2A7138"      # Dark green (same as blue)
RED_SIDE_RED = "#DF2222"        # Pure red
RED_SIDE_BROWN = "#9B5F00"      # Brown (same as blue)
RED_SIDE_YELLOW = "#E6E22B"     # Yellow (same as blue)
RED_SIDE_BEIGE = "#C0BDB5"      # Beige (same as blue)
```

---

## ROS2 Integration

### Topic: `2dmap_mypoint`
- **Message Type**: `std_msgs/String`
- **Content Format**: `"x,y"` (contoh: `"3225,5525"`)
- **Units**: Millimeters (mm)
- **Publisher**: `r2myrobot_2d_gui` node
- **Publish Rate**: On-demand (saat user klik grid)

### Listener Example

```bash
# Terminal 1: Jalankan GUI
r2myrobot_2d_gui

# Terminal 2: Listen to topic
ros2 topic echo 2dmap_mypoint

# Terminal 3: Subscribe dengan Python
python3 r2myrobot_2d/point_listener_example.py
```

---

## GUI Layout

```
┌─────────────────────────────────────────────────────┐
│  R2MyRobot 2D Field Visualization                  │
├──────────────────────┬──────────────────────────────┤
│                      │  LOG                         │
│                      │  ─────────────────────────   │
│   CANVAS             │  [HH:MM:SS] SYSTEM: ...     │
│   (605 x 607 px)     │  [HH:MM:SS] CLICK: ...      │
│   FIELD VIEW         │  [HH:MM:SS] ROS: ...        │
│                      │                              │
│                      │  (Scrollable)                │
├──────────────────────┴──────────────────────────────┤
│ Nav: [Clear Log] [Reset] [Export] [Exit]   Ready  │
└─────────────────────────────────────────────────────┘
```

### Canvas
- Ukuran: ~605 x 607 pixel (scaled dari 12100 x 12150 mm)
- Background: #C9A792 (base field color)
- Cursor: Cross (untuk precision pointing)

### Log Panel
- Scrolled text widget
- Max visible lines: ~35 baris
- Auto-scroll to bottom
- Read-only (for safety)

### Navigation Bar
- Clear Log: Hapus semua log entries
- Reset Field: Re-render field dan grid
- Export Grid Data: Save grid info ke file
- Exit: Terminate aplikasi

---

## Koordinat Sistem

### Definisi
- **Origin (0,0)**: Top-left dari lapangan
- **X-axis**: Horizontal (left to right)
- **Y-axis**: Vertical (top to bottom)
- **Unit**: Millimeters (mm)

### Zona Mapping

**Blue Zone (Sisi Kiri)**:
- Grid area: X=[50...6050], Y=[2050...9250]
- Grid count: 5×6 = 30 grids
- Grid (0,0) center: (650, 2650) mm
- Grid (4,5) center: (5450, 8850) mm

**Red Zone (Sisi Kanan)**:
- Grid area: X=[6100...12100], Y=[2050...9250]
- Grid count: 5×6 = 30 grids
- Grid (0,0) center: (6700, 2650) mm
- Grid (4,5) center: (11500, 8850) mm

---

## Logging System

### Log Format
```
[HH:MM:SS] PREFIX: Message
```

### Prefix Types
| Prefix | Meaning |
|--------|---------|
| `SYSTEM` | System events (startup, field created, reset) |
| `CLICK` | Grid click events dengan koordinat |
| `ROS` | ROS2 publish/subscribe events |
| `INFO` | General information |
| `ERROR` | Error messages |

### Log Examples
```
[10:30:45] SYSTEM: ROS2 node initialized
[10:30:50] SYSTEM: Creating field...
[10:31:00] SYSTEM: Grids created: 30 blue + 30 red
[10:31:15] CLICK: [BLUE] Grid (2,3) -> Point: (3250, 5525) mm
[10:31:15] ROS: Published to 2dmap_mypoint: 3250,5525
[10:31:20] CLICK: [RED] Grid (1,4) -> Point: (9550, 7125) mm
```

---

## Export Format

File `grid_data.txt`:
```
BLUE ZONE GRIDS
==================================================
Grid (0,0): Center=(650, 2650) mm
Grid (0,1): Center=(650, 3850) mm
...
Grid (4,5): Center=(5450, 8850) mm

RED ZONE GRIDS
==================================================
Grid (0,0): Center=(6700, 2650) mm
Grid (0,1): Center=(6700, 3850) mm
...
Grid (4,5): Center=(11500, 8850) mm
```

---

## Testing

### Unit Tests

Jalankan tests:
```bash
cd /root/myrobot_ws/src/r2myrobot/r2myrobot_2d
python3 -m pytest test/test_gui_logic.py -v
```

Test categories:
- **Coordinate Conversion**: mm ↔ pixels
- **Grid Calculation**: Blue & Red zones
- **Color Verification**: Hexadecimal color codes
- **Constants Validation**: Field dimensions, scale factor

### Manual Testing Checklist

- [ ] GUI window opens correctly
- [ ] All field layers visible with correct colors
- [ ] Grid lines rendered for both zones
- [ ] Click on blue grid → Log shows correct (x,y)
- [ ] Click on red grid → Log shows correct (x,y)
- [ ] Bounce animation plays on click
- [ ] ROS topic receives published points (if ROS installed)
- [ ] Clear Log button works
- [ ] Reset Field button works
- [ ] Export Grid Data creates file
- [ ] Exit button closes app cleanly

---

## Performance Considerations

### Rendering
- Total elements: ~150+ (rectangles, dots, grid lines)
- Canvas refresh: Automatic (tkinter optimized)
- Typical render time: <100ms on modern hardware

### Memory
- GUI overhead: ~50 MB
- Grid storage: ~30 grids × 2 zones × 100 bytes = 6 KB
- Log history: Scrolled text widget (auto-managed)

### Animation
- Bounce animation: 10 steps × 30ms = 300ms per click
- Non-blocking (uses after() callback)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| GUI tidak tampil | Cek DISPLAY variable, ensure X11 forwarding |
| Click tidak terdeteksi | Pastikan mouse di dalam canvas area |
| ROS topic tidak publish | Install rclpy, verify ROS2 setup |
| Log text tidak terlihat | Scroll ke atas di log panel |
| Memory leak | Restart app jika berjalan lama |

---

## Future Enhancements

1. **Robot Visualization**
   - Robot pose overlay pada grid
   - Real-time odometry update
   - Trajectory history

2. **Path Planning**
   - Click-to-click pathfinding
   - Obstacle avoidance visualization
   - Path optimization

3. **Multi-Robot Support**
   - Multiple robot markers
   - Collision detection
   - Formation control

4. **Data Logging**
   - CSV export dari semua clicks
   - Timestamp recording
   - Statistical analysis

5. **Configuration**
   - Load custom field layouts
   - Grid size customization
   - Color theme selection

---

## References

- **asr26lap.txt**: Original field specification
- **Python tkinter**: GUI framework
- **ROS2**: Middleware for robotics
- **std_msgs**: Standard ROS2 message types

---

**Version**: 1.0  
**Author**: R2MyRobot Team  
**Date**: January 2026  
**License**: Apache 2.0
