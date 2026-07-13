# R2MyRobot 2D Field Visualization GUI

Aplikasi GUI tkinter untuk visualisasi lapangan 2D R2MyRobot dengan grid interaktif yang sesuai dengan spesifikasi di `asr26lap.txt`.

## Fitur Utama

### 1. Visualisasi Lapangan
- Lapangan berukuran 12100 x 12150 mm dengan detail sesuai spesifikasi
- **Sisi Biru (Blue Side)**: Area dari (50,50) hingga (6050,12050)
  - Background #81D2D6
  - Multiple overlay layers dengan warna berbeda
  - Elemen dekoratif (zona hijau, zona biru, zona kuning, dll)
  
- **Sisi Merah (Red Side)**: Area dari (6100,50) hingga (12100,12050)
  - Background #FEBAA3 
  - Mirrored design dengan warna yang sesuai
  - Elemen dekoratif yang sama dengan sisi biru

- **Elemen Tengah (Center)**:
  - Bar coklat vertikal (#9B5F00) dari (5925,400) ke (6225,1600)
  - Area beige (#FCF7F5) dari (5925,9940) ke (6225,11560)
  - Black dots di berbagai posisi

### 2. Grid Interaktif

**Zona Grid Biru (Zona2GridBiru)**:
- Area: (50, 2050) ke (6050, 9250)
- Grid size: 1200 x 1200 mm
- Total grid: 5 kolom x 6 baris = 30 grid

**Zona Grid Merah (Zona2GridMerah)**:
- Area: (6100, 2050) ke (12100, 9250)
- Grid size: 1200 x 1200 mm
- Total grid: 5 kolom x 6 baris = 30 grid

### 3. Interaktivitas

**Klik Grid**:
- Klik pada grid akan menampilkan bounce animation
- Menampilkan titik pusat grid dalam format (x, y) mm
- Log otomatis ke panel log dengan timestamp

**Animasi Bounce**:
- Efek visual ketika grid diklik
- Grid berubah warna menjadi kuning dengan outline orange
- Scaling effect untuk bounce animation

### 4. Panel Log

- Menampilkan semua event dengan timestamp
- Prefix: `INFO`, `SYSTEM`, `CLICK`, `ROS`, `ERROR`
- Scroll otomatis ke entry terbaru
- Tombol `Clear Log` untuk membersihkan

### 5. Navigation Bar

- **Clear Log**: Menghapus semua log
- **Reset Field**: Mereset visualisasi lapangan dan grid
- **Export Grid Data**: Export data grid ke file `/tmp/grid_data.txt`
- **Exit**: Keluar aplikasi

### 6. ROS2 Integration (Optional)

Jika ROS2 terinstall, aplikasi akan:
- Menginisialisasi ROS2 node bernama `r2myrobot_2d_gui`
- Publish titik (x, y) ke topic **`2dmap_mypoint`**
- Format publish: `"x,y"` (contoh: `"3225,5525"`)

## Instalasi & Menjalankan

### Prerequisites
```bash
pip install tkinter  # Biasanya sudah terinstall di Python
```

### Install Package
```bash
cd /root/myrobot_ws
colcon build --packages-select r2myrobot_2d
source install/setup.bash
```

### Jalankan GUI

**Opsi 1: Menggunakan entry point**
```bash
r2myrobot_2d_gui
```

**Opsi 2: Menjalankan langsung**
```bash
python3 -m r2myrobot_2d.main
```

**Opsi 3: Dari direktori source**
```bash
cd /root/myrobot_ws/src/r2myrobot/r2myrobot_2d
python3 r2myrobot_2d/main.py
```

## Struktur Kode

### Class: `FieldVisualizer`

**Attributes:**
- `FIELD_WIDTH` / `FIELD_HEIGHT`: Dimensi lapangan dalam mm
- `SCALE`: Faktor skala mm ke pixel (0.05)
- `GRID_SIZE`: Ukuran grid dalam mm (1200)
- `zona_biru_grids`: List grid zona biru
- `zona_merah_grids`: List grid zona merah
- `grid_rectangles`: Dictionary mapping canvas_id ke grid info

**Methods Utama:**
- `create_field()`: Membuat visualisasi lapangan
- `create_grids()`: Membuat grid untuk kedua zona
- `create_zone_grid()`: Membuat grid untuk zone spesifik
- `draw_rect_mm()`: Draw rectangle dari koordinat mm
- `draw_dot_mm()`: Draw dot dari koordinat mm
- `on_canvas_click()`: Handle klik canvas
- `on_grid_click()`: Handle klik grid dengan logging & publishing
- `animate_grid_bounce()`: Animasi bounce effect
- `log()`: Tambah entry ke log panel

## Grid Data Structure

Setiap grid memiliki struktur:
```python
{
    "id": int,                      # Grid ID dalam zona
    "zone": str,                    # "BLUE" atau "RED"
    "rect_id": int,                 # Canvas rectangle ID
    "x1": int, "y1": int,          # Top-left corner (mm)
    "x2": int, "y2": int,          # Bottom-right corner (mm)
    "center_x": int,               # Center X coordinate (mm)
    "center_y": int,               # Center Y coordinate (mm)
    "row": int, "col": int         # Grid row & column index
}
```

## ROS2 Topic Specification

**Topic Name**: `2dmap_mypoint`
**Message Type**: `std_msgs/String`
**Format**: `"x,y"` (comma-separated coordinates dalam mm)

**Contoh Subscribe in ROS2**:
```bash
ros2 topic echo 2dmap_mypoint
```

**Contoh Listener in Python**:
```python
import rclpy
from std_msgs.msg import String

def callback(msg):
    x, y = map(int, msg.data.split(','))
    print(f"Received point: ({x}, {y})")

node = rclpy.create_node('listener')
sub = node.create_subscription(String, '2dmap_mypoint', callback, 10)
rclpy.spin(node)
```

## Log Output Format

```
[HH:MM:SS] PREFIX: Message
[10:30:45] SYSTEM: Field created successfully
[10:30:50] CLICK: [BLUE] Grid (2,3) -> Point: (3225, 5525) mm
[10:30:50] ROS: Published to 2dmap_mypoint: 3225,5525
```

## Troubleshooting

### GUI tidak tampil
- Pastikan X11 forwarding aktif jika menggunakan SSH
- Gunakan `export DISPLAY=:0` jika di headless environment

### ROS2 tidak terdeteksi
- Aplikasi akan tetap berjalan tanpa ROS2
- Install ROS2 untuk enable topic publishing

### Grid tidak bisa diklik
- Pastikan mouse pointer di area grid yang valid
- Gradient color mungkin menyebabkan sulit diklik di edge

## Future Enhancements

- [ ] Robot visualization dengan pose tracking
- [ ] Waypoint planning visualizer
- [ ] Grid coloring based on occupancy
- [ ] Real-time odometry display
- [ ] Path recording and playback
- [ ] Multi-robot support
