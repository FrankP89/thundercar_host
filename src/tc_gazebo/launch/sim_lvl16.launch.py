"""Thundercar sim in the lvl16 figure-8 world.

Drive / map (default):
  ros2 launch tc_gazebo sim_lvl16.launch.py

Nav2 companion (no teleop fighting /cmd_vel):
  ros2 launch tc_gazebo sim_lvl16.launch.py for_nav:=true
  # optional: headless:=true if RViz crashes sharing GL with Gazebo GUI
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


# Spawn: lower-left corridor, facing +y
_SPAWN = {'x': '-4.4', 'y': '-7.0', 'z': '0.15', 'yaw': '1.5708'}


def _setup(context, *args, **kwargs):
    pkg = get_package_share_directory('tc_gazebo')
    sim_launch = os.path.join(pkg, 'launch', 'sim.launch.py')
    world = os.path.join(pkg, 'worlds', 'tc_lvl16.sdf')

    for_nav = LaunchConfiguration('for_nav').perform(context).lower() in (
        'true', '1', 'yes',
    )
    if for_nav:
        rviz, teleop, ackermann = 'false', 'false', 'false'
    else:
        rviz = LaunchConfiguration('rviz').perform(context)
        teleop = LaunchConfiguration('teleop').perform(context)
        ackermann = LaunchConfiguration('ackermann_bridge').perform(context)

    headless = LaunchConfiguration('headless').perform(context)

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
                'headless': headless,
                'use_keyboard': LaunchConfiguration('use_keyboard').perform(context),
                'use_joystick': LaunchConfiguration('use_joystick').perform(context),
                'use_sim_time': LaunchConfiguration('use_sim_time').perform(context),
                'max_speed': LaunchConfiguration('max_speed').perform(context),
                'speed_step': LaunchConfiguration('speed_step').perform(context),
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
        # Default off — Gazebo GUI + RViz together often flicker on shared GL
        DeclareLaunchArgument(
            'rviz',
            default_value='false',
            description='Start RViz2 (use with headless:=true to avoid GL flicker)',
        ),
        DeclareLaunchArgument(
            'headless',
            default_value='false',
            description='true: no Gazebo 3D window (frees GPU for RViz)',
        ),
        DeclareLaunchArgument('teleop', default_value='true'),
        DeclareLaunchArgument('ackermann_bridge', default_value='true'),
        DeclareLaunchArgument('use_keyboard', default_value='true'),
        DeclareLaunchArgument('use_joystick', default_value='false'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument(
            'max_speed',
            default_value='0.4',
            description='Keyboard speed cap [m/s] — keep ≤0.4 while mapping',
        ),
        DeclareLaunchArgument('speed_step', default_value='0.1'),
        OpaqueFunction(function=_setup),
    ])
