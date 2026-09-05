"""Optional teleop for sim: keyboard (default) and/or joystick.

Joystick is skipped entirely if joy / joy_teleop are not installed, or if
use_joystick:=false. Keyboard opens in a new terminal when a terminal
emulator is available.
"""

import shutil

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _joy_packages_available() -> bool:
    try:
        get_package_share_directory('joy')
        get_package_share_directory('joy_teleop')
        return True
    except PackageNotFoundError:
        return False


def _terminal_prefix() -> str | None:
    """Return a launch Node prefix that opens an interactive terminal, or None."""
    if shutil.which('gnome-terminal'):
        return 'gnome-terminal --'
    if shutil.which('xterm'):
        return 'xterm -e'
    if shutil.which('konsole'):
        return 'konsole -e'
    return None


def _setup(context, *args, **kwargs):
    use_joystick = LaunchConfiguration('use_joystick').perform(context).lower() in (
        'true', '1', 'yes',
    )
    use_keyboard = LaunchConfiguration('use_keyboard').perform(context).lower() in (
        'true', '1', 'yes',
    )

    actions = []

    # --- Keyboard (default) ------------------------------------------------
    if use_keyboard:
        prefix = _terminal_prefix()
        if prefix:
            actions.append(
                LogInfo(msg=f'Starting keyboard Ackermann teleop in a new terminal ({prefix}).')
            )
            actions.append(
                Node(
                    package='tc_control',
                    executable='keyboard_ackermann',
                    name='keyboard_ackermann',
                    output='screen',
                    prefix=prefix,
                    parameters=[{'topic': '/ackermann_cmd'}],
                )
            )
            actions.append(
                LogInfo(
                    msg='Keyboard: w/s speed, a/d steer, space stop, q quit '
                    '(publishes /ackermann_cmd).'
                )
            )
        else:
            actions.append(
                LogInfo(
                    msg='No gnome-terminal/xterm/konsole found. Start keyboard teleop yourself:\n'
                    '  ros2 run tc_control keyboard_ackermann'
                )
            )

    # --- Joystick (optional; ignored if packages missing) ------------------
    if use_joystick:
        if _joy_packages_available():
            joy_teleop_cfg = PathJoinSubstitution(
                [FindPackageShare('tc_control'), 'config', 'joy_teleop.yaml']
            )
            joy_node_cfg = PathJoinSubstitution(
                [FindPackageShare('tc_control'), 'config', 'joy_node.yaml']
            )
            actions.append(LogInfo(msg='Starting joystick teleop (hold Left Bumper to drive).'))
            actions.append(
                Node(
                    package='joy',
                    executable='joy_node',
                    name='joy_node',
                    parameters=[joy_node_cfg],
                    # Do not take down the whole sim if no gamepad is plugged in
                    respawn=False,
                )
            )
            actions.append(
                Node(
                    package='joy_teleop',
                    executable='joy_teleop',
                    name='joy_teleop',
                    parameters=[joy_teleop_cfg],
                    respawn=False,
                )
            )
        else:
            actions.append(
                LogInfo(
                    msg='use_joystick:=true but joy/joy_teleop are not installed — ignoring. '
                    'Install ros-jazzy-joy ros-jazzy-joy-teleop, or use keyboard teleop.'
                )
            )

    if not use_keyboard and not use_joystick:
        actions.append(
            LogInfo(
                msg='No teleop enabled. Drive with:\n'
                '  ros2 run tc_control keyboard_ackermann\n'
                'or relaunch with use_keyboard:=true / use_joystick:=true'
            )
        )

    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_keyboard',
            default_value='true',
            description='Open keyboard Ackermann teleop (w/a/s/d) in a new terminal',
        ),
        DeclareLaunchArgument(
            'use_joystick',
            default_value='false',
            description='Start joy + joy_teleop if those packages are installed',
        ),
        OpaqueFunction(function=_setup),
    ])
