import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare(package='r2myrobot_simworld').find('r2myrobot_simworld')
    params_file = os.path.join(pkg_share, 'params', 'simworld_params.yaml')

    sim_node = Node(
        package='r2myrobot_simworld',
        executable='simworld_node',
        name='simworld_node',
        output='screen',
        parameters=[params_file]
    )

    return LaunchDescription([
        sim_node
    ])
