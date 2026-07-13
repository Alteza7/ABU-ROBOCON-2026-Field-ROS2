import os
import launch
import launch_ros
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    use_sim_time = True
    
    # Get robot base type from environment variable (default: 2wd)
    robot_base = os.getenv('R2MYROBOT_BASE', '2wd')
    
    # Get package paths
    pkg_path_r2myrobot_gazebo = get_package_share_directory('r2myrobot_gazebo')
    pkg_path_r2myrobot_description = get_package_share_directory('r2myrobot_description')
    pkg_path_gazebo_ros = get_package_share_directory('gazebo_ros')
    
    # URDF path for the robot
    urdf_path = os.path.join(
        pkg_path_r2myrobot_description, 
        'urdf', 
        'robots', 
        f'{robot_base}.urdf.xacro'
    )
    
    # World file path
    world_path = os.path.join(pkg_path_r2myrobot_gazebo, 'worlds', 'empty.world')
    
    # Map xacro path
    map_xacro_path = os.path.join(pkg_path_r2myrobot_gazebo, 'urdf', 'map', 'rcmap.xacro')
    
    # Robot state publisher for the robot
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(
                Command(['xacro ', urdf_path]),
                value_type=str
            ),
            'use_sim_time': use_sim_time
        }]
    )
    
    # Robot state publisher for the map
    robot_state_publisher_map = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher_map',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(
                Command(['xacro ', map_xacro_path]),
                value_type=str
            ),
            'use_sim_time': use_sim_time
        }],
        remappings=[
            ('/robot_description', '/robot_description_map')
        ]
    )
    
    # Spawn the robot in Gazebo
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'r2myrobot',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1',
        ],
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )
    
    # Spawn the map in Gazebo
    spawn_entity_map = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description_map',
            '-entity', 'rcmap',
            '-x', '11.0',
            '-y', '11.0',
            '-z', '0.05',
            '-Y', '3.14',
        ],
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )
    
    # Include Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments=[
            ('world', world_path),
            ('verbose', 'true'),
            ('use_sim_time', str(use_sim_time).lower()),
        ]
    )
    
    return launch.LaunchDescription([
        gazebo,
        robot_state_publisher,
        robot_state_publisher_map,
        spawn_entity,
        spawn_entity_map,
    ])