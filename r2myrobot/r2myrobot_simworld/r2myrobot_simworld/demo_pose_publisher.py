#!/usr/bin/env python3
"""Demo pose publisher for end-to-end testing.
Publishes Pose2D (and optionally PoseStamped/Odometry) in a circular trajectory.
"""
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose2D, PoseStamped, Pose, Quaternion
from nav_msgs.msg import Odometry
from std_msgs.msg import Header
# Local helper functions instead of tf_transformations

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

class DemoPosePublisher(Node):
    def __init__(self):
        super().__init__('demo_pose_publisher')
        self.declare_parameter('pose_topic', '/r2myrobot/pose2d')
        self.declare_parameter('pose_stamped_topic', '')
        self.declare_parameter('odom_topic', '')
        self.declare_parameter('rate', 10.0)
        self.declare_parameter('radius', 1.0)
        self.declare_parameter('angular_speed', 0.2)

        self.pose_topic = self.get_parameter('pose_topic').get_parameter_value().string_value
        self.pose_stamped_topic = self.get_parameter('pose_stamped_topic').get_parameter_value().string_value
        self.odom_topic = self.get_parameter('odom_topic').get_parameter_value().string_value
        self.rate = float(self.get_parameter('rate').get_parameter_value().double_value)
        self.radius = float(self.get_parameter('radius').get_parameter_value().double_value)
        self.angular_speed = float(self.get_parameter('angular_speed').get_parameter_value().double_value)

        self.pose_pub = self.create_publisher(Pose2D, self.pose_topic, 10)
        if self.pose_stamped_topic:
            self.pose_stamped_pub = self.create_publisher(PoseStamped, self.pose_stamped_topic, 10)
        else:
            self.pose_stamped_pub = None
        if self.odom_topic:
            self.odom_pub = self.create_publisher(Odometry, self.odom_topic, 10)
        else:
            self.odom_pub = None

        self.t = 0.0
        self.timer = self.create_timer(1.0 / max(1.0, self.rate), self.timer_cb)

    def timer_cb(self):
        self.t += 1.0 / max(1.0, self.rate)
        x = self.radius * math.cos(self.angular_speed * self.t)
        y = self.radius * math.sin(self.angular_speed * self.t)
        yaw = math.atan2(y, x)

        p = Pose2D()
        p.x = x
        p.y = y
        p.theta = yaw
        self.pose_pub.publish(p)

        if self.pose_stamped_pub:
            ps = PoseStamped()
            ps.header.stamp = self.get_clock().now().to_msg()
            ps.header.frame_id = 'odom'
            ps.pose = Pose()
            ps.pose.position.x = x
            ps.pose.position.y = y
            q = quaternion_from_euler(0, 0, yaw)
            ps.pose.orientation = Quaternion(x=q[0], y=q[1], z=q[2], w=q[3])
            self.pose_stamped_pub.publish(ps)

        if self.odom_pub:
            odom = Odometry()
            odom.header = Header()
            odom.header.stamp = self.get_clock().now().to_msg()
            odom.header.frame_id = 'odom'
            odom.child_frame_id = 'base_link'
            odom.pose.pose.position.x = x
            odom.pose.pose.position.y = y
            q = tf_transformations.quaternion_from_euler(0, 0, yaw)
            odom.pose.pose.orientation = Quaternion(x=q[0], y=q[1], z=q[2], w=q[3])
            self.odom_pub.publish(odom)

def main(args=None):
    rclpy.init(args=args)
    node = DemoPosePublisher()
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
