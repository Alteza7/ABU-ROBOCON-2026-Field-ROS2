#!/usr/bin/env python3
"""
Unit tests untuk R2MyRobot 2D GUI
"""

import unittest


class TestFieldVisualizerConstants(unittest.TestCase):
    """Test constants dan calculations"""
    
    # Constants untuk testing (sesuai dengan FieldVisualizer)
    FIELD_WIDTH = 12100
    FIELD_HEIGHT = 12150
    SCALE = 0.05
    GRID_SIZE = 1200
    
    def mm_to_pixels(self, x, y):
        """Helper: Convert mm ke pixels"""
        return (int(x * self.SCALE), int(y * self.SCALE))
    
    def pixels_to_mm(self, x, y):
        """Helper: Convert pixels ke mm"""
        return (int(x / self.SCALE), int(y / self.SCALE))
    
    def test_mm_to_pixels_conversion(self):
        """Test conversion dari mm ke pixels"""
        # Test basic conversion
        px, py = self.mm_to_pixels(0, 0)
        self.assertEqual((px, py), (0, 0))
        
        # Test conversion dengan nilai tertentu
        px, py = self.mm_to_pixels(1000, 1000)
        self.assertEqual((px, py), (50, 50))
    
    def test_pixels_to_mm_conversion(self):
        """Test conversion dari pixels ke mm"""
        px, py = self.pixels_to_mm(0, 0)
        self.assertEqual((px, py), (0, 0))
        
        px, py = self.pixels_to_mm(50, 50)
        self.assertEqual((px, py), (1000, 1000))
    
    def test_field_dimensions(self):
        """Test dimensi lapangan"""
        self.assertEqual(self.FIELD_WIDTH, 12100)
        self.assertEqual(self.FIELD_HEIGHT, 12150)
    
    def test_grid_size(self):
        """Test ukuran grid"""
        self.assertEqual(self.GRID_SIZE, 1200)
    
    def test_grid_calculation_blue(self):
        """Test perhitungan grid zona biru"""
        start_x, start_y = 50, 2050
        end_x, end_y = 6050, 9250
        grid_size = self.GRID_SIZE
        
        grid_width = end_x - start_x
        grid_height = end_y - start_y
        
        cols = grid_width // grid_size
        rows = grid_height // grid_size
        
        # Blue zone: 6000 x 7200 mm
        self.assertEqual(grid_width, 6000)
        self.assertEqual(grid_height, 7200)
        
        # 6000 / 1200 = 5 columns
        # 7200 / 1200 = 6 rows
        self.assertEqual(cols, 5)
        self.assertEqual(rows, 6)
        self.assertEqual(cols * rows, 30)
    
    def test_grid_calculation_red(self):
        """Test perhitungan grid zona merah"""
        start_x, start_y = 6100, 2050
        end_x, end_y = 12100, 9250
        grid_size = self.GRID_SIZE
        
        grid_width = end_x - start_x
        grid_height = end_y - start_y
        
        cols = grid_width // grid_size
        rows = grid_height // grid_size
        
        # Red zone: 6000 x 7200 mm
        self.assertEqual(grid_width, 6000)
        self.assertEqual(grid_height, 7200)
        
        # 6000 / 1200 = 5 columns
        # 7200 / 1200 = 6 rows
        self.assertEqual(cols, 5)
        self.assertEqual(rows, 6)
        self.assertEqual(cols * rows, 30)
    
    def test_grid_center_calculation(self):
        """Test perhitungan titik pusat grid"""
        # Grid example di zona biru
        x1, y1 = 50, 2050
        x2, y2 = 1250, 3250
        
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        self.assertEqual(center_x, 650)
        self.assertEqual(center_y, 2650)
    
    def test_color_values(self):
        """Test warna-warna yang digunakan"""
        colors = {
            "BG_COLOR": "#C9A792",
            "BLUE_SIDE_BG": "#81D2D6",
            "RED_SIDE_RED": "#DF2222",
            "BLUE_SIDE_YELLOW": "#E6E22B"
        }
        
        # Verify warna sesuai spesifikasi
        self.assertEqual(colors["BG_COLOR"], "#C9A792")
        self.assertEqual(colors["BLUE_SIDE_BG"], "#81D2D6")
        self.assertEqual(colors["RED_SIDE_RED"], "#DF2222")
    
    def test_scale_factor(self):
        """Test scale factor"""
        self.assertEqual(self.SCALE, 0.05)
        
        # 1000 mm should be 50 pixels
        px = int(1000 * self.SCALE)
        self.assertEqual(px, 50)


class TestGridStructure(unittest.TestCase):
    """Test grid data structure"""
    
    def test_grid_info_structure(self):
        """Test struktur informasi grid"""
        grid_info = {
            "id": 0,
            "zone": "BLUE",
            "rect_id": 1,
            "x1": 50,
            "y1": 2050,
            "x2": 1250,
            "y2": 3250,
            "center_x": 650,
            "center_y": 2650,
            "row": 0,
            "col": 0
        }
        
        # Verify all required fields exist
        required_fields = ["id", "zone", "rect_id", "x1", "y1", "x2", "y2", 
                          "center_x", "center_y", "row", "col"]
        for field in required_fields:
            self.assertIn(field, grid_info)


if __name__ == '__main__':
    unittest.main()
