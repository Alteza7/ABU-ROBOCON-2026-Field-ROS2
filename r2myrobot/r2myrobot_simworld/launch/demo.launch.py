import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.conditions import IfCondition


def generate_launch_description():
    pkg_desc = FindPackageShare(package='r2myrobot_description').find('r2myrobot_description')
    desc_launch = os.path.join(pkg_desc, 'launch', 'description.launch.py')

    pkg_sim = FindPackageShare(package='r2myrobot_simworld').find('r2myrobot_simworld')
    sim_launch = os.path.join(pkg_sim, 'launch', 'simworld.launch.py')

    # Detect if Cyclone DDS runtime library is present; prefer it to avoid Fast-RTPS SHM lock errors
    import glob
    cyclonedds_libs = glob.glob('/opt/ros/*/lib/librmw_cyclonedds_cpp.so')
    if cyclonedds_libs:
        env_action = SetEnvironmentVariable('RMW_IMPLEMENTATION', 'rmw_cyclonedds_cpp')
    else:
        env_action = None

    demo_pose_node = Node(
        package='r2myrobot_simworld',
        executable='demo_pose_publisher',
        name='demo_pose_publisher',
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_demo_pose')),
        parameters=[{
            'pose_topic': '/r2myrobot/pose2d',
            'pose_stamped_topic': '',
            'odom_topic': ''
        }]
    )

    # Allow running without the demo pose publisher so GUI/place-robot controls can drive the sim directly
    declare_use_demo = DeclareLaunchArgument('use_demo_pose', default_value='true', description='Run demo pose publisher?')

    map_bridge_node = Node(
        package='r2myrobot_simworld',
        executable='map_point_bridge',
        name='map_point_bridge',
        output='screen'
    )

    actions = []
    if env_action is not None:
        actions.append(env_action)

    actions.extend([
        DeclareLaunchArgument('robot_base', default_value='r2myrobot.urdf.xacro', description='robot xacro filename (example: r2myrobot.urdf.xacro)'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(desc_launch)),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(sim_launch)),
        demo_pose_node,
        map_bridge_node
    ])

    return LaunchDescription(actions)
