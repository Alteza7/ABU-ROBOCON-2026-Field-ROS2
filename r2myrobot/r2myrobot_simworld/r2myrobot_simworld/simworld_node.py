#!/usr/bin/env python3
"""Simple 2D simworld node: raycasting lidar + odom publishing

Publishes:
 - /scan (sensor_msgs/LaserScan)
 - /odom (nav_msgs/Odometry)
Broadcasts TF: odom -> base_link
Subscribes:
 - pose topic (geometry_msgs/Pose2D) name configurable (default: /r2myrobot/pose2d)

World geometry read from parameter `world` as list of polygons (list of list of [x,y]) in meters.
"""
import math
import time
import random
from typing import List, Tuple

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from geometry_msgs.msg import Pose, Quaternion, PoseStamped
from geometry_msgs.msg import PoseWithCovariance, TwistWithCovariance
from geometry_msgs.msg import Pose2D
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Header, String
import tf2_ros
import yaml

# local helper functions to avoid dependency on tf_transformations
def quaternion_from_euler(roll, pitch, yaw):
    """Return quaternion [x,y,z,w] from Euler angles"""
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

def euler_from_quaternion(q):
    """Return roll, pitch, yaw from quaternion-like sequence [x,y,z,w]"""
    x, y, z, w = q
    # roll (x-axis rotation)
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(t0, t1)

    # pitch (y-axis)
    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch = math.asin(t2)

    # yaw (z-axis)
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(t3, t4)

    return (roll, pitch, yaw)


def line_intersection(p1, p2, p3, p4):
    """Return intersection point of segment p1-p2 and ray p3-p4 (as lines). Returns (x,y,t,u) where t is along p1-p2 and u along p3-p4. None if parallel."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-9:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    ix = x1 + t * (x2 - x1)
    iy = y1 + t * (y2 - y1)
    return (ix, iy, t, u)


class SimWorldNode(Node):
    def subtract_segment_by_polygon(self, segments, poly):
        # Untuk setiap segmen, potong bagian yang di dalam poligon
        # Return: list segmen di luar poligon
        result = []
        for seg in segments:
            p1, p2 = seg
            in1 = self.point_in_polygon(p1, poly)
            in2 = self.point_in_polygon(p2, poly)
            if in1 and in2:
                # seluruh segmen di dalam area, buang
                continue
            elif not in1 and not in2:
                # seluruh segmen di luar area, simpan
                result.append((p1, p2))
            else:
                # satu titik di dalam, satu di luar: potong di batas poligon
                # cari titik potong
                min_dist = None
                intersection_pt = None
                for i in range(len(poly)):
                    q1 = poly[i]
                    q2 = poly[(i+1)%len(poly)]
                    inter = line_intersection(p1, p2, q1, q2)
                    if inter is not None:
                        ix, iy, t, u = inter
                        if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
                            dist = (t-0.0)**2
                            if min_dist is None or dist < min_dist:
                                min_dist = dist
                                intersection_pt = (ix, iy)
                if intersection_pt is not None:
                    if in1:
                        # p1 di dalam, p2 di luar
                        result.append((intersection_pt, p2))
                    else:
                        # p1 di luar, p2 di dalam
                        result.append((p1, intersection_pt))
        return result
    def __init__(self):
        super().__init__('simworld_node')

        # Params
        self.declare_parameter('pose_topic', '/r2myrobot/pose2d')
        # optional alternative input topics
        self.declare_parameter('pose_topic_stamped', '')
        self.declare_parameter('pose_topic_odom', '')

        # world param is given as a list of polygon yaml-strings; declare default as string-array
        self.declare_parameter('world', [''])  # list of polygons (string array)
        # Area enable flags (MEIHUA / ARENA for Blue and Red sides)
        self.declare_parameter('meihua_blue_enabled', False)
        self.declare_parameter('arena_blue_enabled', False)
        self.declare_parameter('meihua_red_enabled', False)
        self.declare_parameter('arena_red_enabled', False)
        # Optional polygon lists for the named areas (string-array of YAML lists)
        # Use string-array defaults so YAML string lists map to STRING_ARRAY type
        self.declare_parameter('meihua_blue', [''])
        self.declare_parameter('arena_blue', [''])
        self.declare_parameter('meihua_red', [''])
        self.declare_parameter('arena_red', [''])

        self.declare_parameter('lidar.range_min', 0.05)
        self.declare_parameter('lidar.range_max', 10.0)
        self.declare_parameter('lidar.fov', math.radians(240.0))
        self.declare_parameter('lidar.angle_increment', math.radians(1.0))
        self.declare_parameter('lidar.noise_std', 0.0)
        self.declare_parameter('lidar.update_rate', 10.0)
        self.declare_parameter('publish_scan_frame', 'lidar_link')
        self.declare_parameter('publish_base_frame', 'base_link')

        self.pose_topic = self.get_parameter('pose_topic').get_parameter_value().string_value
        self.pose_topic_stamped = self.get_parameter('pose_topic_stamped').get_parameter_value().string_value
        self.pose_topic_odom = self.get_parameter('pose_topic_odom').get_parameter_value().string_value

        self.world_polygons = self.get_parameter('world').get_parameter_value().string_array_value

        # convert world polygons param to nested list of floats if provided as strings (YAML lists)
        import yaml
        try:
            parsed = []
            if isinstance(self.world_polygons, list):
                for item in self.world_polygons:
                    if isinstance(item, str):
                        # skip empty default placeholder
                        if not item.strip():
                            continue
                        parsed.append(yaml.safe_load(item))
                    else:
                        parsed.append(item)
            # store base world separately; we'll rebuild the runtime world and segments from params
            self.base_world = parsed if parsed else []
        except Exception as e:
            self.get_logger().warning(f"Failed parsing world param: {e}")
            self.base_world = []

        # read area enable flags
        self.meihua_blue_enabled = self.get_parameter('meihua_blue_enabled').get_parameter_value().bool_value
        self.arena_blue_enabled = self.get_parameter('arena_blue_enabled').get_parameter_value().bool_value
        self.meihua_red_enabled = self.get_parameter('meihua_red_enabled').get_parameter_value().bool_value
        self.arena_red_enabled = self.get_parameter('arena_red_enabled').get_parameter_value().bool_value

        def _parse_param_list(param_name):
            raw = self.get_parameter(param_name).get_parameter_value().string_array_value
            parsed_list = []
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, str) and item.strip():
                        try:
                            parsed_list.append(yaml.safe_load(item))
                        except Exception as e:
                            self.get_logger().warning(f"Failed parsing {param_name} item: {e}")
                    elif isinstance(item, list):
                        parsed_list.append(item)
            return parsed_list

        # Build initial world and segment list from params
        self._rebuild_world_from_params()

        # subscribe to external runtime area toggle commands from GUI
        try:
            self.area_sub = self.create_subscription(String, '/r2myrobot/simworld/area_toggle', self.area_toggle_cb, 10)
            self.get_logger().info("Subscribed to /r2myrobot/simworld/area_toggle for runtime area toggles")
        except Exception:
            self.get_logger().warning("Could not subscribe to /r2myrobot/simworld/area_toggle")

        # register parameter change callback to allow updating area enable flags via parameters
        try:
            self.add_on_set_parameters_callback(self._on_set_parameters)
        except Exception:
            pass

        # cmd_vel subscription (optional) and internal velocity state
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('subscribe_cmd_vel', True)
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').get_parameter_value().string_value
        self.subscribe_cmd_vel = self.get_parameter('subscribe_cmd_vel').get_parameter_value().bool_value

        # velocities in robot frame (m/s) and yaw rate (rad/s)
        self.vx = 0.0
        self.vy = 0.0
        self.vyaw = 0.0
        self.last_update_time = self.get_clock().now()

        if self.subscribe_cmd_vel:
            try:
                self.cmd_vel_sub = self.create_subscription(Twist, self.cmd_vel_topic, self.cmd_vel_cb, 10)
                self.get_logger().info(f"Subscribed to cmd_vel on {self.cmd_vel_topic}")
            except Exception:
                self.get_logger().warning(f"Could not subscribe to cmd_vel on {self.cmd_vel_topic}")

        self.range_min = self.get_parameter('lidar.range_min').get_parameter_value().double_value
        self.range_max = self.get_parameter('lidar.range_max').get_parameter_value().double_value
        self.fov = self.get_parameter('lidar.fov').get_parameter_value().double_value
        self.angle_increment = self.get_parameter('lidar.angle_increment').get_parameter_value().double_value
        self.noise_std = self.get_parameter('lidar.noise_std').get_parameter_value().double_value
        self.update_rate = self.get_parameter('lidar.update_rate').get_parameter_value().double_value
        self.scan_frame = self.get_parameter('publish_scan_frame').get_parameter_value().string_value
        self.base_frame = self.get_parameter('publish_base_frame').get_parameter_value().string_value

        # state
        self.pose_x = 0.0
        self.pose_y = 0.0
        self.pose_yaw = 0.0
        self.last_pose_stamp = self.get_clock().now()

        # publishers
        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        # subscriber: Pose2D
        self.pose_sub = None
        try:
            self.pose_sub = self.create_subscription(Pose2D, self.pose_topic, self.pose_cb, 10)
            self.get_logger().info(f"Subscribed to Pose2D topic: {self.pose_topic}")
        except Exception:
            self.get_logger().warning(f"Could not subscribe to Pose2D on {self.pose_topic}")

        # optional PoseStamped subscription and publisher (so we also publish current pose as PoseStamped)
        self.pose_stamped_sub = None
        self.pose_stamped_pub = None
        if self.pose_topic_stamped:
            try:
                self.pose_stamped_sub = self.create_subscription(PoseStamped, self.pose_topic_stamped, self.pose_stamped_cb, 10)
                self.get_logger().info(f"Subscribed to PoseStamped topic: {self.pose_topic_stamped}")
            except Exception:
                self.get_logger().warning(f"Could not subscribe to PoseStamped on {self.pose_topic_stamped}")
            try:
                self.pose_stamped_pub = self.create_publisher(PoseStamped, self.pose_topic_stamped, 10)
                self.get_logger().info(f"Publishing PoseStamped on: {self.pose_topic_stamped}")
            except Exception:
                self.get_logger().warning(f"Could not create PoseStamped publisher on {self.pose_topic_stamped}")

        # optional Odometry subscription
        self.pose_odom_sub = None
        if self.pose_topic_odom:
            try:
                self.pose_odom_sub = self.create_subscription(Odometry, self.pose_topic_odom, self.odom_input_cb, 10)
                self.get_logger().info(f"Subscribed to Odometry topic: {self.pose_topic_odom}")
            except Exception:
                self.get_logger().warning(f"Could not subscribe to Odometry on {self.pose_topic_odom}")

        # tf broadcaster
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # timer
        self.timer = self.create_timer(1.0 / max(1.0, self.update_rate), self.timer_cb)

        self.get_logger().info('SimWorld node started')

    def point_in_polygon(self, point, poly):
        """Return True if point is inside polygon `poly` using winding/ray casting algorithm."""
        x, y = point
        inside = False
        n = len(poly)
        j = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            # Check if edge crosses horizontal ray at y
            intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
            if intersect:
                inside = not inside
            j = i
        return inside

    def _rebuild_world_from_params(self):
        """Rebuild world structures based on current parameters.

        This builds:
        - self.base_polygons: the main world polygons
        - self.area_polys: enabled area polygons
        - self.base_segments: all segments from base polygons (unfiltered)
        - self.area_segments: all segments coming from enabled area polygons
        """
        import yaml
        base_parsed = []
        try:
            if isinstance(self.base_world, list):
                for item in self.base_world:
                    if isinstance(item, str):
                        if not item.strip():
                            continue
                        base_parsed.append(yaml.safe_load(item))
                    else:
                        base_parsed.append(item)
        except Exception as e:
            self.get_logger().warning(f"Failed parsing base world during rebuild: {e}")

        def _parse_param_list(param_name):
            raw = self.get_parameter(param_name).get_parameter_value().string_array_value
            parsed_list = []
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, str) and item.strip():
                        try:
                            parsed_list.append(yaml.safe_load(item))
                        except Exception as e:
                            self.get_logger().warning(f"Failed parsing {param_name} item: {e}")
                    elif isinstance(item, list):
                        parsed_list.append(item)
            return parsed_list

        # collect enabled area polygons separately
        area_polys = []
        try:
            if self.get_parameter('meihua_blue_enabled').get_parameter_value().bool_value:
                area_polys.extend(_parse_param_list('meihua_blue'))
            if self.get_parameter('arena_blue_enabled').get_parameter_value().bool_value:
                area_polys.extend(_parse_param_list('arena_blue'))
            if self.get_parameter('meihua_red_enabled').get_parameter_value().bool_value:
                area_polys.extend(_parse_param_list('meihua_red'))
            if self.get_parameter('arena_red_enabled').get_parameter_value().bool_value:
                area_polys.extend(_parse_param_list('arena_red'))
        except Exception as e:
            self.get_logger().warning(f"Error adding area polygons during rebuild: {e}")

        # build base segments (unfiltered)
        base_segments = []
        for poly in base_parsed:
            if not poly or len(poly) < 2:
                continue
            for j in range(len(poly)):
                p1 = poly[j]
                p2 = poly[(j + 1) % len(poly)]
                base_segments.append((p1, p2))

        # build area segments
        area_segments = []
        for poly in area_polys:
            if not poly or len(poly) < 2:
                continue
            for j in range(len(poly)):
                p1 = poly[j]
                p2 = poly[(j + 1) % len(poly)]
                area_segments.append((p1, p2))

        # store
        self.base_polygons = base_parsed
        self.area_polys = area_polys
        self.base_segments = base_segments
        self.area_segments = area_segments
        # combined world for debugging
        self.world = base_parsed + area_polys
        self.get_logger().info(f"World rebuilt; base_polygons: {len(self.base_polygons)}; area_polygons: {len(self.area_polys)}; base_segments: {len(self.base_segments)}; area_segments: {len(self.area_segments)}")

    def area_toggle_cb(self, msg: String):
        """Handle external area toggle commands in the format 'param_name:true'"""
        try:
            data = msg.data.strip()
            if ':' not in data:
                self.get_logger().warning(f"Invalid area toggle message: {data}")
                return
            name, val = data.split(':', 1)
            val = val.strip().lower() in ('1', 'true', 'yes', 'on')
            # set local parameter (use set_parameters to reflect change internally)
            try:
                p = self.set_parameters([rclpy.parameter.Parameter(name, value=val)])
                self.get_logger().info(f"Area toggle received: {name} -> {val}; calling rebuild")
            except Exception as e:
                # Fallback: set attribute directly
                setattr(self, name, val)
                self.get_logger().info(f"Area toggle received (attribute set): {name} -> {val}")
            # rebuild world based on updated param values
            try:
                self._rebuild_world_from_params()
            except Exception as e:
                self.get_logger().warning(f"Failed to rebuild world after area toggle: {e}")
        except Exception as e:
            self.get_logger().warning(f"Error handling area toggle message: {e}")

    def _on_set_parameters(self, params):
        """Callback for dynamic parameter changes; rebuild world if area flags changed."""
        try:
            touched = False
            for p in params:
                if p.name in ('meihua_blue_enabled', 'arena_blue_enabled', 'meihua_red_enabled', 'arena_red_enabled', 'meihua_blue', 'arena_blue', 'meihua_red', 'arena_red'):
                    touched = True
            if touched:
                # Update our cached flags
                try:
                    self.meihua_blue_enabled = self.get_parameter('meihua_blue_enabled').get_parameter_value().bool_value
                except Exception:
                    pass
                try:
                    self.arena_blue_enabled = self.get_parameter('arena_blue_enabled').get_parameter_value().bool_value
                except Exception:
                    pass
                try:
                    self.meihua_red_enabled = self.get_parameter('meihua_red_enabled').get_parameter_value().bool_value
                except Exception:
                    pass
                try:
                    self.arena_red_enabled = self.get_parameter('arena_red_enabled').get_parameter_value().bool_value
                except Exception:
                    pass
                # Rebuild world
                self._rebuild_world_from_params()
            from rcl_interfaces.msg import SetParametersResult
            return SetParametersResult(successful=True)
        except Exception:
            from rcl_interfaces.msg import SetParametersResult
            return SetParametersResult(successful=False)


    def pose_cb(self, msg: Pose2D):
        self.pose_x = msg.x
        self.pose_y = msg.y
        self.pose_yaw = msg.theta
        # external pose overrides velocities
        self.vx = 0.0
        self.vy = 0.0
        self.vyaw = 0.0
        self.last_pose_stamp = self.get_clock().now()
        self.last_update_time = self.get_clock().now()

    def cmd_vel_cb(self, msg: Twist):
        # store velocities in robot frame
        self.vx = float(msg.linear.x)
        self.vy = float(msg.linear.y)
        self.vyaw = float(msg.angular.z)
        # update last update time to avoid large first-step integration
        self.last_update_time = self.get_clock().now()
        # do not override pose now; integration happens in timer_cb
        self.get_logger().info(f"Received cmd_vel: vx={self.vx}, vy={self.vy}, vyaw={self.vyaw}")

    def pose_stamped_cb(self, msg: PoseStamped):
        # Extract pose from PoseStamped and treat as an external pose input
        self.pose_x = msg.pose.position.x
        self.pose_y = msg.pose.position.y
        q = msg.pose.orientation
        yaw = 0.0
        try:
            yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])[2]
        except Exception:
            yaw = 0.0
        self.pose_yaw = yaw
        # external pose overrides velocities to avoid drift
        self.vx = 0.0
        self.vy = 0.0
        self.vyaw = 0.0
        self.last_pose_stamp = self.get_clock().now()
        self.last_update_time = self.get_clock().now()



    def odom_input_cb(self, msg: Odometry):
        # Use incoming odometry as external pose input and reset velocities
        self.pose_x = msg.pose.pose.position.x
        self.pose_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        try:
            self.pose_yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])[2]
        except Exception:
            self.pose_yaw = 0.0
        # external odom overrides velocities to avoid drift
        self.vx = 0.0
        self.vy = 0.0
        self.vyaw = 0.0
        self.last_pose_stamp = self.get_clock().now()
        self.last_update_time = self.get_clock().now()

    def publish_odom(self, stamp):
        odom = Odometry()
        odom.header = Header()
        odom.header.stamp = stamp.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = self.base_frame

        odom.pose.pose.position.x = self.pose_x
        odom.pose.pose.position.y = self.pose_y
        odom.pose.pose.position.z = 0.0
        q = quaternion_from_euler(0, 0, self.pose_yaw)
        odom.pose.pose.orientation = Quaternion(x=q[0], y=q[1], z=q[2], w=q[3])

        # zero covariances for simplicity
        odom.pose.covariance = [0.0] * 36
        odom.twist.covariance = [0.0] * 36

        self.odom_pub.publish(odom)

        # broadcast tf: odom -> base_link
        t = TransformStamped()
        t.header.stamp = stamp.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = self.base_frame
        t.transform.translation.x = self.pose_x
        t.transform.translation.y = self.pose_y
        t.transform.translation.z = 0.0
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]
        self.tf_broadcaster.sendTransform(t)

        # publish PoseStamped mirror of odom for other components (e.g., GUI)
        if self.pose_stamped_pub:
            ps = PoseStamped()
            ps.header.stamp = stamp.to_msg()
            ps.header.frame_id = 'odom'
            ps.pose = Pose()
            ps.pose.position.x = self.pose_x
            ps.pose.position.y = self.pose_y
            ps.pose.orientation = Quaternion(x=q[0], y=q[1], z=q[2], w=q[3])
            self.pose_stamped_pub.publish(ps)
        t.transform.rotation.w = q[3]
        self.tf_broadcaster.sendTransform(t)

    def timer_cb(self):
        stamp = self.get_clock().now()
        # integrate velocities (if any)
        try:
            dt = (stamp - self.last_update_time).nanoseconds * 1e-9
        except Exception:
            dt = 0.0
        if dt > 0.0 and (abs(self.vx) > 1e-9 or abs(self.vy) > 1e-9 or abs(self.vyaw) > 1e-9):
            # velocities are in robot frame; convert to world frame
            dx = (self.vx * math.cos(self.pose_yaw) - self.vy * math.sin(self.pose_yaw)) * dt
            dy = (self.vx * math.sin(self.pose_yaw) + self.vy * math.cos(self.pose_yaw)) * dt
            self.pose_x += dx
            self.pose_y += dy
            self.pose_yaw += self.vyaw * dt
            self.last_update_time = stamp

        # publish odom
        self.publish_odom(stamp)
        # compute scan
        scan = LaserScan()
        scan.header = Header()
        scan.header.stamp = stamp.to_msg()
        scan.header.frame_id = self.scan_frame

        scan.angle_min = -self.fov / 2.0
        scan.angle_max = self.fov / 2.0
        scan.angle_increment = self.angle_increment
        num_readings = int(round((scan.angle_max - scan.angle_min) / scan.angle_increment)) + 1
        scan.time_increment = 0.0
        scan.scan_time = 1.0 / max(1.0, self.update_rate)
        scan.range_min = float(self.range_min)
        scan.range_max = float(self.range_max)

        ranges = [scan.range_max] * num_readings

        # Build active segments based on the area(s) the robot currently occupies
        # Robot-anchored occlusion: base segments whose midpoint is inside the robot's current area
        # are removed so that the area's walls will occlude them.
        current_area_polys = []
        try:
            for a in getattr(self, 'area_polys', []):
                try:
                    if self.point_in_polygon((self.pose_x, self.pose_y), a):
                        current_area_polys.append(a)
                except Exception:
                    pass
        except Exception:
            current_area_polys = []

        segments_to_use = []
        # base segments: potong jika beririsan area
        for p1, p2 in getattr(self, 'base_segments', []):
            segs = [(p1, p2)]
            for poly in current_area_polys:
                segs = self.subtract_segment_by_polygon(segs, poly)
            segments_to_use.extend(segs)
        # area_segments: tetap tambahkan
        for p1, p2 in getattr(self, 'area_segments', []):
            segments_to_use.append((p1, p2))

        angles = [scan.angle_min + i * scan.angle_increment for i in range(num_readings)]
        for i, a in enumerate(angles):
            # ray in world coordinates
            rx = math.cos(self.pose_yaw + a)
            ry = math.sin(self.pose_yaw + a)
            closest = scan.range_max
            ray_origin = (self.pose_x, self.pose_y)
            ray_end = (self.pose_x + rx * scan.range_max, self.pose_y + ry * scan.range_max)

            # check intersection with active segments
            for p1, p2 in segments_to_use:
                inter = line_intersection(p1, p2, ray_origin, ray_end)
                if inter is None:
                    continue
                ix, iy, t, u = inter
                # t between 0..1 indicates intersection within segment; u between 0..1 indicates along ray segment
                if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
                    dist = math.hypot(ix - self.pose_x, iy - self.pose_y)
                    if dist < closest:
                        closest = dist
            # apply noise
            if self.noise_std and closest < scan.range_max:
                closest = max(scan.range_min, random.gauss(closest, self.noise_std))
            ranges[i] = float(closest)

        scan.ranges = ranges
        self.scan_pub.publish(scan)


def main(args=None):
    rclpy.init(args=args)
    node = SimWorldNode()
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
