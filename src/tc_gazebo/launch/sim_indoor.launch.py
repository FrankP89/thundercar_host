"""Thundercar sim in the small indoor world.

Drive / map:
  ros2 launch tc_gazebo sim_indoor.launch.py

Nav2 companion:
  ros2 launch tc_gazebo sim_indoor.launch.py for_nav:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


_SPAWN = {'x': '-2.0', 'y': '0.0', 'z': '0.15', 'yaw': '0.0'}


def _setup(context, *args, **kwargs):
    pkg = get_package_share_directory('tc_gazebo')
    sim_launch = os.path.join(pkg, 'launch', 'sim.launch.py')
    world = os.path.join(pkg, 'worlds', 'tc_indoor.sdf')

    for_nav = LaunchConfiguration('for_nav').perform(context).lower() in (
        'true', '1', 'yes',
    )
    if for_nav:
        rviz, teleop, ackermann = 'false', 'false', 'false'
    else:
        rviz = LaunchConfiguration('rviz').perform(context)
        teleop = LaunchConfiguration('teleop').perform(context)
        ackermann = LaunchConfiguration('ackermann_bridge').perform(context)

    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(sim_launch),
            launch_arguments={
                'world': world,
                'x': _SPAWN['x'],
                'y': _SPAWN['y'],
                'z': _SPAWN['z'],
                'yaw': _SPAWN['yaw'],
                'rviz': rviz,
                'teleop': teleop,
                'ackermann_bridge': ackermann,
                'use_keyboard': LaunchConfiguration('use_keyboard').perform(context),
                'use_joystick': LaunchConfiguration('use_joystick').perform(context),
                'use_sim_time': LaunchConfiguration('use_sim_time').perform(context),
            }.items(),
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'for_nav',
            default_value='false',
            description='true: rviz/teleop/ackermann_bridge off (Nav2 owns /cmd_vel)',
        ),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('teleop', default_value='true'),
        DeclareLaunchArgument('ackermann_bridge', default_value='true'),
        DeclareLaunchArgument('use_keyboard', default_value='true'),
        DeclareLaunchArgument('use_joystick', default_value='false'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        OpaqueFunction(function=_setup),
    ])
