"""Nav2 on the indoor map (sim must already be running for_nav).

Terminal 1:
  ros2 launch tc_gazebo sim_indoor.launch.py for_nav:=true

Terminal 2:
  ros2 launch tc_gazebo nav_indoor.launch.py

Requires maps/my_indoor.yaml (./scripts/save_map.sh my_indoor).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _default_map(pkg: str) -> str:
    ws_root = os.path.abspath(os.path.join(pkg, '..', '..', '..', '..'))
    return os.path.join(ws_root, 'maps', 'my_indoor.yaml')


def _setup(context, *args, **kwargs):
    pkg = get_package_share_directory('tc_gazebo')
    nav_launch = os.path.join(pkg, 'launch', 'nav_bringup.launch.py')

    map_yaml = os.path.expanduser(LaunchConfiguration('map').perform(context))
    if not map_yaml:
        map_yaml = _default_map(pkg)

    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav_launch),
            launch_arguments={
                'map': map_yaml,
                'use_sim_time': LaunchConfiguration('use_sim_time').perform(context),
                'initial_pose_x': LaunchConfiguration('initial_pose_x').perform(context),
                'initial_pose_y': LaunchConfiguration('initial_pose_y').perform(context),
                'initial_pose_yaw': LaunchConfiguration('initial_pose_yaw').perform(context),
            }.items(),
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value='',
            description='Override map yaml (default: <ws>/maps/my_indoor.yaml)',
        ),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('initial_pose_x', default_value='-2.0'),
        DeclareLaunchArgument('initial_pose_y', default_value='0.0'),
        DeclareLaunchArgument('initial_pose_yaw', default_value='0.0'),
        OpaqueFunction(function=_setup),
    ])
