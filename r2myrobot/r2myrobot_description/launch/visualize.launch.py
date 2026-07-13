import launch
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch.actions import DeclareLaunchArgument
import launch_ros
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    robot_base = LaunchConfiguration('robot_base')

    package_name = 'r2myrobot_description'

    pkg_share = launch_ros.substitutions.FindPackageShare(package=package_name).find(package_name)
    
    from launch.substitutions import PathJoinSubstitution
    xacro_file = PathJoinSubstitution([pkg_share, 'urdf', 'robots', LaunchConfiguration('robot_base')])
    rviz_config_file = PathJoinSubstitution([pkg_share, 'rviz', 'description.rviz'])

    robot_description = Command(['xacro ', xacro_file])
    from launch_ros.parameter_descriptions import ParameterValue

    print('Xacro file: ', xacro_file)

    # Robot State Publisher node
    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': ParameterValue(robot_description, value_type=str)}]
    )

    # Joint State Publisher GUI node
    joint_state_publisher_gui_node = launch_ros.actions.Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui'
    )

    # RViz node
    rviz_node = launch_ros.actions.Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
    )

    # Return the LaunchDescription
    return launch.LaunchDescription([
        DeclareLaunchArgument(
            'robot_base', default_value='r2myrobot.urdf.xacro', description='robot xacro filename (example: r2myrobot.urdf.xacro)'
        ),
        joint_state_publisher_gui_node,
        robot_state_publisher_node,
        rviz_node
    ])
