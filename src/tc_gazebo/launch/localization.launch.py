"""Localization on a saved map (map_server + AMCL).

Expects sim already running (and mapping stopped):
  ros2 launch tc_gazebo sim.launch.py rviz:=false

Example:
  ros2 launch tc_gazebo localization.launch.py
  ros2 launch tc_gazebo localization.launch.py map:=/path/to/map.yaml
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _setup(context, *args, **kwargs):
    pkg = get_package_share_directory('tc_gazebo')
    # Default: workspace maps/my_indoor.yaml (share/ is under install/…/share)
    # Prefer explicit map:= ; else try common workspace path next to install/
    map_yaml = os.path.expanduser(LaunchConfiguration('map').perform(context))
    if not map_yaml:
        # tc_gazebo share -> .../install/tc_gazebo/share/tc_gazebo
        ws_root = os.path.abspath(os.path.join(pkg, '..', '..', '..', '..'))
        candidate = os.path.join(ws_root, 'maps', 'my_indoor.yaml')
        if os.path.isfile(candidate):
            map_yaml = candidate
        else:
            map_yaml = os.path.join(pkg, '..', '..', '..', '..', 'maps', 'my_indoor.yaml')
            map_yaml = os.path.abspath(map_yaml)

    if not os.path.isfile(map_yaml):
        raise RuntimeError(
            f"Map file not found: '{map_yaml}'. Pass map:=/full/path/to/map.yaml "
            "(the .yaml from ./scripts/save_map.sh)."
        )

    use_sim_time = LaunchConfiguration('use_sim_time')
    rviz = LaunchConfiguration('rviz').perform(context).lower() == 'true'
    amcl_params = os.path.join(pkg, 'config', 'amcl_params.yaml')
    rviz_config = os.path.join(pkg, 'rviz', 'localization.rviz')

    initial_pose_x = float(LaunchConfiguration('initial_pose_x').perform(context))
    initial_pose_y = float(LaunchConfiguration('initial_pose_y').perform(context))
    initial_pose_yaw = float(LaunchConfiguration('initial_pose_yaw').perform(context))

    nodes = [
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'yaml_filename': map_yaml,
            }],
        ),
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[
                amcl_params,
                {
                    'use_sim_time': use_sim_time,
                    'set_initial_pose': True,
                    'initial_pose.x': initial_pose_x,
                    'initial_pose.y': initial_pose_y,
                    'initial_pose.z': 0.0,
                    'initial_pose.yaw': initial_pose_yaw,
                },
            ],
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': True,
                'node_names': ['map_server', 'amcl'],
            }],
        ),
    ]

    if rviz:
        nodes.append(
            Node(
                package='rviz2',
                executable='rviz2',
                name='localization_rviz',
                output='screen',
                arguments=['-d', rviz_config],
                parameters=[{'use_sim_time': use_sim_time}],
            )
        )

    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use /clock from Gazebo',
        ),
        DeclareLaunchArgument(
            'map',
            default_value='',
            description='Full path to map.yaml (default: <ws>/maps/my_indoor.yaml)',
        ),
        DeclareLaunchArgument(
            'rviz',
            default_value='true',
            description='Open localization RViz (Fixed Frame map)',
        ),
        DeclareLaunchArgument(
            'initial_pose_x',
            default_value='0.0',
            description='Initial pose x in map frame (or use 2D Pose Estimate)',
        ),
        DeclareLaunchArgument(
            'initial_pose_y',
            default_value='0.0',
            description='Initial pose y in map frame',
        ),
        DeclareLaunchArgument(
            'initial_pose_yaw',
            default_value='0.0',
            description='Initial pose yaw [rad] in map frame',
        ),
        OpaqueFunction(function=_setup),
    ])
