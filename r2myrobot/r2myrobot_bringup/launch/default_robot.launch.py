from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, EqualsSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.conditions import IfCondition


def generate_launch_description():
    sensors_launch_path = PathJoinSubstitution(
        [FindPackageShare('r2myrobot_bringup'), 'launch', 'sensors.launch.py']
    )

    description_launch_path = PathJoinSubstitution(
        [FindPackageShare('r2myrobot_description'), 'launch', 'description.launch.py']
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            name='base_serial_port', 
            default_value='/dev/ttyACM0',
            description='R2myrobot Base Serial Port'
        ),

        DeclareLaunchArgument(
            name='micro_ros_baudrate', 
            default_value='921600',
            description='micro-ROS baudrate'
        ),

        DeclareLaunchArgument(
            name='micro_ros_transport',
            default_value='serial',
            description='micro-ROS transport'
        ),

        DeclareLaunchArgument(
            name='micro_ros_port',
            default_value='8888',
            description='micro-ROS udp/tcp port number'
        ),

        Node(
            condition=IfCondition(EqualsSubstitution(LaunchConfiguration('micro_ros_transport'), 'serial')),
            package='micro_ros_agent',
            executable='micro_ros_agent',
            name='micro_ros_agent',
            output='screen',
            arguments=['serial', '--dev', LaunchConfiguration("base_serial_port"), '--baudrate', LaunchConfiguration("micro_ros_baudrate")],
        ),

        Node(
            condition=IfCondition(EqualsSubstitution(LaunchConfiguration('micro_ros_transport'), 'udp4')),
            package='micro_ros_agent',
            executable='micro_ros_agent',
            name='micro_ros_agent',
            output='screen',
            arguments=[LaunchConfiguration('micro_ros_transport'), '--port', LaunchConfiguration('micro_ros_port')],
        ),
    
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(description_launch_path)
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(sensors_launch_path),
        )
    ])
