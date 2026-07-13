# Quick Start Guide - R2MyRobot 2D GUI

## Instalasi Cepat

### 1. Build Package
```bash
cd /root/myrobot_ws
colcon build --packages-select r2myrobot_2d
source install/setup.bash
```

### 2. Jalankan GUI
```bash
r2myrobot_2d_gui
```

**atau**

```bash
python3 -m r2myrobot_2d.main
```

---

## Cara Menggunakan

### 1. Memahami Lapangan
- **Area Biru (Kiri)**: Sisi pertama dengan grid 5×6 = 30 cell
- **Area Merah (Kanan)**: Sisi kedua dengan grid 5×6 = 30 cell
- **Tengah**: Elemen dekoratif (bar coklat dan area beige)

### 2. Mengklik Grid
1. Posisikan mouse ke salah satu grid (cell)
2. Klik untuk memilih grid tersebut
3. Efek bounce animation akan tampil (warna berubah kuning)
4. Koordinat (x, y) akan muncul di LOG panel

### 3. Membaca LOG
```
[10:30:45] SYSTEM: Field created successfully
[10:30:50] CLICK: [BLUE] Grid (2,3) -> Point: (3250, 5525) mm
[10:30:50] ROS: Published to 2dmap_mypoint: 3250,5525
```

- **Timestamp**: [HH:MM:SS]
- **PREFIX**: Jenis event (SYSTEM, CLICK, ROS, ERROR)
- **Data**: Informasi detail event

### 4. Navigasi
- **Clear Log**: Hapus semua log entries
- **Reset Field**: Bersihkan dan render ulang lapangan
- **Export Grid Data**: Save koordinat semua grid ke file
- **Exit**: Keluar aplikasi

---

## Integrasi dengan ROS2

### Opsi 1: Subscribe dari Terminal
```bash
ros2 topic echo 2dmap_mypoint
```

### Opsi 2: Custom Node
```bash
python3 r2myrobot_2d/point_listener_example.py
```

### Opsi 3: Dalam Kode Python
```python
import rclpy
from std_msgs.msg import String

def callback(msg):
    x, y = map(int, msg.data.split(','))
    print(f"Received: ({x}, {y}) mm")

rclpy.init()
node = rclpy.create_node('my_listener')
sub = node.create_subscription(String, '2dmap_mypoint', callback, 10)
rclpy.spin(node)
```

---

## Koordinat Grid

### Zona Biru - Blue Zone
```
Grid layout (5 columns × 6 rows):

     Col:  0      1      2      3      4
Row 0:   [650]  [1850] [3050] [4250] [5450]
Row 1:   [...]  [...]  [...]  [...]  [...]
...
Row 5:   [...]  [...]  [...]  [...]  [...]

All Y coordinates (row):
Row 0: Y = 2650 mm
Row 1: Y = 3850 mm
Row 2: Y = 5050 mm
Row 3: Y = 6250 mm
Row 4: Y = 7450 mm
Row 5: Y = 8650 mm
```

### Zona Merah - Red Zone
```
Grid layout (5 columns × 6 rows):

     Col:  0      1      2      3      4
Row 0:   [6700] [7900] [9100] [10300][11500]
Row 1:   [...]  [...]  [...]  [...]  [...]
...
Row 5:   [...]  [...]  [...]  [...]  [...]

All Y coordinates (row):
Row 0: Y = 2650 mm
Row 1: Y = 3850 mm
Row 2: Y = 5050 mm
Row 3: Y = 6250 mm
Row 4: Y = 7450 mm
Row 5: Y = 8650 mm
```

---

## Common Tasks

### Task 1: Export Grid Data
1. Jalankan GUI
2. Klik "Export Grid Data"
3. File `/tmp/grid_data.txt` akan terbuat
4. Buka file untuk melihat semua koordinat grid

### Task 2: Subscribe All Points
**Terminal 1 - Run GUI:**
```bash
r2myrobot_2d_gui
```

**Terminal 2 - Listen:**
```bash
ros2 topic echo 2dmap_mypoint
```

**Terminal 3 - Click grids dari GUI:**
Setiap click akan muncul di Terminal 2 sebagai:
```
data: "3250,5525"
---
data: "9700,7125"
---
```

### Task 3: Programmatic Usage
```python
#!/usr/bin/env python3

import rclpy
from std_msgs.msg import String

class PointProcessor:
    def __init__(self):
        rclpy.init()
        self.node = rclpy.create_node('point_processor')
        self.sub = self.node.create_subscription(
            String, '2dmap_mypoint', self.process_point, 10
        )
        self.points = []
    
    def process_point(self, msg):
        x, y = map(int, msg.data.split(','))
        self.points.append((x, y))
        print(f"Point {len(self.points)}: ({x}, {y})")
        
        # Do something dengan point
        # Contoh: move_robot_to(x, y)
    
    def run(self):
        rclpy.spin(self.node)

if __name__ == '__main__':
    processor = PointProcessor()
    processor.run()
```

---

## Troubleshooting

### Problem: GUI tidak muncul
**Solusi:**
```bash
# Check DISPLAY
echo $DISPLAY

# If empty, set it
export DISPLAY=:0

# Try again
r2myrobot_2d_gui
```

### Problem: ROS topic tidak terlihat
**Solusi:**
```bash
# Check if ROS is running
ros2 node list

# Check topic list
ros2 topic list

# Monitor topic
ros2 topic echo 2dmap_mypoint
```

### Problem: Click tidak terdeteksi
**Solusi:**
- Pastikan mouse pointer tepat di area grid
- Grid hanya terdeteksi di area grid yang defined
- Coba klik di tengah cell, bukan di edge

### Problem: Memory usage tinggi
**Solusi:**
```bash
# Restart GUI
pkill -f r2myrobot_2d_gui

# Start fresh
r2myrobot_2d_gui
```

---

## Keyboard Shortcuts

Saat ini tidak ada keyboard shortcuts (bisa ditambahkan di future).

---

## Performance Tips

1. **Banyak clicks?** Log akan auto-scroll, bisa lambat
   - Gunakan "Clear Log" untuk reset

2. **Butuh banyak tests?** 
   - Export Grid Data untuk offline analysis

3. **GUI lag?**
   - Tutup aplikasi lain
   - Restart GUI

---

## API Reference

### Topic: 2dmap_mypoint
- **Type**: `std_msgs/String`
- **Format**: `"x,y"`
- **Example**: `"3250,5525"`
- **Units**: millimeters

### Grid Indexing
- **Zona**: "BLUE" atau "RED"
- **Row**: 0-5 (top to bottom)
- **Col**: 0-4 (left to right)
- **Center calculation**: `((x1+x2)/2, (y1+y2)/2)`

### Colors
- Blue side base: `#81D2D6`
- Red side base: `#FEBAA3`
- Grid lines: Black (#000000)
- Bounce effect: Yellow (#FFFF00) with orange outline

---

## FAQ

**Q: Berapa banyak grid yang tersedia?**
A: Total 60 grid (30 zona biru + 30 zona merah)

**Q: Berapa ukuran satu grid?**
A: 1200 x 1200 mm

**Q: Apa unit koordinat?**
A: Millimeters (mm)

**Q: Bisa customize warna?**
A: Bisa, edit `main.py` dan modifikasi color constants

**Q: Bisa export koordinat?**
A: Ya, gunakan "Export Grid Data" → `/tmp/grid_data.txt`

**Q: Bisa multi-robot?**
A: Belum, bisa ditambahkan di versi selanjutnya

**Q: Perlu internet?**
A: Tidak, semuanya local

**Q: Perlu ROS untuk jalan?**
A: Tidak, GUI jalan tanpa ROS (ROS untuk topic publishing optional)

---

## File Locations

```
/root/myrobot_ws/src/r2myrobot/r2myrobot_2d/
├── r2myrobot_2d/
│   ├── main.py                      ← Main GUI application
│   ├── point_listener_example.py    ← Example ROS2 subscriber
│   └── __init__.py
├── test/
│   └── test_gui_logic.py           ← Unit tests
├── README_GUI.md                    ← Detailed documentation
├── IMPLEMENTATION_DETAIL.md         ← Implementation details
├── QUICKSTART.md                    ← This file
├── asr26lap.txt                     ← Original specification
├── setup.py                         ← Package configuration
└── package.xml                      ← ROS package metadata
```

---

## Next Steps

1. ✅ Run GUI: `r2myrobot_2d_gui`
2. ✅ Click beberapa grid untuk testing
3. ✅ Monitor ROS topic: `ros2 topic echo 2dmap_mypoint`
4. ✅ Explore log entries dan UI
5. ✅ Export grid data jika perlu
6. 🔜 Integrate dengan robot movement system
7. 🔜 Add custom callback untuk grid clicks

---

**Happy mapping! 🤖**
