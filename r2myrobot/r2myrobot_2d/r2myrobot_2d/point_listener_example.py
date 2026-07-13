#!/usr/bin/env python3
"""
Example ROS2 subscriber untuk mendengarkan 2dmap_mypoint topic
"""

import rclpy
from std_msgs.msg import String


def point_callback(msg):
    """Callback function when point is published"""
    try:
        x, y = map(int, msg.data.split(','))
        print(f"Received point from 2D GUI: X={x} mm, Y={y} mm")
        
        # Lakukan sesuatu dengan koordinat (misal: gerakkan robot ke titik tersebut)
        # Contoh: move_robot_to(x, y)
        
    except ValueError:
        print(f"Invalid message format: {msg.data}")


def main():
    rclpy.init()
    node = rclpy.create_node('r2myrobot_2d_point_listener')
    
    print("=" * 60)
    print("R2MyRobot 2D GUI Point Listener")
    print("=" * 60)
    print("Listening to topic: map_2d_mypoint")
    print("Waiting for points from GUI...")
    print("=" * 60)
    
    # Create subscription
    subscription = node.create_subscription(
        String,
        'map_2d_mypoint',
        point_callback,
        10
    )
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\nShutdown requested")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
