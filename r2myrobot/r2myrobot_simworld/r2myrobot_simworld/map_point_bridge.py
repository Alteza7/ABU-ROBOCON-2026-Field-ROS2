#!/usr/bin/env python3
"""Bridge node: map_2d_mypoint (String "x,y" in mm) -> Pose2D + PoseStamped

Publishes:
 - /r2myrobot/pose2d (geometry_msgs/Pose2D)
 - /r2myrobot/pose_stamped (geometry_msgs/PoseStamped)

Subscribes:
 - map_2d_mypoint (std_msgs/String)

Behavior:
 - Parses "x,y" (mm), converts to meters, publishes Pose2D and PoseStamped in frame 'odom'.
"""
import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Pose2D, PoseStamped, Pose, Quaternion


def quaternion_from_euler(roll, pitch, yaw):
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    return (x, y, z, w)


class MapPointBridge(Node):
    def __init__(self):
        super().__init__('map_point_bridge')
        self.declare_parameter('input_topic', 'map_2d_mypoint')
        self.declare_parameter('pose2d_topic', '/r2myrobot/pose2d')
        self.declare_parameter('pose_stamped_topic', '/r2myrobot/pose_stamped')
        self.declare_parameter('frame_id', 'odom')

        self.input_topic = self.get_parameter('input_topic').get_parameter_value().string_value
        self.pose2d_topic = self.get_parameter('pose2d_topic').get_parameter_value().string_value
        self.pose_stamped_topic = self.get_parameter('pose_stamped_topic').get_parameter_value().string_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value

        self.sub = self.create_subscription(String, self.input_topic, self.cb, 10)
        self.pose2d_pub = self.create_publisher(Pose2D, self.pose2d_topic, 10)
        self.ps_pub = self.create_publisher(PoseStamped, self.pose_stamped_topic, 10)

        self.get_logger().info(f"MapPointBridge listening on '{self.input_topic}' -> publishing Pose2D:'{self.pose2d_topic}', PoseStamped:'{self.pose_stamped_topic}'")

    def cb(self, msg: String):
        data = msg.data.strip()
        try:
            x_str, y_str = data.split(',')
            x_mm = float(x_str.strip())
            y_mm = float(y_str.strip())
        except Exception as e:
            self.get_logger().warning(f"Invalid map_2d_mypoint message '{data}': {e}")
            return

        # convert mm to meters
        x_m = x_mm / 1000.0
        y_m = y_mm / 1000.0

        p = Pose2D()
        p.x = x_m
        p.y = y_m
        p.theta = 0.0
        self.pose2d_pub.publish(p)

        ps = PoseStamped()
        ps.header.stamp = self.get_clock().now().to_msg()
        ps.header.frame_id = self.frame_id
        ps.pose = Pose()
        ps.pose.position.x = x_m
        ps.pose.position.y = y_m
        q = quaternion_from_euler(0, 0, 0.0)
        ps.pose.orientation = Quaternion(x=q[0], y=q[1], z=q[2], w=q[3])
        self.ps_pub.publish(ps)

        self.get_logger().info(f"Bridged point {x_mm},{y_mm} mm -> ({x_m},{y_m}) m")


def main(args=None):
    rclpy.init(args=args)
    node = MapPointBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
