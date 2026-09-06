"""Localization + Nav2 for Thundercar sim (map → drive to goal).

Prefer per-map launches:
  ros2 launch tc_gazebo sim_lvl16.launch.py for_nav:=true
  ros2 launch tc_gazebo nav_lvl16.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _setup(context, *args, **kwargs):
    pkg = get_package_share_directory('tc_gazebo')
    loc_launch = os.path.join(pkg, 'launch', 'localization.launch.py')
    nav_launch = os.path.join(pkg, 'launch', 'navigation.launch.py')
    rviz_config = os.path.join(pkg, 'rviz', 'nav2.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)
    start_rviz = LaunchConfiguration('rviz').perform(context).lower() in (
        'true', '1', 'yes',
    )

    actions = [
        LogInfo(msg=['Nav2 RViz config: ', rviz_config, ' (start_rviz=', str(start_rviz), ')']),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(loc_launch),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'map': LaunchConfiguration('map').perform(context),
                'rviz': 'false',
                'initial_pose_x': LaunchConfiguration('initial_pose_x').perform(context),
                'initial_pose_y': LaunchConfiguration('initial_pose_y').perform(context),
                'initial_pose_yaw': LaunchConfiguration('initial_pose_yaw').perform(context),
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav_launch),
            launch_arguments={
                'use_sim_time': use_sim_time,
            }.items(),
        ),
    ]

    if start_rviz:
        # Resolve IfCondition at compose-time — TimerAction+IfCondition often skips RViz.
        rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='nav2_rviz',
            output='screen',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': use_sim_time == 'true'}],
            additional_env={
                'QT_QPA_PLATFORM': 'xcb',
                'DISPLAY': os.environ.get('DISPLAY', ':0'),
            },
        )
        # Measured: launch → navigation "Managed nodes are active" ≈ 14.2s
        # (mostly Smac Hybrid LUT). +15% → 16.3s.
        actions.append(TimerAction(period=16.3, actions=[rviz_node]))
        actions.insert(
            0,
            LogInfo(msg='RViz starts ~16s after launch (Nav2 bringup + 15%)'),
        )

    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument(
            'rviz',
            default_value='true',
            description='Start RViz (lite nav2.rviz — no costmap/camera overlays)',
        ),
        DeclareLaunchArgument(
            'map',
            default_value='',
            description='Path to map.yaml (default: workspace maps/my_indoor.yaml)',
        ),
        DeclareLaunchArgument('initial_pose_x', default_value='0.0'),
        DeclareLaunchArgument('initial_pose_y', default_value='0.0'),
        DeclareLaunchArgument('initial_pose_yaw', default_value='0.0'),
        OpaqueFunction(function=_setup),
    ])
