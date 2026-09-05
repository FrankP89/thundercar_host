"""Localization + Nav2 for Thundercar sim (map → drive to goal).

Expects sim already running WITHOUT teleop cmd_vel bridge:
  ros2 launch tc_gazebo sim.launch.py rviz:=false teleop:=false ackermann_bridge:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('tc_gazebo')
    loc_launch = os.path.join(pkg, 'launch', 'localization.launch.py')
    nav_launch = os.path.join(pkg, 'launch', 'navigation.launch.py')
    rviz_config = os.path.join(pkg, 'rviz', 'nav2.rviz')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='nav2_rviz',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        additional_env={'LIBGL_ALWAYS_SOFTWARE': '0'},
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument(
            'map',
            default_value='',
            description='Path to map.yaml (default: workspace maps/my_indoor.yaml)',
        ),
        DeclareLaunchArgument('initial_pose_x', default_value='0.0'),
        DeclareLaunchArgument('initial_pose_y', default_value='0.0'),
        DeclareLaunchArgument('initial_pose_yaw', default_value='0.0'),

        LogInfo(msg=['Nav2 RViz config: ', rviz_config]),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(loc_launch),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'map': LaunchConfiguration('map'),
                'rviz': 'false',
                'initial_pose_x': LaunchConfiguration('initial_pose_x'),
                'initial_pose_y': LaunchConfiguration('initial_pose_y'),
                'initial_pose_yaw': LaunchConfiguration('initial_pose_yaw'),
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav_launch),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
        ),
        # Delay so map/AMCL are up; always start (no IfCondition — was silently skipping)
        TimerAction(period=2.0, actions=[rviz_node]),
    ])
