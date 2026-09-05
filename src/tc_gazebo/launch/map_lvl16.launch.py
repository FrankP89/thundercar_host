"""SLAM mapping for the lvl16 world (sim must already be running).

Drive slowly and steadily — stop/start bursts and high speed warp the map.
Sim teleop defaults to max_speed:=0.4 m/s for this reason.

Terminal 1:
  source /opt/ros/jazzy/setup.bash && source install/setup.bash
  ros2 launch tc_gazebo sim_lvl16.launch.py rviz:=false

Terminal 2:
  source /opt/ros/jazzy/setup.bash && source install/setup.bash
  ros2 launch tc_gazebo map_lvl16.launch.py

Save when done:
  ./scripts/save_map.sh lvl16
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg = get_package_share_directory('tc_gazebo')
    slam_launch = os.path.join(pkg, 'launch', 'slam.launch.py')

    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        LogInfo(
            msg='Mapping tip: keep a slow constant speed (≤0.4 m/s). '
            'Avoid sudden stops/starts and fast loops — they corrupt the map.'
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch),
            launch_arguments={
                'rviz': LaunchConfiguration('rviz'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
        ),
    ])
