"""Nav2 navigation stack for Thundercar sim (assumes localization is running).

Starts planner / controller / BT navigator / velocity smoother.
Twist commands go to /cmd_vel (Gazebo AckermannSteering).

Run sim without the teleop cmd_vel bridge:
  ros2 launch tc_gazebo sim.launch.py rviz:=false teleop:=false ackermann_bridge:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    pkg = get_package_share_directory('tc_gazebo')
    default_params = os.path.join(pkg, 'config', 'nav2_params.yaml')
    default_bt = os.path.join(
        pkg, 'behavior_trees', 'navigate_to_pose_w_backup_first.xml'
    )
    default_bt_through = os.path.join(
        pkg, 'behavior_trees', 'navigate_through_poses_w_backup_first.xml'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params_file')
    autostart = LaunchConfiguration('autostart')

    lifecycle_nodes = [
        'controller_server',
        'smoother_server',
        'planner_server',
        'behavior_server',
        'bt_navigator',
        'waypoint_follower',
        'velocity_smoother',
    ]

    remappings = [('/tf', 'tf'), ('/tf_static', 'tf_static')]

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
            root_key='',
            param_rewrites={
                'default_nav_to_pose_bt_xml': default_bt,
                'default_nav_through_poses_bt_xml': default_bt_through,
            },
            convert_types=True,
        ),
        allow_substs=True,
    )

    return LaunchDescription([
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('params_file', default_value=default_params),
        DeclareLaunchArgument('autostart', default_value='true'),

        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[configured_params, {'use_sim_time': use_sim_time}],
            remappings=remappings + [('cmd_vel', 'cmd_vel_nav')],
        ),
        Node(
            package='nav2_smoother',
            executable='smoother_server',
            name='smoother_server',
            output='screen',
            parameters=[configured_params, {'use_sim_time': use_sim_time}],
            remappings=remappings,
        ),
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[configured_params, {'use_sim_time': use_sim_time}],
            remappings=remappings,
        ),
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output='screen',
            parameters=[configured_params, {'use_sim_time': use_sim_time}],
            remappings=remappings + [('cmd_vel', 'cmd_vel_nav')],
        ),
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[configured_params, {'use_sim_time': use_sim_time}],
            remappings=remappings,
        ),
        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[configured_params, {'use_sim_time': use_sim_time}],
            remappings=remappings,
        ),
        Node(
            package='nav2_velocity_smoother',
            executable='velocity_smoother',
            name='velocity_smoother',
            output='screen',
            parameters=[configured_params, {'use_sim_time': use_sim_time}],
            remappings=remappings + [
                ('cmd_vel', 'cmd_vel_nav'),
                ('cmd_vel_smoothed', 'cmd_vel'),
            ],
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': autostart,
                'node_names': lifecycle_nodes,
                'bond_timeout': 10.0,
                'bond_respawn_max_duration': 20.0,
                'attempt_respawn_reconnection': True,
            }],
        ),
    ])
